"""Build the six A2 card families, export per-family GLBs, dump stats JSON.
Run: blender -b --factory-startup -noaudio --python build_cards.py
"""
import bpy, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import card_geo

ROOT = os.path.dirname(HERE)
CARDS_DIR = os.path.join(ROOT, "cards")
os.makedirs(CARDS_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

stats = {}
for name, spec in card_geo.FAMILIES.items():
    verts, faces, uvs = spec["build"]()
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    uv_layer = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        uv_layer.data[loop.index].uv = uvs[loop.vertex_index]
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    tris = sum(1 if len(p.vertices) == 3 else 2 for p in me.polygons)
    stats[name] = dict(
        texture=spec["texture"], desc=spec["desc"],
        verts=len(verts), tris=tris,
        geo_verts=[list(v) for v in verts],
        geo_faces=[list(f) for f in faces],
        geo_uvs=[list(u) for u in uvs],
    )
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(CARDS_DIR, name + ".glb"),
        export_format="GLB", use_selection=True, export_yup=True)
    print(f"EXPORTED {name}: {len(verts)} verts, {tris} tris")

with open(os.path.join(HERE, "card_stats.json"), "w") as fh:
    json.dump(stats, fh)
print("WROTE card_stats.json")
