# B1 — Topology & Edge-Flow Study

**Agent:** B1, model-craft wave (Nov 12, 2026); finished by a finisher agent
after the original died silently at the end of its analysis phase. Everything
below is reconstructed from the surviving artifacts in
[`work/`](work/) — `probe.py`, `audit_static.py`, `analyze_static.py`,
`audit_quads.py`, and their outputs `static_dump.json`, `analysis.json`,
`quad_dump.json`. No mesh was modified and no remediation was performed:
this is an analysis document.

**Subject:** one deep dive, not a library sweep. The subject is the
**AKM Border Collie Scientist** (`bodies-3d/parts-library/sketchfab/
border-collie-scientist-akm/border_collie_scientist.glb`) — 9 skinned
meshes, **8,649 vertices, 14,569 triangles, 66 bones**. The library-wide
breadth for the same 68-file library lives in
[B3's QA2](../b3-qa/QA2.md); B1 is the depth counterpart. Where B1's
findings touch deformation, they are read against
[B17's stress audit](../b17-rigfriendly/RIG_FRIENDLY.md) (different
subject: the Tripo/Mixamo bara wolf), and where they touch imported-mesh
hygiene against [B9's edge study](../b9-edges/EDGES.md).

---

## 1. Method

Four scripts, run in order:

1. **`probe.py`** — polygon-size histograms for the collie GLB and a
   BaraWolf `.blend` (the wolf numbers were printed, never persisted —
   see §6).
2. **`audit_static.py`** — imports the collie GLB in Blender, dumps every
   skinned mesh: world-space positions, edge list, per-vertex **valence**
   (edge count), skin weights (dominant bone, bones ≥ 0.25, count of
   influences > 0.05), and the armature's bone heads/lengths.
   → `static_dump.json`.
3. **`analyze_static.py`** — pure-Python analysis of the dump (below).
   → `analysis.json` (per-vertex records + pole list).
4. **`audit_quads.py`** — re-imports the GLB, runs Blender's
   `tris_convert_to_quads` (face/shape thresholds 1.15 rad ≈ 66°) on each
   skinned mesh, dumps post-conversion face histogram, valence, positions.
   → `quad_dump.json`. The finisher verified the quad dump's vertex order
   and positions are **identical** to the static dump's, which licenses
   joining the two (done for §4.3).

**Definitions.**

- **Valence** = number of edges meeting at a vertex. In a triangulated
  mesh the regular interior vertex has valence **6**; in a quad mesh,
  **4**. A **pole** is any vertex off the regular value; a **severe pole**
  is valence ≤ 4 or ≥ 8 (tri form) / ≤ 2 or ≥ 6 (quad form).
- **Deformation zone** (per vertex, either condition):
  *Zone A* — within 0.6 × bone length of any bone head (pivot proximity);
  *Zone B* — in a blend band, i.e. ≥ 2 bones weighted ≥ 0.25.
  44.7% of the collie's vertices sit in a zone by this definition.
- **Region** = anatomical bucket of the vertex's dominant bone
  (HEAD / LEG / TORSO / EAR / FOOT / HAND / ARM / TAIL / NECK; OTHER =
  biceps + pinky chains, whose bone names miss the classifier's keywords).

**Why two forms are reported.** glTF is a triangle format: an authored
quad mesh arrives triangulated, and raw tri valence measures the
*triangulation* as much as the *authoring*. §4.1 reports the as-imported
form (what an engine receives), §4.2 the quad-recovered form (the best
available evidence of what the artist actually built). Judging edge flow
from the tri form alone is the single easiest mistake in this study, and
the numbers below show why.

---

## 2. Results — the as-imported (triangulated) form

### 2.1 Valence, whole character

| Valence | 2 | 3 | 4 | 5 | **6** | 7 | 8 | 9 | 10 | 12 | 15 | 17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Verts | 53 | 926 | 2,867 | 975 | **1,789** | 130 | 1,832 | 22 | 31 | 21 | 2 | 1 |
| % | 0.6 | 10.7 | 33.1 | 11.3 | **20.7** | 1.5 | 21.2 | 0.3 | 0.4 | 0.2 | — | — |

Only **20.7%** of vertices are regular; **79.3% are poles**, and **66.5%
are severe** (v ≤ 4 or ≥ 8). Read naively this says the model is a
topological disaster. Read correctly (§3) it mostly says the model was
**quad-authored and triangulated on export**: a regular quad vertex
(valence 4) lands at tri valence 4–8 depending on which way the two
diagonals around it fall, and the histogram's twin peaks at exactly
**4 (33.1%) and 8 (21.2%)** are that mechanism's fingerprint — a
genuinely tri-authored mesh (scan, photogrammetry) shows a smooth bell
around 6 instead. Two meshes do show that bell: the rigid head submesh
(mesh "2": 44.4% valence-6) and the tail (Object_91: 71.0% valence-6) —
tube/lathe-class geometry, regular for a different reason.

### 2.2 Per-mesh pole rates (tri form)

Mesh identities are inferred from dominant-bone evidence in the dump.

| Mesh | Probable identity | Verts | Tris | Pole rate | Severe share |
|---|---|---|---|---|---|
| "0" | main body + clothing | 4,051 | 7,084 | 97.1% | high (1,530 v4 + 1,384 v8) |
| "1" | head | 914 | 1,411 | 86.0% | — |
| "2" | rigid head submesh (teeth/tongue class) | 360 | 634 | 55.6% | low |
| Object_77 | limb/clothing shell | 1,271 | 2,014 | 47.9% | low (52% regular) |
| Object_79 | head/neck/shoulder piece | 796 | 1,278 | 73.2% | — |
| Object_81 | ears | 352 | 584 | 37.5% | low |
| Object_87 | feet / paws | 478 | 800 | 95.4% | high |
| Object_89 | small rigid head prop | 92 | 150 | 67.4% | 2 hub verts at v15 |
| Object_91 | tail | 335 | 614 | **29.0%** | lowest |

### 2.3 Poles × deformation zones, by region (tri form)

| Region | Verts | Pole rate | Poles in a zone | Severe poles |
|---|---|---|---|---|
| FOOT | 902 | **96.0%** | **91%** of its poles | 695 |
| HAND | 748 | **95.2%** | 40% | 576 |
| LEG | 1,466 | 89.4% | 39% | 1,159 |
| TORSO | 983 | 84.1% | 35% | 756 |
| HEAD | 1,763 | 81.6% | **12%** | 1,124 |
| ARM | 445 | 65.8% | 66% | 269 |
| NECK | 332 | 63.3% | 73% | 165 |
| EAR | 969 | 56.8% | 21% | 480 |
| TAIL | 335 | **29.0%** | 80% | 61 |

Overall: **40.9% of all poles sit inside a deformation zone** (2,805 of
6,860), and 2,310 of the 5,755 severe poles do. The worst pole-in-zone
clusters by nearest bone are the **toes (547 right / 545 left)**, the
root joint (394), head (212), and feet (196 per side). The head is the
counter-example: pole-rich but with only 12% of its poles in zones —
its irregularity lives in rigid flesh where it costs little. The feet
are the anti-pattern: near-total irregularity *and* 91% of it inside
the zone that has to deform.

### 2.4 Density (edge length)

Per-vertex mean edge length, in dump units: median **0.034**, p10
0.0136, p90 0.0658, min 0.0024, max 0.1124. The p90/p10 spread is
≈ **4.8×** and the extremes span ≈ 47× — density varies a lot, and
(§5) not in a way that tracks deformation need. Absolute values are
in the GLB's own scale (see §7); the ratios are the robust part.

### 2.5 Weight context (from the same dump)

Influence counts (> 0.05) run 1–4 per vertex, engine-safe. The main
body mesh carries the richest blending (of 4,051 verts: 1,954 with 2
influences, 466 with 3, 259 with 4); the rigid head submesh and tail
tip meshes are single-influence throughout. Nothing here contradicts
B3's library finding of zero unnormalised weight sums — this file
included.

---

## 3. Results — the quad-recovered form

`tris_convert_to_quads` at 1.15 rad thresholds recovers, per mesh:

| Mesh | Faces after | Quads | Quad ratio | Residual tris |
|---|---|---|---|---|
| "0" body | 3,580 | 3,504 | **97.9%** | 2.1% |
| Object_87 feet | 404 | 396 | **98.0%** | 2.0% |
| "1" head | 736 | 675 | 91.7% | 8.3% |
| Object_77 shell | 1,056 | 958 | 90.7% | 9.3% |
| Object_91 tail | 330 | 284 | 86.1% | 13.9% |
| Object_89 prop | 82 | 68 | 82.9% | 17.1% |
| Object_79 neck/shoulder | 745 | 533 | 71.5% | 28.5% |
| Object_81 ears | 344 | 240 | 69.8% | 30.2% |
| "2" rigid head submesh | 380 | 254 | 66.8% | 33.2% |
| **Total** | **7,657** | **6,912** | **90.3%** | **9.7%** |

(Totals reconcile exactly: 2 × 6,912 + 745 = 14,569 = the imported
triangle count. The dump's own `tris_before` field is wrong for 6 of 9
meshes — it repeats the post-conversion count — so the histogram, not
that field, is authoritative.)

**Interpretation.** Nine-tenths of this character was authored in
quads. The recovery failures are informative, not random: the **ears
(69.8%)** and the **small rigid head submesh (66.8%)** are the least
quad-recoverable parts — small, curved, close-up parts are exactly
where this author dropped into triangles (or where conversion can't
prove otherwise). The big body shells recover almost perfectly.

In quad form the valence picture becomes the honest one:

- **35.6% of vertices are poles** (3,080 of 8,649; valence ≠ 4).
- Valence-3 verts: 2,424; valence-5: 371 — the healthy pole species
  dominate.
- **Severe poles (v ≤ 2 or ≥ 6): 285 verts, 3.3%** — including the
  prop's two valence-15 hub verts and one valence-17 in the tail mesh,
  fan/lathe artefacts that belong only in rigid parts.
- **45.8% of quad-form poles sit in a deformation zone** (1,411 of
  3,080) — worse than the tri form's 40.9%, because recovery removes
  triangulation noise poles preferentially *outside* zones.

Per region (quad form):

| Region | Pole rate | Poles in a zone |
|---|---|---|
| FOOT | 26.6% | **98%** |
| ARM | 33.7% | **94%** |
| TAIL | 26.3% | 78% |
| NECK | 45.8% | 70% |
| LEG | 27.7% | 65% |
| TORSO | 24.1% | 51% |
| HAND | 45.2% | 31% |
| EAR | 43.1% | 29% |
| HEAD | 44.4% | **14%** |

The feet's problem survives recovery: only 240 quad poles, but **236
of them are in the deformation zone**. Foot/toe construction here is
cap-and-fan work dumped into the highest-deformation area of the
character. The arms tell the same story at 94%.

---

## 4. Findings

**F1 — Judge authored flow on the recovered quad form, never the raw
tri form.** The same character reads as 79.3% poles / 66.5% severe
(tri) or 35.6% poles / 3.3% severe (quad). Any topology gate run
against glTF imports without a recovery (or weld — B9) step is
measuring the exporter. Twin tri-valence peaks at 4 and 8 are the
tell-tale of a triangulated quad mesh; a smooth bell at 6 marks
tri-native geometry.

**F2 — Pole *placement* is this model's real failure, not pole
count.** Poles are topologically unavoidable; the collie puts 45.8%
of its (quad-form) poles inside deformation zones, and ~98% of its
foot poles there. The head shows the discipline the feet lack: plenty
of poles, 86% of them parked in rigid flesh. B17's audit explains the
cost side: poles and irregular valence inside a bend are where LBS
folds concentrate (its F7 hinge inversions), and no weight painting
rescues bad placement.

**F3 — Density is not organisation.** Edge length varies ≈ 4.8×
(p10→p90) across this mesh, yet the deformation zones are not where
the organised density is. B17 measured the same lesson from the other
side: the wolf has 16/16 ring support on every limb segment and still
inverts 10.4% of faces in an upper-arm twist, because density that
isn't *loops at the crease* doesn't deform, it tears at higher
resolution. B1's numbers are what that looks like statically: lots of
vertices, few of them arranged as crease loops.

**F4 — Small curved parts are where quad discipline dies.** Ears at
69.8% quad recovery and the rigid head submesh at 66.8% contrast with
97.9% on the body. These are also the parts B9 showed arriving with
787 split verts of exporter normals and no authored edge marks. The
pattern across B1+B9: the library's small parts are its least
deliberately-topologised, in flow *and* in shading.

**F5 — The tail is the model citizen.** 29.0% tri pole rate, 71%
regular valence, 86.1% quad recovery: clean tube/loft construction
with loops along its length — exactly the structure B17's R7/R10 ask
for in a tail chain (≥ 4 segments, rotation distributed). It is the
only region whose topology already matches its deformation job.

**F6 — Hub verts are prop-only artefacts.** Valence 15/17 vertices
(fan caps) appear in the rigid head prop and one tail spot. In a
deforming mesh a hub is a permanent shading and fold defect (B9 §3's
artefact row); in rigid attachments they're harmless. Placement, again.

**F7 — This file's other sins don't contaminate these numbers, but
they bound them.** B3 found this collie (all 3 library copies) wound
**inside-out at 69%**, masked by `doubleSided` materials; B17 found
the wider scene a composite at incoherent scale and declined to pose
it. Valence, face-size and quad-recovery counts are insensitive to
winding and bind coherence, so §§2–3 stand — but nobody should read
B1 as certifying this file *good*. It is a well-quad-authored body
inside a badly-exported file.

---

## 5. Rules for AnthroForge's own bases and parts

Measured baselines are the collie's; targets are set from them plus
B17's deformation evidence. "Deformation zone" uses §1's definition
until the gauntlet grows a posed version.

- **T1 — Author in quads; triangulate only at export.** Every base
  and swappable part is quad-dominant in its *authored* form.
  Baseline: the collie's body recovers 97.9% quads; our own parts
  should not ship below that class of discipline (≥ 90% quads
  authored, per part).
- **T2 — Audit the recovered form.** Topology gates run on the
  quad-recovered, welded mesh (B9's weld-first rule: the v4 ear
  arrived as 1,072 verts for 285 real corners). A part that recovers
  < 85% quads at the standard 1.15 rad thresholds is tri-authored —
  retopo before it becomes a base or a part, don't gate-tune around it.
- **T3 — Poles are valence 3 or 5, budgeted, and placed.** Quad-form
  poles ≤ ~15% of verts on body parts (collie: 35.6% — the
  anti-baseline), zero poles of valence ≥ 6 in any deforming region,
  valence ≤ 2 nowhere. Fan/lathe hubs (v ≥ 8) only inside rigid
  attachments (B17 R13).
- **T4 — Keep poles out of deformation zones.** ≤ 10% of a part's
  poles inside zones (head manages 14% while pole-rich; feet sit at
  98% — fail). Where a pole must sit in a zone, it sits *on* the
  crease line, not beside it.
- **T5 — Loops at the crease, both sides of the pivot.** ≥ 3–4 edge
  loops spanning every hinge crease, perpendicular to the bend axis,
  graded (B17 R3). Toe and finger construction is loops all the way
  down — no cap-and-fan toes (F2's 547-pole toe clusters are what
  that produces).
- **T6 — Flow follows the deformation, not the silhouette.**
  Limb loops run circumferentially; spine/tail flow runs in rings
  along the chain (F5's tail is the template); face flow follows
  B12-class muscle direction, not UV convenience.
- **T7 — Density graded, deliberate, and matched to texture.**
  Within a part, hold p90/p10 edge length ≤ ~3 (collie: 4.8 — too
  loose); density steps happen at region boundaries, not mid-flesh;
  keep texel-density CV ≤ 0.5 (B3's advisory) so topology density and
  texture density tell the same story.
- **T8 — Topology cannot substitute for structure.** Twist segments
  (B17 R6), ≥ 2–3 neck bones (R7), pivots on the flesh axis (R1) are
  skeleton decisions; a mesh that passes T1–T7 on a one-bone neck
  still fails in motion. Topology sign-off and rig sign-off are
  separate gates, both required.
- **T9 — Small parts get full discipline.** Ears, teeth, tails,
  digits: same quad/pole/loop rules as bodies, *plus* B9's finishing
  stack (weld → smooth → weighted normals → angle-limited bevel on
  rims). The library evidence (F4) is that these parts are where
  discipline lapses first; they're also the parts users look at
  closest.
- **T10 — Record the numbers with the part.** Every AnthroForge part
  ships the B1 metric block (quad ratio, pole rate, poles-in-zone
  share, severe count, edge-length spread) in its `.part.json`-class
  record, so regressions are diffs, not rediscoveries.

**Proposed gate graduations** (extending B3's recommended fail list,
which already covers winding, weights, non-manifold edges):
*fail* — quad recovery < 85% on a part submitted as quad-authored ·
any valence ≥ 6 pole in a deformation zone · poles-in-zone share
> 25%. *Advisory* — overall pole rate, edge-length spread, hub verts
in rigid parts. These thresholds are proposals from a one-model
baseline; revisit after B1's method runs on our own base head/body.

---

## 6. Honest limits

- **One model.** All B1 numbers are the AKM collie. It is a
  reasonable representative of hand-authored Sketchfab-class avatar
  work and a B3 "gold" file for weights/winding QA, but per-class
  claims (scans vs sculpts vs AI-generated) would need the same
  pipeline run per class — B17's wolf (Tripo/Mixamo) is the obvious
  second subject, and `probe.py` shows it was intended.
- **The wolf probe was never persisted.** `probe.py`'s BaraWolf
  branch printed to a console nobody kept; no wolf topology numbers
  exist in the artifacts. This document makes no wolf topology claims.
- **Deformation zones are a static proxy.** Pivot-proximity + blend
  bands predict where deformation concentrates; they are not a posed
  measurement. B17 is the posed counterpart, on a different model —
  the two studies agree in direction, not in shared numbers.
- **Scale.** Edge lengths are in the GLB's dump units; B17 found the
  collie's full scene composite at incoherent scale. `audit_static.py`
  dumped only the 9 skinned meshes (duplicated/unskinned scene objects
  excluded), and all ratios (spreads, shares, rates) are
  scale-invariant — but don't quote 0.034 as metres.
- **Quad recovery is threshold-sensitive.** 1.15 rad is Blender's
  permissive end; stricter thresholds lower every quad ratio in §3.
  The recovery proves *at most* that the faces *can* pair into quads
  at that tolerance — strong evidence of quad authoring at 97.9%,
  weaker at 66.8%.
- **Analysis only.** No mesh was fixed, welded, or re-exported; the
  inside-out winding (B3) and bind incoherence (B17) of this file
  remain exactly as found.

## 7. Files

- Scripts: [`work/probe.py`](work/probe.py) ·
  [`work/audit_static.py`](work/audit_static.py) ·
  [`work/analyze_static.py`](work/analyze_static.py) ·
  [`work/audit_quads.py`](work/audit_quads.py)
- Data: [`work/static_dump.json`](work/static_dump.json) ·
  [`work/analysis.json`](work/analysis.json) ·
  [`work/quad_dump.json`](work/quad_dump.json)
- Siblings: [B3 QA2](../b3-qa/QA2.md) (library breadth, winding,
  weights) · [B9 EDGES](../b9-edges/EDGES.md) (normals, weld-first,
  finishing stack) · [B17 RIG_FRIENDLY](../b17-rigfriendly/RIG_FRIENDLY.md)
  (posed deformation, rules R1–R14, stress-pose list S1–S22)
