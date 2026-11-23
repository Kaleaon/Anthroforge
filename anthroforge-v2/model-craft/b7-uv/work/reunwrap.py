import bpy, json
import numpy as np

SRC = "/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.glb"

def stretch_stats(ob):
    me = ob.data; me.calc_loop_triangles()
    P = np.empty((len(me.vertices),3)); me.vertices.foreach_get("co", P.ravel())
    uv = me.uv_layers.active
    UV = np.empty((len(me.loops),2)); uv.data.foreach_get("uv", UV.ravel())
    n=len(me.loop_triangles)
    T = np.empty((n,3),dtype=np.int64); me.loop_triangles.foreach_get("vertices", T.ravel())
    LT = np.empty((n,3),dtype=np.int64); me.loop_triangles.foreach_get("loops", LT.ravel())
    Tuv = UV[LT]
    p0,p1,p2 = P[T[:,0]],P[T[:,1]],P[T[:,2]]
    e1=p1-p0; e2=p2-p0; cr=np.cross(e1,e2); a3=0.5*np.linalg.norm(cr,axis=1)
    du1=Tuv[:,1]-Tuv[:,0]; du2=Tuv[:,2]-Tuv[:,0]
    nrm=np.zeros_like(cr); ok=a3>1e-14; nrm[ok]=cr[ok]/(2*a3[ok])[:,None]
    l1=np.linalg.norm(e1,axis=1); t1=np.zeros_like(e1); safe=ok&(l1>1e-12); t1[safe]=e1[safe]/l1[safe,None]
    t2=np.cross(nrm,t1)
    q11=l1; q12=np.einsum('ij,ij->i',e2,t1); q22=np.einsum('ij,ij->i',e2,t2)
    det=q11*q22; good=safe&(np.abs(q22)>1e-14)
    A=np.zeros((n,2,2)); i00=q22/np.where(det==0,1,det); i01=-q12/np.where(det==0,1,det); i11=q11/np.where(det==0,1,det)
    A[:,0,0]=du1[:,0]*i00; A[:,0,1]=du1[:,0]*i01+du2[:,0]*i11
    A[:,1,0]=du1[:,1]*i00; A[:,1,1]=du1[:,1]*i01+du2[:,1]*i11
    sv=np.linalg.svd(A[good],compute_uv=False); s1,s2=sv[:,0],sv[:,1]
    dens=s1*s2; med=np.median(dens[dens>0]); rel=dens/med
    L2=np.sqrt((s1**2+s2**2)/2)/np.sqrt(med); conf=s1/np.maximum(s2,1e-12)
    return {"L2_rms":round(float(np.sqrt(np.mean(L2**2))),3),"L2_p95":round(float(np.percentile(L2,95)),3),
            "conf_p95":round(float(np.percentile(conf,95)),3),"conf_gt2_pct":round(float(100*np.mean(conf>2)),1),
            "density_CV":round(float(np.std(rel)/np.mean(rel)),3),
            "density_p10":round(float(np.percentile(rel,10)),3),"density_p90":round(float(np.percentile(rel,90)),3)}

def load_head():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC)
    keep = bpy.context.scene.objects["TissueHead"]
    nose = bpy.context.scene.objects["NoseLeather"]
    import numpy as _np
    _nv = _np.empty((len(nose.data.vertices),3)); nose.data.vertices.foreach_get("co", _nv.ravel())
    _hv = _np.empty((len(keep.data.vertices),3)); keep.data.vertices.foreach_get("co", _hv.ravel())
    front_sign = 1.0 if _nv[:,1].mean() > _hv[:,1].mean() else -1.0
    for ob in list(bpy.context.scene.objects):
        if ob != keep: bpy.data.objects.remove(ob, do_unlink=True)
    bpy.context.view_layer.objects.active = keep
    keep.select_set(True)
    return keep, front_sign

results = {}
# (a) original
ob, fs = load_head()
results["original"] = stretch_stats(ob)
print("ORIG", json.dumps(results["original"]), "front_sign", fs)

# (b) smart UV project
ob, fs = load_head()
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.smart_project(angle_limit=np.radians(66), island_margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')
results["smart_project"] = stretch_stats(ob)
print("SMART", json.dumps(results["smart_project"]))

# (c) house method: low-visibility seams + angle-based unwrap + pack
ob, fs = load_head()
me = ob.data
P = np.empty((len(me.vertices),3)); me.vertices.foreach_get("co", P.ravel())
ymin,ymax = P[:,1].min(), P[:,1].max(); zmin,zmax = P[:,2].min(), P[:,2].max()
back_y = ymin + 0.45*(ymax-ymin)   # seam zone behind this (away from muzzle)
front = fs  # +1 if muzzle toward +Y
seam_count=0
for e in me.edges:
    v0,v1 = me.vertices[e.vertices[0]].co, me.vertices[e.vertices[1]].co
    mid = (np.array(v0)+np.array(v1))/2
    # sagittal strip at back of skull: near midline, posterior half
    back = (mid[1]*front) < 0.0   # posterior half relative to head centre (origin ~centre)
    if abs(mid[0]) < 0.012 and back: e.use_seam=True; seam_count+=1; continue
    # under-jaw / chin underside: lowest band, front half
    if mid[2] < zmin + 0.12*(zmax-zmin) and (mid[1]*front) > 0.0: e.use_seam=True; seam_count+=1; continue
    # crown-to-back transition ring behind ears: posterior, upper
    if back and mid[2] > zmin + 0.72*(zmax-zmin) and abs(mid[0])<0.02: e.use_seam=True; seam_count+=1
print("seams marked:", seam_count)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.unwrap(method='ANGLE_BASED', fill_holes=True, correct_aspect=True, use_subsurf_data=False, margin=0.02)
bpy.ops.uv.pack_islands(udim_source='CLOSEST_UDIM', rotate=True, margin=0.02)
bpy.ops.object.mode_set(mode='OBJECT')
results["house_seams"] = stretch_stats(ob)
print("HOUSE", json.dumps(results["house_seams"]))
bpy.ops.wm.save_as_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/model-craft/b7-uv/work/head_reunwrap.blend")
with open("/home/hatch/workspace/anthroforge-v2/model-craft/b7-uv/work/reunwrap.json","w") as f: json.dump(results,f,indent=1)
print("DONE")
