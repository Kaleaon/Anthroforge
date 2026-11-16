#!/usr/bin/env python3
"""B17 rig stress audit (Mixamo-style wolf config). Poses a skinned GLB
through extreme poses in headless Blender; measures edge strain, per-face
deformation-gradient flips, area collapse; static weight / ring-support
/ pivot-offset audits. Bend axes resolved by analytic FK (mathutils
convention) so candidate search costs no depsgraph evals. Results are
flushed per pose (results.json + poses_npz/<pose>.npz + rest.npz) so a
killed run resumes where it stopped.
  blender -b --python audit_rig.py -- <glb> <out_dir>
"""
import bpy, sys, json, math, os
import numpy as np
from mathutils import Euler

argv = sys.argv[sys.argv.index("--") + 1:]
GLB, OUT = argv[0], argv[1]
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
meshes = [o for o in bpy.data.objects if o.type == 'MESH'
          and any(m.type == 'ARMATURE' and m.object == arm
                  for m in o.modifiers)]
print(f"armature: {arm.name}; skinned meshes: {[m.name for m in meshes]}")
BONES = [b.name for b in arm.data.bones]
BIDX = {n: i for i, n in enumerate(BONES)}
NB = len(BONES)
PARENT = {b.name: (b.parent.name if b.parent else None)
          for b in arm.data.bones}

def find(pat):
    if pat in BIDX:
        return pat
    for n in BONES:
        if n.startswith(pat):
            return n
    return None

J = dict(
    pelvis="mixamorig:Hips", spine_lo="mixamorig:Spine",
    spine_mid="mixamorig:Spine1", spine_hi="mixamorig:Spine2",
    neck="mixamorig:Neck", head="mixamorig:Head",
    clav_l="mixamorig:LeftShoulder", arm_l="mixamorig:LeftArm",
    fore_l="mixamorig:LeftForeArm", hand_l="mixamorig:LeftHand",
    clav_r="mixamorig:RightShoulder", arm_r="mixamorig:RightArm",
    fore_r="mixamorig:RightForeArm", hand_r="mixamorig:RightHand",
    thigh_l="mixamorig:LeftUpLeg", shin_l="mixamorig:LeftLeg",
    foot_l="mixamorig:LeftFoot", toe_l="mixamorig:LeftToeBase",
    thigh_r="mixamorig:RightUpLeg", shin_r="mixamorig:RightLeg",
    foot_r="mixamorig:RightFoot", toe_r="mixamorig:RightToeBase")
JN = {k: find(v) for k, v in J.items()}

# ------------------------------------------------------------- rest capture
def evaluated_positions(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me = ev.to_mesh()
    pos = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", pos)
    pos = pos.reshape(-1, 3)
    mw = np.array(ev.matrix_world)
    pos = pos @ mw[:3, :3].T + mw[:3, 3]
    ev.to_mesh_clear()
    return pos

def reset_pose():
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()

reset_pose()
OBJ = []
for obj in meshes:
    me = obj.data
    n = len(me.vertices)
    W = np.zeros((n, NB), dtype=np.float32)
    for v in me.vertices:
        for g in v.groups:
            nm = obj.vertex_groups[g.group].name
            if nm in BIDX:
                W[v.index, BIDX[nm]] += g.weight
    if (W.sum(axis=1) > 0.5).sum() < 50:
        print(f"skip {obj.name}: <50 weighted verts")
        continue
    edges = np.array([(e.vertices[0], e.vertices[1]) for e in me.edges],
                     dtype=np.int64)
    faces = []
    for p in me.polygons:
        vs = list(p.vertices)
        for k in range(1, len(vs) - 1):
            faces.append((vs[0], vs[k], vs[k + 1]))
    OBJ.append(dict(obj=obj, W=W, edges=edges,
                    faces=np.array(faces, dtype=np.int64),
                    rest=evaluated_positions(obj), dom=W.argmax(axis=1)))
    print(f"{obj.name}: {n} verts, {len(edges)} edges, {len(faces)} tris")

MW = np.array(arm.matrix_world)
def to_world(p):
    return p @ MW[:3, :3].T + MW[:3, 3]
BHEAD = {b.name: to_world(np.array(b.head_local)) for b in arm.data.bones}
BTAIL = {b.name: to_world(np.array(b.tail_local)) for b in arm.data.bones}
BDIR = {n: (BTAIL[n] - BHEAD[n]) / max(np.linalg.norm(BTAIL[n] - BHEAD[n]),
                                      1e-9) for n in BONES}
BLEN = {n: float(np.linalg.norm(BTAIL[n] - BHEAD[n])) for n in BONES}

UP = BDIR[JN["spine_lo"]]; UP = UP / np.linalg.norm(UP)
td = BDIR[JN["toe_l"]].copy(); td -= UP * (td @ UP)
FWD = td / np.linalg.norm(td)
print(f"UP={np.round(UP,2)} FWD={np.round(FWD,2)}")

# FK machinery (armature space, mathutils convention) -------------------
RESTL = {b.name: np.array(b.matrix_local) for b in arm.data.bones}
OFFSET = {}
for n in BONES:
    p = PARENT[n]
    OFFSET[n] = (np.linalg.inv(RESTL[p]) @ RESTL[n]) if p else RESTL[n]

def fk(pose):
    out = {}
    for n in BONES:
        base = out[PARENT[n]] @ OFFSET[n] if PARENT[n] else OFFSET[n]
        if n in pose:
            R = np.eye(4)
            R[:3, :3] = np.array(Euler(pose[n], 'XYZ').to_matrix())
            base = base @ R
        out[n] = base
    return out

def fk_seg(fkm, bn):
    M = fkm[bn]
    head = M[:3, 3]
    tail = head + M[:3, :3] @ np.array([0, BLEN[bn], 0])
    d = tail - head
    return head, tail, d / max(np.linalg.norm(d), 1e-9)

def resolve_bend(bn, target_dir, cap_deg):
    _, _, rest_dir = fk_seg(fk({}), bn)
    want = math.degrees(math.acos(float(np.clip(rest_dir @ target_dir,
                                                -1, 1))))
    ang = math.radians(min(max(want, 20.0), cap_deg))
    best = None
    for comp in (0, 2):
        for sgn in (1, -1):
            e = [0, 0, 0]; e[comp] = sgn * ang
            _, _, d = fk_seg(fk({bn: tuple(e)}), bn)
            score = float(d @ target_dir)
            if best is None or score > best[0]:
                best = (score, tuple(e))
    return best[1], math.degrees(ang)

# ------------------------------------------------------------- static audit
static = {}
for O in OBJ:
    W, rest = O["W"], O["rest"]
    sums = W.sum(axis=1)
    infl = (W > 1e-4).sum(axis=1)
    e = O["edges"]
    l1 = np.abs(W[e[:, 0]] - W[e[:, 1]]).sum(axis=1) / 2.0
    worst = []
    for bi, bn in enumerate(BONES):
        sel = np.where(W[:, bi] >= 0.25)[0]
        if len(sel) == 0:
            continue
        a, b = BHEAD[bn], BTAIL[bn]
        ab = b - a; L2 = max(ab @ ab, 1e-12)
        t = np.clip(((rest[sel] - a) @ ab) / L2, 0, 1)
        d = np.linalg.norm(rest[sel] - (a + t[:, None] * ab), axis=1)
        k = int(np.argmax(d))
        worst.append((float(d[k]), bn, int(sel[k])))
    worst.sort(reverse=True)
    static[O["obj"].name] = dict(
        verts=int(len(rest)),
        weight_sum_min=round(float(sums.min()), 4),
        weight_sum_max=round(float(sums.max()), 4),
        verts_sum_off_1pct=int((np.abs(sums - 1) > 0.01).sum()),
        zero_weight_verts=int((sums < 1e-4).sum()),
        verts_over_4_influences=int((infl > 4).sum()),
        max_influences=int(infl.max()),
        weight_edge_L1_p99=round(float(np.percentile(l1, 99)), 3),
        weight_edge_L1_max=round(float(l1.max()), 3),
        distant_weight_worst=[dict(bone=b, vert=v, dist_m=round(d, 3))
                              for d, b, v in worst[:5]])

CHAINS = [("arm_l", "shoulder"), ("fore_l", "elbow"), ("hand_l", "wrist"),
          ("thigh_l", "hip"), ("shin_l", "knee"), ("foot_l", "ankle"),
          ("arm_r", "shoulder"), ("fore_r", "elbow"),
          ("thigh_r", "hip"), ("shin_r", "knee")]
support = {}
for O in OBJ:
    W, rest, dom = O["W"], O["rest"], O["dom"]
    for key, label in CHAINS:
        bn = JN[key]
        if not bn:
            continue
        bi = BIDX[bn]
        sel = np.where(W[:, bi] >= 0.3)[0]
        if len(sel) >= 20:
            t = ((rest[sel] - BHEAD[bn]) @ BDIR[bn]) / BLEN[bn]
            bins = np.clip((t * 16).astype(int), 0, 15)
            support[f"{O['obj'].name}:{bn}:rings"] = dict(
                rings_of_16=int(len(np.unique(bins[(t >= 0) & (t <= 1)]))),
                weighted_verts=int(len(sel)))
        pn = PARENT[bn]
        if pn:
            pi = BIDX[pn]
            selp = np.where(dom == pi)[0]
            d = np.linalg.norm(rest[selp] - BHEAD[bn], axis=1)
            near = selp[d < 0.45 * BLEN[pn]]
            if len(near) >= 8:
                cen = rest[near].mean(axis=0)
                rad = float(np.sqrt((((rest[near] - cen) ** 2)
                                      .sum(axis=1)).mean()))
                off = float(np.linalg.norm(cen - BHEAD[bn]))
                support[f"{O['obj'].name}:pivot:{label}:{bn}"] = dict(
                    offset_m=round(off, 4), local_radius_m=round(rad, 4),
                    offset_over_radius=round(off / max(rad, 1e-6), 3),
                    station_verts=int(len(near)))
static["__support__"] = support

def ang_from(v, ref):
    return round(math.degrees(math.acos(float(
        np.clip(v @ ref / np.linalg.norm(v), -1, 1)))), 1)
static["__bind__"] = {
    JN[k]: dict(angle_from_down_deg=ang_from(BDIR[JN[k]], -UP),
                angle_from_horizontal_deg=90 - ang_from(BDIR[JN[k]], UP))
    for k in ("arm_l", "arm_r", "thigh_l", "thigh_r")}
static["__census__"] = dict(
    total_bones=NB,
    finger_bones=sum(1 for n in BONES if "Hand" in n
                     and n not in (JN["hand_l"], JN["hand_r"])),
    tail_bones=sum(1 for n in BONES if "Tail" in n),
    ear_bones=sum(1 for n in BONES if "Ear" in n),
    twist_helper_bones=[n for n in BONES if "twist" in n.lower()],
    clavicle_bones=[JN["clav_l"], JN["clav_r"]])
with open(os.path.join(OUT, "static.json"), "w") as fh:
    json.dump(static, fh, indent=1, default=str)
print("static audit written")

# ------------------------------------------------------------------- poses
def pose_metrics():
    out = {}
    for O in OBJ:
        pos = evaluated_positions(O["obj"])
        e, f, rest = O["edges"], O["faces"], O["rest"]
        rl = np.linalg.norm(rest[e[:, 0]] - rest[e[:, 1]], axis=1)
        pl = np.linalg.norm(pos[e[:, 0]] - pos[e[:, 1]], axis=1)
        strain = pl / np.maximum(rl, 1e-9)
        p0, p1, p2 = rest[f[:, 0]], rest[f[:, 1]], rest[f[:, 2]]
        q0, q1, q2 = pos[f[:, 0]], pos[f[:, 1]], pos[f[:, 2]]
        e1 = p1 - p0
        e1n = e1 / np.maximum(np.linalg.norm(e1, axis=1, keepdims=True),
                              1e-12)
        n = np.cross(e1, p2 - p0)
        n = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        e2 = np.cross(n, e1n)
        u1 = np.linalg.norm(e1, axis=1)
        u2x = ((p2 - p0) * e1n).sum(axis=1); u2y = ((p2 - p0) * e2).sum(axis=1)
        v1x = ((q1 - q0) * e1n).sum(axis=1); v1y = ((q1 - q0) * e2).sum(axis=1)
        v2x = ((q2 - q0) * e1n).sum(axis=1); v2y = ((q2 - q0) * e2).sum(axis=1)
        detF = (v1x * v2y - v1y * v2x) / np.maximum(u1 * u2y, 1e-12)
        ra = np.linalg.norm(np.cross(p1 - p0, p2 - p0), axis=1)
        pa = np.linalg.norm(np.cross(q1 - q0, q2 - q0), axis=1)
        area = pa / np.maximum(ra, 1e-12)
        vstrain = np.zeros(len(rest))
        np.maximum.at(vstrain, e[:, 0], strain)
        np.maximum.at(vstrain, e[:, 1], strain)
        out[O["obj"].name] = dict(pos=pos, strain=strain, vstrain=vstrain,
                                  detF=detF, area=area)
    return out

def summarise(m, region_bones):
    allstrain = np.concatenate([m[o]["strain"] for o in m])
    s = dict(
        edge_strain_max=round(float(allstrain.max()), 3),
        edge_strain_p99=round(float(np.percentile(allstrain, 99)), 3),
        pct_edges_strain_gt_1_5=round(float((allstrain > 1.5).mean() * 100), 2),
        pct_edges_strain_lt_0_6=round(float((allstrain < 0.6).mean() * 100), 2),
        faces_flipped=int(sum(int((m[o]["detF"] < 0).sum()) for o in m)),
        faces_area_lt_0_2_pct=round(float(np.mean(np.concatenate(
            [m[o]["area"] for o in m]) < 0.2) * 100), 2))
    s["faces_flipped_pct"] = round(100 * s["faces_flipped"] / max(
        sum(len(m[o]["detF"]) for o in m), 1), 2)
    rb = [BIDX[b] for b in region_bones if b in BIDX]
    if rb:
        rstrain, rflip, rarea = [], 0, []
        for O in OBJ:
            mm = m[O["obj"].name]
            emask = np.isin(O["dom"][O["edges"]], rb).any(axis=1)
            fmask = np.isin(O["dom"][O["faces"]], rb).any(axis=1)
            if emask.any():
                rstrain.append(mm["strain"][emask])
            if fmask.any():
                rflip += int((mm["detF"][fmask] < 0).sum())
                rarea.append(mm["area"][fmask])
        if rstrain:
            rc = np.concatenate(rstrain)
            s["region_strain_max"] = round(float(rc.max()), 3)
            s["region_strain_p99"] = round(float(np.percentile(rc, 99)), 3)
        s["region_faces_flipped"] = rflip
        if rarea:
            s["region_min_area_ratio"] = round(
                float(np.concatenate(rarea).min()), 3)
    s["per_object_strain_max"] = {
        o: round(float(m[o]["strain"].max()), 3) for o in m}
    return s

POSES = []
F, U = FWD, UP
def add_bend(name, jkey, target, cap, region_keys, note=""):
    bn = JN[jkey]
    if not bn:
        return
    e, ach = resolve_bend(bn, target, cap)
    POSES.append((name, {bn: e}, [JN[k] for k in region_keys if JN[k]],
                  note, round(ach, 1)))
def add_twist(name, jkey, deg, region_keys, note=""):
    bn = JN[jkey]
    if not bn:
        return
    POSES.append((name, {bn: (0, math.radians(deg), 0)},
                  [JN[k] for k in region_keys if JN[k]], note, deg))
def add_pose(name, pose, region_keys, note=""):
    POSES.append((name, pose, [JN[k] for k in region_keys if JN[k]],
                  note, None))

add_bend("elbow_flex_L", "fore_l", F, 150, ["arm_l", "fore_l"])
add_bend("elbow_flex_R", "fore_r", F, 150, ["arm_r", "fore_r"])
add_bend("knee_flex_L", "shin_l", -F, 140, ["thigh_l", "shin_l"])
add_bend("knee_flex_R", "shin_r", -F, 140, ["thigh_r", "shin_r"])
add_bend("hip_flex_L", "thigh_l", F, 120, ["pelvis", "thigh_l"])
add_bend("shoulder_flex_L", "arm_l", F, 170, ["clav_l", "arm_l"])
add_bend("shoulder_overhead_L", "arm_l", U, 175, ["clav_l", "arm_l"])
add_bend("shoulder_overhead_R", "arm_r", U, 175, ["clav_r", "arm_r"])
add_bend("clavicle_raise_L", "clav_l", U, 40, ["clav_l", "arm_l"],
         "shrug: clavicle carries the arm root")
add_bend("wrist_flex_L", "hand_l", F, 80, ["fore_l", "hand_l"])
add_bend("ankle_plantar_L", "foot_l", -U, 60, ["shin_l", "foot_l"])
add_bend("ankle_dorsi_L", "foot_l", F + U, 40, ["shin_l", "foot_l"])
add_bend("neck_flex", "neck", F, 60, ["neck", "head"])
add_bend("neck_extend", "neck", -F, 60, ["neck", "head"])
add_bend("spine_flex", "spine_mid", F, 45,
         ["spine_lo", "spine_mid", "spine_hi"])
add_twist("forearm_twist_L_180", "fore_l", 180, ["fore_l", "hand_l"],
          "candy-wrapper probe")
add_twist("upperarm_twist_L_180", "arm_l", 180, ["arm_l", "fore_l"])
add_twist("thigh_twist_L_90", "thigh_l", 90, ["thigh_l", "shin_l"])
add_twist("neck_twist_80", "neck", 80, ["neck", "head"])
add_twist("spine_twist_45", "spine_mid", 45,
          ["spine_lo", "spine_mid", "spine_hi"])

for nm, jk, rk in (("elbow_hyper_L", "fore_l", ["arm_l", "fore_l"]),
                   ("knee_hyper_L", "shin_l", ["thigh_l", "shin_l"])):
    bn = JN[jk]
    tgt = F if "elbow" in nm else -F
    e, _ = resolve_bend(bn, tgt, 150)
    dom = max(range(3), key=lambda i: abs(e[i]))
    if abs(e[dom]) > 1e-9:
        scale = math.radians(-12) / e[dom]
        POSES.append((nm, {bn: tuple(x * scale for x in e)},
                      [JN[k] for k in rk], "hyperextension probe", 12))

hand = JN["hand_l"]
if hand:
    pose = {}
    wrist_head, _, _ = fk_seg(fk({}), hand)
    for bn in BONES:
        if bn.startswith("mixamorig:LeftHand") and bn != hand:
            best = None
            for comp in (0, 2):
                for sgn in (1, -1):
                    e = [0, 0, 0]; e[comp] = sgn * math.radians(80)
                    _, tail, _ = fk_seg(fk({bn: tuple(e)}), bn)
                    d = float(np.linalg.norm(tail - wrist_head))
                    if best is None or d < best[0]:
                        best = (d, tuple(e))
            pose[bn] = best[1]
    if pose:
        POSES.append(("fist_L", pose, [hand], "finger bones curled 80deg",
                      None))

def combined(name, specs, note=""):
    pose = {}
    for jk, tgt, cap in specs:
        bn = JN[jk]
        if bn:
            e, _ = resolve_bend(bn, tgt, cap)
            pose[bn] = e
    POSES.append((name, pose, list(pose.keys()), note, None))

combined("deep_squat", [("thigh_l", F, 110), ("thigh_r", F, 110),
                        ("shin_l", -F, 130), ("shin_r", -F, 130),
                        ("foot_l", F + U, 30), ("foot_r", F + U, 30),
                        ("spine_mid", F, 20)])
combined("arms_overhead_both", [("arm_l", U, 175), ("arm_r", U, 175),
                                ("fore_l", F, 30), ("fore_r", F, 30)])
combined("touch_toes", [("spine_lo", F, 20), ("spine_mid", F, 25),
                        ("spine_hi", F, 20), ("thigh_l", F, 60),
                        ("thigh_r", F, 60), ("neck", F, 30)])

# ------------------------------------------------------- run, flushing often
RESULTS_PATH = os.path.join(OUT, "results.json")
POSES_DIR = os.path.join(OUT, "poses_npz")
os.makedirs(POSES_DIR, exist_ok=True)
results = {}
if os.path.exists(RESULTS_PATH):
    try:
        results = json.load(open(RESULTS_PATH)).get("poses", {})
    except Exception:
        results = {}
_rest_dump = {}
for O in OBJ:
    on = O["obj"].name
    _rest_dump[f"rest|{on}|pos"] = O["rest"].astype(np.float32)
    _rest_dump[f"rest|{on}|dom"] = O["dom"].astype(np.int32)
    _rest_dump[f"rest|{on}|edges"] = O["edges"].astype(np.int32)
    _rest_dump[f"rest|{on}|bones"] = np.array(BONES)
np.savez_compressed(os.path.join(OUT, "rest.npz"), **_rest_dump)

for name, pose, region, note, ach in POSES:
    if name in results and os.path.exists(
            os.path.join(POSES_DIR, name + ".npz")):
        print(f"skip {name} (already audited)")
        continue
    reset_pose()
    for bn, e in pose.items():
        arm.pose.bones[bn].rotation_euler = e
    bpy.context.view_layer.update()
    m = pose_metrics()
    s = summarise(m, region)
    s["note"] = note
    if ach:
        s["bend_deg"] = ach
    s["region_bones"] = region
    results[name] = s
    pdump = {}
    for O in OBJ:
        on = O["obj"].name
        pdump[f"{on}|pos"] = m[on]["pos"].astype(np.float32)
        pdump[f"{on}|vstrain"] = m[on]["vstrain"].astype(np.float32)
    np.savez_compressed(os.path.join(POSES_DIR, name + ".npz"), **pdump)
    with open(RESULTS_PATH, "w") as fh:
        json.dump(dict(subject=os.path.basename(GLB), poses=results),
                  fh, indent=1, default=str)
    print(f"{name}: strain_max={s['edge_strain_max']} "
          f"region_max={s.get('region_strain_max')} "
          f"flips={s['faces_flipped']} p99={s['edge_strain_p99']}")
    sys.stdout.flush()

reset_pose()
print("AUDIT DONE")
