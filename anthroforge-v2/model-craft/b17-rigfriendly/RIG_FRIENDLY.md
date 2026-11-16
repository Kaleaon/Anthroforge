# Rig-Friendly Modeling — B17 Study + Deformation Stress Audit

*Model-craft wave, agent B17. Question: what must be true of a **model**
(geometry, pivots, bind pose, skeleton structure) so that skinning weights
have something to work with? Method: study the rigging literature, then run
a measured deformation stress audit on a real library rig and write only
rules that either the literature or a measured failure supports.*

**Subject:** `bara_wolf_avatar.glb` (furry-lineup copy) — Tripo-AI-generated
body, Mixamo skeleton, 65 bones, 69,190 body verts / 127,110 tris, plus two
rigid eye objects. **Tools:** `audit_rig.py` + `supplement.py` (headless
Blender 5.2.3), `analyze_and_capture.py`; raw numbers in `results.json`,
`static.json`, `analysis.json`; posed vertex dumps in `poses_npz/`;
captures in `captures/`.

> **Honesty box.** (1) All deformation is plain linear-blend skinning as
> exported — Blender's armature modifier *without* Preserve Volume, which
> is what glTF engines do; nobody's corrective system is being measured.
> (2) A "flipped face" is a triangle whose 2D deformation gradient in its
> own rest frame has negative determinant — the triangle has folded
> through itself. (3) Edge strain = posed length ÷ rest length; headline
> maxima are also reported filtered to edges ≥ 2 mm so micro-edges can't
> inflate them (only 0.27% of this mesh's edges are < 2 mm, and the
> maxima are identical either way — the big numbers are real).
> (4) Bend angles in the tables are **achieved** angles, resolved per
> joint against anatomical target directions; where left and right
> resolved differently, a controlled equal-angle supplement was run
> (§4.3). (5) Captures are orthographic point-cloud stills (rest in grey,
> posed coloured by per-vertex max edge strain) because this VM has no
> GPU/EGL for viewport rendering — the same evidence class as the
> autoskin prototype. (6) The AKM Border Collie was tried first and
> rejected as a subject — see §2.

---

## 1. The one-paragraph version

Weights get blamed for deformation failures that are actually **modeling**
failures. This rig's weights are hygienically perfect — every vertex sums
to exactly 1.0, max 4 influences, no unweighted verts — and it still
inverts **10.4% of all faces** in an upper-arm twist and **2,622 faces in
one shoulder** raising an arm overhead. The causes are structural: no
twist bones anywhere, one bone carrying the whole neck, a clavicle loaded
with chest flesh, an ankle pivot sitting 0.59 flesh-radii off the limb
axis, a near-T bind pose, and — on a wolf — **zero tail bones and zero ear
bones**. Density is not the answer either: this mesh has full ring support
on every limb segment and fails anyway, because density that isn't
*organised into loops at the creases* doesn't deform, it just tears at
higher resolution.

## 2. Why the collie is not the subject (a finding in itself)

The AKM Border Collie GLB was audited first. Its scene is a composite
whose objects do not share one bind space: body objects sit at ~140-unit
incoherent scale with duplicates offset ~3 m from the armature (the
export-prototype's `SURVIVAL.md` found the same: "composite at incoherent
scale"). Posing it produces strain readings in the hundreds that measure
the file's incoherence, not its rigging. **Rule zero: a model whose parts
don't share one bind space and one scale is not rig-friendly regardless
of weights** — the collie stays our QA *geometry* gold reference, and the
audit moved to the wolf, a single coherent metres-scale export.

## 3. Static audit — the model before any pose

| Check | Result | Reading |
|---|---|---|
| Weight sums | exactly 1.000 min/max, 0 verts off by >1% | clean |
| Influences per vert | max 4, none over | engine-safe |
| Unweighted verts | 0 | clean |
| Weight cliff (max per-edge weight-vector L1) | **0.997** (p99 0.237) | somewhere, two adjacent verts have almost disjoint weight sets — a tear line waiting for load |
| Distant weights (≥0.25 weight, distance to bone segment) | worst 0.37 m (Head), 0.33 m (Spine1/Spine2/Neck), 0.31 m (Hips) | bara torso radius (~0.3 m) makes some of this legitimate surface; those verts still sweep the widest arcs |
| Ring support (stations occupied of 16 per segment) | **16/16 on every limb segment** | density saturated — support is *not* this mesh's problem |
| Clavicle bones | present (Mixamo Shoulder L/R) | good structure, badly loaded (§4, F4) |
| Twist/helper bones | **0** | the twist failures are guaranteed by construction |
| Tail bones / ear bones | **0 / 0** on a wolf | furry articulation absent from the skeleton |
| Finger bones | 40 (full hands) | present — and their bases are a failure site (F8) |
| Eyes | separate objects, rigid, 1 influence (Head) | correct pattern — keep |

**Pivot placement** (perpendicular offset of the bone head from the
centroid axis of the parent-dominated flesh at the joint station, in
units of local flesh radius; along-axis offsets were 1.3–7.2 cm
*proximal*, i.e. muscle bellies sitting above the joint — normal):

| Joint | ⊥ offset / radius | Verdict |
|---|---|---|
| Knee L / R | 0.046 / 0.070 | excellent |
| Elbow L / R | 0.056 / 0.124 | good |
| Wrist L | 0.214 | acceptable |
| **Ankle L** | **0.589** | **the pivot sits over half a flesh-radius off the shin axis** — yet the ankle *poses* pass (§4), because its range is small; the offset would show the moment the foot has to bear a crouch or a digitigrade push-off |

**Bind pose:** upper arms rest **72° from straight-down (18° below
horizontal)** — a near-T bind; thighs rest **splayed 29.5° from
straight-down**. Both numbers matter in §5.

## 4. Stress audit — 26 poses + 4 controlled

Gates used below (derived from this dataset's clean joints, proposed for
the gauntlet in §7): region flipped faces ≈ 0 (clean joints score 0–1;
failures score hundreds–thousands), region strain p99 ≤ 1.45, no edge
≥ 2 mm strained > 5×.

### 4.1 What passed

| Pose | Achieved | Region max | Flips (global) | Note |
|---|---|---|---|---|
| Ankle plantarflexion | 39° | 1.36 | 0 | small range + dense support |
| Ankle dorsiflexion | 40° | 1.36 | 1 | |
| Wrist flexion | 28° | 1.53 | 0 | target-limited angle |
| Elbow hyperextension | −12° | 1.23 | 0 | hinges are fine backwards a little |
| Knee hyperextension | −12° | 1.18 | 0 | |

Small ranges on well-placed pivots deform cleanly. Everything that
failed, failed at large range, under twist, or where one bone carries a
whole region.

### 4.2 Failure catalogue

**F1 — Upper-arm twist 180° is the worst test on the rig.**
13,416 faces flipped (**10.4% of the mesh**), 8,624 of them in the
arm/shoulder region; max edge strain **26.6×**, localised by worst-vertex
analysis to `LeftArm`/`LeftShoulder` verts at the arm root
([capture](captures/upperarm_twist_L_180.png): the arm itself stays dark;
all the shear concentrates in a hot band at the shoulder insertion).
*Mechanism:* with no twist bones, LBS must absorb 180° of axial rotation
in the weight gradient of a single segment; verts midway between two
bones whose transforms now oppose each other collapse toward the axis
(the classic candy-wrapper), and at the root the arm's twist is handed to
the clavicle wholesale. *Rule → R6.*

**F2 — Forearm twist 180°: the textbook candy-wrapper.**
7,585 faces flipped (5.9%), 4,014 in-region; region p99 strain 1.80 —
broad, distributed pinching rather than one tear
([capture](captures/forearm_twist_L_180.png)). Same mechanism as F1, one
joint down. Production rigs split forearm twist across 2–4 helper
segments for exactly this reason. *Rule → R6.*

**F3 — Shoulder overhead (108° achieved): the worst anatomical pose.**
2,622 (L) / 2,555 (R) faces flipped in the shoulder region alone, region
p99 strain 2.67 / 2.49, max 22.2× at `LeftArm`/`LeftShoulder` root verts
([capture](captures/shoulder_overhead_L.png) — arm clean, armpit/deltoid
pocket glowing). Both-arms-overhead flips 13,231 faces (10.3%). The near-T
bind (§3) means "arm down" and "arm up" are *both* ~72–108° of travel
from bind; the deltoid mass is split between clavicle and arm with no
helper to hold its volume. *Rules → R4, R8.*

**F4 — The clavicle is overloaded.**
Rotating *only* the clavicle 40° (a shrug) produces region p99 strain
2.21 and max 11.5×. The clavicle should carry the arm root and a modest
deltoid share; here broad chest/shoulder flesh rides it, so a small
clavicle motion tears a large area. *Rule → R4.*

**F5 — Hip flexion and the deep squat: crease collapse.**
Hip flex at 86°: 1,175 region flips, max 7.5×, worst verts on
`LeftUpLeg`/`Hips`. Deep squat (combined): 5,635 flips global, worst
strain 5.4× at thigh/hip verts ([capture](captures/deep_squat.png)).
The pelvis→thigh transition has density but no organised crease
structure, and no hip helper/corrective path exists. *Rule → R5.*

**F6 — One bone per region: neck and spine concentration.**
Neck flex 60° on the single Neck bone: region p99 2.08, 436 region
flips. **Neck twist 80°: region p99 3.00 — the worst p99 of any test** —
max 17.4× at Neck/Spine2 boundary verts ([capture](captures/neck_twist_80.png)).
Spine flex concentrated on Spine1 alone: 608 region flips, max 6.3×.
Articulation regions need their rotation *distributed* over several
short bones; a single bone turns its whole region into one hinge with
one crease. *Rule → R7.*

**F7 — Deep hinge flexion inverts ~1–2.7k faces per joint (see §4.3).**
At a controlled 120°: elbows flip 1,014 (L) / 1,143 (R) region faces,
knees 2,702 (L) / 2,726 (R), region min area ratio down to 0.015 — the
inside of each hinge folds through itself. Elbow/knee pivot *placement*
is good (§3); what's missing is crease geometry and volume preservation:
loops across the crease that can bunch on the inside and stretch on the
outside. *Rule → R3.*

**F8 — Finger bases tear in a fist.**
Curling all finger bones 80°: worst verts in the whole test sit on
`LeftHandMiddle1`/`LeftHandRing1` bases at vstrain **8.9**
([capture](captures/fist_L.png)); ~1,190 faces flip, concentrated in the
finger chains. Knuckle pivots + a loop at each knuckle are the fix;
finger bases are where the hand's weight gradient is steepest. *Rule → R9.*

**F9 — Whole-pose fold-through.**
Touch-toes: some faces end at **0.2% of their rest area** (min area ratio
0.002) — complete fold-through where spine, hip and neck bends stack.
Combined poses don't create new failure types; they stack F3/F5/F6 in
the same verts. *Rule → the gauntlet must include combined poses (§7),
because isolation passes don't predict them.*

### 4.3 The left/right lesson (a methods finding)

The first pass made the right elbow look catastrophically worse than the
left (744 region flips vs 0). It wasn't a fair test: the resolved bend
angles were **33° (L) vs 105° (R)** — at rest, the two elbows sit at very
different angles to the same target direction, so an uncontrolled
"flex toward front" test barely bends one side. The supplement re-ran
both sides at exactly 120° about each side's resolved axis:

| Joint @120° | Region flips L / R | Region p99 L / R | Region max L / R |
|---|---|---|---|
| Elbow | 1,014 / 1,143 | 1.61 / 1.76 | 2.29 / 2.45 |
| Knee | 2,702 / 2,726 | 1.76 / 1.70 | 3.23 / 3.76 |

Verdict: near-symmetric (right elbow ~13% worse on flips — a mild real
asymmetry worth a weight pass, not a scandal), and *both* sides fail the
deep-flexion bar systemically. Two rules fall out: mirrored poses must be
run at **equal angles** or the comparison is meaningless, and a bind pose
whose left and right elbows rest 70° apart in readiness is itself a
modeling smell — the sculpt's rest pose wasn't checked for symmetry of
*function*, only of silhouette. *Rule → R11.*

## 5. Neutral-pose choice (the bind is a modeling decision)

The literature is consistent: the bind pose decides how much deformation
you fight later, because skinning travel is measured *from bind*
(neural4d; triverse; mocaponline). T-pose binds are axis-clean and
tool-friendly (Mixamo, Unity Humanoid, VRM expect them) but put ~90° of
travel between bind and a hanging arm, paid for in the armpit. A-pose
binds (arms ~40–45° below horizontal, UE5's mannequin default) halve
that travel and deform better in everyday ranges, at the cost of the
overhead extreme. Relaxed binds (slight elbow/knee bend, arms a few
degrees off the torso) additionally give hinge axes an unambiguous
direction to solve around.

This wolf sits between: arms 18° below horizontal — close enough to T to
pay the T price (F3 overhead *and* arm-down travel both large), with
thighs splayed 29.5°, so hip *adduction* and cross-leg poses start
pre-strained. **The rule is not "always A-pose"; it is: bind at the
middle of the character's actual working range, state the choice, and
stress-test both extremes from it.** For AnthroForge's created avatars
(default use: standing, gesturing, walking — arms low), that argues for
a relaxed A: arms 35–45° below horizontal, elbows and knees carrying a
2–5° rest bend in their hinge direction, legs straight down and
together, spine straight, tail in a gentle natural curve (not modelled
straight, or its curl range is spent before it moves).

## 6. The rules (consolidated)

**Joint placement**
- **R1 — Pivot on the flesh axis.** A joint's pivot should sit within
  ~0.25× the local flesh radius of the limb's cross-section centroid
  axis (perpendicular measure). Elbows/knees here: 0.05–0.12 — and they
  are the cleanest deep bends relative to their mass. Ankle: 0.59.
- **R2 — Pivot at the anatomical rotation centre, not the visual
  centre.** Knee axis slightly behind the leg's midline, elbow slightly
  behind the arm's, shoulder lower and more inboard than the deltoid's
  outer edge (threedium). Model a slight rest bend in the hinge
  direction so the axis is defined and IK/rigging can read it.

**Geometry support**
- **R3 — Loops at the crease, on both sides of the pivot.** Every hinge
  needs ≥3–4 edge loops spanning the crease, perpendicular to the bend
  axis, graded over the transition (hip/crotch: 3–4 loops, innermost
  crotch verts split evenly between legs). Density elsewhere does not
  substitute — this mesh is dense everywhere and still folds (F7).
  A joint that collapses flat at 90° is "one edge loop where three are
  needed — a mesh problem more than a weight problem" (Blender rigging
  guide).
- **R12 — No weight cliffs.** Adjacent verts should not hand over their
  whole weight vector across one edge (per-edge L1 ≤ ~0.5; this mesh's
  p99 is a fine 0.24 but its max is 0.997). Cliffs live where the sculpt
  has a hard crease — either put a deliberate loop there or smooth the
  weights across it.
- **R14 — Audit distant influence.** Any vert weighted ≥0.25 to a bone
  whose segment is far away (scale-relative; >0.25 m on a ~2 m
  character) needs a stated reason. Bara torso mass is a legitimate
  reason; on lean characters it's a bug that sweeps verts through wide
  arcs.

**Shoulder & hip complexity**
- **R4 — The shoulder is a system, not a joint.** Clavicle + upper arm
  + deltoid split between them, with the deltoid never wholly on the
  arm (it detaches visually when raised) and the clavicle never loaded
  with broad chest flesh (F4). For hero range, add a shoulder helper
  bone or a corrective for the overhead pocket (F3).
- **R5 — The hip gets the same respect.** Pelvis→thigh graded over
  loops (R3), crotch split between legs, and a planned answer for deep
  flexion (helper bone or corrective) *before* the first squat test,
  not after (F5).

**Twist**
- **R6 — Twist is structure.** Forearm and upper arm (and thigh, on
  digitigrade/quadruped builds) get 2–4 twist segments sharing axial
  rotation in graded shares (the rex guide's 25/50/75% pattern;
  Rigify's segmented limbs). Zero twist bones measured: 5.9% face
  inversion (forearm) and 10.4% (upper arm) at 180°. No weight painting
  fixes this; it is decided when the skeleton is built.

**Distribution of rotation**
- **R7 — Never one bone per articulation region.** Neck ≥ 2–3 bones,
  spine bends distributed across all spine bones (and stress-tested
  both distributed *and* isolated, §7), tail ≥ 4 segments, ears on
  their own base bones. Single-bone regions produced this audit's
  worst p99 readings (F6).

**Bind pose & symmetry**
- **R8 — Bind at mid-range** (§5): relaxed A for hang-armed characters;
  legs straight down, not splayed; rest bend in every hinge.
- **R11 — Symmetry is tested at equal angles**, and the bind is
  checked for functional symmetry (both elbows equally ready to flex),
  not just silhouette symmetry (§4.3).
- **R10 — Furry articulation is in the base skeleton contract.** Tail
  chain, ear bases, jaw — a wolf with 0 tail and 0 ear bones cannot
  pass a furry stress suite no matter how good its humanoid numbers
  are. (AnthroForge's own 36-bone contract already requires Tail and
  Ear bones; this rig fails that contract in the QA gauntlet for the
  same underlying reason.)
- **R9 — Knuckles get pivots and loops.** Finger pivots at the
  anatomical knuckle (place by loop centroid), one loop per knuckle;
  the fist test grades the bases (F8).
- **R13 — Rigid attachments stay rigid and separate.** Eyes as their
  own objects bound 100% to Head (this rig does it right) — don't merge
  them into a deforming body mesh, don't half-weight them.

## 7. The standard stress-pose list (for the QA gauntlet)

Run on every new base, re-run on any topology/weight/skeleton change.
Isolation poses are diagnostics; combined poses are the sign-off
(after robosize's distinction). Gates per isolation pose: **region
flipped faces ≤ 25 · region strain p99 ≤ 1.45 · max strain on edges
≥ 2 mm ≤ 5× · region min area ratio ≥ 0.05.** Combined poses: same
gates, reported per region.

| # | Pose | Grades |
|---|---|---|
| S1 | Bind pose (baseline capture) | reference |
| S2 | Elbow flexion 90°, then max (~140°) — L and R | hinge crease, R3 |
| S3 | Knee flexion 90°, then max (~130°) — L and R | hinge crease, R3 |
| S4 | **Mirrored pair control**: elbow & knee at exactly 120° both sides | symmetry, R11 |
| S5 | Hip flexion 120° (one leg) | hip crease, R5 |
| S6 | Deep squat (combined) | hip+knee+ankle stack, R5 |
| S7 | Shoulder flexion to front, then overhead — L and R | shoulder system, R4/R8 |
| S8 | Arms behind back | shoulder/chest clipping |
| S9 | Clavicle shrug (isolated, 30–40°) | clavicle load, R4 |
| S10 | Forearm twist 180° | candy-wrapper, R6 |
| S11 | Upper-arm twist 180° | candy-wrapper at root, R6 |
| S12 | Thigh twist 90° | R6 |
| S13 | Wrist flexion/extension full range | small-hinge control |
| S14 | Ankle plantar/dorsi full range | pivot placement, R1 |
| S15 | Neck flex / extend / lateral / twist 80° | distribution, R7 |
| S16 | Spine flexion & twist — distributed, then single-vertebra isolation | R7 |
| S17 | Fist (full finger curl) | knuckles, R9 |
| S18 | Touch toes (combined) | fold-through stacking, F9 |
| S19 | Tail curl (per-segment ~20°, cumulative) + tail lateral | furry set, R10 |
| S20 | Ear fold + ear swivel | furry set, R10 |
| S21 | Hyperextension probes: elbow/knee −12° | hinge axis sanity, R2 |
| S22 | Walk-cycle extreme frames (if animation exists) | temporal popping |

This rig's score against S1–S18, S21 as run: passes S13, S14, S21 and
the small-angle halves of S2/S3; fails S4–S12, S15–S18 — i.e. it is a
presentable standing avatar and not yet an animatable body. That is the
normal state of an auto-rigged AI-generated mesh, and exactly what the
list exists to catch before it becomes someone's character.

## 8. Sources

Bind pose / A-vs-T:
- https://blog.neural4d.com/comparisons/a-pose-vs-t-pose/
- https://dev.triverse.ai/blog/a-pose-vs-t-pose
- https://mocaponline.com/blogs/mocap-news/character-rigging-for-motion-capture

Stress testing practice:
- https://github.com/bborn/rex-marks-the-spot/blob/HEAD/docs/workflows/character-rigging-validation.md (8-pose stress set + human review gate)
- https://github.com/bborn/rex-marks-the-spot/blob/HEAD/docs/guides/character-rigging-production-guide.md (stress poses, twist-bone setup)
- https://robosize.com/blog/skinning-3d-models/ (diagnostic vs representative poses; 90°/180° diagnostic bends; bend+twist isolation)

Joint placement, twist, weights craft:
- https://threedium.io/create/3d-models/avatars/full-body (anatomical rotation centres; hip/shoulder/knee weight practice; 3–4 loop hip transition)
- https://www.crownashes.com/articles/skeletal-animation-and-rigging/ (LBS volume loss and the candy-wrapper mechanism)
- https://app.cinevva.com/guides/how-to-rig-a-character-in-blender (Rigify placement rules; slight elbow/knee bend; "one loop where three are needed"; Preserve Volume vs twist bones)
- https://www.mcpinstall.com/skills/el4cteo/blender-skills/blender-character-rigging (pivot-of-rotation placement; twist segments; stress-test step)

## 9. Files & reproduction

- `audit_rig.py` — static audit + 26-pose stress run (resumable;
  flushes per pose). `supplement.py` — controlled 120° L/R pairs.
  `analyze_and_capture.py` — filtered strain, worst-vertex localisation,
  pivot decomposition, captures.
- `results.json` (all 30 pose summaries), `static.json`, `analysis.json`,
  `bones.json`, `rest.npz`, `poses_npz/*.npz` (posed verts per pose).
- `captures/` — upperarm_twist_L_180, forearm_twist_L_180,
  shoulder_overhead_L, deep_squat, elbow_flex_R, neck_twist_80, fist_L.
- Re-run: `blender -b --python audit_rig.py -- <glb> <this dir>` with an
  isolated `HOME` (the shared Blender config carries a broken extension
  that spams tracebacks; harmless but noisy). Joint-name config at the
  top of `audit_rig.py` is Mixamo-shaped; the collie config from the
  first attempt was dropped when the subject changed (§2).
