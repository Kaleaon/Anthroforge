"""B18 prototype: scripted sculpt pass on the B10 wolf torso blockout.

Stages: A blockout primitives -> B join + voxel remesh (sculpt substrate)
-> C data-level sculpt pass implementing five brush analogues with their
real deformation math (no viewport operators — see probe results):
  S1 clay-strips : layered elongated-normal displacement along stroke lines
  S2 inflate/sag : radial falloff displacement biased downward (belly)
  S3 scrape      : pull toward a dorsal level plane inside a band
  S4 pinch/crease: pull toward a groove plane + inward along normal
  S5 smooth      : masked Laplacian over the union of touched verts
Symmetry: all fields are functions of |y| -> deltas are mirror-symmetric
by construction; residual asymmetry measured with a KD-tree.

Run: blender -b --python proto_sculpt.py   (renders: BLENDER_WORKBENCH)
"""
import bpy, bmesh, json
from mathutils import Vector, kdtree

ROOT = "/home/hatch/workspace/anthroforge-v2/model-craft/b18-sculpt/"
SRC = "/home/hatch/workspace/anthroforge-v2/model-craft/b10-blocking/wolf_blockout.blend"
R = {}
def rec(k, v):
    R[k] = v
    print("B18R", k, "=", v, flush=True)

def smoothstep(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)

# ---------------------------------------------------------------- setup render
def setup_render():
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_WORKBENCH'
    sc.render.resolution_x = 640; sc.render.resolution_y = 480
    sc.render.threads_mode = 'FIXED'; sc.render.threads = 2
    sh = sc.display.shading
    sh.light = 'STUDIO'; sh.color_type = 'SINGLE'
    sh.single_color = (0.72, 0.68, 0.62)
    sh.show_cavity = True; sh.cavity_type = 'WORLD'
    return sc

def add_cam(name, loc, target, ortho=1.25):
    cd = bpy.data.cameras.new(name); cd.type = 'ORTHO'; cd.ortho_scale = ortho
    co = bpy.data.objects.new(name, cd); bpy.context.scene.collection.objects.link(co)
    co.location = loc
    d = (Vector(target) - Vector(loc))
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return co

def render(sc, cam, only, path):
    for o in sc.objects:
        o.hide_render = (o not in only)
    sc.camera = cam
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

# ---------------------------------------------------------------- open source
bpy.ops.wm.open_mainfile(filepath=SRC)
sc = setup_render()
cam_side = add_cam("CamSide", (0.0, -2.4, 0.62), (0.0, 0.0, 0.62))
cam_34 = add_cam("Cam34", (1.5, -1.5, 1.15), (0.0, 0.0, 0.58))

torso_names = ["Chest", "Belly", "Pelvis"]
prims = [bpy.context.scene.objects[n] for n in torso_names]
render(sc, cam_side, prims, ROOT + "renders/before_blockout_side.png")

# ---------------------------------------------------------------- stage B: fuse
for o in bpy.context.scene.objects: o.select_set(False)
for o in prims: o.select_set(True)
bpy.context.view_layer.objects.active = prims[0]
bpy.ops.object.join()
torso = bpy.context.active_object; torso.name = "Torso"
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
rec("joined_verts", len(torso.data.vertices))

torso.data.remesh_voxel_size = 0.018
bpy.ops.object.voxel_remesh()
rec("remeshed_verts", len(torso.data.vertices))
rec("remeshed_faces", len(torso.data.polygons))

bm = bmesh.new(); bm.from_mesh(torso.data)
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
rec("volume_fused_m3", round(bm.calc_volume(), 5))
xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
rec("bbox_fused", [round(max(xs)-min(xs),3), round(max(ys)-min(ys),3), round(max(zs)-min(zs),3)])
# keep a frozen copy of stage B for the file + before render
stageB = torso.copy(); stageB.data = torso.data.copy(); stageB.name = "Torso_fused_remesh"
sc.collection.objects.link(stageB)
render(sc, cam_side, [stageB], ROOT + "renders/before_sculpt_side.png")
render(sc, cam_34, [stageB], ROOT + "renders/before_sculpt_34.png")

# neighbours for the smooth pass (topology never changes after this)
nbrs = {v.index: [] for v in bm.verts}
for e in bm.edges:
    a, b = e.verts[0].index, e.verts[1].index
    nbrs[a].append(b); nbrs[b].append(a)

def symmetry_rmse(bm, sample_step=7):
    kd = kdtree.KDTree(len(bm.verts))
    for i, v in enumerate(bm.verts): kd.insert(v.co, i)
    kd.balance()
    errs = []
    for i, v in enumerate(bm.verts):
        if i % sample_step or v.co.y < 0.02: continue
        co, idx, dist = kd.find(Vector((v.co.x, -v.co.y, v.co.z)))
        errs.append(dist)
    errs.sort()
    if not errs: return None
    return dict(n=len(errs), median_mm=round(errs[len(errs)//2]*1000, 2),
                p90_mm=round(errs[int(len(errs)*0.9)]*1000, 2))
rec("symmetry_fused", symmetry_rmse(bm))

# ---------------------------------------------------------------- sculpt engine
touch = [0.0] * len(bm.verts)
stats = {}
def dist_seg(p, a, b):
    ab = b - a; t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length, t

def stroke_pass(name, lines, radius, strength, passes=1):
    bm.normal_update()
    total = [0.0] * len(bm.verts); cnt = 0; mx = 0.0
    for p in range(passes):
        for i, v in enumerate(bm.verts):
            q = Vector((v.co.x, abs(v.co.y), v.co.z))
            best = None
            for (a, b) in lines:
                d, t = dist_seg(q, a, b)
                if best is None or d < best: best = d
            w = smoothstep(radius, radius * 0.25, best)
            if w <= 0: continue
            dvec = v.normal * (strength * w)
            v.co += dvec
            total[i] += dvec.length; touch[i] = max(touch[i], w); cnt += 1; mx = max(mx, dvec.length)
    stats[name] = dict(verts_touched=cnt, max_disp_mm=round(mx*1000, 2),
                       mean_disp_mm=round(1000*sum(total)/max(1, sum(1 for t in total if t > 0)), 2))
    rec("stroke_" + name, stats[name])

V = Vector
# S1 clay strips: two layered bands along the chest side (shoulder/pec mass)
lines1 = [(V((0.02, 0.088, 0.565)), V((0.38, 0.088, 0.565))),
          (V((0.02, 0.088, 0.625)), V((0.38, 0.088, 0.625))),
          (V((0.02, 0.088, 0.685)), V((0.38, 0.088, 0.685)))]
stroke_pass("S1_clay_strips", lines1, radius=0.075, strength=0.0045, passes=3)

# S2 inflate/sag: belly volume, biased downward
bm.normal_update()
c = V((-0.05, 0.0, 0.47)); cnt = 0; mx = 0.0
for i, v in enumerate(bm.verts):
    d = V(((v.co.x-c.x)/0.24, (v.co.y)/0.115, (v.co.z-c.z)/0.105)).length
    w = smoothstep(1.0, 0.35, d)
    if w <= 0: continue
    dirv = (v.normal * 0.55 + V((0, 0, -1)) * 0.75).normalized()
    step = dirv * (0.020 * w); v.co += step
    touch[i] = max(touch[i], w); cnt += 1; mx = max(mx, step.length)
rec("stroke_S2_inflate_sag", dict(verts_touched=cnt, max_disp_mm=round(mx*1000, 2)))

# S3 scrape: level the dorsal band toward plane z=0.795
cnt = 0; mx = 0.0
for i, v in enumerate(bm.verts):
    if v.co.z < 0.735 or abs(v.co.y) > 0.075 or not (-0.45 < v.co.x < 0.40): continue
    w = smoothstep(0.075, 0.02, abs(v.co.y)) * smoothstep(0.735, 0.775, v.co.z)
    dz = (0.795 - v.co.z) * 0.55 * w
    v.co.z += dz; touch[i] = max(touch[i], w); cnt += 1; mx = max(mx, abs(dz))
rec("stroke_S3_scrape", dict(verts_touched=cnt, max_disp_mm=round(mx*1000, 2)))

# S4 pinch/crease: flank tuck groove at x=-0.20
bm.normal_update()
cnt = 0; mx = 0.0
for i, v in enumerate(bm.verts):
    dx = abs(v.co.x + 0.20)
    if dx > 0.05 or v.co.z > 0.68: continue
    w = smoothstep(0.05, 0.008, dx) * smoothstep(0.68, 0.60, v.co.z)
    if w <= 0: continue
    pull = (-0.20 - v.co.x) * 0.35 * w
    v.co.x += pull
    inward = v.normal * (-0.006 * w); v.co += inward
    touch[i] = max(touch[i], w); cnt += 1; mx = max(mx, abs(pull) + inward.length)
rec("stroke_S4_pinch_crease", dict(verts_touched=cnt, max_disp_mm=round(mx*1000, 2)))

# S5 smooth: masked Laplacian, 3 iterations over touched verts
for it in range(3):
    delta = {}
    for i, v in enumerate(bm.verts):
        if touch[i] <= 0.02 or not nbrs[i]: continue
        avg = V((0, 0, 0))
        for j in nbrs[i]: avg += bm.verts[j].co
        avg /= len(nbrs[i])
        delta[i] = (avg - v.co) * (0.35 * touch[i])
    for i, d in delta.items(): bm.verts[i].co += d
rec("stroke_S5_smooth", dict(verts_blended=sum(1 for t in touch if t > 0.02), iterations=3))

bm.to_mesh(torso.data); torso.data.update()
torso.name = "Torso_sculpted"
rec("volume_sculpted_m3", round(bm.calc_volume(), 5))
rec("vol_delta_pct", round(100 * (bm.calc_volume() - R["volume_fused_m3"]) / R["volume_fused_m3"], 2))
xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
rec("bbox_sculpted", [round(max(xs)-min(xs),3), round(max(ys)-min(ys),3), round(max(zs)-min(zs),3)])
rec("symmetry_sculpted", symmetry_rmse(bm))

render(sc, cam_side, [torso], ROOT + "renders/after_sculpt_side.png")
render(sc, cam_34, [torso], ROOT + "renders/after_sculpt_34.png")
stageB.hide_render = True
bpy.ops.wm.save_as_mainfile(filepath=ROOT + "prototype_sculpt.blend")
with open(ROOT + "work/proto_results.json", "w") as f:
    json.dump(R, f, indent=1, default=str)
print("B18 PROTO DONE", flush=True)
