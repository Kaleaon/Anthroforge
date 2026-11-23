# A16 — Two-layer fur prototype (AnthroForge fur-craft wave)
# One wolf torso.back patch built twice from the SAME guard generation:
#   patch A = guard hairs only
#   patch B = guard hairs + undercoat layer (shorter, denser, paler, crimped)
# A centre parting band (|x| < 0.02) carries NO guard roots on either patch:
# on A the parting shows skin; on B it shows undercoat. That is the read
# the prototype exists to compare.
# Parameters: A19 species.wolf.coat torso.back (guard 0.065 m, agouti) +
# A11 wolf undercoat profile (near-solid pale warm grey, distance #9a8d78).
# Run: blender -b --python build_twolayer.py   (renders + saves .blend)

import bpy
import numpy as np
import math, os, sys, time

rng = np.random.default_rng(1616)

OUT = os.path.expanduser("~/workspace/anthroforge-v2/fur-craft/a16-twolayer")
RENDERS = os.path.join(OUT, "renders")
os.makedirs(RENDERS, exist_ok=True)

# ---------------------------------------------------------------- patch surface
# Gentle dome (a flank/back section). z defined analytically so strand roots
# sit exactly on the mesh.
PX, PY = 0.26, 0.19            # half-extents (m)
def surf_z(x, y):
    return 0.052 * (1.0 - (x / 0.31) ** 2) * (1.0 - (y / 0.25) ** 2)
def surf_n(x, y):
    dzdx = 0.052 * (-2.0 * x / 0.31 ** 2) * (1.0 - (y / 0.25) ** 2)
    dzdy = 0.052 * (1.0 - (x / 0.31) ** 2) * (-2.0 * y / 0.25 ** 2)
    n = np.array([-dzdx, -dzdy, 1.0])
    return n / np.linalg.norm(n)

def build_patch_mesh(name, skin_rgb):
    nx, ny = 78, 57
    xs = np.linspace(-PX, PX, nx)
    ys = np.linspace(-PY, PY, ny)
    verts, faces = [], []
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            verts.append((x, y, surf_z(x, y)))
    for j in range(ny - 1):
        for i in range(nx - 1):
            a = j * nx + i; b = a + 1; c = a + nx; d = c + 1
            faces.append((a, b, d, c))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    m = bpy.data.materials.new(name + "_skin")
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = tuple(skin_rgb) + (1.0,)  # linear values
    bsdf.inputs["Roughness"].default_value = 0.8
    me.materials.append(m)
    return ob

# ---------------------------------------------------------------- strand gen
def sample_roots(spacing, band_exclude=None):
    """Jittered-grid roots on the patch. band_exclude: half-width of a centre
    strip (along x) to leave empty (the parting). Rim taper thins edges."""
    pts = []
    xs = np.arange(-PX + spacing * 0.5, PX, spacing)
    ys = np.arange(-PY + spacing * 0.5, PY, spacing)
    for y in ys:
        for x in xs:
            jx = x + rng.uniform(-0.5, 0.5) * spacing
            jy = y + rng.uniform(-0.5, 0.5) * spacing
            if abs(jx) > PX - 0.004 or abs(jy) > PY - 0.004:
                continue
            if band_exclude is not None and abs(jx) < band_exclude:
                continue
            # rim taper: thin out near the patch edge so it doesn't look cut
            edge = min(PX - abs(jx), PY - abs(jy))
            keep = min(1.0, max(0.15, edge / 0.014))
            if rng.random() > keep:
                continue
            pts.append((jx, jy))
    return np.array(pts)

def grow_strands(roots, length, length_var, theta_root, theta_tip,
                 crimp_amp=0.0, crimp_cycles=0.0, npts=8, yaw=0.10):
    """Integrate polylines by an exit-angle profile: the strand leaves the
    skin at theta_root (degrees from the surface, along the flow direction
    toward -Y with a parting-aware outward lean near x=0) and eases to
    theta_tip (negative = tips press back toward the surface — the low
    shingled arc of a lying coat, NOT a hoop)."""
    out = np.empty((len(roots), npts, 3), dtype=np.float64)
    for k, (x, y) in enumerate(roots):
        n = surf_n(x, y)
        # flow: project world -Y onto tangent plane; near the parting, lean
        # away from the centre line so the coat falls open on both sides.
        f = np.array([0.0, -1.0, 0.0])
        f = f - n * np.dot(f, n)
        f /= np.linalg.norm(f)
        if abs(x) < 0.07:
            side = 1.0 if x >= 0 else -1.0
            lean = side * (1.0 - abs(x) / 0.07) * 0.55
            fx = np.array([1.0, 0.0, 0.0]) - n * n[0]
            fx /= np.linalg.norm(fx)
            f = f + fx * lean
            f /= np.linalg.norm(f)
        # per-strand yaw noise — breaks the grid rows into organic flow
        a = rng.uniform(-yaw, yaw)
        perp0 = np.cross(n, f)
        f = f * math.cos(a) + perp0 * math.sin(a)
        f /= np.linalg.norm(f)
        L = length * (1.0 + rng.uniform(-length_var, length_var))
        step = L / (npts - 1)
        phase = rng.uniform(0, 2 * math.pi)
        # crimp axis: horizontal perpendicular to strand direction
        perp = np.cross(f, n)
        pl = np.linalg.norm(perp)
        perp = perp / pl if pl > 1e-9 else np.array([1.0, 0.0, 0.0])
        p = np.array([x, y, surf_z(x, y)]) + n * 0.0006
        out[k, 0] = p
        for i in range(1, npts):
            s = i / (npts - 1)
            th = math.radians(theta_root + (theta_tip - theta_root) * (s ** 0.85))
            d = f * math.cos(th) + n * math.sin(th)
            p = p + d * step
            q = p.copy()
            if crimp_amp > 0:
                off = crimp_amp * math.sin(2 * math.pi * crimp_cycles * s + phase) * (0.3 + 0.7 * s)
                q = q + perp * off + n * (0.4 * abs(off))
            out[k, i] = q
    return out

def make_hair(name, strands, r_root, r_tip, material):
    n, P, _ = strands.shape
    cd = bpy.data.hair_curves.new(name)
    cd.add_curves([P] * n)
    cd.points.foreach_set("position", strands.astype(np.float32).ravel().tolist())
    t = np.linspace(0, 1, P, dtype=np.float32)
    rad = np.tile(r_root * (1.0 - (1.0 - r_tip / r_root) * t), n)
    if "radius" not in cd.attributes:
        cd.attributes.new("radius", "FLOAT", "POINT")
    cd.attributes["radius"].data.foreach_set("value", rad.tolist())
    cd.materials.append(material)
    ob = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(ob)
    return ob

# ---------------------------------------------------------------- hair material
def mel(c):
    lum = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    return max(0.03, min(1.0, 1.05 - lum))

def sock(node, name):
    """Find a socket by display name via iteration. (Blender 5.2.3 quirk:
    the Hair Principled node's melanin-family sockets list 'Melanin' in
    .inputs but raise KeyError on name lookup — identifiers differ.)"""
    for s in node.inputs:
        if s.name == name:
            return s
    raise KeyError(name)

def hair_material(name, stops, tint_rgb, roughness):
    """Principled Hair, MELANIN parametrization (A7's verified route: COLOR
    blows out to white at density). stops = [(pos, srgb_colour)] root->tip,
    carried as melanin amounts on a ramp; Tint colours the whole strand."""
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    bsdf = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    bsdf.parametrization = "MELANIN"   # default COLOR silently ignores Melanin/Tint
    nt.links.new(bsdf.outputs["BSDF"], nt.nodes["Material Output"].inputs["Surface"])
    info = nt.nodes.new("ShaderNodeHairInfo")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    els = ramp.color_ramp.elements
    els[0].position = stops[0][0]
    els[0].color = (mel(stops[0][1]),) * 3 + (1.0,)
    els[1].position = stops[-1][0]
    els[1].color = (mel(stops[-1][1]),) * 3 + (1.0,)
    for pos, col in stops[1:-1]:
        e = els.new(pos)
        e.color = (mel(col),) * 3 + (1.0,)
    nt.links.new(info.outputs["Intercept"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], sock(bsdf, "Melanin"))
    sock(bsdf, "Tint").default_value = tuple(min(1.0, c ** 0.75) for c in tint_rgb) + (1.0,)
    sock(bsdf, "Melanin Redness").default_value = 0.25
    sock(bsdf, "Roughness").default_value = roughness
    return m

# ---------------------------------------------------------------- scene setup
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.samples = 64
sc.cycles.use_denoising = True
sc.cycles.device = "CPU"
try:
    sc.render.hair_type = "STRAND"   # round strands; 5.2 default STRIP = ribbons
    print("hair_type =", sc.render.hair_type, flush=True)
except Exception as e:
    print("hair_type set failed:", e, flush=True)
TEST = "--test" in sys.argv
if TEST:
    sc.render.resolution_x = 360
    sc.render.resolution_y = 360
    sc.cycles.samples = 16
sc.render.resolution_x = 720
sc.render.resolution_y = 720
sc.render.threads_mode = "FIXED"
sc.render.threads = 2
w = bpy.data.worlds.new("Studio")
sc.world = w
w.node_tree.nodes["Background"].inputs[0].default_value = (0.13, 0.13, 0.145, 1.0)
w.node_tree.nodes["Background"].inputs[1].default_value = 1.0

def area_light(name, loc, energy, size=0.6):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = energy
    ld.shape = "DISK"
    ld.size = size
    ob = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(ob)
    ob.location = loc
    from mathutils import Vector
    d = Vector((0, 0, 0.03)) - ob.location
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    return ob

area_light("Key", (0.55, -0.65, 0.85), 26.0)
area_light("Fill", (-0.75, 0.15, 0.35), 6.0)
area_light("Rim", (0.1, 0.75, 0.55), 20.0)

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
sc.camera = cam
from mathutils import Vector
def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

# ---------------------------------------------------------------- build fur
t0 = time.time()
patchA = build_patch_mesh("PatchA_guardonly", (0.035, 0.025, 0.018))
patchB = build_patch_mesh("PatchB_twolayer", (0.035, 0.025, 0.018))

# guard: A19 wolf torso.back — 0.065 m, agouti bands (A11 profile colours)
guard_mat = hair_material(
    "GuardHair",
    [(0.0, (0.22, 0.192, 0.169)),   # root #38312b (A11 ground)
     (0.34, (0.663, 0.494, 0.310)), # pulse band #a97e4f
     (0.60, (0.851, 0.769, 0.604)), # pulse band #d9c49a
     (0.90, (0.125, 0.110, 0.098)), # tip #201c19
     (1.0, (0.125, 0.110, 0.098))],
    (0.30, 0.20, 0.11), 0.45)
# undercoat: A11 — near-solid pale warm grey (distance colour #9a8d78)
under_mat = hair_material(
    "UndercoatHair",
    [(0.0, (0.42, 0.36, 0.29)),
     (1.0, (0.70, 0.64, 0.54))],
    (0.55, 0.50, 0.42), 0.68)

guard_roots = sample_roots(0.0088, band_exclude=0.02)
guard_strands = grow_strands(guard_roots, length=0.070, length_var=0.30,
                             theta_root=30.0, theta_tip=-6.0, npts=8)
print(f"guard strands: {len(guard_roots)}")

under_roots = sample_roots(0.0058, band_exclude=None)
under_strands = grow_strands(under_roots, length=0.030, length_var=0.35,
                             theta_root=58.0, theta_tip=12.0, crimp_amp=0.0016,
                             crimp_cycles=2.2, npts=5, yaw=0.20)
print(f"undercoat strands: {len(under_roots)}")

gA = make_hair("A_Guard", guard_strands, 0.00075, 0.00012, guard_mat)
gB = make_hair("B_Guard", guard_strands, 0.00075, 0.00012, guard_mat)
uB = make_hair("B_Undercoat", under_strands, 0.0004, 0.00008, under_mat)

if not TEST:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "prototype_twolayer.blend"))
print(f"build time {time.time()-t0:.1f}s", flush=True)

# ---------------------------------------------------------------- renders
VIEWS = {
    "close":   (Vector((0.03, -0.155, 0.175)), Vector((0.0, 0.012, 0.045)), 55),
    "medium":  (Vector((0.10, -0.52, 0.42)),   Vector((0.0, 0.0, 0.03)),    50),
    "grazing": (Vector((-0.05, -0.315, 0.030)), Vector((0.02, 0.10, 0.052)), 60),
}
SETS = {
    "guardonly": [patchA, gA],
    "twolayer":  [patchB, gB, uB],
}
ALL = [patchA, patchB, gA, gB, uB]
for label, objs in SETS.items():
    for ob in ALL:
        ob.hide_render = ob not in objs
    for view, (pos, tgt, lens) in VIEWS.items():
        if TEST and not (label == "guardonly" and view == "close"):
            continue
        cam.location = pos
        cam_data.lens = lens
        aim(cam, tgt)
        sc.render.filepath = os.path.join(RENDERS, f"{label}_{view}.png")
        t1 = time.time()
        bpy.ops.render.render(write_still=True)
        print(f"render {label}_{view}: {time.time()-t1:.1f}s")
print("ALL DONE")
