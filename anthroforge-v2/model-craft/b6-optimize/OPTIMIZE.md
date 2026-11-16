# Mesh Optimization & LOD — B6 Study + Measured LOD Prototype

*Model-craft wave, agent B6. Question: how do you take triangles away
from a skinned anthro character without taking away its ability to
move — and what does the removal actually cost, measured in poses, not
in bind-pose renders? Method: study the failure mechanisms (grounded
in B17's deformation stress audit of this same rig), build a 3-level
LOD chain two ways — naive collapse vs deformation-aware collapse —
then pose every level with B17's own stress poses and metric and
compare.*

**Subject:** `bara_wolf_avatar.glb` — Tripo-AI body, Mixamo skeleton,
65 bones, 69,190 body verts / 127,110 tris, two rigid eye objects plus
one stray rigid icosphere. The same file B17 audited, chosen so every
LOD number can be read against a known LOD0 baseline. **Tools:**
Blender 5.2.3 headless (`build_lods.py`, `pose_check.py`), numpy
analysis (`analyze.py`); raw numbers in `work/lod_build.json` and
`work/measurements.json`; posed vertex dumps in `work/dumps/`.

> **Honesty box.** (1) All deformation is plain linear-blend skinning
> (Blender's armature modifier, no Preserve Volume), the same
> conditions as B17 — no corrective system is being measured at any
> LOD. (2) A "flipped face" is B17's metric: negative determinant of
> the triangle's 2D deformation gradient in its rest frame. (3) The
> pipeline cross-validates: my LOD0 run reproduces B17's published
> numbers **exactly** (elbow 120°: 3,553 global / 1,014 region flips,
> region strain p99 1.612; forearm twist 180°: 7,585 / 4,014, p99
> 1.796) — same poses, same metric, same results, so LOD deltas are
> attributable to the decimation, not the measuring. (4) This subject
> is a structurally weak rig (B17: no twist bones, single-bone neck,
> no crease-loop organisation) and carries **no morph targets**; the
> morph arm of LOD policy is doctrine from B5, not prototype data.
> (5) LOD GLBs are exported without embedded images
> (`export_image_format='NONE'`): an LOD chain ships with one shared
> texture set, and embedding it per level would fake the file-size
> table. (6) Blender's glTF importer prunes >4 influences on load (it
> warned doing so on this file), so in-Blender LOD0 already reads
> "max 4 influences" even though the raw file violates it somewhere;
> B17 measured the same post-import state.

---

## 1. The one-paragraph version

Naive decimation is pose-blind: its error metric prices a vertex by
what it costs the *bind-pose surface*, and the vertices a joint needs
most — crease loops, weight-gradient spans — are nearly free at bind
and priceless at 120°. A deformation-aware collapse (protecting
weight-gradient, joint-proximity and curvature) measurably buys
**surface fidelity** (mean deviation from LOD0 roughly halved at
LOD1: 0.79 mm vs 1.54 mm) and **skin hygiene** (3–12× fewer
>4-influence verts created). It does **not** buy posed integrity: on
this rig, flip rates in posed regions are roughly density-invariant
and slightly *worse* under gradient protection — because the faces
that flip are precisely the high-weight-gradient faces the importance
function protects, and what a crease needs is loop *completeness*
(topology), which per-vertex survival cannot express. Meanwhile plain
uniform decimation keeps the better projected silhouette at every
level measured. Conclusion: LOD policy is three separate budgets —
surface, skin, silhouette — and posed integrity is set by the
skeleton and topology of LOD0, not by the decimator. Choose the
decimator to protect what the *distance* punishes; fix the rig to
protect what the *pose* punishes.

## 2. Why naive decimation destroys joint areas

Five mechanisms, each traceable to a B17 measurement on this rig.

**M1 — The crease is flat at bind.** Quadric-style collapse costs
(Blender's Decimate included) measure static geometric error. A crease
loop's verts sit on a nearly flat sheet in the bind pose, so removing
them costs ~zero measured error — and removes exactly the loops that
must bunch on the inside of a bend and stretch on the outside. B17
R3: this mesh has 16/16 ring support on every limb segment and still
folds 1,014–2,726 faces per hinge at 120°, because density that isn't
*organised into loops at the creases* doesn't deform. Decimation
doesn't need to be malicious to break this; it only needs to be
indifferent, thinning loops and panels at the same rate until a loop
is a suggestion.

**M2 — Weight cliffs get averaged.** Collapse replaces two verts with
one whose weights are interpolated from both. Across a weight cliff
(B17 measured a max per-edge weight L1 of **0.997** on this mesh —
near-total handover across one edge), the merged vert smears the
transition: flesh that belonged purely to bone A now drags bone B.
Worse, interpolation *accumulates* influences — §8 measures naive
LOD2 producing verts with **7 influences** from a 4-influence source.
The optimiser itself manufactures export-rule violations (every
real-time profile caps at 4 — B5 §3 rule 1).

**M3 — Twist is gradient resolution.** The candy-wrapper (B17 F1/F2:
5.9% of all faces inverted in a forearm twist, 10.4% in an upper-arm
twist, both at 180°, zero twist bones) is LBS absorbing axial
rotation in the weight gradient along the segment. Halve the rings
along the segment and each surviving span absorbs twice the twist.
Uniform decimation thins twist spans at the global rate; there is no
slack elsewhere to compensate, because the gradient *is* the
mechanism. (Forarm-region flip rate here stays ~92–96% at every LOD
— §8 — the structure fails identically at any density, which is
B17's R6 verdict from the other side: twist is skeleton, not mesh.)

**M4 — High-travel regions look unimportant at bind.** This rig binds
near-T (arms 18° below horizontal, thighs splayed 29.5°), so the
armpit and crotch — the regions with the largest skinning travel
(B17 F3/F5) — are smooth, low-curvature, low-gradient sheets at bind.
Every static importance signal under-rates them; every pose invoices
them.

**M5 — Silhouette features have no deformation signal at all.** Ears
(this rig has **0 ear bones**), muzzle, tail tip, horn tips: identity
at distance, invisible to any skin-based importance, and small-area
(free) to a quadric. An anthro character at LOD2 distance *is* its
silhouette — ears and tail are the species read. A method that only
protects deformation will spend nothing there and lose the character
first where the audience looks last and longest.

## 3. LOD chain design

**Ratios.** The cross-profile doctrine (B5 §3 rule 3) is ~100 / 50 /
25 / impostor: each step halves the triangles, because perceived
degradation tracks log ratios, and engines (Unity LODGroup, SL's
4-level chain) are built around halving steps. The prototype uses
exactly 100 / 50 / 25 on faces. A fourth level, where a profile
requires one, is an *impostor* (SL Lowest ≤300 tris, B5 §2.1), and
300 tris cannot be reached responsibly by collapse from 32k — it is
hand-assembled or hand-checked (§9, O6).

**What changes per level.** LOD0 is the authored asset: full
topology, full morph set, the only level whose deformation is
*designed*. LOD1 (50%) is the same character at conversational
distance: decimation is safe here *if* it is deformation-aware,
because every structure still exists, just thinner. LOD2 (25%) is
the crowd/distance body: silhouette and gross motion only; morphs
mostly baked, fingers/toes merged into masses, fur cards thinned
(placement density, never card collapse — a card is already 2 tris).
Below 25% you are no longer decimating a character, you are deriving
a variant — B5 §2.3 says the mobile profile must admit this in its
report, and the prototype agrees: this 127k body at its measured
LOD2 (31.8k tris) is still 3× over VRChat-mobile Good (≤10k). No
collapse ratio turns a hero body into a mobile body honestly.

**Parts get their own chains.** A part's LODs are budgeted against
the part, not the body (SL caps are per uploaded mesh; PARTS_STANDARD
points are per part). Rigid parts (Class B — horns, claws, the eyes
here) take naive collapse far more safely — no skin to smear — but
keep the curvature term: a horn is all silhouette. Skinned parts
(Class A — tails, ears, digitigrade legs) follow body rules at part
scale, with one addition: a part's *root* verts (the socket blend
zone) are a weight cliff by design and must be hard-protected, or
the seam opens at pose. Fur is a separate chain entirely (card sets
≈13.6k / 5.4k / 2.0k tris measured in the fur prototype, B5 §2.4):
thin the placement, shorten the cards, drop the undercoat layer —
never collapse card geometry.

**Switching.** LOD selection is screen-height based in every target
engine; the authoring rule is that adjacent levels must share
silhouette within a few percent or the swap pops (A20's fur QA uses
a 0.25 pop-in gate on card chains). §8's filled-silhouette IoU is
the body-scale version of that check: LOD1 vs LOD0 ≈ 0.90–0.99
(acceptable), LOD2 ≈ 0.71–0.79 (visible pop at swap range — mitigate
by switching LOD2 in later, not by pretending it matches).

## 4. Triangle budgets per platform (the LOD lens on B5)

All numbers from B5 STANDARDS.md §1–2 (`[S]` = platform-published,
`[E]` = AnthroForge policy); this table keeps only what an LOD chain
must satisfy.

| Profile | LOD0 ceiling | Chain | Binding constraints |
|---|---|---|---|
| SL (per mesh) | ≤20k tris design, ≤65,536 verts/LOD hard `[S]` | 4 levels mandatory: 100 / ~50 / ~25 / ≤300 tris | ≤110 joints/mesh, ≤8 materials, ≤4 influences — all hard `[S]`; download weight driven by the low LODs |
| VRChat PC (Good) | ≤70k tris total `[S]` | author 100 / 50 / 25 for Unity LODGroup | ≤150 bones, ≤8 material slots; rank ignores LODs, streaming doesn't `[E]` |
| VRChat mobile (Good) | ≤10k tris `[S]` | derived variant, not a chain step | ≤90 bones, 1 skinned mesh, 1 material, ≤10 MB file hard `[S]` |
| WebGL Mini App | ≤20k tris `[E]` | 100 / 50 / 25 in one GLB | ≤12 draw calls, ≤90 bones, GLB ≤5 MB `[E]` |
| Indie PC hero / NPC | ≤80k / ≤20k `[S-range]` | 3–4 levels, ~50% steps | ≤4 influences (Unity default) `[S]` |
| Print | n/a — resolution, not count `[S]` | none — decimation is damage | watertight, min wall 0.6–1.2 mm by process `[S]` |

Reading for this prototype: the wolf's 127k LOD0 already exceeds
every avatar profile except indie-hero — it is an *authoring* body,
and its chain (127k / 63.5k / 31.8k) is an indie/SL-shaped answer.
The same method at WebGL scale starts from an authored ≤20k LOD0;
the ratios and the protection recipe transfer unchanged.

## 5. Texture/geometry tradeoffs

- **Bytes live in textures, counts live in geometry.** A 2048² RGBA
  texture is ≈22 MB VRAM with mips regardless of file size (B5 §1.4);
  this body's entire geometry is 6.3 MB. An LOD chain therefore
  shares one texture set across levels (hence `export_image_format=
  'NONE'` here) and spends its size decisions on texture resolution
  per profile, not per LOD. Dropping LOD2's textures to half
  resolution saves more memory than the whole geometry reduction.
- **Normal maps buy shading, not silhouette.** Baking LOD0 detail
  into normals for LOD1/2 recovers the *look* of density on lit
  surfaces and hides thinning in flat panels — and does nothing for
  the outline, the crease, or the pose. It is the correct trade for
  panels (belly, back, thigh) and a fraudulent one for ears, muzzle
  and joints.
- **Morphs are per-LOD0 data.** One morph ≈ one full per-vertex
  delta buffer (B5 §3 rule 2), indexed by LOD0's vertex list;
  decimation orphans the deltas. Production doctrine (B5 §2):
  customisation sliders bake at export; a small expression/viseme
  set may ride LOD0 (and a separately re-solved set on the head's
  LOD1); lower body LODs ship baked. Re-solving deltas per LOD by
  surface projection is possible and is a research project, not a
  checkbox — untested here (subject has no morphs).
- **Skinning cost scales with verts × influences.** Aware LOD2
  reaches the same face count with 7% fewer verts than naive
  (19,689 vs 21,163) — a small but real per-frame saving that
  compounds across a crowd, and a reason to report verts, not just
  tris, in every LOD table.

## 6. The deformation-aware method (as implemented)

**Importance field** (per vertex, computed on LOD0 in
`build_lods.py`):

```
importance = clip( 0.55 * grad + 0.25 * prox + 0.35 * curv , 0, 1 )
  grad = max skin-weight L1 gradient across incident edges,
         normalised by its 99.5th percentile      (M2: cliffs)
  prox = exp( -(d / 0.06 m)^2 ), d = distance to nearest bone head
         (M1/M4: joint neighbourhoods)
  curv = max normal deviation across incident edges, normalised by
         its 99th percentile                     (M5: silhouette)
```

On this mesh: mean importance 0.161; 42.0% of verts score < 0.1
(freely collapsible); 0.44% score > 0.8. The raw weight gradient
maxes at L1 = 1.995 of a possible 2.0 — B17's cliff, confirmed in the
field that prices it.

**The Blender quirk that decides the sign.** A probe
(`work/probe_decimate.py`, subdivided grid, one half weighted 1.0)
establishes Decimate/Collapse vertex-group semantics empirically:
weight acts as a *collapse preference* — non-inverted, the weighted
half was eaten 820 → 1 verts; with `invert_vertex_group=True` the
same weights protect absolutely (820 → 820). The aware arm therefore
feeds importance with invert on. Anyone wiring "protection" into
Blender decimation without the probe ships the exact opposite of
their intent.

**Pipeline order.** Import → compute importance (aware arm) →
Decimate/Collapse to ratio (Armature modifier removed first and
re-added after, so applying the modifier can't bake or drop the
skin) → measure hygiene → export. Ratios hit their face targets
exactly in both arms (63,555 and 31,776–31,777 vs targets 63,555 /
31,778), no retry needed.

**Known calibration weakness (measured in §8):** the curvature term
is normalised at its 99th percentile (1.44 rad — a heavy tail), which
squashes typical silhouette curvature to ~0.1–0.2 of the field; the
outline results below show the cost. A p90 cap, or an explicit
outline-vertex set (local extremes along the body's long axes),
is the named fix (§10).

## 7. Prototype protocol

1. **Build** (`build_lods.py`): LOD1 = 50% faces, LOD2 = 25% faces,
   each in naive and aware arms, from fresh imports of LOD0. Eyes
   and the stray icosphere carried unchanged (rigid attachments are
   not decimation subjects — B17 R13).
2. **Pose** (`pose_check.py`): every level gets B17's two controlled
   stress poses, constructed identically — elbow flexion to exactly
   120° about the resolved axis (B17 supplement method), forearm
   twist Euler (0, π, 0) (B17 `add_twist`). Posed verts are the
   evaluated depsgraph output: real armature-modifier LBS.
3. **Measure** (`analyze.py`): per pose — global + region flipped
   faces (B17's det metric; regions by dominant bone: elbow =
   LeftArm+LeftForeArm, twist = LeftForeArm+LeftHand), region strain
   p99, region vertex survival; per level — silhouette IoU vs LOD0
   (front projection, 4 mm cells; reported raw and hole-filled, see
   §8 note) and nearest-vertex deviation vs posed LOD0.
4. **Cross-check**: LOD0 through the identical pipeline must (and
   does) reproduce B17's `results.json` to the face.

## 8. Results

### 8.1 Counts and skin hygiene

| Level | Faces | Verts | File (geom only) | Max influences | Verts >4 infl. | Weight sums |
|---|---:|---:|---:|---:|---:|---|
| LOD0 | 127,110 | 69,190 | 6.32 MB (incl. images) | 4 | 0% | 1.000 |
| LOD1 naive | 63,555 | 37,336 | 3.18 MB | 6 | 0.50% | 1.000 |
| LOD1 aware | 63,555 | 36,612 | 3.13 MB | 5 | **0.04%** | 1.000 |
| LOD2 naive | 31,776 | 21,163 | 1.95 MB | 7 | 0.98% | 1.000 |
| LOD2 aware | 31,777 | 19,689 | 1.86 MB | 6 | **0.30%** | 1.000 |

Decimation never unweights a vertex and never breaks the weight sum
(interpolation preserves both) — but it *accumulates influences*
(M2), up to 7 at naive LOD2. The aware arm produces 3–12× fewer
>4-influence verts. Either way, **prune-to-4 + renormalise is a
mandatory post-decimation pass** (B5 §3 rule 1 already demands it at
export; this is the measurement that makes it non-optional).

### 8.2 Posed integrity — flips (B17 metric; region rate = region flips ÷ region tris)

| Pose / region | LOD0 | LOD1 naive | LOD1 aware | LOD2 naive | LOD2 aware |
|---|---:|---:|---:|---:|---:|
| Elbow 120° — global flips (% of faces) | 3,553 (2.80%) | 2,158 (3.40%) | 3,098 (4.87%) | 1,101 (3.46%) | 2,434 (7.66%) |
| Elbow — region rate | 10.4% | 9.5% | 12.5% | 9.4% | 14.5% |
| Elbow — region strain p99 | 1.612 | 1.614 | 1.694 | 1.554 | 1.709 |
| Twist 180° — global flips (% of faces) | 7,585 (5.97%) | 4,282 (6.74%) | 6,261 (9.85%) | 2,144 (6.75%) | 4,756 (14.97%) |
| Twist — region rate | 95.6% | 94.2% | 93.7% | 91.8% | 93.0% |
| Twist — region strain p99 | 1.796 | 1.869 | 1.848 | 1.849 | 1.809 |

Raw flip *counts* fall with LOD only because there are fewer faces;
rates are the integrity signal. Readings:

- **Twist region rate is ~92–96% at every level and in every arm.**
  The forearm's faces are inside-out after a 180° twist no matter
  what the decimator does — B17's structural verdict (no twist
  bones) is density-invariant across a 4× range. No LOD policy fixes
  or meaningfully worsens it.
- **Elbow region rate rises under aware protection** (10.4% → 12.5%
  / 14.5%) while naive slightly *falls* (9.5% / 9.4%). Global rates
  inherit this, amplified by composition (aware keeps more of its
  faces in the failure-prone regions — elbow+twist region tris sum
  to 12.8% of all faces at LOD2 vs naive's 10.6% and LOD0's 11.0%;
  the two regions overlap on the forearm, so read this as a trend,
  not an exact share).
- Region strain p99 moves little anywhere (±10%): the *severity* of
  the surviving deformation is set by the rig; decimation mostly
  chooses how many faces participate.

**The gradient-protection paradox (the study's central finding).**
The faces that flip at a crease are the high-weight-gradient faces —
the transition spans where two bones' influences fight. A
gradient-based importance function protects exactly those faces, at
higher density, and they flip at a higher rate, because flipping is
a property of the *span's* weight change, not of its resolution.
What integrity actually needs is R3's loop completeness — rings that
survive *as rings*, evenly spaced, on both sides of the pivot — a
topological property that per-vertex protection weights cannot
express and Blender's collapse does not preserve as a side effect.
Preserving density near a joint preserves the joint's failure mode
at higher fidelity. This does not make protection useless — §8.3 is
what it's *for* — it makes "deformation-aware" a claim that must
specify which deformation property it defends. This recipe defends
surface shape and skin hygiene. It does not defend fold resistance,
and on this rig nothing in the decimator's gift does.

### 8.3 Surface fidelity and silhouette vs LOD0

| Level | Mean dev (rest, mm) | p95 dev (mm) | Max dev (mm) | Silhouette IoU rest (filled) | Silhouette IoU elbow (filled) |
|---|---:|---:|---:|---:|---:|
| LOD1 naive | 1.54 | 4.91 | 9.76 | 0.990 | 0.990 |
| LOD1 aware | **0.79** | 4.20 | 9.18 | 0.903 | 0.899 |
| LOD2 naive | 1.61 | 5.21 | 9.62 | 0.781 | 0.793 |
| LOD2 aware | **1.36** | 4.97 | **13.0** | 0.718 | 0.708 |

(Deviation = nearest-vertex distance to posed/rest LOD0, sampled;
elbow-pose numbers track rest within ~0.05 mm throughout — posing
does not amplify decimation error on this rig, it merely reveals
the flips of §8.2. Silhouette IoU on *raw* point occupancy reads
0.51–0.79 and mostly measures interior point sparsity, so the
hole-filled outline IoU is the reported form; the figure in
`renders/silhouette_compare.png` shows the raw point clouds.)

- **Aware halves mean surface error at LOD1** and stays ahead at
  LOD2: the panels and joint neighbourhoods sit measurably closer to
  the authored surface. That is the fidelity a viewer sees in a
  still or a slow shot.
- **Naive keeps the better outline at both levels** (0.990 / 0.781
  vs 0.903 / 0.718 filled IoU) and the better worst-case deviation
  at LOD2. Uniform thinning preserves the extreme envelope — some
  vert survives near every outline extreme — while aware spends its
  budget inward (joints, curvature) and lets long smooth spans
  (back, thigh line, tail curve) give up their local extreme verts.
  The under-powered curvature term (§6) is the named cause: at
  distance, the outline *is* the character (M5).

### 8.4 Region vertex survival (dominant-bone verts retained)

| Region | LOD0 | LOD1 naive | LOD1 aware | LOD2 naive | LOD2 aware |
|---|---:|---:|---:|---:|---:|
| Elbow (Arm+ForeArm) | 5,083 | 51% | 53% | 27% | 25% |
| Twist (ForeArm+Hand) | 2,099 | 50% | **69%** | 26% | **42%** |

Protection worked where the gradient signal is unambiguous (the
forearm/hand twist span: +19 and +16 points over naive) and barely
at the elbow, where the region is large, the proximity term is
diluted across two long bones, and at LOD2 the collapse quota
overruns the protected set's mid-weights entirely (25% vs naive
27% — within noise of each other, and a warning that protection
budgets saturate: past some ratio, everything is negotiable).

## 9. Rules for AnthroForge (proposed)

- **O1 — Pipeline order is fixed:** decimate → prune to ≤4
  influences → renormalise → pose-validate. Never decimate after
  pruning (collapse re-accumulates influences; §8.1), never ship an
  unvalidated LOD.
- **O2 — Validate LODs posed, not bound.** The acceptance test for
  any LOD is B17's stress list (S1–S22) run at that LOD, reported
  as *degradation vs the same poses at LOD0* (rates, not counts —
  counts fall with face count and lie). A base that fails at LOD0
  (this one) is graded on delta, not on B17's absolute gates.
- **O3 — Budget the three properties separately.** Surface
  (deviation), skin (hygiene + region survival), silhouette
  (filled IoU). A method may trade between them (§8 shows both
  arms doing so); the export report must state all three per level.
- **O4 — Default recipe:** gradient+proximity protection for
  Class A bodies and parts at LOD1; at LOD2 add an explicit outline
  term (§6 fix) or accept naive's outline with aware's surface —
  the hybrid (protect joints, *also* lock outline-extreme verts)
  is the recommended next iteration, not yet measured.
- **O5 — Ratios 100 / 50 / 25** (B5 doctrine); beyond 25%, derive a
  variant and say so in the report (mobile is a variant, §3).
- **O6 — Impostor levels are authored, not decimated.** SL Lowest
  (≤300 tris) and any billboard tier are hand-built or hand-checked
  per level; collapse output at that ratio is not a character.
- **O7 — Socket roots are hard-locked** on parts (§3): the blend
  zone never decimates. Seams fail before surfaces do.
- **O8 — Morphs bake below LOD0** (B5 doctrine), except a re-solved
  expression set on the head; never promise slider parity across
  LODs.
- **O9 — Fur thins by placement, never by collapse** (§3); shell
  counts and card density are the fur LOD dials.
- **O10 — Report verts alongside tris** in every LOD table (skinning
  cost is verts × influences, §5).

## 10. Honest limits

- **One subject, and a deliberately hard one.** The wolf is an
  AI-generated, structurally weak rig (B17's verdict). On a
  well-built base — crease loops organised, twist bones present —
  the flip-rate story may differ: protection might preserve *good*
  structure as faithfully as it preserved this rig's bad structure.
  The surface/hygiene/silhouette findings should transfer; the
  integrity findings are rig-conditional and are stated that way.
- **Two poses, one side.** Elbow + forearm twist, left only, chosen
  because B17 published controlled baselines for exactly them.
  Shoulder overhead (B17's worst anatomical pose) and the hip/squat
  stack are unmeasured at LOD; M4 predicts they're where naive
  hurts most, unverified here.
- **The importance recipe is a first cut with a known flaw** (the
  p99-squashed curvature term, §6) and a structural ceiling (§8.2's
  paradox): it cannot protect loop completeness. The principled
  upgrade — pose-sampled importance (weight verts by measured
  strain/flip involvement across the stress list) plus loop locking
  — is specified by the findings and not yet built.
- **No morphs, no animation, no rendering.** Deviation and IoU are
  geometric proxies measured on point clouds (this VM has no GPU);
  nobody has *looked* at these LODs lit and moving. Vertex counts in
  §8 are post-export re-imports (the exporter sheds ~0.1–0.5% of
  verts as duplicates/unreferenced; faces are exact).
- **Source debits carried, not fixed:** the stray rigid `Icosphere`
  in the source file rides along in every export; the raw GLB's
  >4-influence verts are silently pruned by Blender's importer
  before any of this starts (Honesty box 6).

## 11. Files & reproduction

- `lods/bara_wolf_lod0.glb` — byte-identical copy of the source.
- `lods/bara_wolf_lod1.glb`, `lods/bara_wolf_lod2.glb` — aware arm;
  `lods/bara_wolf_lod1_naive.glb`, `lods/bara_wolf_lod2_naive.glb` —
  naive arm. (Geometry + skin; shared textures intentionally not
  embedded, §5.)
- `work/probe_decimate.py` — the vertex-group semantics probe (§6).
- `work/build_lods.py` — importance field + chain build →
  `work/lod_build.json`.
- `work/pose_check.py` — B17-identical posing → `work/dumps/*.npz`.
- `work/analyze.py` — metrics + figure → `work/measurements.json`,
  `renders/silhouette_compare.png`.
- Re-run: `blender -b --python work/build_lods.py -- <glb> work
  lods`, then `pose_check.py`, then `python3 work/analyze.py work
  /dumps work`. Isolated `HOME` recommended (the shared Blender
  config loads unrelated addons that spam network-probe errors;
  harmless, noisy).
- Cross-references: B5 `../b5-standards/STANDARDS.md` (budgets),
  B17 `../b17-rigfriendly/RIG_FRIENDLY.md` (mechanisms, stress list,
  LOD0 baselines), A20 fur QA (pop-in gate precedent).
