"""Build Kaleaon unique-anatomy parts on the sacdrape host.

Inputs : bodies-3d/kaleaon-sacdrape/kaleaon_sacdrape.blend (host, untouched)
Outputs: kaleaon_anatomy_parts.blend in this folder (host + parts replacing
         the original Sac/Shaft objects), work/build_numbers.json
Canon anchors (measured on the host, sacdrape REPORT.md):
  sac volume 209.46 L, bottom z 0.031 m, root z 1.005; shafts bone-articulated
  (Shaft_N_Base/Tip on CC_Base_Pelvis), NO erection morphs.
"""
import bpy, bmesh, json, math
import numpy as np
from mathutils import Vector

SRC = "/home/hatch/workspace/bodies-3d/kaleaon-sacdrape/kaleaon_sacdrape.blend"
OUT = "/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/kaleaon_anatomy_parts.blend"
NUM = "/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/work/build_numbers.json"

bpy.ops.wm.open_mainfile(filepath=SRC)
arm = bpy.data.objects["KaleaonRig"]
arm_mw = arm.matrix_world.copy()

def bone_world(name):
    b = arm.data.bones[name]
    return (arm_mw @ b.head_local, arm_mw @ b.tail_local)

def vol_of(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); v = bm.calc_volume(); bm.free()
    return v

report = {"bones_world": {}, "parts": {}}

# ---------------------------------------------------------------- shafts
# Girth shape keys: radial scale about the shaft axis (Base.head -> Tip.tail).
# Length is the bone-scale channel (documented, demoed in QA) - no morph.
GIRTH_PLUS, GIRTH_MINUS = 1.28, 0.78
for n in (1, 2, 3, 4):
    src = bpy.data.objects[f"Shaft_{n}"]
    base_h, _ = bone_world(f"Shaft_{n}_Base")
    _, tip_t = bone_world(f"Shaft_{n}_Tip")
    axis_w = (tip_t - base_h); axis_w.normalize()
    report["bones_world"][f"Shaft_{n}"] = {
        "base": [round(v, 4) for v in base_h], "tip": [round(v, 4) for v in tip_t],
        "length_m": round((tip_t - base_h).length, 4)}
    ob = src.copy(); ob.data = src.data.copy(); ob.name = f"Part_Shaft_{n}"
    bpy.context.collection.objects.link(ob)
    # axis in object local space
    mw = ob.matrix_world
    inv = mw.inverted()
    base_l = inv @ base_h
    axis_l = (inv.to_3x3() @ axis_w); axis_l.normalize()
    co = np.empty(len(ob.data.vertices) * 3)
    ob.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    B = np.array(base_l); A = np.array(axis_l)
    t = (co - B) @ A
    radial = co - (B + np.outer(t, A))
    taper = np.clip(1.0 - 0.35 * np.clip((t / max((tip_t - base_h).length, 1e-6) - 0.75) / 0.25, 0, 1), 0.65, 1.0)
    ob.shape_key_add(name="Basis")
    for nm, s in (("GirthPlus", GIRTH_PLUS), ("GirthMinus", GIRTH_MINUS)):
        sk = ob.shape_key_add(name=nm)
        new = co + radial * ((s - 1.0) * taper)[:, None]
        sk.data.foreach_set("co", new.astype(np.float32).ravel())
        sk.value = 0.0  # shape_key_add leaves value at 1.0: rest MUST be pure
                        # Basis (bug caught by duplicate-agent QA, Nov 12)
    report["parts"][ob.name] = {"verts": len(ob.data.vertices),
                                "volume_L": round(vol_of(ob) * 1000, 3),
                                "morphs": ["GirthPlus", "GirthMinus"],
                                "bones": [f"Shaft_{n}_Base", f"Shaft_{n}_Tip"]}
    bpy.data.objects.remove(src, do_unlink=True)

# ---------------------------------------------------------------- sac-udder
sac_src = bpy.data.objects["Sac"]
sac = sac_src.copy(); sac.data = sac_src.data.copy(); sac.name = "Part_SacUdder"
bpy.context.collection.objects.link(sac)
bpy.data.objects.remove(sac_src, do_unlink=True)
report["parts"]["Part_SacUdder"] = {"verts": len(sac.data.vertices),
                                    "volume_L": round(vol_of(sac) * 1000, 3),
                                    "bones": ["Sac"]}

# Teat placement: columns on the underside; root = lowest sac vert nearby,
# axis = mostly down, tilted by the local surface normal.
mw = sac.matrix_world
ws = np.array([mw @ v.co for v in sac.data.vertices])
ns = np.array([ (mw.to_3x3() @ v.normal).normalized() for v in sac.data.vertices])
COLUMNS = [(-0.13, -0.17), (0.13, -0.17), (-0.13, 0.03), (0.13, 0.03)]  # FL FR RL RR
TEAT_LEN, TEAT_R = 0.095, 0.034
ROOT_Z = 0.115  # root on the underside slope, NOT the lowest pole: tips must
                # stay above ground (canon: sac bottom 0.031, never touching)
teat_specs = []
for (cx, cy) in COLUMNS:
    d2 = (ws[:, 0] - cx) ** 2 + (ws[:, 1] - cy) ** 2
    cand = np.argsort(d2)[:120]
    cand = cand[ns[cand, 2] < -0.25]           # downward-facing surface only
    pick = cand[np.argmin(np.abs(ws[cand, 2] - ROOT_Z))]
    root = Vector(ws[pick]); nrm = Vector(ns[pick])
    direction = (nrm * 0.35 + Vector((0, 0, -1)) * 0.94)
    direction.normalize()
    teat_specs.append({"root_surface": root, "dir": direction})

# Add Teat_N bones to the rig (parent: Sac), head at root, tail along dir.
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
for i, ts in enumerate(teat_specs, 1):
    eb = arm.data.edit_bones.new(f"Teat_{i}")
    head_a = arm_mw.inverted() @ (ts["root_surface"] - ts["dir"] * 0.015)
    tail_a = arm_mw.inverted() @ (ts["root_surface"] + ts["dir"] * (TEAT_LEN * 0.8))
    eb.head = head_a; eb.tail = tail_a
    eb.parent = arm.data.edit_bones["Sac"]
    eb.use_connect = False
bpy.ops.object.mode_set(mode='OBJECT')
arm_mw = arm.matrix_world.copy()

def build_teat(i, ts):
    root, d = ts["root_surface"], ts["dir"]
    # local frame: z along teat dir
    zax = d
    xax = Vector((1, 0, 0)).cross(zax)
    if xax.length < 1e-4: xax = Vector((0, 1, 0)).cross(zax)
    xax.normalize(); yax = zax.cross(xax).normalized()
    rings = [0.0, 0.08, 0.20, 0.35, 0.50, 0.65, 0.80, 0.90, 0.96]
    SEG = 12
    verts, faces = [], []
    center0 = root - d * 0.022  # embedded root
    for t in rings:
        r = TEAT_R * (0.86 + 0.30 * math.exp(-(((t - 0.18) / 0.17) ** 2)))
        if t > 0.84:
            r *= math.sqrt(max(1.0 - ((t - 0.84) / 0.16) ** 2 * 0.92, 0.02))
        c = center0 + d * (TEAT_LEN * t)
        for s in range(SEG):
            a = 2 * math.pi * s / SEG
            p = c + (xax * math.cos(a) + yax * math.sin(a)) * r
            verts.append(tuple(p))
    tip = center0 + d * TEAT_LEN
    verts.append(tuple(tip))
    nr = len(rings)
    for ri in range(nr - 1):
        for s in range(SEG):
            a, b = ri * SEG + s, ri * SEG + (s + 1) % SEG
            c2, d2 = (ri + 1) * SEG + (s + 1) % SEG, (ri + 1) * SEG + s
            faces.append((a, d2, c2, b))
    tip_i = len(verts) - 1
    for s in range(SEG):
        faces.append(((nr - 1) * SEG + s, (nr - 1) * SEG + (s + 1) % SEG, tip_i))
    me = bpy.data.meshes.new(f"Teat_{i}_mesh")
    me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new(f"Part_SacUdder_Teat_{i}", me)
    bpy.context.collection.objects.link(ob)
    ob.matrix_world = Matrix_identity()
    vg = ob.vertex_groups.new(name=f"Teat_{i}")
    vg.add(list(range(len(verts))), 1.0, 'REPLACE')
    mod = ob.modifiers.new("Armature", 'ARMATURE'); mod.object = arm
    return ob

from mathutils import Matrix as _M
def Matrix_identity():
    return _M.Identity(4)

for i, ts in enumerate(teat_specs, 1):
    ob = build_teat(i, ts)
    report["parts"][ob.name] = {"verts": len(ob.data.vertices),
                                "volume_L": round(vol_of(ob) * 1000, 3),
                                "bones": [f"Teat_{i}"],
                                "root_world": [round(v, 4) for v in ts["root_surface"]],
                                "dir_world": [round(v, 4) for v in ts["dir"]],
                                "length_m": TEAT_LEN, "base_radius_m": TEAT_R}

bpy.ops.wm.save_as_mainfile(filepath=OUT)
with open(NUM, "w") as f:
    json.dump(report, f, indent=1)
print("BUILT", OUT)
print(json.dumps(report["parts"], indent=1))
