import bpy, math

SRC="/home/hatch/workspace/bodies-3d/parts-library/sketchfab/cougar-galileogb/source/FemaleCougar_ForSale.blend"
try:
    bpy.ops.wm.open_mainfile(filepath=SRC)
except RuntimeError as e:
    print("load warning:", e)

def get(name): return bpy.data.objects[name]

def apply_mods(ob, keep=("MIRROR","SUBSURF")):
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    for m in list(ob.modifiers):
        if m.type in keep:
            bpy.ops.object.modifier_apply(modifier=m.name)
        else:
            ob.modifiers.remove(m)
    ob.select_set(False)

def dup(name, newname):
    ob = get(name)
    n = ob.copy(); n.data = ob.data.copy(); n.name = newname
    bpy.context.collection.objects.link(n)
    n.matrix_world = ob.matrix_world.copy()
    return n

# --- LoPoly head cut on BASE mesh via bone weights (rest geometry, pose-independent)
body = dup("LoPoly","TissueHead_source")
HEAD_GROUPS = {"DEF_Head","Ear.L","Eye.L","Ear.R","Eye.R"}
gi = {g.name:i for i,g in enumerate(body.vertex_groups)}
hw = []
for v in body.data.vertices:
    s = 0.0
    for g in v.groups:
        if body.vertex_groups[g.group].name in HEAD_GROUPS: s += g.weight
    hw.append(s)
me = body.data
kill = set()
for p in me.polygons:
    if not all(hw[vi] >= 0.40 for vi in p.vertices): kill.add(p.index)
import bmesh
bm = bmesh.new(); bm.from_mesh(me)
bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.faces[fi] for fi in kill if fi < len(bm.faces)], context='FACES')
bm.to_mesh(me); bm.free()
# drop unreferenced verts
used = set()
for p in me.polygons: used.update(p.vertices)
killv = [v.index for v in me.vertices if v.index not in used]
bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[vi] for vi in killv if vi < len(bm.verts)], context='VERTS')
bm.to_mesh(me); bm.free()
# connected components: keep comps with >=20 verts and centroid z>100 (source units)
import collections
parent = list(range(len(me.vertices)))
def find(a):
    while parent[a]!=a: parent[a]=parent[parent[a]]; a=parent[a]
    return a
def union(a,b):
    ra,rb=find(a),find(b)
    if ra!=rb: parent[ra]=rb
for e in me.edges: union(e.vertices[0], e.vertices[1])
comps = collections.defaultdict(list)
for v in me.vertices: comps[find(v.index)].append(v.index)
keepv = set()
compinfo=[]
for root, idxs in comps.items():
    cz = sum(me.vertices[i].co.z for i in idxs)/len(idxs)
    compinfo.append((len(idxs), round(cz,1)))
    if len(idxs) >= 20 and cz > 100: keepv.update(idxs)
killf = [p.index for p in me.polygons if not all(vi in keepv for vi in p.vertices)]
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.faces[fi] for fi in killf if fi < len(bm.faces)], context='FACES')
bm.to_mesh(me); bm.free()
used = set()
for p in me.polygons: used.update(p.vertices)
killv = [v.index for v in me.vertices if v.index not in used]
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[vi] for vi in killv if vi < len(bm.verts)], context='VERTS')
bm.to_mesh(me); bm.free()
print("HEAD comps (size, cz):", sorted(compinfo, reverse=True)[:10])
print("HEAD verts after cut:", len(me.vertices))
apply_mods(body, keep=("MIRROR",))
print("HEAD verts after mirror:", len(body.data.vertices))

pieces = {}
for src, nn in (("LoPoly.006","Piece006"), ("LoPoly.010","Piece010"), ("Eyes.002","Eye_source")):
    o = dup(src, nn); apply_mods(o, keep=("MIRROR","SUBSURF")); pieces[nn]=o

# delete everything else
for ob in list(bpy.data.objects):
    if ob not in [body]+list(pieces.values()):
        bpy.data.objects.remove(ob, do_unlink=True)

# --- frame transform: rotate 180 about Z (face -Y -> +Y), then centre on head bbox, scale L=1
def bbox(ob):
    vs=[v.co for v in ob.data.vertices]
    xs=[v.x for v in vs]; ys=[v.y for v in vs]; zs=[v.z for v in vs]
    return (min(xs),max(xs)),(min(ys),max(ys)),(min(zs),max(zs))
(x0,x1),(y0,y1),(z0,z1) = bbox(body)
L = y1-y0  # NOTE after rotation y extent same; nose was at y0 (min y = front since facing -Y)
print("source head bbox x",x0,x1," y",y0,y1," z",z0,z1," L=",L)
import mathutils
M = mathutils.Matrix.Rotation(math.radians(180),4,'Z')
for ob in [body]+list(pieces.values()):
    ob.matrix_world = M @ ob.matrix_world
    bpy.context.view_layer.objects.active=ob; ob.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    ob.select_set(False)
(x0,x1),(y0,y1),(z0,z1) = bbox(body)
cx, cy, cz = (x0+x1)/2,(y0+y1)/2,(z0+z1)/2
s = 1.0/L
T = mathutils.Matrix.Translation((-cx*s, -cy*s, -cz*s)) @ mathutils.Matrix.Scale(s,4)
for ob in [body]+list(pieces.values()):
    for v in ob.data.vertices: v.co = T @ v.co
    ob.matrix_world = mathutils.Matrix.Identity(4)
print("framed. tissue verts:", len(body.data.vertices))
for nn,o in pieces.items():
    print(nn, "verts", len(o.data.vertices), "bbox", bbox(o))
bpy.ops.wm.save_as_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/base-head-v3/work/head_source.blend")
print("SAVED")
