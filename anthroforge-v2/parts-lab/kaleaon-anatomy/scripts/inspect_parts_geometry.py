import bpy,json,bmesh
bpy.ops.wm.open_mainfile(filepath='/home/hatch/workspace/bodies-3d/kaleaon-sacdrape/kaleaon_sacdrape.blend')
for name in ['Body','Sac','Shaft_1','Shaft_2','Shaft_3','Shaft_4']:
 o=bpy.data.objects[name]; bm=bmesh.new(); bm.from_mesh(o.data); vol=bm.calc_volume(); bm.free()
 ws=[o.matrix_world@v.co for v in o.data.vertices]
 groups={}
 for g in o.vertex_groups:
  vals=[]
  for v in o.data.vertices:
   for e in v.groups:
    if e.group==g.index: vals.append(e.weight)
  if vals: groups[g.name]={'n':len(vals),'min':round(min(vals),4),'max':round(max(vals),4),'mean':round(sum(vals)/len(vals),4)}
 print('\n',name,'verts',len(o.data.vertices),'polys',len(o.data.polygons),'volL',round(vol*1000,3),'min',[round(min(v[i] for v in ws),4) for i in range(3)],'max',[round(max(v[i] for v in ws),4) for i in range(3)])
 print('shapekeys',[k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else [])
 print('groups',json.dumps(groups,indent=1))
 print('materials',[m.name if m else None for m in o.data.materials])
arm=bpy.data.objects['KaleaonRig']
for n in ['CC_Base_Pelvis','Sac','Shaft_1_Base','Shaft_1_Tip','Shaft_2_Base','Shaft_2_Tip','Shaft_3_Base','Shaft_3_Tip','Shaft_4_Base','Shaft_4_Tip']:
 b=arm.data.bones[n]; print('BONE',n,'head',tuple(round(x,4) for x in b.head_local),'tail',tuple(round(x,4) for x in b.tail_local),'parent',b.parent.name if b.parent else None)
