import bpy,json,bmesh
bpy.ops.wm.read_factory_settings(use_empty=True)
src='/home/hatch/workspace/bodies-3d/kaleaon-sacdrape/kaleaon_sacdrape.blend'
names=['Sac','Shaft_1','Shaft_2','Shaft_3','Shaft_4','KaleaonRig']
with bpy.data.libraries.load(src, link=False) as (f,t): t.objects=[n for n in names if n in f.objects]
for o in t.objects: bpy.context.scene.collection.objects.link(o)
out={}
for name in names[:-1]:
 o=bpy.data.objects[name]; bm=bmesh.new(); bm.from_mesh(o.data); vol=bm.calc_volume(); bm.free(); ws=[o.matrix_world@v.co for v in o.data.vertices]
 groups={}
 for g in o.vertex_groups:
  vals=[e.weight for v in o.data.vertices for e in v.groups if e.group==g.index]
  if vals: groups[g.name]={'n':len(vals),'min':round(min(vals),4),'max':round(max(vals),4),'mean':round(sum(vals)/len(vals),4)}
 out[name]={'verts':len(o.data.vertices),'polys':len(o.data.polygons),'vol_L':round(vol*1000,3),'min':[round(min(v[i] for v in ws),4) for i in range(3)],'max':[round(max(v[i] for v in ws),4) for i in range(3)],'shapekeys':[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [],'groups':groups,'materials':[m.name if m else None for m in o.data.materials]}
arm=bpy.data.objects['KaleaonRig']; out['bones']={n:{'head':[round(x,4) for x in arm.data.bones[n].head_local],'tail':[round(x,4) for x in arm.data.bones[n].tail_local],'parent':arm.data.bones[n].parent.name if arm.data.bones[n].parent else None} for n in ['CC_Base_Pelvis','Sac','Shaft_1_Base','Shaft_1_Tip','Shaft_2_Base','Shaft_2_Tip','Shaft_3_Base','Shaft_3_Tip','Shaft_4_Base','Shaft_4_Tip']}
open('/home/hatch/workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/work/loaded_parts.json','w').write(json.dumps(out,indent=1))
print(json.dumps(out,indent=1))
