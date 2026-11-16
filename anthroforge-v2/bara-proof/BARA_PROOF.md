# BARA PROOF — strongman-pole bara build on hm08

**Task:** Joe, Nov 12, 2026 — "look up further lessons for bara… and apply
it." Build the strongman-pole bara build from `../BARA_LESSONS.md` on the
MakeHuman hm08 base as a two-vector slider pair (`body.muscle` ×
`body.tissue.strongman`), belly reusing the accepted v4 system, graded
against the study's 12-metric scorecard.

**Mid-build additions from Joe (same day):** (1) chest *broadness* is its
own editable component — shipped as a third slider `body.chest.width`
and measured as M13; (2) fat must *wrap front-to-sides* — the tissue
layer's angular profile is QA'd front/flank/back (side-mass check,
§5).

**Verdict:** the build lands the pole's defining relations — chest ring
out-rings the waist ring (M4 **1.301** vs Shaw anchor 1.28), the yoke is
the first thing you see (M1, M6, M7, M8 pass), thighs carry the lower
half (M11), and it is fold-free everywhere. It misses where the source
vocabulary runs out: neck *girth* (M2) and forearm (M3) can't reach the
Reeves/Hall relations at any legal recipe values, chest *depth* (M5)
loses to the power belly at the navel station, and the head is
untouched (M12). **0 flipped faces at +1** in numpy on both bases and
on the evaluated Blender mesh. All numbers below are measured, not
tuned-to.

---

## 1. What ships

| file | what |
|---|---|
| `body.muscle.target` + `.slider.json` | muscle vector, core (10,482 moved verts) |
| `body.chest.width.target` + `.slider.json` | broadness component (5,816 moved verts) |
| `body.tissue.strongman.target` + `.slider.json` | tissue vector, strongman cell (8,331 moved verts) |
| `body.bara.strongman.target` | combined +1/+1/+1 convenience target (verified = sum of the three keys on the evaluated mesh, max deviation 0.020 cm — the sparse-write threshold) |
| `scripts/build_bara.py` | the whole pipeline, runnable end to end |
| `scripts/test_bara.py` | Blender verification + renders |
| `work/qa_numbers_bara.json`, `work/bara_fields.npz`, `work/blender_bara_numbers.json` | full QA record |
| `renders/` | combined front / profile / three-quarter, muscle-system profile, base profile, base-vs-build profile composite |

## 2. Composition

**Muscle core** (`body.muscle`) — BARA_LESSONS §6C shared MuscleVector ×
the §4.2 Sen preset, doctrine order (frame → yoke → torso → arms →
legs): BodyMass 0.30 · TorsoSterHeight 1.00 · TorsoSterDepth 0.90 ·
Muscle 0.80 · **yoke first (R4): NeckMass (authored) + Traps 0.95 /
TrapsMeat 1.00 / TrapsPush 0.90** · TorsoMass 1.00 · BackSize 1.00 ·
BackSlope 0.90 · SerratusMid 0.40 · TorsoLower 1.00 · Pecs Size 1.00 /
Mass 1.00 / Width 1.00 / Lower 0.70 / Clavicle 0.70 · Delts 0.90
(+Back/Shape 0.60) · Biceps 0.85 / **BicepsBack 0.75 (R13)** / Side
0.75 / Brachio 0.80 · **Fore 1.00 (R14)** · LegsSize 1.00 · LegsThigh
1.00 · Glutes 0.80 · CalfSize 0.80 / CalfWidth 0.75 · ButtBooty 0.75 ·
BubbleButt 0.40. **NeckMass** is authored per study item A2: Sen's
Weight 0.90 with the block gated to the neck band (h 0.88–1.18,
r < 0.13–0.20) so the yoke gets the mass without the block's known
whole-body inflation.

**Broadness** (`body.chest.width`) — Joe's component: TorsoShoulderInc
0.50 · TorsoWidth 0.95 · ArmsShoulders 0.90 · TorsoBackShape 0.85 (lat
sweep). Lateral frame + lat width ONLY: no depth (SterDepth lives in
the core), no pec mass. Dial it without touching either.

**Tissue** (`body.tissue.strongman`) — Sen's tissue values: Chubby
0.80 · TorsoMassSmooth 0.75 · TorsoBellyLHandles 0.60 · PecsSaggy 0.45 ·
LegsChubby 0.75 · ButtSaggy 0.25 · BellySmooth 0.70 · TrapsValleys
0.30. **Belly = the v4 system, not a re-derivation**: inside the v4
core mask the kernel tissue crossfades to τ·D3 (learned field +
pendant drape), plus D_posture over the torso — muscle stays fully
applied underneath (R17's built core). **τ = 0.60**, solved *after* the
muscle-system repair, on slice-loop girths, for chest:waist ≥ 1.30.

**Corrective passes (all documented deviations, made against the
scorecard):** TorsoSterDepth 0.60→0.90 and BackSize/PecsMass →1.00 (M5
pass — chest depth was losing to belly depth); calf pair trimmed
(0.90/0.85 → 0.80/0.75) after the calf stack out-grew the neck 1.9×;
NeckMass gate widened once (r falloff 0.10–0.16 → 0.13–0.20; moved
neck girth only +0.4 cm — see §6).

**Excluded, with reasons:** Lean (two-sided, sign-ambiguous — v4
precedent) · TorsoWaistSize ("Shrink Waist" semantics; R18 routes the
waist through TorsoLower + LHandles + belly, no shrink term) · the
HIMBO belly stack (replaced by the v4 system per the brief) ·
SamuelLike and BodyMass > 0.30 (body-swap / inflation, H1) · Femme* /
genital orphans (wrong pattern / out of scope) · definition family
above TrapsValleys (definition is tissue-dial-*down* at this cell).

**Atomic Muscle:** attempted, not transferred. Its base positions are
locked in a FO4 BSTriShape NIF (half-float interleaved vertex stream);
three extraction routes failed (32-byte f32 stream scan, .tri position
probe — the .tri holds morph records only, Skyrim NiTriShape parser).
Its decode stats serve as a calibration cross-check: AM's Nuclear
BodyBuilder macro peaks at ~7.3 cm; our granular muscle stack peaks at
7.7 cm on its own base — same order, as AM_VS_HIMBO's granularity
argument predicts.

## 3. Machinery

v1/v4 kernel transfer, extended from torso-only to the whole body:

- **Torso kernel** — v4's pairwise Gaussian in (h, θ) with band-mean
  arc, but **signed θ** (v4 folded |θ|; bara needs pecs ≠ lats).
  Sample gate widened for the yoke (neck band to h = 1.18 at r < 0.13).
- **Limb kernels (new)** — per chain (arm/leg), side, and segment
  (upper arm/forearm, thigh/calf): Gaussian in (t along axis, φ·r̄ arc),
  transferring (dr, ds). Landmarks are geometric (radius-profile local
  minima — a plain argmin picks the *wrist* as the elbow; caught in QA
  when the base forearm read 13 cm). **Scaling lesson:** dr scales by
  the segment's base-*radius* ratio, ds by its length ratio. A single
  length ratio (v1) over-amplified the calf ×1.9, because Skyrim's calf
  segment is proportionally far shorter than hm08's — the first build's
  calf grew +88% where the source recipe grows +42%. Thigh (homologous
  proportions) was faithful under both rules, which is how the bug was
  isolated.
- **Region weights** — torso (v4's W + neck extension, jaw fade
  tightened to h 1.07–1.15), arm, leg; graph-smoothed; partition of
  unity only where coverage ≥ 1 (no normalisation spikes at edges).
  Hand fade past the wrist (t > 1): no recipe slider targets hands,
  and kernel smear there was a flip source.
- **Fold repair, surgical** — slope limiter (κ 0.55, v4) + attenuation
  of flipped verts only (×0.78) and their direct neighbours (×0.93).
  The first run used v4's broad ring rule and dusted **10,453 verts**,
  visibly costing chest/neck mass between solve and grade; the surgical
  rule attenuates **31 / 45 / 28 verts** (core/width/tissue) and the
  τ solve now runs on the repaired muscle system, so the shipped M4 is
  the solved M4.
- **Found en route (affects v1–v4 assumptions):** the saved MPFB macro
  base lives in its own frame (z: feet 0 → crown 1.659) while
  base.obj / correspondence / D3 / posture live in the raw obj frame
  (z: −0.817 → 0.849). Harmless in v4 (only used for
  translation-invariant flip checks); fatal to landmarks and girths
  here. The build aligns the macro base into the raw frame per-axis by
  min/max before any use (residual = the macro reshaping itself,
  median 0.3 / 0.8 / 1.4 cm per axis).

**Kernel CV** (5-fold, v4 protocol, 23 fields): torso/muscle median
0.43 cm / p95 1.87 cm (v4's torso benchmark: 1.96); torso/tissue
0.29 / 0.90; torso/width 0.24 / 0.74; all limb fields median
0.07–0.45 cm, p95 ≤ 1.30 cm. Zone residuals are therefore at or below
the v1–v4 standard everywhere.

## 4. Scorecard (BARA_LESSONS §2, combined +1/+1/+1, macro base)

Circumferences are mesh-plane slice-loop perimeters; arm girths use
the largest-loop tape convention (the field data's own). Full record:
`work/qa_numbers_bara.json`.

| metric | base | build | band | verdict |
|---|---|---|---|---|
| M1 neck width / head width | 0.633 | **0.711** | ≥ 0.68 | **PASS** |
| M2 neck ÷ arm (Reeves 1.00) | 1.180 | 0.688 | 0.92–1.05 | miss |
| M2 neck ÷ calf | 0.947 | 0.633 | 0.90–1.08 | miss |
| M3 forearm ÷ arm | 0.828 | 0.690 | 0.80–0.88 [E] | miss |
| M4 chest ÷ waist girth | 1.555 | **1.301** | ≥ 1.28 | **PASS** |
| M5 chest ÷ waist depth | 1.017 | 0.938 | ≥ 1.25 | miss |
| M6 trap slope | 34.5° | **32.9°** | 28–50° | **PASS** |
| M7 visible neck / head | 0.237 | **0.168** | 0.12–0.38 | **PASS** |
| M8 delt span / head width | 3.53 | **4.51** | ≥ 2.6 | **PASS** |
| M9 built mass (volume, fixed height) | 51.2 L | **98.7 L (+92.7%)** | grows at fixed height | **PASS** |
| M10 fat band 15–25% | — | tissue = 43% of added volume (proxy) | n/a per study | reported |
| M11 thigh ÷ waist | 0.684 | **0.740** | ≥ 0.62 | **PASS** |
| M12 heads tall | 7.61 | 7.36 | 6.4–7.2 | miss |
| M13 chest width ratio (Joe add.) | 46.7 cm | **56.0 cm (×1.199)** | ≥ 1.15 [E] | **PASS** |

Raw girths (cm), base → muscle system → combined: chest 108.2 →
129.1 → **133.6** · waist 69.6 → 84.9 → **102.6** · neck 32.2 → 36.0 →
**36.4** · upper arm 27.3 → 49.4 → **52.9** · forearm 22.6 → 33.5 →
**36.5** · thigh 47.6 → 64.5 → **75.9** · calf 34.0 → 46.7 → **57.6**.
Muscle-system chest:waist is 1.522; the tissue layer spends it to
1.301 — exactly R17's budget mechanics.

## 5. Joe's additions, measured

**Broadness (M13).** Chest loop width 46.7 → **56.0 cm (+19.9%)**;
deltoid span 55.7 → **71.1 cm (+27.6%)**. The width slider alone
carries a 5.8k-vert field (max 1.8 cm — it is a frame nudge, not a
mass), separable from SterDepth (depth) and the pec stack (mass),
both of which stay in the core.

**Fat wrap (side-mass).** Mean |radial| tissue displacement by angular
sector (θ = 0 front, ±90° flanks, 180° back), tissue layer alone,
pre-correction:

| band | front | flank | back | flank/front |
|---|---|---|---|---|
| chest (h .78–.92) | 0.30 cm | 0.32 cm | 0.26 cm | **1.08** |
| belly (h .35–.55) | 1.44 cm | 1.06 cm | 0.75 cm | **0.74** |

The layer already wraps — both ratios clear the pre-registered
correction thresholds (0.45 / 0.50), so **no flank correction was
applied** (had it triggered: LHandles → 0.85, MassSmooth → 0.85,
Chubby → 0.90). In the *shipped* tissue the belly flanks carry
**1.23 cm** of tissue — the v4 crossfade does not eat them (its mask
is front-weighted; flank verts keep the kernel tissue, LHandles
included). The shipped belly flank/front prints 0.29 only because the
denominator becomes the 4.98 cm v4 belly core — a front structure by
design. The silhouette-level check agrees: waist loop *width*
24.1 → **35.4 cm (+46.9%)** — the sides move out with the front, they
do not stay narrow while the front pads.

## 6. Honest self-critique — where it still reads wrong

1. **The neck is the ceiling (M2, both relations miss).** Neck girth
   grows only 32.2 → 36.4 cm (+13%) while arms grow +94% and thighs
   +59%. HIMBO's neck material is thin: the Weight block gated to the
   neck plus trap spill is all the vocabulary offers, and widening the
   gate bought +0.4 cm. The *width* read passes (M1 0.711, traps carry
   the yoke visually — see the front render), but a tape around this
   neck will never call it Reeves-equal to a 52.9 cm arm. The fix is
   an authored neck field or a neck-bearing learned source, not a
   recipe value. This is the build's #1 gap against the study.
2. **Forearm lags (M3 0.690 vs band 0.80–0.88 [E], field data
   0.70–0.76).** ArmsFore is already pinned at 1.00; HIMBO's forearm
   field is simply weaker than its biceps/triceps stack. We land just
   under even the strongman *field* band. In the front render the
   forearm reads smooth and tapered against a huge upper arm; a faint
   crease at the elbow segment seam is visible on close inspection.
3. **The belly wins on depth (M5 0.938 vs ≥ 1.25).** At the navel
   station the power belly's AP depth (26.2 cm) exceeds the chest's
   (24.6 cm) even after the depth corrective pass. In profile the
   belly, not the chest, leads the silhouette — it reads
   fat-dominant rather than built-core-first. Two honest caveats: the
   girth relation (the one Shaw's numbers actually anchor) passes,
   and Shaw's own implied depth ratio is ~1.15–1.2, so the study's
   1.25 band may itself be ~0.05–0.1 optimistic — flagged as a
   question for the study, not silently re-banded here.
4. **The head is the base's head (M12 7.36 vs 6.4–7.2).** No head
   work is in scope for a body proof; on this frame the unmodified
   head reads small (which M8's 4.51 partly *is*). Species-head
   pipeline territory.
5. **The base is feminine.** The MPFB default-macro human carries a
   bust form; the pec stack adds mass on top of it rather than
   replacing its shape (visible in both renders). Every hm08 proof
   inherits this; masculinising macros are an app-layer concern, but
   on *this* pole it is the largest single visual wrongness after
   the neck.
6. **Proportion debt from the source.** Skyrim's HIMBO base is a
   ~1.46 m-proportioned stylisation; per-segment radial scaling keeps
   girth relations honest, but ds (along-axis) components inherit its
   compressed limb proportions. The renders don't show an obvious
   artifact; the CVs say the fields are faithful; the debt is noted,
   not hidden.
7. **M10 remains a proxy.** "Tissue = 43% of added volume" is not a
   body-fat percentage (the scorecard itself marks M10 n/a); it only
   documents that the tissue layer is a substantial minority of the
   build, muscle-led, per R15/R16.

**What would move the needle next:** an authored NeckMass field
(hand-built, like the belly core was) for M2; a forearm-specific
learned source for M3; a masculine macro base for the chest-form
problem. All three are asset work, not recipe work — the recipe layer
is at the vocabulary's ceiling.

## 7. Provenance

Study-only, as the other proofs. Every field derives from sliders
decoded from Joe's own legitimately obtained mod files (the learned
library: HIMBO full decode; the v4 belly system from the Fat Males /
HIMBO first-proof lineage). No source assets, meshes, or slider data
are redistributed — only composed displacement fields, recipes, and
measurements ship. Atomic Muscle contributed calibration statistics
from its published decode only.
