"""End-to-end verification of the exported GLB inside Blender.

Imports orc_bust_skinned.glb fresh, rotates the Jaw pose bone 25 deg about
the world X axis through the jaw head, evaluates the deformed meshes via the
depsgraph, and measures: chin displacement, upper-teeth displacement (want
~0), lower-teeth displacement (want ~0.42, matching the numpy LBS result).
Run: blender -b --python blender_verify.py
"""
import bpy, math
import numpy as np
from mathutils import Matrix, Vector

W = "/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work"
GLB = "/home/hatch/workspace/anthroforge-v2/autoskin-prototype/orc_bust_skinned.glb"
JAW_HEAD = Vector((0, -0.30, -0.35))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
print("armature bones:", len(arm.data.bones))

def evaluated_verts(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    v = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", v)
    v = v.reshape(-1, 3)
    M = np.array(ob.matrix_world)
    v = v @ M[:3, :3].T + M[:3, 3]
    ev.to_mesh_clear()
    return v

meshes = {o.name.replace(" ", "_"): o for o in bpy.context.scene.objects if o.type == "MESH"}
rest = {k: evaluated_verts(o) for k, o in meshes.items()}

R = Matrix.Rotation(math.radians(25), 4, "X")
Mrot = Matrix.Translation(JAW_HEAD) @ R @ Matrix.Translation(-JAW_HEAD)
pb = arm.pose.bones["Jaw"]
pb.matrix = Mrot @ pb.bone.matrix_local
bpy.context.view_layer.update()

d = np.load(f"{W}/bust_meshes.npz")
posed = {k: evaluated_verts(o) for k, o in meshes.items()}
for k in ("OrcBust_LP_Main_0", "Teeth_LP_Main_0", "Eyes_LP_Eyes_0"):
    v0 = d[k + "_v"]
    disp = np.linalg.norm(posed[k][: len(v0)] - rest[k][: len(v0)], axis=1)
    print(f"{k}: mean disp {disp.mean():.4f} max {disp.max():.4f}")
    if k.startswith("OrcBust"):
        chin = (v0[:, 1] < -0.95) & (v0[:, 2] < -1.15)
        print(f"   chin mean disp {disp[chin].mean():.3f} (numpy LBS: 0.377)")
    if k.startswith("Teeth"):
        low = v0[:, 2] < -1.0
        print(f"   teeth z<-1.0 mean disp {disp[low].mean():.3f}; z>=-0.9 mean disp {disp[~low & (v0[:,2]>=-0.9)].mean():.4f}")
print("verify done")
