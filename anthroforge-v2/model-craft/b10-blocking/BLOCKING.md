# BLOCKING.md — B10 · Blocking & Proportion Workflow

*Model-craft wave, Nov 12, 2026. How a character starts in AnthroForge: primitives
first, proportions measured, silhouette proven — before any sculpting, skinning,
or sliders. Companion demo: `build_blockout.py` + `wolf_blockout.blend` +
`renders/` + `measurements.json` in this folder.*

---

## 0. The rule

**Detail on wrong proportions is wasted work; a blockout is cheap, a re-proportioned
sculpt is not.** Every source consulted for this study says the same thing in
different words: work big-to-small, spend a disproportionate share of the schedule
on the block stage (≈30% in one production guide), and do not crease, carve, or
detail anything until the primary masses are right from every view. Blocking is
where AnthroForge's proportion data (species spec, Muscle×Tissue model, body
plans) enters the pipeline — it is the last stage where moving a shoulder costs
one transform instead of a re-rig.

## 1. What a blockout is (and is not)

- A set of **named primitives** (sphere/box/cylinder/cone, transforms unapplied),
  one per anatomical mass, at **real-world scale** in metres.
- It **is**: proportion proof, silhouette proof, landmark placement (joints, eye
  line, brisket), plan proof (does this rig configuration read?).
- It **is not**: a base mesh. No edge flow, no loops-for-bending, no UVs, no
  symmetry polish. Those belong to the retopo/base stage that follows *after*
  the block is approved. (Conflating the two is the classic beginner trap: loops
  placed for deformation freeze proportions early, which is exactly backwards.)

## 2. Proportion systems — pick the module before you place anything

Never block in "eyeball units." Choose a **module** and a ratio table first:

| Plan | Module | Why |
|---|---|---|
| Biped | Head height (the classic "7½ heads") or head **length** | Human proportion canon is head-based; our head spec is skull-length-based, so head length keeps both systems convertible |
| Feral / quadruped | **Skull length L** (and shoulder height as the vertical check) | Quadruped bodies don't stack heads vertically; comparative anatomy is published as ratios to skull/basal length (our species spec's ZB/L, mandible/L, ear/L) |
| Taur / naga | Shoulder height of the animal half + skull L for the head | Two proportion systems meet at the waist — block each half in its own module and reconcile at the junction station |

Ratio discipline follows the house [S]/[D]/[E] convention from the species spec:
a proportion you cannot source is labelled [E] *in the blockout file header*, so
nobody downstream mistakes an estimate for anatomy.

**Comparative measures beat absolute measures.** "Chest 0.52 L deep, brisket at
elbow station" survives rescaling to a 9-ft Titan; "chest 34 cm" does not. Block
in ratios, instantiate in metres.

## 3. The AnthroForge blocking workflow

0. **Paper first (5 min).** Name the plan (BODY_PLANS.md), the species preset,
   the module, and write the ratio table with targets *before* opening Blender.
   For a known species this is a lookup; for a new one it is a mini species-spec
   pass. The demo's table is §5 below.
1. **Stations before shapes.** Place the vertical/horizontal stations as numbers:
   ground, brisket, elbow, spine line, withers, head station. Shapes are then
   hung on stations, not floated. (In the demo these are literal coordinates in
   the script header.)
2. **Torso masses first.** Pelvis, belly, chest — three ellipsoid masses on the
   spine's **line of action** (§4). Torso order matters: the chest/pelvis
   relationship *is* the character's posture and distribution read (pear ↔
   big-chest is visible already at this step).
3. **Neck + head.** Neck as one tapered mass (its width relative to the head is a
   species tell — wolf neck ≈ head width at base). Head as cranium + muzzle +
   jaw blocks at the spec's ratios; ears as cones at ear/L. **Head blocks are
   skull-anchored**: cranium sized from L and ZB/L, flesh added as a stated
   allowance (demo: +3% length), never the other way round.
4. **Limbs as segment chains.** One stretched-sphere primitive per bone segment,
   joint stations exact. Front quadruped legs are near-columns; hind legs are a
   three-angle chain (thigh forward, gaskin back, cannon down) — block the
   *angles*, they carry the species' gait read. Biped: upper/fore segments with
   elbow/wrist stations on the head-unit grid.
5. **Tail / wings / extras last**, as segment chains from their socket stations
   (PARTS_STANDARD sockets), sized in module units (wolf tail ≈ 1.6 L).
6. **Silhouette pass.** Material-override everything to flat near-black on a
   light ground and render side + front + top. The figure must read as its
   species at thumbnail size with zero shading information. If it doesn't,
   no later stage will save it — fix masses, not details.
7. **Measure pass.** Script the bounding-box checks (the demo's
   `measurements.json`): every ratio in the step-0 table gets a measured value
   and a delta. Block tolerance is **±5%** on primary ratios (shoulder height,
   module length, ZB/L); beyond that, adjust the block, don't rationalise it.
8. **Approve or iterate.** Only an approved block goes to sculpt/base-mesh. The
   block file (`.blend` + script + measurements) is kept — it is the proportion
   record the slider QA later compares against.

## 4. Gesture & line of action — biped vs quadruped

- **Biped:** the line of action runs vertically — head → spine curve → pelvis →
  support foot. Gesture lives in the spine's C/S curve and the head/pelvis tilt
  opposition. Blocking check: the line must be drawable in one stroke on the
  side render; a standing-straight block is a valid *neutral* but the line must
  still exist (withers-equivalent: shoulder line vs pelvis line not parallel-
  locked unless the character is meant to read rigid).
- **Quadruped:** the line of action is **horizontal** — a spine line from head
  station through withers to pelvis, plus the support polygon of the four feet.
  Gesture lives in (a) spine slope (wolf: withers above pelvis, a gentle
  downhill line to the rear), (b) **head carriage** (wolf carries the head at
  back level, raising it only when alert — block the neutral carriage, not the
  alert pose), and (c) neck angle where it leaves the chest. Checks: head top
  near the spine line, feet inside a plausible support polygon, brisket depth
  reaching the elbow station (a shallow chest is the most common quadruped
  block error — it makes every species read as a greyhound).
- **Taur:** both lines exist and must *meet* — the biped line rises out of the
  quadruped line at the junction station; block the junction as its own mass or
  the two halves will read as glued toys.

## 5. Measure vs eyeball — the standing rule

| Measure (script it) | Eyeball (silhouette pass) |
|---|---|
| Module length, ZB/L, ear/L, mandible/L | Mass balance / "does the chest outweigh the pelvis correctly" |
| Shoulder height, brisket & elbow stations | Spine-line flow, neck blend into chest |
| Joint stations on limbs | Whether the hind chain reads as angles, not a bent tube |
| Tail length in module units | Head carriage attitude (level vs alert) |
| Head width/length/depth | Ear set and tilt |

Principle: **anything a downstream system consumes numerically** (slider anchors,
rig stations, socket placements, species presets) **is measured; anything only a
viewer consumes is eyeballed** — but eyeballed *on the silhouette render*, never
on the shaded 3/4 view, which flatters bad blocks.

## 6. Demo — grey wolf, feral plan, blocked from primitives

Targets (module L = skull length 0.25 m):

| Measure | Target | Source | Measured (script) | Δ |
|---|---|---|---|---|
| Shoulder height | 0.82 m | [S] ASM/Wikipedia avg 80–85 cm | 0.83 m | +1.2% |
| Skull L (module) | 0.25 m | [S] spec §2.1 (GL 235–250 mm) | head block 0.257 m incl. flesh | +2.8% |
| ZB / L | 0.53 | [S] spec §2.1 (125.18/235.65) | 0.528 | −0.4% |
| Ear / L | 0.36–0.40 | [S] spec §2.1 (90–110 mm) | 0.392 | in band |
| Nose → tail base | 1.30 m | [S] head-body 105–160 cm, mid-large male | 1.318 m | +1.4% |
| Tail | 0.40 m | [S] 29–50 cm | 0.399 m | −0.3% |
| Brisket bottom | ≈ elbow station (0.42 m) | [S] chest drops to elbow level | 0.43 m | 1 cm |

Build: 28 named primitives — 3 torso masses, neck, cranium/muzzle/jaw, 2 ear
cones, 4 legs × 4 segments, 3 tail segments — one clay material, transforms
unapplied, saved as `wolf_blockout.blend`; the script (`build_blockout.py`)
regenerates everything and re-measures, so the block is reproducible from its
ratio table alone.

Renders: [side](renders/side.png) · [front](renders/front.png) ·
[three-quarter](renders/threequarter.png) ·
[side silhouette](renders/side_silhouette.png) — block stage only, by design:
flat clay, no sculpt, no fur, no rig.

What the demo proved about the method:
- The first scripted pass caught a **12.8 cm torso overshoot** (nose→tail-base
  1.428 m vs the 1.30 target) that the shaded renders did not flag — the
  stations were individually plausible and jointly wrong. This is the entire
  argument for step 7: measure, because the eye integrates proportions
  forgivingly and the rig will not.
- The ear cone's bounding height initially read 0.45 L against a 0.40 L target —
  cone tilt inflates bounding boxes; pinna *depth* was set to 0.36 L so the
  placed block measures in-band. Lesson filed: for tilted primitives, measure
  the primitive's own axis, not the world bbox, when the two disagree.
- Brisket and elbow stations agreeing within 1 cm is what makes the side
  silhouette read "wolf" rather than "dog, generic": chest depth is a
  first-order species signal, not a detail.
- Tooling lesson for the headless pipeline: a Blender material's *viewport*
  diffuse colour does not drive Cycles — the silhouette pass only went dark
  once the Principled **Base Color** was set (and the view-layer material
  override proved unreliable headless, so the demo swaps materials directly).
  Any future automated silhouette/QA render must set BSDF colour, not
  `diffuse_color`.

## 7. Failure modes this workflow exists to prevent

1. **Sculpt-first drift** — proportions discovered after detail exists; every
   fix costs the detail. (Prevented by steps 0–2 ordering.)
2. **One-view blocking** — a block tuned to the 3/4 hero view that collapses in
   front/side ortho. (Prevented by ortho-first cameras + silhouette pass.)
3. **Module mixing** — head blocked in cm from one reference, body in head-units
   from another; the junction silently disagrees. (Prevented by step 0's single
   ratio table.)
4. **Flesh-first heads** — cranium sized to the *furry* outline; every slider
   derived from it inherits the error. Skull-anchor first (step 3) — the same
   doctrine as the layered head construction (skull → muscle → tissue).
5. **Biped habits on quadrupeds** — vertical line of action, head stacked over
   shoulders, shallow chest. (§4's separate quadruped checks.)

## 8. Sources

- Production blocking practice: Nomad Sculpt ultimate guide (blocking workflow /
  golden rule), https://kumarprem886.github.io/3d-modeling-guides/nomad_ultimate.html ·
  Sculpty anime production guide (silhouette blocking, build order),
  https://sculpty.ai/blog/anime-3-d-modelling ·
  Tripo "From Concept to Rig" (blockout checklist: silhouette readable at
  distance, landmarks placed, real-world units),
  https://www.tripo3d.ai/blog/explore/repo-character-model
- Wolf size/proportions: ASM Mammal Diversity via iNaturalist species guide
  (105–160 cm, 80–85 cm shoulder, tail 29–50 cm, ears 90–110 mm, skull
  230–280 mm), https://www.inaturalist.org/guide_taxa/889013 · San Diego Zoo
  Wildlife Alliance fact sheet (head-body, shoulder 26–36 in, narrow keel-like
  chest, long legs), https://ielc.libguides.com/sdzg/factsheets/graywolf/characteristics-page
- Wolf skull ratios: this project's `species-head-spec.md` §2.1 (ZB/L 0.53,
  braincase 0.32 L, rostrum 0.18 L, mandible 0.74 L, ear 0.36–0.40 L).
- Internal: BODY_PLANS.md (plan = rig configuration), PARTS_STANDARD.md
  (sockets), MUSCLE_TISSUE_MODEL.md (distribution read at block stage).
