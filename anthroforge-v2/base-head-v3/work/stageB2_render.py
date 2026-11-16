import bpy, math
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/work/head_source.blend")
T=bpy.data.objects["TissueHead_source"]; E=bpy.data.objects["Eye_source"]
P6=bpy.data.objects["Piece006"]; P10=bpy.data.objects["Piece010"]
vs=[v.co for v in T.data.vertices]
print("TISSUE bbox x",min(v.x for v in vs),max(v.x for v in vs)," y",min(v.y for v in vs),max(v.y for v in vs)," z",min(v.z for v in vs),max(v.z for v in vs))
def mat(name,rgb):
    m=bpy.data.materials.new(name); m.use_nodes=True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(*rgb,1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=0.85
    return m
for ob,rgb in ((T,(0.78,0.74,0.68)),(P6,(0.85,0.3,0.25)),(P10,(0.25,0.5,0.9)),(E,(0.15,0.15,0.17))):
    ob.data.materials.clear(); ob.data.materials.append(mat(ob.name,rgb))
sc=bpy.context.scene
sc.render.engine='CYCLES'; sc.cycles.samples=24; sc.cycles.use_denoising=True; sc.render.resolution_x=700; sc.render.resolution_y=700
w=bpy.data.worlds.new("W"); sc.world=w; w.use_nodes=True
w.node_tree.nodes["Background"].inputs[0].default_value=(0.45,0.45,0.45,1)
cam=bpy.data.objects.new("Cam",bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=1.2
sun=bpy.data.objects.new("Sun",bpy.data.lights.new("Sun",'SUN')); sc.collection.objects.link(sun)
sun.rotation_euler=(0.9,0.3,0.5); sun.data.energy=3.5
for name,loc,rot in (("src_front",(0,1.7,0),(math.radians(90),0,math.radians(180))),
                     ("src_side",(1.7,0,0),(math.radians(90),0,math.radians(90))),
                     ("src_threequarter",(1.2,1.2,0.35),(math.radians(65),0,math.radians(135)))):
    cam.location=loc; cam.rotation_euler=rot
    sc.render.filepath=f"/home/hatch/workspace/anthroforge-v2/base-head-v3/work/{name}.png"
    bpy.ops.render.render(write_still=True)
print("DONE")
