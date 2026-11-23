import bpy, json, math
from mathutils import Vector
from mathutils.kdtree import KDTree

bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/work/head_source.blend")
T = bpy.data.objects["TissueHead_source"]
E = bpy.data.objects["Eye_source"]
P6 = bpy.data.objects["Piece006"]; P10 = bpy.data.objects["Piece010"]
print("Tissue groups:", [g.name for g in T.vertex_groups])
tv = [v.co.copy() for v in T.data.vertices]

def spans(vs):
    xs=[v.x for v in vs]; ys=[v.y for v in vs]; zs=[v.z for v in vs]
    return (min(xs),max(xs)),(min(ys),max(ys)),(min(zs),max(zs))
(x0,x1),(y0,y1),(z0,z1) = spans(tv)
L = y1-y0; nose_y, occ_y = y1, y0
# eyes
el=[v.co for v in E.data.vertices if v.co.x<0]; er=[v.co for v in E.data.vertices if v.co.x>=0]
def cent(vs): 
    c=Vector((0,0,0))
    for v in vs: c+=v
    return c/len(vs)
cenL, cenR = cent(el), cent(er)
eye_c = (cenL+cenR)/2
ball = max( spans(el)[0][1]-spans(el)[0][0], spans(el)[1][1]-spans(el)[1][0], spans(el)[2][1]-spans(el)[2][0] )
# palate from Piece006 top-front
p6f=[v.co for v in P6.data.vertices if v.co.y>0.18]
pal_z = max(v.z for v in p6f) if p6f else max(v.co.z for v in P6.data.vertices)
# ear mask: vgroups if present else geometric
groups={g.name:g.index for g in T.vertex_groups}
ear_idx=set()
if "Ear.L" in groups and "Ear.R" in groups:
    for v in T.data.vertices:
        w=0.0
        for g in v.groups:
            if T.vertex_groups[g.group].name in ("Ear.L","Ear.R"): w+=g.weight
        if w>0.5: ear_idx.add(v.index)
    print("ear mask from vgroups:", len(ear_idx))
if len(ear_idx)<40:
    ear_idx=set()
    topc = max(v.z for v in tv if abs(v.x)<0.05)
    for i,v in enumerate(tv):
        if v.z>topc-0.03 and v.y<eye_c.y and abs(v.x)>0.07: ear_idx.add(i)
    print("ear mask geometric:", len(ear_idx), "topc", topc)
earv=[tv[i] for i in ear_idx]; noear=[v for i,v in enumerate(tv) if i not in ear_idx]
skull_top = max(v.z for v in noear)
def band(vs, ylo, yhi, zlo=None, zhi=None):
    return [v for v in vs if ylo<=v.y<=yhi and (zlo is None or v.z>=zlo) and (zhi is None or v.z<=zhi)]
def width(vs): 
    return (max(v.x for v in vs)-min(v.x for v in vs)) if vs else 0.0
eye_y, eye_z = eye_c.y, eye_c.z
muz_len = nose_y-eye_y
y_can = eye_y + 0.5*muz_len
sec_can = band(noear, y_can-0.02, y_can+0.02)
cran = band(noear, eye_y-0.42, eye_y-0.10, zlo=eye_z-0.03)
hinge_y = None
earL=[v for v in earv if v.x<0]; earR=[v for v in earv if v.x>=0]
def ear_stats(ev):
    evs=sorted(ev, key=lambda v:v.z)
    base = cent(evs[:max(8,len(evs)//7)])
    tip = max(ev, key=lambda v:(v-base).length)
    return base, tip, (tip-base).length
bL,tL,lenL = ear_stats(earL); bR,tR,lenR = ear_stats(earR)
ear_base = (bL+bR)/2; ear_tip_z = max(tL.z,tR.z)
jawband = band(noear, ear_base.y-0.05, ear_base.y+0.07, zhi=eye_z)
jawlow  = [v for v in noear if v.z < pal_z+0.02]
chin_y  = max(v.y for v in jawlow) if jawlow else nose_y
frontlow= [v for v in noear if v.y>-0.20]
res = {
 "frame_L": L, "nose_y": nose_y, "occiput_y": occ_y,
 "eye_centre": list(eye_c), "eye_centre_spacing": abs(cenL.x-cenR.x),
 "eyeball_diameter": ball,
 "palatal_z": pal_z,
 "ZB_width": width(noear),
 "CraniumWidth": width(cran),
 "MuzzleFraction": muz_len/L,
 "MuzzleWidth_at_canine": width(sec_can),
 "MuzzleDepth_at_canine": (max(v.z for v in sec_can)-min(v.z for v in sec_can)) if sec_can else 0,
 "SkullHeight": skull_top - min(v.z for v in frontlow),
 "SkullTop_z": skull_top,
 "JawLength_proxy": chin_y - ear_base.y,
 "JawWidth_at_hinge": width(jawband),
 "RamusDepth_proxy": (max(v.z for v in jawband)-min(v.z for v in jawband)) if jawband else 0,
 "Interorbital": abs(cenL.x-cenR.x)-ball,
 "OrbitHeight": eye_z - pal_z,
 "EarLength": (lenL+lenR)/2,
 "EarBase_z": ear_base.z, "EarTip_z": ear_tip_z,
 "EarBaseHeight_above_palate": ear_base.z - pal_z,
 "EarBase_below_skulltop": skull_top - ear_base.z,
 "EarTip_above_skulltop": ear_tip_z - skull_top,
 "ear_verts": len(ear_idx), "tissue_verts": len(tv),
}
# asymmetry: mirror RMS on subsample
kd=KDTree(len(tv))
for i,v in enumerate(tv): kd.insert(v,i)
kd.balance()
import random
random.seed(1)
samp=random.sample(tv, min(300,len(tv)))
errs=[]
for v in samp:
    co,idx,dist = kd.find(Vector((-v.x, v.y, v.z)))
    errs.append(dist)
errs.sort()
res["mirror_asym_RMS"]= (sum(e*e for e in errs)/len(errs))**0.5
res["mirror_asym_p95"]= errs[int(0.95*len(errs))]
print(json.dumps(res,indent=1))
with open("/home/hatch/workspace/anthroforge-v2/base-head-v3/work/source_measurements.json","w") as f: json.dump(res,f,indent=1)

# --- ID render: colour pieces, front + side, Eevee
def mat(name, rgb):
    m=bpy.data.materials.new(name)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(*rgb,1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=0.85
    return m
for ob,rgb in ((T,(0.75,0.72,0.68)),(P6,(0.85,0.3,0.25)),(P10,(0.25,0.5,0.9)),(E,(0.2,0.2,0.22))):
    ob.data.materials.clear(); ob.data.materials.append(mat(ob.name, rgb))
sc=bpy.context.scene
sc.render.engine='BLENDER_EEVEE'; sc.render.resolution_x=640; sc.render.resolution_y=640
w=bpy.data.worlds.new("W"); sc.world=w
w.node_tree.nodes["Background"].inputs[0].default_value=(0.5,0.5,0.5,1); w.node_tree.nodes["Background"].inputs[1].default_value=1.0
cam=bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera=cam
sun=bpy.data.objects.new("Sun", bpy.data.lights.new("Sun",'SUN')); sc.collection.objects.link(sun)
sun.rotation_euler=(0.9,0.2,0.6); sun.data.energy=3
for name, loc, rot in (("id_front",(0,1.6,0.05),(math.radians(90),0,math.radians(180))), ("id_side",(1.6,0,0.05),(math.radians(90),0,math.radians(90)))):
    cam.location=loc; cam.rotation_euler=rot; cam.data.type='ORTHO'; cam.data.ortho_scale=1.15
    sc.render.filepath=f"/home/hatch/workspace/anthroforge-v2/base-head-v3/work/{name}.png"
    bpy.ops.render.render(write_still=True)
print("RENDERED")
