import json
import numpy as np
from collections import defaultdict, deque
from glb_lib import load_glb, meshes

gltf, bin_chunk = load_glb("/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.glb")
MS = meshes(gltf, bin_chunk)

def weld(pos, idx, tol=1e-4):
    key = np.round(pos / tol).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    wpos = pos[first]
    widx = inv[idx]
    ok = (widx[:,0]!=widx[:,1]) & (widx[:,1]!=widx[:,2]) & (widx[:,0]!=widx[:,2])
    return wpos, widx[ok]

def topo(pos, idx):
    edges = {}
    for t in idx:
        for a,b in ((0,1),(1,2),(2,0)):
            k = (min(t[a],t[b]), max(t[a],t[b]))
            edges[k] = edges.get(k, 0) + 1
    val = np.zeros(len(pos), int)
    for (a,b) in edges: val[a]+=1; val[b]+=1
    bnd = [e for e,c in edges.items() if c==1]
    nonman = [e for e,c in edges.items() if c>2]
    # boundary loops
    adj = defaultdict(list)
    for a,b in bnd: adj[a].append(b); adj[b].append(a)
    seen=set(); loops=[]
    for s in adj:
        if s in seen: continue
        loop=[s]; seen.add(s); prev=None; cur=s
        while True:
            nxt=[n for n in adj[cur] if n!=prev]
            if not nxt: break
            n=nxt[0]
            if n==s: break
            loop.append(n); seen.add(n); prev,cur=cur,n
            if len(loop)>10000: break
        loops.append(loop)
    return val, bnd, nonman, loops

def adj_list(idx, n):
    adj = defaultdict(set)
    for t in idx:
        for a,b in ((0,1),(1,2),(2,0)):
            adj[a].add(b); adj[b].add(a)
    return adj

def bfs_rings(adj, seeds, max_rings=12):
    seen = set(seeds); rings=[len(seeds)]
    frontier = list(seeds)
    for _ in range(max_rings):
        nxt=[]
        for v in frontier:
            for n in adj[v]:
                if n not in seen: seen.add(n); nxt.append(n)
        if not nxt: break
        rings.append(len(nxt)); frontier=nxt
    return rings, seen

out = {}
W = {}
for name, prims in MS.items():
    pos, idx = prims[0]
    wp, wi = weld(pos, idx)
    W[name] = (wp, wi)
    val, bnd, nonman, loops = topo(wp, wi)
    out[name] = dict(welded_verts=int(len(wp)), tris=int(len(wi)),
                     valence_med=int(np.median(val)), poles_v5=int((val==5).sum()),
                     poles_v7plus=int((val>=7).sum()),
                     boundary_edges=int(len(bnd)), nonmanifold_edges=int(len(nonman)),
                     boundary_loops=[int(len(l)) for l in loops])
    print(name, out[name])

# ---------- TissueHead deep dive ----------
tp, ti = W["TissueHead"]
tadj = adj_list(ti, len(tp))
eyeL = np.array([0.131, -0.008, -0.082]); eyeR = np.array([-0.131, -0.008, -0.082])
d_eye = np.minimum(np.linalg.norm(tp-eyeL,axis=1), np.linalg.norm(tp-eyeR,axis=1))
rim = np.where((d_eye>0.070)&(d_eye<0.088))[0]
rings, seen = bfs_rings(tadj, rim.tolist(), 8)
out["eye_socket_rings_from_rim"] = rings
# radial distance distribution of ring layers
layer_of = {}
seen2=set(rim.tolist()); layer_of.update({int(v):0 for v in rim})
frontier=list(rim)
for L in range(1,9):
    nxt=[]
    for v in frontier:
        for n in tadj[v]:
            if n not in seen2: seen2.add(n); layer_of[int(n)]=L; nxt.append(n)
    frontier=nxt
ring_rad = {}
for v,L in layer_of.items():
    ring_rad.setdefault(L, []).append(float(d_eye[v]))
out["eye_ring_radial_extent"] = {L: [round(min(r),3), round(max(r),3), len(r)] for L,r in sorted(ring_rad.items())}

# regional density: assign each tri to a region by centroid
def tri_areas(pos, idx):
    a = pos[idx[:,0]]; b = pos[idx[:,1]]; c = pos[idx[:,2]]
    return 0.5*np.linalg.norm(np.cross(b-a, c-a), axis=1)
areas = tri_areas(tp, ti)
cent = tp[ti].mean(axis=1)
regions = {
 "brow_band":   (np.abs(cent[:,0])<0.16)&(cent[:,1]>0.03)&(cent[:,1]<0.16)&(cent[:,2]>-0.25)&(cent[:,2]<0.05),
 "eye_socket_zone": (d_eye[ti].min(axis=1)<0.20),
 "muzzle_dorsum": (np.abs(cent[:,0])<0.09)&(cent[:,2]<-0.25)&(cent[:,1]>-0.10),
 "whisker_pad_zone": (np.abs(cent[:,0])>0.07)&(np.abs(cent[:,0])<0.20)&(cent[:,2]<-0.30)&(cent[:,2]>-0.50)&(cent[:,1]>-0.28)&(cent[:,1]<-0.08),
 "lip_line_zone": (cent[:,2]<-0.38)&(cent[:,1]>-0.30)&(cent[:,1]<-0.16),
 "cheek": (np.abs(cent[:,0])>0.18)&(cent[:,2]>-0.25)&(cent[:,2]<0.10)&(cent[:,1]<0.05),
 "forehead": (np.abs(cent[:,0])<0.14)&(cent[:,1]>0.14)&(cent[:,2]>-0.15)&(cent[:,2]<0.15),
 "cranium_side": (np.abs(cent[:,0])>0.20)&(cent[:,2]>0.05),
}
dens = {}
for rn, m in regions.items():
    if m.sum()==0: continue
    vids = np.unique(ti[m])
    dens[rn] = dict(tris=int(m.sum()), verts=int(len(vids)), area_L2=round(float(areas[m].sum()),4),
                    verts_per_L2=round(len(vids)/max(areas[m].sum(),1e-9),1),
                    mean_edge_L=None)
out["region_density"] = dens

# midline dorsal profile + stop detection
mid = tp[np.abs(tp[:,0])<0.012]
order = np.argsort(mid[:,2])
prof = mid[order]
# smooth y(z)
zs = np.linspace(-0.50, 0.30, 161)
ys = np.interp(zs, prof[:,2], prof[:,1])
dy = np.gradient(ys, zs); d2 = np.gradient(dy, zs)
win = (zs>-0.28)&(zs<-0.02)
i_stop = np.argmax(np.where(win, np.abs(d2), 0))
out["stop"] = dict(z_at_max_curvature=round(float(zs[i_stop]),3),
                   profile_y_at_stop=round(float(ys[i_stop]),3),
                   slope_before=round(float(dy[i_stop-4]),2), slope_after=round(float(dy[i_stop+4]),2))
out["midline_profile"] = [[round(float(a),3), round(float(b),3)] for a,b in zip(zs[::4], ys[::4])]

# boundary loop locations
val, bnd, nonman, loops = topo(tp, ti)
loop_info=[]
for lp in loops:
    P = tp[lp]
    loop_info.append(dict(n=len(lp), centre=np.round(P.mean(0),3).tolist(),
                          span=np.round(P.max(0)-P.min(0),3).tolist()))
out["tissue_boundary_loops"] = loop_info

# ---------- Eyelid ----------
ep, ei = W["Eyelid_L"]
eval_, ebnd, enon, eloops = topo(ep, ei)
eadj = adj_list(ei, len(ep))
out["eyelid_loops_detail"] = []
for lp in eloops:
    P = ep[lp]
    out["eyelid_loops_detail"].append(dict(n=len(lp), centre=np.round(P.mean(0),3).tolist(),
                                           span=np.round(P.max(0)-P.min(0),3).tolist()))
# rings inward from the largest boundary loop (the margin)
if eloops:
    margin = max(eloops, key=len)
    r, sn = bfs_rings(eadj, margin, 20)
    out["eyelid_rings_from_margin"] = r

# ---------- Ear ----------
ap, ai = W["Ear_L"]
aval, abnd, anon, aloops = topo(ap, ai)
out["ear_loops_detail"] = []
for lp in aloops:
    P = ap[lp]
    out["ear_loops_detail"].append(dict(n=len(lp), centre=np.round(P.mean(0),3).tolist(),
                                        span=np.round(P.max(0)-P.min(0),3).tolist()))
# ear plane relief: PCA plane, signed distance
c = ap.mean(0); U,S,Vt = np.linalg.svd(ap-c, full_matrices=False)
n = Vt[2]
d = (ap-c)@n
out["ear_relief"] = dict(pca_extents=np.round(S,3).tolist() if False else np.round(np.sqrt(S**2/len(ap))*2,3).tolist(),
                         signed_dist_min=round(float(d.min()),3), signed_dist_max=round(float(d.max()),3),
                         frac_beyond_002L=int(((np.abs(d)>0.02)).sum()), nverts=int(len(ap)))
# concha probe: verts in central 50% of ear (PCA coords), their depth vs rim verts
pc = (ap-c)@Vt.T
central = (np.abs(pc[:,0])<0.25*np.ptp(pc[:,0])) & (np.abs(pc[:,1])<0.25*np.ptp(pc[:,1]))
rimz = (np.abs(pc[:,0])>0.40*np.ptp(pc[:,0])) | (np.abs(pc[:,1])>0.40*np.ptp(pc[:,1]))
out["ear_concha_probe"] = dict(central_mean_depth=round(float(d[central].mean()),4),
                               rim_mean_depth=round(float(d[rimz].mean()),4),
                               central_n=int(central.sum()))

# ---------- Nose leather seating ----------
np_, ni = W["NoseLeather"]
from scipy.spatial import cKDTree
tree = cKDTree(tp)
dd, _ = tree.query(np_)
out["nose_seating"] = dict(nn_dist_median=round(float(np.median(dd)),4),
                           nn_dist_p90=round(float(np.percentile(dd,90)),4),
                           nn_dist_max=round(float(dd.max()),4),
                           frac_within_0005L=round(float((dd<0.005).mean()),3))
nose_weld_n = len(np_)
out["nose_welded_verts"] = int(nose_weld_n)

# whisker pad check: are there any verts standing proud on the pad zone? skip - density covers it
json.dump(out, open("topology_stats.json","w"), indent=1)
print(json.dumps({k:v for k,v in out.items() if k not in ("midline_profile",)}, indent=1)[:4500])
