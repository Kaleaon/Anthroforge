import bpy, math
# --- render Piece006/010 alone
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/work/head_source.blend")
T=bpy.data.objects["TissueHead_source"]; T.hide_render=True
E=bpy.data.objects["Eye_source"]; E.hide_render=True
def mat(name,rgb):
    m=bpy.data.materials.new(name)
    bsdf=m.node_tree.nodes["Principled BSDF"]; bsdf.inputs["Base Color"].default_value=(*rgb,1); bsdf.inputs["Roughness"].default_value=0.7
    return m
P6=bpy.data.objects["Piece006"]; P10=bpy.data.objects["Piece010"]
P6.data.materials.clear(); P6.data.materials.append(mat("r",(0.85,0.3,0.25)))
P10.data.materials.clear(); P10.data.materials.append(mat("b",(0.25,0.5,0.9)))
for nm,ob in (("P6",P6),("P10",P10)):
    vs=[v.co for v in ob.data.vertices]
    print(nm,"z>pal(-0.137):",sum(1 for v in vs if v.z>-0.137),"of",len(vs),"| y range %.2f..%.2f z %.2f..%.2f"%(min(v.y for v in vs),max(v.y for v in vs),min(v.z for v in vs),max(v.z for v in vs)))
sc=bpy.context.scene; sc.render.engine='CYCLES'; sc.cycles.samples=16; sc.cycles.use_denoising=True
sc.render.resolution_x=640; sc.render.resolution_y=640
w=bpy.data.worlds.new("W"); sc.world=w; w.node_tree.nodes["Background"].inputs[0].default_value=(0.45,0.45,0.45,1)
cam=bpy.data.objects.new("Cam",bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type='ORTHO'; cam.data.ortho_scale=0.85
sun=bpy.data.objects.new("Sun",bpy.data.lights.new("Sun",'SUN')); sc.collection.objects.link(sun); sun.rotation_euler=(0.9,0.3,0.5); sun.data.energy=3.5
for name,loc,rot in (("id6_side",(1.4,0.1,-0.15),(math.radians(90),0,math.radians(90))),("id6_front",(0,1.4,-0.15),(math.radians(90),0,math.radians(180)))):
    cam.location=loc; cam.rotation_euler=rot
    sc.render.filepath=f"/home/hatch/workspace/anthroforge-v2/base-head-v3/work/{name}.png"
    bpy.ops.render.render(write_still=True)
print("ID DONE")
