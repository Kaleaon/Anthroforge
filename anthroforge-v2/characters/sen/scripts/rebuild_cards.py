#!/usr/bin/env python3
"""SEN stage 2 - card rebuild against the repaired curtain texture.

The extraction + build_cards + LOD loop below is copied byte-for-byte
from build_cards_renders.py; it is re-run because the card material
loads fur_card_texture_sen.png from disk, and the first build embedded
the empty (alpha 0.000) bake. Preamble names (HAIR / WORK) are the
stage-1 definitions, as in build_cards_renders_run.py. The blend is
NOT saved.
"""
import json, math, random
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector

SEN = Path(__file__).resolve().parent.parent
WORK = SEN / "work"
HAIR = {
    "ruff":     (2200, 0.150, (0.115, 0.070, 0.038), 0.60, "WAVE"),
    "back":     (3000, 0.100, (0.150, 0.092, 0.048), 0.42, "CURL"),
    "belly":    (2400, 0.045, (0.165, 0.103, 0.055), 0.25, "NO"),
    "coat":     (5200, 0.068, (0.155, 0.097, 0.052), 0.38, "CURL"),
    "crescent": (700, 0.055, (0.620, 0.545, 0.400), 0.30, "NO"),
}
bpy.ops.wm.open_mainfile(filepath=str(SEN / "sen_build.blend"))
sc = bpy.context.scene
body = bpy.data.objects["SenBody"]
random.seed(11)

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
print('cards rebuilt')
