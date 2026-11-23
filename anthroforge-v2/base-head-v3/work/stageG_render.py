import bpy, math, os
from mathutils import Vector, Matrix
OUT="/home/hatch/workspace/anthroforge-v2/base-head-v3"
bpy.ops.wm.open_mainfile(filepath=OUT+"/neutral_base_head_v3.blend")
FINAL=["TissueHead","Jaw","Ear_L","Ear_R","Eyeball_L","Eyeball_R","Iris_L","Iris_R","Pupil_L","Pupil_R",
       "Eyelid_L","Eyelid_R","LidMargin_L","LidMargin_R","NoseLeather","TeethArcade","Tongue","Throat",
       "NeckSocket","NeckSocketDisc"]
REF=["Skull","SkullMandible","Muscles"]
O={n:bpy.data.objects[n] for n in FINAL+REF}
scene=bpy.context.scene
scene.render.engine='CYCLES'; scene.cycles.samples=40; scene.cycles.use_denoising=True
scene.render.resolution_x=950; scene.render.resolution_y=950
world=bpy.data.worlds.new('W'); scene.world=world
env=world.node_tree.nodes.new('ShaderNodeTexEnvironment')
env.image=bpy.data.images.load(os.path.expanduser('~/workspace/bodies-3d/parts-library/polyhaven/photo-studio-01-hdri/photo_studio_01_2k.hdr'))
bg=world.node_tree.nodes['Background']
world.node_tree.links.new(env.outputs['Color'], bg.inputs['Color']); bg.inputs['Strength'].default_value=0.85
bg2=world.node_tree.nodes.new('ShaderNodeBackground'); bg2.inputs['Color'].default_value=(0.145,0.145,0.15,1.0)
lp=world.node_tree.nodes.new('ShaderNodeLightPath'); mix=world.node_tree.nodes.new('ShaderNodeMixShader')
wo=world.node_tree.nodes['World Output']
world.node_tree.links.new(lp.outputs['Is Camera Ray'], mix.inputs['Fac'])
world.node_tree.links.new(bg.outputs['Background'], mix.inputs[1])
world.node_tree.links.new(bg2.outputs['Background'], mix.inputs[2])
world.node_tree.links.new(mix.outputs['Shader'], wo.inputs['Surface'])
cam_data=bpy.data.cameras.new('Cam'); cam_data.lens=82
cam=bpy.data.objects.new('Cam', cam_data); scene.collection.objects.link(cam); scene.camera=cam
def look_at(obj, target):
    obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
def shoot(name, pos, target=Vector((0,-0.01,0.0))):
    cam.location=pos; look_at(cam, target)
    scene.render.filepath=os.path.join(OUT,name)
    bpy.ops.render.render(write_still=True)
def show(names, on):
    for n in names: O[n].hide_render = not on
H=Vector((0,-0.2167,-0.1278))
def pose_jaw(deg, tongue=True):
    O["Jaw"].rotation_euler=(math.radians(deg),0,0)
    if tongue:
        M=Matrix.Translation(H) @ Matrix.Rotation(math.radians(deg),4,'X') @ Matrix.Translation(-H)
        TON=O["Tongue"]
        TON.matrix_world = M @ TON.matrix_world
        bpy.context.view_layer.update()
def unpose():
    O["Jaw"].rotation_euler=(0,0,0)
    O["Tongue"].matrix_world=Matrix.Identity(4)
    bpy.context.view_layer.update()
show(REF, False); show(FINAL, True)
shoot('render_front.png', Vector((0,2.1,0.10)), Vector((0,-0.01,0.05)))
shoot('render_side.png', Vector((2.1,0,0.06)), Vector((0,-0.01,0.02)))
# threequarter: jaw open, arcade hidden (fused sculpt - see notes), tongue rides jaw
O["TeethArcade"].hide_render=True
pose_jaw(-18)
shoot('render_threequarter.png', Vector((1.35,1.45,0.62)), Vector((0,-0.01,0.03)))
unpose()
# jaw-open proof, side, arcade visible
O["TeethArcade"].hide_render=False
pose_jaw(-20)
shoot('render_jaw_open.png', Vector((2.1,0,0.06)), Vector((0,-0.01,0.02)))
unpose()
# layers
show(FINAL, False); show(REF, True)
shoot('render_layers.png', Vector((1.35,1.45,0.62)))
print("MAIN RENDERS DONE")

# ---------- comparison: v1 / v2 / v3 front
for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
def append_from(path, names):
    with bpy.data.libraries.load(path, link=False) as (src,dst):
        dst.objects=[n for n in names if n in src.objects]
    got=[]
    for ob in dst.objects:
        bpy.context.collection.objects.link(ob); got.append(ob)
    return got
v1=append_from("/home/hatch/workspace/anthroforge-v2/base-head/neutral_base_head.blend", ["Head"])
v2=append_from("/home/hatch/workspace/anthroforge-v2/base-head-v2/neutral_base_head_v2.blend", ["TissueHead"])
v3=append_from(OUT+"/neutral_base_head_v3.blend", ["TissueHead","Ear_L","Ear_R","Jaw"])
print("comparison sets:", [o.name for o in v1], [o.name for o in v2], [o.name for o in v3])
clay=bpy.data.materials.new("Clay")
bsdf=clay.node_tree.nodes["Principled BSDF"]; bsdf.inputs["Base Color"].default_value=(0.72,0.62,0.52,1); bsdf.inputs["Roughness"].default_value=0.55
bsdf.inputs["Subsurface Weight"].default_value=0.25
def place(objs, xoff):
    vs=[]
    for ob in objs:
        vs += [ob.matrix_world @ v.co for v in ob.data.vertices]
    L=max(v.y for v in vs)-min(v.y for v in vs)
    c=Vector((sum(v.x for v in vs)/len(vs), sum(v.y for v in vs)/len(vs), sum(v.z for v in vs)/len(vs)))
    M=Matrix.Translation(Vector((xoff,0,0))) @ Matrix.Scale(1.0/L,4) @ Matrix.Translation(-c)
    for ob in objs:
        ob.matrix_world = M @ ob.matrix_world
        ob.data.materials.clear(); ob.data.materials.append(clay)
place(v1,-1.18); place(v2,0.0); place(v3,1.18)
cam.location=Vector((0,3.8,0.12)); look_at(cam, Vector((0,0,0.0)))
cam.data.lens=58
scene.render.filepath=os.path.join(OUT,"render_compare_v1v2v3.png")
bpy.ops.render.render(write_still=True)
print("COMPARISON DONE")
