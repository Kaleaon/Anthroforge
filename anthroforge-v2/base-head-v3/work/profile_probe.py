import bpy
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/work/head_source.blend")
T=bpy.data.objects["TissueHead_source"]
vs=[v.co for v in T.data.vertices]
print("BBOX x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f"%(min(v.x for v in vs),max(v.x for v in vs),min(v.y for v in vs),max(v.y for v in vs),min(v.z for v in vs),max(v.z for v in vs)))
print("y-band: width / zmin / zmax (band 0.04)")
for i in range(12):
    yc=0.46-i*0.0833
    b=[v for v in vs if abs(v.y-yc)<0.021]
    if b: print(" y=%+.2f n=%3d w=%.3f z %.3f..%.3f"%(yc,len(b),max(v.x for v in b)-min(v.x for v in b),min(v.z for v in b),max(v.z for v in b)))
