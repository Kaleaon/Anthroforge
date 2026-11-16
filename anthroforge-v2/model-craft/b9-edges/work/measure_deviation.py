#!/usr/bin/env python3
"""Post-pass: loop-normal deviation per variant from edges_demo.blend,
written back into stats.json. Run after build_edges.py."""
import bpy, json, math, sys

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]

def loop_deviation(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m = ev.to_mesh()
    cn = m.corner_normals
    devs = []
    for p in m.polygons:
        fn = p.normal
        for li in range(p.loop_start, p.loop_start + p.loop_total):
            ln = cn[li].vector
            if ln.length > 0 and fn.length > 0:
                devs.append(math.degrees(fn.angle(ln)))
    ev.to_mesh_clear()
    devs.sort()
    n = len(devs)
    return {"mean_deg": round(sum(devs) / n, 2),
            "p95_deg": round(devs[int(0.95 * n)], 2),
            "loops_over_15deg_pct": round(100.0 * sum(1 for d in devs if d > 15) / n, 1)}

bpy.ops.wm.open_mainfile(filepath=f"{OUT}/edges_demo.blend")
stats = json.load(open(f"{OUT}/stats.json"))
for key, name in (("A", "A_raw_autosmooth"), ("B", "B_weighted_normals"),
                  ("C", "C_bevelled_weighted")):
    ob = bpy.context.scene.objects[name]
    stats["variants"][key]["loop_dev"] = loop_deviation(ob)
    print(key, stats["variants"][key]["loop_dev"], flush=True)
json.dump(stats, open(f"{OUT}/stats.json", "w"), indent=1)
print("MEASURED DONE", flush=True)
