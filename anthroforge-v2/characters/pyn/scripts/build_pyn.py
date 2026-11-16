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
WORK = PYN / "work"
TG = PYN / "targets"
APP = Path.home() / "workspace/anthroforge-app"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(APP))
sys.path.insert(0, str(V2 / "characters/sen/scripts"))

import pyn_machinery as M          # noqa: E402  (executes build_bara loads)
import bara_machinery as BM        # noqa: E402  (Sen's verbatim rulers)
from core.build import Library, evaluate_character   # noqa: E402
from core.character import Character                 # noqa: E402
from core.geometry import write_glb                  # noqa: E402

DM_M = 0.1

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
    assert f"HIMBO - Body{key}" in M.hi_blocks, f"missing OSD block {key}"
recipe = {NAME[cid]: EFF[cid] for cid in NAME}
print("\nHIMBO recipe (effective values):", recipe)
src = M.compose(recipe)
mag = np.linalg.norm(src, axis=1)
print(f"HIMBO-space composed field: support {(mag > 0.02).sum()} verts, "
      f"max {mag.max() * M.SK * 100:.1f} cm")

# ---------------------------------------------------------- transfer to hm08
torso_f, (h_mh, r_mh) = M.torso_field(src, "pyn")
M.h_mh, M.r_mh = h_mh, r_mh
exec((HERE / "w3_block.txt").read_text(), M.__dict__)   # region weights W3
limb_f = M.limb_fields(src, "pyn")
D = M.blend(torso_f, limb_f)
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
ZERO = np.zeros((M.NB, 3))
D, att, traj = M.repair(D, [(M.mh_pos, ZERO), (M.mh_pos_mac, ZERO)],
                        "pyn composed")
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


def parse_target(path):
    """MPFB .target -> canonical delta (metres), grade_sen convention."""
    Dq = np.zeros((M.NB, 3))
    for line in Path(path).read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        p = line.split()
        Dq[int(p[0])] = [float(p[1]), float(p[3]), float(p[2])]
    return Dq * DM_M


def fold_stats(pos, Dq):
    F = M.FACES_B
    n0 = np.cross(pos[F[:, 1]] - pos[F[:, 0]], pos[F[:, 2]] - pos[F[:, 0]])
    pp = pos + Dq
    n1 = np.cross(pp[F[:, 1]] - pp[F[:, 0]], pp[F[:, 2]] - pp[F[:, 0]])
    l0 = np.linalg.norm(n0, axis=1)
    l1 = np.linalg.norm(n1, axis=1)
    ok = (l0 > 1e-12) & (l1 > 1e-12)
    cos = np.full(len(F), np.nan)
    cos[ok] = np.einsum("ij,ij->i", n0[ok], n1[ok]) / (l0[ok] * l1[ok])
    return cos, ok


def gate(Dq):
    out = {}
    worst = 1.0
    for nm, base in (("raw", M.mh_pos), ("macro", M.mh_pos_mac)):
        cos, ok = fold_stats(base, Dq)
        out[nm] = {"flips": int((cos[ok] <= 0).sum()),
                   "min_dot": float(np.nanmin(cos)),
                   "faces_below_0.01": int((cos[ok] < 0.01).sum())}
        worst = min(worst, out[nm]["min_dot"])
    out["pass"] = all(v["flips"] == 0 and v["min_dot"] >= 0.01
                      for v in out.values() if isinstance(v, dict))
    return out


M.write_target(TARGET, D, NOTE)
D_q = parse_target(TARGET)
g = gate(D_q)
print("fold gate on shipped (quantised) delta:", json.dumps(g, indent=1))
q_rounds = 0
while not g["pass"] and q_rounds < 40:
    # quantised-space repair (hyper-lineage pattern): attenuate the
    # verts of every sub-margin face on either base, rewrite, re-gate
    badv = np.zeros(M.NB, bool)
    for base in (M.mh_pos, M.mh_pos_mac):
        cos, ok = fold_stats(base, D_q)
        bad = np.zeros(len(cos), bool)
        bad[ok] = cos[ok] < 0.01
        badv[M.FACES_B[bad].ravel()] = True
    nbr = np.zeros(M.NB, bool)
    nbr[M._e[badv[M._e].any(axis=1)].ravel()] = True
    D[badv] *= 0.90
    D[nbr & ~badv] *= 0.97
    M.write_target(TARGET, D, NOTE)
    D_q = parse_target(TARGET)
    g = gate(D_q)
    q_rounds += 1
    print(f" quantised repair round {q_rounds}: {g}")
assert g["pass"], "fold gate still failing after quantised repair rounds"

# ---------------------------------------------------------- export scale + GLB
composed = M.mh_pos_mac + D_q
h_base = float(composed[:, 2].max() - composed[:, 2].min())
S = 1.68 / h_base
pos_out = composed * S
h_out = float(pos_out[:, 2].max() - pos_out[:, 2].min())
print(f"composed height at base scale {h_base:.4f} m -> export scale "
      f"{S:.5f} -> GLB height {h_out:.4f} m")
GLB = PYN / "pyn_composed.glb"
write_glb(GLB, pos_out, M.mh_tris)
print("wrote", GLB)

# ---------------------------------------------------------- grade (bara rulers)
BM.FACES_B = M.FACES_B
BM.BODY_END = M.BODY_END
BM.mh_neck, BM.mh_crotch, BM.L_mh = M.mh_neck, M.mh_crotch, M.L_mh
BM.mh_pos_mac = M.mh_pos_mac
BM.navel_mh = M.navel_mh
BM.h_mh = BM.torso_params(M.mh_pos, M.mh_crotch, M.mh_neck, "mh")[0]
G = BM.grade(M.mh_pos_mac + D_q, M.mh_lab)
G_base = BM.grade(M.mh_pos_mac, M.mh_lab)
vol_export_L = float(BM.mesh_volume(pos_out) * 1000.0)
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
