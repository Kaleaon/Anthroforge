import bpy, json
import numpy as np
from mathutils import kdtree

def face_data(ob):
    me = ob.data
    me.calc_loop_triangles()
    n = len(me.loop_triangles)
    P = np.empty((len(me.vertices),3))
    me.vertices.foreach_get("co", P.ravel())
    uv_layer = me.uv_layers.active
    if uv_layer is None: return None
    UV = np.empty((len(me.loops),2)); uv_layer.data.foreach_get("uv", UV.ravel())
    tris = np.empty((n,3), dtype=np.int64)
    me.loop_triangles.foreach_get("vertices", tris.ravel())
    ltris = np.empty((n,3), dtype=np.int64)
    me.loop_triangles.foreach_get("loops", ltris.ravel())
    return P, UV[ltris], tris

def metrics(ob):
    fd = face_data(ob)
    if fd is None: return {"object": ob.name, "uv": None}
    P, Tuv, T = fd
    p0,p1,p2 = P[T[:,0]], P[T[:,1]], P[T[:,2]]
    e1 = p1-p0; e2 = p2-p0
    cr = np.cross(e1,e2); a3 = 0.5*np.linalg.norm(cr,axis=1)
    u0,u1,u2 = Tuv[:,0],Tuv[:,1],Tuv[:,2]
    du1 = u1-u0; du2 = u2-u0
    auv = 0.5*np.abs(du1[:,0]*du2[:,1]-du1[:,1]*du2[:,0])
    ok = a3 > 1e-14
    # orthonormal basis per face
    nrm = np.zeros_like(cr); nrm[ok] = cr[ok]/ (2*a3[ok])[:,None]
    t1 = np.zeros_like(e1); 
    l1 = np.linalg.norm(e1,axis=1); safe = ok & (l1>1e-14)
    t1[safe] = e1[safe]/l1[safe,None]
    t2 = np.cross(nrm, t1)
    q11 = l1; q12 = np.einsum('ij,ij->i', e2, t1); q22 = np.einsum('ij,ij->i', e2, t2)
    # A = S * Q^-1, Q=[[q11,q12],[0,q22]]
    det = q11*q22
    good = safe & (np.abs(q22)>1e-14)
    A = np.zeros((len(T),2,2))
    i00 =  q22/det; i01 = -q12/det; i11 = q11/det
    A[:,0,0] = du1[:,0]*i00;            A[:,0,1] = du1[:,0]*i01 + du2[:,0]*i11
    A[:,1,0] = du1[:,1]*i00;            A[:,1,1] = du1[:,1]*i01 + du2[:,1]*i11
    sv = np.linalg.svd(A[good], compute_uv=False)
    s1, s2 = sv[:,0], sv[:,1]
    dens = s1*s2  # = auv/a3
    med = np.median(dens[dens>0]) if np.any(dens>0) else 1.0
    rel = dens/med
    L2 = np.sqrt((s1**2+s2**2)/2)/np.sqrt(med)
    conf = s1/np.maximum(s2,1e-12)
    # islands via union-find on shared UV edges
    parent = list(range(len(T)))
    def find(a):
        while parent[a]!=a: parent[a]=parent[parent[a]]; a=parent[a]
        return a
    edge_map = {}
    for fi in range(len(T)):
        for a,b,la,lb in ((0,1,0,1),(1,2,1,2),(2,0,2,0)):
            va,vb = T[fi,a],T[fi,b]
            key = (min(va,vb), max(va,vb))
            uv_a, uv_b = tuple(np.round(Tuv[fi,la],5)), tuple(np.round(Tuv[fi,lb],5))
            if key in edge_map:
                ofi, ouv_a, ouv_b = edge_map[key]
                if np.allclose(uv_a, ouv_a, atol=1e-4) and np.allclose(uv_b, ouv_b, atol=1e-4) or \
                   np.allclose(uv_a, ouv_b, atol=1e-4) and np.allclose(uv_b, ouv_a, atol=1e-4):
                    ra, rb = find(fi), find(ofi)
                    if ra!=rb: parent[ra]=rb
                else:
                    edge_map[key]=(fi, uv_a, uv_b)
            else:
                edge_map[key]=(fi, uv_a, uv_b)
    islands = len(set(find(i) for i in range(len(T))))
    outside = float(np.mean((Tuv< -0.001)|(Tuv>1.001))) if Tuv.size else 0.0
    # occupancy raster 256
    G=256; occ=np.zeros((G,G),bool)
    uvq = np.clip(Tuv,0,1)
    # rasterize by face centroids + verts (approx)
    cents = uvq.mean(axis=1)
    occ[(cents[:,1]*(G-1)).astype(int), (cents[:,0]*(G-1)).astype(int)] = True
    vert_occ = np.zeros((G,G),bool)
    flat = uvq.reshape(-1,2)
    vert_occ[(flat[:,1]*(G-1)).astype(int), (flat[:,0]*(G-1)).astype(int)] = True
    return {
      "object": ob.name, "verts": int(len(P)), "tris": int(len(T)),
      "islands": int(islands),
      "uv_area_sum": round(float(auv.sum()),4),
      "outside_tile_frac": round(outside,4),
      "density_rel_p10": round(float(np.percentile(rel,10)),3),
      "density_rel_p90": round(float(np.percentile(rel,90)),3),
      "density_CV": round(float(np.std(rel)/np.mean(rel)),3),
      "density_outside_0.5_2_pct": round(float(100*np.mean((rel<0.5)|(rel>2.0))),1),
      "L2stretch_rms": round(float(np.sqrt(np.mean(L2**2))),3),
      "L2stretch_p95": round(float(np.percentile(L2,95)),3),
      "conformal_p95": round(float(np.percentile(conf,95)),3),
      "conformal_gt2_pct": round(float(100*np.mean(conf>2.0)),1),
      "zero_uv_faces_pct": round(float(100*np.mean(auv<=1e-12)),1),
    }

def symmetry(ob, axis=0):
    me = ob.data
    uv_layer = me.uv_layers.active
    if uv_layer is None: return None
    P = np.empty((len(me.vertices),3)); me.vertices.foreach_get("co", P.ravel())
    # per-vertex uv (first loop)
    vuv = {}
    for loop in me.loops:
        if loop.vertex_index not in vuv:
            vuv[loop.vertex_index] = uv_layer.data[loop.index].uv
    kd = kdtree.KDTree(len(P))
    for i,p in enumerate(P): kd.insert(p, i)
    kd.balance()
    idxs = np.array(sorted(vuv.keys()))
    mir = P.copy(); mir[:,axis] *= -1
    good=0; tot=0; errs=[]
    rng = np.random.default_rng(0)
    sample = idxs if len(idxs)<=4000 else rng.choice(idxs, 4000, replace=False)
    scale = np.linalg.norm(P.max(0)-P.min(0))
    for i in sample:
        _, j, d = kd.find(mir[i])
        if d < 0.01*scale and j in vuv:
            tot += 1
            du = abs(vuv[i].x - (1.0 - vuv[j].x)); dv = abs(vuv[i].y - vuv[j].y)
            errs.append((du,dv))
            if du<0.02 and dv<0.02: good+=1
    if tot<20: return {"pairs": tot, "note": "too few pairs"}
    errs=np.array(errs)
    return {"pairs": tot, "mirrored_within_0.02_pct": round(100*good/tot,1),
            "mean_abs_du_err": round(float(errs[:,0].mean()),4), "mean_abs_dv_err": round(float(errs[:,1].mean()),4)}

jobs = [
 ("/home/hatch/workspace/stick-figure-avatar/furry-lineup/threejs-lineup/models/border_collie.glb", ["0","1","2"]),
 ("/home/hatch/workspace/bodies-3d/parts-library/sketchfab/anthro-fennec-rigged-codaj/anthro_fennec_rigged.glb", ["Object_113"]),
 ("/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.glb", ["TissueHead","Jaw","Ear_L","TeethArcade","Tongue"]),
]
out={}
for path, names in jobs:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=path)
    key = path.split("/")[-1]
    out[key]={}
    for nm in names:
        ob = bpy.context.scene.objects.get(nm)
        if ob is None: continue
        m = metrics(ob); out[key][nm]=m
        print(json.dumps(m))
    big = bpy.context.scene.objects.get(names[0])
    if big: 
        s = symmetry(big); out[key][names[0]+"_symmetry"]=s; print("SYM", json.dumps(s))
with open("/home/hatch/workspace/anthroforge-v2/model-craft/b7-uv/work/metrics.json","w") as f: json.dump(out,f,indent=1)
print("DONE")
