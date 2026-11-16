import bpy, json, math, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
P = {"LENT_K":1.15, "ZB_AMP":0.09, "GLOBX":0.97, "MUZN":0.16, "DORS":-0.065,
     "JAWDP":0.030, "DOME":-0.005, "CRAN_C":0.0, "EAR_LEN":1.43, "EAR_W":0.92, "EAR_LIFT":0.015, "ZB_C":-0.06, "ZB_S":0.20, "ORBLIFT":-0.008, "FHDROP":0.10, "CRAN_AMP":-0.06, "CRANX":-0.125}
if argv: P.update(json.loads(argv[0]))
print("PARAMS", P)

bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/work/head_source.blend")
T = bpy.data.objects["TissueHead_source"]; T.name="TissueHead"
ARC = bpy.data.objects["Piece006"]; ARC.name="TeethArcade"
TON = bpy.data.objects["Piece010"]; TON.name="Tongue"
EYE = bpy.data.objects["Eye_source"]

def ramp(v,a,b):
    t=max(0.0,min(1.0,(v-a)/(b-a))); return t*t*(3-2*t)
def gauss(v,c,s): return math.exp(-((v-c)/s)**2)

# ---------- landmarks (source)
def allv(ob): return [v.co for v in ob.data.vertices]
tv = allv(T)
nose_y = max(v.y for v in tv)
eye_c = Vector((0,0,0))
evs = allv(EYE)
for v in evs: eye_c += v
eye_c /= len(evs)
eye_y, eye_z = eye_c.y, eye_c.z
pal_z = max(v.co.z for v in ARC.data.vertices if v.co.y>0.18)

# ---------- separate ears (vgroup mask), +x side = _L per v2 convention
groups={g.name:g.index for g in T.vertex_groups}
ear_w=[]
for v in T.data.vertices:
    w=0.0
    for g in v.groups:
        if T.vertex_groups[g.group].name in ("Ear.L","Ear.R"): w+=g.weight
    ear_w.append(w)
import bmesh
def split_faces(ob, keep_fn, newname):
    me=ob.data
    bm=bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    keep=[f for f in bm.faces if keep_fn(f)]
    # build new mesh from kept faces
    nme=bpy.data.meshes.new(newname)
    verts={}; nverts=[]; nfaces=[]
    bm.verts.ensure_lookup_table()
    for f in keep:
        nf=[]
        for v in f.verts:
            if v.index not in verts:
                verts[v.index]=len(nverts); nverts.append(v.co.copy())
            nf.append(verts[v.index])
        nfaces.append(nf)
    nme.from_pydata(nverts, [], nfaces); nme.update()
    nob=bpy.data.objects.new(newname, nme); bpy.context.collection.objects.link(nob)
    # remove kept faces from source
    bmesh.ops.delete(bm, geom=keep, context='FACES')
    bm.to_mesh(me); bm.free()
    # prune orphan verts
    used=set()
    for p in me.polygons: used.update(p.vertices)
    bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in range(len(bm.verts)) if i not in used], context='VERTS')
    bm.to_mesh(me); bm.free()
    return nob
earL = split_faces(T, lambda f: all(ear_w[v.index]>0.5 for v in f.verts) and sum(v.co.x for v in f.verts)/len(f.verts)>0, "Ear_L")
earR = split_faces(T, lambda f: all(ear_w[v.index]>0.5 for v in f.verts) and sum(v.co.x for v in f.verts)/len(f.verts)<0, "Ear_R")
print("ears split:", len(earL.data.vertices), len(earR.data.vertices), "tissue now", len(T.data.vertices))

# ---------- deformation fields
y_stop = eye_y - 0.02
def deform(ob, is_mouth=False):
    for v in ob.data.vertices:
        x,y,z = v.co.x, v.co.y, v.co.z
        # rostrum lengthen
        w = ramp(y, y_stop-0.03, y_stop+0.12)
        y += (P["LENT_K"]-1)*max(0.0, y-y_stop)*w
        # ZB narrow (tissue only)
        if not is_mouth:
            x *= 1 - P["ZB_AMP"]*gauss(y, P["ZB_C"], P["ZB_S"])
            x *= P["GLOBX"]
            # muzzle narrow
            x *= 1 - P["MUZN"]*ramp(y, y_stop, 0.30)*(1-0.35*ramp(y,0.34,0.50))
            # cranium width adjust (upper shell band)
            x *= 1 + P["CRAN_C"]*ramp(y, -0.40, -0.30)*(1-ramp(y,-0.06,0.02))*ramp(z, eye_z+0.04, eye_z+0.12)
        # dorsum lower (upper muzzle)
        z -= P["DORS"]*ramp(y, y_stop-0.05, y_stop+0.08)*ramp(z, pal_z+0.05, pal_z+0.15)
        # jaw deepen (below palate, front of rear ramp); mouth parts: fade out near palate
        jd = P["JAWDP"]*ramp(y, y_stop-0.20, y_stop+0.02)*(1-ramp(z, pal_z-0.06, pal_z+0.04))
        if is_mouth: jd *= (1-ramp(z, pal_z-0.10, pal_z-0.015))
        z -= jd
        # orbit lift (tissue only): raise socket/brow block around each eye centre
        if not is_mouth:
            for sx in (-1,1):
                dx=x-sx*0.1417; dy=y-eye_y; dz=z-eye_z
                d2=dx*dx+dy*dy+dz*dz
                z += P["ORBLIFT"]*max(0.0,1-d2/(0.23*0.23))**2
        # forehead drop at orbit station (tissue only): lowers dorsal profile toward eye line
        if not is_mouth:
            dx=x; dy=y-(eye_y+0.01); dz=z-(eye_z+0.20)
            d2=dx*dx+dy*dy+dz*dz
            z -= P["FHDROP"]*max(0.0,1-d2/(0.20*0.20))**2
        # braincase block narrowing (tissue only)
        if not is_mouth:
            x *= 1 + P["CRANX"]*(1-ramp(y, eye_y-0.04, eye_y+0.06))*ramp(z, pal_z+0.08, pal_z+0.16)
        # dome-shell narrowing (tissue only)
        if not is_mouth:
            x *= 1 + P["CRAN_AMP"]*ramp(y,-0.42,-0.32)*(1-ramp(y,-0.04,0.04))*ramp(z, eye_z+0.16, eye_z+0.24)
        # dome lower (tissue only)
        if not is_mouth:
            z -= P["DOME"]*ramp(z, eye_z+0.13, eye_z+0.22)*(1-ramp(y, eye_y-0.02, eye_y+0.10))
        v.co = (x,y,z)
deform(T); deform(ARC, True); deform(TON, True)
# ears: scale about base along ear axis
def ear_deform(ob):
    vs=[v.co for v in ob.data.vertices]
    low=sorted(vs, key=lambda v:v.z)[:max(8,len(vs)//7)]
    base=Vector((0,0,0))
    for v in low: base+=v
    base/=len(low)
    tip=max(vs, key=lambda v:(v-base).length)
    ax=(tip-base); axn=ax.normalized()
    for v in ob.data.vertices:
        d=v.co-base
        par=axn*d.dot(axn); perp=d-par
        v.co = base + par*P["EAR_LEN"] + perp*P["EAR_W"] + Vector((0,0,P["EAR_LIFT"]))
ear_deform(earL); ear_deform(earR)

# ---------- renormalise: L=1, bbox centre at origin (apply to all)
objs=[T,ARC,TON,earL,earR,EYE]
allt=[v.co for v in T.data.vertices]+[v.co for v in earL.data.vertices]+[v.co for v in earR.data.vertices]
L=max(v.y for v in allt)-min(v.y for v in allt)
cx=(max(v.x for v in allt)+min(v.x for v in allt))/2; cy=(max(v.y for v in allt)+min(v.y for v in allt))/2; cz=(max(v.z for v in allt)+min(v.z for v in allt))/2
for ob in objs:
    for v in ob.data.vertices:
        v.co = Vector(((v.co.x-cx)/L,(v.co.y-cy)/L,(v.co.z-cz)/L))
print("renorm L was", round(L,4))
LAND={"renorm_L":L,"centre":[cx,cy,cz],
      "eye_landmark_lifted":[0.1417, eye_y, eye_z+P["ORBLIFT"]],
      "eye_landmark_src":[0.1417, eye_y, eye_z]}
with open("/home/hatch/workspace/anthroforge-v2/base-head-v3/work/landmarks.json","w") as f: json.dump(LAND,f,indent=1)

# ---------- measure
def measure():
    tv=[v.co for v in T.data.vertices]
    nose=max(v.y for v in tv); occ=min(v.y for v in tv); L=nose-occ
    evs=[v.co for v in EYE.data.vertices]
    el=[v for v in evs if v.x<0]; er=[v for v in evs if v.x>=0]
    def cent(vs):
        c=Vector((0,0,0))
        for v in vs: c+=v
        return c/len(vs)
    cl,cr=cent(el),cent(er); ec=(cl+cr)/2
    ball=max(max(v.x for v in el)-min(v.x for v in el), max(v.y for v in el)-min(v.y for v in el), max(v.z for v in el)-min(v.z for v in el))
    pal=max(v.co.z for v in ARC.data.vertices if v.co.y>0.18)
    top=max(v.z for v in tv)
    ycan=ec.y+0.5*(nose-ec.y)
    sec=[v for v in tv if abs(v.y-ycan)<0.02]
    cran=[v for v in tv if ec.y-0.42<=v.y<=ec.y-0.06 and v.z>=top-0.11]
    ears=[]
    for ob in (earL,earR):
        vs=[v.co for v in ob.data.vertices]
        low=sorted(vs, key=lambda v:v.z)[:max(8,len(vs)//7)]
        b=cent(low); tip=max(vs, key=lambda v:(v-b).length)
        ears.append((b,tip,(tip-b).length))
    eb=(ears[0][0]+ears[1][0])/2
    return {
      "L":round(L,4), "ZB":round(max(v.x for v in tv)-min(v.x for v in tv),4),
      "CraniumWidth_domeShell":round(max(v.x for v in cran)-min(v.x for v in cran),4) if cran else None,
      "MuzzleWidth":round(max(v.x for v in sec)-min(v.x for v in sec),4) if sec else None,
      "MuzzleDepth":round((max(v.z for v in sec)-pal),4) if sec else None,
      "SkullHeight_domeRise":round(top-ec.z,4),
      "MuzzleFrac_antOrbit":round((nose-(ec.y+ball/2))/L,4),
      "MuzzleFrac_eyePlane":round((nose-ec.y)/L,4),
      "OrbitHeight":round(ec.z-pal,4),
      "EyeballDiam_source":round(ball,4),
      "Interorbital_source":round(abs(cl.x-cr.x)-ball,4),
      "EarLength":round((ears[0][2]+ears[1][2])/2,4),
      "EarBaseHeight_abovePalate":round(eb.z-pal,4),
      "EarBase_belowSkullTop":round(top-eb.z,4),
      "EarTip_aboveSkullTop":round(max(ears[0][1].z,ears[1][1].z)-top,4),
      "eye_centre":[round(v,4) for v in ec], "pal_z":round(pal,4), "skull_top":round(top,4),
      "ear_base_y":round(eb.y,4),
    }
m=measure()
print("MEASURE", json.dumps(m,indent=1))
with open("/home/hatch/workspace/anthroforge-v2/base-head-v3/work/stageC_measure.json","w") as f: json.dump({"params":P,"measure":m},f,indent=1)
bpy.ops.wm.save_as_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/work/stageC.blend")
print("SAVED C")
