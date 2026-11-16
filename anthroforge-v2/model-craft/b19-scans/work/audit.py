"""Mesh audit for scan-like assets. Usage:
blender -b --python audit.py -- <mesh-file> [label]
Prints one JSON line prefixed AUDIT:: with topology/health metrics."""
import bpy, bmesh, json, sys, math
from mathutils import kdtree

def boundary_loops(bm):
    bedges = [e for e in bm.edges if len(e.link_faces) == 1]
    # adjacency among boundary verts
    adj = {}
    for e in bedges:
        a, b = e.verts[0].index, e.verts[1].index
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    seen = set()
    loops = []
    for start in adj:
        if start in seen:
            continue
        stack = [start]; comp = []
        while stack:
            v = stack.pop()
            if v in seen:
                continue
            seen.add(v); comp.append(v)
            stack.extend(adj[v])
        loops.append(len(comp))
    return len(bedges), sorted(loops, reverse=True)

def components(bm):
    parent = {}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for f in bm.faces:
        idxs = [v.index for v in f.verts]
        for i in idxs:
            parent.setdefault(i, i)
        for i in idxs[1:]:
            ra, rb = find(idxs[0]), find(i)
            if ra != rb:
                parent[ra] = rb
    from collections import Counter
    return Counter(find(v.index) for v in bm.verts if v.link_faces)

def audit(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if path.endswith(('.gltf', '.glb')):
        bpy.ops.import_scene.gltf(filepath=path)
    elif path.endswith('.obj'):
        bpy.ops.wm.obj_import(filepath=path)
    elif path.endswith('.stl'):
        bpy.ops.wm.stl_import(filepath=path)
    obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]
    # apply transforms for honest world-space numbers
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    me = obj.data
    bm = bmesh.new(); bm.from_mesh(me)
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    nv, ne, nf = len(bm.verts), len(bm.edges), len(bm.faces)
    bnd_edges, loops = boundary_loops(bm)
    nonmanifold = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    wire = sum(1 for e in bm.edges if len(e.link_faces) == 0)
    degen = sum(1 for f in bm.faces if f.calc_area() < 1e-10)
    loose_verts = sum(1 for v in bm.verts if not v.link_faces)
    # duplicate verts (exact-position hash after rounding to 1e-6)
    seenp = {}
    dup = 0
    for v in bm.verts:
        k = (round(v.co.x, 6), round(v.co.y, 6), round(v.co.z, 6))
        if k in seenp: dup += 1
        else: seenp[k] = 1
    comps = components(bm)
    comp_sizes = sorted(comps.values(), reverse=True)
    # signed volume (valid sign even if open; magnitude indicative)
    vol = 0.0
    for f in bm.faces:
        vs = [v.co for v in f.verts]
        for i in range(1, len(vs) - 1):
            vol += vs[0].dot(vs[i].cross(vs[i + 1])) / 6.0
    area = sum(f.calc_area() for f in bm.faces)
    # roughness: mean distance of vert from centroid of linked neighbours
    rough = 0.0; cnt = 0
    for v in bm.verts:
        ns = [e.other_vert(v) for e in v.link_edges]
        if ns:
            c = sum((n.co for n in ns), ns[0].co * 0) / len(ns)
            rough += (v.co - c).length; cnt += 1
    rough = rough / max(cnt, 1)
    # asymmetry: verts right of midplane (x>2mm), mirrored nearest distance
    xs = [v.co for v in bm.verts]
    kd = kdtree.KDTree(nv)
    for i, co in enumerate(xs): kd.insert(co, i)
    kd.balance()
    import random
    random.seed(7)
    sample = [co for co in xs if co.x > 0.002]
    random.shuffle(sample); sample = sample[:2000]
    dists = []
    for co in sample:
        m = co.copy(); m.x = -m.x
        _, _, d = kd.find(m)
        dists.append(d)
    dists.sort()
    asym_med = dists[len(dists) // 2] if dists else None
    asym_p90 = dists[int(len(dists) * 0.9)] if dists else None
    dims = obj.dimensions
    out = {
        'verts': nv, 'edges': ne, 'faces': nf,
        'boundary_edges': bnd_edges, 'boundary_loops': len(loops),
        'loop_sizes_top5': loops[:5],
        'nonmanifold_edges': nonmanifold, 'wire_edges': wire,
        'degenerate_faces': degen, 'loose_verts': loose_verts,
        'duplicate_verts_1e-6': dup,
        'components': len(comp_sizes), 'component_vert_sizes': comp_sizes[:8],
        'signed_volume_m3': round(vol, 6), 'surface_area_m2': round(area, 4),
        'bbox_m': [round(float(d), 4) for d in dims],
        'roughness_mean_m': round(rough, 6),
        'asym_median_m': None if asym_med is None else round(asym_med, 5),
        'asym_p90_m': None if asym_p90 is None else round(asym_p90, 5),
    }
    print('AUDIT::' + json.dumps(out))
    return out

if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:]
    audit(argv[0])
