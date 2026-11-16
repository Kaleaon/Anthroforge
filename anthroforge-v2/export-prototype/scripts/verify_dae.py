"""Stage 2 (DAE): parse the exported .dae back with pycollada (an independent
implementation from the hand-rolled writer) plus raw-XML cross-checks, and
emit a dump in the same shape as the Blender inspector dumps.

Run: /tmp/dae-venv/bin/python verify_dae.py <file.dae> <dump.json>
"""
import json
import sys
import xml.etree.ElementTree as ET

import collada

NS = "{http://www.collada.org/2005/11/COLLADASchema}"
PATH, DUMP = sys.argv[1], sys.argv[2]

mesh = collada.Collada(PATH)
tree = ET.parse(PATH)
root = tree.getroot()

out = {"armatures": [], "meshes": [], "actions": [], "objects": [], "extra": {}}

# ---- joints: from skin controllers (raw XML, authoritative for counts) ----
joint_names = []
for vw in root.iter(NS + "vertex_weights"):
    pass
skin_el = next(root.iter(NS + "skin"), None)
if skin_el is not None:
    for src in skin_el.iter(NS + "source"):
        acc = src.find(NS + "technique_common/" + NS + "accessor/" + NS + "param")
        if acc is not None and acc.get("name") == "JOINT":
            narr = src.find(NS + "Name_array")
            joint_names = narr.text.split()
out["armatures"].append({"object": "DAE skins (first controller)",
                         "bone_count": len(joint_names), "bones": joint_names})

# original bone names survive in scene node name= attributes
node_names = [n.get("name") for n in root.iter(NS + "node") if n.get("type") == "JOINT"]
out["extra"]["joint_node_names_preserved"] = node_names

# ---- geometries / meshes ----
skin_by_source = {}
morph_targets = {}
for ctrl in root.iter(NS + "controller"):
    skin = ctrl.find(NS + "skin")
    if skin is not None:
        vw = skin.find(NS + "vertex_weights")
        vcounts = [int(x) for x in vw.find(NS + "vcount").text.split()]
        skin_by_source[skin.get("source").lstrip("#")] = {
            "weighted_verts": sum(1 for c in vcounts if c > 0),
            "max_influences": max(vcounts) if vcounts else 0,
            "vert_count": len(vcounts),
        }
    morph = ctrl.find(NS + "morph")
    if morph is not None:
        base = morph.get("source").lstrip("#")  # geometry id (morphs source geometry)
        n = 0
        for src in morph.iter(NS + "source"):
            if src.get("id", "").endswith("-weights"):
                n = int(src.find(NS + "float_array").get("count"))
        morph_targets[base] = n

geom_info = {}
for g in root.iter(NS + "geometry"):
    gid = g.get("id")
    pos_acc = None
    mats = set()
    ntris = 0
    for t in g.iter(NS + "triangles"):
        ntris += int(t.get("count"))
        if t.get("material"):
            mats.add(t.get("material"))
    for src in g.iter(NS + "source"):
        if src.get("id", "").endswith("-pos"):
            pos_acc = int(src.find(NS + "float_array").get("count")) // 3
    geom_info[gid] = {"verts": pos_acc, "tris": ntris, "materials": sorted(mats)}

# map controller ids -> geometry ids for morph counting
ctrl_source = {}
for ctrl in root.iter(NS + "controller"):
    for child in ctrl:
        if child.tag in (NS + "skin", NS + "morph"):
            ctrl_source[ctrl.get("id")] = child.get("source").lstrip("#")

for gid, info in geom_info.items():
    if "-target-" in gid:
        continue  # morph target geometries listed under their base mesh
    sk = skin_by_source.get(gid)
    nkeys = morph_targets.get(gid, 0)
    out["meshes"].append({
        "object": gid.replace("geom-", ""),
        "verts": info["verts"],
        "polys": info["tris"],
        "vgroup_count": len(joint_names) if sk else 0,
        "weighted_verts": sk["weighted_verts"] if sk else 0,
        "max_influences": sk["max_influences"] if sk else 0,
        "shape_keys": ["morph_weights:%d" % nkeys] if nkeys else [],
        "materials": info["materials"],
    })

# ---- animations (raw XML) ----
anims = root.findall(NS + "library_animations/" + NS + "animation")
total_channels = 0
samples = 0
for a in anims:
    chans = a.findall(NS + "channel")
    total_channels += len(chans)
    for src in a.iter(NS + "source"):
        if src.get("id", "").endswith("-input"):
            samples = int(src.find(NS + "float_array").get("count"))
out["actions"].append({"name": "library_animations (%d joint clips)" % len(anims),
                       "fcurves": total_channels, "frame_range": None,
                       "samples_per_channel": samples})

# ---- asset header ----
asset = root.find(NS + "asset")
out["extra"]["up_axis"] = asset.find(NS + "up_axis").text
unit = asset.find(NS + "unit")
out["extra"]["unit"] = {"name": unit.get("name"), "meter": unit.get("meter")}
out["extra"]["pycollada_counts"] = {
    "geometries": len(mesh.geometries),
    "controllers": len(mesh.controllers),
    "materials": len(mesh.materials),
    "effects": len(mesh.effects),
    "images": len(mesh.images),
    "scene_nodes": len(list(mesh.scene.nodes)) if mesh.scene else 0,
}

with open(DUMP, "w") as f:
    json.dump(out, f, indent=1)
print("DAE DUMPED", DUMP)
print(json.dumps(out["extra"], indent=1))
