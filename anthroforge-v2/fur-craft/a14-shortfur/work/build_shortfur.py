"""A14 — Short fur & fuzz comparison build.

Opens neutral base head v3, bakes ONE shared muzzle+cheek zone mask
(vertex colour attribute 'A14Zone') onto TissueHead + Jaw, then lays out
four copies of the head in a row:
  BASE  - flat coat material (control)
  T1    - velvet/fresnel fuzz (Principled sheen + fresnel rim, zone-driven)
  T2    - shell micro-layers (14 normal-offset shells, 3D-noise strand alpha)
  T3    - texture-only directional pelt (streak albedo + normal + roughness)
Saves shortfur_compare.blend and fires the shots listed in SHOTS.
Usage: blender -b --python build_shortfur.py -- [build|render|all]
"""
import bpy, math, os, sys, json
from mathutils import Vector

ROOT = "/home/hatch/workspace/anthroforge-v2/fur-craft/a14-shortfur"
WORK = ROOT + "/work"
SRC = "/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.blend"
HDRI = os.path.expanduser("~/workspace/bodies-3d/parts-library/polyhaven/"
                          "photo-studio-01-hdri/photo_studio_01_2k.hdr")
PHASE = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "all"

# ---------------------------------------------------------------- palette
def lin(hexs):
    return tuple((int(hexs[i:i + 2], 16) / 255.0) ** 2.2 for i in (0, 2, 4)) + (1.0,)
COAT   = lin("7d6248")   # tawny coat base
ROOTC  = lin("3d2d1d")   # under-shell root
SROOT  = lin("54402a")   # shell root
STIP   = lin("a5855e")   # shell tip
FUZZ   = lin("cbb28a")   # fresnel fuzz tint
SHEENC = lin("d8c096")   # sheen colour

# ---------------------------------------------------------------- zone mask
def sstep(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)

def ell(px, py, pz, c, r):
    return math.sqrt(((px - c[0]) / r[0]) ** 2 + ((py - c[1]) / r[1]) ** 2 +
                     ((pz - c[2]) / r[2]) ** 2)

def zone_mask(p):
    x, y, z = p
    m = 1.0 - sstep(0.72, 1.05, ell(x, y, z, (0, 0.335, -0.075), (0.235, 0.205, 0.205)))  # muzzle
    for sx in (1, -1):  # cheeks (masseter + zygomatic)
        m = max(m, 1.0 - sstep(0.70, 1.05, ell(x, y, z, (sx * 0.205, 0.085, -0.015),
                                               (0.125, 0.235, 0.205))))
    m = max(m, 1.0 - sstep(0.70, 1.05, ell(x, y, z, (0, 0.40, -0.285), (0.15, 0.13, 0.11))))  # chin front
    m *= sstep(0.55, 0.95, ell(x, y, z, (0, 0.487, -0.186), (0.055, 0.045, 0.050)))   # nose leather out
    for sx in (1, -1):  # eyes out
        m *= sstep(0.60, 1.00, ell(x, y, z, (sx * 0.134, 0.075, 0.010), (0.095, 0.095, 0.095)))
    return min(max(m, 0.0), 1.0)

# ---------------------------------------------------------------- node helpers
def principled(nt):
    return nt.nodes["Principled BSDF"]

def new_mat(name):
    m = bpy.data.materials.new(name)
    return m

def zone_node(nt, x, y):
    at = nt.nodes.new("ShaderNodeAttribute"); at.attribute_name = "A14Zone"
    at.location = (x, y)
    sep = nt.nodes.new("ShaderNodeSeparateColor"); sep.location = (x + 180, y)
    nt.links.new(at.outputs["Color"], sep.inputs["Color"])
    return sep.outputs["Red"]

# ---------------------------------------------------------------- build
bpy.ops.wm.open_mainfile(filepath=SRC)
scene = bpy.context.scene

KEEP_SURFACE = ["TissueHead", "Jaw", "Ear_L", "Ear_R", "Eyelid_L", "Eyelid_R",
                "LidMargin_L", "LidMargin_R"]
KEEP_ORIG = ["Eyeball_L", "Eyeball_R", "Iris_L", "Iris_R", "Pupil_L", "Pupil_R",
             "NoseLeather"]
for ob in list(bpy.data.objects):
    if ob.name not in KEEP_SURFACE + KEEP_ORIG:
        bpy.data.objects.remove(ob, do_unlink=True)

# bake the shared zone mask (world coords, heads at origin)
for name in ("TissueHead", "Jaw"):
    ob = bpy.data.objects[name]
    me = ob.data
    attr = me.color_attributes.new(name="A14Zone", type='FLOAT_COLOR', domain='POINT')
    mw = ob.matrix_world
    for i, v in enumerate(me.vertices):
        w = zone_mask(mw @ v.co)
        attr.data[i].color = (w, w, w, 1.0)
    me.update()

# ---- materials
mat_base = new_mat("A14_Base")
p = principled(mat_base.node_tree)
p.inputs["Base Color"].default_value = COAT
p.inputs["Roughness"].default_value = 0.95

mat_root = new_mat("A14_Root")
p = principled(mat_root.node_tree)
p.inputs["Base Color"].default_value = ROOTC
p.inputs["Roughness"].default_value = 1.0

# T1 velvet fuzz
mat_t1 = new_mat("A14_T1_Velvet")
nt = mat_t1.node_tree; p = principled(nt)
p.inputs["Roughness"].default_value = 0.90
p.inputs["Sheen Roughness"].default_value = 0.50
p.inputs["Sheen Tint"].default_value = SHEENC
zone = zone_node(nt, -900, 300)
lw = nt.nodes.new("ShaderNodeLayerWeight"); lw.location = (-900, 40)
ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.location = (-700, 40)
ramp.color_ramp.elements[0].position = 0.55
ramp.color_ramp.elements[1].position = 0.98
nt.links.new(lw.outputs["Facing"], ramp.inputs["Fac"])
mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.location = (-500, 160)
nt.links.new(ramp.outputs["Color"], mul.inputs[0]); nt.links.new(zone, mul.inputs[1])
mul2 = nt.nodes.new("ShaderNodeMath"); mul2.operation = 'MULTIPLY'; mul2.location = (-320, 160)
mul2.inputs[1].default_value = 0.60
nt.links.new(mul.outputs["Value"], mul2.inputs[0])
mixc = nt.nodes.new("ShaderNodeMixRGB"); mixc.location = (-140, 240)
mixc.inputs[1].default_value = COAT; mixc.inputs[2].default_value = FUZZ
nt.links.new(mul2.outputs["Value"], mixc.inputs["Fac"])
nt.links.new(mixc.outputs["Color"], p.inputs["Base Color"])
sh = nt.nodes.new("ShaderNodeMath"); sh.operation = 'MULTIPLY_ADD'; sh.location = (-500, 330)
sh.inputs[1].default_value = 0.85; sh.inputs[2].default_value = 0.15
nt.links.new(zone, sh.inputs[0])
nt.links.new(sh.outputs["Value"], p.inputs["Sheen Weight"])

# T3 texture pelt
def img_node(nt, path, srgb, x, y):
    n = nt.nodes.new("ShaderNodeTexImage")
    n.image = bpy.data.images.load(path)
    n.image.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
    n.location = (x, y)
    return n
mat_t3 = new_mat("A14_T3_Pelt")
nt = mat_t3.node_tree
flat = nt.nodes.new("ShaderNodeBsdfPrincipled"); flat.location = (0, -260)
flat.inputs["Base Color"].default_value = COAT
flat.inputs["Roughness"].default_value = 0.95
pelt = principled(nt); pelt.location = (0, 320)
tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-1100, 320)
mp = nt.nodes.new("ShaderNodeMapping"); mp.location = (-920, 320)
mp.inputs["Scale"].default_value = (3.0, 3.0, 3.0)
nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
alb = img_node(nt, WORK + "/tex_pelt_albedo.png", True, -700, 460)
nrm = img_node(nt, WORK + "/tex_pelt_normal.png", False, -700, 200)
rou = img_node(nt, WORK + "/tex_pelt_rough.png", False, -700, -40)
for im in (alb, nrm, rou):
    nt.links.new(mp.outputs["Vector"], im.inputs["Vector"])
nt.links.new(alb.outputs["Color"], pelt.inputs["Base Color"])
nm = nt.nodes.new("ShaderNodeNormalMap"); nm.location = (-380, 200)
nm.inputs["Strength"].default_value = 0.85
nt.links.new(nrm.outputs["Color"], nm.inputs["Color"])
nt.links.new(nm.outputs["Normal"], pelt.inputs["Normal"])
nt.links.new(rou.outputs["Color"], pelt.inputs["Roughness"])
zone3 = zone_node(nt, -700, 640)
mixs = nt.nodes.new("ShaderNodeMixShader"); mixs.location = (320, 60)
out = nt.nodes["Material Output"]; out.location = (540, 60)
nt.links.new(zone3, mixs.inputs[0])
nt.links.new(flat.outputs["BSDF"], mixs.inputs[1])
nt.links.new(pelt.outputs["BSDF"], mixs.inputs[2])
nt.links.new(mixs.outputs["Shader"], out.inputs["Surface"])
# (default principled->output link replaced by mix above)

# T2 shell materials
NSHELL = 14
SHELL_LEN = 0.012
shell_mats = []
for i in range(NSHELL):
    t = i / (NSHELL - 1)
    m = new_mat(f"A14_T2_Shell_{i:02d}")
    nt = m.node_tree; p = principled(nt)
    p.inputs["Roughness"].default_value = 0.92
    out = nt.nodes["Material Output"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-1100, 0)
    noi = nt.nodes.new("ShaderNodeTexNoise"); noi.location = (-920, 120)
    noi.inputs["Scale"].default_value = 170.0
    noi.inputs["Detail"].default_value = 2.5
    noi.inputs["Roughness"].default_value = 0.65
    nt.links.new(tc.outputs["Object"], noi.inputs["Vector"])
    thr = 0.20 + 0.60 * t
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.location = (-700, 200)
    ramp.color_ramp.elements[0].position = max(thr - 0.07, 0.0)
    ramp.color_ramp.elements[1].position = min(thr + 0.09, 1.0)
    nt.links.new(noi.outputs["Fac"], ramp.inputs["Fac"])
    zoneS = zone_node(nt, -1100, 420)
    k1 = nt.nodes.new("ShaderNodeMath"); k1.operation = 'MULTIPLY'; k1.location = (-460, 260)
    k1.inputs[1].default_value = 1.0 - 0.12 * t
    nt.links.new(ramp.outputs["Color"], k1.inputs[0])
    k2 = nt.nodes.new("ShaderNodeMath"); k2.operation = 'MULTIPLY'; k2.location = (-280, 260)
    nt.links.new(k1.outputs["Value"], k2.inputs[0]); nt.links.new(zoneS, k2.inputs[1])
    # root->tip colour with per-strand jitter from the same noise
    jit = nt.nodes.new("ShaderNodeMath"); jit.operation = 'MULTIPLY_ADD'; jit.location = (-700, -60)
    jit.inputs[0].default_value = 0.0  # placeholder, rewired below
    jit.inputs[1].default_value = 0.30; jit.inputs[2].default_value = t - 0.15
    nt.links.new(noi.outputs["Fac"], jit.inputs[0]); jit.inputs[0].default_value = 0.0
    # jit computes noise*0.30 + (t-0.15); clamp to [0,1]
    cmax = nt.nodes.new("ShaderNodeMath"); cmax.operation = 'MAXIMUM'; cmax.location = (-520, -60)
    cmax.inputs[1].default_value = 0.0
    nt.links.new(jit.outputs["Value"], cmax.inputs[0])
    cmin = nt.nodes.new("ShaderNodeMath"); cmin.operation = 'MINIMUM'; cmin.location = (-380, -60)
    cmin.inputs[1].default_value = 1.0
    nt.links.new(cmax.outputs["Value"], cmin.inputs[0])
    mixc = nt.nodes.new("ShaderNodeMixRGB"); mixc.location = (-160, 60)
    mixc.inputs[1].default_value = SROOT; mixc.inputs[2].default_value = STIP
    nt.links.new(cmin.outputs["Value"], mixc.inputs["Fac"])
    nt.links.new(mixc.outputs["Color"], p.inputs["Base Color"])
    transp = nt.nodes.new("ShaderNodeBsdfTransparent"); transp.location = (-160, 320)
    mixsh = nt.nodes.new("ShaderNodeMixShader"); mixsh.location = (80, 200)
    nt.links.new(k2.outputs["Value"], mixsh.inputs[0])
    nt.links.new(transp.outputs["BSDF"], mixsh.inputs[1])
    nt.links.new(p.outputs["BSDF"], mixsh.inputs[2])
    for lnk in list(out.inputs["Surface"].links):
        nt.links.remove(lnk)
    nt.links.new(mixsh.outputs["Shader"], out.inputs["Surface"])
    try:
        m.surface_render_method = 'DITHERED'
    except Exception:
        pass
    shell_mats.append(m)

# zone-viz material (debug mask check)
mat_viz = new_mat("A14_ZoneViz")
nt = mat_viz.node_tree
em = nt.nodes.new("ShaderNodeEmission"); em.location = (0, 0)
em.inputs["Strength"].default_value = 1.6
zoneV = zone_node(nt, -500, 0)
comb = nt.nodes.new("ShaderNodeCombineColor"); comb.location = (-200, 0)
nt.links.new(zoneV, comb.inputs["Red"])
inv = nt.nodes.new("ShaderNodeMath"); inv.operation = 'SUBTRACT'; inv.location = (-500, -160)
inv.inputs[0].default_value = 1.0
nt.links.new(zoneV, inv.inputs[1])
sc = nt.nodes.new("ShaderNodeMath"); sc.operation = 'MULTIPLY'; sc.location = (-320, -160)
sc.inputs[1].default_value = 0.30
nt.links.new(inv.outputs["Value"], sc.inputs[0])
nt.links.new(sc.outputs["Value"], comb.inputs["Blue"])
nt.links.new(comb.outputs["Color"], em.inputs["Color"])
nt.links.new(em.outputs["Emission"], nt.nodes["Material Output"].inputs["Surface"])

# ---- lay out the four heads
GROUPS = [("ctrl", -2.55, "BASE"), ("t1", -0.85, "T1 VELVET"),
          ("t2", 0.85, "T2 SHELLS"), ("t3", 2.55, "T3 PELT")]
orig = {n: bpy.data.objects[n] for n in KEEP_SURFACE + KEEP_ORIG}

def assign(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)

stats = {}
for gname, xoff, _label in GROUPS:
    copies = {}
    for n in KEEP_SURFACE + KEEP_ORIG:
        src = orig[n]
        cp = src.copy()
        if n in KEEP_SURFACE:
            cp.data = src.data.copy()
        cp.location = src.location + Vector((xoff, 0, 0))
        cp.name = f"A14_{gname}_{n}"
        scene.collection.objects.link(cp)
        copies[n] = cp
    if gname == "ctrl":
        for n in KEEP_SURFACE: assign(copies[n], mat_base)
    elif gname == "t1":
        for n in KEEP_SURFACE: assign(copies[n], mat_t1)
    elif gname == "t3":
        for n in KEEP_SURFACE: assign(copies[n], mat_t3)
    elif gname == "t2":
        for n in ("TissueHead", "Jaw"): assign(copies[n], mat_root)
        for n in KEEP_SURFACE:
            if n not in ("TissueHead", "Jaw"): assign(copies[n], mat_base)
        # shells from this group's tissue + jaw (local coords; object offset matches)
        nverts = 0
        for base_name in ("TissueHead", "Jaw"):
            bobj = copies[base_name]
            bme = bobj.data
            polys = [[v for v in p.vertices] for p in bme.polygons]
            uv = None
            if bme.uv_layers:
                uv = [tuple(bme.uv_layers.active.data[i].uv) for i in range(len(bme.loops))]
            loops = [i for p in bme.polygons for i in p.loop_indices]
            zattr = bme.color_attributes["A14Zone"]
            zvals = [tuple(zattr.data[i].color) for i in range(len(bme.vertices))]
            for i in range(NSHELL):
                t = i / (NSHELL - 1)
                off = t * SHELL_LEN
                verts = [tuple(v.co + v.normal * off) for v in bme.vertices]
                me = bpy.data.meshes.new(f"A14_t2_{base_name}_shell{i:02d}")
                me.from_pydata(verts, [], polys)
                me.update()
                if uv:
                    layer = me.uv_layers.new(name="UVMap")
                    for li, src_li in enumerate(loops):
                        layer.data[li].uv = uv[src_li]
                za = me.color_attributes.new(name="A14Zone", type='FLOAT_COLOR', domain='POINT')
                for vi, c in enumerate(zvals):
                    za.data[vi].color = c
                me.materials.append(shell_mats[i])
                so = bpy.data.objects.new(f"A14_t2_{base_name}_shell{i:02d}", me)
                so.location = bobj.location
                scene.collection.objects.link(so)
                nverts += len(verts)
        stats["t2_shell_verts"] = nverts
    stats[gname] = sum(len(copies[n].data.vertices) for n in KEEP_SURFACE)

for n in KEEP_SURFACE + KEEP_ORIG:
    bpy.data.objects.remove(orig[n], do_unlink=True)

# ---- labels
def look_at(obj, target):
    obj.rotation_euler = (target - obj.location).to_track_quat('-Z', 'Y').to_euler()
for _g, xoff, label in GROUPS:
    cd = bpy.data.curves.new("lbl", 'FONT')
    cd.body = label; cd.size = 0.115; cd.align_x = 'CENTER'
    lo = bpy.data.objects.new("A14_label_" + label, cd)
    lo.location = (xoff, 0.35, -0.68)
    scene.collection.objects.link(lo)
    look_at(lo, Vector((xoff, 5.0, -0.55)))
    lm = new_mat("A14_LabelMat")
    principled(lm.node_tree).inputs["Base Color"].default_value = (0.75, 0.75, 0.78, 1.0)
    lo.data.materials.append(lm)

# ---- floor + world + rim light (v3 studio rig)
floor = bpy.data.objects.new("A14_Floor", bpy.data.meshes.new("A14_Floor"))
bpy.context.scene.collection.objects.link(floor)
import bmesh
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=30)
bm.to_mesh(floor.data); bm.free()
floor.location = (0, 0, -0.62)
fm = new_mat("A14_FloorMat")
principled(fm.node_tree).inputs["Base Color"].default_value = (0.028, 0.028, 0.030, 1.0)
principled(fm.node_tree).inputs["Roughness"].default_value = 1.0
floor.data.materials.append(fm)

world = bpy.data.worlds.new('W'); scene.world = world
env = world.node_tree.nodes.new('ShaderNodeTexEnvironment')
env.image = bpy.data.images.load(HDRI)
bg = world.node_tree.nodes['Background']
world.node_tree.links.new(env.outputs['Color'], bg.inputs['Color'])
bg.inputs['Strength'].default_value = 0.85
bg2 = world.node_tree.nodes.new('ShaderNodeBackground')
bg2.inputs['Color'].default_value = (0.145, 0.145, 0.15, 1.0)
lp = world.node_tree.nodes.new('ShaderNodeLightPath')
mixw = world.node_tree.nodes.new('ShaderNodeMixShader')
wo = world.node_tree.nodes['World Output']
world.node_tree.links.new(lp.outputs['Is Camera Ray'], mixw.inputs['Fac'])
world.node_tree.links.new(bg.outputs['Background'], mixw.inputs[1])
world.node_tree.links.new(bg2.outputs['Background'], mixw.inputs[2])
world.node_tree.links.new(mixw.outputs['Shader'], wo.inputs['Surface'])

rim = bpy.data.objects.new("A14_Rim", bpy.data.lights.new("A14_Rim", 'AREA'))
rim.data.energy = 900; rim.data.shape = 'DISK'; rim.data.size = 3.0
rim.location = (0, -3.0, 1.9)
scene.collection.objects.link(rim)
look_at(rim, Vector((0, 0, 0)))

# ---- cameras
def make_cam(name, pos, target, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    co = bpy.data.objects.new(name, cd)
    scene.collection.objects.link(co)
    co.location = pos; look_at(co, target)
    return co
CAM_LINEUP = make_cam("CamLineup", Vector((0, 6.6, 1.25)), Vector((0, 0, -0.02)), 30)
CAMS_CLOSE = {g: make_cam("CamClose_" + g, Vector((x + 0.58, 0.98, 0.24)),
                          Vector((x + 0.10, 0.30, -0.05)), 72)
              for g, x, _ in GROUPS}
CAM_GRAZE = make_cam("CamGrazeT2", Vector((0.85 + 1.5, 0.30, 0.02)),
                     Vector((0.85, 0.02, -0.02)), 55)

scene.render.engine = 'CYCLES'
scene.cycles.use_denoising = True
scene.cycles.transparent_max_bounces = 32
os.makedirs(ROOT + "/renders", exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=ROOT + "/shortfur_compare.blend")
with open(WORK + "/stats.json", "w") as f:
    json.dump(stats, f, indent=1)
print("A14 BUILD OK", stats)

# ---- shots
def shoot(cam, name, w, h, samples):
    scene.camera = cam
    scene.render.resolution_x = w; scene.render.resolution_y = h
    scene.cycles.samples = samples
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = ROOT + "/renders/" + name
    bpy.ops.render.render(write_still=True)
    print("SHOT", name)

if PHASE in ("build", "all"):
    vl = bpy.context.view_layer
    vl.material_override = mat_viz
    shoot(CAM_LINEUP, "debug_zone_mask", 720, 380, 16)
    vl.material_override = None
    shoot(CAM_LINEUP, "test_lineup", 720, 380, 24)
    shoot(CAMS_CLOSE["t2"], "test_close_t2", 512, 512, 24)
if PHASE in ("render", "all"):
    shoot(CAM_LINEUP, "render_lineup", 1680, 880, 96)
    for g, _x, _l in GROUPS:
        shoot(CAMS_CLOSE[g], f"render_close_{g}", 880, 880, 128)
    shoot(CAM_GRAZE, "render_grazing_t2", 1200, 820, 96)
print("A14 DONE")
