#!/usr/bin/env python3
"""PYN — body composition (AnthroForge, Nov 16, 2026).

Composes Pyn's BODY from the preset vector
(anthroforge-app/library/presets/pyn.afchar.json) on the hm08 base,
Sen stage-1 scope: unrigged static bake, NO fur, NO renders, NO head
build (the preset's head vector is recorded for later; the GLB keeps
the base head as placeholder geometry so the mesh is complete).

Pipeline (the proven bara-proof path, same as Sen):
  1. effective vector from the app core's own coupling evaluation
     (anthroforge-app core/build.py evaluate_character — raw preset
     values -> coupled effective values; geometry consumes effective)
  2. HIMBO vocabulary composed on the HIMBO base (pyn_machinery
     compose/hi_diff, extracted verbatim from build_bara.py)
  3. kernel transfer to hm08: (h,theta) torso kernel + (t,phi) limb
     segment kernels, region-weight blend (partition of unity)
  4. definition.flat_abs (hm08-native field) at its effective value
  5. slope limiter + surgical attenuation repair, judged on the FULL
     delta against BOTH bases (raw + macro), per the lineage
  6. shipped as a MakeHuman .target (0.1 mm quantisation); the delta
     is parsed BACK from the target file and the fold gate runs on
     those shipped numbers (house rule): 0 flips and min normalised
     face-normal dot >= 0.01 on both bases
  7. GLB export, uniformly scaled so crown-sole = 1.680 m
  8. graded with the bara rulers (characters/sen/scripts/
     bara_machinery.py, verbatim) + QA gauntlet

Three preset sliders have NO field on the Vanilla HIMBO base —
TorsoMassSmooth, BubbleButt, ButtTighten exist only in the SOS /
NeverNude OSD variants, whose base meshes are index-incompatible
(SOS base 11,007 verts vs Vanilla 9,346; shared blocks differ in
index sets). They are reported unapplied, never faked (the app
core's own rule). TorsoMassSmooth's coupling effect (tissue.level
0.4 -> flat_abs attenuation) IS included via the effective vector.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PYN = HERE.parent
V2 = PYN.parent.parent
FP = V2 / "first-proof"
WORK = PYN / "work"
TG = PYN / "targets"
APP = V2.parent / "anthroforge-app"
LEARNED = Path.home() / "workspace/character_assets/learned"
HIMBO_DIR = (Path.home() / "workspace/character_assets/_himbo_work/"
             "CalienteTools/BodySlide/ShapeData/HIMBO")
MPFB_ZIP = Path.home() / "workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip"

sys.path.insert(0, str(LEARNED / "tools"))
sys.path.insert(0, str(V2))
sys.path.insert(0, str(APP))

from osdparse import load_osd  # noqa: E402
from body_machinery.axes import torso_params  # noqa: E402
from body_machinery.labels import (  # noqa: E402
    blend_regions,
    label_mesh,
    region_weights_w3,
)
from body_machinery.loops import grade, mesh_volume  # noqa: E402
from body_machinery.osd import (  # noqa: E402
    BODY_END,
    SK_UNIT_M as SK,
    align_macro_base,
    compose_osd,
    extract_base_positions,
    load_mpfb_base_obj,
)
from body_machinery.repair import cos_fold_stats, repair  # noqa: E402
from body_machinery.transfer import limb_fields, torso_field  # noqa: E402
from core.build import Library, evaluate_character  # noqa: E402
from core.character import Character  # noqa: E402
from core.geometry import parse_target, write_glb, write_target  # noqa: E402

# ---------------------------------------------------------- mesh loads
corr = np.load(FP / "work/correspondence.npz")
mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
navel_mh = int(corr["navel_mh"])
mh_tris = corr["mh_tris"]
L_mh = mh_neck - mh_crotch
W_TORSO_V4 = np.load(FP / "work/belly_v4.npz")["torso_weight"].astype(np.float64)

mh_pos = load_mpfb_base_obj(MPFB_ZIP)
_mac = np.load(FP / "work/mh_macro_base.npz")["pos_canonical_m"]
mh_pos_mac = align_macro_base(mh_pos, _mac, BODY_END)
NB = len(mh_pos)
FACES_B = mh_tris[np.all(mh_tris < BODY_END, axis=1)]

hi_pos_u = extract_base_positions(
    (HIMBO_DIR / "HIMBO Body - Vanilla.nif").read_bytes(), 4000)
assert hi_pos_u is not None and len(hi_pos_u) == 9346, "HIMBO base extract"
hi_blocks = {b["name"]: b for b in
             load_osd(str(HIMBO_DIR / "HIMBO Body - Vanilla.osd"))["blocks"]}
NH = len(hi_pos_u)
_missed_blocks: set[str] = set()

h_hi, th_hi, r_hi, _ax_hi, cr_hi, nk_hi, L_hi = torso_params(hi_pos_u * SK)
s_hi = L_mh / L_hi
hi_lab = label_mesh(hi_pos_u * SK, cr_hi, nk_hi)
_mh_body_mask = np.zeros(NB, bool)
_mh_body_mask[:BODY_END] = True
mh_lab = label_mesh(mh_pos_mac, mh_crotch, mh_neck, _mh_body_mask)

# ---------------------------------------------------------- effective vector
preset = json.loads((APP / "library/presets/pyn.afchar.json").read_text())
lib = Library.load()
rep, eff = evaluate_character(Character.from_dict(preset), lib)
assert rep.ok, f"preset validation failed: {rep.errors}"
EFF = {k: float(v) for k, v in eff.sliders.items()}
RAW = {k: float(v) for k, v in preset["sliders"].items()}
print("effective vector (body):")
for k in sorted(EFF):
    if k.startswith("body."):
        mark = "" if abs(EFF[k] - RAW.get(k, 0.0)) < 1e-9 else \
            f"  (raw {RAW.get(k)}, coupled)"
        print(f"  {k:38s} {EFF[k]:.4f}{mark}")
print("derived tissue.level:", eff.derived.get("tissue.level"))

# ---------------------------------------------------------- HIMBO composition
NAME = {  # canonical slider id -> HIMBO compose() key (OSD block suffix)
    "body.himbo.weight_0_to_1": "Weight 0 to 1",
    "body.himbo.lean": "Lean",
    "body.muscle": "Muscle",
    "body.torso.mass": "TorsoMass",
    "body.himbo.torso_waist_size": "TorsoWaistSize",
    "body.himbo.torso_hip": "TorsoHip",
    "body.pecs.size": "PecsSize",
    "body.himbo.pecs_mass": "PecsMass",
    "body.himbo.pecs_width": "PecsWidth",
    "body.himbo.pecs_clavicle": "PecsClavicle",
    "body.himbo.arms_traps": "ArmsTraps",
    "body.himbo.arms_shoulders": "ArmsShoulders",
    "body.arms.delts": "ArmsDelts",
    "body.himbo.arms_biceps": "ArmsBiceps",
    "body.himbo.arms_fore": "ArmsFore",
    "body.himbo.legs_size": "LegsSize",
    "body.himbo.legs_thinner": "LegsThinner",
    "body.himbo.legs_thigh": "LegsThigh",
    "body.himbo.legs_calf_size": "LegsCalfSize",
    "body.himbo.butt_booty": "ButtBooty",
}
UNAPPLIED = {  # canonical id -> reason (no Vanilla-base field exists)
    "body.tissue.mass_smooth": "TorsoMassSmooth block exists only in "
        "SOS/NeverNude-variant OSDs (index-incompatible base meshes)",
    "body.himbo.bubble_butt": "BubbleButt block exists only in "
        "SOS/NeverNude-variant OSDs (index-incompatible base meshes)",
    "body.himbo.butt_tighten": "ButtTighten block exists only in "
        "SOS/NeverNude-variant OSDs (index-incompatible base meshes)",
}
for cid in UNAPPLIED:
    assert cid in EFF, cid
for key in NAME.values():
    assert f"HIMBO - Body{key}" in hi_blocks, f"missing OSD block {key}"
recipe = {NAME[cid]: EFF[cid] for cid in NAME}
print("\nHIMBO recipe (effective values):", recipe)
src = compose_osd(
    hi_blocks, NH, recipe, scale=SK, warn_missing=True, missed=_missed_blocks
)
mag = np.linalg.norm(src, axis=1)
print(f"HIMBO-space composed field: support {(mag > 0.02).sum()} verts, "
      f"max {mag.max() * SK * 100:.1f} cm")

# ---------------------------------------------------------- transfer to hm08
torso_f, (h_mh, r_mh) = torso_field(
    src,
    "pyn",
    hi_lab=hi_lab,
    h_hi=h_hi,
    th_hi=th_hi,
    r_hi=r_hi,
    mh_pos_mac=mh_pos_mac,
    mh_crotch=mh_crotch,
    mh_neck=mh_neck,
    s_hi=s_hi,
)
W3, _e = region_weights_w3(
    mh_pos_mac, mh_lab, h_mh, r_mh, W_TORSO_V4, mh_tris, body_end=BODY_END
)
limb_f = limb_fields(
    src,
    "pyn",
    hi_pos_m=hi_pos_u * SK,
    mh_pos_mac=mh_pos_mac,
    hi_lab=hi_lab,
    mh_lab=mh_lab,
)
D = blend_regions(torso_f, limb_f, W3)
mag = np.linalg.norm(D, axis=1)
print(f"transferred field on hm08: support {(mag > 0.0002).sum()}, "
      f"max {mag.max() * 100:.1f} cm")

# definition.flat_abs — hm08-native field at its effective value
fa = np.load(V2 / "bara-proof/work/definition_fields.npz")[
    "body_definition_flat_abs"]
D = D + EFF["body.definition.flat_abs"] * fa
print(f"flat_abs added at effective {EFF['body.definition.flat_abs']:.4f} "
      f"(raw {RAW['body.definition.flat_abs']})")

# ---------------------------------------------------------- repair (float)
ZERO = np.zeros((NB, 3))
D, att, traj = repair(
    D,
    [(mh_pos, ZERO), (mh_pos_mac, ZERO)],
    "pyn composed",
    faces=FACES_B,
    edges=_e,
    ref_pos=mh_pos,
)
print(f"repair: att min {att.min():.3f}, "
      f"{int((att < 0.999).sum())} verts attenuated, traj {traj}")

# ---------------------------------------------------------- ship + gate
NOTE = ("Provenance: Pyn body build (AnthroForge, Nov 16 2026) — preset "
        "pyn.afchar.json body vector at the app core's coupled effective "
        "values; HIMBO granular vocabulary composed on the HIMBO base, "
        "kernel-transferred to hm08 (bara-proof machinery verbatim), "
        "plus body.definition.flat_abs at its effective value. Three "
        "preset sliders unapplied (TorsoMassSmooth / BubbleButt / "
        "ButtTighten: SOS-variant OSD blocks only, index-incompatible "
        "base). Unrigged static bake; base head is placeholder "
        "geometry (no head build). Study-only, internal — not a CC0 "
        "MakeHuman asset. See PYN_BUILD.md.")
TARGET = TG / "body.pyn.target"


def gate(Dq):
    out = {}
    worst = 1.0
    for nm, base in (("raw", mh_pos), ("macro", mh_pos_mac)):
        cos, ok = cos_fold_stats(base, Dq, FACES_B)
        out[nm] = {"flips": int((cos[ok] <= 0).sum()),
                   "min_dot": float(np.nanmin(cos)),
                   "faces_below_0.01": int((cos[ok] < 0.01).sum())}
        worst = min(worst, out[nm]["min_dot"])
    out["pass"] = all(v["flips"] == 0 and v["min_dot"] >= 0.01
                      for v in out.values() if isinstance(v, dict))
    return out


write_target(TARGET, D, NOTE)
D_q = parse_target(TARGET, NB)
g = gate(D_q)
print("fold gate on shipped (quantised) delta:", json.dumps(g, indent=1))
q_rounds = 0
while not g["pass"] and q_rounds < 40:
    # quantised-space repair (hyper-lineage pattern): attenuate the
    # verts of every sub-margin face on either base, rewrite, re-gate
    badv = np.zeros(NB, bool)
    for base in (mh_pos, mh_pos_mac):
        cos, ok = cos_fold_stats(base, D_q, FACES_B)
        bad = np.zeros(len(cos), bool)
        bad[ok] = cos[ok] < 0.01
        badv[FACES_B[bad].ravel()] = True
    nbr = np.zeros(NB, bool)
    nbr[_e[badv[_e].any(axis=1)].ravel()] = True
    D[badv] *= 0.90
    D[nbr & ~badv] *= 0.97
    write_target(TARGET, D, NOTE)
    D_q = parse_target(TARGET, NB)
    g = gate(D_q)
    q_rounds += 1
    print(f" quantised repair round {q_rounds}: {g}")
assert g["pass"], "fold gate still failing after quantised repair rounds"

# ---------------------------------------------------------- export scale + GLB
composed = mh_pos_mac + D_q
h_base = float(composed[:, 2].max() - composed[:, 2].min())
S = 1.68 / h_base
pos_out = composed * S
h_out = float(pos_out[:, 2].max() - pos_out[:, 2].min())
print(f"composed height at base scale {h_base:.4f} m -> export scale "
      f"{S:.5f} -> GLB height {h_out:.4f} m")
GLB = PYN / "pyn_composed.glb"
write_glb(GLB, pos_out, mh_tris)
print("wrote", GLB)

# ---------------------------------------------------------- grade (bara rulers)
h_mh_raw = torso_params(mh_pos, mh_crotch, mh_neck, "mh")[0]
G = grade(
    mh_pos_mac + D_q,
    mh_lab,
    faces_b=FACES_B,
    mh_crotch=mh_crotch,
    mh_neck=mh_neck,
    mh_pos_mac=mh_pos_mac,
    navel_mh=navel_mh,
    h_mh=h_mh_raw,
    body_end=BODY_END,
)
G_base = grade(
    mh_pos_mac,
    mh_lab,
    faces_b=FACES_B,
    mh_crotch=mh_crotch,
    mh_neck=mh_neck,
    mh_pos_mac=mh_pos_mac,
    navel_mh=navel_mh,
    h_mh=h_mh_raw,
    body_end=BODY_END,
)
vol_export_L = float(mesh_volume(pos_out, FACES_B) * 1000.0)
print("grade (base scale):", json.dumps(G, indent=1, default=float))
print(f"export volume {vol_export_L:.1f} L")

# ---------------------------------------------------------- QA gauntlet
qa_dir = WORK / "qa-gauntlet"
proc = subprocess.run(
    [sys.executable, str(V2 / "qa-gauntlet/validate_glb.py"), str(GLB),
     "--out", str(qa_dir)], capture_output=True, text=True, timeout=600)
qa_files = sorted(qa_dir.glob("*.qa.json"))
gauntlet = json.loads(qa_files[0].read_text()) if qa_files else {
    "error": (proc.stderr or proc.stdout)[-500:], "blocked": True}
print("gauntlet status:", gauntlet.get("status"))

# ---------------------------------------------------------- persist
np.savez_compressed(WORK / "pyn_fields.npz",
                    himbo_src=src, delta_float=D, delta_shipped=D_q,
                    attenuation=att, export_scale=np.float64(S),
                    recipe=json.dumps(recipe))
qa = {
    "recipe_effective": recipe,
    "effective_vector": EFF, "raw_vector": RAW,
    "derived": {k: float(v) for k, v in eff.derived.items()},
    "unapplied": UNAPPLIED,
    "repair": {"att_min": float(att.min()),
               "att_verts": int((att < 0.999).sum()), "traj": traj},
    "fold_gate_shipped": g, "quantised_repair_rounds": q_rounds,
    "export_scale": S, "height_base_m": h_base, "height_glb_m": h_out,
    "grade_base_scale": G, "grade_base_only": G_base,
    "volume_export_L": vol_export_L,
    "mass_evidence": {
        "mass_at_rho_1.00_kg": vol_export_L,
        "implied_density_for_37.2kg": 37.2 / vol_export_L,
        "implied_density_for_65kg": 65.0 / vol_export_L,
        "implied_density_for_75kg": 75.0 / vol_export_L,
        "implied_density_for_85kg": 85.0 / vol_export_L},
    "gauntlet": gauntlet,
}
(WORK / "qa_pyn.json").write_text(json.dumps(qa, indent=1, default=float))
print("\nwrote work/qa_pyn.json + work/pyn_fields.npz + targets/body.pyn.target")
