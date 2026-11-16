import bpy
import numpy as np

def section_width(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    P, F = [], []
    for nm in ("TissueHead", "Jaw"):
        ob = bpy.data.objects[nm]
        base = len(P)
        P += [tuple(ob.matrix_world @ v.co) for v in ob.data.vertices]
        F += [tuple(i + base for i in p.vertices) for p in ob.data.polygons]
    P = np.array(P)
    ycan = 0.0815 + 0.5 * (0.5 - 0.0815)
    xs = []
    for f in F:
        pts = P[list(f)]
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            if (a[1] - ycan) * (b[1] - ycan) < 0 and a[1] != b[1]:
                t = (ycan - a[1]) / (b[1] - a[1])
                xs.append(a[0] + t * (b[0] - a[0]))
    xs = np.array(xs)
    return float(xs.max() - xs.min()) if len(xs) else None

print("v3 surface-true section width at ycan:", section_width("/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.blend"))
print("v4 surface-true section width at ycan:", section_width("/home/hatch/workspace/anthroforge-v2/base-head-v4/neutral_base_head_v4.blend"))
