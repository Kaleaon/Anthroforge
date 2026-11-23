"""Generate plan-specific species greybox meshes in Blender.

This complements build_species_blockouts.py with genuinely different
quadruped-feral, taur, and naga body layouts. It emits editable named objects;
these are topology/rig authoring blockouts, not final avatar meshes.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parents[1]
PROFILES = HERE / "species_profiles.v1.json"

def args():
    av = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--profile", default="all")
    p.add_argument("--plan", choices=["plan.quadruped_feral","plan.quadruped_taur","plan.naga","all"], default="all")
    p.add_argument("--output", default="./species-plan-blockouts")
    return p.parse_args(av)

def clear():
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    for block in list(bpy.data.meshes):
        if block.users == 0: bpy.data.meshes.remove(block)

def mat(name, rgba):
    m=bpy.data.materials.new(name); m.diffuse_color=(*rgba,1); return m

def ellipsoid(name, center, radii, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=center)
    o=bpy.context.object; o.name=name; o.scale=radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth=True
    return o

def tube(name, points, radii, material, sides=16):
    pts=[Vector(p) for p in points]; verts=[]; faces=[]
    for j,p in enumerate(pts):
        tangent=(pts[min(j+1,len(pts)-1)]-pts[max(j-1,0)]).normalized()
        helper=Vector((0,0,1)) if abs(tangent.z)<0.9 else Vector((0,1,0))
        u=tangent.cross(helper).normalized(); v=tangent.cross(u).normalized()
        radius=radii[j] if isinstance(radii,list) else radii
        for i in range(sides):
            a=2*math.pi*i/sides
            q=p+radius*(math.cos(a)*u+math.sin(a)*v)
            verts.append(tuple(q))
    for j in range(len(pts)-1):
        for i in range(sides):
            a=j*sides+i; b=j*sides+(i+1)%sides
            faces.append((a,b,b+sides,a+sides))
    faces.append(tuple(range(sides-1,-1,-1)))
    base=(len(pts)-1)*sides; faces.append(tuple(base+i for i in range(sides)))
    mesh=bpy.data.meshes.new(name+"_Mesh"); mesh.from_pydata(verts,[],faces); mesh.materials.append(material); mesh.update()
    obj=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(obj)
    for p in mesh.polygons:p.use_smooth=True
    return obj

def claw_set(prefix, x, y, z, scale, material):
    for i in range(3):
        dx=(i-1)*0.045*scale
        ellipsoid(prefix+"_Toe"+str(i+1),(x+dx,y+0.055*scale,z),(0.035*scale,0.075*scale,0.035*scale),material)
        tube(prefix+"_Claw"+str(i+1),[(x+dx,y+0.09*scale,z),(x+dx,y+0.15*scale,z-0.012*scale),(x+dx,y+0.18*scale,z+0.008*scale)],[0.018*scale,0.011*scale,0.001],material,8)

def build_feral(p, plan, out):
    clear(); body=mat("AF_"+p["family"]+"_Body",(0.47,0.49,0.52)); detail=mat("AF_"+p["family"]+"_Detail",(0.25,0.27,0.30))
    ident=p["id"].replace(".","_")+"_"+plan.replace(".","_")
    t=p["torso"]; h=p["head"]; limbs=p["limbs"]
    # Longitudinal torso axis is Y; front is +Y.
    ellipsoid(ident+"_Ribcage",(0,0.30,0.93),(t["shoulder_width"]*.57,.58,.36),body)
    ellipsoid(ident+"_Abdomen",(0,-.12,.83),(t["waist_width"]*.50,.48,.29),body)
    ellipsoid(ident+"_Pelvis",(0,-.48,.86),(t["hip_width"]*.55,.34,.32),body)
    tube(ident+"_Neck",[(0,.62,1.02),(0,.82,1.17),(0,1.02,1.31)],[.19,.16,.13],body)
    ellipsoid(ident+"_Skull",(0,1.13,1.34),(h["width"]*.52,h["length"]*.48,h["height"]*.50),body)
    ellipsoid(ident+"_Muzzle",(0,1.36,1.28),(h["width"]*.31,max(.07,h["muzzle_length"]*.40),h["height"]*.22),detail)
    # Four separately named limb chains with shoulder/hip stations.
    for xside,lr in [(-1,"L"),(1,"R")]:
      for yside,fb in [(1,"Fore"),(-1,"Hind")]:
        x=xside*(t["shoulder_width"]*.39 if fb=="Fore" else t["hip_width"]*.36)
        y=.53 if fb=="Fore" else -.56
        foot=(x,y+.05,.12)
        ellipsoid(ident+"_"+fb+"Upper_"+lr,(x,y,.70),(.12,.19,.27),body)
        tube(ident+"_"+fb+"Lower_"+lr,[(x,y,.58),(x,y-.03,.34),foot],[.09,.07,.055],body)
        paw_scale=limbs["paw_scale"] or 1.0
        ellipsoid(ident+"_"+fb+"Paw_"+lr,(x,y+.10,.09),(.11*paw_scale,.18*paw_scale,.07),detail)
        claw_set(ident+"_"+fb+"Paw_"+lr,x,y+.17,.09,paw_scale,detail)
    tube(ident+"_Tail",[(0,-.70,.92),(0,-.95,.82),(0,-1.20,.70),(0,-1.42,.64)],[.09,.075,.045,.008],body)
    return finish(p,plan,ident,out)

def build_taur(p, plan, out):
    clear(); body=mat("AF_"+p["family"]+"_Body",(0.47,0.49,0.52)); detail=mat("AF_"+p["family"]+"_Detail",(0.25,0.27,0.30))
    ident=p["id"].replace(".","_")+"_"+plan.replace(".","_"); t=p["torso"]; h=p["head"]
    # Human-like upper torso is mounted at the front of a four-legged lower body.
    ellipsoid(ident+"_UpperTorso",(0,0.40,1.42),(t["shoulder_width"]*.52,.30,.48),body)
    ellipsoid(ident+"_UpperPelvis",(0,.24,1.08),(t["hip_width"]*.46,.25,.25),body)
    tube(ident+"_Neck",[(0,.48,1.70),(0,.61,1.91)],[.15,.12],body)
    ellipsoid(ident+"_Skull",(0,.68,2.03),(h["width"]*.5,h["length"]*.48,h["height"]*.5),body)
    ellipsoid(ident+"_Muzzle",(0,.87,1.99),(h["width"]*.30,max(.06,h["muzzle_length"]*.35),h["height"]*.20),detail)
    ellipsoid(ident+"_QuadrupedRibcage",(0,-.30,.90),(t["shoulder_width"]*.58,.62,.34),body)
    ellipsoid(ident+"_QuadrupedAbdomen",(0,-.78,.83),(t["waist_width"]*.52,.40,.28),body)
    ellipsoid(ident+"_QuadrupedPelvis",(0,-1.12,.87),(t["hip_width"]*.58,.36,.33),body)
    for xside,lr in [(-1,"L"),(1,"R")]:
      # Human arms
      x=xside*t["shoulder_width"]*.57
      tube(ident+"_Arm_"+lr,[(xside*.20,.40,1.55),(x,.35,1.20),(x,.40,.96)],[.09,.075,.055],body)
      ellipsoid(ident+"_Hand_"+lr,(x,.43,.91),(.07,.09,.10),detail)
      # Four equine/canid lower-body legs, front and rear
      for y,tag in [(-.02,"Front"),(-1.12,"Rear")]:
        lx=xside*(t["shoulder_width"]*.39 if tag=="Front" else t["hip_width"]*.40)
        tube(ident+"_"+tag+"Leg_"+lr,[(lx,y,.93),(lx,y-.03,.57),(lx,y+.03,.27),(lx,y+.11,.12)],[.12,.095,.055,.035],body)
        ellipsoid(ident+"_"+tag+"Foot_"+lr,(lx,y+.16,.08),(.10,.16,.06),detail)
        claw_set(ident+"_"+tag+"Foot_"+lr,lx,y+.20,.08,.8,detail)
    tube(ident+"_Tail",[(0,-1.36,.92),(0,-1.62,.76),(0,-1.85,.64)],[.08,.05,.006],body)
    return finish(p,plan,ident,out)

def build_naga(p, plan, out):
    clear(); body=mat("AF_"+p["family"]+"_Body",(0.47,0.49,0.52)); detail=mat("AF_"+p["family"]+"_Detail",(0.25,0.27,0.30))
    ident=p["id"].replace(".","_")+"_"+plan.replace(".","_"); t=p["torso"]; h=p["head"]
    ellipsoid(ident+"_Chest",(0,0,.98),(t["shoulder_width"]*.5,.27,.38),body)
    ellipsoid(ident+"_Shoulder",(0,.05,1.27),(t["shoulder_width"]*.55,.28,.24),body)
    tube(ident+"_Neck",[(0,.18,1.34),(0,.28,1.53)],[.13,.11],body)
    ellipsoid(ident+"_Skull",(0,.36,1.66),(h["width"]*.5,h["length"]*.47,h["height"]*.5),body)
    ellipsoid(ident+"_Muzzle",(0,.54,1.62),(h["width"]*.28,max(.06,h["muzzle_length"]*.35),h["height"]*.2),detail)
    # One continuous axial coil tube with variable radius; this is the actual
    # naga body silhouette, not a biped pelvis plus detached tail.
    points=[]; radii=[]
    for i in range(49):
        q=i/48
        angle=2*math.pi*1.35*q
        points.append((.62*math.cos(angle),-.22-.62*math.sin(angle)-.35*q,.24+.13*math.sin(math.pi*q)))
        radii.append(.31*(1-.72*q))
    tube(ident+"_AxialCoil",points,radii,body,20)
    return finish(p,plan,ident,out)

def finish(p,plan,ident,out):
    scene=bpy.context.scene
    scene["anthroforge_species_id"]=p["id"]; scene["anthroforge_body_plan"]=plan
    scene["anthroforge_mesh_stage"]="plan_specific_greybox_unrigged"
    scene["anthroforge_profile_json"]=json.dumps(p,sort_keys=True)
    out.mkdir(parents=True,exist_ok=True)
    blend=out/(ident+".blend"); glb=out/(ident+".glb")
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format="GLB",export_apply=False)
    return blend,glb

def main():
    a=args(); data=json.loads(PROFILES.read_text())
    profiles=data["profiles"] if a.profile=="all" else [p for p in data["profiles"] if p["id"]==a.profile]
    if not profiles: raise SystemExit("Unknown species profile: "+a.profile)
    plans=["plan.quadruped_feral","plan.quadruped_taur","plan.naga"] if a.plan=="all" else [a.plan]
    out=Path(a.output).resolve()
    for p in profiles:
      for plan in plans:
        if plan not in p.get("supported_plans", [p["body_plan"]]):
            print("SKIP", p["id"], plan, "not declared compatible")
            continue
        if plan=="plan.naga": result=build_naga(p,plan,out)
        elif plan=="plan.quadruped_taur": result=build_taur(p,plan,out)
        else: result=build_feral(p,plan,out)
        print("BUILT",p["id"],plan,*result)

if __name__=="__main__": main()
