import bpy, json
import numpy as np
from mathutils import Vector

bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v4/neutral_base_head_v4.blend")
print("=== OBJECTS ===")
for o in bpy.data.objects:
    if o.type == 'MESH':
        print(f"{o.name:24s} verts={len(o.data.vertices):6d} polys={len(o.data.polygons):6d} loc={tuple(round(v,4) for v in o.location)} groups={[g.name for g in o.vertex_groups]}")
    else:
        print(f"{o.name:24s} type={o.type} loc={tuple(round(v,4) for v in o.location)}")

def world_verts(o):
    M = o.matrix_world
    return np.array([tuple(M @ v.co) for v in o.data.vertices])

TIS = bpy.data.objects["TissueHead"]; JAW = bpy.data.objects["Jaw"]
H = np.array(JAW.location)
tis = world_verts(TIS); jaw = world_verts(JAW)
print("\nHinge (Jaw loc):", H)
print("Tissue bounds min", tis.min(0).round(4), "max", tis.max(0).round(4))
print("Jaw(world) bounds min", jaw.min(0).round(4), "max", jaw.max(0).round(4))

# seam: position-matched verts (rounded 1e-5)
def keyset(P):
    return {tuple(np.round(c,5)): i for i,c in enumerate(P)}
tk = keyset(tis)
seam = [jaw[i] for i in range(len(jaw)) if tuple(np.round(jaw[i],5)) in tk]
seam = np.array(seam)
print(f"\nSeam shared verts: {len(seam)}")
if len(seam):
    print("seam y range", seam[:,1].min().round(4), seam[:,1].max().round(4))
    # front crossing: seam verts with |x|<0.01
    fr = seam[np.abs(seam[:,0])<0.012]
    if len(fr): print("seam near midline (x~0): y,z =", np.round(fr[np.argsort(fr[:,1])],4).tolist())
    # seam profile: for y bins, min/max z of seam verts
    for y0 in np.arange(-0.45, 0.36, 0.1):
        b = seam[(seam[:,1]>=y0)&(seam[:,1]<y0+0.1)]
        if len(b): print(f"  y[{y0:+.2f},{y0+0.1:+.2f}) n={len(b):3d} z[{b[:,2].min():+.4f},{b[:,2].max():+.4f}] x[{b[:,0].min():+.4f},{b[:,0].max():+.4f}]")

# teeth bounds
for name in ("TeethUpper","TeethLower"):
    o = bpy.data.objects.get(name)
    if o:
        P = world_verts(o)
        print(f"\n{name}: bounds min {P.min(0).round(4)} max {P.max(0).round(4)} loc {tuple(round(v,4) for v in o.location)}")
        fr = P[P[:,1] > P[:,1].max()-0.05]
        print(f"  front-most band: z range [{fr[:,2].min():.4f},{fr[:,2].max():.4f}]")

# profile section at x~0 of merged tissue+jaw surface: for z bins, max y (front profile)
mg = np.vstack([tis, jaw])
print("\n=== front profile (merged, |x|<0.008): z -> max y ===")
sel = mg[np.abs(mg[:,0])<0.008]
for z0 in np.arange(-0.34, 0.16, 0.02):
    b = sel[(sel[:,2]>=z0)&(sel[:,2]<z0+0.02)]
    if len(b): print(f"  z[{z0:+.2f},{z0+0.02:+.2f}) n={len(b):3d} maxy={b[:,1].max():+.4f}")

# lip crease scan: sections at several x, within muzzle front band: find local y-min (valley) in z in [-0.26,-0.10], y>0.1
print("\n=== crease scan: per x-slab, profile valley in z[-0.27,-0.09] ===")
for xc in (0.0, 0.04, -0.04, 0.08, -0.08, 0.105, -0.105):
    sel = mg[(np.abs(mg[:,0]-xc)<0.006) & (mg[:,1]>0.10)]
    prof = []
    for z0 in np.arange(-0.27, -0.09, 0.01):
        b = sel[(sel[:,2]>=z0)&(sel[:,2]<z0+0.01)]
        if len(b)>=1: prof.append((z0+0.005, b[:,1].max()))
    if len(prof)>4:
        ys = np.array([p[1] for p in prof]); zs = np.array([p[0] for p in prof])
        # valley: local min of maxy(z) in interior
        valleys = [(zs[i], ys[i]) for i in range(1,len(ys)-1) if ys[i]<ys[i-1] and ys[i]<=ys[i+1]]
        print(f"  x={xc:+.3f} valleys(z,y)={[(round(float(z),3),round(float(y),3)) for z,y in valleys]}  front y at z=-0.13:{np.interp(-0.13, zs, ys):.3f} z=-0.19:{np.interp(-0.19, zs, ys):.3f}")
