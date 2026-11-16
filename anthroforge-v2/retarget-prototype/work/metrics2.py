import bpy, math, os, json
from mathutils import Matrix, Vector

OUT = os.path.expanduser("~/workspace/anthroforge-v2/retarget-prototype")
FPS = 30.0
P = "mixamorig:"
bpy.ops.wm.open_mainfile(filepath=os.path.join(OUT, "retarget_prototype.blend"))
wolf = bpy.data.objects["Wolf_SRC"]; fen = bpy.data.objects["Fennec_TGT"]; orc = bpy.data.objects["OrcSim_TGT"]
for a in (wolf, fen, orc):
    if a.animation_data:
        for t in a.animation_data.nla_tracks: t.mute = True
        a.animation_data.action = None
bpy.context.view_layer.update()

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
}
SPEC[orc.name] = SPEC[wolf.name]

def tip_w(arm, b): 
    pb = arm.pose.bones[b]
    return arm.matrix_world @ (pb.matrix @ Vector((0, pb.bone.length, 0)))
def head_w(arm, b):
    return arm.matrix_world @ arm.pose.bones[b].matrix.translation

def char_frame(arm, spec):
    """Orthonormal character frame from the REST pose, in world space.
    Returns (origin, R) with R columns = (right, forward, up); a world point
    p maps to frame coords R^T (p - origin): x=right, y=forward, z=up."""
    arm.animation_data.action = None
    bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
    hips = head_w(arm, spec["hips"]); head = head_w(arm, spec["head"])
    up = (head - hips); up.normalize()
    toe_c = (tip_w(arm, spec["toe"]["L"]) + tip_w(arm, spec["toe"]["R"])) / 2
    ank_c = (head_w(arm, spec["foot"]["L"]) + head_w(arm, spec["foot"]["R"])) / 2
    fwd = toe_c - ank_c
    fwd = fwd - up * fwd.dot(up); fwd.normalize()
    right = fwd.cross(up).normalized() if False else up.cross(fwd).normalized()
    # ensure right points toward the character's left side (+X for wolf): use hips->left ankle
    la = head_w(arm, spec["foot"]["L"]) - hips
    if right.dot(la) < 0: right = -right
    R = Matrix((right, fwd, up)).transposed()  # columns? build explicitly below
    M = Matrix.Identity(3)
    M.col[0] = right; M.col[1] = fwd; M.col[2] = up
    return hips, M

FRAMES = {}
for a in (wolf, fen, orc):
    o, M = char_frame(a, SPEC[a.name])
    FRAMES[a.name] = (o, M)
    print(f"[M2] {a.name} frame: origin={tuple(round(v,3) for v in o)} up_col={tuple(round(v,2) for v in M.col[2])} fwd_col={tuple(round(v,2) for v in M.col[1])}")

def to_frame(arm, p):
    o, M = FRAMES[arm.name]
    return M.inverted() @ (p - o)

def floor_ref(arm, spec):
    arm.animation_data.action = None
    bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
    return min(to_frame(arm, tip_w(arm, spec["toe"][s])).z for s in "LR")

def eval_traj(arm, act, spec):
    arm.animation_data.action = act
    f0, f1 = act.frame_range
    frames = list(range(int(math.ceil(f0)), int(math.floor(f1)) + 1))
    T = {k: [] for k in ("toeL","toeR","ankL","ankR","hips","handL","handR","shL","shR","headtop")}
    for f in frames:
        bpy.context.scene.frame_set(f); bpy.context.view_layer.update()
        for key, b, fn in (("toeL","toe_L",None),): pass
        T["toeL"].append(to_frame(arm, tip_w(arm, spec["toe"]["L"]))); T["toeR"].append(to_frame(arm, tip_w(arm, spec["toe"]["R"])))
        T["ankL"].append(to_frame(arm, head_w(arm, spec["foot"]["L"]))); T["ankR"].append(to_frame(arm, head_w(arm, spec["foot"]["R"])))
        T["hips"].append(to_frame(arm, head_w(arm, spec["hips"])))
        T["handL"].append(to_frame(arm, tip_w(arm, spec["hand"]["L"]))); T["handR"].append(to_frame(arm, tip_w(arm, spec["hand"]["R"])))
        T["shL"].append(to_frame(arm, head_w(arm, spec["sh"]["L"]))); T["shR"].append(to_frame(arm, head_w(arm, spec["sh"]["R"])))
        T["headtop"].append(to_frame(arm, tip_w(arm, spec["head"])))
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
    dt = 1.0 / FPS; out = {}; all_seg = []
    for side in "LR":
        P = T["ank" + side]; zs = [p.z for p in T["toe" + side]]
        zmin, zmax = min(zs), max(zs)
        thr = zmin + max(0.02, 0.25 * (zmax - zmin))
        segs = segments([z <= thr for z in zs])
        for s in segs:
            all_seg.append(([frames[i] * dt for i in s], [Vector((P[i].x, P[i].y)) for i in s]))
        out[f"{side}_contact_frames"] = sum(len(s) for s in segs); out[f"{side}_segments"] = len(segs)
    num = Vector((0.0, 0.0)); den = 0.0
    for ts, ps in all_seg:
        tm = sum(ts) / len(ts); pm = sum(ps, Vector((0.0, 0.0))) / len(ps)
        for t, p in zip(ts, ps): num += (t - tm) * (p - pm); den += (t - tm) ** 2
    v = -num / den if den > 0 else Vector((0.0, 0.0))
    drifts, nets, rmss = [], [], []
    for ts, ps in all_seg:
        g = [p + v * t for t, p in zip(ts, ps)]
        gm = sum(g, Vector((0.0, 0.0))) / len(g)
        drifts.append(sum((g[i+1] - g[i]).length for i in range(len(g) - 1)))
        nets.append((g[-1] - g[0]).length)
        rmss.append(math.sqrt(sum((x - gm).length ** 2 for x in g) / len(g)))
    vhat = v.normalized() if v.length > 1e-6 else Vector((0.0, 1.0))
    strides = []
    for key in ("ankL", "ankR"):
        proj = [(p - h).x * vhat.x + (p - h).y * vhat.y for p, h in zip(T[key], T["hips"])]
        strides.append(max(proj) - min(proj))
    allz = [p.z for k in ("toeL", "toeR") for p in T[k]]
    cz = []
    for k in ("toeL", "toeR"):
        zs = [p.z for p in T[k]]; thr = min(zs) + max(0.02, 0.25 * (max(zs) - min(zs)))
        cz += [z for z in zs if z <= thr]
    out.update(treadmill_speed_mps=round(v.length, 3),
               drift_path_cm_per_step=round(100 * sum(drifts) / len(drifts), 2) if drifts else None,
               drift_path_cm_max=round(100 * max(drifts), 2) if drifts else None,
               drift_net_cm_per_step=round(100 * sum(nets) / len(nets), 2) if nets else None,
               contact_rms_cm=round(100 * sum(rmss) / len(rmss), 2) if rmss else None,
               stride_m=round(sum(strides) / len(strides), 3),
               min_toe_below_floor_cm=round(100 * (min(allz) - floor), 2),
               mean_contact_toe_above_floor_cm=round(100 * (sum(cz) / len(cz) - floor), 2),
               hips_mean_height=round(sum(h.z for h in T["hips"]) / len(T["hips"]), 3))
    return out

def chain_len(arm, names): return sum(arm.data.bones[n].length for n in names)
A = bpy.data.actions
results = {}
floors = {a.name: floor_ref(a, SPEC[a.name]) for a in (wolf, fen, orc)}
print("[M2] floors (char frame):", {k: round(v, 4) for k, v in floors.items()})
walk_versions = [("wolf_original", wolf, A["Walk"]), ("fennec_C0_nocomp", fen, A["Walk@Fennec_C0"]),
                 ("fennec_C1_comp", fen, A["Walk@Fennec_C1"]), ("orc_C0_nocomp", orc, A["Walk@Orc_C0"]),
                 ("orc_C1_comp", orc, A["Walk@Orc_C1"])]
for label, arm, act in walk_versions:
    fr, T = eval_traj(arm, act, SPEC[arm.name])
    results[label] = analyse_walk(fr, T, floors[arm.name])
    print("[M2] WALK", label, results[label])
frw, Tw = eval_traj(wolf, A["Wave"], SPEC[wolf.name])
rng = {s: max(p.z for p in Tw[f"hand{s}"]) - min(p.z for p in Tw[f"hand{s}"]) for s in "LR"}
side = max(rng, key=rng.get)
print("[M2] wave side:", side, rng)
wolf_al = chain_len(wolf, SPEC[wolf.name]["armchain"][side])
wave_res = {}
for label, arm, act in [("fennec_C1_comp", fen, A["Wave@Fennec_C1"]), ("fennec_C0_nocomp", fen, A["Wave@Fennec_C0"]),
                        ("orc_C1_comp", orc, A["Wave@Orc_C1"])]:
    fr2, T2 = eval_traj(arm, act, SPEC[arm.name])
    alen = chain_len(arm, SPEC[arm.name]["armchain"][side])
    ns = [(h - s) / wolf_al for h, s in zip(Tw[f"hand{side}"], Tw[f"sh{side}"])]
    nt = [(h - s) / alen for h, s in zip(T2[f"hand{side}"], T2[f"sh{side}"])]
    n = min(len(ns), len(nt))
    rms = math.sqrt(sum((ns[i] - nt[i]).length ** 2 for i in range(n)) / n)
    peak_t = max(T2[f"hand{side}"][i].z - T2["headtop"][i].z for i in range(len(fr2))) / alen
    peak_s = max(Tw[f"hand{side}"][i].z - Tw["headtop"][i].z for i in range(len(frw))) / wolf_al
    wave_res[label] = dict(hand_rms_err_pct_arm=round(100 * rms, 1), hand_rms_err_cm_at_target=round(100 * rms * alen, 1),
                           peak_hand_above_head_norm=round(peak_t, 2), peak_hand_above_head_norm_source=round(peak_s, 2))
    print("[M2] WAVE", label, wave_res[label])
results["wave"] = wave_res
results["meta"] = dict(frame="per-rig character frame (right/forward/up from rest pose); heights along character up-axis",
                       floors={k: round(v, 4) for k, v in floors.items()}, wave_hand_side=side, fps=FPS,
                       wolf_arm_len_m=round(wolf_al, 3), fen_arm_len_m=round(chain_len(fen, SPEC[fen.name]["armchain"][side]), 3),
                       orc_arm_len_m=round(chain_len(orc, SPEC[orc.name]["armchain"][side]), 3))
with open(os.path.join(OUT, "metrics.json"), "w") as fh: json.dump(results, fh, indent=1)
print("[M2] metrics.json rewritten. DONE")
