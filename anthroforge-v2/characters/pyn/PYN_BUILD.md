# PYN — Body Build (AnthroForge)

**Date:** Nov 16, 2026 · **Scope (Joe, Nov 16):** body shapes only — NO fur, NO renders, numeric QA only. Sen stage 1 is the pattern; stage 2 (LOD cards/renders) skipped entirely. **No head build** — the preset's head vector is recorded in the preset for later; the GLB keeps the hm08 base head as placeholder geometry so the mesh is complete.
**Deliverable:** `pyn_composed.glb` — unrigged static bake, single body mesh (19,158 verts), uniformly scaled to crown–sole **1.680 m**. Plus `targets/body.pyn.target` (the shipped quantised delta), `work/qa_pyn.json`, `work/pyn_fields.npz`, `scripts/build_pyn.py` (+ verbatim-extracted machinery in `scripts/pyn_machinery.py`, `scripts/w3_block.txt`).

> **⚠ CORRECTED Nov 16, 2026 — see the Correction section below.** The
> 19,158-vert GLB contained MakeHuman helper geometry alongside the body,
> and the "crown–sole 1.680 m" claim described the helper-inclusive mesh.
> The GLB has been re-exported body-only (13,380 verts); the composed
> **body itself measures 1.6522 m** as shipped. Composition, girths, fold
> gate and volume are unchanged.

## Correction — Nov 16, 2026 (body-only re-export; helper geometry removed, height claim corrected)

The shape-render pass found that the shipped `pyn_composed.glb` was the
full hm08 export mesh, not the body alone: **19,158 verts in 154
islands** — the 13,380-vert body island plus **153 MakeHuman helper
islands** (hair/skirt helpers, joint cubes, eye/teeth bits; 5,778 verts).
Jorge's export had shipped body-only; Pyn's (and Brand's) had not.

**Fix.** The GLB was re-exported with only the body island, at the
*same* scale and transform as shipped — no vertex moved. The original
file is preserved at `work/originals/pyn_composed.glb`. New file:
13,380 verts / 26,756 tris, exactly 1 island, 0.64 MB. Verification
(`work/qa_bodyonly_fix.json`): the new body verts are **position-
identical to the original's body island — max deviation 0.0 m**
(bitwise, float32; normals likewise). QA gauntlet re-run
(`work/qa-bodyfix/`): parse/geometry/scale/textures ok, skin/morphs
warn (same signature as the original run), 0 degenerate, 0 NaN, max
extent now 1.6522 m.

**Height claim — corrected.** Method step 7 computed the export scale
0.99141 from the base-scale z-range **1.6946 m of the whole mesh**,
helpers included; the helpers extend ~28 mm past the body's crown and
sole, so "GLB height exactly 1.6800 m" was true only of the
helper-inclusive mesh. The composed body itself: **1.6665 m at base
scale** (the grade-station height in the Measurements table — that
figure was body-measured all along), and **1.6522 m as shipped**
(×0.99141) — i.e. the body sits **27.8 mm short of the 168 cm target**.
A scale of **1.00811** (not 0.99141) would have put the body at
exactly 1.680 m. The re-export deliberately keeps the shipped scale —
the geometry is the composed geometry, untouched; whether to rescale
to a true 168 cm body is a separate decision, not taken here.

**What did NOT change.** The slider composition and the shipped
`.target` are untouched. Every girth and ratio in the Measurements
table was graded on the 26,756 body faces and stands. The fold gate
ran on the shipped delta over those body faces — helpers never
entered it — so the PASS stands verbatim. Volume: recomputed on the
body-only GLB = **45.703 L**, matching the 45.70 L below — that figure
was body-only all along, so the mass-evidence section stands
unchanged (it keys off the 45.7 L volume; only its "at 168 cm"
framing should now be read as "at 165.2 cm as shipped").

## Method

The proven bara-proof path (same as Sen), because the app path cannot apply this vector: 21 of the preset's HIMBO-vocabulary sliders have only `skyrim_himbo` record instances (native-base decode stats, no hm08 instance pack). Pipeline:

1. **Effective vector** from the app core's own coupling evaluation (`anthroforge-app` `core/build.py: evaluate_character` on `pyn.afchar.json`; validation ok, no errors/warnings). Geometry consumes the *effective* values, per the composition doctrine.
2. **HIMBO composition** on the HIMBO base (9,346 verts, Vanilla OSD blocks) — `compose()`/`hi_diff()` verbatim from `bara-proof/scripts/build_bara.py`.
3. **Kernel transfer to hm08** — (h,θ) torso kernel + (t,φ) limb segment kernels, region-weight partition-of-unity blend, all verbatim machinery.
4. **`body.definition.flat_abs`** (hm08-native field, `bara-proof/work/definition_fields.npz`) added at its effective value.
5. **Slope limiter + attenuation repair** — needed *zero* iterations: the composed field flipped nothing on either base (att min 1.000, 0 verts attenuated).
6. **Shipped as a `.target`** (0.1 mm quantisation); the delta was parsed back from the file and the fold gate ran on those shipped numbers.
7. **Export scale:** composed z-range at base scale 1.6946 m → uniform scale **0.99141** → GLB height exactly 1.6800 m. (The preset's `export_scale 0.96` was HIMBO-base-relative, ≈175 cm × 0.96 = 168 cm; 0.99141 is the hm08 equivalent. The preset file itself is unchanged.)

**Direction verification (empirical, before composing):** the four sign-ambiguous sliders were applied solo at +1.0 on the HIMBO base and measured by slice profiles — Lean shrinks all torso bands (−7 to −9% radii), TorsoWaistSize shrinks the waist band (depth −8 to −17%), TorsoHip shrinks hip width (−7 to −11%), LegsThinner shrinks the leg/hip zone. All four: +diff = shrink-ward, matching the batch-1 "Shrink Waist / Shrink Hips" decode, so the preset's positive values multiply the decoded fields directly.

## Vector applied

Raw = preset value; Effective = after the app core's couplings (what was actually composed). 21 of 24 body sliders received geometry; 3 are unapplied (below).

| Slider (canonical id) | HIMBO block / field | Raw | Effective | Applied |
|---|---|---|---|---|
| body.himbo.weight_0_to_1 | Weight 0 to 1 | 0.10 | 0.10 | ✓ |
| body.himbo.lean | Lean | 0.70 | 0.70 | ✓ |
| body.muscle | Muscle | 0.30 | 0.30 | ✓ |
| body.torso.mass | TorsoMass | 0.10 | 0.1036 | ✓ (coupled) |
| body.himbo.torso_waist_size | TorsoWaistSize | 0.55 | 0.55 | ✓ |
| body.himbo.torso_hip | TorsoHip | 0.40 | 0.40 | ✓ |
| body.pecs.size | PecsSize | 0.15 | 0.1554 | ✓ (coupled) |
| body.himbo.pecs_mass | PecsMass | 0.10 | 0.10 | ✓ |
| body.himbo.pecs_width | PecsWidth | 0.10 | 0.10 | ✓ |
| body.himbo.pecs_clavicle | PecsClavicle | 0.40 | 0.40 | ✓ |
| body.himbo.arms_traps | ArmsTraps | 0.10 | 0.10 | ✓ |
| body.himbo.arms_shoulders | ArmsShoulders | 0.10 | 0.10 | ✓ |
| body.arms.delts | ArmsDelts | 0.20 | 0.2084 | ✓ (coupled) |
| body.himbo.arms_biceps | ArmsBiceps | 0.25 | 0.25 | ✓ |
| body.himbo.arms_fore | ArmsFore | 0.35 | 0.35 | ✓ |
| body.himbo.legs_size | LegsSize | 0.15 | 0.15 | ✓ |
| body.himbo.legs_thinner | LegsThinner | 0.50 | 0.50 | ✓ |
| body.himbo.legs_thigh | LegsThigh | 0.10 | 0.10 | ✓ |
| body.himbo.legs_calf_size | LegsCalfSize | 0.25 | 0.25 | ✓ |
| body.himbo.butt_booty | ButtBooty | 0.20 | 0.20 | ✓ |
| body.definition.flat_abs | hm08-native field | 0.30 | **0.1482** | ✓ (attenuated by coupling: tissue.level 0.4 → attenuation 0.494) |
| body.tissue.mass_smooth | TorsoMassSmooth | 0.40 | 0.40 | ✗ unapplied — see debits |
| body.himbo.bubble_butt | BubbleButt | 0.15 | 0.15 | ✗ unapplied — see debits |
| body.himbo.butt_tighten | ButtTighten | 0.30 | 0.30 | ✗ unapplied — see debits |

Field magnitudes: HIMBO-space composed field max 3.3 cm (support >2 mm: 8,934 verts); transferred hm08 field max 2.4 cm; shipped quantised delta max 2.2 cm, 10,381 moved verts.

## Measurements (bara rulers, verbatim — `characters/sen/scripts/bara_machinery.py`)

Graded at base scale on the shipped delta; export column = ×0.99141 (volume measured directly on the GLB positions).

| Measure | hm08 base | Composed (base scale) | Composed (export, 168 cm) |
|---|---|---|---|
| Height (grade station) | 1.6659 m | 1.6665 m | body z-range 1.6522 m as shipped (see Correction — the 1.6800 m figure was the helper-inclusive mesh) |
| Volume | 51.21 L | 46.90 L | **45.70 L** |
| Chest girth | 1.082 m | 1.065 m | 1.056 m |
| Waist girth | 0.696 m | 0.613 m | **0.607 m** |
| Waist width | 0.241 m | 0.213 m | 0.211 m |
| Chest width | 0.467 m | 0.458 m | 0.454 m |
| Neck girth | 0.322 m | 0.323 m | 0.320 m |
| Upper-arm girth | 0.273 m | 0.273 m | 0.270 m |
| Forearm girth | 0.226 m | 0.230 m | 0.228 m |
| Thigh girth | 0.476 m | 0.428 m | 0.424 m |
| Calf girth | 0.340 m | 0.342 m | 0.339 m |
| Delt span | 0.557 m | 0.544 m | 0.539 m |

Scorecard ratios (scale-invariant): M4 chest:waist **1.738**, M5 torso depth ratio 1.177, M3 forearm/upper-arm 0.844, M11 thigh/waist 0.698, M12 7.62 heads tall (base-head stations). Every delta vs base moves the intended lean direction: waist −12% girth, thigh −10%, volume −8.4%, chest nearly held (−1.6%, pecs/clavicle vocabulary), and the forearm is the one growth (+1.9%) — the batch-1 "builder's forearms" intent, ArmsFore 35 being the highest relative arm value.

## Fold gate (shipped quantised numbers — house rule)

Delta parsed back from `targets/body.pyn.target`; face-normal dots over the 26,756 body faces:

| Base | Flips | Min normalised dot | Faces below 0.01 |
|---|---|---|---|
| raw hm08 | **0** | 0.891 | 0 |
| macro hm08 | **0** | 0.928 | 0 |

**PASS** — 0 flips, thinnest margin 0.891 vs the ≥0.01 requirement; no quantised-space repair rounds needed (the lean field is gentle; float-space repair also converged in 0 iterations).

## QA gauntlet (`anthroforge-v2/qa-gauntlet/validate_glb.py` on `pyn_composed.glb`)

`parse: ok · geometry: ok · scale: ok · textures: ok · skin: warn · morphs: warn · contract: n/a` — not blocked. The two warns are the expected signature of this scope: no skin (unrigged static bake) and no morph targets. Full record: `work/qa-gauntlet/`. (That run was on the original helper-inclusive file; the Nov 16, 2026 re-run on the body-only file, `work/qa-bodyfix/`, returns the identical verdicts with max extent 1.6522 m — see Correction.)

## ⚠ Open item — mass (flagged, NOT resolved, per instructions)

The preset follows the person file's body-engineering target **37.2 kg (82 lb)**; Joe's estimate is **~75 kg ±10**. The composed geometry's volume is evidence:

- Composed volume at 168 cm: **45.7 L**.
- At flesh densities (0.95–1.06 kg/L) that volume weighs **43–48 kg** (BMI ≈ 15.4–17.2 — very lean, consistent with this vector).
- 37.2 kg implies density **0.814 kg/L** — below every flesh density (fat ≈ 0.90, muscle ≈ 1.06). Not achievable in flesh at this volume; achievable only if the engineered body is built lighter than flesh (which a biosynthetic spec may intend — the 82 lb figure is an engineering target, not a flesh prediction).
- 75 kg implies density **1.64 kg/L** — denser than any human tissue composite. A flesh body of *this shape* cannot weigh 75 kg; 75 kg at 168 cm would need ~71–79 L of volume, i.e. a substantially larger vector, not this lean one.

The geometry was composed exactly as the preset specifies; the ruling is Joe's.

## Honest debits

1. **Three sliders unapplied.** TorsoMassSmooth (0.4), BubbleButt (0.15), ButtTighten (0.3) exist only in the SOS / NeverNude-variant OSDs, whose base meshes are index-incompatible with the Vanilla base this machinery composes on (SOS base 11,007 verts vs Vanilla 9,346; shared blocks differ in index sets — verified directly). Composing them would require a cross-base field transfer with unquantifiable error; per the lineage rule they are reported, never faked. Their magnitudes are small (at Pyn's values, ≤ ~0.5 cm local displacement on their native base). Partial mitigation: TorsoMassSmooth's *coupling* effect is included — it sets tissue.level 0.4, which attenuated flat_abs 0.30 → 0.1482 in the effective vector.
2. **Base head is placeholder geometry.** No head build in scope; grade stations involving the head (head_w, M1, M12) describe the hm08 base head, not Pyn, and are reported for completeness only. The fennec head vector (incl. 36 cm pinnae) sits in the preset for the later head build.
3. **Unrigged static bake** — gauntlet skin/morph warns are scope, not defects. Rigging is a later stage, as with Sen.
4. **Trap angle 38.9°** is a base-mesh trait the vector barely touches (ArmsTraps 0.1); Pyn has no trap gate in batch-1 (the 20–26° band was Sen's §4.2), so it is measured, not gated.
5. **The waist is extremely lean** (60.7 cm at export) — that is the authored vector (Lean 0.7 + WaistSize 0.55 + Hip 0.4 + LegsThinner 0.5 all pulling the same way), verified against the base at every step, not a composition error.
6. Cosmetic: the build log's "HIMBO-space composed field: max 0.0 cm" line double-applies the Skyrim-unit factor in its *print* only; the true field max is 3.3 cm, verified from the saved `work/pyn_fields.npz`. No geometry impact.

## Files

- `pyn_composed.glb` (0.64 MB) — the composed body, body-only re-export Nov 16, 2026; 165.2 cm as shipped (see Correction). Original helper-inclusive file: `work/originals/pyn_composed.glb` (0.90 MB)
- `targets/body.pyn.target` — shipped quantised delta (the gate ran on this)
- `work/qa_pyn.json` — full numeric record (vectors, gate, grades, mass evidence, gauntlet)
- `work/pyn_fields.npz` — HIMBO source field, float + shipped deltas, attenuation, scale
- `work/build_log.txt`, `work/qa-gauntlet/` — run log + gauntlet report
- `scripts/build_pyn.py`, `scripts/extract_machinery.py`, `scripts/pyn_machinery.py`, `scripts/w3_block.txt`

## HEADS — Pyn head build (Nov 16, 2026)

Built on **base-head-v4** (`base-head-v4/neutral_base_head_v4.glb`) with the
batch-1 §3.1 vector — the fennec species vector verbatim + the one character
delta (BrowScowl −10 → +15). Deliverables: `pyn_head.glb` / `pyn_head.blend`
in this folder; clay renders `renders/head_front.png`,
`renders/head_threequarter.png`, `renders/head_profile.png`. No fur, no body
changes. The body above still carries its placeholder base head; this head
replaces it at assembly.

**Machinery.** Sen's head build (`characters/sen/scripts/build_head.py`)
generalised into `scripts/build_head.py` (identical copies in all three
character folders): same smooth-field deformations, same
proportional-from-neutral convention (factor = (neutral + t·span)/neutral,
preserving the base's deliberate deviations), same [E] index maps calibrated
so Sen's values reproduce Sen's shipped fields. Adaptations for v4: the
teeth are two arcades, not the fused slab (below); ear bases seat against
the *deformed* tissue by material-point delta. `--base` is a parameter —
when base-head-v5 lands, re-run with the v5 GLB and this same vector
(`scripts/pyn_vector.json`). Verify: `scripts/verify_head.py` (stage-F
rulers from `base-head-v4/work/measure_v4.py`, re-checked against the v4
base's own `proportions.json` before use — ZB .5466, MuzzleWidth .2332,
JawWidth .533, RamusDepth .2697 all reproduced); raw numbers in
`work/head_measure.json` + `work/head_verify.json`.

**Side-convention fix (pattern-level, also affects Sen).** The Sen script
keyed left/right off object names (R = +1). In this head frame
`Eyeball_L`/`Ear_L` sit at **+x** (verified: Eyeball_L mean x = +0.1311),
so name-keyed shifts run mirrored — an early run of this build moved
Pyn's eyes *inward* under EyeSpacing +10 before the probe caught it.
Side is now taken from each part's own position. Sen's shipped head
carries the same inversion (his EyeSpacing +30 converged his eyes
0.012/side; his EarSpread shifted mirrored) — flagged for a Sen rebuild,
not silently patched here.

### Measured vs target (L = head length; stage-F rulers)

"Expected" = base × (species target / neutral) — the proportional
convention's prediction; built-vs-expected is the build-accuracy number.
Built-vs-target additionally carries the base's own deliberate deviations.

| Station | Slider | Base | Built | Species target | vs target | vs expected |
|---|---|---|---|---|---|---|
| ZB | CheekWidth −30 | 0.5466 | 0.5223 | 0.520 | +0.5% | +6.6% |
| MuzzleWidth (vertex slab) | MuzzleWidth −25 | 0.2332 | 0.1926 | 0.150 | +28.4% | −6.4% |
| MuzzleWidth (merged section) | MuzzleWidth −25 | 0.2412 | 0.2341 | 0.150 | +56.0% | +10.0% |
| MuzzleDepth | MuzzleDepth −15 | 0.2310 | 0.2103 | 0.185 | +13.7% | −1.6% |
| MuzzleFrac | MuzzleLength +15 | 0.3435 | 0.3582 | 0.360 | −0.5% | −4.4% |
| CraniumWidth (dome shell) | CraniumWidth −10 | 0.4780 | 0.4568 | 0.344 | +32.8% | −0.0% |
| SkullHeight | CraniumHeight +5 | 0.3168 | 0.3229 | 0.316 | +2.2% | −0.0% |
| OrbitDiameter | EyeSize +20 | 0.1500 | 0.1700 | 0.170 | +0.0% | −0.0% |
| EarLength (stage-F) | EarHeight +100 | 0.3690 | 0.9658 | 1.050 | −8.0% | −0.3% |
| JawLength (stage-F origin) | JawLength −20 | 0.7104 | 0.7283 | 0.720 | +1.1% | +5.4% |
| JawWidth | JawWidth −20 | 0.5330 | 0.4997 | 0.372 | +34.3% | +0.8% |
| RamusDepth | JawDepth −25 | 0.2697 | 0.2308 | 0.250 | −7.7% | −4.2% |

Notes on the non-obvious rows:

- **EarLength.** The stage-F ruler tracks the applied field to −0.3%.
  Built ear/L 0.9658 vs the 1.05 species anchor: the proportional
  convention preserves the base's own −5.6% ear deviation. Batch-1 §3.1's
  reconciliation stands — Pyn's absolute 36 cm pinna decision governs at
  assembly if the head builds smaller than L ≈ 34 cm; the slider is a
  fit target, not a violation. (The base→tip ruler reads +12.0% vs its
  own expected — quartile-population migration on the elongated ear,
  the same artefact family as v4's EarLength note; stage-F is the
  stable ruler here.) Cosmetic: the renders show a rim kink partway up
  each pinna — the base ear's rim profile stretched ×2.625, inherited
  geometry amplified, not a field error.
- **JawLength.** The stage-F origin is ear-derived (hinge_y from the ear
  bases) and migrated when the ears grew — ruler artefact. About the
  node hinge the applied ratio is **0.973 measured vs 0.973 expected —
  exact**.
- **MuzzleWidth, two rulers.** The slab ruler (−6.4% vs expected) tracks
  the tissue field; the merged-section ruler (+10.0%) is set by the jaw
  surface at that station, which the muzzle-width field does not move —
  the scope effect BUILD_V4.md's appendix documents.
- **Interorbital.** Eye centres moved +0.008 total, exactly EyeSpacing
  +10's order; the *gap* narrowed −0.012 net because EyeSize +20 grew
  the balls by 0.020. Both numbers are the vectors working as written.
- **MuzzleFrac −4.4%** is denominator composition (ball growth shrinks
  the numerator's reference, CraniumLength/L growth), not a length-field
  miss. ZB +6.6% is zygomatic-band weighting vs the ptp ruler (Sen
  family behaviour). Probes: NoseWidth ratio 0.945 = expected exactly;
  RuffZone −5.7% (RuffVolume −10, correct direction); StopBandZ −0.005
  (StopAngle +15 dip); OcciputY +0.0094 (CraniumLength −5). OrbitRise
  drift −0.0076 with no slider: BrowThickness −40's band field overlaps
  the rise sample window.

### Teeth / jaw

Upper arcade rides the muzzle's metric fields (length/width/taper/
depth); lower rides JawLength about the hinge. The stop pitch is
deliberately not followed by the teeth (profile-posture fiction; see
Brand/Jorge docs). BVH overlap, upper vs lower (in-build, recorded in
`work/head_measure.json`):

| Jaw | −0° (rest) | −10° | −20° | −30° |
|---|---|---|---|---|
| Overlap pairs | 0 | 0 | 0 | 0 |
| Min clearance (L) | 0.0004 | 0.0254 | 0.0487 | 0.0695 |

The raw v4 base reads 27 pairs at rest and 0 at all open angles
(clearances 0.0241/0.0476/0.0692) — Pyn's fields happen to open his rest
occlusion entirely, and his open-angle clearances match the base's own.
Teeth-vs-tissue probe: **1 logical vertex** of TeethUpper sits outside
the tissue (posterior root at (−0.061, 0.001, −0.156), 0.0156 L proud)
— the CheekWidth band pulled tissue in around a mask-edge root vertex;
deep in the mouth corner, not surface-visible. The earlier length-only
follow left 85 verts outside; the metric follow is what fixed the
arcade's side wall.

### Paths / coverage

Full or near-full: all ratio sliders, EyeSize, EyeSpacing, EarHeight,
EarWidth, NoseSize. Partial [E] fields: MuzzleTaper, StopAngle, the brow
band (Projection/Thickness/Shelf/Position/Padding/Scowl — Scowl is a
baked rest expression; the expression system owns the live slider),
EarSpread, EarPlacementHeight, EarTilt, EarTipPoint, RuffVolume (tissue
swell only — the ruff proper is fur, not built). None, recorded:
BrowContinuity (no torus components on a non-hominin head),
EyeForwardness (socket-rig parameter, Sen precedent). Tongue unscaled —
no tongue direction in the batch-1 vector. NeckSocket/NeckSocketDisc
untouched (body interface).

## EAR FIX — fennec ears read upside down (Nov 16, 2026)

Joe's verdict on the head renders above: "the fennec ears are upside
down." Diagnosis first, measured on the pre-fix `pyn_head.glb` (preserved
as `work/originals/pyn_head_pre-earfix_2026-11-16.glb`, with the pre-fix
`head_measure.json` / `head_verify.json` beside it) against the v4 base.

### Diagnosis — what exactly was inverted

1. **The stretched root spike (the inversion proper).** The ear mesh's
   along-axis extent in the base is t ∈ [−0.145, +0.292]: a third of it
   is the sub-base *root*, which in the base ends at z = +0.026, inside
   the skull silhouette. EarHeight scaled t for every vertex, root
   included — at ×2.625 the built root reached t = −0.285, tip
   z = −0.203, clear of Pyn's narrower skull, hanging free beside the
   jaw to chin level and tapering to a point. The visible appendage was
   therefore blade-above + point-down spike below the attachment — the
   vertical mirror of a fennec ear, whose whole mass sits above a short
   narrow stalk. (In profile, the far ear's spike was the detached
   "cup" floating behind the skull.)
2. **Aspect collapse.** EarWidth is a width/*length* ratio in the spec
   (0.55, span 0.35) but was applied as an absolute x-scale (×1.3818),
   independent of the length stretch (×2.94 base→tip measured). The two
   do not compose: achieved W/L went 0.67 (base) → **0.31** (built),
   against a fennec fan's ≈0.55–0.65. The blade read as a narrow
   ribbon, not a fan.
3. **Cup flattening.** No ear slider touches the depth coordinate: cup
   depth span stayed at base scale (≈0.085 L) while the ear grew
   ×2.9, and the floor sat only −0.0053 L behind the rim plane —
   proportionally flat.
4. **Not inverted:** the normalised width profile along the axis
   (base bin 0.43 of max, peak at u ≈ 0.75, tip bin 0.43) already
   matched the fan distribution, and the cup's facing sign was correct
   (floor behind rim = opens forward). The fault was the root stretch
   + the non-composing width, not the profile curve.

**Scope.** The machinery fault is systemic — it bites any vector with a
large |EarHeight| — but Pyn (f_len = 2.625) is the only build in the
regime. Jorge: f_len = 1.00, no stretch (drop-fold regime). Brand:
f_len = 1.1625, root grew +0.024 and stays inside his skull; his width
profile peaks at u ≈ 0.75 and reads badger-appropriate. Sen was built
by his own ancestor script at f_len = 0.84 — his root *shrank* into the
skull (hidden), and his base-heavy measured profile is a round bear ear
read along its diagonal axis (W/L 1.59), not a fan inversion. Flagged
here per instructions; neither rebuilt.

### Fix (builder ear stage; all three generic copies updated, byte-identical)

- **Root preservation in EarHeight:** stretch weight
  `sstep(t/tmax, −0.02, +0.25)` — the sub-base root keeps its base
  length at any factor; only the blade takes the stretch. The root is
  skull interface, the same principle as the untouched NeckSocket.
- **EarFlare stage [E]** (after EarWidth, before EarTipPoint), driven
  by the vector's own length factor: k = sstep(f_len, 1.15, 2.20), so
  ordinary ears (k = 0) keep the calibrated legacy behaviour exactly
  and any long-ear species picks the fan up from its vector alone.
  At k = 1 (Pyn): the blade's width envelope is remapped onto a fan
  profile (base 0.40 of max, peak at u ≈ 0.72, rounded tip 0.45), the
  aspect is restored to W/L 0.58, and the cup is deepened ×1.55
  (blended in over u 0.12–0.35). Root verts (u < 0) are not flared;
  envelope scales are capped to [0.45, 2.60].

Rebuilt with the vector **unchanged** (`scripts/pyn_vector.json`) on
the same v4 base. Fresh clay renders: `renders/head_front.png`,
`renders/head_threequarter.png`, `renders/head_profile.png`.

### Post-fix measurements

- Root: t ∈ [−0.116, +0.772]; root tip z = **+0.045** (base +0.026) —
  the spike is gone; the ears end at the skull in all three renders.
- Fan: max width 0.448 at u ≈ 0.75; **W/L 0.581** (target 0.58; was
  0.31). Width profile by u-bin: 0.37 / 0.51 / 0.62 / 0.66 / 0.82 /
  0.87 / 0.89 / 1.00 / 0.92 / 0.65 — narrow base, upper-third peak,
  rounded tip. Build's flare report: k = 1.0, envelope width
  0.2652 → 0.4221 target (pre-tilt frame).
- Cup: floor−rim −0.0077 L (was −0.0053), still opening forward;
  mid-blade depth span 0.118–0.135 (was ≈0.085).
- Teeth: **0 overlap pairs at 0° / −10° / −20° / −30°**, clearances
  0.0004 / 0.0254 / 0.0487 / 0.0695 — identical to pre-fix (Pyn's rest
  count was already 0 and stays 0).
- Stage-F stations: every tissue / eye / nose station is identical to
  the pre-fix table to the printed digit — the rest of the head is
  untouched. EarLength on the base→tip ruler (the builder's own base
  definition): **0.7716 vs expected 0.7676 (+0.5%)** — the blade takes
  exactly the ordered stretch. EarLength on the stage-F ruler reads
  0.8217 vs expected 0.9687 (−15.2%): that ruler's base is the
  centroid of the *lowest-z* ear verts, which pre-fix was the spike
  tip (inflating the old 0.9658 reading); with the root restored, the
  population is the natural root bottom. The jaw stations moved for
  the same reason — their origin and sample band derive from that ear
  base: JawLength +5.4% → −1.2%, JawWidth +0.8% → −3.6%, RamusDepth
  −4.2% → −0.1% vs expected, while JawLength about the node hinge is
  unchanged (ratio 0.973 = expected) and the teeth clearances are
  identical. Jaw geometry untouched; the spike had been corrupting
  the ear-derived rulers as well.
- Known remainder: the rim kink on the medial rim (inherited base
  geometry, flagged in the original build) is still faintly present,
  less prominent at the new width; the cup is deeper than it was but
  still shallow in absolute terms; the blade's forward lean is the
  base ear's axis, unchanged.
