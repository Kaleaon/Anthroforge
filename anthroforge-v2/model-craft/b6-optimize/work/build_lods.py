#!/usr/bin/env python3
"""B6: build naive vs deformation-aware LOD1/LOD2 from a skinned GLB.

Method (deformation-aware arm):
  importance(v) = clip(0.55*grad + 0.25*prox + 0.35*curv, 0, 1) where
    grad = per-vertex max skin-weight L1 gradient across incident edges,
           normalised by its 99.5th percentile  (weight cliffs, B17 R12)
    prox = exp(-(d/0.06)^2), d = distance to nearest bone head (joint)
    curv = per-vertex max dihedral-ish normal deviation across edges,
           normalised by its 99th percentile   (silhouette detail:
           ears, muzzle, fingers, toes)
  fed to Blender Decimate/Collapse as a vertex group with
  invert_vertex_group=True (probe_decimate.py: weight 1 = protected,
  weight 0 = collapses freely).

Naive arm: same ratios, no vertex group.

Ratios target the B5 shared LOD doctrine: LOD1 = 50% faces,
LOD2 = 25% faces. Achieved counts are recorded; if the aware arm lands
>5% off target, one ratio retry is made.

  blender -b --python build_lods.py -- <src.glb> <out_dir> <lods_dir>
Writes <lods_dir>/bara_wolf_lod{1,2}{,_naive}.glb and
<out_dir>/lod_build.json with counts + weight-hygiene stats.
Rigid attachments (eyes: no armature modifier) are carried unchanged.
"""
import bpy, sys, json, os
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT, LODS = argv[0], argv[1], argv[2]
os.makedirs(OUT, exist_ok=True)
os.makedirs(LODS, exist_ok=True)

TARGETS = [("lod1", 0.50), ("lod2", 0.25)]

def load():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC)
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    body = None
    rigid = []
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        if any(m.type == 'ARMATURE' and m.object == arm for m in o.modifiers):
            if body is None or len(o.data.vertices) > len(body.data.vertices):
                body = o
            else:
                rigid.append(o)
        else:
            rigid.append(o)
    return arm, body, rigid

def skin_matrix(obj, arm):
    """Dense (V x B) weight matrix + bone name list, from vertex groups."""
    bones = [b.name for b in arm.data.bones]
    bidx = {n: i for i, n in enumerate(bones)}
    gname = {g.index: g.name for g in obj.vertex_groups}
    W = np.zeros((len(obj.data.vertices), len(bones)), dtype=np.float32)
    for v in obj.data.vertices:
        for g in v.groups:
            nm = gname.get(g.group)
            if nm in bidx:
                W[v.index, bidx[nm]] += g.weight
    return W, bones

def edge_list(me):
    return np.array([(e.vertices[0], e.vertices[1]) for e in me.edges],
                    dtype=np.int64)

def importance(obj, arm):
    me = obj.data
    W, bones = skin_matrix(obj, arm)
    E = edge_list(me)
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    mw = np.array(obj.matrix_world)
    co_w = co @ mw[:3, :3].T + mw[:3, 3]
    # --- weight gradient (max L1 across incident edges) -------------------
    gd = np.abs(W[E[:, 0]] - W[E[:, 1]]).sum(axis=1)          # per edge
    grad = np.zeros(len(co), dtype=np.float64)
    np.maximum.at(grad, E[:, 0], gd)
    np.maximum.at(grad, E[:, 1], gd)
    gcap = np.percentile(grad, 99.5) or 1.0
    grad_n = np.clip(grad / gcap, 0, 1)
    # --- joint proximity (Gaussian around bone heads, 6 cm) ---------------
    MW = np.array(arm.matrix_world)
    heads = []
    for b in arm.data.bones:
        h = np.array(b.head_local)
        heads.append(h @ MW[:3, :3].T + MW[:3, 3])
    heads = np.array(heads)
    dmin = np.full(len(co), 1e9)
    for s in range(0, len(co), 8192):
        d = np.linalg.norm(co_w[s:s + 8192, None, :] - heads[None, :, :],
                           axis=2)
        dmin[s:s + 8192] = d.min(axis=1)
    prox = np.exp(-((dmin / 0.06) ** 2))
    # --- normal dispersion (curvature / silhouette detail) ----------------
    no = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("normal", no)
    no = no.reshape(-1, 3)
    cosang = np.clip((no[E[:, 0]] * no[E[:, 1]]).sum(axis=1), -1, 1)
    ang = np.arccos(cosang)
    curv = np.zeros(len(co), dtype=np.float64)
    np.maximum.at(curv, E[:, 0], ang)
    np.maximum.at(curv, E[:, 1], ang)
    ccap = np.percentile(curv, 99.0) or 1.0
    curv_n = np.clip(curv / ccap, 0, 1)
    imp = np.clip(0.55 * grad_n + 0.25 * prox + 0.35 * curv_n, 0, 1)
    stats = dict(grad_p995=float(gcap), grad_max=float(grad.max()),
                 curv_p99=float(ccap), dmin_median=float(np.median(dmin)),
                 imp_mean=float(imp.mean()),
                 imp_frac_gt_0_8=float((imp > 0.8).mean()),
                 imp_frac_lt_0_1=float((imp < 0.1).mean()))
    return imp, stats

def set_importance_group(obj, imp):
    vg = obj.vertex_groups.get("B6_importance")
    if vg:
        obj.vertex_groups.remove(vg)
    vg = obj.vertex_groups.new(name="B6_importance")
    # add in weight buckets for speed
    for lo in np.arange(0.0, 1.0, 0.05):
        idx = np.where((imp >= lo) & (imp < lo + 0.05))[0]
        if len(idx):
            vg.add(idx.tolist(), float(lo + 0.025), 'REPLACE')
    idx = np.where(imp >= 1.0)[0]
    if len(idx):
        vg.add(idx.tolist(), 1.0, 'REPLACE')
    return vg

def weight_hygiene(obj, arm):
    W, bones = skin_matrix(obj, arm)
    s = W.sum(axis=1)
    infl = (W > 1e-6).sum(axis=1)
    return dict(verts=int(len(s)),
                wsum_min=float(s.min()), wsum_max=float(s.max()),
                unweighted=int((s <= 1e-6).sum()),
                max_influences=int(infl.max()),
                frac_gt4_influences=float((infl > 4).mean()))

def decimate(obj, ratio, vg_name=None):
    # Remove the Armature modifier first: applying Decimate while it sits
    # *below* Armature in the stack would bake the stack and drop the
    # skin. Re-add Armature afterwards (vertex groups carry the skin).
    arm_mods = [(m.object, m.use_vertex_groups, m.use_bone_envelopes)
                for m in obj.modifiers if m.type == 'ARMATURE']
    for m in list(obj.modifiers):
        if m.type == 'ARMATURE':
            obj.modifiers.remove(m)
    mod = obj.modifiers.new("b6dec", 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = ratio
    if vg_name:
        mod.vertex_group = vg_name
        mod.invert_vertex_group = True
        mod.vertex_group_factor = 1.0
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.select_set(False)
    for arm_obj, uvg, ube in arm_mods:
        m = obj.modifiers.new("Armature", 'ARMATURE')
        m.object = arm_obj
        m.use_vertex_groups = uvg
        m.use_bone_envelopes = ube
    return len(obj.data.polygons)

def export(path):
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB',
                              export_image_format='NONE',
                              export_apply=False)

report = {"source": SRC, "arms": {}}
arm, body, rigid = load()
F0 = len(body.data.polygons)
V0 = len(body.data.vertices)
report["lod0"] = dict(verts=V0, faces=F0,
                      hygiene=weight_hygiene(body, arm),
                      rigid_objects=[o.name for o in rigid],
                      shape_keys=bool(body.data.shape_keys))
print("LOD0 body:", V0, "verts", F0, "faces; rigid:", [o.name for o in rigid])

imp, istats = importance(body, arm)
report["importance"] = istats
print("importance:", istats)

for name, frac in TARGETS:
    target_faces = int(round(F0 * frac))
    for arm_name, use_vg in (("naive", False), ("aware", True)):
        a, b, r = load()
        if use_vg:
            set_importance_group(b, imp)
        got = decimate(b, frac, "B6_importance" if use_vg else None)
        # one retry if the VG arm lands >5% off target
        if use_vg and abs(got - target_faces) / target_faces > 0.05:
            r2 = frac * target_faces / max(got, 1)
            a, b, r = load()
            set_importance_group(b, imp)
            got = decimate(b, float(min(max(r2, 0.02), 0.95)),
                           "B6_importance")
            report["arms"].setdefault(name, {})["aware_retry_ratio"] = r2
        hyg = weight_hygiene(b, a)
        suffix = "_naive" if not use_vg else ""
        path = os.path.join(LODS, f"bara_wolf_{name}{suffix}.glb")
        export(path)
        report["arms"].setdefault(name, {})[arm_name] = dict(
            verts=len(b.data.vertices), faces=got,
            target_faces=target_faces, hygiene=hyg,
            file=path, bytes=os.path.getsize(path))
        print(name, arm_name, "->", got, "faces", len(b.data.vertices),
              "verts", path)

json.dump(report, open(os.path.join(OUT, "lod_build.json"), "w"), indent=1)
print("BUILD DONE")
