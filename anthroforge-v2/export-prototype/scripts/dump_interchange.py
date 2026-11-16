"""Stage 1b: dump the imported scene to an interchange file for the DAE writer.

Blender 5.2 has no Collada exporter, so write_dae.py (pycollada) builds the DAE
from this dump. Everything geometry-side is baked to WORLD space at rest pose;
skin weights are dumped raw (all influences) — normalisation is the writer's
job so the SL profile rule (top-4, renormalise) is explicit there.

Run: blender -b --factory-startup --python dump_interchange.py -- <src.glb> <out.npz> <out.json> <texdir>
"""
import bpy
import numpy as np
import os
import sys
import json

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, NPZ, JSONPATH, TEXDIR = argv[0], argv[1], argv[2], argv[3]
os.makedirs(TEXDIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)

arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
arm.data.pose_position = "REST"
bpy.context.view_layer.update()

arrays = {}
meta = {"meshes": [], "bones": [], "materials": [], "fps": bpy.context.scene.render.fps}

# ---------- materials ----------
mat_index = {}
for i, mat in enumerate(bpy.data.materials):
    mat_index[mat.name] = i
    color = [1.0, 1.0, 1.0, 1.0]
    tex_name = None
    if mat.use_nodes:
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                bc = node.inputs["Base Color"].default_value
                color = [float(bc[0]), float(bc[1]), float(bc[2]), float(bc[3])]
                break
        # glTF importer routes textures through a node group, so the Base
        # Color input may have no direct TEX_IMAGE link: take the material's
        # first image texture node as the diffuse map.
        for node in mat.node_tree.nodes:
            if node.type == "TEX_IMAGE" and node.image:
                img = node.image
                tex_name = os.path.splitext(img.name)[0] + ".png"
                out = os.path.join(TEXDIR, tex_name)
                try:
                    img.save_render(out)
                except Exception as e:
                    print("TEX SAVE FAIL", img.name, e)
                    tex_name = None
                break
    else:
        color = [float(c) for c in mat.diffuse_color]
    meta["materials"].append({"name": mat.name, "color": color, "texture": tex_name})

# ---------- skeleton ----------
bone_names = []
if arm:
    arm_world = np.array(arm.matrix_world)
    for b in arm.data.bones:
        bone_names.append(b.name)
        rest_world = arm.matrix_world @ b.matrix_local
        meta["bones"].append({
            "name": b.name,
            "parent": b.parent.name if b.parent else None,
            "rest_world": [float(x) for x in np.array(rest_world).ravel()],
        })
    meta["armature_world"] = [float(x) for x in arm_world.ravel()]
    meta["armature_name"] = arm.name

# ---------- meshes ----------
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    me = obj.data
    mw = np.array(obj.matrix_world)
    rot = mw[:3, :3]
    pos = np.array([v.co for v in me.vertices], dtype=np.float64)
    pos_w = pos @ rot.T + mw[:3, 3]
    me.calc_loop_triangles()  # not used for polys; we keep polys + fan-triangulate in writer
    polys = []
    poly_mat = []
    for p in me.polygons:
        polys.append([int(i) for i in p.vertices])
        poly_mat.append(int(p.material_index))
    # normals per-vertex (split normals averaged — acceptable for prototype)
    normals = np.array([v.normal for v in me.vertices], dtype=np.float64)
    nrm_w = normals @ rot.T
    nrm_w /= (np.linalg.norm(nrm_w, axis=1, keepdims=True) + 1e-12)
    # UVs: first layer, per-vertex from first loop using the vertex
    uv = np.zeros((len(me.vertices), 2))
    if me.uv_layers:
        layer = me.uv_layers[0].data
        seen = np.zeros(len(me.vertices), dtype=bool)
        for loop in me.loops:
            vi = loop.vertex_index
            if not seen[vi]:
                uv[vi] = layer[loop.index].uv
                seen[vi] = True
    key = f"mesh{len(meta['meshes'])}"
    arrays[key + "_pos"] = pos_w
    arrays[key + "_nrm"] = nrm_w
    arrays[key + "_uv"] = uv
    # weights: raw (group name -> weight) per vertex
    weights = []
    for v in me.vertices:
        weights.append([[obj.vertex_groups[g.group].name, float(g.weight)]
                        for g in v.groups if g.weight > 0.0])
    # shape keys (world space)
    keys_meta = []
    if me.shape_keys:
        for bi, kb in enumerate(me.shape_keys.key_blocks):
            if kb.name == "Basis":
                continue
            kp = np.array([kb.data[i].co for i in range(len(me.vertices))], dtype=np.float64)
            kp_w = kp @ rot.T + mw[:3, 3]
            arrays[f"{key}_key_{kb.name}"] = kp_w
            keys_meta.append({"name": kb.name, "value": float(kb.value)})
    mats = [obj.material_slots[s].material.name if obj.material_slots[s].material else None
            for s in range(len(obj.material_slots))]
    parent_arm = obj.parent.name if obj.parent else None
    meta["meshes"].append({
        "key": key, "name": obj.name, "polys": polys, "poly_mat": poly_mat,
        "weights": weights, "shape_keys": keys_meta, "materials": mats,
        "skinned": parent_arm == (arm.name if arm else None) and len(obj.vertex_groups) > 0,
        "matrix_world": [float(x) for x in mw.ravel()],
    })

# ---------- animation (sampled local bone matrices) ----------
anim_meta = None
if arm and arm.animation_data and arm.animation_data.action:
    act = arm.animation_data.action
    f0, f1 = float(act.frame_range[0]), float(act.frame_range[1])
    arm.data.pose_position = "POSE"
    step = 2
    frames = list(range(int(np.floor(f0)), int(np.ceil(f1)) + 1, step))
    samples = {b.name: [] for b in arm.pose.bones}
    from mathutils import Matrix
    for f in frames:
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        for pb in arm.pose.bones:
            if pb.parent:
                local = pb.parent.matrix.inverted() @ pb.matrix
            else:
                local = pb.matrix.copy()
            samples[pb.name].append([float(x) for x in np.array(local).ravel()])
    anim_meta = {"name": act.name, "frames": frames,
                 "fps": meta["fps"], "samples": samples}
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()

np.savez_compressed(NPZ, **arrays)
meta["animation"] = ({"name": anim_meta["name"], "frames": anim_meta["frames"],
                      "fps": anim_meta["fps"]} if anim_meta else None)
with open(JSONPATH, "w") as f:
    json.dump(meta, f)
if anim_meta:
    np.savez_compressed(os.path.join(os.path.dirname(NPZ), "anim_samples.npz"),
                        **{k: np.array(v) for k, v in anim_meta["samples"].items()},
                        frames=np.array(anim_meta["frames"]))
print("INTERCHANGE DUMPED", NPZ, JSONPATH)
