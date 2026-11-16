# COUPLING VALIDATION — Muscle × Tissue couplings on hm08 geometry

*Nov 12, 2026. Geometry validation of the coupling model in
`MUSCLE_TISSUE_MODEL.md` §9 items 1 + 7b: the model's vector-layer
numbers were evaluator truths, not mesh truths — this pass settled
them on the actual hm08 mesh. Build + measurement scripts ran Nov 12;
the hyper-range pass later the same day found and repaired fold
defects in two of the three shipped targets (§6 tells that whole
story), and a read-only re-gate at the end of the day confirmed the
repaired state from disk (§6.4). This document is the report that
should have shipped with the build; it is written from the preserved
numbers, logs, and files, and says plainly which measurements were
taken when, and on what.*

**Verdict up front:** every coupling claim that was tested on mesh
held — definition submergence matched the attenuation model to
~0.001, the distribution axis moved girths in the predicted
directions at the predicted relative sizes, the pecs-crease
interaction ratio matched its prediction to three decimals, and the
neck show-through boost measured +2.0 mm against a separable-field
prediction. The one failure was not a coupling claim but a shipping
one: two targets that gated clean in float space flipped faces once
quantised into `.target` files (§6). Both are repaired; the house
rule that came out of it — *ship gates run on the shipped quantised
numbers* — is now load-bearing.

---

## 1. What was built, and the machinery

Three character targets, composed by the app evaluator's coupling
rules and written as MPFB `.target` files against hm08 (19,158
verts; fold gates over the 13,378 body faces):

| target | moved verts | recipe (evaluator inputs) |
|---|---|---|
| `body.coupling.gachidebu.target` | 10,570 | muscle 0.80, chubby 1.0, tissue.mass_smooth 0.9, belly pot/protrusion 0.85, distribution 0 → derived tissue level **0.945** |
| `body.coupling.pear.target` | 10,482 | distribution **−1**, muscle 0.45, tissue level **0.637** |
| `body.coupling.bigchest.target` | 10,482 | distribution **+1**, muscle 0.85, tissue level **0.419** |

Composition choices, documented in the build script and not hidden:

- **Gachidebu tissue** = the shipped strongman tissue field scaled by
  the level ratio 0.945/0.7575 = **×1.2475** (uniform, because
  distribution is 0 at both cells — the model's own regional
  formula). The PowerBelly core/drape routing is a vector-layer
  output whose pre-belly kernel component was never saved, so the
  belly scales with the layer and M4 (chest/waist) is graded as the
  check on that choice.
- **Distribution pair tissue substrate** = the v5 adiposity system
  (D5(w) = w·LIN5 + w²·SAG, γ=2), not the bara tissue field — v5 is
  the library's whole-body fat system and its limb component is what
  the distribution weighting needs. The evaluator's level is
  identified with the v5 slider value w [E identification: both are
  0..1 adiposity fractions]. Muscle amplitude (the composed strongman
  field) is held constant across the pair so the axis is the only
  muscle-side variable.
- **Definition fields** (traps valleys, V line, pecs crease) were
  transferred to hm08 as unit fields with a feature-preserving
  kernel. Peak recovery vs the source fields: valleys 0.42, vline
  0.43, crease 0.28 (standard kernel: 0.20 / 0.14 / 0.12). Dip
  measurements are therefore *increments over the identical build
  without the added field*, never absolutes — the substrate's own
  relief cancels out of the contrast.
- **Fold gates run on both frames** — the raw base.obj frame and the
  MPFB macro frame (range-aligned), house standard since the v1
  belly proof. A "flip" is a body face whose normalised normal dot
  (rest vs deformed) goes negative.

**Machinery self-check.** Before any coupling number was taken, the
shipped strongman build was re-graded with this script's machinery
and reproduced `BARA_PROOF.md` exactly: M4 1.301, M1 0.711, chest
133.6 cm, waist 102.6 cm, neck 36.4 cm, thigh 75.9 cm. The measuring
instruments were not the variable in anything below.

Scripts: `scripts/build_coupling_validation.py` (build + primary
numbers), `scripts/measure_coupling_validation.py` (follow-up:
perimeter stations, curve-following dips, crossfade wrap audit),
`scripts/measure_coupling_hip.py` (hip addendum — see §4.3),
`scripts/test_coupling_validation.py` (Blender end-to-end — see §7).
Numbers: `work/coupling_validation_numbers.json`,
`work/coupling_measurements.json`; logs alongside them.

---

## 2. Gachidebu — definition submergence (§9 item 1)

The worked example from the model doc (§7.1): muscle 0.80, tissue
level 0.945, distribution 0. Grade of the composed build: height
1.668 m, volume 104.8 L, M1 (neck/head width) 0.864, M4
(chest/waist girth) 1.265, trap angle 28.4°, visible-neck ratio
0.578, thigh girth 78.5 cm, calf 60.0 cm.

### 2.1 Definition attenuation — the headline test

The coupling claims tissue submerges definition relief by a
per-region attenuation factor. Measured on the surface, as dip-depth
increments over the identical build without the field:

| field | class | raw | effective (evaluator) | attenuation | measured total read | model prediction |
|---|---|---|---|---|---|---|
| V line | abdomen | 0.85 | 0.195 | 0.2297 | **0.2294** | 0.2297 |
| traps valleys | yoke | 0.40 | 0.322 | 0.8054 | **0.8043** | 0.8054 |

The abdomen class submerges to ~23% visibility at this tissue level;
the yoke class keeps ~80%. The measured reads land within 0.001 of
the evaluator's predictions — the attenuation coupling is a mesh
truth, not just a vector-layer one. (Tissue fill factor 0.9986–0.9987
in both cases: at level 0.945 the tissue field covers the relief
almost completely, and what survives is exactly the predicted
fraction.)

A second, curve-following dip metric (follow-up measurement run,
sampling along each field's own footprint because the binned profile
metric smears diagonal lines) corroborates the direction: V-line dip
increment +0.50 mm at low tissue → **+0.11 mm coupled** — the same
~4.4× submergence, measured independently.

### 2.2 Neck show-through — and a bug found in the shipped muscle

NeckMass is the one show-through boost that is separable post-hoc
(it was authored as a gated Weight-block transfer), so it was
applied exactly: embedded neck field × (0.9574/0.90 − 1) = factor
1.0638. Measured on mesh: neck girth 43.37 → **43.57 cm (+2.0 mm)**,
neck width 13.50 → 13.61 cm, M1 0.856 → 0.864. Small, in the
predicted direction, at the predicted size.

The larger finding is about the substrate: **the shipped
`body.muscle` contains no authored neck field at all** — a name miss
in `build_bara.py` dropped it (bug report also in the build script's
notes). Every neck number in the bara proof was therefore carried by
other fields. With an authored neck field derived in this script
(support 1,818 verts, max 1.53 cm), the shipped strongman's neck
goes 36.4 → **43.2 cm** and M1 0.711 → **0.854**. The coupling
validation's neck results use that derived field throughout, on
identical builds raw-vs-effective, so the comparison is clean — but
any future muscle rebuild should fix the name miss at the source.

The other two boosts are honestly unmeasurable post-hoc and no
geometry change is claimed for them: PecsSize and TorsoMass were
requested at 1.085 and **clamped to 1.0** by the evaluator (the
excess is a warning, per the model — both warnings are preserved in
the numbers file), and their fields already sit at recipe 1.00
inside `body.muscle`. ArmsDelts (0.90 → 0.989) is inseparable from
the composed muscle field after the fact.

### 2.3 Tissue wrap audit

The tissue_wrap coupling emits, for this build: wrap.factor.chest
0.798, wrap.factor.waist 1.000, wrap.ratio.waist 0.65, with the
stiff-sides floor 0.40 enforced. Audited three ways, because "ring
tissue" has no unique post-hoc reconstruction:

| band | full-field audit (front / flank cm) | flank/front | ring-only audit | crossfade-weighted (follow-up) |
|---|---|---|---|
| chest | 0.57 / 0.66 (back 1.95) | 1.149 | flank/front 1.210 | flank/front **5.70** (front 0.21, flank 1.21) |
| waist | 9.34 / 2.39 (back 1.37) | 0.256 | front 0.00, flank 1.73 | front 0.00, flank 1.07 |
| belly apron | 9.24 / 2.20 (back 1.29) | 0.238 | front 0.00, flank 1.73 | front 0.00, flank 1.27 |

Reading: at the waist and apron the front carries the tissue
(+9.3 cm) and the flanks move at roughly the emitted ratio of the
front — front-dominant, as the wrap model intends at high front
tissue. At the chest the displacement routes to the back (1.95 cm)
and flanks instead — the chest band's tissue goes around, not
forward. The ring-only and crossfade audits agree that within the
ring band proper, the *front* contribution is ~0: the front growth
lives in the belly/apron field below the ring, not in the ring
itself. The three audits measure three different reconstructions;
the doc reports all three rather than picking the flattering one.

---

## 3. The distribution pair — pear (−1) vs big-chest (+1)

Question: do the distribution factors, applied as muscle-field
weights (0.6-strength factors) and v5 adiposity weights
(full-strength factors) per macro region, move the body's girths in
the axis's directions? Each build is graded against its own
distribution-0 control (same levels, distribution 0), so the axis
is the only difference.

### 3.1 Slice girths (build run)

| | chest | waist (navel) | waist (min) | chest:waist | hip width | shoulder:hip | thigh |
|---|---|---|---|---|---|---|---|
| pear | 127.5 | 104.9 | 88.8 | **1.216** | 0.433 m | 1.527 | 81.0 cm |
| pear control | 134.1 | 111.5 | 93.8 | 1.202 | 0.408 m | 1.619 | — |
| bigchest | 138.9 | 93.4 | 87.9 | **1.486** | 0.381 m | 1.959 | 66.1 cm |
| bigchest control | 132.2 | 96.9 | 88.8 | 1.365 | 0.399 m | 1.871 | — |

Directions all as predicted: pear sheds chest (−6.6 cm vs control),
widens hips (+2.5 cm width), drops the shoulder:hip ratio; bigchest
gains chest (+6.7 cm), narrows hips (−1.8 cm), raises
shoulder:hip. The chest:waist contrast between the two poles is
1.216 vs 1.486 — the axis separates the silhouettes decisively.
Volumes underline it: pear is the *most* voluminous build of the
three (106.8 L) despite a mid tissue level, because the mass sits
in hips/thighs (thigh girth 81.0 cm, M11 thigh/waist 0.806);
bigchest is the leanest (93.2 L, M4 1.425).

### 3.2 Perimeter stations (follow-up run) — and the hip NaN

The build's slice-girth method fits an ellipse per section; on
pelvis sections the fit degenerates and **hip girth came back NaN
for every build, including the base**. The follow-up run therefore
re-measured girths as raw loop perimeters at fixed stations (a
different method — absolute values run larger and must not be
cross-compared with §3.1):

| station (cm) | base | strongman | gachidebu | pear | pear ctl | bigchest | bigchest ctl |
|---|---|---|---|---|---|---|---|
| chest | 134.5 | 157.1 | 158.7 | 147.5 | 165.4 | 171.0 | 159.6 |
| waist (navel) | 73.6 | 103.5 | 107.6 | 102.2 | 109.5 | 101.8 | 101.3 |
| waist (min) | 75.7 | 106.2 | 111.0 | 113.9 | 114.7 | 102.2 | 104.2 |
| hip | 125.8 | 125.8 | 127.0 | **135.8** | 130.9 | **125.8** | 128.3 |
| thigh | 112.2 | 112.2 | 112.2 | 112.2 | 112.2 | 112.2 | 112.2 |

(Thigh is a fixed-station perimeter above where these fields act —
identical everywhere by construction of the station, not a result.
The thigh *girths* in §3.1 come from the grade's own stations.)

Station ratios tell the same story as the slices: pear waist:hip
0.753 vs control 0.837, chest:hip 1.086 vs 1.264; bigchest
chest:waist 1.679 vs 1.575, chest:hip 1.359 vs 1.244. Pear's hip
perimeter grows +4.9 cm over its control while its chest shrinks
−17.9 cm; bigchest's chest grows +11.4 cm while its hip slightly
shrinks. The axis redistributes; it does not merely scale.

A tissue-scaled-only gachidebu variant (strongman + the ×1.2475
tissue scaling, no other change) was also stationed — chest 158.8,
waist-navel 107.8, waist-min 111.3, hip 126.8 — within 0.3 cm of the
full gachidebu at every station, which is the M4 attribution check
on the §1 composition choice: the level-ratio scaling accounts for
essentially all of the build's girth change.

### 3.3 Zone residuals — the price of the approximation

The distribution reweighting is applied per macro region
(region sizes: chest 9,371 / waist 289 / hips-glutes 564 / thighs
3,156 / neck 4,408 / arms 4,042 verts). Residuals of the composed
field against evaluator intent, RMS by zone:

| zone | gachidebu | pear | bigchest |
|---|---|---|---|
| chest | 0.43 | 0.63 | 0.49 |
| waist | 0.86 | 1.06 | 0.75 |
| hips/glutes | 0.73 | **1.46** | 1.12 |
| thighs | 0.20 | 0.46 | 0.37 |
| neck | 0.47 | 0.12 | 0.10 |
| arms | 0.39 | 0.64 | 0.56 |

Worst cell: pear hips/glutes, RMS 1.46 cm, max 4.24 cm — the
strongest reweighting (factor 1.45) on the most curved region.
These residuals are the documented cost of zone-wise weighting;
nothing in §§2–3 depends on them being zero, and they are the
obvious first target if the axis ever needs sharpening.

---

## 4. Pecs crease interaction (§9 item 7b — test conditions)

The model carries a test-asserted claim: distribution × attenuation
interact, so the same raw crease survives *less* on a big-chest
build than on a pear build at equal tissue level. Measured on mesh
at the test's own conditions (tissue level 0.6, muscle 1.0, raw
crease 0.80):

| | effective | attenuation | dip increment, coupled | dip increment, raw |
|---|---|---|---|---|
| pear | 0.771 | 0.9636 | 0.54 mm | 0.56 mm |
| bigchest | 0.566 | 0.7080 | 0.40 mm | 0.56 mm |

**Coupled ratio measured 0.7347 vs predicted 0.7347** (attenuation
ratio 0.7347, fill ratio 1.000). The follow-up curve-following
metric independently confirms it: pear coupled +0.84 mm vs raw
+0.87; bigchest +0.62 vs +0.87 — ratio 0.735. The interaction is
real, sized as predicted, and it is purely the attenuation coupling
at work (fill contributes nothing) — exactly the mechanism the
model asserts.

**Caveat, recorded not buried:** in that same float-space test
composition, the full bigchest + crease build showed **7 flipped
faces on the macro frame** (pear: 0). The crease field does not
ship inside the coupling targets — this was a measurement build —
but a combined bigchest+crease *preset* would sit past the fold
boundary and needs its own repair before it ships as anything.

---

## 5. Fold gates, act 1 — the build (float space)

During the build, each field increment was attenuation-repaired
until clean, then the composed builds were gated in float64:

| build | increment repair | composed, raw frame | composed, macro frame |
|---|---|---|---|
| gachidebu | clean after 17 iterations (204 → 0) | 0 flips, min_dot **+0.00061** | 0 flips, min_dot +0.00585 |
| pear | clean after 0 iterations | 0 flips, min_dot +0.00465 | 0 flips, min_dot +0.31701 |
| bigchest | muscle weighting 16 iters, tissue 13 iters | 0 flips, min_dot **+0.00177** | 0 flips, min_dot +0.00210 |

All three passed. But look at the margins: gachidebu and bigchest
sat **on** the fold boundary — a min_dot of +0.0006 means the worst
face was one rounding step from inverting. That is the setup for
what happened next.

## 6. Fold gates, acts 2–3 — the shipped defect and its repair

*(Hyper-range pass, later the same day; full account in
`../hyper/HYPER_RANGES.md` §4, numbers in
`../hyper/work/defect_fix.json`, script
`../hyper/scripts/fix_coupling_defects.py`.)*

### 6.1 Discovery

The `.target` format quantises deltas to 0.1 mm (3-decimal dm).
Nobody had gated the files *as shipped* — the gates in §5 ran on
the in-memory float deltas. When the hyper pass re-gated the
shipped files recomposed from disk, two of the three were
defective at their own 1.0× design point:

| shipped file | flips (raw / macro) | flipped faces |
|---|---|---|
| bigchest | **1 / 0** (min_dot −0.0239) | F4952 — centroid (−0.005, +0.057, +0.670) m, height fraction 0.892 |
| gachidebu | **3 / 3** (min_dot −0.0239 / −0.916) | F489 (h 0.887), F4952 (h 0.892), F7215 (h 0.895) |
| pear | 0 / 0 | — |

All four flipped faces live in one cluster — the upper-chest /
shoulder field at ~89% body height — and F4952 flips in both
combos. The quantisation step (≤0.05 mm per component) was enough
to push faces that were sitting at min_dot +0.0006…+0.0018 over
the edge. The builds were never "wrong"; the *gate was applied to
numbers that were not the numbers that shipped*.

### 6.2 Repair

Attenuation repair performed **in quantised space** — iterating on
the exact values that ship — gated on both frames to 0 flips
**and** a margin floor (min normalised dot ≥ 0.01), so the fix has
headroom instead of landing back on the boundary:

| combo | repair rounds | after: flips, min_dot (raw / macro) | deviation vs original |
|---|---|---|---|
| bigchest | 2 | **0**, +0.0764 / +0.0542 | max 1.64 mm, RMS 0.038 mm, 34 verts changed |
| gachidebu | 13 | **0**, +0.0233 / +0.0189 | max 3.06 mm, RMS 0.085 mm, 87 verts changed |

The repair cost is invisible (worst vertex 3.06 mm, sub-0.1 mm
RMS). The repaired files were written back over
`body.coupling.{bigchest,gachidebu}.target` with provenance notes
in their headers; the originals are preserved in
`../hyper/work/originals/` (md5-verified identical to the shipped
files before repair). Pear was never defective and was not touched.

### 6.3 What the repair does not buy

The repaired combos still fold at 1.5× (bigchest 45 faces,
gachidebu 111, raw frame). That is expected and stated in
HYPER_RANGES §3.5: these are 1× families until a per-segment
re-solve exists (H4). The repair buys a clean design point, not a
range extension.

### 6.4 Re-verification from disk (this report's own check)

Before writing this doc, the three targets as they currently exist
in `bara-proof/` were re-gated read-only (the hyper pass's
`hyper_common.fold_stats`, both frames, nothing written):

| current file | raw frame | macro frame |
|---|---|---|
| pear | 0 flips, min_dot +0.00609 | 0 flips, min_dot +0.35188 |
| bigchest | 0 flips, min_dot +0.07643 | 0 flips, min_dot +0.05420 |
| gachidebu | 0 flips, min_dot +0.02330 | 0 flips, min_dot +0.01889 |

The bigchest and gachidebu numbers reproduce `defect_fix.json`
exactly, and re-gating the preserved originals reproduces the
defect exactly (1 and 3 flips, same min_dots). The post-fix state
on disk is the state §6.2 claims.

One honest flag: **pear's raw-frame margin (+0.0061) is the
thinnest of the three and sits below the 0.01 floor the hyper pass
adopted.** Pear never flipped — in float, as shipped, or now — so
it was legitimately left alone; but it is the closest of the three
to the boundary, and any future edit to that target should re-gate
it under the margin-floor rule rather than the pass/fail rule it
was built under.

---

## 7. Known debits and loose ends

- **Blender end-to-end not run.** `test_coupling_validation.py`
  (loads the three targets as shape keys on an MPFB human,
  flip-checks the *evaluated* mesh, renders front + profile per
  character) was written but there is no record of it having run —
  no coupling renders exist and no output JSON was produced. All
  gates above are numpy-space, the same machinery B16's audit and
  the hyper pass used; an evaluated-mesh check inside Blender
  remains a genuinely different (stronger) test that is still owed.
- **Hip addendum output missing.** `measure_coupling_hip.py` was
  written to fix the hip NaN at a fixed station and to write
  `work/coupling_hip.json`; that file does not exist and its log
  shows only the setup preamble. The hip evidence in §3.2 therefore
  rests entirely on the follow-up run's perimeter stations.
- **Crease-at-bigchest composition flips** (7 faces, macro frame,
  float space, test conditions) — §4 caveat. A combined preset
  needs its own quantised-space repair before shipping.
- **A cast warning in every log.** All three runs log
  `RuntimeWarning: invalid value encountered in cast` from the
  build script's transfer code. It predates this validation (the
  machinery is copied from the earlier proofs) and no number in
  this doc is known to be affected by it, but it has never been
  run to ground.
- **The neck field fix belongs upstream.** §2.2's missing authored
  neck field is a `build_bara.py` bug; this validation worked
  around it with a derived field. A muscle rebuild should fix the
  name miss and re-derive, at which point the strongman neck
  numbers in BARA_PROOF.md (36.4 cm) will move to the authored
  values (~43.2 cm) and every downstream neck comparison shifts
  with them.

## 8. Evidence inventory

| artifact | where |
|---|---|
| This report | `bara-proof/COUPLING_VALIDATION.md` |
| Shipped targets (2 repaired, 1 original) | `bara-proof/body.coupling.{gachidebu,pear,bigchest}.target` |
| Pre-repair originals (bigchest, gachidebu) | `hyper/work/originals/` |
| Build + primary numbers | `bara-proof/work/coupling_validation_numbers.json`, `build_coupling_validation.log` |
| Follow-up measurements | `bara-proof/work/coupling_measurements.json`, `measure_coupling_validation.log` |
| Repair record | `hyper/work/defect_fix.json`, `hyper/work/fix_log.txt`, `hyper/HYPER_RANGES.md` §4 |
| Scripts | `bara-proof/scripts/{build,measure}_coupling_validation.py`, `measure_coupling_hip.py`, `test_coupling_validation.py`; `hyper/scripts/fix_coupling_defects.py`, `hyper_common.py` |
