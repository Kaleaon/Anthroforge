import bpy
import numpy as np

bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.blend")
ob = bpy.data.objects["TeethArcade"]
V = np.array([tuple(v.co) for v in ob.data.vertices])

# For y-slices through the mouth, print x-width per z-bin to find the occlusal waist
for y0 in (0.34, 0.28, 0.20, 0.12, 0.04, -0.04, -0.12):
    m = (V[:,1]>=y0-0.02)&(V[:,1]<y0+0.02)
    P = V[m]
    print(f"--- y={y0:+.2f} n={len(P)}")
    if len(P)<4: continue
    for z0 in np.arange(-0.38, -0.14, 0.02):
        mm = (P[:,2]>=z0)&(P[:,2]<z0+0.02)
        if mm.sum()>=2:
            Q=P[mm]
            print(f"   z {z0:+.2f}: n={mm.sum():3d} xwidth={Q[:,0].max()-Q[:,0].min():.3f} zmean={Q[:,2].mean():+.3f}")
