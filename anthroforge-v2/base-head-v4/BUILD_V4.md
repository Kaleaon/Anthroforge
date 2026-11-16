# Neutral Base Head v4 — Build Notes

**What v4 is:** v3's geometry, finished — not a rebuild. One subdivision level +
guarded sculpt-smoothing over the whole head, the jaw seam re-cut on the smoothed
surface, the fused teeth slab split into separate upper/lower arcades, and the
skull/muscle layers and vertex groups regenerated on the denser mesh. Every
proportion ruler is v3's (identical stage-F rulers, L = nose tip → occiput = 1.0,
targets = species-head-spec neutral column, unchanged).

**Verification status:** this doc was written after the fact from the build logs
(`work/build_log_a.json`, `work/build_log_b.json`, `work/final_measure_v4.json`),
the build scripts (`work/build_v4.py`, `work/build_v4b.py`), and an independent
re-measurement of the shipped GLBs (QA gauntlet + raw accessor dump, v3 and v4).
Where the logs and the geometry disagree, the geometry wins and the disagreement
is flagged below.

## Pipeline (as logged)

1. **Stage A — subdivide + smooth** (`build_v4.py`, `build_log_a.json`).
   Tissue + jaw merged (1,439 verts pre-subdivision) → one `subdivide_edges`
   pass (cuts = 1, grid fill) → 5,660 verts / 5,656 faces. Relaxation was
   *guarded*, by design:
   - **Original v3 vertices were pinned** as measurement anchors; only
     subdivision-new vertices relaxed (Taubin). Max displacement: new verts
     0.012, originals 0.00535 (the originals' allowance covers the jaw-seam
     band re-cut and a strong sculpt-relax in named facet regions).
   - **Ruler guards:** after relaxation, positions were clipped to v3's
     stage-F ruler-band extents, so smoothing could not extend any measured
     band beyond v3's.
   - Jaw seam **re-cut** on the smoothed surface (hinge test with tiebreak
     flips). Hinge moved slightly: (0, −0.2167, −0.1278) → **(0, −0.2167,
     −0.1249)**. Palate line unchanged (pal_z −0.1799 in both).
   - Split result: tissue 3,756 verts, jaw 2,023 verts; ears 285 verts each.
2. **Stage B — teeth split, layers, groups, export** (`build_v4b.py`,
   `build_log_b.json`). Teeth split (below); skull layers regenerated with
   v3's stage-D recipes on the dense mesh (Skull 3,197 v, SkullMandible
   2,023 v, Muscles 735 v — .blend only, as in v3); 20 vertex groups
   regenerated; GLB exported from the 21 surface objects.

## Teeth split — confirmed from the geometry

v3 limitation 1 (one fused slab spanning both jaws; intersects on jaw-open) is
**fixed**.

- **Method:** a scan over candidate split planes (final plane a = 0.09,
  b = 0.2696) with Sutherland–Hodgman polygon clipping. A plane was accepted
  only if a BVH overlap test at jaw rotations −10° / −20° / −30° returned
  **zero overlapping triangle pairs** and the waist error was < 0.002.
- **Result in the shipped GLB:** the single `TeethArcade` mesh is gone,
  replaced by two meshes —
  - `TeethUpper`: 475 logical verts / **724 tris**, node at identity →
    skull-fixed.
  - `TeethLower`: 614 logical verts / **1,012 tris**, node carrying the
    **exact Jaw node translation** (0, −0.1249, +0.2167 in glTF axes) → the
    lowers sit on the jaw pivot and articulate with it.
  - Combined 1,736 tris vs the v3 slab's 1,368 (+368: the clip's new
    boundary faces along the split plane).
- **Clearance at jaw-open** (BVH, build log): 0 overlap pairs at −10° /
  −20° / −30°, min clearances 0.0241 / 0.0476 / 0.0692 L. The v3 jaw-open
  intersection does not occur at any tested angle.
- **Caveat:** `TeethLower` is a *sibling* of `Jaw` in the GLB scene graph,
  not a child — it shares the pivot by copied translation. A consumer must
  apply the jaw rotation to both nodes (or parent TeethLower under Jaw on
  import). Same "pivot is a node transform, no armature" scope as v3.

## Smoothing — confirmed, with numbers

One subdivision level landed everywhere it was supposed to (triangle counts
×4.0 on tissue, jaw, ears):

| Mesh | v3 tris | v4 tris | v3 GLB verts | v4 GLB verts |
|---|---|---|---|---|
| TissueHead | 1,828 | 7,320 | 1,023 | 14,724 |
| Jaw | 952 | 3,800 | 1,904 | 7,600 |
| Ear_L / Ear_R (each) | 134 | 536 | 268 | 1,072 |
| **Whole GLB** | **11,280** | **20,792** | **16,286** | **41,389** |

(GLB vert counts are split-vertex counts from the exporter; logical .blend
counts are in the build logs — tissue 3,756, jaw 2,023, ears 285 each.)

Surface quality (final unified rulers, `final_measure_v4.json`):

| Metric | v3 | v4 | Change |
|---|---|---|---|
| Cheek facet angle | 15.97° | **9.08°** | −43% |
| Cheek vertex-normal step | 19.77° | **11.33°** | −43% |
| Jaw seam roughness | 0.0473 | **0.0259** | −45% |
| Seam loop points | 61 | 119 | denser loop |

The faceting and the zigzag jaw-cut edge that v3's limitation 2 flagged are
substantially reduced by measurement. Whether the surface now *reads*
"scan-grade" is a visual judgement — see debit 1: v4 shipped with no renders,
so that call has not been made.

## Proportion gates — v3 vs v4 side by side

Targets and rulers identical in both. "±6% band" is the spec gate; "≤ v3
|dev|" is the stricter rule the v4 build set itself
(`proportions.json`: *"Gates must hold |dev| ≤ v3's |dev|"* — **it does not
fully hold: 11 of 14**).

| Measure | Target | v3 dev | v4 measured | v4 dev | ±6% band | ≤ v3 \|dev\| |
|---|---|---|---|---|---|---|
| Zygomatic breadth | 0.58 | −5.8% | 0.5466 | −5.8% | ✓ | ✓ |
| Cranium width (dome shell) | 0.36 | +32.8% | 0.478 | +32.8% | ✗ | ✓ |
| Muzzle width | 0.17 | +26.9% | 0.2332 | **+37.2%** | ✗ | **✗ drifted** |
| Muzzle depth | 0.20 | +15.5% | 0.231 | +15.5% | ✗ | ✓ |
| Skull height (dome rise) | 0.31 | +2.2% | 0.3168 | +2.2% | ✓ | ✓ |
| Muzzle fraction (ant. orbit) | 0.33 | +4.1% | 0.3435 | +4.1% | ✓ | ✓ |
| Orbit diameter | 0.15 | 0.0% | 0.150 | 0.0% | ✓ | ✓ |
| Interorbital | 0.19 | −40.9% | 0.1122 | −40.9% | ✗ | ✓ |
| Orbit height | 0.17 | +1.2% | 0.172 | +1.2% | ✓ | ✓ |
| Orbit rise | 0.12 | +69.6% | 0.2035 | +69.6% | ✗ | ✓ |
| Ear length | 0.40 | −2.8% | 0.3776 | **−5.6%** | ✓ | **✗ drifted** |
| Jaw length | 0.74 | −3.3% | 0.7128 | **−3.7%** | ✓ | **✗ drifted** |
| Jaw width | 0.40 | +33.4% | 0.533 | +33.2% | ✗ | ✓ |
| Ramus depth | 0.28 | −10.5% | 0.2697 | −3.7% | ✓ **gained** | ✓ |

**Band count: v4 holds 8 of 14 inside ±6%** — Ramus depth moved into the
band (−10.5% → −3.7%) as a side effect of the seam re-cut and jaw smoothing,
and nothing fell out of the band. (v3's notes claim 8 of 14 for v3; its own
table's ✓ marks count 7 — Ramus was out — so by the table v4 gains one.)

The three drifts, honestly:

- **MuzzleWidth +26.9% → +37.2%** (0.2158 → 0.2332) is the one real
  regression candidate. It was already a deliberate partial in v3; v4 moved
  *away* from target. The build's own diagnostics (`work/diag_e.py`,
  `work/diag_f.py`) probed exactly this — vertex-extremum ruler vs
  surface-true section width on the denser mesh — but **no verdict was
  saved**, so it is unresolved whether the muzzle surface genuinely widened
  under relaxation or the vertex ruler simply samples the subdivided mesh
  differently. Do not treat either way until it's re-measured with the
  section ruler.
- **EarLength −2.8% → −5.6%** (0.3889 → 0.3776) is documented in the build
  script as a **ruler artifact, not a shape change**: a subdivided but
  *unrelaxed* ear already reads 0.3778, because the ear ruler's base is the
  centroid of the lowest n//7 verts and densification migrates that sample
  population (the hinge frame derives from the same centroid family). Note
  the stage-A script also records a plan to *hold ears at v3 density* for
  exactly this reason — **the shipped GLB's ears are subdivided anyway**
  (134 → 536 tris; ear group verts 76 → 285), so the hold did not survive
  into the final build. Consequence is the ruler reading above; the ear
  geometry itself is v3's shape at 4× density.
- **JawLength −3.3% → −3.7%** (0.7156 → 0.7128): a 0.4-point drift,
  inside the band, consistent with the seam re-cut moving the jaw's
  measured extent slightly. Not investigated further by the build.

All other measures are bit-identical to v3 (the pinned-anchor + ruler-guard
design did its job), including the carried-over deliberate deviations:
**Interorbital stayed at the physical socket seating, 0.1122** — v4 did not
use the spec anchor 0.19 and did not move the eyes at all (eye centre
(0, 0.0815, −0.0079) in both). The v1/v3 tension stands exactly where v3
left it: 0.19 + Ø 0.15 eyes implies a centre spacing that lands outside
this skull; **a spec ruling is still owed**, and v4 neither forces nor
prejudges it. Cranium width, Orbit rise, Jaw width and Muzzle depth remain
out of band for the same bone-anchor-vs-fleshed-measure reasons documented
in v3's notes; smoothing was never going to move them and didn't.

## What v4 did not address

- **Lip line (B12, `model-craft/b12-face/FACE_CRAFT.md` §1.4, F-M7):** B12
  found v3's lip line is a *crease in a closed surface*, not a structure —
  without a closed elliptical loop cage (≥ 3 loops, poles only at the
  commissures) there are no lip sliders, "only crease smears." **v4 did not
  build the cage.** The lip line was used as a landmark during relaxation
  masking and nothing more; it remains a crease. This is now the head's
  biggest known structural gap and is v5 work.
- **No rig**, same as v3: QA gauntlet reports no skin, 0 morphs. Jaw
  articulation is the Jaw node's transform (plus TeethLower's copied
  pivot, above).
- **Skull/muscle layers** exist only in the .blend (24 objects), not in
  the GLB (21 surface objects) — same export scope as v3.

## QA gauntlet (independent re-run)

`qa-gauntlet/validate_glb.py` on the shipped GLBs:

- **v4:** parses clean — 21 meshes, 41,389 v / 20,792 t, no skin, morphs 0,
  **0 degenerate triangles, 0 NaN**, world extent 1.0977 m.
- **v3 (control):** 20 meshes, 16,286 v / 11,280 t, 0 degenerate, 0 NaN,
  extent 1.0977 m — identical extent confirms the L = 1.0 frame and the
  ear-tip overshoot that defines it are unchanged.

## Honest debits

1. **No renders.** v3 shipped five; v4 shipped none. Every claim in this
   doc is numeric. The smoothed surface, the re-cut seam, and the split
   arcade have never been visually inspected — produce front / side /
   three-quarter / jaw-open renders before calling the finish bar cleared.
2. **MuzzleWidth drift is unexplained** (see above) — the one place v4 may
   be worse than v3 in substance, not just in ruler behaviour.
3. **The build's own gate rule failed**: `all_gates_within_v3_dev: false`
   in the build's own `proportions.json`. 11/14 held; the 3 drifts are
   itemised above rather than averaged away.
4. **TeethLower parenting** is by copied translation, not hierarchy
   (see Teeth split caveat).
5. **Ear-density plan vs shipped state disagree** (stage-A comment vs
   GLB) — flagged above; harmless to shape, confusing to provenance.
6. Housekeeping: `neutral_base_head_v4.blend1` and
   `work/stage_v4a.blend` (+ its `.blend1`) are duplicate-weight backups
   in the deliverable folder.

## Verdict

v4 completes v3's two named finish items: the faceting/seam problem is
measurably reduced (−43% facet angles, −45% seam roughness at 4× density,
anchors pinned so no passing gate moved), and the teeth are now a real
two-arcade split that clears at every tested jaw angle — v3 limitation 1
is closed. It holds 8/14 gates in the ±6% band (one gained), at the cost
of one unexplained muzzle-width drift against its own no-drift rule. The
head's open structural item is no longer surface finish — it is the **lip
loop cage** (B12 F-M7), plus the still-owed **Interorbital spec ruling**.

## Appendix — MuzzleWidth verdict: ruler artefact; the muzzle did not grow

*(Diagnosis appended after first publication. Debit 2 above is resolved by
this section: the drift is in the ruler, not the geometry. Script:
`work/diag_g_muzzle_verdict.py` — gate replication, surface-true sections,
subdivided-unrelaxed control, BVH signed distances; blends measured as the
gate measures them, geometry untouched.)*

**Verdict: artefact.** The head's true width at the muzzle station is
unchanged to four decimals. The gate's +0.0174 L reading increase
(0.2158 → 0.2332) decomposes into densification sampling (+0.0130), a
capped relax of subdivision-new verts under a wider-scope guard
(+0.0044), and zero from stage B.

Both methods, both versions (L units; at the file's scale 0.001 L ≈ 1 mm):

| Measure | v3 | v4 | Δ |
|---|---|---|---|
| Vertex-slab ruler, **TissueHead only** (the gate as defined) | 0.2158 | 0.2332 | **+0.0174** |
| Vertex-slab ruler, merged tissue+jaw | 0.2418 | 0.2418 | 0.0000 |
| Surface-true section width at ycan, tissue only | 0.2204 | 0.2316 | +0.0112 |
| Surface-true section width at ycan, **merged surface** | 0.2413 | 0.2412 | −0.0001 |
| Max surface section width inside the slab band, merged | 0.2448 | 0.2448 | 0.0000 |
| Section curve length (perimeter) at ycan, merged | 1.4834 | 1.4806 | −0.0028 |
| Control: v3 tissue subdivided, **unrelaxed**, gate ruler | 0.2288 | — | +0.0130 over v3 |

The surface-true section is the diag_f method (edge∩plane at
ycan = 0.29077, exact for the polyhedral surface) and is the arbiter: it
is density- and partition-independent, and it does not move. The
tissue-only section's +0.0112 at the exact plane is the same artefact
family one level down — the seam re-cut moved the tissue/jaw boundary
(hinge z −0.1278 → −0.1249), so the tissue partition owns slightly
different surface at that plane; the tissue section's max across the
slab band is 0.2380 (v3) vs 0.2385 (v4).

**Mechanism — three stacked causes, all in the measurement chain:**

1. **Scope.** The stage-F ruler samples TissueHead only. At the muzzle
   station, v3's widest surface is *jaw*: verts at (±0.1209, 0.2876,
   −0.2575), with the next jaw pairs at ±0.1181 / ±0.1167 in the same
   slab. v3's published 0.2158 (attainers (±0.1079, 0.296, −0.183),
   tissue) silently excluded them — **v3's full surface at this station
   (0.2418 vertex / 0.2413 surface) was already wider than v4's
   tissue-only reading of 0.2332.** The +26.9% v3 deviation was itself
   an under-read.
2. **Sampling.** The v3 slab holds 14 tissue verts; the widest in-slab
   surface lies on edges whose endpoints fall outside the ±0.02 slab.
   Subdividing v3's tissue with *no relax at all* already reads 0.2288
   (59 slab verts) — +0.0130 of the drift is pure densification, the
   same population-migration mechanism documented for EarLength.
3. **Guard basis mismatch.** `build_v4.py`'s ruler guard clipped the
   slab to the **merged** V0 extremum (lim = 0.1209/side, set by the jaw
   verts above), not to the tissue-only 0.1079 the gate compares
   against. Relax then moved subdivision verts within their 0.012 cap
   up toward — but not past — that wider limit: v4's attaining vert
   (±0.1166, 0.2958, −0.2230) is a relaxed subdivision vert (not an
   original, not an exact edge midpoint), contributing the remaining
   +0.0044. It never reached the guard's 0.1209.

Corroboration: BVH signed distances of all v4 tissue verts against the
v3 tissue surface in the muzzle band (|y − ycan| < 0.05, n = 341) give
mean +0.0004, p99 +0.0032 — smoothing noise, no systematic outward
movement (a single seam-band vert reaches +0.0237, at the deliberately
re-cut seam). Stage attribution: `work/stage_v4a.blend`'s tissue is
**bit-identical** to the shipped v4 tissue (max diff 0.0) and already
reads 0.2332 — stage B contributed exactly nothing; within stage A,
subdivision accounts for +0.0130 and the guarded relax for +0.0044.

**Gate recommendation.** Redefine MuzzleWidth as the surface-true
section width over the merged head surface at ycan (or, if the vertex
ruler is kept, scope it to the merged mesh). Under the section ruler:
v3 = 0.2413 (**+41.9%**), v4 = 0.2412 (**+41.9%**) — the no-drift rule
holds exactly, and the gate is out of its ±6% band on *both* versions,
as it always was on an honest measure. Any future build guard must use
the same scope as the gate it protects. No geometry fix is owed: there
is nothing to fix.
