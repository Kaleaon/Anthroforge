#!/usr/bin/env python3
"""SEN — body assembly, head graft, fur groom, LOD cards, renders.

Stages (each stage's artefact is saved before the next begins):
  A. MPFB human + the four shipped targets (muscle, chest.width,
     tissue.strongman x1.0, terminal_v51) -> baked body mesh; human
     head cut at the neck (min-width slice), helper verts removed.
  B. sen_head.glb grafted at the neck socket (scale 0.2414 = head
     L 0.42 m at export / 1.74), yaw-aligned to the body's forward.
     Socket-overlap join per the parts standard — not a welded seam.
     Exports sen_composed.glb, saves work/sen_assembly.blend.
  C. Fur region maps on the composed body (analytic fields, the
     fur-prototype method) + one particle system per region; the
     chest crescent is its own region with PALE hair — a fur-colour
     zone per MARKINGS.md section 1.1, never a decal/tattoo.
  D. Card texture baked from a curtain of Sen's own groom hair;
     LOD card sets sampled from the groom's parent strands.
  E. Cycles renders (front / profile / three-quarter / head
     close-up). Saves sen_build.blend.

Run: HOME=/tmp/af_home xvfb-run blender -b --python build_body_fur.py
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix

HERE = Path(__file__).resolve().parent
SEN = HERE.parent
V2 = SEN.parent.parent
sys.path.insert(0, str(V2))

from body_machinery.axes import sstep  # noqa: E402
from body_machinery.osd import BODY_END  # noqa: E402

WORK = SEN / "work"
REND = SEN / "renders"
TG = SEN / "targets"
MPFB_ZIP = Path("/home/hatch/workspace/stick-figure-avatar/photoreal/"
                "tools/mpfb2.zip")
HEAD_SCALE = 0.42 / 1.74

bpy.ops.wm.read_factory_settings(use_empty=True)
try:
    bpy.ops.extensions.package_install_files(
        filepath=str(MPFB_ZIP), repo="user_default", enable_on_install=True)
except RuntimeError:
    bpy.ops.preferences.addon_enable(module="bl_ext.user_default.mpfb")
import importlib  # noqa: E402
importlib.import_module("bl_ext.user_default.mpfb")
from bl_ext.user_default.mpfb.services.humanservice import HumanService  # noqa: E402
from bl_ext.user_default.mpfb.services.targetservice import TargetService  # noqa: E402


def co_of(o):
    M = np.array(o.matrix_world)
    co = np.empty(len(o.data.vertices) * 3)
    o.data.vertices.foreach_get("co", co)
    return co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]


# ------------------------------------------------------------ stage A
human = HumanService.create_human(mask_helpers=False)
assert len(human.data.vertices) == 19158
keys = {}
for tag, p in (("muscle", TG / "body.muscle.target"),
               ("width", TG / "body.chest.width.target"),
               ("tissue", TG / "body.tissue.strongman.target"),
               ("terminal", TG / "body.belly.protrusion_terminal_v51.target")):
    keys[tag] = TargetService.load_target(human, str(p))
blocks = human.data.shape_keys.key_blocks
for tag in keys:
    blocks[keys[tag].name].value = 1.0
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
ev = human.evaluated_get(dg)
body_mesh = bpy.data.meshes.new_from_object(ev)
body = bpy.data.objects.new("SenBody", body_mesh)
bpy.context.scene.collection.objects.link(body)
P = co_of(body)
print(f"body baked: {len(P)} verts, z {P[:,2].min():.3f}..{P[:,2].max():.3f}")

# forward direction from the navel (correspondence index, as test_bara)
corr = np.load(V2 / "first-proof/work/correspondence.npz")
NAVEL = int(corr["navel_mh"])
nz = P[NAVEL][2]
sl = []
for zz in np.arange(nz - 0.06, nz + 0.061, 0.005):
    sel = np.where(np.abs(P[:, 2] - zz) < 0.004)[0]
    sel = sel[np.abs(P[sel][:, 0] - P[NAVEL][0]) < 0.17]
    if len(sel) > 20:
        sl.append(P[sel].mean(axis=0))
sl = np.array(sl)
fdir = P[NAVEL] - np.array([np.interp(nz, sl[:, 2], sl[:, 0]),
                            np.interp(nz, sl[:, 2], sl[:, 1]), nz])
fdir[2] = 0.0
fdir = fdir / np.linalg.norm(fdir)
print("forward dir:", np.round(fdir, 3))
FRONT = float(np.sign(fdir[1])) or 1.0     # front = FRONT * +y side

# neck cut: min-width slice in the neck band
best = None
for zz in np.arange(1.34, 1.54, 0.004):
    sel = P[np.abs(P[:, 2] - zz) < 0.003]
    sel = sel[np.abs(sel[:, 0]) < 0.20]
    if len(sel) > 30:
        w = float(np.ptp(sel[:, 0]))
        if best is None or w < best[1]:
            best = (float(zz), w)
cut_z = best[0] - 0.012
print(f"neck min-width slice z={best[0]:.3f} w={best[1]*100:.1f} cm; "
      f"cut at {cut_z:.3f}")
neck_axis = P[np.abs(P[:, 2] - cut_z) < 0.01].mean(axis=0)

bm = bmesh.new()
bm.from_mesh(body_mesh)
bm.verts.ensure_lookup_table()
kill = [v for v in bm.verts if v.index >= BODY_END or v.co.z > cut_z]
bmesh.ops.delete(bm, geom=kill, context="VERTS")
bm.to_mesh(body_mesh)
bm.free()
body_mesh.update()
P = co_of(body)
print(f"body after cut: {len(P)} verts")

# coat material for the (unfurred) skin under the fur
mat_coat = bpy.data.materials.new("SenCoatSkin")
mat_coat.use_nodes = True
bsdf = mat_coat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.30, 0.185, 0.10, 1.0)
bsdf.inputs["Roughness"].default_value = 0.85
body.data.materials.append(mat_coat)

# ------------------------------------------------------------ stage B
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(SEN / "sen_head.glb"))
head_objs = [o for o in bpy.data.objects if o not in before
             and o.type == "MESH"]
print("head objects:", [o.name for o in head_objs])
tis = next(o for o in head_objs if o.name == "TissueHead")
sock = next(o for o in head_objs if o.name == "NeckSocket")
nose = next(o for o in head_objs if o.name == "NoseLeather")
HW = co_of(tis)
socket_c = co_of(sock).mean(axis=0)
head_fwd = co_of(nose).mean(axis=0) - HW.mean(axis=0)
head_fwd[2] = 0.0
head_fwd /= np.linalg.norm(head_fwd)
yaw = math.atan2(fdir[0], fdir[1]) - math.atan2(head_fwd[0], head_fwd[1])
print(f"head fwd {np.round(head_fwd,3)} -> yaw {math.degrees(yaw):.1f} deg")
target = np.array([neck_axis[0], neck_axis[1], cut_z - 0.015])
Rz = np.array([[math.cos(yaw), -math.sin(yaw), 0],
               [math.sin(yaw), math.cos(yaw), 0], [0, 0, 1]])
sock_t = Rz @ (socket_c * HEAD_SCALE)
T = target - sock_t
M4 = np.eye(4)
M4[:3, :3] = Rz * HEAD_SCALE
M4[:3, 3] = T
for o in head_objs:
    o.matrix_world = Matrix(M4 @ np.array(o.matrix_world))
    o.name = "Sen_" + o.name
# head materials: coat on tissue/jaw, amber iris, dark nose
mat_head = bpy.data.materials.new("SenHeadCoat")
mat_head.use_nodes = True
mat_head.node_tree.nodes["Principled BSDF"].inputs[
    "Base Color"].default_value = (0.30, 0.185, 0.10, 1.0)
mat_head.node_tree.nodes["Principled BSDF"].inputs[
    "Roughness"].default_value = 0.9
mat_amber = bpy.data.materials.new("SenIrisAmber")
mat_amber.use_nodes = True
mat_amber.node_tree.nodes["Principled BSDF"].inputs[
    "Base Color"].default_value = (0.85, 0.45, 0.08, 1.0)
for o in head_objs:
    if o.name in ("Sen_TissueHead", "Sen_Jaw", "Sen_Throat",
                  "Sen_Ear_L", "Sen_Ear_R"):
        o.data.materials.clear()
        o.data.materials.append(mat_head)
    elif o.name.startswith("Sen_Iris"):
        o.data.materials.clear()
        o.data.materials.append(mat_amber)

bpy.ops.object.select_all(action="DESELECT")
for o in [body] + head_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.export_scene.gltf(filepath=str(SEN / "sen_composed.glb"),
                          export_format="GLB", use_selection=True)
bpy.ops.wm.save_as_mainfile(filepath=str(WORK / "sen_assembly.blend"))
print("ASSEMBLY SAVED")

# ------------------------------------------------------------ stage C
P = co_of(body)
z = P[:, 2]
front = FRONT * P[:, 1]
# normals for facing
body_mesh.calc_loop_triangles()
vn = np.zeros_like(P)
for poly in body_mesh.polygons:
    pass
norms = np.empty(len(P) * 3)
body_mesh.vertices.foreach_get("normal", norms)
N = norms.reshape(-1, 3)
facing = N[:, 1] * FRONT                       # +1 front, -1 back
r_ax = np.hypot(P[:, 0] - neck_axis[0], P[:, 1] - neck_axis[1])
crotch_z = float(P[(np.abs(P[:, 0]) < 0.03) & (z < 1.1)][:, 2].min()) \
    if ((np.abs(P[:, 0]) < 0.03) & (z < 1.1)).sum() > 10 else 0.95
chest_z = cut_z - 0.30
print(f"landmarks: crotch {crotch_z:.2f} chest {chest_z:.2f} cut {cut_z:.2f}")

W = {}
W["ruff"] = sstep(z, chest_z - 0.02, chest_z + 0.10) \
    * (1 - sstep(z, cut_z + 0.02, cut_z + 0.10)) \
    * (0.45 + 0.55 * np.clip(facing * 0.5 + 0.5, 0, 1)) \
    + 0.6 * np.exp(-((z - cut_z + 0.03) / 0.05) ** 2) * np.exp(-(r_ax / 0.16) ** 2)
W["ruff"] = np.clip(W["ruff"], 0, 1)
W["back"] = np.clip(-facing, 0, 1) ** 1.5 \
    * sstep(z, crotch_z + 0.05, crotch_z + 0.25) \
    * (1 - sstep(z, cut_z - 0.02, cut_z + 0.08))
W["belly"] = np.clip(facing, 0, 1) ** 1.5 \
    * sstep(z, crotch_z - 0.02, crotch_z + 0.12) \
    * (1 - sstep(z, chest_z + 0.02, chest_z + 0.14))
# crescent: width-normalised arc band across the upper chest —
# q rises toward the sides (horns-up arc), band where q in [0,1].
# (First attempt drew fixed-radius discs in the x-z plane: on a
# 56 cm chest the thin ring caught only 24 verts. This parametrised
# band spans the chest properly.)
q = (z - (chest_z - 0.055)) / 0.13 + 0.85 * (P[:, 0] / 0.30) ** 2
cres = sstep(q, -0.05, 0.22) * (1 - sstep(q, 0.78, 1.05)) \
    * np.clip(facing, 0, 1) ** 1.2 \
    * sstep(z, chest_z - 0.17, chest_z - 0.12) \
    * (1 - sstep(z, chest_z + 0.06, chest_z + 0.12))
W["crescent"] = np.clip(cres, 0, 1)
others = np.maximum(np.maximum(W["ruff"], W["back"]),
                    np.maximum(W["belly"], W["crescent"]))
W["coat"] = np.clip(1.0 - others, 0.04, 1.0)
for name, w in W.items():
    vg = body.vertex_groups.new(name=f"FUR_{name}")
    for i, wi in enumerate(w):
        if wi > 0.01:
            vg.add([i], float(wi), "REPLACE")
    print(f"region {name}: mean {w.mean():.3f} max {w.max():.2f} "
          f"verts>0.5: {(w > 0.5).sum()}")

HAIR = {
    # region: (parents, length m, colour, clump, kink)
    "ruff":     (2200, 0.150, (0.115, 0.070, 0.038), 0.60, "WAVE"),
    "back":     (3000, 0.100, (0.150, 0.092, 0.048), 0.42, "CURL"),
    "belly":    (2400, 0.045, (0.165, 0.103, 0.055), 0.25, "NO"),
    "coat":     (5200, 0.068, (0.155, 0.097, 0.052), 0.38, "CURL"),
    "crescent": (700, 0.055, (0.620, 0.545, 0.400), 0.30, "NO"),
}
hair_mats = {}
for name, (n, ln, col, clump, kink) in HAIR.items():
    m = bpy.data.materials.new(f"Hair_{name}")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    hb = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    hb.inputs["Color"].default_value = (*col, 1.0)
    hb.inputs["Roughness"].default_value = 0.42
    nt.links.new(hb.outputs["BSDF"], nt.nodes["Material Output"]
                 .inputs["Surface"])
    body.data.materials.append(m)
    hair_mats[name] = len(body.data.materials)  # 1-based slot for psys
stats = {}
for name, (n, ln, col, clump, kink) in HAIR.items():
    ps = body.modifiers.new(f"Fur_{name}", "PARTICLE_SYSTEM") \
        .particle_system
    st = ps.settings
    st.type = "HAIR"
    st.count = n
    st.hair_length = ln
    st.use_advanced_hair = True
    st.child_type = "INTERPOLATED"
    st.rendered_child_count = 3      # children per parent at render
    st.child_percent = 50            # viewport display fraction
    st.clump_factor = clump
    if kink != "NO":
        st.kink = kink
        st.kink_amplitude = 0.25 if kink == "WAVE" else 0.35
        st.kink_frequency = 4.0
    ps.vertex_group_density = f"FUR_{name}"   # 5.2: vgroups live on
    ps.vertex_group_length = f"FUR_{name}"    # the ParticleSystem
    st.material = hair_mats[name]
    stats[name] = {"parents": n, "length_m": ln,
                   "rendered_children_per_parent": 3,
                   "rendered_strands": n * 4,   # parent + 3 children
                   "colour_authored": col}
stats["total_parents"] = sum(v["parents"] for v in stats.values()
                             if isinstance(v, dict))
stats["total_rendered_strands"] = sum(
    v["rendered_strands"] for v in stats.values() if isinstance(v, dict))
(WORK / "fur_stats.json").write_text(json.dumps(
    {k: v for k, v in stats.items()}, indent=1))
print("fur groom:", stats["total_parents"], "parents,",
      stats["total_rendered_strands"], "rendered strands")


# persist integration landmarks for the cards/renders stage
sc = bpy.context.scene
sc["af_front"] = float(FRONT)
sc["af_cut_z"] = float(cut_z)
sc["af_chest_z"] = float(chest_z)
sc["af_crotch_z"] = float(crotch_z)
bpy.ops.wm.save_as_mainfile(filepath=str(SEN / "sen_build.blend"))
print("BUILD SAVED (stage 1: body+head+groom)")
