# Definition geometry instances — the definition family gets relief fields

*Nov 12, 2026. Companion to BARA_PROOF.md, MUSCLE_TISSUE_MODEL.md
(anthroforge-v2/) and the coupling validation. Build:
`scripts/build_definition.py`; renders:
`scripts/render_definition.py`; records:
`body.definition.<name>.slider.json` here +
`makehuman_hm08` instances registered in the anthroforge-app
slider library. All numbers: `work/definition_numbers.json`,
`work/blender_definition_numbers.json`. Study-only.*

## What shipped

The Muscle×Tissue evaluator has always attenuated definition
sliders *numerically*; the app library held definition records
whose only instance was the Skyrim HIMBO source. Now all four
definition sliders have **hm08 geometry instances** — relief fields
(micro-displacement, millimetre amplitudes) whose feature depths
are *anchored to the source sculpts* and whose submersion under
tissue reproduces the evaluator's predictions on the mesh:

| slider | target | moved verts | canonical depth at 1.0 | relief peak |
|---|---|---|---|---|
| body.definition.flat_abs | body.definition.flat_abs.target | 197 | **2.70 mm** flattening (+ 0.91 mm linea-alba groove) | 5.7 mm |
| body.definition.traps_valleys | body.definition.traps_valleys.target | 488 | **−0.94 mm** signed dip increment | 3.8 mm |
| body.definition.pecs_crease | body.definition.pecs_crease.target | 336 | **1.21 mm** crease dip | 4.2 mm |
| body.definition.back | body.definition.back.target | 624 | **1.56 mm** relief RMS (furrow component 0.23 mm) | 10.0 mm |

All four compose at raw 1.0 over the muscle, strongman and
gachidebu substrates with **0 flipped triangles** (raw and macro
bases), individually and as a combined set over gachidebu.

## Method: transfer for shape, closed-loop calibration for amplitude

Same two-stage discipline as the bara proof, with one upgrade.
The field's *shape* comes from the source sculpt through the
pipeline's torso kernel machinery at the slider-lab feature kernel
(σ_h 0.018, σ_arc 0.014 — the definition-tuned kernel from the
coupling validation), blended torso-only through the bara region
weights. The field's *amplitude* is then **closed-loop
calibrated**: a canonical station measure (a feature-depth
instrument, defined per slider below) is evaluated identically on
(a) the bare source base + source field at 1.0 and (b) the hm08
muscle substrate + transferred field at 1.0, and the field is
scaled so (b) equals (a) × the pipeline frame scale s = 0.7902
(source L 0.7937 m → hm08 L 0.6272 m). The coupling validation
graded *ratios* on uncalibrated transfers; these instances are
anchored in absolute millimetres. Kernel cross-validation
(leave-one-out position recovery on the footprint): median
0.08–0.14 cm, p95 0.20–0.34 cm per slider — the shape transfer is
sub-millimetre at the median.

**Cross-check source that wasn't:** Atomic Muscle's full decode
contains no definition-family material at all (verified by keyword
scan: no valley/crease/definition/flat/v-line/abs entries; its 12
user-facing sliders are macro/state morphs). The definition
vocabulary is HIMBO-only, consistent with AM_VS_HIMBO's
granularity finding — AM switches states, HIMBO sculpts relief.

## Per-slider

### body.definition.flat_abs — HIMBO - BodyTorsoFlatAbs (Vanilla set)

Station: over the footprint's core h-band, the **flattening
depth** = mean radial increment of the flank bins (|θ| 0.30–1.00)
minus the centre bins (|θ| ≤ 0.30) on the front; plus the
**linea-alba groove** = segment band (|θ| 0.12–0.35) minus midline
(|θ| ≤ 0.05).

- Source: support 484 verts, peak 9.0 mm, flattening depth
  **3.45 mm** → hm08 target **2.72 mm**; groove 1.17 mm → 0.92 mm.
- Kernel transfer alone: depth 2.56 mm, groove only **0.42 mm** —
  the kernel smooths the narrow midline groove away, exactly the
  "sources are thin" case the brief anticipated.
- **Groove authored** (slider-lab authoring, disclosed in the
  record): a midline radial Gaussian (σ_θ 0.045) windowed to the
  source footprint's core band, solved jointly with the transfer
  scale as a 2×2 linear system against both station targets, plus
  one refinement pass (the station windows ride on the combined
  field's own footprint). Solved: transfer scale 0.900, groove
  peak 0.65 mm.
- Final: depth **2.70 mm** (target 2.72, −0.7%), groove
  **0.91 mm** (target 0.92, −1%), peak 5.7 mm, 183 verts over
  0.2 mm (197 stored).

### body.definition.traps_valleys — HIMBO - BodyArmsTrapsValleys (Vanilla set)

Station: the coupling validation's **dip_theta** (shoulder-bin
minus core-bin mean radius over the footprint, both sides) — kept
deliberately, for continuity with the validation that graded this
feature. It is a *signed* measure and reads **negative** for
valleys on both frames (the carved field loads the window's
shoulder bins as much as its core); calibration is by signed
ratio with a sign-match guard.

- Source: support 885 verts, peak 7.7 mm, signed depth
  **−1.19 mm** → target **−0.94 mm**.
- Transfer: −0.79 mm — *identical* to the coupling validation's
  implied raw-1.0 increment (−0.79), an independent reproduction
  check on the transfer. Calibration scale 1.182.
- Final: **−0.94 mm**, peak 3.8 mm, 419 verts over 0.2 mm
  (488 stored).

### body.definition.pecs_crease — HIMBO - BodyPecsCrease (Vanilla set)

Station: **dip_h** — the radius-profile dip across the footprint's
h-extent at chest angles (|θ| ≤ 0.5), the validation's crease
instrument.

- Source: support 267 verts, peak 8.5 mm, depth **1.53 mm** →
  target **1.21 mm**.
- Transfer: 0.70 mm — the kernel under-carries this narrow crease
  the most of the four; calibration scale **1.726** restores it.
  (The scale is large because the *measure* is narrow-band; the
  field's peak after calibration is 4.2 mm, well inside the source
  sculpt's own 8.5 mm peak envelope.)
- Final: **1.21 mm**, 312 verts over 0.2 mm (336 stored).

### body.definition.back — HIMBO - Body HPTorsoBackDefinition (SOS HP set)

The sourcing problem, stated plainly: the Vanilla HIMBO set has
**no** back-definition block. The block exists in `SOS.osd`
(1,519 verts) and as the HP twin in `SOS HP.osd` (1,065 verts,
identical sculpt, different tessellation) — but SOS-family sets do
not index the Vanilla base (verified: same-named blocks carry
different index sets), and `SOS.nif` defeats the pipeline's
extractor. `SOS HP.nif` extracts cleanly (14,597 verts) and
**position-verifies 1:1**: every Vanilla vertex has an
exact-position twin in the HP base (NN median 0.000 units), and
the HP set's own torso blocks land in their expected regions
(FlatAbs 99% front, VLine 74% front, BackDefinition 0% front).
The instance therefore transfers the HP twin block from the HP
base through the same kernel machinery, on the same frame scale.

Station: probed both candidates on the source. The
**spinal-furrow** contrast (paraspinal minus midline bins) reads
only **0.29 mm** — the source sculpt is mostly broad lat/scapular
shaping, not a carved furrow. The **relief RMS** (standard
deviation of the binned radial-increment profile across the back)
reads **1.98 mm** and is the honest canonical amplitude; it is
the calibration measure, with the furrow reported as a component.

- Source: support 859 verts, peak 19.5 mm, RMS **1.98 mm** →
  target **1.56 mm** (furrow component 0.23 mm).
- Transfer: RMS 2.24 mm (the broad field over-carries profile
  variance slightly); calibration scale 0.698.
- Final: RMS **1.56 mm**, peak 10.0 mm — the peak is the source
  sculpt's broad lat sweep, not a spike; 539 verts over 0.2 mm
  (624 stored).

## Attenuation vs prediction — the geometry half of the coupling validation

Protocol (the validation's): the field's dip increment is measured
on a substrate twice — composed at the evaluator's **effective**
value for that build, and naively at raw 1.0 — over the strongman
build (tissue level 0.7575) and the gachidebu build (level 0.945,
rebuilt in float exactly as the validation built it: 17 repair
iterations, 653 verts touched, matching its record). Muscle 0.80,
authored raw 1.0 throughout.

| slider | strongman predicted | strongman measured | gachidebu predicted | gachidebu measured |
|---|---|---|---|---|
| flat_abs | 0.338 | **0.338** | 0.230 | **0.230** |
| traps_valleys | 0.848 | **0.848** | 0.805 | **0.804** |
| pecs_crease | 0.698 | **0.698** | 0.597 | **0.597** |
| back | 0.756 | **0.756** | 0.673 | **0.673** |

Measured = coupled dip ÷ tissue-0 dip. Worst deviation 0.001.

**The honest half of the finding — fill factor ≈ 1.00.** The
naive composition (field at raw 1.0 over the tissue substrate)
shows the *same* dip increment as at tissue 0, for every slider
and both builds (fill factors 0.999–1.000). Additive tissue does
not measurably fill millimetre relief at these amplitudes: the
tissue field's own surface is smooth at the dip stations, so the
increment passes through untouched. Submersion in the composed
character is therefore carried **entirely by the effective
value** — which is precisely the model's claim (attenuation is an
evaluation-stage phenomenon, MUSCLE_TISSUE_MODEL §2), now
confirmed geometrically for all four definition sliders at
calibrated amplitudes. A pipeline that instead expected the
tissue mesh to blur authored relief would be disappointed; ours
never asks it to. (As in the validation, absolute dips on the
gachidebu substrate are not the instrument — its macro surface is
far rougher than a 1–3 mm feature; increments are.)

## Fold gates

Each field at raw 1.0 composed over each substrate, face-normal
dot products against the undeformed base, raw base + MPFB macro
base, numpy:

| substrate | raw flips | raw min dot | macro flips |
|---|---|---|---|
| muscle system | 0 | 0.008 | 0 |
| strongman | 0 | 0.008 | 0 |
| gachidebu (float rebuild) | 0 | 0.0006 | 0 |
| all four combined over gachidebu | 0 | 0.0006 | 0 |

Blender evaluated-mesh check on the three render states:
tissue 0 → 0 flips (min dot 0.222); strongman → 0 (0.084);
gachidebu render state → **2 flips, which are not ours**: a probe
with the definition keys at 0 shows the same 2 flipped triangles
(z ≈ 1.486–1.487, upper chest) in the *shipped* coupling target
alone — its 0.1 mm-quantised export flips two marginal faces of
the flip-free float build — and the definition set at full 1.0
adds none. Flagged for the coupling target's next re-export, not
fixed here (not this task's artifact).

## Renders

`renders/def_{tissue0,strongman,gachidebu}_{front,back}.png` —
torso close-ups, Workbench cavity shading, one authored value
(raw 1.0) shown at tissue 0, and at the evaluator's effective
values over the two tissue builds. Read them honestly: calibrated
definition is 1–3 mm of relief on a ~60 cm torso, so it reads as
gentle shading — a faint linea alba and navel shadow at tissue 0,
visibly submerged under the gachidebu belly (front view), the
valleys and back relief softening but present at strongman
(eff 0.70–0.85). The station numbers above are the grading
instrument; the renders show placement and scale honesty. The
feminine base's bust form under the crease field is the known
substrate property (masculine-base work is a separate task).

## Limits

- Relief here is a (dr, dz) torso-kernel transfer, not a
  normal-projected sculpt: at these amplitudes the distinction is
  below the kernel's own CV, but a future high-frequency detail
  pass (pores, striations) would need true normal-space authoring.
- Calibration is single-station per slider (two for flat_abs).
  A field can in principle game one station; the kernel CV and
  the fold gates are the guards, and the renders are the eyeball
  check.
- The back instance's provenance crosses source sets (SOS HP
  twin block) — justified by the 1:1 position verification and
  recorded in both JSONs, but it is a transfer *between sibling
  bases*, one notch below the other three's same-base transfers.
- Valleys' canonical depth is a signed instrument reading, not a
  physical groove depth; anyone re-grading should use the same
  dip_theta definition (it is the validation's, and it is in
  `scripts/build_definition.py`).
