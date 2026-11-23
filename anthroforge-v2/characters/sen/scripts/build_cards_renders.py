#!/usr/bin/env python3
"""SEN stage 2 - LOD cards + curtain bake + renders.

Opens sen_build.blend (saved by build_body_fur.py stage 1) in a FRESH
process: the single-process run was OOM-killed during stage D on this
6 GB VM, so the pipeline is split. Landmarks ride in scene custom
properties written by stage 1.
"""
import json, math, random
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector

SEN = Path.home() / "workspace/anthroforge-v2/characters/sen"
bpy.ops.wm.open_mainfile(filepath=str(SEN / "sen_build.blend"))
sc = bpy.context.scene
FRONT = int(sc["af_front"]); CUT_Z = float(sc["af_cut_z"])
cut_z = CUT_Z
body = bpy.data.objects["SenBody"]
random.seed(11)

# ------------------------------------------------------------ stage D
# curtain bake for the card alpha texture (Sen's own hair, dark coat)
cur = bpy.data.objects.new("Curtain",
                           bpy.data.meshes.new("CurtainMesh"))
bpy.context.scene.collection.objects.link(cur)
import bmesh as _bm
bm2 = _bm.new()
bm2.from_mesh(cur.data)
vs = [bm2.verts.new(v) for v in ((-0.15, 5.0, 1.6), (0.15, 5.0, 1.6),
                                 (0.15, 5.0, 1.1), (-0.15, 5.0, 1.1))]
bm2.faces.new(vs)
bm2.to_mesh(cur.data)
bm2.free()
vg = cur.vertex_groups.new(name="all")
vg.add(list(range(len(cur.data.vertices))), 1.0, "REPLACE")
mat_clear = bpy.data.materials.new("Clear")
mat_clear.node_tree.nodes.remove(
    mat_clear.node_tree.nodes["Principled BSDF"])
tr = mat_clear.node_tree.nodes.new("ShaderNodeBsdfTransparent")
mat_clear.node_tree.links.new(
    tr.outputs["BSDF"],
    mat_clear.node_tree.nodes["Material Output"].inputs["Surface"])
cur.data.materials.append(mat_clear)                    # slot 1: faces
cur.data.materials.append(bpy.data.materials["Hair_coat"])  # slot 2: hair
cur.rotation_euler = (math.radians(75), 0, 0)  # strands read as streaks
ps = cur.modifiers.new("curtain", "PARTICLE_SYSTEM").particle_system
st = ps.settings
st.type = "HAIR"
st.count = 800
st.hair_length = 0.42
st.use_advanced_hair = True
st.child_type = "INTERPOLATED"
st.rendered_child_count = 4
st.child_percent = 50
ps.vertex_group_density = "all"
st.material = 2
st.emit_from = "FACE"

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 24
scene.render.resolution_x = 512
scene.render.resolution_y = 1024
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"
cam_d = bpy.data.cameras.new("TCam")
tcam = bpy.data.objects.new("TCam", cam_d)
scene.collection.objects.link(tcam)
tcam.location = (0, 3.6, 1.35)
tcam.rotation_euler = (math.pi / 2, 0, math.pi)
scene.camera = tcam
sun_d = bpy.data.lights.new("Sun", "SUN")
sun_d.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_d)
scene.collection.objects.link(sun)
sun.rotation_euler = (0.9, 0.2, 0.6)
# only curtain visible for this render
for o in bpy.data.objects:
    o.hide_render = o not in (cur, tcam, sun)
scene.render.filepath = str(SEN / "fur_card_texture_sen.png")
bpy.ops.render.render(write_still=True)
for o in bpy.data.objects:
    o.hide_render = False
bpy.data.objects.remove(cur, do_unlink=True)
print("card texture baked")

# cards sampled from the groom's parent strands
bpy.context.view_layer.update()
for m in body.modifiers:
    if m.type == "PARTICLE_SYSTEM":
        m.particle_system.settings.child_percent = 0  # parents only:
        # keeps the evaluated strand extraction inside the VM's RAM
dg = bpy.context.evaluated_depsgraph_get()
ev_body = body.evaluated_get(dg)
strands = []      # (points (k,3), region)
ev_mods = [m for m in ev_body.modifiers if m.type == "PARTICLE_SYSTEM"]
og_mods = [m for m in body.modifiers if m.type == "PARTICLE_SYSTEM"]
for og, evm in zip(og_mods, ev_mods):
    name = og.name.replace("Fur_", "")
    if name not in HAIR:
        continue
    ps = evm.particle_system
    for p in ps.particles:
        pts = np.array([tuple(k.co) for k in p.hair_keys])
        if len(pts) >= 3:
            strands.append((pts, name))
print(f"groom parent strands available: {len(strands)}")
rng = np.random.default_rng(20261112)
WIDTHS = {"ruff": 0.028, "back": 0.022, "belly": 0.015, "coat": 0.020,
          "crescent": 0.018}
TINTS = {"ruff": (0.30, 0.19, 0.10), "back": (0.36, 0.23, 0.12),
         "belly": (0.40, 0.26, 0.14), "coat": (0.38, 0.24, 0.13),
         "crescent": (0.92, 0.85, 0.68)}


def build_cards(chosen, path):
    verts, cols, uvs, faces, idx = [], [], [], [], [0]

    def add_card(pts, region):
        # resample to 5 points along the curve
        seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        s = np.concatenate([[0], np.cumsum(seg)])
        if s[-1] < 1e-6:
            return
        q = np.array([np.interp(u, s, pts[:, k]) for k in range(3)]).T \
            if False else np.stack(
                [np.interp(np.linspace(0, s[-1], 5), s, pts[:, k])
                 for k in range(3)], axis=1)
        w0 = WIDTHS[region]
        side = np.array([1.0, 0.0, 0.0])
        tw = rng.uniform(-0.6, 0.6)
        base = idx[0]
        for i, p in enumerate(q):
            t = i / 4.0
            wdt = w0 * (1.0 - 0.85 * t)
            off = side * (wdt / 2) * math.cos(tw * t)
            offz = side * (wdt / 2) * math.sin(tw * t)
            for sgn in (-1, 1):
                verts.append(tuple(p + sgn * off +
                                   np.array([0, 0, sgn * offz[0]])))
                cols.append(TINTS[region])
                uvs.append((0.0 if sgn < 0 else 1.0, 1.0 - t))
            if i:
                a = base + 2 * (i - 1)
                faces.append((a, a + 1, a + 3, a + 2))
        idx[0] += 10

    for pts, region in chosen:
        add_card(pts, region)
    me = bpy.data.meshes.new("Cards")
    me.from_pydata(verts, [], [tuple(f) for f in faces])
    me.update()
    colattr = me.color_attributes.new(name="tint", type="FLOAT_COLOR",
                                      domain="POINT")
    for i, c in enumerate(cols):
        colattr.data[i].color = (*c, 1.0)
    uv = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        uv.data[loop.index].uv = uvs[loop.vertex_index]
    ob = bpy.data.objects.new("FurCards", me)
    bpy.context.scene.collection.objects.link(ob)
    m = bpy.data.materials.new("CardMat")
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(SEN / "fur_card_texture_sen.png"))
    vc = nt.nodes.new("ShaderNodeVertexColor")
    vc.layer_name = "tint"
    nt.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    bsdf.inputs["Roughness"].default_value = 0.9
    m.surface_render_method = "DITHERED"
    me.materials.append(m)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB",
                              use_selection=True)
    bpy.data.objects.remove(ob, do_unlink=True)
    return len(chosen)


order = rng.permutation(len(strands))
pool = [strands[i] for i in order]
card_counts = {}
for lod, total in ((0, 1700), (1, 680), (2, 255)):
    chosen = pool[:total]
    card_counts[f"lod{lod}"] = build_cards(
        chosen, SEN / f"fur_cards_sen_lod{lod}.glb")
    print(f"LOD{lod}: {card_counts[f'lod{lod}']} cards")
(WORK / "card_counts.json").write_text(json.dumps(card_counts, indent=1))

# ------------------------------------------------------------ stage E
scene.render.engine = "CYCLES"
scene.cycles.samples = 32
scene.render.resolution_x = 640
scene.render.resolution_y = 800
scene.render.film_transparent = False
world = bpy.data.worlds.new("W") if not bpy.data.worlds \
    else bpy.data.worlds[0]
scene.world = world
world.node_tree.nodes["Background"].inputs[0].default_value = \
    (0.12, 0.12, 0.13, 1)
cam_d2 = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_d2)
scene.collection.objects.link(cam)
scene.camera = cam
centre = np.array([neck_axis[0], neck_axis[1], 0.0])


def point_cam(loc, target):
    cam.location = loc
    d = np.array(target) - np.array(loc)
    cam.rotation_euler = (
        math.atan2(d[2], math.hypot(d[0], d[1])) + math.pi / 2,
        0, math.atan2(d[1], d[0]) - math.pi / 2)


side = np.array([-fdir[1], fdir[0], 0.0])
tgt = tuple(centre + np.array([0, 0, 0.92]))
views = {
    "front": tuple(centre + fdir * 2.5 + np.array([0, 0, 1.02])),
    "profile": tuple(centre + side * 2.5 + np.array([0, 0, 1.02])),
    "threequarter": tuple(centre + fdir * 1.85 + side * 1.65
                          + np.array([0, 0, 1.06])),
}
for tag, loc in views.items():
    point_cam(loc, tgt)
    scene.render.filepath = str(REND / f"sen_{tag}.png")
    bpy.ops.render.render(write_still=True)
    print("rendered", tag)
# head close-up
head_c = (np.array([neck_axis[0], neck_axis[1], cut_z]) +
          fdir * 0.10 + np.array([0, 0, 0.13]))
point_cam(tuple(head_c + fdir * 0.62 + side * 0.18 +
                np.array([0, 0, 0.10])), tuple(head_c))
scene.render.filepath = str(REND / "sen_head_closeup.png")
bpy.ops.render.render(write_still=True)
print("rendered head close-up")
bpy.ops.wm.save_as_mainfile(filepath=str(SEN / "sen_build.blend"))
print("BODY+FUR DONE")
