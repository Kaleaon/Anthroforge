"""Create species-specific modular head/limb/wing add-ons in Blender.

Run from Blender:
 blender --background --python scripts/build_species_addons.py -- --profile all --output ./addons
All outputs are separate named meshes intended for fitting/rigging, not final assets.
"""
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
PROFILE_FILE=ROOT/"species_profiles.v1.json"

def parse():
 a=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
 p=argparse.ArgumentParser();p.add_argument("--profile",default="all");p.add_argument("--output",default="./species-addons");return p.parse_args(a)

def reset():
 bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
 for m in list(bpy.data.meshes):
  if m.users==0:bpy.data.meshes.remove(m)

def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);return m

def uv(n,loc,scale,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=loc)
 o=bpy.context.object;o.name=n;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 return o

def tube(n,pts,rs,m,sides=12):
 ps=[Vector(p) for p in pts];v=[];f=[]
 for j,p in enumerate(ps):
  d=(ps[min(j+1,len(ps)-1)]-ps[max(j-1,0)]).normalized();h=Vector((0,0,1)) if abs(d.z)<.9 else Vector((0,1,0));u=d.cross(h).normalized();w=d.cross(u).normalized();r=rs[j] if isinstance(rs,list) else rs
  for i in range(sides):
   a=2*math.pi*i/sides;v.append(tuple(p+r*(math.cos(a)*u+math.sin(a)*w)))
 for j in range(len(ps)-1):
  for i in range(sides):
   a=j*sides+i;b=j*sides+(i+1)%sides;f.append((a,b,b+sides,a+sides))
 f.append(tuple(range(sides-1,-1,-1)));base=(len(ps)-1)*sides;f.append(tuple(base+i for i in range(sides)))
 me=bpy.data.meshes.new(n+"_Mesh");me.from_pydata(v,[],f);me.materials.append(m);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o)
 for p in me.polygons:p.use_smooth=True
 return o

def build(p,out):
 reset(); ident=p["id"].replace(".","_"); family=p["family"]; detail=mat("AF_"+family+"_Addon",(0.25,.27,.30)); membrane=mat("AF_"+family+"_Membrane",(.38,.40,.43))
 # Species-specific cranial add-ons.
 if family in ("canid","vulpine"):
  for s,lr in [(-1,"L"),(1,"R")]:
   tube(ident+"_Pinna_"+lr,[(s*.09,-.02,1.91),(s*.12,-.02,2.03),(s*.17,-.01,2.16)],[.075,.052,.002],detail)
 elif family=="feline":
  for s,lr in [(-1,"L"),(1,"R")]:
   tube(ident+"_RoundedEar_"+lr,[(s*.10,-.02,1.91),(s*.14,-.01,2.00),(s*.17,0,2.07)],[.07,.055,.002],detail)
 elif family=="equine":
  for s,lr in [(-1,"L"),(1,"R")]:
   tube(ident+"_HorseEar_"+lr,[(s*.08,-.02,1.94),(s*.10,-.02,2.08),(s*.13,-.01,2.19)],[.06,.04,.002],detail)
 elif family=="draconic":
  for s,lr in [(-1,"L"),(1,"R")]:
   tube(ident+"_Horn_"+lr,[(s*.11,-.03,1.91),(s*.17,-.04,2.04),(s*.22,-.08,2.20)],[.07,.045,.001],detail)
   tube(ident+"_JawFin_"+lr,[(s*.13,.02,1.78),(s*.20,.03,1.72),(s*.24,.06,1.65)],[.05,.035,.001],membrane)
 elif family=="avian":
  for s,lr in [(-1,"L"),(1,"R")]:
   tube(ident+"_Crest_"+lr,[(s*.05,-.04,1.91),(s*.08,-.07,2.05),(s*.12,-.10,2.16)],[.05,.035,.001],detail)
   # Wing silhouette is a separate module, two broad feather-like lofts.
   uv(ident+"_WingRoot_"+lr,(s*.32,-.03,1.39),(.18,.22,.20),membrane)
   tube(ident+"_WingFingerA_"+lr,[(s*.35,-.04,1.42),(s*.60,-.10,1.52),(s*.82,-.16,1.49)],[.10,.07,.001],membrane)
   tube(ident+"_WingFingerB_"+lr,[(s*.35,-.04,1.37),(s*.58,-.18,1.32),(s*.76,-.27,1.25)],[.09,.06,.001],membrane)
 elif family=="serpentine":
  for s,lr in [(-1,"L"),(1,"R")]:
   tube(ident+"_CrestFin_"+lr,[(s*.08,-.02,1.88),(s*.12,-.04,2.00),(s*.16,-.08,2.10)],[.045,.03,.001],membrane)
 # Foot add-ons: equine gets broad hoof caps, others paw/toe/claw sets.
 if family=="equine":
  for s,lr in [(-1,"L"),(1,"R")]:
   uv(ident+"_Hoof_"+lr,(s*.18,.10,.04),(.085,.13,.075),detail)
   tube(ident+"_Fetlock_"+lr,[(s*.18,.02,.12),(s*.18,.03,.20),(s*.18,.04,.26)],[.06,.05,.04],membrane)
 else:
  for s,lr in [(-1,"L"),(1,"R")]:
   for i in range(4):
    x=s*.18+(i-1.5)*.035
    uv(ident+"_Toe_"+lr+str(i),(x,.14,.055),(.025,.075,.03),detail)
    tube(ident+"_Claw_"+lr+str(i),[(x,.19,.055),(x,.25,.045),(x,.29,.065)],[.016,.009,.001],detail,8)
 # Dragon dorsal scutes and optional tail fin; avian feather fan.
 if family=="draconic":
  for i in range(7):
   y=.45-i*.17;z=1.58-(i*.025)
   tube(ident+"_DorsalScute_"+str(i),[(0,y,z),(0,y-.03,z+.10),(0,y-.08,z+.02)],[.045,.001,.001],detail,8)
 if family=="avian":
  for i in range(7):
   x=(i-3)*.055
   tube(ident+"_TailFeather_"+str(i),[(x,-.55,.86),(x*1.3,-.78,.91),(x*1.5,-1.02,.94)],[.025,.018,.001],membrane,8)
 scene=bpy.context.scene;scene["anthroforge_species_id"]=p["id"];scene["anthroforge_addon_stage"]="unrigged_species_modules"
 out.mkdir(parents=True,exist_ok=True);blend=out/(ident+"_addons.blend");glb=out/(ident+"_addons.glb")
 bpy.ops.wm.save_as_mainfile(filepath=str(blend));bpy.ops.export_scene.gltf(filepath=str(glb),export_format="GLB",export_apply=False)
 return blend,glb

def main():
 a=parse();data=json.loads(PROFILE_FILE.read_text());ps=data["profiles"] if a.profile=="all" else [p for p in data["profiles"] if p["id"]==a.profile]
 if not ps:raise SystemExit("Unknown profile "+a.profile)
 for p in ps:print("BUILT",p["id"],*build(p,Path(a.output).resolve()))
if __name__=="__main__":main()
