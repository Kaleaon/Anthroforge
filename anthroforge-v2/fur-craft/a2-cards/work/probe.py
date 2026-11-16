import bpy, json
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="/home/hatch/workspace/anthroforge-v2/fur-prototype/work/fur_stage2.blend")
ob = bpy.data.objects["BaraWolfBody"]
me = ob.data
print("verts", len(me.vertices), "polys", len(me.polygons))
print("vgroups:", [g.name for g in ob.vertex_groups])
print("psys:", [(p.name, p.settings.count) for p in ob.particle_systems])

REGIONS = ["FUR_ruff", "FUR_back", "FUR_belly", "FUR_coat", "FUR_bodyhair"]
gidx = {r: ob.vertex_groups[r].index for r in REGIONS}
area = {r: 0.0 for r in REGIONS}
total = 0.0
for poly in me.polygons:
    a = poly.area
    total += a
    w = {r: 0.0 for r in REGIONS}
    for vi in poly.vertices:
        v = me.vertices[vi]
        for g in v.groups:
            for r in REGIONS:
                if g.group == gidx[r]:
                    w[r] += g.weight
    n = len(poly.vertices)
    for r in REGIONS:
        area[r] += a * (w[r] / n)
print("TOTAL AREA m2:", round(total, 3))
for r in REGIONS:
    print(r, "area m2:", round(area[r], 3))

bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
zs = [c.z for c in bb]; xs = [c.x for c in bb]
print("height m:", round(max(zs)-min(zs), 3), "width m:", round(max(xs)-min(xs), 3))

# evaluated parents per system
dg = bpy.context.evaluated_depsgraph_get()
ev = ob.evaluated_get(dg)
for ps in ev.particle_systems:
    parts = list(ps.particles)
    lens = []
    for p in parts[:50]:
        ks = p.hair_keys
        if len(ks) >= 2:
            L = sum((ks[i+1].co - ks[i].co).length for i in range(len(ks)-1))
            lens.append(L)
    import statistics
    print(ps.name, "parents:", len(parts), "median strand len m:", round(statistics.median(lens), 4) if lens else None)
