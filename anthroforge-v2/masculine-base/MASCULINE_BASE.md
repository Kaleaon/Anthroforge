# Masculine base variant — hm08 with MPFB macro gender 1.0

Every AnthroForge body proof so far (belly v1–v5.1, the bara strongman
proof) sits on MPFB's default-macro human. Those defaults are
`get_default_macro_info_dict()` — gender 0.5 — whose bust form visibly
fights the pec stack in the strongman build (BARA_PROOF.md
self-critique) and whose proportions caveat every measurement. This
package adds the masculine variant: **the identical default macro dict
with exactly one value changed, gender 0.5 → 1.0**, plus the full
correspondence package the proof pipeline needs, validated by re-running
the belly v1 transfer on the new base.

Macro dict used (read back from the created basemesh in Blender and
verified): gender **1.0**, age 0.5, muscle 0.5, weight 0.5,
proportions 0.5, height 0.5, cupsize 0.5, firmness 0.5, race
{asian 0.33, caucasian 0.33, african 0.33}. Under male weighting the
cupsize/firmness macros are inert (see the chest measurements below).

## Deliverables

| File | What |
|---|---|
| `masculine_base.obj` | The masculine neutral mesh (19,158 verts, base.obj face list, base.obj axis layout, metres) |
| `work/mh_macro_base_masculine.npz` | Raw Blender dump: evaluated positions **as dumped (grounded frame)**, basis positions, the macro dict |
| `work/correspondence_masc.npz` | Correspondence package (below) |
| `body.belly.protrusion.target` | The v1 belly slider re-derived on the masculine base (542 moved verts) — the validation artefact |
| `work/qa_numbers_masc.json`, `work/blender_test_masc.json` | All validation numbers, numpy + Blender |
| `renders/belly_masc_w+0.0_profile.png`, `w+0.5`, `w+1.0_profile`, `w+1.0_front` | Acceptance renders |
| `scripts/dump_masculine_base.py`, `build_masculine.py`, `test_masculine.py`, `export_base_obj.py` | The pipeline (MPFB runs use the isolated env: `HOME=/tmp/af_home xvfb-run blender -b`, MPFB 2.0.18 from the stock zip) |

`correspondence_masc.npz` mirrors the feminine package's keys —
`mh_delta_canonical_m` (the validation transfer), `mh_mask`,
`navel_mh`, `navel_sk`, `h_star`, `sk_landmarks`, `mh_landmarks`,
`belly_face_mask`, `mh_tris` — and adds what the feminine package
lacked: `pos_neutral_canonical_m` (the aligned masculine neutral,
19,158 rows), `pos_raw_baseobj_m`, `pos_macro_grounded_m`,
`frame_offset_m`, `torso_h`, `torso_theta`, `macro_gender`.

## The frame trap, documented properly

Three frames circulate in this project and they are **not**
interchangeable:

1. **base.obj canonical** (all numpy builders): `(x, z_obj, y_obj) × 0.1 m`
   — z (up) is *centred*: −0.845…+0.850 m over all verts (body rows
   −0.817…+0.850).
2. **Blender evaluated dumps**: Blender grounds the human — z spans
   ~0…height. The feminine `mh_macro_base.npz` is stored in this frame.
3. **Blender basis coords**: base.obj under a rigid shift of exactly
   (0, 0, +0.81861 m) (verified componentwise, zero deviation).

The feminine package mixes frames 1 and 2: `correspondence.npz` is
centred, `mh_macro_base.npz` is grounded, and the v1 builder spliced
grounded body rows into a centred array. Its fold scans stayed valid
because the splice is a *rigid translation of the body rows* — face
normals, hence flip counts, are translation-invariant. But any
z-dependent measurement (landmarks, girth bands, torso parameters)
computed across the splice is silently wrong; BARA_PROOF hit exactly
this and had to align per-axis before its girths meant anything.

**This package never mixes frames.** The masculine dump is aligned into
frame 1 before any use, with offset = (median Δx, median Δy,
grounded z-min − raw body z-min) over the body rows:

- masculine dump → offset (0, +0.40 cm, +81.68 cm)
- feminine dump, same method → (0, +0.65 cm, +81.68 cm) — cross-checks
  the method against the known package

Residual after alignment is pure macro deformation: masculine p50
7.0 cm / max 11.2 cm vs raw (feminine: p50 3.2 / max 6.2 cm — gender 1.0
is twice as far from the file base as 0.5, as expected). Residuals at
deformation scale, with no metre-scale outliers, also confirm the
evaluated mesh's vertex order matches base.obj body order on the male
human (the basis check above pins the order independently).

## Landmarks and correspondence

Same operational definitions as v1 (width-profile neck base,
lowest-midline crotch), computed on each base's own neutral:

| | Skyrim source | Feminine (v1 pkg) | Masculine |
|---|---|---|---|
| crotch z (m) | 0.8376 | −0.0447 | −0.0182 |
| neck base z (m) | 1.5910 | 0.5825 | 0.6345 |
| torso length L (m) | 0.7534 | 0.6272 | 0.6523 |
| scale s = L/L_sk | — | 0.8325 | 0.8657 |
| navel vertex | 741 | 4075 | **4151** |
| h* (source-derived) | 0.4625 | 0.4625 | 0.4625 |

Notes: h* is a property of the source morph and is identical across
bases. The navel index differs (4151 vs 4075) because the landmark is
selected by rule — front-most midline vertex at the h* band — and the
male torso's band lands on a neighbouring vertex; same rule, per-base
answer. One asymmetry inherited from v1: the feminine landmarks were
taken on **raw base.obj**, while re-measuring them on the feminine
macro neutral gives L = 0.668 m (its crotch gate dips lower). The
masculine landmarks are taken on the masculine macro neutral — the
only neutral that base has. Anchor comparisons below use each
package's own landmarks, consistently within itself.

## Validation — belly v1 re-run on the masculine base

Method is v1 verbatim (kernel-field init; 60-iteration non-rigid
registration in torso-param space onto the Fat Males fat surface;
canonical belly mask; tight navel pin; targeted fold repair), with the
target side derived on the masculine neutral and fold-checked on that
neutral **and** raw base.obj.

**Anchor.** The slider's endpoint anchor is defined proportionally
(§6.1): source navel displacement 14.38 cm × torso-length ratio s.
Masculine s = 0.8657 → canonical anchor **12.45 cm**, vs the feminine
instance's 11.97 cm. The +0.48 cm difference is not an error — it is
the definition: the male torso is 2.5 cm longer, so the same studied
belly is proportionally deeper. Each instance is graded against its
own canonical anchor with the §8 tolerance of 5 mm.

| Check | Feminine v1 | Masculine |
|---|---|---|
| Anchor (cm) | 11.97 | 12.45 |
| Navel at +1, numpy finished field (cm) | 11.90 | 12.26 |
| Navel at +1, **Blender measured (cm)** | **12.06** | **12.43** |
| Criterion-1 error, Blender (mm) | 0.9 | **0.2 — PASS** |
| Response linearity (Blender) | −12.06/0/+6.03/+12.06 | −12.43/0/+6.22/+12.43 |
| Weight-0 state after load | bit-identical | bit-identical |
| Flips at +1, own base (numpy) | 0 (raw + macro) | 0, min_dot 0.134 |
| Flips at +1, Blender evaluated | 0, min_dot 0.087 | 0, min_dot 0.132 |
| Flips at +1.05, own base | — | 0, min_dot 0.091 |
| safe_max (own base) | 1.0 | 1.0 |
| Surface residual fwd p50 / p95 (cm) | 0.039 / 1.394 | 0.067 / 1.650 |
| Moved verts | 535 | 542 |

Details worth knowing:

- The numpy finished field sits 1.9 mm under its anchor: fold repair
  relaxed the pin peak, and the guarded micro-pin was rejected because
  it would fold on the *raw basis* (see misuse case). The
  Blender-measured value — the number that matters, taken on the real
  macro human — is 12.43 cm, 0.2 mm from anchor. (v1 showed the same
  numpy↔Blender spread in the other direction: 11.90 vs 12.06.)
- Residuals are the same class as v1: bulk near-exact (p50 0.07 cm);
  the p95 tail is the landmark-pin patch plus the flank dead zone, the
  known structural trade (PROOF.md §"Why criterion 3 fails").
- **Misuse case, measured:** applied to raw base.obj *without* the
  masculine macro, the target folds 6 of 1,124 belly faces at +1, all
  in one pinpoint band at h = 0.700–0.702 (from weight 0.7 up;
  raw-basis safe_max 0.5). The dual-base repair ran 300 rounds without
  reaching union-clean — at that band the two neutrals' curvature
  differs enough that no single delta is fold-free on both at full
  weight. This is precisely what "per-base instance" means; on its own
  base the instance is clean through +1.05.
- **Negative pole** folds (106/1,124 faces at −1 in Blender), same as
  v1: the source morph is one-sided; a production decrease needs its
  own authored target. Unchanged from the feminine instance.
- **Chest fat is part of the v1 slider — now visible.** The canonical
  mask reaches h ≈ 0.81 at the front, and the Fat Males source carries
  chest fat, so both instances add forward mass at chest height
  (mean forward delta at h 0.66–0.78: feminine +1.8 cm, masculine
  +1.0–1.2 cm). On the feminine base it merged invisibly into the
  bust; on the masculine base it reads as a soft fat-male chest mound
  at +1 — faithful to the source sculpt, but flagged: a future
  mask revision may want the chest band gated separately from the
  belly proper.

## Base proportions — old vs new

Identical method per base: stations are fractions of each base's own
crotch→neck length (chest h 0.78, waist h = h*, hip h 0.12, shoulder
h 0.93); slabs ±1.25 cm; girth = convex-hull perimeter of the slab
under a torso-only radial gate (r < 0.215 m, the v4 precedent — wider
gates catch deltoid/arm cross-sections and poison the hull); widths
are 1–99 percentile extents. Mound prominence = peak front-band
surface (99th-pct y within ±11 cm of the axis) over h 0.68–0.88 above
the line joining the h 0.62 and h 0.88 references — a localised mound
over the chest's own slope; a flat pec plane scores near the raw
base's value.

| Measure (m) | Feminine (gender 0.5) | Masculine (gender 1.0) | Δ | Raw base.obj (ref) |
|---|---|---|---|---|
| Height | 1.659 | 1.729 | **+0.070** | 1.666 |
| Torso length L | 0.668* | 0.652 | −0.016 | 0.627 |
| Chest girth (h .78) | 1.079 | 1.094 | +0.015 | 1.027 |
| Waist girth (h*) | 0.707 | 0.759 | +0.052 | 0.684 |
| Hip girth (h .12) | 0.944 | 0.939 | −0.005 | 0.963 |
| Chest width | 0.413 | 0.404 | −0.009 | 0.397 |
| Chest depth | 0.213 | 0.226 | **+0.013** | 0.190 |
| Shoulder width (h .93) | 0.429 | 0.469 | **+0.040** | 0.444 |
| Hip width | 0.354 | 0.344 | −0.010 | 0.347 |
| Chest mound prominence | 0.022 | 0.015 | −0.007 | 0.011 |

\* Feminine L here is re-measured on its macro neutral; the feminine
correspondence package's own landmarks (on raw base.obj) give 0.6272 m.

Read: the masculine base is 7 cm taller, 4 cm broader at the
shoulders, deeper through the chest (+1.3 cm) with a flatter front
(mound prominence 2.2 → 1.5 cm, against the raw base's 1.1 cm pec
plane — the bust form that fought the strongman's pec stack is
largely gone, though muscle-0.5 pecs remain), wider at the waist,
and narrower at the hips (−1.0 cm width, girth level). Chest girth
still rises slightly despite the flatter front, carried by ribcage
depth. Full per-station profiles are in `work/qa_numbers_masc.json`.

## Migration notes — what it costs to move the proof suite

**Every existing `.target` is a per-base instance. None of them can be
applied to the masculine base.** A target is a delta against a
specific neutral; the two neutrals differ per-vertex by up to 11.2 cm,
so a feminine instance on the masculine human double-counts the macro
difference (and vice versa — see the measured misuse case above:
6 folded faces even for the gentle v1 field). Affected instances:

- Belly lineage: `body.belly.protrusion` v1–v5.1 and its components
  (sag v2/v3, distribution v4, limb v5, terminal v5.1) in first-proof/
- Bara proof: `body.muscle`, `body.chest.width`, `body.tissue.strongman`
  and their combined target in bara-proof/

**What carries over unchanged:** the canonical slider *records* —
IDs, semantics, endpoint anchors, ranges. Anchors are defined from
source data × per-base torso ratio, so a record re-derives its
instance on any base; the record itself is base-independent by design.

**Re-derivation cost, honestly:** the builders are all script-driven
and parameterised by the base package, so migration is re-runs, not
research. The expensive machinery (source fields, kernel CV, source
registration surface) is base-independent and reusable as-is. Per
slider, the target-side work is: torso params + mask (~seconds),
registration (~1 min), fold repair (seconds to ~10 min when the union
gate fights — v1-masc's 300-round repair dominated its 52 s build),
plus the Blender acceptance pass (~1 min + renders). The belly
lineage is sequential (v3 builds on v1's field, v4 on v3, v5 on v4,
v5.1 on v5), so the full chain is a single ordered re-run — budget
roughly an hour of machine time end-to-end including QA, most of it
fold repair and renders. The bara proof's three components are
independent of each other and cheaper. The correspondence package in
this folder is the only new artefact the suite needed; everything
downstream is pointing existing builders at it.

**Deriving on the neutral matters.** Feminine v1 was derived on raw
base.obj and *applied* over the default macro; the ~1–2 mm
numpy↔Blender spread at its landmark is that slop made visible. The
masculine instance is derived on the neutral it will sit on, and its
Blender error is 0.2 mm. Future instances on either base should
follow the masculine pattern: derive on the macro neutral, check on
raw only as a misuse bound.

## Caveats

- Landmark definitions remain operational (width-profile neck,
  lowest-midline crotch); s carries ≈ ±0.07 uncertainty, absorbed at
  the landmark by the pin, inherited off-landmark as in v1.
- The masculine neutral still carries MPFB's muscle-0.5 pec form and
  the feminine-default's other 0.5 macros (age, weight, proportions)
  by design — this package changes gender only, nothing else.
- Provenance unchanged: the validation target is derived from
  study-only learned data, is internal-only, and is labelled as such
  in its file header. The base mesh and correspondence are MPFB/CC0
  hm08 derivatives.
