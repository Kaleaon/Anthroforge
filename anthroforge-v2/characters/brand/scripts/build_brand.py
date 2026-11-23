#!/usr/bin/env python3
"""BRAND — body composition + grading + GLB export.

PRIMARY ROUTE: anthroforge-app core/build.py — the authored preset
plus the build-recipe sliders, composed from the hm08 instance packs
on the app base (the base the packs were verified against: the app
suite asserts every instance folds 0 faces at full value, and the
Sen preset build folds 0).

    recipe = preset sliders
           + body.build.muscle 1.0 + body.build.chest_width 1.0
           + s * body.build.tissue_strongman
           + 0.30 * body.belly.protrusion

The preset's own neck.mass / forearm.mass / definition sliders ride
along and are applied at their COUPLING-EFFECTIVE values by
build_character itself (definition attenuation + neck show-through,
MUSCLE_TISSUE_MODEL §8). Grading uses the bara machinery rulers
(characters/sen/scripts/bara_machinery.py) on the composed positions
— vertex indexing is identical across the bases (same triangles,
navel 4075), so the labels transfer.

Tissue scan (pre-registered): s in {0.35, 0.45, 0.55, 0.65}; ship the
LARGEST s with flips_body == 0, min_body_dot >= 0.01 and M4
(chest/waist girth) >= 1.30 — Brand's wedge gate. If no s qualifies,
ship the smallest s and report the miss. Belly 0.30 fixed [E]:
a slight working gut, not Sen's terminal belly.

Fold gate on the SHIPPED numbers: build_character's GLB positions
are float32; flips + min dot are recomputed on the exact float32
positions written. Gate: 0 flips AND min dot >= 0.01.

CROSS-CHECK: the same recipe composed from the shipped .target
files on the bara machinery macro base (Sen's route). Reported
honestly, including its folds: the post-neck-fix muscle target
folds one throat face (23379) on the macro base even alone —
a pre-existing field/base interaction, not Brand's vector — and
neck.mass over it folds more. The app base is clean; that is why
the app route ships.

Outputs: brand_body.glb (base scale, unrigged static bake; export
scale lives in the preset record), work/qa_brand_body.json,
work/brand_body_delta.npz (delta on the APP base).
"""
import json
import sys
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BRAND = HERE.parent
V2 = BRAND.parent.parent
APP = Path.home() / "workspace/anthroforge-app"
sys.path.insert(0, str(APP))
sys.path.insert(0, str(V2 / "characters" / "sen" / "scripts"))
import bara_machinery as BM  # noqa: E402

from core.build import (Library, build_character, evaluate_character,  # noqa: E402
                        WORKSPACE_ROOT)
from core.character import Character             # noqa: E402
from core import geometry                        # noqa: E402

TARGET_HEIGHT_M = 1.83
DRAFT_MASS_KG = 140.0
BELLY_W = 0.30
SCAN_S = (0.35, 0.45, 0.55, 0.65)
BODY_END = 13380

lib = Library.load(APP / "library")
preset = Character.load(APP / "library" / "presets" / "brand.afchar.json")
app_base = lib.bases.load("makehuman_hm08")

report, effective = evaluate_character(preset, lib)
assert report.ok, report.errors
DER = effective.derived
print("coupling evaluation of the authored vector:")
print(f"  tissue.level derived      : {DER.get('tissue.level'):.3f}")
for sid in ("body.neck.mass", "body.forearm.mass",
            "body.definition.back", "body.definition.traps_valleys",
            "body.definition.pecs_crease"):
    print(f"  {sid:28s}: raw {preset.sliders[sid]:.2f} -> "
          f"effective {effective.sliders.get(sid, 0.0):.3f}")

# ------------------------------------------------- machinery labellers
# (labels/landmarks by vertex index — identical indexing on hm08)
FP = V2 / "first-proof"
corr = np.load(FP / "work/correspondence.npz")
mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
navel_mh = int(corr["navel_mh"])
mh_tris = corr["mh_tris"].astype(np.int64)
with zipfile.ZipFile(Path.home() / "workspace/stick-figure-avatar"
                     "/photoreal/tools/mpfb2.zip") as z:
    _lines = z.read("mpfb/data/3dobjs/base.obj").decode().splitlines()
_obj = np.array([[float(x) for x in l.split()[1:4]]
                 for l in _lines if l.startswith("v ")])
mh_pos = np.stack([_obj[:, 0], _obj[:, 2], _obj[:, 1]], axis=1) * 0.1
_mac = np.load(FP / "work/mh_macro_base.npz")["pos_canonical_m"]
mh_pos_mac = mh_pos.copy()
_mb = _mac.copy()
for _ax in range(3):
    r0, r1 = mh_pos[:BODY_END, _ax].min(), mh_pos[:BODY_END, _ax].max()
    m0, m1 = _mb[:, _ax].min(), _mb[:, _ax].max()
    _mb[:, _ax] = r0 + (_mb[:, _ax] - m0) * (r1 - r0) / (m1 - m0)
mh_pos_mac[:len(_mb)] = _mb
NB = len(mh_pos)
FACES_B = mh_tris[np.all(mh_tris < BODY_END, axis=1)]
BM.FACES_B = FACES_B
BM.BODY_END = BODY_END
BM.mh_neck, BM.mh_crotch, BM.L_mh = mh_neck, mh_crotch, mh_neck - mh_crotch
BM.mh_pos_mac = mh_pos_mac
BM.navel_mh = navel_mh
BM.h_mh = BM.torso_params(mh_pos, mh_crotch, mh_neck, "mh")[0]
_mh_body_mask = np.zeros(NB, bool)
_mh_body_mask[:BODY_END] = True
mh_lab = BM.label_mesh(mh_pos_mac, mh_crotch, mh_neck, _mh_body_mask)


def recipe_character(s, neck_raw=None):
    sliders = dict(preset.sliders)
    if neck_raw is not None:
        sliders["body.neck.mass"] = neck_raw
    sliders.update({"body.build.muscle": 1.0,
                    "body.build.chest_width": 1.0,
                    "body.build.tissue_strongman": s,
                    "body.belly.protrusion": BELLY_W})
    return Character(name="Brand (build recipe)", sliders=sliders)


def fold_stats(pos):
    fl = geometry.count_flips(app_base.positions, pos,
                              app_base.triangles,
                              app_base.body_face_mask)
    dots = np.einsum("ij,ij->i",
                     geometry.face_normals(app_base.positions,
                                           app_base.triangles),
                     geometry.face_normals(pos, app_base.triangles))
    return fl, float(dots[app_base.body_face_mask].min())


def composed_positions(char):
    """app base + instance deltas at the character's coupling-
    effective values, over build_character's applied set."""
    _, eff = evaluate_character(char, lib)
    pos = app_base.positions.copy()
    applied = []
    for sid in sorted(eff.sliders):
        val = eff.sliders[sid]
        if abs(val) < 1e-12:
            continue
        rec = lib.sliders.find(sid)
        spec = (rec.instances or {}).get(app_base.id) if rec else None
        if spec is None:
            continue
        fld = geometry.load_instance(sid, spec, app_base.id,
                                     app_base.n_verts, WORKSPACE_ROOT)
        pos = pos + fld.at(float(val))
        applied.append(sid)
    return pos, applied, eff


# ------------------------------------------- neck cap scan (corrective)
# The vector's neck intent (raw 0.90, effective 0.930) folds 3 throat
# faces over the full muscle system. Pre-registered corrective: ship
# the LARGEST raw neck value with 0 flips and min-dot >= 0.01 at the
# mid-scan tissue load; the record keeps the intent (see preset
# build_recipe.neck_cap + BRAND_BUILD.md).
print("\n== neck cap scan at s=0.45 (corrective for the fold gate) ==")
cap_scan = []
neck_raw_ship = None
for raw in (0.90, 0.75, 0.60, 0.45, 0.40, 0.35, 0.30, 0.25, 0.20):
    pos_p, _, eff_p = composed_positions(recipe_character(0.45, raw))
    fl_p, md_p = fold_stats(pos_p)
    ok = fl_p == 0 and md_p >= 0.01
    cap_scan.append({"raw": raw,
                     "effective": float(eff_p.sliders["body.neck.mass"]),
                     "flips": fl_p, "min_dot": md_p, "passes": ok})
    print(f"  raw {raw:.2f} (eff {eff_p.sliders['body.neck.mass']:.3f}): "
          f"flips {fl_p}  min-dot {md_p:.4f}  passes={ok}")
    if ok and neck_raw_ship is None:
        neck_raw_ship = raw
assert neck_raw_ship is not None, "no neck cap in the grid passes"
print(f"neck cap shipped: raw {neck_raw_ship} "
      f"(intent 0.90 — build-layer corrective)")


# ------------------------------------------------------------------ scan
print("\n== tissue scan via core/build.py "
      "(gate: flips==0, min-dot>=0.01, M4>=1.30) ==")
scan = []
tmp_glb = BRAND / "work" / "_scan.glb"
for s in SCAN_S:
    char = recipe_character(s, neck_raw_ship)
    rep = build_character(char, lib, out_path=tmp_glb, run_qa=False)
    pos, _, _ = composed_positions(char)
    G = BM.grade(pos, mh_lab)
    row = {"s": s, "flips_body": rep.flips_body,
           "min_body_dot": rep.min_body_dot,
           "M4": G["M4_chest_waist"], "M5": G["M5_depth_ratio"],
           "M6": G["M6_trap_deg"], "chest_g": G["chest_g"],
           "waist_g": G["waist_g"], "fa_g": G["fa_g"],
           "volume_L": G["volume_L"],
           "passes": (rep.flips_body == 0 and rep.min_body_dot >= 0.01
                      and G["M4_chest_waist"] >= 1.30)}
    scan.append(row)
    print(f" s={s:.2f}: flips {row['flips_body']}  min-dot "
          f"{row['min_body_dot']:.4f}  M4 {row['M4']:.3f}  M5 "
          f"{row['M5']:.3f}  M6 {row['M6']:.1f}  chest "
          f"{row['chest_g']*100:.1f} cm  waist {row['waist_g']*100:.1f} "
          f"cm  fa {row['fa_g']*100:.1f} cm  passes={row['passes']}")
tmp_glb.unlink(missing_ok=True)

passing = [r for r in scan if r["passes"]]
if passing:
    ship_s = passing[-1]["s"]
    rule = (f"largest s passing all gates (0 flips, min-dot >= 0.01, "
            f"M4 >= 1.30): s={ship_s}")
else:
    ship_s = SCAN_S[0]
    rule = ("NO s passes all gates; shipping the smallest "
            f"s={ship_s} and reporting the miss")
print("corrective:", rule)

# ------------------------------------------------------------- final build
glb_path = BRAND / "brand_body.glb"
char = recipe_character(ship_s, neck_raw_ship)
rep = build_character(char, lib, out_path=glb_path)
pos, applied, eff = composed_positions(char)
G_brand = BM.grade(pos, mh_lab)
G_base = BM.grade(app_base.positions, mh_lab)

pos_muscle = app_base.positions.copy()
for sid in ("body.build.muscle", "body.build.chest_width"):
    spec = lib.sliders.find(sid).instances[app_base.id]
    fld = geometry.load_instance(sid, spec, app_base.id,
                                 app_base.n_verts, WORKSPACE_ROOT)
    pos_muscle = pos_muscle + fld.at(1.0)
G_musc = BM.grade(pos_muscle, mh_lab)

# shipped-numbers fold gate: the float32 positions in the GLB
pos32 = pos.astype(np.float32).astype(np.float64)
fl32 = geometry.count_flips(app_base.positions, pos32,
                            app_base.triangles, app_base.body_face_mask)
_dots = np.einsum("ij,ij->i",
                  geometry.face_normals(app_base.positions,
                                        app_base.triangles),
                  geometry.face_normals(pos32, app_base.triangles))
md32 = float(_dots[app_base.body_face_mask].min())
_body_idx = np.where(app_base.body_face_mask)[0]
_limit_face = int(_body_idx[int(np.argmin(_dots[app_base.body_face_mask]))])
_limit_cent = pos32[app_base.triangles[_limit_face]].mean(0)
print(f"limiting face {_limit_face} at centroid "
      f"{np.round(_limit_cent, 3).tolist()} (min-dot {md32:.4f})")
print(f"\nshipped gate: flips {fl32}  min-dot {md32:.4f}  "
      f"(gate: 0 flips, >= 0.01)  build_character: flips "
      f"{rep.flips_body} min-dot {rep.min_body_dot:.4f}")
print(f"GLB QA gauntlet: {rep.qa}")

export_scale = TARGET_HEIGHT_M / G_brand["height_m"]
vol_export_L = G_brand["volume_L"] * export_scale ** 3
implied_mass = vol_export_L * 1.0
print(f"Brand: height {G_brand['height_m']:.3f} m base scale, "
      f"volume {G_brand['volume_L']:.1f} L; export scale "
      f"{export_scale:.4f} -> {TARGET_HEIGHT_M:.2f} m, "
      f"{vol_export_L:.1f} L; mass @ density 1.0 = {implied_mass:.1f} "
      f"kg; 140 kg draft implies density "
      f"{DRAFT_MASS_KG / vol_export_L:.3f}")

# ------------------------------------------------- machinery cross-check
TG = BRAND / "targets"


def parse_target(path):
    D = np.zeros((NB, 3))
    for line in Path(path).read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        p = line.split()
        i = int(p[0])
        D[i] = [float(p[1]), float(p[3]), float(p[2])]
    return D * 0.1


D_mach = (parse_target(TG / "body.muscle.target")
          + parse_target(TG / "body.chest.width.target")
          + ship_s * parse_target(TG / "body.tissue.strongman.target")
          + BELLY_W * parse_target(
              TG / "body.belly.protrusion_terminal_v51.target")
          + float(eff.sliders["body.forearm.mass"])
          * parse_target(TG / "body.forearm.mass.target")
          + float(eff.sliders["body.neck.mass"])
          * parse_target(TG / "body.neck.mass.target")
          + float(eff.sliders["body.definition.back"])
          * parse_target(TG / "body.definition.back.target")
          + float(eff.sliders["body.definition.traps_valleys"])
          * parse_target(TG / "body.definition.traps_valleys.target")
          + float(eff.sliders["body.definition.pecs_crease"])
          * parse_target(TG / "body.definition.pecs_crease.target"))
G_mach = BM.grade(mh_pos_mac + D_mach, mh_lab)
fl_mach = {"raw": int(BM.flipped(mh_pos, D_mach).sum()),
           "macro": int(BM.flipped(mh_pos_mac, D_mach).sum())}
print(f"machinery cross-check: chest {G_mach['chest_g']*100:.1f} cm  "
      f"waist {G_mach['waist_g']*100:.1f} cm  volume "
      f"{G_mach['volume_L']:.1f} L  flips {fl_mach} (macro-base "
      "throat folds — see BRAND_BUILD.md debits)")

qa = {
    "composition": {
        "route": "anthroforge-app core/build.py (instance packs on "
                 "the app hm08 base); graded with bara_machinery",
        "formula": "preset sliders (neck/forearm/definition at "
                   "coupling-effective values) + muscle 1.0 "
                   "+ chest_width 1.0 + s*tissue_strongman "
                   "+ 0.30*belly.protrusion",
        "tissue_scale_shipped": ship_s,
        "corrective_rule": rule,
        "scan": scan,
        "neck_cap": {"intent_raw": 0.90, "shipped_raw": neck_raw_ship,
                     "scan": cap_scan,
                     "reason": "neck field at intent folds 3 throat "
                               "faces over the full muscle system; "
                               "largest fold-safe raw value shipped "
                               "(build-layer corrective, record keeps "
                               "the intent)"},
        "applied_sliders": rep.applied,
        "unapplied_count": len(rep.unapplied),
        "coupling_derived": {k: DER[k] for k in sorted(DER)},
        "effective_weights": {
            "neck_mass": float(eff.sliders["body.neck.mass"]),
            "forearm_mass": float(eff.sliders["body.forearm.mass"]),
            "definition": {sid: float(eff.sliders[sid]) for sid in
                           ("body.definition.back",
                            "body.definition.traps_valleys",
                            "body.definition.pecs_crease")}},
    },
    "export": {"target_height_m": TARGET_HEIGHT_M,
               "composed_height_m": G_brand["height_m"],
               "export_scale": export_scale,
               "volume_L_base_scale": G_brand["volume_L"],
               "volume_L_at_export": vol_export_L,
               "mass_kg_at_density_1": implied_mass,
               "draft_mass_kg": DRAFT_MASS_KG,
               "draft_implied_density": DRAFT_MASS_KG / vol_export_L},
    "fold_gate_shipped": {"flips_float32_shipped": int(fl32),
                          "min_dot_float32_shipped": float(md32),
                          "limiting_face": _limit_face,
                          "limiting_face_centroid": _limit_cent.tolist(),
                          "build_character_flips": rep.flips_body,
                          "build_character_min_dot": rep.min_body_dot,
                          "body_faces": int(app_base.body_face_mask.sum()),
                          "gate": "0 flips and min_dot >= 0.01",
                          "passes": bool(fl32 == 0 and md32 >= 0.01)},
    "glb_qa": rep.qa,
    "scorecard": {
        "base": {k: G_base[k] for k in
                 ("neck_w", "head_w", "chest_g", "waist_g", "volume_L",
                  "height_m")},
        "muscle_width": {k: G_musc[k] for k in
                         ("M1_neckW_headW", "M4_chest_waist",
                          "M5_depth_ratio", "M6_trap_deg", "neck_w",
                          "chest_g", "waist_g", "volume_L")},
        "brand": {k: G_brand[k] for k in
                  ("M1_neckW_headW", "M2_neck_arm", "M2_neck_calf",
                   "M3_fa_arm", "M4_chest_waist", "M5_depth_ratio",
                   "M6_trap_deg", "M7_vis_neck_ratio", "M8_span_headW",
                   "M11_thigh_waist", "M12_heads_tall", "neck_w",
                   "neck_g", "head_w", "head_h", "chest_g", "chest_w",
                   "waist_g", "waist_w", "chest_d", "waist_d",
                   "delt_span", "ua_g", "fa_g", "thigh_g", "calf_g",
                   "volume_L", "height_m", "visible_neck")},
    },
    "machinery_crosscheck": {
        "grade": {k: G_mach[k] for k in
                  ("chest_g", "waist_g", "neck_g", "fa_g", "thigh_g",
                   "calf_g", "volume_L", "height_m", "M4_chest_waist",
                   "M5_depth_ratio", "M6_trap_deg")},
        "flips": fl_mach,
        "note": "composed at the SHIPPED weights (neck capped). "
                "The post-neck-fix muscle target folds throat face "
                "23379 on the macro base even alone (0 on the raw "
                "base) — the 1 macro flip here is that pre-existing "
                "field/base interaction, not Brand's vector; at the "
                "uncapped neck intent the same composition folds "
                "4 macro / 2 raw. App base: 0 flips. Girths differ "
                "from the app route because the machinery macro base "
                "is a smaller-framed extraction of hm08 (base volume "
                "51.2 L vs the app base's 54.9 L). Cross-check only "
                "— the app route ships."},
}
(BRAND / "work" / "qa_brand_body.json").write_text(json.dumps(qa, indent=1))
np.savez(BRAND / "work" / "brand_body_delta.npz",
         delta_brand_on_app_base_m=pos - app_base.positions,
         tissue_scale=ship_s)
print("\nwrote work/qa_brand_body.json + work/brand_body_delta.npz "
      f"+ {glb_path.name}")
