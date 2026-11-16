import bpy, time, json
start=time.time()
bpy.ops.wm.read_factory_settings(use_empty=True)
src='/home/hatch/workspace/bodies-3d/kaleaon-sacdrape/kaleaon_sacdrape.blend'
names=['Sac','Shaft_1','Shaft_2','Shaft_3','Shaft_4','KaleaonRig']
with bpy.data.libraries.load(src, link=False) as (from_data,to_data):
    to_data.objects=[n for n in names if n in from_data.objects]
print('loaded', [o.name if o else None for o in to_data.objects], 'elapsed', time.time()-start)
for o in to_data.objects:
    if o: bpy.context.scene.collection.objects.link(o)
print('objects in scene', [o.name for o in bpy.context.scene.objects])
print('arm bones', len(bpy.data.objects['KaleaonRig'].data.bones))
