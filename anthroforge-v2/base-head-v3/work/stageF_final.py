import bpy, json, math, os
from mathutils import Vector, Matrix

OUT="/home/hatch/workspace/anthroforge-v2/base-head-v3"
WORK=OUT+"/work"

def cent(vs):
    c=Vector((0,0,0))
    for v in vs: c+=v
    return c/len(vs)
def measure(tissue, ears, eye_objs, pal_obj, jaw_obj=None, ear_excl=None):
    tv=[tissue.matrix_world @ v.co for v in tissue.data.vertices]
    tvx=[v for i,v in enumerate(tv) if not ear_excl or i not in ear_excl]
    nose=max(v.y for v in tv); occ=min(v.y for v in tv); L=nose-occ
    top=max(v.z for v in tv)
    pal=max(v.z for v in [pal_obj.matrix_world @ v.co for v in pal_obj.data.vertices] if v.y>0.18)
    evs=[]
    for eo in eye_objs: evs += [eo.matrix_world @ v.co for v in eo.data.vertices]
    el=[v for v in evs if v.x<0]; er=[v for v in evs if v.x>=0]
    cl,cr=cent(el),cent(er); ec=(cl+cr)/2
    ball=max(max(v.x for v in el)-min(v.x for v in el), max(v.y for v in el)-min(v.y for v in el), max(v.z for v in el)-min(v.z for v in el))
    ycan=ec.y+0.5*(nose-ec.y)
    sec=[v for v in tv if abs(v.y-ycan)<0.02]
    cran=[v for v in tvx if ec.y-0.42<=v.y<=ec.y-0.06 and v.z>=top-0.11]
    estats=[]
    for eo in ears:
        vs=[eo.matrix_world @ v.co for v in eo.data.vertices]
        low=sorted(vs, key=lambda v:v.z)[:max(8,len(vs)//7)]
        b=cent(low); tip=max(vs, key=lambda v:(v-b).length)
        estats.append((b,tip,(tip-b).length))
    eb=(estats[0][0]+estats[1][0])/2 if estats else Vector((0,0,pal+0.25))
    if not estats:
        r_extra={}
    r={"L":round(L,4),
      "ZB":round(max(v.x for v in tvx)-min(v.x for v in tvx),4),
      "CraniumWidth_domeShell":round(max(v.x for v in cran)-min(v.x for v in cran),4) if cran else None,
      "MuzzleWidth":round(max(v.x for v in sec)-min(v.x for v in sec),4) if sec else None,
      "MuzzleDepth":round((max(v.z for v in sec)-pal),4) if sec else None,
      "SkullHeight_domeRise":round(top-ec.z,4),
      "MuzzleFrac_antOrbit":round((nose-(ec.y+ball/2))/L,4),
      "OrbitDiameter":round(ball,4),
      "Interorbital":round(abs(cl.x-cr.x)-ball,4),
      "OrbitHeight":round(ec.z-pal,4),
      "OrbitRise":round((max((v.z for v in tv if abs(v.y-ec.y)<0.03), default=ec.z)-ec.z),4),
      "EarLength":round((estats[0][2]+estats[1][2])/2,4) if estats else None,
      "EarBaseHeight_abovePalate":round(eb.z-pal,4) if estats else None,
      "EarBase_belowSkullTop":round(top-eb.z,4) if estats else None,
      "EarTip_aboveSkullTop":round(max(estats[0][1].z,estats[1][1].z)-top,4) if estats else None,
      "eye_centre":[round(v,4) for v in ec], "pal_z":round(pal,4)}
    hinge_y = eb.y-0.02; hinge_z = pal+0.055
    r["EarTipHeight_abovePalate"]=round((max(estats[0][1].z,estats[1][1].z)-pal),4) if estats else None
    if jaw_obj is not None:
        jw=[jaw_obj.matrix_world @ v.co for v in jaw_obj.data.vertices]
        band=[v for v in jw if hinge_y-0.03<=v.y<=hinge_y+0.05]
        r["JawLength"]=round(max(v.y for v in jw)-hinge_y,4)
        r["JawWidth"]=round(max(v.x for v in band)-min(v.x for v in band),4) if band else None
        r["RamusDepth"]=round(max(v.z for v in band)-min(v.z for v in band),4) if band else None
        r["FullHeadHeight"]=round(top-min(v.z for v in jw),4)
    else:
        band=[v for v in tv if hinge_y-0.03<=v.y<=hinge_y+0.05 and v.z<hinge_z+0.10]
        lowb=[v for v in tv if v.z<pal+0.02]
        r["JawLength_proxy"]=round((max(v.y for v in lowb)-hinge_y),4) if lowb else None
        r["JawWidth_proxy"]=round(max(v.x for v in band)-min(v.x for v in band),4) if band else None
        r["RamusDepth_proxy"]=round(max(v.z for v in band)-min(v.z for v in band),4) if band else None
    return r

# ---------- source measures
bpy.ops.wm.open_mainfile(filepath=WORK+"/head_source.blend")
_T0=bpy.data.objects["TissueHead_source"]
_excl=set()
for _v in _T0.data.vertices:
    _w=0.0
    for _g in _v.groups:
        if _T0.vertex_groups[_g.group].name in ("Ear.L","Ear.R"): _w+=_g.weight
    if _w>0.5: _excl.add(_v.index)
src=measure(_T0, [], [bpy.data.objects["Eye_source"]], bpy.data.objects["Piece006"], ear_excl=_excl)
# source ear stats via vgroups on the source tissue
T0=bpy.data.objects["TissueHead_source"]
ew=[]
for v in T0.data.vertices:
    w=0.0
    for g in v.groups:
        if T0.vertex_groups[g.group].name in ("Ear.L","Ear.R"): w+=g.weight
    ew.append(w)
# source ear stats computed inline from weight mask
class V: 
    def __init__(s,co): s.co=co
earL_vs=[V(T0.matrix_world @ v.co) for v in T0.data.vertices if ew[v.index]>0.5 and v.co.x>0]
earR_vs=[V(T0.matrix_world @ v.co) for v in T0.data.vertices if ew[v.index]>0.5 and v.co.x<0]
def ear_stats(vs):
    low=sorted(vs, key=lambda v:v.co.z)[:max(8,len(vs)//7)]
    b=cent([v.co for v in low]); tip=max((v.co for v in vs), key=lambda c:(c-b).length)
    return b,tip,(tip-b).length
eL=ear_stats(earL_vs); eR=ear_stats(earR_vs)
src["EarLength"]=round((eL[2]+eR[2])/2,4)
src["EarBaseHeight_abovePalate"]=round(((eL[0].z+eR[0].z)/2)-src["pal_z"],4)
src["EarTipHeight_abovePalate"]=round(max(eL[1].z,eR[1].z)-src["pal_z"],4)
src["EarTip_aboveSkullTop"]=round(max(eL[1].z,eR[1].z)-max(v.z for v in [ _T0.matrix_world @ vv.co for vv in _T0.data.vertices]),4)
print("SOURCE", json.dumps(src,indent=1))

# ---------- result scene
bpy.ops.wm.open_mainfile(filepath=WORK+"/stageD.blend")
FINAL_NAMES=["TissueHead","Jaw","Ear_L","Ear_R","Eyeball_L","Eyeball_R","Iris_L","Iris_R","Pupil_L","Pupil_R",
             "Eyelid_L","Eyelid_R","LidMargin_L","LidMargin_R","NoseLeather","TeethArcade","Tongue","Throat",
             "NeckSocket","NeckSocketDisc"]
REF_NAMES=["Skull","SkullMandible","Muscles"]
O={n:bpy.data.objects[n] for n in FINAL_NAMES+REF_NAMES}
res=measure(O["TissueHead"], [O["Ear_L"],O["Ear_R"]], [O["Eyeball_L"],O["Eyeball_R"]], O["TeethArcade"], O["Jaw"])
print("RESULT", json.dumps(res,indent=1))

TARGETS={"ZB":0.58,"CraniumWidth_domeShell":0.36,"MuzzleWidth":0.17,"MuzzleDepth":0.20,
 "SkullHeight_domeRise":0.31,"MuzzleFrac_antOrbit":0.33,"OrbitDiameter":0.15,"Interorbital":0.19,
 "OrbitHeight":0.17,"OrbitRise":0.12,"EarLength":0.40,"JawLength":0.74,"JawWidth":0.40,"RamusDepth":0.28}
table={}
for k,t in TARGETS.items():
    v=res.get(k)
    table[k]={"measured":v,"target":t,"dev_pct":round(100*(v-t)/t,1) if v is not None else None,
              "source":src.get(k) or src.get(k+"_proxy")}
props={"meta":{"L_definition":"nose tip to occiput, tissue Y extent, normalised to 1.0",
               "targets":"species-head-spec.md neutral column; OrbitHeight target 0.22 = canid-felid mid-range (derived, see BUILD_NOTES)"},
       "result":table,
       "result_extra":{k:res[k] for k in ("EarBaseHeight_abovePalate","EarBase_belowSkullTop","EarTip_aboveSkullTop","FullHeadHeight","eye_centre","pal_z")},
       "source_cougar":src}
with open(OUT+"/proportions.json","w") as f: json.dump(props,f,indent=1)
import shutil
shutil.copy(WORK+"/groups_v3.json", OUT+"/neutral_base_head_v3.groups.json")

# ---------- exports
scene=bpy.context.scene
bpy.ops.object.select_all(action='DESELECT')
for n in FINAL_NAMES: O[n].select_set(True)
bpy.context.view_layer.objects.active=O["TissueHead"]
bpy.ops.export_scene.gltf(filepath=OUT+"/neutral_base_head_v3.glb", export_format='GLB', use_selection=True)
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.wm.save_as_mainfile(filepath=OUT+"/neutral_base_head_v3.blend")
print("EXPORTED")
json.dump({"src":src,"res":res}, open(WORK+"/final_tables.json","w"), indent=1)
