# First proof: `body.belly.protrusion` — Fat Males → MakeHuman hm08

The §8 first proof from `MAKEHUMAN_OMNIVERSAL.md`: carry one slider across
systems. The Fat Males belly morph (learned as an exact-topology delta against
the Skyrim male base) was transferred onto the MakeHuman hm08 base and shipped
as a native `.target` file plus a canonical slider record.

**Verdict: 3 of 4 pass criteria met.** The residual criterion fails as a
single headline number, for a measured structural reason documented below —
the transfer's bulk fidelity is near-exact (median residual 0.04 cm), and the
breach is concentrated exactly where two of the criteria conflict.

## Pass criteria (§8) — results

| # | Criterion | Result | Numbers |
|---|-----------|--------|---------|
| 1 | Navel-landmark forward displacement at +1 within 5 mm of the canonical anchor | **PASS** | Anchor 11.97 cm; measured in Blender **12.06 cm → error 0.9 mm**. Numpy raw-frame measurement 11.90 cm (error 0.7 mm). Response is linear: −12.06 / 0 / +6.03 / +12.06 cm at −1 / 0 / +0.5 / +1 |
| 2 | Zero belly fold-overs at +1 (else ship `safe_max` ≥ 0.7) | **PASS** | **0 flips** over 1,092 belly faces at +1 — on the raw base.obj geometry (min normal-dot 0.055), on the MPFB default-macro evaluated base (0.089), and cross-checked inside Blender on the evaluated mesh (0 flips, min_dot 0.087). `safe_max = 1.0` |
| 3 | Residual p95 ≤ 0.3 cm over the belly mask | **FAIL** (see analysis) | Forward (result→source surface) p50 **0.039 cm**, **p95 1.394 cm**, max 4.28 cm. Backward (coverage-matched) p95 2.53 cm at 94% coverage |
| 4 | `.target` loads in stock MakeHuman/MPFB2 with no code changes | **PASS** | Loaded via stock `TargetService.load_target`; weight-0 evaluated state is bit-identical to the pre-load human (max diff 0.0) |

## Why criterion 3 fails — and what the numbers actually say

The unpinned registration by itself reaches **p95 0.130 cm** forward residual
(criterion-grade) — but its navel displacement is only ≈8–9.5 cm, not the
11.97 cm anchor, and it folds at the under-belly creases. The gap is not a
fitting error; it is anatomical:

- The two bases have **different neutral bellies**. At the navel band, hm08's
  neutral front radius is 9.23 cm; the Skyrim lean base's, scaled by the
  torso-length ratio, is 7.31 cm — a **~1.9 cm neutral-radius gap**. A
  displacement anchor ("navel moves X forward of *its own* neutral") and a
  surface anchor ("navel sits *on the studied fat surface*") therefore
  differ by that gap at the landmark, by construction. Satisfying criterion 1
  requires a local pin (3.75 cm radial correction at the landmark, Gaussian
  σ_u 0.035 / σ_v 0.045 in torso-param units); the pin patch (~29 of 391 core
  verts, errors 0.7–4.3 cm) is what pushes p95 over 0.3 cm.
- The remaining tail is the **flank band** (~27 verts, 0.6–2.4 cm) — the same
  dead zone the HIMBO→Fat Males fit POC named — plus under-belly crease
  spots touched by fold repair.
- Outside those zones the field is essentially exact: **p50 0.039 cm**, and
  83% of mask-core verts sit within 0.3 cm of the source surface.
- Context bound: a kernel-field model of the source delta, cross-validated
  on the source's own verts, has p95 2.03 cm inside the belly mask — the
  sculpted delta carries genuine crease-scale features (adjacent-vertex
  delta steps: median 0.80 cm, p95 3.66 cm), so vert-level *field*
  reproduction cannot reach 0.3 cm either; 0.3 cm is only reachable as a
  *surface* distance, which is how it is reported here.

**Recommendation for the canonical QA schema:** report residuals split by
zone (core / landmark-pin patch / named dead zones) instead of one p95 over
the whole mask — a single number hides exactly the trade-off a proof is
supposed to expose. This record's JSON carries the split qualitatively in
`qa.residual_note`.

## Method (as shipped)

1. **Frames.** Skyrim canonical (X right, Y forward, Z up), 1 unit =
   0.01428 m. hm08 from MPFB2's `base.obj`: canonical (x, z_obj, y_obj) ×
   0.1 m. The .target write/read chain was verified empirically end-to-end
   with MPFB's bundled `stomach-tone-incr` target before trusting our file:
   file line (a, b, c) → Blender offset (a, −c, b) × 0.1 m, exact match.
2. **Correspondence.** Torso-param space (arc/L, h, r/L) with per-mesh
   torso length L (crotch → neck base, operationally defined from gated
   width profiles; Skyrim L = 0.7534 m, hm08 L = 0.6272 m, **s = 0.8325**).
   Kernel-field init (σ_h 0.05, σ_arc 0.04 m), then 60 iterations of
   non-rigid registration onto the source fat surface (closest-point on
   triangles, normal-gated smoothing in-loop) — the fit POC's machinery.
3. **Mask.** Canonical rule: geodesic falloff from the navel landmark,
   r = 0.35 × torso length (full weight inside 0.65r). 535 hm08 verts moved.
4. **Anchor pin.** Navel landmark = front-centre vertex at the
   forward-displacement profile peak (source vert 741, Δ 14.38 cm → scaled
   anchor **0.1197 m**; hm08 vert 4075). Tight Gaussian pin in (u, v) along
   the local radial direction; no global gain (a global trim was tested and
   rejected — it taxes every vertex for a landmark-local deficit).
5. **Fold control.** Targeted repair only: graph-Laplacian smoothing
   (λ 0.5) applied to verts of near-degenerate faces + 1-ring, iterated
   until clean on **both** bases (raw base.obj and the MPFB default-macro
   evaluated base — the first Blender check caught 14 flips that the raw
   base alone did not predict; dual-base repair fixed them with margin).

## Renders (MPFB2 default-macro human, Workbench, profile)

| Weight | Render |
|--------|--------|
| −1 | [belly_w-1.0_profile.png](renders/belly_w-1.0_profile.png) |
| 0 | [belly_w+0.0_profile.png](renders/belly_w+0.0_profile.png) |
| +0.5 | [belly_w+0.5_profile.png](renders/belly_w+0.5_profile.png) |
| +1 | [belly_w+1.0_profile.png](renders/belly_w+1.0_profile.png) |
| +1 front | [belly_w+1.0_front.png](renders/belly_w+1.0_front.png) |

## Honest caveats

- **Negative pole.** At −1 the reversed field folds (~140/1,092 belly
  faces). The source morph is one-sided; MakeHuman convention is a separate
  decrease target. The canonical range keeps min −1 (slider semantics), but
  this instance's negative half is not production-safe.
- **Landmark definitions are operational**, not anatomical landmarks
  (width-profile neck base, lowest-midline crotch). s uncertainty ≈ ±0.07;
  the pin absorbs this at the landmark, but off-landmark displacements
  inherit the scale uncertainty.
- **MPFB quirks found:** the depsgraph-evaluated mesh strips helper
  geometry (13,380 body verts; body indices preserved — belly work is
  unaffected); shape keys load with slider range [0, 1], so negative
  weights need `slider_min` extended (test harness does this; no code
  changes anywhere).
- **Provenance:** the instance is derived from study-only learned data.
  It is internal-only, is labelled as such in the .target header and the
  slider record, and must never be shipped or mistaken for a CC0
  MakeHuman asset.

## Files

- `body.belly.protrusion.target` — the hm08 instance (535 moved verts)
- `body.belly.protrusion.slider.json` — canonical slider record with QA
- `scripts/build_target.py` — correspondence + transfer + QA (numpy)
- `scripts/probe_mpfb.py` — frame/scale chain verification vs a bundled target
- `scripts/dump_macro_base.py` — default-macro evaluated base dump
- `scripts/test_mpfb.py` — Blender acceptance test + renders
- `work/qa_numbers.json`, `work/blender_test.json`, `work/correspondence.npz`,
  `work/mh_macro_base.npz` — raw QA data
