"""Scan cleanup prototype v2: Poly Haven lion head.
Pipeline: weld -> component cull (distance+size rule) -> hole fill ->
normals -> guarded Taubin smooth (numpy) -> export GLB.
Prints STAGE::<json> per stage; final audit JSON saved."""
import bpy, bmesh, json
import numpy as np
from collections import Counter
from mathutils import kdtree

SRC = 'lion-src/lion_head_1k.gltf'
OUT_GLB = '../lion_head_clean.glb'
AUDIT_JSON = 'lion_audit.json'

def measure(bm):
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    bnd = [e for e in bm.edges if len(e.link_faces) == 1]
    adj = {}
    for e in bnd:
        a, b = e.verts[0].index, e.verts[1].index
        adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
    seen = set(); loops = []
    for s in list(adj):
        if s in seen: continue
        stack = [s]; comp = []
        while stack:
            v = stack.pop()
            if v in seen: continue
            seen.add(v); comp.append(v); stack.extend(adj[v])
        loops.append(len(comp))
    parent = {}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for f in bm.faces:
        idx = [v.index for v in f.verts]
        for i in idx: parent.setdefault(i, i)
        for i in idx[1:]:
            ra, rb = find(idx[0]), find(i)
            if ra != rb: parent[ra] = rb
    comps = Counter(find(v.index) for v in bm.verts if v.link_faces)
    vol = 0.0
    for f in bm.faces:
        vs = [v.co for v in f.verts]
        for i in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[i].cross(vs[i + 1])) / 6.0
    rough = 0.0; cnt = 0
    for v in bm.verts:
        ns = [e.other_vert(v).co for e in v.link_edges]
        if ns:
            c = sum(ns, ns[0] * 0) / len(ns)
            rough += (v.co - c).length; cnt += 1
    P = np.array([v.co for v in bm.verts])
    return {
        'verts': len(bm.verts), 'faces': len(bm.faces),
        'boundary_edges': len(bnd), 'boundary_loops': len(loops),
        'loop_sizes_top5': sorted(loops, reverse=True)[:5],
        'nonmanifold_edges': sum(1 for e in bm.edges if len(e.link_faces) > 2),
        'degenerate_faces': sum(1 for f in bm.faces if f.calc_area() < 1e-10),
        'components': len(comps),
        'component_vert_sizes': sorted(comps.values(), reverse=True)[:8],
        'signed_volume_m3': round(vol, 6),
        'roughness_mean_m': round(rough / max(cnt, 1), 6),
        'bbox_m': [round(float(P[:, i].max() - P[:, i].min()), 4) for i in range(3)],
    }

stages = {}
def stage(name, bm):
    stages[name] = measure(bm)
    print('STAGE::' + name + ' ' + json.dumps(stages[name]), flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]
bpy.context.view_layer.objects.active = obj
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bm = bmesh.new(); bm.from_mesh(obj.data)
stage('0_imported', bm)

# 1 weld
n0 = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-5)
stages['weld_removed'] = n0 - len(bm.verts)
stage('1_welded', bm)

# 2 component cull: size <1% of largest AND min distance to main shell > 2mm
bm.verts.ensure_lookup_table()
parent = {}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
for f in bm.faces:
    idx = [v.index for v in f.verts]
    for i in idx: parent.setdefault(i, i)
    for i in idx[1:]:
        ra, rb = find(idx[0]), find(i)
        if ra != rb: parent[ra] = rb
groups = {}
for v in bm.verts:
    if v.link_faces: groups.setdefault(find(v.index), []).append(v)
ordered = sorted(groups.values(), key=len, reverse=True)
main = ordered[0]
kd = kdtree.KDTree(len(main))
for i, v in enumerate(main): kd.insert(v.co, i)
kd.balance()
culled = []
for g in ordered[1:]:
    dmin = min(kd.find(v.co)[2] for v in g)
    frac = len(g) / len(main)
    print(f'COMP_CHECK:: verts={len(g)} frac={frac:.4f} min_dist_to_main={dmin:.4f}', flush=True)
    if frac < 0.01 and dmin > 0.002:
        culled.extend(g)
if culled:
    bmesh.ops.delete(bm, geom=culled, context='VERTS')
stages['culled_verts'] = len(culled)
stage('2_components_culled', bm)

# 3 hole fill (any real boundary loops left after welding)
bnd = [e for e in bm.edges if len(e.link_faces) == 1]
if bnd:
    bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
stage('3_holes_filled', bm)

# 4 normals
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
stage('4_normals', bm)

# 5 guarded Taubin smoothing in numpy (lambda 0.30 / mu -0.34, 3 pairs)
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
idx = {v.index: i for i, v in enumerate(bm.verts)}
P = np.array([v.co for v in bm.verts], dtype=np.float64)
E = np.array([[idx[e.verts[0].index], idx[e.verts[1].index]] for e in bm.edges])
src = np.r_[E[:, 0], E[:, 1]]; dst = np.r_[E[:, 1], E[:, 0]]
deg = np.bincount(src, minlength=len(P)).astype(np.float64)
def avg_nb(Q):
    out = np.zeros_like(Q)
    np.add.at(out, src, Q[dst])
    return out / deg[:, None]
def taubin(P, pairs=3, lam=0.30, mu=-0.34):
    Q = P.copy()
    for _ in range(pairs):
        for s in (lam, mu):
            Q = Q + s * (avg_nb(Q) - Q)
    return Q
def rough_of(P):
    return float(np.linalg.norm(avg_nb(P) - P, axis=1).mean())
r0 = rough_of(P)
Pt = taubin(P)
r1 = rough_of(Pt)
bb0 = P.max(0) - P.min(0); bb1 = Pt.max(0) - Pt.min(0)
drift = float(np.max(np.abs(bb1 - bb0) / bb0))
gain = (r0 - r1) / r0
print(f'TAUBIN_TRIAL:: gain={gain:.3f} drift={drift:.5f} r0={r0:.6f} r1={r1:.6f}', flush=True)
if gain > 0.10 and drift < 0.005:
    for v, q in zip(bm.verts, Pt):
        v.co = q
    stages['taubin_applied'] = True
    print('TAUBIN:: applied', flush=True)
else:
    stages['taubin_applied'] = False
    print('TAUBIN:: rejected by guard', flush=True)
stage('5_smoothed', bm)

# 6 grounding: seat the subject on z=0 (its base was floating on the culled disc)
bm.verts.ensure_lookup_table()
zmin = min(v.co.z for v in bm.verts)
for v in bm.verts:
    v.co.z -= zmin
stages['grounded_shift_m'] = round(float(zmin), 4)
stage('6_grounded', bm)

bm.to_mesh(obj.data); bm.free()
obj.data.update()
bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT_GLB, export_format='GLB')
json.dump(stages, open(AUDIT_JSON, 'w'), indent=1)
print('EXPORTED::', OUT_GLB, flush=True)
