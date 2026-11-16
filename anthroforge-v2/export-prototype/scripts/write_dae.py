"""Stage 1c: build the Second-Life-profile Collada (.dae) from the interchange
dump. Hand-authored Collada 1.4.1 XML (stdlib ElementTree) because Blender 5.2
dropped its Collada exporter and pycollada's Skin/Morph classes are load-side.

SL profile applied here:
  - up_axis = Z_UP, unit = 1 metre (SL's importer convention)
  - skin weights: top-4 influences per vertex, renormalised to sum 1
  - full joint set kept (66 custom joints; names will NOT match the SL Bento
    skeleton — documented in SURVIVAL.md, the file is a valid rigged DAE)
  - geometry triangulated (fan), one <triangles> per material group
  - morph targets written as <morph> controllers (SL's uploader ignores them;
    they are in the file for other Collada consumers)

Run with the pycollada venv python (only stdlib is used, any python3 works):
  python3 write_dae.py <interchange.json> <interchange.npz> <anim_samples.npz> <out.dae>
"""
import json
import sys
import numpy as np
import xml.etree.ElementTree as ET

NS = "http://www.collada.org/2005/11/COLLADASchema"
ET.register_namespace("", NS)


def q(tag):
    return f"{{{NS}}}{tag}"


def sub(parent, tag, attrib=None, text=None):
    el = ET.SubElement(parent, q(tag), attrib or {})
    if text is not None:
        el.text = text
    return el


def fmt(arr):
    return " ".join("%.6g" % float(x) for x in np.asarray(arr).ravel())


def sid(name):
    out = []
    for ch in name:
        out.append(ch if (ch.isalnum() or ch in "_-") else "_")
    s = "".join(out)
    if s and s[0].isdigit():
        s = "_" + s
    return s or "unnamed"


def float_source(parent, id_, arr, params):
    src = sub(parent, "source", {"id": id_})
    fa = sub(src, "float_array", {"id": id_ + "-array", "count": str(len(np.asarray(arr).ravel()))},
             fmt(arr))
    tc = sub(src, "technique_common")
    stride = len(params)
    acc = sub(tc, "accessor", {"source": "#" + id_ + "-array", "count": str(len(np.asarray(arr).ravel()) // stride),
                               "stride": str(stride)})
    for p in params:
        sub(acc, "param", {"name": p, "type": "float"})
    return src


JSONPATH, NPZPATH, ANIMPATH, OUT = sys.argv[1:5]
meta = json.load(open(JSONPATH))
data = np.load(NPZPATH)
anim = np.load(ANIMPATH) if meta.get("animation") else None

bones = meta["bones"]
bone_idx = {b["name"]: i for i, b in enumerate(bones)}
bone_rest = {b["name"]: np.array(b["rest_world"]).reshape(4, 4) for b in bones}
arm_world = np.array(meta["armature_world"]).reshape(4, 4)

root = ET.Element(q("COLLADA"), {"version": "1.4.1"})  # xmlns comes from register_namespace
asset = sub(root, "asset")
sub(sub(asset, "contributor"), "authoring_tool", text="AnthroForge export prototype (write_dae.py)")
sub(asset, "created", text="2026-11-12T00:00:00Z")
sub(asset, "modified", text="2026-11-12T00:00:00Z")
sub(asset, "unit", {"name": "meter", "meter": "1.0"})
sub(asset, "up_axis", text="Z_UP")

# ---------------- images / effects / materials ----------------
lib_images = sub(root, "library_images")
for m in meta["materials"]:
    if m["texture"]:
        img = sub(lib_images, "image", {"id": "img-" + sid(m["name"]), "name": m["texture"]})
        sub(img, "init_from", text="textures_dae/" + m["texture"])

lib_effects = sub(root, "library_effects")
for m in meta["materials"]:
    eff = sub(lib_effects, "effect", {"id": "eff-" + sid(m["name"])})
    prof = sub(eff, "profile_COMMON")
    tech = sub(prof, "technique", {"sid": "common"})
    phong = sub(tech, "phong")
    dif = sub(phong, "diffuse")
    if m["texture"]:
        sub(dif, "texture", {"texture": "img-" + sid(m["name"]), "texcoord": "UVMap"})
    else:
        sub(dif, "color", text=fmt(m["color"]))
    spec = sub(phong, "specular")
    sub(spec, "color", text="0.1 0.1 0.1 1")
    shin = sub(phong, "shininess")
    sub(shin, "float", text="10")

lib_materials = sub(root, "library_materials")
for m in meta["materials"]:
    mat = sub(lib_materials, "material", {"id": "mat-" + sid(m["name"]), "name": m["name"]})
    sub(mat, "instance_effect", {"url": "#eff-" + sid(m["name"])})

# ---------------- geometries ----------------
def build_geometry(lib, mesh_meta, pos_override=None, id_suffix="", name_suffix=""):
    key = mesh_meta["key"]
    pos = data[key + "_pos"] if pos_override is None else pos_override
    nrm = data[key + "_nrm"]
    uv = data[key + "_uv"]
    gid = "geom-" + sid(mesh_meta["name"]) + id_suffix
    geom = sub(lib, "geometry", {"id": gid, "name": mesh_meta["name"] + name_suffix})
    me = sub(geom, "mesh")
    float_source(me, gid + "-pos", pos, ["X", "Y", "Z"])
    float_source(me, gid + "-nrm", nrm, ["X", "Y", "Z"])
    float_source(me, gid + "-uv", uv, ["S", "T"])
    verts = sub(me, "vertices", {"id": gid + "-verts"})
    sub(verts, "input", {"semantic": "POSITION", "source": "#" + gid + "-pos"})
    # group polys by material
    groups = {}
    for pi, p in enumerate(mesh_meta["polys"]):
        groups.setdefault(mesh_meta["poly_mat"][pi], []).append(p)
    for mi, polys in groups.items():
        tris = []
        for p in polys:
            for k in range(1, len(p) - 1):
                tris.append((p[0], p[k], p[k + 1]))
        idx = np.array(tris, dtype=np.int64)
        matname = mesh_meta["materials"][mi] if mi < len(mesh_meta["materials"]) else None
        t = sub(me, "triangles", {"count": str(len(tris)),
                                  **({"material": "sym-" + sid(matname)} if matname else {})})
        sub(t, "input", {"semantic": "VERTEX", "source": "#" + gid + "-verts", "offset": "0"})
        sub(t, "input", {"semantic": "NORMAL", "source": "#" + gid + "-nrm", "offset": "1"})
        sub(t, "input", {"semantic": "TEXCOORD", "source": "#" + gid + "-uv", "offset": "2", "set": "0"})
        inter = np.stack([idx, idx, idx], axis=2).reshape(-1)
        sub(t, "p", text=" ".join(str(int(x)) for x in inter))
    return gid

lib_geoms = sub(root, "library_geometries")
geom_id = {}
target_geom_id = {}
for mm in meta["meshes"]:
    geom_id[mm["name"]] = build_geometry(lib_geoms, mm)
    for kb in mm["shape_keys"]:
        target_geom_id[(mm["name"], kb["name"])] = build_geometry(
            lib_geoms, mm, pos_override=data[f"{mm['key']}_key_{kb['name']}"],
            id_suffix="-target-" + sid(kb["name"]), name_suffix="_" + kb["name"])

# ---------------- controllers (skin + morph) ----------------
lib_ctrl = sub(root, "library_controllers")
weight_profile_stats = {"verts_over4": 0, "verts_total": 0}
skin_id = {}
morph_id = {}
inv_bind = {b["name"]: np.linalg.inv(bone_rest[b["name"]]) for b in bones}

for mm in meta["meshes"]:
    if not mm["skinned"]:
        continue
    cid = "skin-" + sid(mm["name"])
    skin_id[mm["name"]] = cid
    ctrl = sub(lib_ctrl, "controller", {"id": cid, "name": mm["name"] + "Skin"})
    skin = sub(ctrl, "skin", {"source": "#" + geom_id[mm["name"]]})
    sub(skin, "bind_shape_matrix", text=fmt(np.eye(4)))
    # joints source (names)
    jsrc = sub(skin, "source", {"id": cid + "-joints"})
    narr = sub(jsrc, "Name_array", {"id": cid + "-joints-array", "count": str(len(bones))},
               " ".join(sid(b["name"]) for b in bones))
    tc = sub(jsrc, "technique_common")
    acc = sub(tc, "accessor", {"source": "#" + cid + "-joints-array", "count": str(len(bones)), "stride": "1"})
    sub(acc, "param", {"name": "JOINT", "type": "name"})
    # inv bind source
    ib = np.stack([inv_bind[b["name"]] for b in bones])
    float_source(skin, cid + "-invbind", ib, ["TRANSFORM"])
    # weight values (dedup)
    per_vert = []
    uniq = []
    uniq_index = {}
    for wlist in mm["weights"]:
        top = sorted(wlist, key=lambda t: -t[1])[:4]
        if len(wlist) > 4:
            weight_profile_stats["verts_over4"] += 1
        weight_profile_stats["verts_total"] += 1
        s = sum(w for _, w in top) or 1.0
        pairs = []
        for jname, w in top:
            wn = w / s
            if wn not in uniq_index:
                uniq_index[wn] = len(uniq)
                uniq.append(wn)
            pairs.append((bone_idx[jname], uniq_index[wn]))
        per_vert.append(pairs)
    float_source(skin, cid + "-weights", np.array(uniq), ["WEIGHT"])
    joints_el = sub(skin, "joints")
    sub(joints_el, "input", {"semantic": "JOINT", "source": "#" + cid + "-joints"})
    sub(joints_el, "input", {"semantic": "INV_BIND_MATRIX", "source": "#" + cid + "-invbind"})
    vw = sub(skin, "vertex_weights", {"count": str(len(per_vert))})
    sub(vw, "input", {"semantic": "JOINT", "source": "#" + cid + "-joints", "offset": "0"})
    sub(vw, "input", {"semantic": "WEIGHT", "source": "#" + cid + "-weights", "offset": "1"})
    sub(vw, "vcount", text=" ".join(str(len(p)) for p in per_vert))
    sub(vw, "v", text=" ".join(f"{j} {w}" for p in per_vert for (j, w) in p))

    if mm["shape_keys"]:
        mid = "morph-" + sid(mm["name"])
        morph_id[mm["name"]] = mid
        mctrl = sub(lib_ctrl, "controller", {"id": mid, "name": mm["name"] + "Morph"})
        # NOTE: morphs are sourced on the GEOMETRY, not chained on the skin
        # controller. Chaining is legal Collada 1.4.1, but real readers
        # (pycollada verified; SL's uploader ignores morphs entirely) only
        # resolve morph->geometry. The scene instances the skin; the morph
        # controller ships library-level. See SURVIVAL.md.
        morph = sub(mctrl, "morph", {"method": "NORMALIZED", "source": "#" + geom_id[mm["name"]]})
        tsrc = sub(morph, "source", {"id": mid + "-targets"})
        sub(tsrc, "IDREF_array", {"id": mid + "-targets-array", "count": str(len(mm["shape_keys"]))},
            " ".join(target_geom_id[(mm["name"], kb["name"])] for kb in mm["shape_keys"]))
        tc = sub(tsrc, "technique_common")
        acc = sub(tc, "accessor", {"source": "#" + mid + "-targets-array",
                                   "count": str(len(mm["shape_keys"])), "stride": "1"})
        sub(acc, "param", {"name": "MORPH_TARGET", "type": "IDREF"})
        float_source(morph, mid + "-weights",
                     np.array([kb["value"] for kb in mm["shape_keys"]]), ["MORPH_WEIGHT"])
        tg = sub(morph, "targets")
        sub(tg, "input", {"semantic": "MORPH_TARGET", "source": "#" + mid + "-targets"})
        sub(tg, "input", {"semantic": "MORPH_WEIGHT", "source": "#" + mid + "-weights"})

# ---------------- visual scene ----------------
lib_vs = sub(root, "library_visual_scenes")
vs = sub(lib_vs, "visual_scene", {"id": "scene", "name": "scene"})

children = {}
roots = []
for b in bones:
    if b["parent"]:
        children.setdefault(b["parent"], []).append(b["name"])
    else:
        roots.append(b["name"])

def local_rest(name):
    if bones[bone_idx[name]]["parent"]:
        return np.linalg.inv(bone_rest[bones[bone_idx[name]]["parent"]]) @ bone_rest[name]
    return np.linalg.inv(arm_world) @ bone_rest[name]

def add_bone_node(parent_el, name):
    node = sub(parent_el, "node", {"id": sid(name) + "_node", "sid": sid(name),
                                   "name": name, "type": "JOINT"})
    sub(node, "matrix", {"sid": "transform"}, fmt(local_rest(name)))
    for c in children.get(name, []):
        add_bone_node(node, c)
    return node

arm_node = sub(vs, "node", {"id": "armature_node", "name": meta.get("armature_name", "Armature")})
sub(arm_node, "matrix", {"sid": "transform"}, fmt(arm_world))
for r in roots:
    add_bone_node(arm_node, r)

root_joint_node = sid(roots[0]) + "_node" if roots else ""
for mm in meta["meshes"]:
    node = sub(vs, "node", {"id": "node-" + sid(mm["name"]), "name": mm["name"]})
    ctrl_ref = skin_id.get(mm["name"]) or morph_id.get(mm["name"])
    if ctrl_ref:
        inst = sub(node, "instance_controller", {"url": "#" + ctrl_ref})
        sub(inst, "skeleton", text="#" + root_joint_node)
    else:
        inst = sub(node, "instance_geometry", {"url": "#" + geom_id[mm["name"]]})
    if mm["materials"]:
        bm = sub(inst, "bind_material")
        tc = sub(bm, "technique_common")
        for mname in mm["materials"]:
            if mname:
                sub(tc, "instance_material", {"symbol": "sym-" + sid(mname),
                                              "target": "#mat-" + sid(mname)})

scene_el = sub(root, "scene")
sub(scene_el, "instance_visual_scene", {"url": "#scene"})

tree = ET.ElementTree(root)

# ---------------- animations (appended as raw XML into the tree) ----------------
if anim is not None:
    lib_anim = ET.Element(q("library_animations"))
    frames = anim["frames"]
    times = frames / float(meta["animation"]["fps"])
    for b in bones:
        name = b["name"]
        mats = anim[name]  # (nframes, 16) row-major local matrices
        aid = "anim-" + sid(name)
        a = ET.SubElement(lib_anim, q("animation"), {"id": aid, "name": name})
        # input source
        src = ET.SubElement(a, q("source"), {"id": aid + "-input"})
        ET.SubElement(src, q("float_array"), {"id": aid + "-input-array",
                                              "count": str(len(times))}).text = fmt(times)
        tc = ET.SubElement(src, q("technique_common"))
        acc = ET.SubElement(tc, q("accessor"), {"source": "#" + aid + "-input-array",
                                                "count": str(len(times)), "stride": "1"})
        ET.SubElement(acc, q("param"), {"name": "TIME", "type": "float"})
        # output source
        src = ET.SubElement(a, q("source"), {"id": aid + "-output"})
        ET.SubElement(src, q("float_array"), {"id": aid + "-output-array",
                                              "count": str(mats.size)}).text = fmt(mats)
        tc = ET.SubElement(src, q("technique_common"))
        acc = ET.SubElement(tc, q("accessor"), {"source": "#" + aid + "-output-array",
                                                "count": str(len(times)), "stride": "16"})
        ET.SubElement(acc, q("param"), {"name": "TRANSFORM", "type": "float4x4"})
        # interpolation source
        src = ET.SubElement(a, q("source"), {"id": aid + "-interp"})
        ET.SubElement(src, q("Name_array"), {"id": aid + "-interp-array",
                                             "count": str(len(times))}).text = " ".join(["LINEAR"] * len(times))
        tc = ET.SubElement(src, q("technique_common"))
        acc = ET.SubElement(tc, q("accessor"), {"source": "#" + aid + "-interp-array",
                                                "count": str(len(times)), "stride": "1"})
        ET.SubElement(acc, q("param"), {"name": "INTERPOLATION", "type": "name"})
        samp = ET.SubElement(a, q("sampler"), {"id": aid + "-sampler"})
        ET.SubElement(samp, q("input"), {"semantic": "INPUT", "source": "#" + aid + "-input"})
        ET.SubElement(samp, q("input"), {"semantic": "OUTPUT", "source": "#" + aid + "-output"})
        ET.SubElement(samp, q("input"), {"semantic": "INTERPOLATION", "source": "#" + aid + "-interp"})
        chan = ET.SubElement(a, q("channel"), {"source": "#" + aid + "-sampler",
                                               "target": sid(name) + "_node/transform"})
    # insert library_animations before library_controllers (schema order is
    # lenient in most readers, but keep canonical ordering anyway)
    idx_ctrl = list(root).index(lib_ctrl)
    root.insert(idx_ctrl, lib_anim)

ET.indent(tree, space=" ")
tree.write(OUT, encoding="utf-8", xml_declaration=True)
print("DAE WRITTEN", OUT)
print("weight profile:", weight_profile_stats)
