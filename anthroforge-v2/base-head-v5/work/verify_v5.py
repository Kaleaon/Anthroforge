import bpy, json
from collections import Counter, defaultdict

def census(path, tag):
    bpy.ops.wm.open_mainfile(filepath=path)
    out = {}
    for name in ("TissueHead", "Jaw"):
        ob = bpy.data.objects[name]
        me = ob.data
        ecnt = Counter(); edir = Counter()
        for p in me.polygons:
            vs = list(p.vertices)
            for i in range(len(vs)):
                a, b = vs[i], vs[(i + 1) % len(vs)]
                ecnt[(min(a, b), max(a, b))] += 1
                edir[(a, b)] += 1
        bnd = [e for e, c in ecnt.items() if c == 1]
        nonman = [e for e, c in ecnt.items() if c > 2]
        # orientation consistency: interior edge traversed same direction by both faces
        incons = 0
        for (a, b), c in edir.items():
            if c == 2 and edir[(b, a)] == 0: incons += 1
        # boundary loops
        adj = defaultdict(list)
        for a, b in bnd: adj[a].append(b); adj[b].append(a)
        seen = set(); loops = []
        for s in list(adj):
            if s in seen: continue
            lp = [s]; seen.add(s); prev, cur = -1, s
            while True:
                nxt = [w for w in adj[cur] if w != prev]
                if not nxt: break
                w = nxt[0]
                if w == s or w in seen: break
                lp.append(w); seen.add(w); prev, cur = cur, w
            loops.append(len(lp))
        out[name] = {"verts": len(me.vertices), "faces": len(me.polygons),
                     "boundary_edges": len(bnd), "boundary_loops": sorted(loops, reverse=True),
                     "nonmanifold_edges": len(nonman), "orientation_inconsistent_edges": incons}
    print(tag, json.dumps(out, indent=1))
    return out

census("/home/hatch/workspace/anthroforge-v2/base-head-v4/neutral_base_head_v4.blend", "V4")
census("/home/hatch/workspace/anthroforge-v2/base-head-v5/neutral_base_head_v5.blend", "V5")
