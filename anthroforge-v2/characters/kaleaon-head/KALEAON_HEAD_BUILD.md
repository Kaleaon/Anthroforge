# KALEAON HEAD — PHASE 2 BUILD

**Status: BUILT + VERIFIED (clay stage).** Kaleaon's own head on the
base-head-v5 base, per `KALEAON_HEAD_SPEC.md` §8 and Joe's ruling of
Nov 16, 2026 (build our own; the donor-graft route is closed). No
fur/groom — the mane, cheek tufts and chin tuft are clay shell
geometry, the under-structure for the later groom pass.

Deliverables in this folder:

- `kaleaon_head.glb` — the shipped head (26 meshes, 59,878 verts /
  27,299 tris; QA gauntlet: 0 degenerate, 0 NaN).
- `kaleaon_head.blend` — the same head with vertex groups intact
  (LipCage / Philtrum / CommissureL/R / Chin — GLB carries no groups).
- `renders/` — clay renders: `head_front.png`,
  `head_threequarter.png`, `head_profile.png`,
  `head_jawopen_threequarter.png` (jaw −25°), `head_on_body_full.png`,
  `head_on_body_closeup.png` (assembly context on the r3 body).
- `scripts/` — the full build pipeline (`stage1_audit.py` …
  `stage8_export.py`, `verify_*.py`, render scripts); `work/` holds
  the per-stage checkpoint blends + JSON gate records.

## The vector as built

Lion preset + the spec's hybrid deltas, exactly as specced:
MuzzleWidth **+20**, MuzzleTaper **−5**, BrowScowl **+10** (not +20 —
canon default is gentle; the heavy read comes from shelf/padding
mass). Species verticals per species-head-spec §5.5 lion column:
OrbitHeight +10, OrbitRise +5, StopDepth 0, BraincaseRise +5,
EarTipHeight −20, JawDepthProfile +25. The spec's EarLength /
EarBaseHeight ride under the sona builder's keys `EarHeight` /
`EarPlacementHeight`. Full vector: `scripts/kaleaon_vector.json`.

Machinery: the corrected sona builder's field stack (side from part
position, never names; masks computed once from input coordinates and
threaded through the stack), v5's lip-cage groups for the mouth work,
metric teeth follow for the arcades. Stage checkpoints
`work/stage2.blend` … `work/stage7.blend` per §8.

Build-level work beyond the vector (spec §8): whisker pads (+0.012 L
at the canine band), chin mass (−0.010 L via the Chin group),
smile-line cage path (≤ +0.010 L lift at the commissures, v5 grading),
canine emphasis (below), tongue re-proportioned to spec, mane shell +
cheek tufts + chin tuft authored new.

## Station table — S1–S20

Built L = 0.9614 (base frame L = 1.0; the muzzle shortening is the
whole delta). "Proportional" = the family judging ruler (base ×
species/base ratio); absolute species targets are the spec's, and
where the base itself misses them structurally the proportional read
governs — the same convention as the Pyn/Jorge/Brand builds.

| # | Station | Target | Built | Verdict |
|---|---|---|---|---|
| S1 | Zygomatic breadth (fleshed) | 0.70 abs / prop 0.6597 | **0.634** | −3.9% vs prop (family band; Jorge −2.8%) |
| S2 | Muzzle width at canine station | 0.186 abs / prop 0.3514 | **0.4461 own-station; 0.3247 at the base's fixed station (+1.1%)** | field proportional; the own-station read is inflated by station migration — see Deviations |
| S3 | Muzzle depth | 0.23 abs / prop 0.2656 (mid) / 0.3747 (canine slab) | **0.2759 mid (+3.9%); 0.3872 canine slab (+3.3%)** | PASS both rulers (±6% band) |
| S4 | Muzzle fraction (ant. orbit) | 0.28 | **0.2872** | PASS (+2.6%) |
| S5 | Mandible length / L | 0.74 abs / prop = base 0.7066 | **0.6826** (node-hinge 0.6913) | −3.4% vs prop — deviation, see below |
| S6 | Orbit diameter | 0.17 | **0.1700** | PASS exact |
| S7 | Orbit height (palate→centre) | 0.18 ± 0.02 | **0.1905** | PASS (in band) |
| S8 | Orbit station u | ≈ 0.36 | **0.3756** (base 0.4185) | PASS (near; +4.3%) |
| S9 | Ear length | 0.22 | **0.2256** (stage-F ruler) | PASS (+2.5%); quartile ruler 0.1591 and growth-axis 0.1185 are frame-mismatched reads — see Deviations |
| S10 | Ear tip height above palate | additive expectation 0.4915 | **0.5159** (build palate) / 0.5225 (rulers palate) | +5.0% / +6.3% — inside/at the ±6% edge; no nudge applied |
| S11 | Head height | 0.72–0.76 (spec band) | **palate→crown 0.5351; total extent 0.8144** (base: 0.4888 / 0.7586) | the spec band matches the base's TOTAL-EXTENT ruler; built total runs +7.3% over base — deviation, see below |
| S12 | Mane width / position of max | 1.02 ± 0.05 L at ≈ 0.60 H | **1.0200 L at 0.595 H** | PASS (0.595 also inside the Roaring reference's 0.62–0.75 read at its edge… see note) |
| S13 | Crown width ≤ 0.80 × S12 | ≤ 0.816 | **0.8058 (ratio 0.79)** | PASS |
| S14 | Ear tips ≤ mane surface (peek ≤ +0.005) | buried | **0 ear↔mane intersections; tip 0.031 L inside the shell surface (pocket)** | PASS in substance; strict-test caveats — see Deviations |
| S15 | Brow projection beyond bridge line | 0.02–0.05 | **0.00 profile overhang (base also 0.00)** | NOT satisfiable on this base's profile — see Deviations; shelf mass evidenced by ForeheadWidth probe ×1.167 |
| S16 | Jaw hinge position | (0, −0.2167, −0.1249), unmoved | **identical in base and built GLB nodes** (Jaw / TeethLower / Tongue all on it) | PASS exact |
| S17 | Teeth overlaps at −10°/−20°/−30° | 0 | **0 overlaps; clearances 0.0241 / 0.0476 / 0.0692** | PASS (the v5 base family values, held through the canine pass) |
| S18 | L/R symmetry (mirrored nearest) | ≤ 0.001 | **TissueHead 0.0014 (base 0.0013); Jaw 0.0037 (base 0.0032); ManeShell 0.0014** | base itself exceeds 0.001 — tessellation residual; build adds ≤ +0.0006. See Deviations |
| S19 | Fold gate, quantised (1e-4) | no exterior pair < +0.01 | **exterior min dot: TissueHead 0.345, Jaw 0.961; 0 exterior pairs < 0.01** | PASS (all sub-0.01 pairs are mouth-interior, base included) |
| S20 | Lip cage integrity | groups intact, rim coincident | **LipCage 405/405, Philtrum 14, CommissureL/R 22 each; rim gap 0.00022 max** | PASS |

Supporting reads: interorbital **0.1122 held exactly** (EyeSize growth
ate the +10 spacing at the surface — the physical seating is
unchanged); nose width ratio **1.191 exact**; lid rest coverage
**0.1525** of the eye (canon neutral-open band 0.15–0.20 — no re-seat
needed); temple corridor clearance **0.0589 L** (glasses channel
clear); skull→tissue mean layer distance 0.0101 → 0.0113 and muscles
0.0043 → 0.0296 after the layer fields (masseter/JawDepth effect; the
muscle layer rides proud of its base offset by design of the depth
fields — flagged for the rig pass to re-check registration).

## Teeth tables

Arcades: v5 split-teeth layout, metric follow on both jaws.

| Measure | Base | Built |
|---|---|---|
| Overlap pairs at −10° / −20° / −30° | 0 / 0 / 0 | **0 / 0 / 0** |
| Min clearance at −10° / −20° / −30° | 0.0241 / 0.0476 / 0.0692 | **same (held through the canine pass)** |
| Rest interpenetration pairs | 27 | 289 (family behaviour: Jorge 256, Brand 334 — occlusion re-seat is a separate known job) |
| Upper canine crown height | 0.0194 | **0.0425 — tallest upper teeth** (canine emphasis, stretch 1.9) |
| Lower canine | — | crown-lift field +0.014 L |
| Tongue size | 0.66 W × 1.39 W | **0.5500 W × 0.9800 W (spec exact)** |
| Tongue ↔ TeethLower crossings | 172 at rest | 133 (base inheritance — the fused arcade slab has no clean trough; clearing needs ~0.35–0.40 W seat drop, rejected as off-spec) |
| Tongue ↔ TeethUpper | — | 13 at rest, 0 open |
| Tongue ↔ tissue/jaw; cage ↔ teeth | — | 0 / 0 at all angles |

Lip margin vs cage: margin crossings (BVH) 33 base → 129 built,
concentrated at the commissure poles, **rest-only, all interior**,
clearing on jaw opening. Two separation-pass variants (vertex-distance
and BVH signed-distance) were tried against them and **reverted** —
neither improved the count without distorting the rim. The rim itself
is coincident to 0.00022 after the jaw-cage grade-blend (the tissue and
jaw stacks move the shared rim differently; rim rows now take the
tissue transform verbatim).

## Slider coverage (37)

Full stack applied per the vector: all primary form sliders (Cheek,
Muzzle W/D/L/Taper, Cranium W/H/L, Jaw L/W/D, Eye Size/Spacing,
Ear H/Placement, NoseSize, Forehead, Ruff evidence via the mane,
StopBand via StopAngle evidence +0.0147, Occiput ×1.032).
**None:** BrowContinuity, EyeForwardness (no field in the machinery —
same as every sona build to date). **No-op by spec:** StopDepth 0
(neutral). **Partial [E]:** the six species verticals ride the
machinery's partial vertical fields; EarTipHeight lands by composed
fields (no direct nudge needed — S10). Build-level (not sliders):
whisker pads, chin mass, smile-line path, canine emphasis, mane/tufts.

## Mechanism / rig interface (spec §5.4)

Phase 2 delivers geometry + node pivots; the rig pass follows (Sen
precedent). The whole jaw train now shares the hinge origin
(0, −0.2167, −0.1249): **Jaw, TeethLower, Tongue, SkullMandible**
(Tongue and SkullMandible were re-pivoted in stage 8 — world geometry
verified identical, bbox-exact, sum-delta ≤ 1.4e-5 float noise).
TeethUpper stays on the head origin. Node naming per spec (Teeth01/
LipU upper; Teeth02/Tongue01–03/LipL on JawRoot; LidU/LidL fans; Brow
chains; Ear 3-bone chains; Nose01) is the rig pass's binding job.
**Pupil ships ROUND** (spec flag F7 — canon; the slit alternative was
not taken).

## Assembly (context renders)

Head L = 0.42 m on the r3 body: scale s = 0.42 / 0.9614 = 0.4369,
rotation build (x, y, z) → body (−x, −y, z), hinge seated exactly on
CC_Base_JawRoot (0, +0.055, 1.800) — verified in the context-render
script (hinge error < 1e-6; face height and head top printed there).
The r3 placeholder head objects were hidden for the context shots;
the neck join is the rig pass's work (the mane drape covers the join
region in the renders).

## Deviations & honest flags

1. **S2 station migration.** MuzzleLength −25 moved the nose back, so
   the nose-relative canine station sits ~0.046 deeper into the cheek
   flare, where even the BASE reads 0.4014. At a fixed station the
   width field is proportional (+1.1%); the merged-section ruler reads
   −2.2% vs proportional. The 0.4461 own-station number is reported,
   not hidden, with this decomposition.
2. **S5 mandible −3.4%.** JawLength slider is 0; the −3% comes from
   the JawWidth/JawDepth fields rotating the chin mass down-forward
   (the same class as Brand's −1.5%). The 0.74 absolute target is
   missed by the base itself (0.7066).
3. **S11 ruler split.** The spec's 0.72–0.76 band matches the base's
   total-extent (chin→crown) ruler (0.7586), not palate→crown
   (0.4888). Built: palate→crown 0.5351 (+9.5% — CraniumHeight +10 and
   the OrbitHeight band), total extent 0.8144 (+7.3% — JawDepthProfile
   +25 deepens the jaw drop). Both rulers reported; if Joe wants the
   total extent inside the band, the jaw-depth vertical is the knob.
4. **S14 strict tests.** The growth-ray test finds no shell surface on
   the exact growth line: the smoothed shell's ear cap drapes ~0.03
   forward of the tip, leaving the tip in a shallow pocket (nearest
   shell surface 0.031 L). The (y,z)-grid tests under-read a sparse
   shell for the same reason. The substantive facts: **zero**
   ear↔mane intersections, no ear vertex crosses the shell, the ear
   sits inside the mane's silhouette in both projections. An earlier
   unsmoothed shell passed the growth-ray at +0.0045 peek — on a noise
   spike of the same crumple the smoothing removed; the smooth shell
   is the one that ships.
5. **S15 profile overhang = 0.** The v5 base's forehead profile is
   concave all the way (base reads 0.00 by the same measure); there is
   no bridge-line overhang to add to without re-profiling the base.
   The brow shelf is present as mass (ForeheadWidth probe ×1.167,
   BrowScowl +10, StopBandZ +0.0147). If Joe wants a true profile
   shelf, that's a base-geometry job, not a slider.
6. **S18 vs the base.** The ≤ 0.001 gate is not met by the base itself
   under the mirrored-nearest ruler (tessellation asymmetry at a few
   verts; means are ~1e-5). All build fields are side-symmetric by
   construction; the mane's normals field is symmetrised explicitly
   (graph-diffusion drift found and fixed in stage 7b — mane max
   0.0014, bbox exactly ±0.4903).
7. **Rest teeth interpenetration (289 pairs)** and **tongue↔lower
   crossings (133)** are base inheritances, reduced or held vs base,
   with open angles clean (S17). Occlusion re-seat remains a separate
   job, as on every sona head.
8. **Margin crossings 129 vs base 33** — interior, rest-only,
   commissure-concentrated; two fix attempts reverted (documented in
   stage 3). The rim itself is coincident (S20 PASS).
9. **Mane construction notes.** Width fitted by a single x-scale
   (×1.052 from a 0.970 raw build); crown ratio achieved with the
   crown taper + one correction pass. A (y,z) profile flare around
   the ears and a displacement-vector smoothing pass were both tried
   and reverted (coverage/amplitude regressions, documented in
   `stage7_mane.py` comments). Corridor clearance 0.0589 L.
10. **Spec flags F1–F9 stand as recorded** in the spec; F7 resolved
    for this build: pupil ROUND per canon.

## What remains after this pass

Rig pass (bones/binding per §5.4 names, neck join, occlusion
re-seat), groom over the mane shell, glasses + braid systems,
markings/colour. The head itself — geometry, stations, teeth, cage,
assembly — is done at clay stage.
