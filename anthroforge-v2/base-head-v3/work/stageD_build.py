import bpy, json, math
from mathutils import Vector, Matrix
import bmesh

bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/work/stageC.blend")
T=bpy.data.objects["TissueHead"]; ARC=bpy.data.objects["TeethArcade"]; TON=bpy.data.objects["Tongue"]
earL=bpy.data.objects["Ear_L"]; earR=bpy.data.objects["Ear_R"]
EYESRC=bpy.data.objects["Eye_source"]
scm=json.load(open("/home/hatch/workspace/anthroforge-v2/base-head-v3/work/stageC_measure.json"))["measure"]
lm=json.load(open("/home/hatch/workspace/anthroforge-v2/base-head-v3/work/landmarks.json"))
pal=scm["pal_z"]; top=scm["skull_top"]
eye_x=(lm["eye_landmark_lifted"][0]-lm["centre"][0])/lm["renorm_L"]
eye_y=(lm["eye_landmark_lifted"][1]-lm["centre"][1])/lm["renorm_L"]
eye_z=(lm["eye_landmark_lifted"][2]-lm["centre"][2])/lm["renorm_L"]
print("eye line:",round(eye_y,4),round(eye_z,4),"pal",pal,"top",top)

def ramp(v,a,b):
    t=max(0.0,min(1.0,(v-a)/(b-a))); return t*t*(3-2*t)
def separate_by(ob, fn, newname):
    me=ob.data
    bm=bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
    keep=[f for f in bm.faces if fn(f.calc_center_median())]
    verts={}; nverts=[]; nfaces=[]
    for f in keep:
        nf=[]
        for v in f.verts:
            if v.index not in verts:
                verts[v.index]=len(nverts); nverts.append(v.co.copy())
            nf.append(verts[v.index])
        nfaces.append(nf)
    nme=bpy.data.meshes.new(newname); nme.from_pydata(nverts,[],nfaces); nme.update()
    nob=bpy.data.objects.new(newname,nme); bpy.context.collection.objects.link(nob)
    nob.matrix_world = ob.matrix_world.copy()
    bmesh.ops.delete(bm, geom=keep, context='FACES'); bm.to_mesh(me); bm.free()
    used=set()
    for p in me.polygons: used.update(p.vertices)
    bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in range(len(bm.verts)) if i not in used], context='VERTS')
    bm.to_mesh(me); bm.free()
    return nob

# ---- jaw split (world coords; T at identity)
ear_base_y=scm["ear_base_y"]
H=Vector((0, ear_base_y-0.02, pal+0.055))
def jaw_test(c):
    if c.y < H.y-0.18 or c.z > H.z+0.12: return False
    zcut = H.z - 0.16*max(0.0,c.y-H.y) + (0.30*(H.y-c.y) if c.y<H.y else 0.0) + 0.025*math.exp(-((c.y-H.y)/0.10)**2)
    return c.z < zcut
JAW=separate_by(T, jaw_test, "Jaw")
for v in JAW.data.vertices: v.co -= H
JAW.location=H
print("jaw verts",len(JAW.data.vertices),"tissue",len(T.data.vertices))

# ---- skull layers (world-baked offsets)
def offset_copy(ob, newname, tfn):
    n=ob.copy(); n.data=ob.data.copy(); n.name=newname
    bpy.context.collection.objects.link(n)
    ws=[n.matrix_world @ v.co for v in n.data.vertices]
    n.matrix_world=Matrix.Identity(4); n.location=(0,0,0); n.rotation_euler=(0,0,0); n.scale=(1,1,1)
    for i,v in enumerate(n.data.vertices):
        w=ws[i]; v.co = w - v.normal*tfn(w)
    return n
SK=offset_copy(T,"Skull", lambda w: 0.009 + 0.005*ramp(w.y,0.05,0.35) - 0.002*ramp(w.z, top-0.15, top))
SKM=offset_copy(JAW,"SkullMandible", lambda w: 0.008)
def muscle_test(c):
    tempo = -0.30<=c.y<=0.06 and c.z>=pal+0.10 and abs(c.x)>=0.09
    mass  = -0.12<=c.y<=0.10 and pal-0.01<=c.z<=pal+0.11 and abs(c.x)>=0.115
    return tempo or mass
MUS=separate_by(SK, muscle_test, "Muscles")
for v in MUS.data.vertices: v.co += v.normal*0.0045
print("skull",len(SK.data.vertices),"muscles",len(MUS.data.vertices),"mandible",len(SKM.data.vertices))

# ---- grafts from v2
V2="/home/hatch/workspace/anthroforge-v2/base-head-v2/neutral_base_head_v2.blend"
WANT=["Eyeball_L","Eyeball_R","Iris_L","Iris_R","Pupil_L","Pupil_R","Eyelid_L","Eyelid_R",
      "LidMargin_L","LidMargin_R","NoseLeather","Throat","NeckSocket","NeckSocketDisc"]
with bpy.data.libraries.load(V2, link=False) as (src,dst):
    dst.objects=[n for n in WANT if n in src.objects]
grafted={}
for ob in dst.objects:
    bpy.context.collection.objects.link(ob); grafted[ob.name]=ob
bpy.context.view_layer.update()
for ob in grafted.values():
    M=ob.matrix_world.copy()
    for v in ob.data.vertices: v.co = M @ v.co
    ob.matrix_world=Matrix.Identity(4); ob.location=(0,0,0); ob.rotation_euler=(0,0,0); ob.scale=(1,1,1)
print("grafted:", sorted(grafted))
def xform(ob, C2, C3, s):
    for v in ob.data.vertices:
        v.co = C3 + (v.co-C2)*s
    ob.matrix_world=Matrix.Identity(4); ob.location=(0,0,0); ob.rotation_euler=(0,0,0); ob.scale=(1,1,1)
for side in ("L","R"):
    sx = 1 if side=="L" else -1
    C2=Vector((sx*0.106, 0.085, 0.040)); C3=Vector((sx*eye_x*0.98, eye_y-0.008, eye_z))
    R=Matrix.Rotation(math.radians(-15*sx),4,'Z')
    for part in ("Eyeball_","Iris_","Pupil_","Eyelid_","LidMargin_"):
        ob=grafted[part+side]; xform(ob, C2, C3, 1.5)
        for v in ob.data.vertices: v.co = C3 + R @ (v.co - C3)
_eb=grafted["Eyeball_L"]; _vs=[v.co for v in _eb.data.vertices]
print("EYEBALL_L centre after graft:", [round((min(v[i] for v in _vs)+max(v[i] for v in _vs))/2,4) for i in range(3)], "expect", [round(eye_x*0.98,4), round(eye_y-0.008,4), round(eye_z,4)])
# nose leather
nose_y=max(v.co.y for v in T.data.vertices)
tipv=[v.co for v in T.data.vertices if v.co.y>nose_y-0.04]
z_nose=sum(v.z for v in tipv)/len(tipv)
xform(grafted["NoseLeather"], Vector((0,0.487,0.012)), Vector((0, nose_y-0.015, z_nose)), 1.05)
# throat
xform(grafted["Throat"], Vector((0,0.015,-0.045)), Vector((0,-0.08,pal+0.035)), 1.35)
# neck socket: fit to stub
stub=[v.co for v in T.data.vertices if v.co.y<-0.36]
Cc=Vector((0,0,0))
for v in stub: Cc+=v
Cc/=len(stub)
w_c=max(v.x for v in stub)-min(v.x for v in stub)
axis=(Cc-Vector((0,-0.05,0.0))).normalized()
q=Vector((0,-1,0)).rotation_difference(axis)
s=w_c/0.206
for nm in ("NeckSocket","NeckSocketDisc"):
    ob=grafted[nm]
    for v in ob.data.vertices:
        v.co = Cc + q @ ((v.co-Vector((0,-0.44,-0.03)))*s)
    ob.matrix_world=Matrix.Identity(4); ob.location=(0,0,0); ob.rotation_euler=(0,0,0); ob.scale=(1,1,1)
print("socket centre", [round(v,3) for v in Cc], "width", round(w_c,3), "scale", round(s,2))

# ---- materials for native objects
def claymat(name, rgb, rough=0.6, sss=0.0):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name)
    bsdf=m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value=(*rgb,1); bsdf.inputs["Roughness"].default_value=rough
    if sss:
        bsdf.inputs["Subsurface Weight"].default_value=sss
    return m
def assign(ob, m):
    ob.data.materials.clear(); ob.data.materials.append(m)
tissue_m=claymat("TissueClay",(0.72,0.62,0.52),0.55,0.25)
for ob in (T,earL,earR,JAW): assign(ob,tissue_m)
assign(SK, claymat("Bone",(0.88,0.84,0.76),0.5))
assign(SKM, claymat("Bone",(0.88,0.84,0.76),0.5))
assign(MUS, claymat("Muscle",(0.55,0.22,0.18),0.45))
assign(ARC, claymat("MouthInterior",(0.45,0.2,0.18),0.35))
assign(TON, claymat("Tongue",(0.62,0.3,0.3),0.35))

# ---- vertex groups (v2 scheme, index lists)
def wpos(ob, v): return ob.matrix_world @ v.co
groups={}
gt={}
tv=list(T.data.vertices)
def sel(fn): return [v.index for v in tv if fn(wpos(T,v))]
gt["Muzzle"]=sel(lambda w: w.y>eye_y-0.02)
gt["MuzzleTip"]=sel(lambda w: w.y>nose_y-0.16)
gt["NoseLeather"]=sel(lambda w: w.y>nose_y-0.09 and abs(w.x)<0.095)
gt["MuzzleBridge"]=sel(lambda w: w.y>eye_y-0.02 and w.z>pal+0.13 and abs(w.x)<0.105)
gt["Cranium"]=sel(lambda w: w.y<=eye_y+0.06 and w.z>pal+0.02)
gt["CraniumDome"]=sel(lambda w: w.z>top-0.13)
gt["CheekL"]=sel(lambda w: abs(w.y+0.02)<0.17 and w.z<eye_z+0.05 and w.x>0)
gt["CheekR"]=sel(lambda w: abs(w.y+0.02)<0.17 and w.z<eye_z+0.05 and w.x<0)
for side,sx in (("L",1),("R",-1)):
    ec=Vector((sx*eye_x, eye_y, eye_z))
    gt["Brow"+side]=sel(lambda w,ec=ec,sx=sx: (w-ec).length<0.215 and w.z>eye_z+0.02 and w.x*sx>0)
    gt["EyeSocket"+side]=sel(lambda w,ec=ec,sx=sx: (w-ec).length<0.155 and w.x*sx>0)
groups["TissueHead"]=gt
for ob,tag in ((earL,"L"),(earR,"R")):
    vs=[v.co for v in ob.data.vertices]
    low=sorted(vs, key=lambda v:v.z)[:max(8,len(vs)//7)]
    base=Vector((0,0,0))
    for v in low: base+=v
    base/=len(low)
    tip=max(vs, key=lambda v:(v-base).length); ax=(tip-base); L2=ax.length
    g={}
    g["Ear_"+tag]=list(range(len(vs)))
    g["EarBase_"+tag]=[i for i,v in enumerate(vs) if ((v-base).dot(ax)/L2)/L2<0.38]
    g["EarTip_"+tag]=[i for i,v in enumerate(vs) if ((v-base).dot(ax)/L2)/L2>0.68]
    groups["Ear_"+tag]=g
gj={"Jaw": list(range(len(JAW.data.vertices))),
    "Chin": [v.index for v in JAW.data.vertices if (v.co+H).y>nose_y-0.18]}
groups["Jaw"]=gj
with open("/home/hatch/workspace/anthroforge-v2/base-head-v3/work/groups_v3.json","w") as f: json.dump(groups,f)
print("groups:", {k:{g:len(v) for g,v in vv.items()} for k,vv in groups.items()})

# ---- final measure
bpy.context.view_layer.update()
jw=[JAW.matrix_world @ v.co for v in JAW.data.vertices]
band=[v for v in jw if H.y-0.03<=v.y<=H.y+0.05]
eb=grafted["Eyeball_L"]; ebv=[v.co for v in eb.data.vertices]
ball=max(max(v.x for v in ebv)-min(v.x for v in ebv), max(v.y for v in ebv)-min(v.y for v in ebv), max(v.z for v in ebv)-min(v.z for v in ebv))
fm={
 "JawLength": round(max(v.y for v in jw)-H.y,4),
 "JawWidth": round(max(v.x for v in band)-min(v.x for v in band),4) if band else None,
 "RamusDepth": round(max(v.z for v in band)-min(v.z for v in band),4) if band else None,
 "FullHeadHeight": round(top-min(v.z for v in jw),4),
 "Hinge": [round(v,4) for v in H],
 "OrbitDiameter_grafted": round(ball,4),
 "EyeCentreSpacing_grafted": round(2*eye_x*0.98,4),
 "Interorbital_grafted": round(2*eye_x*0.98-ball,4),
 "OrbitHeight_final": round(eye_z-pal,4),
 "SkullHeight_domeRise_final": round(top-eye_z,4),
 "eye_centre_final": [round(eye_x*0.98,4), round(eye_y-0.008,4), round(eye_z,4)],
}
print("FINAL", json.dumps(fm,indent=1))
with open("/home/hatch/workspace/anthroforge-v2/base-head-v3/work/final_measure.json","w") as f: json.dump(fm,f,indent=1)

# remove source eyes from deliverable scene
bpy.data.objects.remove(EYESRC, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/work/stageD.blend")
print("SAVED D; objects:", [o.name for o in bpy.data.objects])
