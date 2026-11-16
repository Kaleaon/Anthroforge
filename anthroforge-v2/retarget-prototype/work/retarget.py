import bpy, math, os, json, sys
from mathutils import Matrix, Vector

OUT = os.path.expanduser("~/workspace/anthroforge-v2/retarget-prototype")
MODELS = os.path.expanduser("~/workspace/stick-figure-avatar/furry-lineup/threejs-lineup/models")
FPS = 30.0

def log(*a): print("[RT]", *a, flush=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = 30

# ---------- import source (wolf) ----------
bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, "bara_wolf_avatar.glb"))
wolf = bpy.data.objects["BaraWolf"]; wolf.name = "Wolf_SRC"
SRC_ACTIONS = {a.name: a for a in bpy.data.actions}
log("wolf actions:", list(SRC_ACTIONS))
for a in SRC_ACTIONS.values(): a.use_fake_user = True
def strip_nla(arm):
    """Remove NLA tracks so evaluation is driven by the active action only."""
    if arm.animation_data:
        for t in list(arm.animation_data.nla_tracks):
            arm.animation_data.nla_tracks.remove(t)
        arm.animation_data.action = None
strip_nla(wolf)

# ---------- import target (fennec) ----------
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, "pyn_fennec.glb"))
newobjs = [o for o in bpy.data.objects if o not in before]
fen = [o for o in newobjs if o.type == 'ARMATURE'][0]; fen.name = "Fennec_TGT"
fen.rotation_euler = (0, 0, 0)  # importer left a -90deg X world rotation on the object; zero it so world-space metrics share the wolf's frame (armature space untouched)
fen_meshes = [o for o in newobjs if o.type == 'MESH']
log("fennec armature:", fen.name, "meshes:", [m.name for m in fen_meshes])
log("fennec world matrix:", [round(v,3) for row in fen.matrix_world for v in row])
log("wolf   world matrix:", [round(v,3) for row in wolf.matrix_world for v in row])

# ---------- bone mapping: wolf (Mixamo) -> fennec (Codaj) ----------
P = "mixamorig:"
MAP = {
    P+"Hips": "Hips_01", P+"Spine": "Spine_02", P+"Spine1": "Chest_001_03",
    P+"Spine2": "Chest_06", P+"Neck": "Neck_07", P+"Head": "Head_08",
    P+"LeftShoulder": "Shouder_L_020", P+"LeftArm": "Left arm_021",
    P+"LeftForeArm": "Middlearm_L_022", P+"LeftHand": "Left wrist_023",
    P+"RightShoulder": "Shouder_R_044", P+"RightArm": "Right arm_045",
    P+"RightForeArm": "Middlearm_R_046", P+"RightHand": "Right wrist_047",
    P+"LeftUpLeg": "Left leg_068", P+"LeftLeg": "Middleleg_L_069",
    P+"LeftFoot": "Foot1_L_070", P+"LeftToeBase": "Foot2_L_071",
    P+"RightUpLeg": "Right leg_092", P+"RightLeg": "Middleleg_R_093",
    P+"RightFoot": "Foot1_R_094", P+"RightToeBase": "Foot2_R_095",
}
for s, t in MAP.items():
    assert s in wolf.data.bones, f"missing source bone {s}"
    assert t in fen.data.bones, f"missing target bone {t}"
log("mapping OK:", len(MAP), "pairs")

# ---------- rest data ----------
def rest_data(arm):
    return {b.name: b.matrix_local.copy() for b in arm.data.bones}
def depth_order(arm):
    def depth(b):
        d = 0
        while b.parent: d += 1; b = b.parent
        return d
    return [b.name for b in sorted(arm.data.bones, key=depth)]
def chain_len(arm, names):
    return sum(arm.data.bones[n].length for n in names)

REST = {wolf: rest_data(wolf), fen: rest_data(fen)}
ORDER = {wolf: depth_order(wolf), fen: depth_order(fen)}

def leg_ratio(src, tgt, src_hip, tgt_hip):
    s = REST[src][src_hip].translation.z
    t = REST[tgt][tgt_hip].translation.z
    return t / s

R_FEN = leg_ratio(wolf, fen, P+"Hips", "Hips_01")
log(f"leg/hip-height ratio wolf->fennec: {R_FEN:.3f}")

# ---------- retarget core ----------
def retarget(src, tgt, mapping, src_action, new_name, hip_scale):
    """World-space (armature-space) rotation-delta retarget.
    Rotations: Q_tgt(f) = (Q_src(f) * Q_src_rest^-1) * Q_tgt_rest.
    Positions follow the TARGET's own chain (rest offsets), except the
    mapped hips bone, whose translation delta is scaled by hip_scale."""
    inv_map = {v: k for k, v in mapping.items()}
    tgt_hips = inv_map and [t for s, t in mapping.items() if s.endswith("Hips")][0]
    if tgt.animation_data is None: tgt.animation_data_create()
    act = bpy.data.actions.new(new_name)
    act.use_fake_user = True
    for pb in tgt.pose.bones:
        if pb.name in inv_map: pb.rotation_mode = 'QUATERNION'
    if src.animation_data is None: src.animation_data_create()
    src.animation_data.action = src_action
    tgt.animation_data.action = act
    Rs, Rt = REST[src], REST[tgt]
    f0, f1 = src_action.frame_range
    frames = list(range(int(math.ceil(f0)), int(math.floor(f1)) + 1))
    check = {}
    for f in frames:
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        # source deltas
        dQ, dpos = {}, None
        for s in mapping:
            Pm = src.pose.bones[s].matrix
            dQ[s] = Pm.to_quaternion() @ Rs[s].to_quaternion().inverted()
            if s.endswith("Hips"):
                dpos = Pm.translation - Rs[s].translation
        # full-tree desired matrices on target
        desired = {}
        for bn in ORDER[tgt]:
            bone = tgt.data.bones[bn]
            R = Rt[bn]
            par = bone.parent.name if bone.parent else None
            if par is None:
                base_pos = R.translation.copy()
                Mp_rot = None
            else:
                Mp = desired[par]
                base_pos = Mp @ (Rt[par].inverted() @ R.translation)
                Mp_rot = Mp.to_quaternion()
            if bn in inv_map:
                Q = dQ[inv_map[bn]] @ R.to_quaternion()
                pos = (R.translation + dpos * hip_scale) if bn == tgt_hips else base_pos
            else:
                if par is None:
                    Q, pos = R.to_quaternion(), base_pos
                else:
                    Q = Mp_rot @ (Rt[par].to_quaternion().inverted() @ R.to_quaternion())
                    pos = base_pos
            desired[bn] = Matrix.LocRotScale(pos, Q, (1, 1, 1))
        for bn, s in [(t, s) for s, t in mapping.items()]:
            # Decompose desired pose matrix into pose channels via matrix_basis
            # math: B = R_b^-1 * R_p * P_p^-1 * P_b  (root: R_b^-1 * P_b).
            # NOTE: setting pb.matrix directly does NOT sync the channels and
            # keyframing right after bakes garbage (probe-verified); the
            # explicit channel decomposition below reproduces desired exactly.
            pb = tgt.pose.bones[bn]
            bone = tgt.data.bones[bn]
            par = bone.parent.name if bone.parent else None
            if par is None:
                B = Rt[bn].inverted() @ desired[bn]
            else:
                B = Rt[bn].inverted() @ Rt[par] @ desired[par].inverted() @ desired[bn]
            pb.location = B.translation.copy()
            pb.rotation_quaternion = B.to_quaternion()
            pb.keyframe_insert(data_path="rotation_quaternion", frame=f)
            pb.keyframe_insert(data_path="location", frame=f)
        if f in (frames[0], frames[len(frames)//2], frames[-1]):
            check[f] = {bn: desired[bn].copy() for bn in inv_map}
    tgt.animation_data.action = None
    src.animation_data.action = None
    return act, check

def validate(tgt, act, check, label):
    """Re-evaluate baked action; compare pose matrices to construction values."""
    if tgt.animation_data is None: tgt.animation_data_create()
    tgt.animation_data.action = act
    worst_t, worst_r = 0.0, 0.0
    for f, mats in check.items():
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        for bn, M in mats.items():
            E = tgt.pose.bones[bn].matrix
            worst_t = max(worst_t, (E.translation - M.translation).length)
            dq = E.to_quaternion() @ M.to_quaternion().inverted()
            worst_r = max(worst_r, abs(dq.angle))
    tgt.animation_data.action = None
    log(f"VALIDATE {label}: max pos dev {worst_t*1000:.2f} mm, max rot dev {math.degrees(worst_r):.3f} deg")
    return worst_t, worst_r


# ---------- orc-sim: proportion-scaled clone of the wolf rig ----------
orc = wolf.copy(); orc.data = wolf.data.copy(); orc.name = "OrcSim_TGT"
bpy.context.scene.collection.objects.link(orc)
strip_nla(orc)
orc_meshes = []
for m in [o for o in bpy.data.objects if o.type == 'MESH' and o != orc]:
    pass
wolf_meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.parent != fen and o not in fen_meshes and o.name != 'Icosphere']
# wolf meshes: those imported in the first batch (parent or modifier -> wolf)
wolf_meshes = []
for o in list(bpy.data.objects):
    if o.type != 'MESH' or o in fen_meshes: continue
    mods = [md for md in o.modifiers if md.type == 'ARMATURE']
    if (mods and mods[0].object == wolf) or o.parent == wolf:
        wolf_meshes.append(o)
log("wolf meshes:", [m.name for m in wolf_meshes])
for m in wolf_meshes:
    nm = m.copy(); nm.name = m.name + "_OrcSim"
    bpy.context.scene.collection.objects.link(nm)
    for md in nm.modifiers:
        if md.type == 'ARMATURE': md.object = orc
    if nm.parent == wolf:
        nm.parent = orc
    orc_meshes.append(nm)

A = REST[wolf][P+"Hips"].translation.copy()  # hips anchor (armature space)
LEGK, SPINEK, ARMK = 1.20, 1.25, 1.40
def is_leg(n): return any(k in n for k in ("UpLeg","Leg","Foot","ToeBase","Toe_End")) and "Hand" not in n
def is_arm(n): return any(k in n for k in ("Shoulder","Arm","ForeArm","Hand"))
bpy.context.view_layer.objects.active = orc
bpy.ops.object.mode_set(mode='EDIT')
eb = orc.data.edit_bones
pts = {b.name: [b.head.copy(), b.tail.copy()] for b in eb}
# pass 1: legs about hips anchor (YZ x1.2), spine/head z x1.25 about hips anchor
for n, (h, t) in pts.items():
    if n == P+"Hips": continue
    for v in (h, t):
        if is_leg(n):
            v.y = A.y + (v.y - A.y) * LEGK
            v.z = A.z + (v.z - A.z) * LEGK
        else:
            v.z = A.z + (v.z - A.z) * SPINEK
# pass 2: arms x1.4 about their (already spine-scaled) shoulder head
for side in ("Left", "Right"):
    S = pts[P+side+"Shoulder"][0].copy()
    for n, (h, t) in pts.items():
        if is_arm(n) and side in n:
            for v in (h, t):
                v.x = S.x + (v.x - S.x) * ARMK
                v.y = S.y + (v.y - S.y) * ARMK
                v.z = S.z + (v.z - S.z) * ARMK
# pass 3: lift whole rig so toe tips rest on z=0
minz = min(min(pts[P+s+"Toe_End"][1].z, pts[P+s+"ToeBase"][1].z) for s in ("Left","Right"))
for n, (h, t) in pts.items():
    for v in (h, t): v.z -= minz
for n, (h, t) in pts.items():
    eb[n].head = h; eb[n].tail = t
bpy.ops.object.mode_set(mode='OBJECT')
REST[orc] = rest_data(orc); ORDER[orc] = depth_order(orc)
R_ORC = leg_ratio(wolf, orc, P+"Hips", P+"Hips")
orc_arm = chain_len(orc, [P+"RightShoulder", P+"RightArm", P+"RightForeArm", P+"RightHand"])
wolf_arm = chain_len(wolf, [P+"RightShoulder", P+"RightArm", P+"RightForeArm", P+"RightHand"])
orc_h = max(b.tail_local.z for b in orc.data.bones)
wolf_h = max(b.tail_local.z for b in wolf.data.bones)
log(f"orc-sim: hip ratio {R_ORC:.3f}, arm ratio {orc_arm/wolf_arm:.3f}, height ratio {orc_h/wolf_h:.3f} ({wolf_h:.2f} -> {orc_h:.2f} m)")

IDENT = {n: n for n in MAP}
baked = {}
# ---------- bake: fennec ----------
for clip in ("Idle", "Walk", "Wave", "Dance"):
    a, chk = retarget(wolf, fen, MAP, SRC_ACTIONS[clip], f"{clip}@Fennec_C1", R_FEN)
    baked[a.name] = a
    if clip == "Walk": validate(fen, a, chk, "fennec Walk C1")
a, chk = retarget(wolf, fen, MAP, SRC_ACTIONS["Walk"], "Walk@Fennec_C0", 1.0)
baked[a.name] = a; validate(fen, a, chk, "fennec Walk C0")
a, _ = retarget(wolf, fen, MAP, SRC_ACTIONS["Wave"], "Wave@Fennec_C0", 1.0)
baked[a.name] = a
# ---------- bake: orc-sim ----------
for clip in ("Walk", "Wave", "Idle"):
    a, chk = retarget(wolf, orc, IDENT, SRC_ACTIONS[clip], f"{clip}@Orc_C1", R_ORC)
    baked[a.name] = a
    if clip == "Walk": validate(orc, a, chk, "orc Walk C1")
a, chk = retarget(wolf, orc, IDENT, SRC_ACTIONS["Walk"], "Walk@Orc_C0", 1.0)
baked[a.name] = a; validate(orc, a, chk, "orc Walk C0")
log("baked actions:", sorted(baked))

# ---------- metrics ----------
SPEC = {
    wolf.name: dict(hips=P+"Hips", foot={"L": P+"LeftFoot", "R": P+"RightFoot"},
                    toe={"L": P+"LeftToeBase", "R": P+"RightToeBase"},
                    hand={"L": P+"LeftHand", "R": P+"RightHand"},
                    sh={"L": P+"LeftShoulder", "R": P+"RightShoulder"}, head=P+"Head",
                    armchain={"L": [P+"LeftShoulder", P+"LeftArm", P+"LeftForeArm", P+"LeftHand"],
                              "R": [P+"RightShoulder", P+"RightArm", P+"RightForeArm", P+"RightHand"]}),
    fen.name: dict(hips="Hips_01", foot={"L": "Foot1_L_070", "R": "Foot1_R_094"},
                   toe={"L": "Foot2_L_071", "R": "Foot2_R_095"},
                   hand={"L": "Left wrist_023", "R": "Right wrist_047"},
                   sh={"L": "Shouder_L_020", "R": "Shouder_R_044"}, head="Head_08",
                   armchain={"L": ["Shouder_L_020", "Left arm_021", "Middlearm_L_022", "Left wrist_023"],
                             "R": ["Shouder_R_044", "Right arm_045", "Middlearm_R_046", "Right wrist_047"]}),
    orc.name: None,
}
SPEC[orc.name] = SPEC[wolf.name]

def tip_world(arm, bname):
    pb = arm.pose.bones[bname]
    return arm.matrix_world @ (pb.matrix @ Vector((0, pb.bone.length, 0)))
def head_world(arm, bname):
    return arm.matrix_world @ arm.pose.bones[bname].matrix.translation

def floor_ref(arm, spec):
    if arm.animation_data: arm.animation_data.action = None
    bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
    return min(tip_world(arm, spec["toe"][s]).z for s in "LR")

def eval_traj(arm, act, spec):
    if arm.animation_data is None: arm.animation_data_create()
    arm.animation_data.action = act
    f0, f1 = act.frame_range
    frames = list(range(int(math.ceil(f0)), int(math.floor(f1)) + 1))
    T = {k: [] for k in ("toeL", "toeR", "ankL", "ankR", "hips", "handL", "handR", "shL", "shR", "headtop")}
    for f in frames:
        bpy.context.scene.frame_set(f); bpy.context.view_layer.update()
        T["toeL"].append(tip_world(arm, spec["toe"]["L"])); T["toeR"].append(tip_world(arm, spec["toe"]["R"]))
        T["ankL"].append(head_world(arm, spec["foot"]["L"])); T["ankR"].append(head_world(arm, spec["foot"]["R"]))
        T["hips"].append(head_world(arm, spec["hips"]))
        T["handL"].append(tip_world(arm, spec["hand"]["L"])); T["handR"].append(tip_world(arm, spec["hand"]["R"]))
        T["shL"].append(head_world(arm, spec["sh"]["L"])); T["shR"].append(head_world(arm, spec["sh"]["R"]))
        T["headtop"].append(tip_world(arm, spec["head"]))
    arm.animation_data.action = None
    return frames, T

def segments(mask):
    segs, cur = [], []
    for i, m in enumerate(mask):
        if m: cur.append(i)
        elif cur: segs.append(cur); cur = []
    if cur: segs.append(cur)
    return [s for s in segs if len(s) >= 3]

def analyse_walk(frames, T, floor):
    dt = 1.0 / FPS
    out = {}
    all_seg = []  # (t, p) per segment for shared velocity fit
    per_foot = {}
    for side, key in (("L", "toeL"), ("R", "toeR")):
        P = T["ank" + side]  # slide fit on the ankle (toe tip adds foot-roll arc noise)
        zs = [p.z for p in T[key]]
        zmin, zmax = min(zs), max(zs)
        thr = zmin + max(0.02, 0.25 * (zmax - zmin))
        mask = [z <= thr for z in zs]
        segs = segments(mask)
        seg_data = []
        for s in segs:
            ts = [frames[i] * dt for i in s]
            ps = [Vector((P[i].x, P[i].y)) for i in s]
            seg_data.append((ts, ps)); all_seg.append((ts, ps))
        per_foot[side] = seg_data
        out[f"{side}_contact_frames"] = sum(len(s) for s in segs)
        out[f"{side}_segments"] = len(segs)
    # shared treadmill velocity (least squares, per-segment intercepts)
    num = Vector((0.0, 0.0)); den = 0.0
    for ts, ps in all_seg:
        tm = sum(ts) / len(ts); pm = sum(ps, Vector((0.0, 0.0))) / len(ps)
        for t, p in zip(ts, ps):
            num += (t - tm) * (p - pm); den += (t - tm) ** 2
    v = -num / den if den > 0 else Vector((0.0, 0.0))
    drifts, nets, rmss = [], [], []
    for ts, ps in all_seg:
        g = [p + v * t for t, p in zip(ts, ps)]
        gm = sum(g, Vector((0.0, 0.0))) / len(g)
        drifts.append(sum((g[i+1] - g[i]).length for i in range(len(g) - 1)))
        nets.append((g[-1] - g[0]).length)
        rmss.append(math.sqrt(sum((x - gm).length ** 2 for x in g) / len(g)))
    # stride: toe travel along velocity dir relative to hips
    vhat = v.normalized() if v.length > 1e-6 else Vector((0.0, -1.0))
    strides = []
    for key in ("ankL", "ankR"):
        rel = [(p - h) for p, h in zip(T[key], T["hips"])]
        proj = [r.x * vhat.x + r.y * vhat.y for r in rel]
        strides.append(max(proj) - min(proj))
    allz = [p.z for k in ("toeL", "toeR") for p in T[k]]
    contact_z = [T[k][i].z for k in ("toeL", "toeR") for i in range(len(frames))
                 if T[k][i].z <= min(p.z for p in T[k]) + max(0.02, 0.25 * (max(p.z for p in T[k]) - min(p.z for p in T[k])))]
    out.update(
        treadmill_speed_mps=round(v.length, 3),
        drift_path_cm_per_step=round(100 * sum(drifts) / len(drifts), 2) if drifts else None,
        drift_path_cm_max=round(100 * max(drifts), 2) if drifts else None,
        drift_net_cm_per_step=round(100 * sum(nets) / len(nets), 2) if nets else None,
        contact_rms_cm=round(100 * (sum(rmss) / len(rmss)), 2) if rmss else None,
        stride_m=round(sum(strides) / len(strides), 3),
        min_toe_below_floor_cm=round(100 * (min(allz) - floor), 2),
        mean_contact_toe_above_floor_cm=round(100 * (sum(contact_z) / len(contact_z) - floor), 2),
        hips_mean_z=round(sum(h.z for h in T["hips"]) / len(T["hips"]), 3),
    )
    return out

def analyse_wave(frames, Tsrc, Ttgt, side, arm_src, arm_tgt):
    ns = [(h - s) / arm_src for h, s in zip(Tsrc[f"hand{side}"], Tsrc[f"sh{side}"])]
    nt = [(h - s) / arm_tgt for h, s in zip(Ttgt[f"hand{side}"], Ttgt[f"sh{side}"])]
    n = min(len(ns), len(nt))
    rms = math.sqrt(sum((ns[i] - nt[i]).length ** 2 for i in range(n)) / n)
    return rms, None

results = {}
floors = {a.name: floor_ref(a, SPEC[a.name]) for a in (wolf, fen, orc)}
log("floor refs:", floors)

walk_versions = [
    ("wolf_original", wolf, SRC_ACTIONS["Walk"]),
    ("fennec_C0_nocomp", fen, baked["Walk@Fennec_C0"]),
    ("fennec_C1_comp", fen, baked["Walk@Fennec_C1"]),
    ("orc_C0_nocomp", orc, baked["Walk@Orc_C0"]),
    ("orc_C1_comp", orc, baked["Walk@Orc_C1"]),
]
traj = {}
for label, arm, act in walk_versions:
    fr, T = eval_traj(arm, act, SPEC[arm.name])
    traj[label] = (fr, T)
    results[label] = analyse_walk(fr, T, floors[arm.name])
    log("WALK", label, results[label])

# wave hand detection on source
frw, Tw = eval_traj(wolf, SRC_ACTIONS["Wave"], SPEC[wolf.name])
rng = {s: max(p.z for p in Tw[f"hand{s}"]) - min(p.z for p in Tw[f"hand{s}"]) for s in "LR"}
side = max(rng, key=rng.get)
log("wave hand side:", side, "z-ranges:", rng)
wolf_arm_len = chain_len(wolf, SPEC[wolf.name]["armchain"][side])
wave_res = {}
for label, arm, act in [("fennec_C1_comp", fen, baked["Wave@Fennec_C1"]),
                        ("fennec_C0_nocomp", fen, baked["Wave@Fennec_C0"]),
                        ("orc_C1_comp", orc, baked["Wave@Orc_C1"])]:
    fr2, T2 = eval_traj(arm, act, SPEC[arm.name])
    alen = chain_len(arm, SPEC[arm.name]["armchain"][side])
    rms, _ = analyse_wave(frw, Tw, T2, side, wolf_arm_len, alen)
    peak_tgt = max(T2[f"hand{side}"][i].z - T2["headtop"][i].z for i in range(len(fr2))) / alen
    peak_src = max(Tw[f"hand{side}"][i].z - Tw["headtop"][i].z for i in range(len(frw))) / wolf_arm_len
    wave_res[label] = dict(hand_rms_err_pct_arm=round(100 * rms, 1),
                           hand_rms_err_cm_at_target=round(100 * rms * alen, 1),
                           peak_hand_above_head_norm=round(peak_tgt, 2),
                           peak_hand_above_head_norm_source=round(peak_src, 2))
    log("WAVE", label, wave_res[label])
results["wave"] = wave_res
results["meta"] = dict(
    leg_ratio_fennec=round(R_FEN, 3), leg_ratio_orc=round(R_ORC, 3),
    arm_ratio_orc=round(orc_arm / wolf_arm, 3), height_ratio_orc=round(orc_h / wolf_h, 3),
    wolf_arm_len_m=round(wolf_arm, 3), fen_arm_len_m=round(chain_len(fen, SPEC[fen.name]["armchain"][side]), 3),
    floors={k: round(v, 4) for k, v in floors.items()}, wave_hand_side=side, fps=FPS)
with open(os.path.join(OUT, "metrics.json"), "w") as fh:
    json.dump(results, fh, indent=1)
log("metrics written")

# ---------- NLA stash, save, export ----------
def stash(arm, acts):
    if arm.animation_data is None: arm.animation_data_create()
    arm.animation_data.action = None
    have = {t.name for t in arm.animation_data.nla_tracks}
    for a in acts:
        if a and a.name not in have:
            trk = arm.animation_data.nla_tracks.new(); trk.name = a.name
            trk.strips.new(a.name, 1, a)
stash(wolf, [SRC_ACTIONS[n] for n in ("Idle", "Walk", "Wave", "Dance")])
stash(fen, [baked[n] for n in ("Idle@Fennec_C1", "Walk@Fennec_C1", "Wave@Fennec_C1", "Dance@Fennec_C1", "Walk@Fennec_C0", "Wave@Fennec_C0")])
stash(orc, [baked[n] for n in ("Idle@Orc_C1", "Walk@Orc_C1", "Wave@Orc_C1")])
blend_path = os.path.join(OUT, "retarget_prototype.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
log("saved blend:", blend_path)

bpy.ops.object.select_all(action='DESELECT')
for o in [fen] + fen_meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = fen
glb_path = os.path.join(OUT, "fennec_retargeted.glb")
try:
    bpy.ops.export_scene.gltf(filepath=glb_path, use_selection=True, export_animations=True,
                              export_animation_mode='NLA_TRACKS')
except TypeError:
    bpy.ops.export_scene.gltf(filepath=glb_path, use_selection=True, export_animations=True)
log("exported GLB:", glb_path, os.path.getsize(glb_path))
log("DONE")
