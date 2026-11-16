"""Hole-fill validation: cut a synthetic defect into a COPY of the cleaned
lion, verify boundary appears, fill, verify closure + patch stats."""
import bpy, bmesh, json
import numpy as np

def counts(bm):
    bm.edges.ensure_lookup_table()
    bnd = [e for e in bm.edges if len(e.link_faces) == 1]
    return {'verts': len(bm.verts), 'faces': len(bm.faces),
            'boundary_edges': len(bnd),
            'nonmanifold_edges': sum(1 for e in bm.edges if len(e.link_faces) > 2)}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath='../lion_head_clean.glb')
obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]
bm = bmesh.new(); bm.from_mesh(obj.data)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
print('HF::before_cut', json.dumps(counts(bm)), flush=True)

# defect centre: an actual front-facing cheek face's own centroid
best = None
for f in bm.faces:
    c = f.calc_center_median()
    if f.normal.y < -0.7 and abs(c.x - 0.07) < 0.03 and abs(c.z - 0.22) < 0.04:
        best = np.array(c); break
assert best is not None, 'no cheek face found'
centre = best
print('HF::centre', [round(float(x), 3) for x in centre], flush=True)
kill = []
for f in bm.faces:
    c = np.mean([v.co for v in f.verts], axis=0)
    if np.linalg.norm(c - centre) < 0.025:
        kill.append(f)
print('HF::faces_cut', len(kill), flush=True)
bmesh.ops.delete(bm, geom=kill, context='FACES')
print('HF::after_cut', json.dumps(counts(bm)), flush=True)

bnd = [e for e in bm.edges if len(e.link_faces) == 1]
res = bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
print('HF::after_fill', json.dumps(counts(bm)), flush=True)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
print('HF::after_normals', json.dumps(counts(bm)), flush=True)
bm.free()
