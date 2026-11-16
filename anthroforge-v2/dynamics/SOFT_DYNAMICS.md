# Soft-Tissue Dynamics for AnthroForge

**Status: prototyped and measured, Nov 12, 2026.** Deliverables in this folder:
`SOFT_DYNAMICS.md` (this spec) · `dynamics_spec.json` (machine-readable
records) · `prototype_softdynamics.blend` (working prototype, dynamics baked
as bone animation) · `measurements` in §6 and `work/sim_metrics.json` ·
`renders/` (lag plot + stride frames) · `scripts/` (simulator + builders).

Joe's brief (Nov 12, 2026): unique soft geometry must *behave* — "teat
softness, sag when walking, etc." Heavy soft parts (belly apron, sac, teats,
chest tissue, ears, tails) need secondary motion: sag under gravity, sway and
lag in locomotion, settle wobble when motion stops.

---

## 1. The core fact: GLB ships nothing dynamic

A glTF file carries a static skeleton, skin weights, morphs and baked
animation clips. There is no standard glTF mechanism for "this chain swings
when the character walks" — no springs, no colliders, no softness. So
dynamics in AnthroForge are **data, not geometry**:

1. **Chain records** — for each soft part: the bone chain, per-segment rest
   offsets, and spring parameters (stiffness, drag, gravity response,
   collision radius). Schema in `dynamics_spec.json`.
2. **A paintable softness field, `AF_softness`** — a per-vertex float
   (0 = rigid core tissue, 1 = freest soft tissue) that modulates the chain
   parameters locally, exactly as `AF_mobility` modulates the gravity/sag
   morph fields (first-proof GRAVITY_WEIGHTS). Same brush discipline, same
   storage pattern (vertex group in Blender tooling, sidecar data in the
   character record).
3. **An integrator** — a small verlet spring-chain solver that consumes the
   records. It runs live in the app runtime, or offline to *bake* bone
   animation for static targets (plain GLB, print, video).

Field names deliberately mirror the **VRMC_springBone** glTF extension
(`stiffness`, `dragForce`, `gravityPower`, `hitRadius`), so a VRM export of
an AnthroForge character maps our records across 1:1 instead of translating
concepts.

## 2. What the existing systems do (study summary)

**VRM SpringBone (UniVRM / VRM 1.0 spec).** The proven pattern. Each chain
is a series of joints integrated with **verlet integration**: gravity and
inertia move the particles; a *stiffness* force pulls each joint toward the
position it would occupy in the animated rest pose; *drag* bleeds velocity;
distance constraints re-impose bone lengths; sphere/capsule **colliders**
push joints out of the body. Parameters are per-chain with per-joint
overrides. Cost is trivial (a handful of particles per chain). This is the
model we adopt — with one structural change, §3.

**VRChat PhysBones.** Same physics family, productised for users: Pull
(spring toward rest), Spring/damping, Stiffness (stretch resistance),
Gravity (−1..1 scaled), Immobility (how much the chain ignores root motion),
per-bone radius, colliders, angle limits. Two lessons worth stealing:
*Immmobility* as an explicit knob (a heavy sac should partially ignore
small root jitter), and **per-chain angle limits** so a chain can never fold
through the body even when the integrator is pushed.

**Blender-native routes — honestly assessed.**
- *Bone constraints* (Damped Track, Limit Rotation): pendulum-flavoured lag,
  no spring dynamics, no settle wobble. Fine for a quick pose garnish, not a
  system.
- *Rigid-body on empties + Copy Transforms:* workable but heavy, fragile at
  chain scale, and the results still have to be baked to bones.
- *Soft body / cloth on the mesh:* this is how the Kaleaon sac's rest drape
  was derived (cloth + pressure, §5) — right tool for **shaping the rest
  pose**, wrong tool for locomotion garnish (slow, chaotic across runs, and
  the output is mesh deformation, not portable bone data).
- *Community spring-bone addons* exist and validate the demand; we don't
  depend on them — our integrator is ~120 lines of numpy (and a short TS
  port for the app), owned outright.

**Decision:** VRM-style verlet chains as the one true model; our integrator
for both runtime and baking; cloth stays in its existing role (rest-shape
derivation for extreme masses).

## 3. The integrator — and the one change that matters

Prototype finding, stated plainly because it decides whether tissue reads
as tissue: **the stiffness spring must be angular, not positional.**

- *Positional (shape-matching) springs* — pull every particle toward its
  global rest position — were implemented first. Result on a walk cycle:
  peak lag 1–2°, no settle, no life. Every particle is glued to the rest
  pose; the pendulum mode is exactly what gets cancelled.
- *Angular (bend) stiffness* — each segment is rotated toward its **rest
  direction relative to its parent segment's current direction** (segment 1:
  relative to the root bone's animated frame) — resists *kinking*, not
  *swinging*. The chain can hang plumb under gravity, lag behind root
  accelerations, overshoot, and ring down when motion stops. This is also,
  structurally, what VRM's bone-hierarchy formulation does.

Integrator (reference: `scripts/simulate.py`): verlet particles, gravity,
drag; per substep, two root→tip passes of [bend-spring slerp + segment
length enforcement]; root particle pinned to the animated attach point.
4 substeps per 30 fps frame is stable for every parameter set in §7.

## 4. The softness field — `AF_softness`

Per-vertex float, 0..1, painted like `AF_mobility`:

- **Semantics:** 0 = rigid core tissue (belly wall over muscle, ear base),
  1 = freest soft tissue (teats, sac pole, ear tips). The gradient on a part
  runs root→tip: the prototype sac runs 0.15–0.2 at the root to 1.0 at the
  pole; teats sit at 1.0.
- **Effective stiffness mapping (v1, [E] constants for first builds):**
  `k_eff = k_chain · (1 − 0.6 · softness) · length_factor`.
  The **length factor is load-bearing**: pendulum frequency scales as
  √(g/L), so a 4.8 cm teat naturally oscillates ~3× faster than a 42 cm sac.
  Short chains need *less* spring relief, not more — the prototype's teat
  chains run softness 1.0 with `k = 2.0 ×` the host sac's stiffness and land
  exactly in the believable band (§6). The naive alternative (teats at 0.55×
  sac stiffness, free softness) measured **55–60° of flail** — a teat is
  soft *tissue* on a *short* pendulum; conflating the two is the one easy
  mistake in this whole system, and the field mapping exists to prevent it.
- **Authoring rule:** softness increases monotonically root→tip on a part
  unless anatomy says otherwise; the field is data in the character record,
  sampled per segment (at segment midpoints) into chain records at build
  time.

## 5. The heavy end: Kaleaon-scale sac (analytic anchors)

The prototype is wolf-scale (0.42 m chain). The part Joe actually named —
Kaleaon's sac-udder — is documented on disk at canon scale
(`~/workspace/bodies-3d/kaleaon-sacdrape/REPORT.md`): 209.5 L, ≈218 kg,
0.94 m hang, bottom 0.031 m above ground, skinned to a single `Sac` bone
with a graduated blend from the pelvis. Analytic anchors for its chain
record [D]:

- **Pendulum period** T = 2π√(L/g) ≈ **1.95 s** at L = 0.94 m — *slower
  than a stride* (~1.0–1.1 s). A mass this size cannot follow the gait; it
  sways near its own period and the gait pumps it. Expect large, slow,
  phase-shifted sway — this is the correct look, not a tuning failure.
- **Momentum dominates.** At 218 kg the chain record needs *more drag*
  (0.045 vs the prototype's 0.025), not more stiffness, or the sway builds
  run over successive strides. Stiffness 0.8 (below the prototype's SOFT).
- **Single-bone articulation has limits** — the sacdrape report's own
  aft-swing pose folds the bag against the belly. A 4–5 segment chain with
  per-joint angle limits (PhysBones lesson, §2) is the fix the record
  format already supports; the Kaleaon anatomy build should ship the sac
  with a real chain, not the single r3 `Sac` bone.
- **Teats at that scale** stay short pendulums (~2.3 Hz) riding a slow
  carrier — the two-timescale contrast (slow sac sway, quick teat quiver)
  is precisely the "teat softness" read Joe asked for, and it falls out of
  the length factor for free.

## 6. Prototype — build and measurements

**Host:** bara wolf from the retarget prototype (Mixamo rig, real `Walk`
clip, 32-frame loop at 30 fps, loops seamlessly — verified frame 33 ≡
frame 1). **Soft part:** a sac stand-in loft (13 rings × 16, teardrop
profile, 0.42 m hang) attached front-below the pelvis, skinned to a 4-bone
chain `AF_Sac1..4` (tent weights across segments), plus two teat chains
`AF_TeatL/R` (single 4.8 cm bones) at the sac pole. `AF_softness` painted
on all three meshes. **Timeline:** 96 frames of Walk (3 loops), then the
root freezes and the chains settle for 90 frames. **Bake:** wolf fcurves
copied cyclically, chain quaternions computed analytically from sim
particle positions (no depsgraph iteration) — **verified 0.0 mm tip error
against the sim at frames 40 and 150**; teat bone tips within ~9 mm
(teat root frame is constructed from the tip segment, a known small
divergence). Two full actions baked: `AF_Full_Soft`, `AF_Full_Firm`.

**Measurements** (third walk cycle = steady state; lag = tip direction vs
root-frame rest direction; full series in `work/sim_metrics.json`, plot in
`renders/lag_plot.png`):

| Metric | SOFT (k = 1.5) | FIRM (k = 8.0) |
|---|---|---|
| Walk lag, peak | 10.9° | 9.1° |
| Walk lag, RMS | 7.4° | 6.2° |
| Dynamic swing about equilibrium, peak | 4.2° | 3.2° |
| **Settle time after stop (to < 2°)** | **1.60 s** | **0.43 s** |
| Equilibrium hang offset (static sag) | 7.1° | 5.8° |
| Phase lag, lateral tip error vs pelvis sway | +67 ms | ≈ 0 (rigid at frame resolution) |
| Tip travel over one cycle | 0.27 m | 0.51 m |
| Teat lag, peak (vs sac-tip frame) | 33.5° | 30.1° |

**Reading the table — three honest findings:**

1. **Settle time is the stiffness readout, not peak lag.** On a real walk
   clip the lag signal is dominated by the equilibrium hang offset (the
   authored shape has a forward bow; gravity pulls it plumb, ~6–7° at any
   stiffness) plus direct following of pelvis rotation. Stiffness moves
   settle time 3.7× (1.60 s vs 0.43 s) while peak lag barely shifts. Tune
   and QA dynamics by settle, and by dynamic swing about equilibrium —
   both are in the metrics tooling (`scripts/simulate.py`).
2. **The firm chain travels *farther* than the soft one** (0.51 m vs
   0.27 m per cycle): a stiff chain is dragged through the pelvis's full
   trajectory, while a soft chain sloshes around its hang point and
   partially cancels root motion. Counter-intuitive, physical, and a good
   reminder that "more motion" ≠ "softer".
3. **Static sag is real and desirable:** at frame 1 the chain already hangs
   ~6–7° off its authored bow toward plumb — the same gravity honesty the
   belly work needed (v1 rose, v2+ sags). Authored rest shapes for soft
   parts should be authored slightly *proud* of the intended hang, or the
   sim's equilibrium becomes the de-facto rest pose. (The sacdrape cloth
   workflow already works this way: settle, then bake.)

## 7. Parameter profiles (starting sets)

Full table in `dynamics_spec.json` (`profiles`). Anchors:

| Part class | stiffness | drag | gravity | softness root→tip | tier |
|---|---|---|---|---|---|
| Sac (standard) | 1.5 | 0.025 | 1.0 | 0.2 / 0.5 / 0.8 / 1.0 | [S] prototype |
| Sac, firm/lean variant | 8.0 | 0.025 | 1.0 | same | [S] prototype |
| Hyper sac (Kaleaon scale) | 0.8 | 0.045 | 1.0 | same | [D] §5 |
| Teat | 2.0 × host k | = host | 1.0 | 1.0 | [S] prototype |
| Belly apron | 2.0 | 0.03 | 1.0 | 0.3 / 0.55 / 0.8 / 0.95 | [E] |
| Chest tissue | 3.0 | 0.03 | 1.0 | 0.35 / 0.7 | [E] |
| Ear | 6.0 | 0.04 | 0.6 | 0.25 / 0.6 / 0.9 | [E] |
| Tail | 4.0 | 0.03 | 0.8 | 0.2 / 0.4 / 0.6 / 0.8 | [E] |

Gravity < 1 for ears/tails: they are light and partly muscle-held; full
gravity drags them off the authored silhouette. Tails especially are
*authored* animation first — dynamics are garnish, stiffness mid.

## 8. Export paths

- **Babylon app (primary):** the runtime integrates chains live from the
  records (TS port of `simulate.py`); softness sampled from the character's
  painted field at build time. Root input = the root bone's world matrix
  per frame; colliders from the record.
- **Plain GLB:** no dynamics (say so in the export profile). A **baked
  variant** — sim run against a chosen clip, bone fcurves written — is the
  `scripts/build_prototype.py` path, verified exact in this prototype.
- **VRM:** map records to `VRMC_springBone` (names already aligned, §1).
- **Print/fursuit profiles:** dynamics irrelevant; the *equilibrium hang*
  is the pose to print — bake one settled frame.

## 9. Hyper-animation slot

A parallel research wave is studying hyper-scale animation under
`dynamics/hyper-animation/`. This spec's `dynamics_spec.json` reserves the
merge point: its per-part parameter tables land as `profiles.hyper_<part>`
entries with the same field shape, and its findings on hyper-specific
behaviour (multi-part chains, extreme-mass colliders) extend §7 without
restructuring the format. Nothing here blocks on it; nothing there needs to
re-litigate §§1–4.

## 10. Known limits / next steps

- No collider solving in the prototype (chains hang in free space below the
  pelvis; the wolf's thighs would need the record's collider spheres in a
  closer-fitting part). Format supports it; integrator needs the pass.
- Teat root frame is derived from the tip segment each frame — simple and
  stable, but a authored teat root bone orientation would be cleaner.
- The softness→stiffness constants (0.6 relief, length factor) are [E]
  fits from one prototype; the first real character build (Sen or the
  Kaleaon anatomy pass) should re-tighten them against renders.
- Runtime TS port not yet written — it is a port of a 120-line reference,
  scheduled with the app work, not a research risk.
