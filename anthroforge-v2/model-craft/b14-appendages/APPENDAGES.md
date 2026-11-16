# Appendages — Tails / Ears / Horns / Wing-Arm Construction Rules

**Agent B14, model-craft wave, Nov 12, 2026.**
**Agrees with:** `PARTS_STANDARD.md` (sockets, classes, cost formula,
fit gate) · `species-head-spec.md` (ear slider families, tip families)
· `BODY_PLANS.md` §3.5 (wing chain template and state set).
**Companion artefacts:** `parts/` (GLB + STL + `*.part.json` records),
`assembly.blend`, `renders/`, `scripts/build_parts.py`,
`scripts/fixup_render.py`.

Three parts were modelled to prove the rules: a bushy canine tail
(class A, `tail.base`), an upright canine ear pair (class A, `ear.L/R`),
and a curved horn pair (class B, `head.top`). Wing-arm rules are
specified (§5) but no wing was modelled in this pass — the library's
only build-tier wing donor is still the styloo butterfly (PARTS_STANDARD
§6, pack #9) and a from-scratch wing deserves its own pass.

All dimensions are for a ~1.8 m biped at neutral sliders, in metres,
in each part's **local socket frame** (origin = socket anchor).

---

## 1. Shared appendage principles

- **A1 — Two-layer construction for anything furred.** A lean
  *skeletal core* carries the silhouette's structure and the skinning;
  a separate *volume shell* carries the fur mass. The two have
  different radius profiles (§2) and must never be merged: sliders
  that change "bushiness" act on the shell, sliders that change pose
  act through the core's chain. (Same lesson as the head: structure
  first, tissue over it.)
- **A2 — Bases are skirts, not cut edges.** Every socketed part extends
  a narrowing skirt *into* the base's fit volume (tail base cone,
  ear skirt rows, horn base flare). A part that ends exactly at the
  surface shows its rim the moment the base deforms. The socket fit
  volumes in PARTS_STANDARD §2 are sized for this: ear cone depth
  0.05 m, tail rump cone base Ø 0.08 m.
- **A3 — Cross-sections are placed by parallel transport, never by
  world-axis rings.** Any curved appendage (tail, horn, ear centreline)
  is a tube/sheet swept along a Catmull-Rom spine with
  parallel-transport frames; world-axis rings shear on curves and the
  shear reads as a kink at render distance.
- **A4 — Colour is structure.** Vertex-colour zones are authored with
  the geometry, not painted later: dorsal/ventral coat split on the
  tail, pale inner-ear material zone, keratin base→tip gradient on
  horns. These are the zones the materials/markings systems bind to
  (`fur.accepts` in the part records).

## 2. Tails — curve, taper, volume

Reference build: `tail_canine_bushy` — 312 verts / 616 tris / 6 bones,
**7 points** (major class cap 25). Spine length ≈ 0.55 m.

- **T1 — The curve is a resting S, not an arc.** Canine tail carriage:
  leaves the rump angled down (~20–25° below horizontal), bottoms out
  at 25–35% of length, then rises so the tip points up-forward. A
  single-radius arc reads as a banana; the down-then-up S is what
  makes it read as *canine* at silhouette distance. Control points
  (socket frame, −Y back, +Z up): (0, .005, .002), (0, −.075, −.028),
  (0, −.155, −.030), (0, −.235, .005), (0, −.300, .065),
  (0, −.345, .135), (0, −.365, .185), (0, −.370, .215).
- **T2 — Core taper is monotonic and gentle.** Skeletal core radius:
  30 mm at base → 22 mm at mid → 7 mm at tip, no local pinch anywhere
  (a pinch in the core becomes a hinge crease under chain bending).
  The core is the bend-safety layer: it may look plain, it may not kink.
- **T3 — Fur volume peaks distal of middle, never at the base.**
  Shell radius profile: 50 mm base → 84 mm peak at **t ≈ 0.55** →
  24 mm tip. This is the bushy/sleek discriminator: a sleek tail's
  shell ≈ core + ~8 mm everywhere (near-constant offset); a bushy
  tail's shell/core ratio peaks at ~3.8× around 55–65% and the tip
  tuft is the shell collapsing back to the core, not a separate blob.
  Volume at the base is the amateur error — it reads as a rump tumour
  because real tail fur is shortest where the tail meets the body.
- **T4 — Shell ripple is small and high-frequency.** ±3.5% radius
  modulation (two crossed sine terms) breaks the lathe-perfect read.
  Above ~5% it reads as lumps; at 0% it reads as a pool noodle.
- **T5 — Chain: 6 bones is the sweet spot for 0.5–0.6 m.** Module
  chain per PARTS_STANDARD (5–8 allowed). Weights are triangular
  blends over spine parameter t (each ring shared by ≤ 2 bones);
  ring-per-bone density ≥ 2.5 keeps the S-curve smooth under sway.
  `function.tail` sway donor values: amp 12°, 0.6 Hz.
- **T6 — Coat split follows gravity, not the seam.** Dorsal dark /
  ventral pale split is computed from the ring frame's up component,
  so the pale underside stays underneath when the chain bends.
  Distal third darkens again (canine tail-tip pattern).

## 3. Ears — base fold, inner ear, tip families

Reference build: `ear_canine_upright` — 265 verts / 500 tris / 4 bones
per ear, **5 points** per ear (standard anatomy cap 12). Pinna length
0.115 m = 0.38 L (wolf band 0.36–0.40, species-head-spec §2.1).

- **E1 — An ear is a folded sheet, not a cone and not a fin.** The
  pinna is a parametric sheet (width × height grid) with three
  simultaneous deformations: **cup** (cross-section arcs forward,
  depth ~20 mm at mid-height, flattening to the tip), **lean**
  (centreline tips backward ~16 mm over the height and cants
  ~10 mm outward), and **tip taper** (width profile: 60 mm base →
  88 mm at 38% → point). Remove any one and it stops reading as an ear.
- **E2 — The base fold is geometry, and it needs a skirt.** The bottom
  ~35% of the sheet twists (~20°) as it narrows into the skull — this
  twist is the base fold that lets one flat-ish sheet sit on a round
  skull. Below that, two skirt rows continue 15 mm *into* the skull
  cone, narrowing to 76%: a sheet that ends at the surface line shows
  its bottom corners floating off the curved skull (caught in this
  pass's first render — see §6).
- **E3 — Thickness is real but minimal.** Solidify 2.2 mm. Zero-
  thickness sheets break under closeups and print export; more than
  ~3 mm at this scale reads as a foam fursuit ear.
- **E4 — The inner ear is a separate, inset sheet — never a texture.**
  Inset to 74% width, spanning v 0.16–0.90, floated ~4 mm forward of
  the outer sheet's cup floor, with its own shallower cup. It carries
  the pale inner-ear material zone (`fur.accepts: ear.inner`) and the
  **tragus ridge**: a low gaussian bump low-centre on the inner sheet
  — the single cheapest detail that makes an ear read as anatomy
  instead of a leaf.
- **E5 — Tip families are topology variants on one base** (head spec
  §3): pointed (this build), rounded (tip rows collapse to a wide arc
  instead of a point), tufted (point + a class-C tuft on the tip),
  fold (mid-sheet hinge — needs its own chain split). Only the tip
  rows change; base, fold, inner sheet and weights are shared, so
  all four variants price and fit identically.
- **E6 — Carriage is placement + chain, not geometry.** The geometry
  is authored neutral-upright. Carriage at equip: yaw ~21° (plane
  faces forward-out), cant ~22°, lean-back ~10°, then the 4-bone
  module chain (EarBase→Ear1→Ear2→EarTip, weights triangular over
  height) serves expression (`function.ear` carriage −30°…+45°).
  Authoring carriage into the mesh would bake one emotion into the part.
- **E7 — Size is a species statement.** EarLength is the head spec's
  widest-range slider for a reason (wolf 0.36–0.40 L, red fox
  0.6–0.75 L, fennec ≥ 1.0 L): the same ear part re-fits across that
  range via `rescale_by: head.ear.height`; what changes at fennec
  scale is the inner-ear zone (enlarged, furred — a variant, E5-style),
  not the construction.

## 4. Horns & antlers — growth-direction forms

Reference build: `horns_curved_pair` — 304 verts / 600 tris / rigid,
**1 point**. Length ≈ 0.21 m per horn; bases at ±36 mm on the poll.

- **H1 — A horn is a growth curve, not a bent cone.** The spine is
  the growth direction history: emerge tilted (this build: back and
  out from the poll), sweep up-back-out, and let the tip curl
  *against* the sweep (here: forward-down at the last 15%). The tip
  curl direction is the species signature — ibex curls back-down,
  kudu spirals, dragon horns (this build's brief) sweep and hook.
- **H2 — Section morphs along the length.** Near-elliptical at the
  base (wide axis across the skull, ratio ~1.2), rounding by mid,
  near-round at the tip. A constant circular section reads as a
  manufactured peg; the ellipse is also structural honesty — horn
  cores are loaded in the sweep plane.
- **H3 — Taper is convex, never linear.** Radius stops: 24.5 mm base →
  16.8 at 45% → 7.2 at 88% → 1.6 tip. Linear taper reads as a traffic
  cone; the convex curve (fast early narrowing, long fine tip) is
  what keratin growth actually produces.
- **H4 — Growth annuli are radius modulation.** ±3.8% sinusoidal
  radius ripple, wavelength ≈ length/7.5, amplitude fading to the
  tip. Rings are the horn's age lines; making them a normal-map-only
  effect loses them at silhouette distance, where horns are read.
- **H5 — Keratin gradient: light base, dark polished tip.** Vertex
  colour from grey-brown at the base to near-black at the tip with a
  t^1.4 curve (the darkening concentrates distally), roughness
  dropping along the same axis (worn smooth at the tip).
- **H6 — Class discipline.** Horn *cores* are class B rigid (they do
  not bend; PARTS_STANDARD socket 9). **Antlers are class A**: they
  are branched (each tine is a section-morph branch off the main
  beam, same rules H1–H4 per branch) and they sway — a rigid antler
  is the Bento folded-wing error again. Branch points sit at growth
  stops, never mid-annulus.

## 5. Wings — arm structure (specification only this pass)

Per BODY_PLANS §3.5, restated as construction rules:

- **W1 — The wing is an arm, not a fan bolted to a back.** The main
  chain Wing1→Wing5 is a limb: root at the chest/withers socket,
  one elbow-class joint (Wing2/Wing3), one wrist-class joint (Wing3),
  then the hand-equivalent span. Fold geometry is limb-fold geometry:
  a wing that cannot fold like an arm cannot wear the `folded` state.
- **W2 — Fan branches are fingers.** Membrane wings: fan branches at
  the wrist (WingFan1) and Wing4 (WingFan2) are finger rays — they
  spread, they don't just trail; membrane is skinned *between* rays
  and must carry slack in `folded` (a membrane taut in fold pose is
  the wing equivalent of the ear's floating corners). Feathered
  wings: the same branches are feather-*group* bones (primaries /
  secondaries / coverts); per-feather bones are not required for the
  groups to fan and overlap.
- **W3 — Root construction mirrors the tail base.** The root patch
  (0.10 × 0.14 m) gets a skirt into the back's fit volume and the
  first segment is the thickest of the chain — wing roots fail
  visually exactly like tail bases do when the volume peaks at the
  joint instead of just distal of it (T3's rule, transposed).
- **W4 — States are the part family's, always.** `folded, relaxed,
  spread, flap, glide, display` — a wing part that ships without its
  state poses is unfinished in the same way a jaw without gape limits
  is; Bento's lesson (§1.7 of BODY_PLANS) is that an unanimated wing
  does nothing, so the poses are part of the part.

## 6. Fit, cost, and what the renders caught

Fit scored with `parts-lab/fit_score.py` (resolution 128) against the
mounting bases, parts in their placed frames; base-ring seating
distance (mean distance from the part's base ring verts to the base
surface) is reported alongside, because the buried/engaged score is
designed for *inset* parts (teeth, gums, tongues) — a proud appendage
(ear, horn, tail) legitimately puts most of its verts far from the
base surface, so its seating evidence is the base ring, not the
whole-mesh engagement. Measured 2026-11-12 (fit_score at default
resolution; seating via KDTree from part verts to base surface verts,
patch = mean distance of the closest 5 % of part verts — for a seated
appendage that patch is the contact ring):

| Part | Points (cap) | Class / socket | fit_score | buried % | engaged % | excess % | out-of-grid % | seating patch |
|---|---|---|---|---|---|---|---|---|
| tail_canine_bushy | 7 (25, major) | A / tail.base | 0.090 | 39.7 | 9.8 | 8.3 | 42.2 | 2.6 wolf-units ≈ 0.5 % of torso scale (min 1.4) |
| ear_canine_upright (per ear) | 5 (12, standard) | A / ear.L/R | 0.106 | 1.4 | 10.6 | 0.0 | 77.7 | 0.022 L (min 0.006 L) |
| horns_curved_pair | 1 (12, standard) | B / head.top | 0.070 | 2.8 | 7.0 | 0.0 | 90.0 | 0.023 L (min 0.011 L) |

How to read this — the headline `fit_score` verdict ("poor") does
**not** apply to proud appendages, for the reason in the preamble plus
one more the runs exposed: the scorer's grid is built around the
*base's* bounding box, so 78–90 % of an ear's or horn's vertices fall
**outside the grid entirely** (out-of-grid column) and can never count
as engaged. The appendage gates are the other columns:

- **Excess burial 0 %** for ear and horn — nothing swallowed or
  mis-scaled; burial is only the designed skirt/root (1.4 % / 2.8 %).
- **Seating patch ≈ 0.02 L** for both head parts: the contact ring
  sits ~2 % of head length off the surface rather than intersecting
  it, because the head's own ear-base nubs forced the mounts that far
  proud (see render notes). At render distance the joint reads
  seamless, but a production mount should consume the nub (merge into
  the tissue layer) or deepen the skirt by ~0.02 L. Recorded as a
  known tolerance, not hidden.
- **Tail: 39.7 % buried is the root, by design.** The mount derives
  from the pelvis weight-cluster centroid — an interior point — so
  the proximal shell sits inside the rump and *emerges* through the
  surface, the way a real tail root does; the 8.3 % "excess" is the
  deep part of that same root. The seating patch (2.6 units on a
  ~490-unit torso scale) confirms the shell crosses the surface right
  at the mount. Judged on emergence + renders, not the inset rubric.

Render review (this pass, `renders/`):
- **Caught & fixed — horn pair origin.** First build put both horn
  bases at one central point (each horn authored from its own
  origin); on the head they read as a single curled tuft. Fix: pair
  spacing baked into the geometry (bases at ±36 mm, file origin =
  midpoint). Rule recorded in H1's build notes: *a pair part's file
  origin is the pair's centre, never one member's base.*
- **Caught & fixed — scale discipline.** The neutral head v3 is
  authored in head-length units (bbox = 1.0 L), not metres. Parts are
  true-metre; the assembly scales them ×3.3 (ears) / ×3.0 (horns).
  All ratios in this document are scale-free, but any cross-asset
  assembly must check the base's unit convention first — the fit
  score is frame-relative and would have hidden this completely.
- **Caught & mostly fixed — ear base corners.** First skirtless build
  left the sheet's bottom corners floating off the skull (visible in
  the first closeup as a hanging fin). Fixed by E2's buried skirt
  rows. A second, similar-looking fin in later closeups turned out to
  be the *base head's own* ear-base nub (v3 TissueHead) at its native
  ear site — the ear GLB is clean standalone. The ears were re-mounted
  onto the real sites (±0.295, −0.150, 0.185 in head units, pitched/
  rolled to the nub's axis), which is also what set the ~0.02 L
  seating tolerance above; a small pointed bit of the nub still
  peeks below the ear base in the final closeup. Fully clearing it
  needs the nub merged into the tissue layer — a base-head fix, not
  a part fix.
- **Noted — tail render presentation.** The wolf body and the tail
  are both near-black; at honest materials the tail is illegible
  against the rump in stills. `tail_on_wolf_rump.png` therefore uses
  a warm-tan highlight material on the placed tail shell only
  (geometry untouched). Even so, the still only evidences the
  *emergence* — the rump crop occludes most of the curve from every
  angle tried (three attempts); the full S-curve is judged from
  `parts_lineup.png` and the §6 fit numbers instead. The shipped
  part keeps its authored vertex-colour coat.
- **Noted, not fixed — material wash.** The prototype vertex-colour
  materials read pale under the lab lighting (Filmic + area lights);
  geometry zones are correct in the data. Material calibration
  belongs to the materials wave, not this one.
- **Noted — the wolf rig has no tail bones.** The CVRxEarth "wolf"
  is a Mixamo humanoid rig (222 bones, none caudal). The tail was
  anchored from the evaluated mesh's skin-weight landmark clusters
  (Hips centroid + back ≈86 mm, up ≈11 mm at real scale; facing from
  the foot/toe clusters, since the bind pose is reclined). A
  library truth worth recording in the pack notes: our reference
  canine base cannot pose its tail; tail chains arrive *with the
  part*, which is exactly the module-chain design in PARTS_STANDARD.

## 7. Deliverables

- `parts/tail_canine_bushy.glb` (+ .stl, .part.json) — class A, 7 pts
- `parts/ear_canine_upright_R.glb`, `ear_canine_upright_L.glb`
  (+ .stl, shared .part.json) — class A, 5 pts per ear
- `parts/horns_curved_pair.glb` (+ .stl, .part.json) — class B, 1 pt
- `assembly.blend` — head v3 with ears + horns mounted (its own ears
  hidden), wolf at +3 m X with the tail mounted on a rump crop
- `renders/` — head_front, head_threequarter, ear_closeup,
  tail_on_wolf_rump, parts_lineup
- `scripts/build_parts.py`, `scripts/renders_fix.py` (definitive
  assembly/render pass), `scripts/fixup_render.py`,
  `scripts/assemble_render.py`, `scripts/final_render.py`
  (superseded iterations; kept for history)
