# GRAVITY v5 — the system reaches the limbs

**Joe, Nov 12, 2026:** "keep learning and look up further lessons for
bara, etc, and apply it." v4 made fat a whole-*torso* system and was
accepted as the right direction ("a bit better now, even if not
perfect"). Its named remaining debit was the system boundary: it sat
at the arm and thigh roots, and the limbs stayed lean — a heavy torso
on a light frame. v5 removes that boundary. The system now ends where
anatomy says it should: at the wrists and ankles, with hands and feet
staying lean.

> **v5.1 addendum (Nov 12, 2026) — terminal tissue correction.**
> Joe: *"wrists and hands also need fat, not massive amounts but
> that is realistic."* He is right, and it corrects a claim made in
> this document: v5's distal fades ended at **zero**, and the text
> below says the system "ends where anatomy says it should: at the
> wrists and ankles, with hands and feet staying lean." That was L1
> read too absolutely — L1 says hands carry the *least* fat, not
> none. Pudgy hands are a heavy-body tell (dorsal hand pad,
> thickened finger bases, softened knuckles, wrist definition
> lost), and a zero endpoint erased it. **v5.1 = v5 + TERM**, a
> terminal component that stacks on the v5 combined target
> (`body.belly.protrusion_terminal_v51.target`); v1–v5 targets are
> untouched. Full detail in the addendum at the end of this file.

Same slider, same coupling, same anchor:

```
shape(w) = base + w * LIN5 + sign(w) * |w|^2.0 * SAG      (gamma = 2.0, as v3/v4)
D5  = D4 + INC          LIN5 = LIN4 + INC          SAG unchanged
INC(v) = m(v) * w_prox(s) * ( F_limb(v) * d_fade(s) - D4(v) )   on limb verts, else 0
```

The navel anchor is untouched and reproduces exactly (numpy 11.14 cm
forward / 6.99 down; Blender evaluated 11.27 / 6.99; +0.5 coupled
5.95 / 1.62 — all identical to v4, because the navel is not a limb
vertex). One counterintuitive bookkeeping fact: **the v5 combined
target moves fewer vertices than v4's (4,762 vs 6,104)**. v4's torso
field was evaluated off-gate on every vertex at torso heights, so
forearms and hands carried a spurious torso-band extrapolation; the
limb crossfade retires it. Part of the limb component's job is
subtraction.

## The limb reference addendum (L1–L5)

FAT_REFERENCE.md's rules cover limbs only in passing (R2 ordering,
R3 pooling sites, R10 thigh contact), so a small targeted reference
check was run before building, and its findings were treated with
the same discipline as R1–R10:

- **L1 — proximal gradient.** Limbs carry more fat near the torso:
  upper arm > forearm > hand (least; bone shows through), thigh >
  calf > ankle. Wrists, ankles, collarbones stay comparatively lean
  and hard. [Love Life Drawing, "How to draw fat"]
- **L2 — joints stay findable.** Fat accumulates *around* joints, not
  on top of them: pads behind the knee and around the elbow; the
  postdeltoid fat pad on the back of the upper arm is a named region
  (Richer, *Morpho: Fat and Skin Folds*). Elbow/knee landmarks
  persist under load.
- **L3 — underside pooling.** Upper-arm mass hangs on the underside
  (triceps/postdeltoid side); thigh mass pools outer + inner (R3
  restated for limbs; the subtrochanteric region under the hip is
  the thigh's named pad).
- **L4 — calf moderation.** The calf's subcutaneous layer is thin
  even in heavy legs (pinch ≈ 1.5–2 cm in liposuction candidates);
  calf shape is gastrocnemius-belly dominated. Gains belong over the
  muscle belly (upper shank) and taper hard to a lean ankle — never
  a uniform tube. [clinical / liposuction anatomy]
- **L5 — contact squish (R10).** Where thighs meet, they flatten.
  Measured here as a gap, handled (if ever needed) as a cap on the
  inner sector rather than interpenetration.

## Construction

**Limb-local transfer, same sources, one level down.** Each limb gets
an axis polyline extracted from cross-section centroids (legs:
z-bands, hip→ankle; arms: PCA-direction bands, shoulder→wrist),
binomial-smoothed — coarse sources (Fat Males: 2,024 verts) give
centroids that zigzag, and the first unsmoothed Fat Males leg axis
measured 115 cm on a 70 cm leg. Vertices are parametrised by
(s, φ): arc position and angle around the limb. φ is measured in
**mirrored right-limb space** — the torso kernel folded |θ| because
a torso is roughly left/right symmetric in cross-section; a limb is
not (inner thigh ≠ outer thigh), so φ runs the full circle and left
limbs are x-flipped for the angle only. Components kept: radial and
axial; tangential dropped, as in v1–v4.

**Sources.** The Fat Males full field (its body mesh carries arms
and legs) and the HIMBO "Chonky" recipe composed from its **arms and
legs blocks** — the blocks v4 excluded as outside its torso gate.
Atomic Muscle again contributes no transferable field: its FO4 NIF
vertex buffer defeated extraction in the v3 cross-check, so it stays
a field-level cross-check, as in v3/v4.

- **HIMBO carries 17 of the recipe's 22 limb blocks.** The missing
  five (ArmsDeltsShape, LegsThighSmoothCurve, LegsVastusMReduction,
  LegsCalfOut, LegsCalfSideIn) exist only on the SOS-variant mesh.
  Verified, not assumed: the SOS OSD's same-named blocks carry
  different vertex supports (LegsCalfWidth: 2,422 vs 4,009 verts),
  so they do not index the Vanilla base v4 used and cannot be
  composed onto it. Every primary mass slider is present; the five
  are shape refinements.
- **Calibration mirrors v4:** per-limb length-ratio scaling (arm and
  leg separately: FM 1.152/1.103, HIMBO 1.180/1.164), then HIMBO's
  alpha matched to Fat Males on the thigh band — mean |radial| over
  leg samples s∈[0.08, 0.45] — FM 2.92 cm vs HIMBO 4.49 cm scaled,
  giving **alpha_limb = 0.65**, inside the [0.5, 2.0] cap. The
  sources disagree on limbs far less than on the belly front (where
  v4's alpha capped at 2.0); on the thigh, HIMBO is the heavier of
  the two and gets pulled *down*.

**The crossfade is the silhouette guarantee.** Proximally
(w_prox → 0 across the first ~15% of the limb) a vertex keeps v4's
value, so the shoulder/hip junction inherits v4's accepted field;
distally the pure limb field takes over; at the ends a cosine fade
(d_fade) returns displacement to zero at the hands/feet. The fade
windows were re-anchored to the measured joints after the first
full run put +5.4 cm on the wrist and +5.5 cm on the ankle: wrist
sits at s≈0.72, ankle at s≈0.84 on the base profile, so the fades
now span s 0.58–0.82 (arm) and 0.70–0.90 (leg).

**Two disclosed reference-driven shapings** sit on the blend where
the sources' construction conflicts with the reference rules. Both
are hand-set, both are in the code at their call sites, and neither
is learned:

1. *Arm underside sector gain (R3/L3).* HIMBO's arm recipe is
   deltoid/biceps-led (muscle sliders) and Fat Males' arm is its
   coarsest region (kernel CV p95 2.54 cm), so the raw blend
   under-pools the underside. The blended arm radial gets a smooth
   sector gain toward φ_down (world-down in the arm's own frame,
   −2.12 rad), strength 1.0, mean-preserved over the arm region:
   mass moves to the underside, it is not added.
2. *Leg distal taper (L4).* The raw blend adds near-uniform radial
   (≈1.6 cm) from the knee to s=0.9, which tubes the shank. Leg
   radial is factored ×1.0 through the gastrocnemius belly
   (s ≤ 0.68), → 0.55 at s=0.85, → 0.35 at s=1.0, under the distal
   fade.

**Fold machinery** is v4's, widened: graph smoothing and the
κ = 0.55 slope limiter on the increment, then attenuation repair
against **all 26,756 body faces** on both bases (raw + macro). The
repair converged at full increment scale in **2 rounds, min
attenuation 0.59, only 29 verts attenuated below 0.99** — the limb
fields are intrinsically smooth where the torso's crease zones were
not (v4: 4 rounds / 67 verts; v3: 40 rounds / 509).

## QA scorecard

### Fold gate (hard gate: 0 flips at +1, full affected surface)

| state | v4 raw | v4 macro | v5 raw | v5 macro |
|---|---|---|---|---|
| −1 (linear) | 183 ✗ | 170 ✗ | 184 ✗ | 162 ✗ |
| +0.5 (coupled) | 0 (0.481) | 0 (0.587) | 0 (0.450) | 0 (0.587) |
| **+1 (combined)** | **0 (0.116)** | **0 (0.0051)** | **0 (0.070)** | **0 (0.0018)** |
| +1.05 (combined) | 0 (0.082) | 8 ✗ | 0 (0.050) | 11 ✗ |

(min-dot in parentheses.) Blender evaluated mesh at +1: belly region
918 faces, **0 flips, min-dot 0.021**; all body faces (13,378
polygons ≈ the same 26,756-triangle surface), **0 flips, min-dot
0.021**. The −1 pole and the +1.05 macro folds are inherited v4
behaviour, unchanged in character; the gate state (+1) is clean on
every base and in Blender. The macro +1 margin (0.0018) is thin —
see self-critique.

### Torso scorecard re-run (corrected definitions; v5 must not damage v4)

| metric | v4 | v5 | |
|---|---|---|---|
| M1 below-navel share | 63.1% | 63.0% | — |
| M2 apron bottom above crotch | 8.81 cm | 8.99 cm | — |
| M3 waist girth (narrowest) | 85.5 cm | 85.5 cm | — |
| M3 hip girth | 102.9 cm | **104.1 cm** | +1.2: legitimate hip/thigh-root mass now inside the window |
| M3 ratio (narrowest) | 0.831 | 0.822 | follows the hip |
| M3 navel-level girth | 117.4 cm | 117.4 cm | — |
| M9 waist/height | 0.513 | 0.513 | — |
| flank roll peak | h 0.279, 45.1 cm | h 0.279, 44.7 cm | — |
| flank pinch above roll | 10.3 cm | 9.9 cm | — |
| M5 back radial | 5.59 cm | 5.59 cm | — |
| M6 chest front radial | 1.77 cm | 1.77 cm | — |

### Limb metrics at +1 (right = left; girths in cm)

| point | s | base | v4 | v5 | gain |
|---|---|---|---|---|---|
| upper-arm tube | 0.36 | 23.8 | 24.3 | 30.0 | **+6.2** |
| elbow (landmark) | 0.56 | 16.5 | — | 22.2 | +5.7 |
| forearm | 0.64 | 16.2 | 15.9 | 21.5 | **+5.4** |
| wrist | 0.72 | 16.0 | 16.4 | 17.8 | **+1.9** |
| mid-thigh | 0.26 | 43.0 | 43.0 | 59.9 | **+17.0** |
| knee (landmark) | 0.52→0.56 | 33.4 | — | 43.9 | +10.5 |
| calf belly | 0.60 | 34.6 | 34.6 | 44.9 | **+10.3** |
| ankle | 0.84 | 22.2 | 22.2 | 24.4 | **+2.2** |

- **L1 ordering holds on both limbs:** upper arm +6.2 > forearm
  +5.4 > wrist +1.9; thigh +17.0 > calf +10.3 > ankle +2.2.
- **Pooling (L3):** upper-arm field radial, back/underside sector
  **1.81 cm** vs front **0.45 cm** (totals on the shipped mesh:
  1.67 vs 0.38). The postdeltoid/back quadrant carries the arm's
  largest radial in the per-φ probe (+2.1 cm), as the reference
  names it.
- **Landmarks (L2):** the knee's girth-profile minimum is an
  interior minimum before (s 0.52) and after (s 0.56) — it
  persists. The elbow has no interior minimum in either state on
  this base (the arm tapers monotonically through the joint); the
  elbow zone gains less than the upper arm (+5.7 vs +6.2), i.e. it
  is not preferentially padded. See the critique for the knee's
  shallowness.
- **Boundary step ratios** (deformed vs base max profile gradient;
  1.0 = no added step): arm proximal 0.85, arm joint 1.00, leg
  proximal 0.70, leg joint 1.71. Three of four add no step at all;
  the knee window steepens because the knee zone itself gains mass
  (next section).
- **Inner thighs (R10/L5):** closest-band gap **7.16 cm at base →
  6.38 cm at +1** (top band, z = −0.105). **The thighs do not meet
  at +1 on this base.** The contact cap machinery was armed and
  never fired. Reported, not faked: closing the last 6.4 cm would
  need either a higher weight or a wider-hipped base, and inflating
  the inner sector past the sources to force contact is exactly
  the parametric-guess failure v4 retired.
- **Field quality (5-fold CV, as v4):** HIMBO arm p50 0.14 / p95
  0.47 cm (3,322 samples); HIMBO leg 0.35 / 1.81 (3,422); Fat Males
  arm 0.53 / 2.54 (594); Fat Males leg 0.47 / 2.43 (1,084). HIMBO
  carries the limb detail; Fat Males' limb data is its coarsest.

## Measurement traps caught during the build

Kept here because each produced a plausible-looking wrong number
first — the same failure family as v4's corrected metrics:

1. **Reversed leg axis (run 1).** Leg polylines were built
   ankle→hip while everything downstream assumed proximal-first, so
   the crossfade and distal fade acted on the wrong ends and the
   "thigh" metrics were calf metrics. The torso scorecard exposed
   it (hip girth *dropped* 5.6 cm — the fade was erasing v4's hip
   field). Fixed by construction order + smoothing; the torso
   scorecard returning to ≈v4 was the acceptance signal.
2. **Phantom thigh overlap (run 2).** Min/max band extents reported
   the *undeformed base* as interpenetrating by 12 cm: midline
   perineum vertices sit inside both legs' axis gates and poison
   extrema. A contact cap fired on the phantom and cut the inner
   thigh field to 0.40 before the probe caught it. Gap is now
   measured side-correct with percentile extents (base gap
   +7.16 cm, sane).
3. **Pose-confounded pooling test (run 2).** A world-vertical
   "underside" sector read −0.09 cm and looked like an L3 failure;
   on this posed arm the underside is the back-inner quadrant, and
   the anatomical-sector test shows the field pooling exactly
   where L3 says (back 1.81 vs front 0.45).

## Honest self-critique

- **The knee is the shallowest landmark.** Its dip persists, but
  the joint-line girth gains +10.5 cm — nearly the calf belly's
  gain — so at +1 the dip is only ~1 cm below the calf. L2's pads
  *around* the knee are in the sources (LegsKneePit 0.57 is
  literally a behind-knee pad), but the full-ring gain at the joint
  line is more than "around". A narrow joint-line moderation was
  considered and rejected: with two disclosed shapings already in
  the field, a third hand-cut would start authoring the limb
  outright. Flagged as the first thing to revisit if a better limb
  reference set (or the SOS-variant blocks on their own base) ever
  lands.
- **Thighs don't meet.** R10 is approached (7.2 → 6.4 cm) and not
  reached at +1. On this lean, narrow-stance base that is the
  honest answer; contact belongs to higher weights.
- **The macro-base +1 margin is thin** (min-dot 0.0018, vs raw
  0.070 and Blender-evaluated 0.021). The limiting face sits in a
  crease zone the repair attenuates to the same floor in every run;
  it is positive and the gate is met, but there is little headroom
  — stacking another aggressive field on v5 without re-running the
  repair would be unwise.
- **The arm is fat-led, not muscle-led.** Upper arm +6.2 cm at +1
  reads soft in the renders, softer than peak bara. That is the
  calibration working as designed (alpha matched to Fat Males, the
  fat authority); muscle mass is a different slider's job in the
  stack. But if Joe wants the Chonky silhouette at full recipe
  strength, alpha_limb is the single knob (0.65 → 1.0 would take
  the thigh band to the HIMBO recipe's own 4.49 cm).
- **Fat Males' limb fields are coarse** (CV p95 ≈ 2.4–2.5 cm, worst
  of any field in the system). The blend leans on HIMBO for limb
  detail, which makes the limb layer stylistically more "preset"
  and less "measured" than the torso layer. A denser fat-limb
  reference is the highest-value future source for this slider.
- The slope limiter still hits its 80-iteration cap on the raw
  increment (repair converges regardless); the −1 pole still folds
  (184/162), inherited from every prior version and out of scope
  here, as before.

## Files

- `body.belly.protrusion_v5.target` — combined field at +1 (LIN5 + SAG)
- `body.belly.protrusion_limb_v5.target` — the limb component
  (= D5 − D4; a crossfade increment, apply on top of v4, not standalone)
- `body.belly.protrusion.slider_v5.json` — slider definition + full QA
- `scripts/build_belly_v5.py`, `scripts/test_belly_v5.py`,
  `scripts/finalize_v5.py`; numbers in `work/qa_numbers_v5.json`,
  `work/blender_v5_numbers.json`, `work/belly_v5.npz`
- Renders: `renders/belly_v5_w+1.0_{front,profile,threequarter}.png`,
  `renders/belly_v5_w+0.5_profile.png`,
  `renders/belly_v4_vs_v5_{front,profile}.png`

Provenance as v1–v4: study-only, internal; not a CC0 MakeHuman
asset; do not redistribute. v1–v4 files untouched.

---

## v5.1 addendum — terminal tissue (Nov 12, 2026)

**Joe:** "wrists and hands also need fat, not massive amounts but
that is realistic."

```
D51 = D5 + TERM     TERM is linear: shape(w) = base + w*(LIN5+TERM)
                    + sign(w)|w|^2.0 * SAG
```

**Source — measured, not guessed.** The Fat Males set ships
separate `malehands_0/_1` and `malefeet_0/_1` meshes, and the
original PoC extracted their exact same-topology deltas into the
learned library (hands mean 0.150 / max 0.501 Skyrim units; feet
mean 0.384 / max 1.520). v5.1's zone gains are those deltas'
perpendicular (radial) zone means, scaled by the hand/foot length
ratio to hm08 (hand 0.642, foot 0.692):

| zone | FM perp mean | scaled gain |
|---|---|---|
| wrist | 4.35 mm | 2.80 mm |
| palm | 2.36 mm | 1.52 mm |
| proximal finger | 2.91 mm | 1.87 mm |
| distal finger | 1.51 mm | 0.97 mm |
| ankle/heel | 7.29 mm | 5.04 mm |
| midfoot | 5.16 mm | 3.57 mm |
| toes | 3.09 mm | 2.14 mm |

Sector shaping (hand dorsal > lateral > palmar; foot dorsal >
side > sole) and the knuckle-softening term are anatomical
shaping [E] over those measured magnitudes [S]. Two calibrations,
both solved to **1.000** — the scaled source itself, not an
inflation: CAL on composed wrist girth (target +3.0 cm total) and
FBOOST on fingers 2–5 proximal thickness (target 0.150 mean
radial). Per-vert caps do the policing: proximal finger radial
≤ 20% of local radius (the specified band's ceiling; it binds on
the dorsal sector), mid/distal ≤ 15%; a **contact cap** (≤ 45% of
the distance to the nearest other-digit vertex + 0.3 mm) routes
finger growth into the free sectors — contact faces flatten
instead of interpenetrating, the L5 squish principle one scale
down. The FM ankle/heel zone conflates heel pad + ankle + shin
splash, so the ankle *ring* is capped at ~1.7 mm and the excess is
routed to the heel/dorsal zones. Feet got the same treatment as
hands for symmetry — Joe named hands; the principle is terminal,
not manual.

**Segmentation lesson (worth the three attempts it took).** The
hm08 hand is one webbed mesh whose fingers rest ~2 mm apart, and
every geometric segmentation failed on it: lateral-gap splitting
(1 cluster), euclidean linkage (1 cluster), and a geodesic
fingertip watershed (split two fingers, merged two others —
euclidean seed suppression cannot tell same-tip verts from
neighbouring tips). What works is the **MPFB default rig's finger
bone skin weights**: digit = argmax finger group, segment =
dominant segment bone — sizes 197 (thumb) / 301 / 298 / 295 / 301,
clean on both hands. The **dorsal sign** has its own trap: the
fingertip-curl cue flipped it in the first run (the palmar side
silently received the dorsal weighting; caught because the
"palmar" render showed fingernails). The decisive cue is in
base.obj's joint helpers: the thumb's first joint sits **8.2 mm
palmar** to the finger MCP plane. Both are now the standing
method for hand work on this base.

**QA.**

- Fold gate: **0 flips at +1 over all 26,756 body faces, both
  bases** (raw min-dot 0.070, macro 0.0018 — identical to v5; the
  limiting face is v5's torso crease, the terminal field does not
  touch it). Blender evaluated mesh: 0 flips, min-dot 0.0214,
  also identical to v5. No attenuation repair was needed.
- Wrist girth: 15.98 → 17.83 (v5) → **18.96 cm (+2.98 total)**,
  inside the 2.5–3.5 band. Ankle: 22.24 → 24.42 → **25.57 cm
  (+3.32 total)**.
- Proximal fingers: mean radial thickness gain **13.5–15.4%** per
  finger (thumb 12.8% radial / 14.9% dorsal-palmar) — the foot of
  the specified ~15–20% band, reached at the source's own
  magnitude; dorsal-palmar thickness reads 11.8–11.9% on fingers
  because the lateral sectors are contact-capped, by design.
- Inter-digit: minimum pairwise distance 2.11 → **1.01 mm**; zero
  new sub-0.3 mm close pairs; digit centroid separations
  preserved (ratio 1.000). No webbing blowouts.
- Renders: `renders/belly_v51_hand_dorsal_{base,w+1.0}.png`,
  `belly_v51_hand_palmar_w+1.0.png`, `belly_v51_foot_w+1.0.png`,
  `belly_v51_w+1.0_front.png`. The dorsal view (nails, knuckles)
  at +1 reads subtly fuller with softened knuckle relief — the
  correct scale for ~1.3–2.0 mm of tissue; anything louder would
  be the "massive amounts" Joe ruled out.

**Files.** `body.belly.protrusion_terminal_v51.target` (5,590
moved verts), `body.belly.protrusion_v5.1.target` (combined),
`body.belly.protrusion.slider_v5.1.json`,
`scripts/build_belly_v51.py`, `scripts/test_belly_v51.py`,
`scripts/finalize_v51.py`; numbers in `work/qa_numbers_v51.json`,
`work/blender_v51_numbers.json`, `work/belly_v51.npz`. The
regional-tissue profile in MUSCLE_TISSUE_MODEL.md §4 now carries
hand/foot entries (0.12 / 0.15 [E]) — they were absent there,
which was the same zero-endpoint assumption in profile form.
