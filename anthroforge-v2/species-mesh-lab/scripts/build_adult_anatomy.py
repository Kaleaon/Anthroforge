"""Adult-only parametric external-anatomy authoring module.

Generates editable, separately named anatomy components and a simple
articulation rig. This is a configurable procedural base, not a claim of
veterinary/medical accuracy or a finished production asset.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
CONFIG=ROOT/"anatomy_profiles.v1.json"

def parse():
    av=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--profile",default="adult_quad_canid")
    p.add_argument("--scale",type=float,default=1.0,help="0.15 micro through 8.0 extreme macro")
    p.add_argument("--count",type=int,default=None,help="1..4 independently editable members")
    p.add_argument("--output",default="./adult-anatomy")
    return p.parse_args(av)

def mat(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);return m

def make_tube(name,points,radii,material,sides=24):
    ps=[Vector(p) for p in points]; verts=[]; faces=[]
    for j,p in enumerate(ps):
        tangent=(ps[min(j+1,len(ps)-1)]-ps[max(j-1,0)]).normalized()
        helper=Vector((0,0,1)) if abs(tangent.z)<.9 else Vector((0,1,0))
        u=tangent.cross(helper).normalized();v=tangent.cross(u).normalized()
        r=radii[j] if isinstance(radii,list) else radii
        for i in range(sides):
            a=2*math.pi*i/sides
            verts.append(tuple(p+r*(math.cos(a)*u+math.sin(a)*v)))
    for j in range(len(ps)-1):
        for i in range(sides):
            a=j*sides+i;b=j*sides+(i+1)%sides
            faces.append((a,b,b+sides,a+sides))
    faces.append(tuple(range(sides-1,-1,-1)))
    base=(len(ps)-1)*sides;faces.append(tuple(base+i for i in range(sides)))
    me=bpy.data.meshes.new(name+"_Mesh");me.from_pydata(verts,[],faces);me.materials.append(material);me.update()
    ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
    for f in me.polygons:f.use_smooth=True
    return ob

def ellipsoid(name,loc,scale,material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=loc)
    o=bpy.context.object;o.name=name;o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(material)
    for f in o.data.polygons:f.use_smooth=True
    return o

def add_rig(prefix,count,segments):
    arm=bpy.data.armatures.new(prefix+"_RigData")
    rig=bpy.data.objects.new(prefix+"_Rig",arm);bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active=rig;rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    root=arm.edit_bones.new("GenBase");root.head=(0,0,.0);root.tail=(0,0,.12)
    sac=arm.edit_bones.new("GenSac");sac.head=(0,0,.0);sac.tail=(0,0,-.16);sac.parent=root
    for idx in range(count):
        x=(idx-(count-1)/2)*.14
        parent=root
        for j in range(segments):
            b=arm.edit_bones.new(f"Gen{idx+1:02d}_{j+1:02d}")
            b.head=(x,0,.08+j*.16);b.tail=(x,0,.08+(j+1)*.16);b.parent=parent
            parent=b
    bpy.ops.object.mode_set(mode="OBJECT");rig.select_set(False)
    return rig

def bind_segment_weights(obj,rig,bone_names,axis="z"):
    # Deterministic longitudinal weights; replace with authored weights in
    # production and run deformation QA before shipping.
    for name in bone_names:obj.vertex_groups.new(name=name)
    for v in obj.data.vertices:
        coord=v.co.z if axis=="z" else v.co.y
        idx=max(0,min(len(bone_names)-1,int(coord*len(bone_names))))
        obj.vertex_groups[bone_names[idx]].add([v.index],1.0,"REPLACE")
    mod=obj.modifiers.new("AdultAnatomy_Armature","ARMATURE");mod.object=rig
    obj.parent=rig

def build(cfg,scale,count,out):
    if not cfg.get("adult_only"):raise ValueError("Adult-only profile flag is required")
    if not .15<=scale<=8.0:raise ValueError("Scale must be between 0.15 and 8.0")
    if not 1<=count<=4:raise ValueError("Member count must be between 1 and 4")
    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    ident=cfg["id"];prefix="AF_"+ident
    skin=mat(prefix+"_Anatomy",(0.34,.22,.25));accent=mat(prefix+"_Detail",(.22,.13,.16))
    length=cfg["dimensions_m"]["length"]*scale
    girth=cfg["dimensions_m"]["girth"]*scale
    sac_w=cfg["dimensions_m"]["sac_width"]*scale
    sac_h=cfg["dimensions_m"]["sac_height"]*scale
    spacing=cfg["dimensions_m"]["member_spacing"]*scale
    # Shared base and sac are independent, editable mesh objects.
    base=ellipsoid(prefix+"_Base",(0,0,.0),(girth*.78,girth*.70,.13*scale),skin)
    sac=ellipsoid(prefix+"_Sac",(0,-.015,-sac_h*.36),(sac_w*.5,sac_w*.43,sac_h*.64),skin)
    details=[]
    for i in range(count):
        x=(i-(count-1)/2)*spacing
        # Profile stations keep taper and tip rounding adjustable per profile.
        stations=cfg["shape"]["stations"]
        points=[];radii=[]
        for j,s in enumerate(stations):
            z=.04*scale+length*s["t"]
            points.append((x,0,z))
            radii.append(girth*s["radius"])
        obj=make_tube(prefix+f"_Member_{i+1:02d}",points,radii,skin)
        obj["anthroforge_member_index"]=i+1
        obj["anthroforge_scale"]=scale
        details.append(obj)
    rig=add_rig(prefix,count,5)
    for i,obj in enumerate(details):
        names=[f"Gen{i+1:02d}_{j+1:02d}" for j in range(1,6)]
        bind_segment_weights(obj,rig,names)
    for obj in (base,sac):
        obj.parent=rig
    scene=bpy.context.scene
    scene["anthroforge_adult_only"]=True
    scene["anthroforge_anatomy_profile"]=ident
    scene["anthroforge_anatomy_scale"]=scale
    scene["anthroforge_anatomy_member_count"]=count
    scene["anthroforge_anatomy_stage"]="parametric_blockout_auto_weights"
    scene["anthroforge_anatomy_dimensions_json"]=json.dumps(cfg["dimensions_m"],sort_keys=True)
    out.mkdir(parents=True,exist_ok=True)
    stem=f"{ident}_s{scale:.2f}_n{count}"
    blend=out/(stem+".blend");glb=out/(stem+".glb")
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format="GLB",export_apply=False)
    return blend,glb

def main():
    a=parse();data=json.loads(CONFIG.read_text(encoding="utf-8"))
    if a.profile not in data["profiles"]:raise SystemExit("Unknown anatomy profile")
    cfg=data["profiles"][a.profile];count=a.count or cfg["default_member_count"]
    print("BUILT",*build(cfg,a.scale,count,Path(a.output).resolve()))
if __name__=="__main__":main()
