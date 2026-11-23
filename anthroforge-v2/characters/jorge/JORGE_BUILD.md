# JORGE_BUILD — Jorge's body, composed from his preset vector

**Date:** Nov 16, 2026 · **Tasking (Joe):** body shapes first — NO fur, NO
renders, NO head; numeric QA only. Sen stage 1 is the pattern
(`../characters/sen/SEN_BUILD.md`).

**Deliverables in this folder**

| file | what |
|---|---|
| `jorge_body.glb` | composed body, **unrigged static bake** (no skin, no morphs, no head, no fur), baked at export scale ×1.39 — 13,380 verts / 26,756 tris, extent 2.319 m |
| `targets/body.muscle.target` | muscle component at Jorge's vector (Muscle **0.45**) |
| `targets/body.chest.width.target` | broadness component |
| `targets/body.tissue.jorge.target` | tissue component (belly = v4 system, τ = 0.60) |
| `targets/body.belly.protrusion_terminal_v51.target` | v5.1 terminal component ×0.60 |
| `targets/body.jorge.target` | combined convenience target (sum of the four) |
| `work/qa_jorge_body.json` | full numeric record (recipes, CV, grades, gates) |
| `work/jorge_fields.npz` | float fields + shipped quantised components |
| `scripts/build_jorge.py` | the build (bara-proof machinery, verbatim kernels) |
| `scripts/gate_check_jorge.py` | independent ship-gate re-check from disk |
| `scripts/export_glb.py` | the GLB exporter |

**Base:** MakeHuman **hm08** (MPFB macro base for grading; raw base.obj
frame as the second fold-gate basis) — identical base and machinery to
Sen's build; the undeformed base grades byte-identical numbers to Sen's
run (height 1.666 m, volume 51.21 L), which is the parity check.

**Composition** (Sen pattern):
`delta = muscle + chest.width + tissue.jorge + terminal×0.60`, HIMBO
granular fields composed on the HIMBO base and kernel-transferred to
hm08; belly from the accepted v4 whole-torso system.

---

## 1. Vector applied

From `anthroforge-app/library/presets/jorge.afchar.json` (derivation:
`presets-titan-batch1.md` §5.2). All 41 record sliders accounted for:

- **Muscle (24 entries)** — Muscle **0.45** (the watch item, §3),
  TorsoMass 1.00, TorsoLower 1.00, LegsSize 1.00, LegsThigh 1.00,
  PecsSize 0.95, PecsWidth 0.95, ArmsTrapsMeat 0.90, PecsMass 0.85,
  TorsoBackSize 0.85, ArmsFore 0.85, LegsCalfSize 0.85, ArmsTraps 0.80,
  ArmsDelts 0.80, LegsCalfWidth 0.80, ArmsBiceps 0.75, LegsGlutes 0.75,
  ButtBooty 0.75, ArmsTrapsPush 0.70, ArmsBrachio 0.70, PecsLower 0.65,
  PecsClavicle 0.60, BubbleButt 0.50, BodyMass 0.25. NeckMass authored
  from the `Weight 0 to 1` block at **0.95**, gated to the neck band.
- **Width (3)** — TorsoWidth 0.90, ArmsShoulders 0.85, TorsoBackShape 0.70.
- **Tissue (8)** — Chubby 0.85, TorsoMassSmooth 0.85, LegsChubby 0.80,
  BellySmooth 0.80, TorsoBellyLHandles 0.65, PecsSaggy 0.50,
  ButtSaggy 0.35, TrapsValleys 0.20 (definition rides tissue, Sen mapping).
- **Belly drive** — τ := **BellyPot 0.60**, fixed. The strongman build's
  chest:waist ≥ 1.30 ratio-solve does NOT apply to Jorge's cell; his
  ratio is measured and reported (§3), not solved.
- **Terminal** — v5.1 terminal component × **0.60** (v5.1
  linear-component semantics at w = BellyPot). Max displacement
  0.18 cm — hands/feet only.
- **Composes ZERO — vocabulary gap (5 entries):** BodyMass 0.25,
  PecsLower 0.65, BubbleButt 0.50, **TorsoMassSmooth 0.85**,
  **BellySmooth 0.80**. None has a block in `HIMBO Body - Vanilla.osd`,
  the machinery's vocabulary (the build log carries the five loud
  `hi_diff` warnings). All five exist in `SOS.osd`, but that file's base
  runs to vert index 11006 (~11k verts) vs the Vanilla base's 9,346 —
  its diffs are **not index-compatible** with this machinery without new
  verification. Same gap as Sen's shipped build; it is Joe's already-open
  decision (see `../bara-proof/FIX_NECK_FIELD.md`). No substitutes were
  used — swapping in e.g. `PecsLowerSide` would corrupt the watch-item
  evidence. **Effect: this build understates Jorge's softness** — and
  MassSmooth is, per §5.2, most of the intended Sen/Jorge tissue
  difference.
- **Excluded with bara-proof precedent:** Lean −1.00 (two-sided,
  sign-ambiguous), TorsoWaistSize −0.65 ("Shrink Waist" semantics; the
  waist is routed through TorsoLower + LHandles + the belly core),
  TorsoBelly 0.75 / TorsoBellyChub 0.80 (HIMBO belly stack, replaced by
  the v4/v5.1 belly system). Machinery-only entries of the strongman
  build (SterDepth, SterHeight, BackSlope, SerratusMid, DeltsBack,
  DeltsShape, BicepsBack, ArmsSide, ShoulderInc) are absent from Jorge's
  record and were NOT carried over — adding them would invent values.
- **Fat-wrap side-mass:** measured, NOT corrected (the strongman flank
  correction table is Sen-recipe-specific). Kernel tissue wrap:
  belly flank/front **0.74**, chest **1.07** (fat wraps front-to-sides
  ✓). After the v4 belly core is applied the belly-band ratio reads
  **0.31** — the belly core is front-dominant by design; Sen's shipped
  build reads 0.29 on the same measure.

---

## 2. Measured numbers (shipped quantised targets, macro base)

Girths by mesh-plane slice loops, cm. Export column = ×1.39 (linear).

| measure | base | muscle only | **combined** | combined ×1.39 |
|---|---|---|---|---|
| height | 166.6 cm | 166.8 | **166.8 cm** | **231.9 cm (7′ 7.3″)** |
| volume | 51.21 L | 73.96 L | **94.88 L** | **254.8 L** |
| neck girth | 32.2 | 41.6 | **42.1** | **58.5** |
| chest girth | 108.2 | 123.3 | **127.3** | **177.0** |
| waist girth | 69.6 | 83.0 | **101.3** | **140.8** |
| thigh girth | 47.6 | 63.0 | **75.2** | **104.5** |
| calf girth | 34.0 | 45.3 | **56.7** | **78.7** |
| upper-arm girth | 27.3 | 41.0 | **44.7** | **62.2** |
| forearm girth | 22.6 | 29.6 | **32.3** | **44.9** |
| delt span | 55.7 | 63.8 | **66.7** | **92.7** |
| chest width (loop) | 46.7 | 52.7 | **53.9** | **74.9** |
| waist width (loop) | 24.1 | 29.5 | **35.0** | **48.7** |

**Mass estimate [E] — volume-derived only.** The person file records
**no mass for Jorge**; nothing here is canon. At water density
1.00 kg/L: **254.8 kg ≈ 562 lbs** at the shipped ×1.39 scale
(0.95–1.05 kg/L band: 242–268 kg / 534–590 lbs). At the record's
nominal 2.44 m height (see debit 2) the same shape gives 296.8 L →
**≈ 297 kg ≈ 654 lbs** [E].

**Scorecard values** (base | muscle | combined): M1 neck/head width
0.634 | 0.836 | **0.844** · M2 neck/arm 1.177 | 1.015 | **0.941** ·
M2 neck/calf 0.945 | 0.920 | **0.743** · M3 forearm/arm 0.827 | 0.721 |
**0.722** · M4 chest:waist 1.555 | 1.486 | **1.257** · M5 chest-depth
ratio 1.013 | 1.105 | **0.917** · M6 trap slope 34.5° | 32.8° |
**31.8°** · M7 visible neck 0.238 | 0.477 | **0.475** · M8 delt
span/head 3.53 | 4.05 | **4.23** · M11 thigh/waist 0.684 | 0.759 |
**0.742** · M13 chest-width ratio **×1.154**.

---

## 3. The watch item — muscle-vs-fat evidence (Joe's call)

*Recorded rule (§5.2): Muscle stays 45; only if the first build reads
fat-not-strong does Muscle go 45→60 — explicitly NOT more Chubby. Built
at 45; NO change applied. The evidence:*

**The muscle system alone reads strong.** At Muscle 0.45 the granular
stack (TorsoMass/TorsoLower/LegsSize/LegsThigh pinned at 1.00, traps
0.80–0.90, neck gate 0.95) already produces: chest:waist **1.486**,
neck 41.6 cm and M1 **0.836** (vs Sen's combined 0.853), delt span
63.8 cm, volume +44% over base. The 0.45 macro dial is not what carries
this frame — the pinned granular entries are.

**The tissue layer then does the softening — heavily at the waist.**
Tissue adds +18.4 cm at the waist vs +4.1 cm at the chest, +12.2 cm
thigh, +11.4 cm calf, +0.5 cm neck. Chest:waist falls 1.486 → **1.257**
and chest-depth:waist-depth falls 1.105 → **0.917** (the belly is
deeper than the chest — belly-forward, as designed: "arrives before he
does", never tucked). Tissue's share of all added volume (M10 proxy):
**0.48** — about half the build's added bulk is tissue (Sen: 0.42).

**Distribution read:** this is a strong frame wearing a heavy soft
coat, heaviest low (waist/thigh/calf), lightest at the neck — the
§5.2 shape ("soft over a working frame", "big everywhere, soft
everywhere"). It does **not** read fat-instead-of-strong at the frame
level: underneath the tissue, the muscle-only build out-ratios Sen's
*tissue-softened* combined build on chest:waist (1.486 vs 1.303).

**Bias warning:** the tissue read above is a **lower bound**. The two
biggest smoothing entries of Jorge's tissue vector — TorsoMassSmooth
0.85 and BellySmooth 0.80 — composed as zeros (vocabulary gap, §1).
With them, the same vector would read softer still. If more softness
is wanted, the lever is the vocabulary decision, not Muscle and not
Chubby.

**One counter-note:** M7 visible neck = **0.475**, vs Sen's **0.580**
on identical machinery — Jorge's neck *width* is there (M1 ≈ Sen's),
but its visible *length* reads shorter than Sen's, against the "Jorge
HAS a neck" design note. His yoke rides high. Flagged for Joe; no
corrective applied.

---

## 4. Fold gate — shipped quantised numbers (house rule)

Float build first: slope limiter + surgical attenuation repair, 0
flips on both bases, every component solo and composed (muscle
16 iterations, width 5, tissue 10; attenuation minima: muscle 0.06 /
520 verts, width 0.29 / 32, tissue 0.08 / 32 — same profile as Sen's
0.051 / 556).

Then the ship gate on the **written .target files parsed back**
(0.1 mm quantisation): as first written, the muscle component carried
**1 flipped face on the raw base** (min_dot −0.0486) — quantisation
tipping a boundary face, the neckfix failure mode. Repaired in
quantised space (neckfix precedent): **2 rounds, 13 verts attenuated,
max deviation 0.45 mm**, muscle target + combined rewritten.

**Final gate — 0 flips everywhere, worst min_dot +0.0352 ≥ +0.01:**

| composition | raw flips / min_dot | macro flips / min_dot |
|---|---|---|
| muscle | 0 / +0.0381 | 0 / +0.0352 |
| width | 0 / +0.8687 | 0 / +0.9229 |
| tissue | 0 / +0.3839 | 0 / +0.7309 |
| terminal | 0 / +0.9590 | 0 / +0.9587 |
| muscle+width | 0 / +0.0381 | 0 / +0.0352 |
| **full sum** | **0 / +0.0381** | **0 / +0.0352** |

Independently re-verified from disk by `scripts/gate_check_jorge.py`
(includes the combined file itself): **PASS**. Shipped-vs-float grades
agree to 3 decimals everywhere (volume 94.877 vs 94.876 L).

## 5. QA gauntlet

`qa-gauntlet/validate_glb.py jorge_body.glb` → parses ✓; 1 mesh,
13,380 v / 26,756 t; **degenerate 0, NaN 0**; extent 2.3189 m (matches
the graded export height); 1 material; skin absent, morphs 0 — both
expected and correct for an unrigged static bake.

## 6. Against Sen (identical machinery)

| | Sen combined | Jorge combined |
|---|---|---|
| volume (base scale) | 99.43 L | 94.88 L |
| M4 chest:waist | 1.303 | 1.257 |
| M1 neck/head | 0.853 | 0.844 |
| M6 trap slope | 31.9° | 31.8° |
| M7 visible neck | 0.580 | 0.475 |
| M10 tissue share | 0.42 | 0.48 |
| belly τ | 0.60 (ratio-solved) | 0.60 (BellyPot, fixed) |

Jorge lands slightly lighter and softer than Sen at base scale, with
a near-identical yoke — the §5.2 intent ("same neighbourhood, gentler
pole") in measured form.

## 7. Honest debits

1. **Vocabulary gap (largest).** Five vector entries compose zero —
   including TorsoMassSmooth 0.85, the single biggest intended
   Sen/Jorge tissue differentiator. The build is biased strong.
   Awaiting Joe's decision on the SOS.osd vocabulary (index
   compatibility unverified) — same open item as the bara recipes.
2. **Export scale lands short of nominal.** ×1.39 was calibrated in
   §5.2 against a ~1.756 m base (244/175.6); this machinery's hm08
   macro base grades 1.666 m, so ×1.39 yields **2.319 m, not 2.44 m**
   (Sen's build shares the property). Hitting exactly 2.44 m on this
   base needs **×1.463**. The factor was applied as recorded; the
   shortfall is reported, not silently corrected.
3. **M5 = 0.917** — belly depth exceeds chest depth. Consistent with
   Jorge's belly-forward design, but it is the inverse of the
   strongman cell's gate; stated plainly so Joe can judge.
4. **M2 neck/calf = 0.743** — the calves outgrew the Reeves neck
   relation, driven mostly by tissue (muscle-only: 0.920). Sen's
   build trimmed calves in a corrective pass; none was applied here
   (no invented values).
5. **M7 visible neck** reads shorter than Sen's (0.475 vs 0.580) —
   §3 counter-note.
6. **Float attenuation** cut a localised patch of the muscle field
   to 6% (520 verts ≥ any attenuation) where the composed field
   would have folded — under-displacement at fold-prone junctions
   (neck/trap/shoulder), same profile as Sen's build.
7. **Terminal scaling diverges from Sen's build** (×0.60 here vs
   ×1.0 there) — a deliberate, documented choice following the v5.1
   slider semantics at Jorge's BellyPot; effect ≤ 0.18 cm either way.
8. **GLB scale convention diverges from Sen's** — his bake sat at
   scene scale with the export factor recorded separately; Jorge's
   GLB is baked at ×1.39 so the file itself is the specced body.
   Graded numbers are the record in both cases.
9. **M12 "heads tall" (9.34) is a machinery artefact** — the grade's
   head-height landmark shrinks as the traps rise; Sen reads the
   identical 9.338. Not a proportion claim.
10. **Unrigged static bake** — no skeleton, skinning, morphs, head,
    or fur, per the tasking. Rigging is a later pass.

*Provenance: study-only. All fields derive from sliders decoded from
Joe's own legitimately obtained mod files (learned library); only
composed displacement fields ship, never source assets.*

## HEADS — Jorge head build (Nov 16, 2026)

Built on **base-head-v4** with the batch-1 §5.1 vector — the dog species
vector re-derived for St. Bernard from the breed standards (skull:muzzle
2:1, muzzle deeper than long, ≈90° stop, ZB/L 0.615). Deliverables:
`jorge_head.glb` / `jorge_head.blend` here; clay renders
`renders/head_front.png`, `renders/head_threequarter.png`,
`renders/head_profile.png`. No fur, no body changes; the body above
still carries its placeholder base head.

Machinery: the generalised Sen-pattern builder
(`characters/common/build_head.py`, clay renders via
`characters/common/render_head.py`, verify via
`characters/common/verify_head.py`) — see the HEADS section of
`characters/pyn/PYN_BUILD.md` for the shared method (proportional
convention, [E] maps, v4 teeth handling, the L/R side-convention fix,
`--base` parameterised for the v5 re-run; vector at
`scripts/jorge_vector.json`, raw numbers in `work/head_measure.json` +
`work/head_verify.json`).

**⚠ FLEWS — NOT BUILT (flag).** The `flews_saintbernard` part variant
(§5.3: enlarged/lowered flews, drape ceiling at the UKC fault line) does
not exist anywhere in the parts library — it is a paper item in the
preset doc and the app preset's parts list is empty. This head was
therefore built **without flews**: the enlarged/lowered flew drape from
the Sep 26, 2026 head direction is not in this geometry, and the muzzle
will read drier/blockier than the breed intends until the part exists.
Nothing was improvised in its place.

### Measured vs target (L = head length; stage-F rulers)

"Expected" = base × (species target / neutral); built-vs-expected is
the build-accuracy number. Built-vs-target also carries the base's own
deliberate deviations.

| Station | Slider | Base | Built | Species target | vs target | vs expected |
|---|---|---|---|---|---|---|
| ZB | CheekWidth +20 | 0.5466 | 0.6186 | 0.620 | −0.2% | +5.9% |
| MuzzleWidth (vertex slab) | MuzzleWidth +85 | 0.2332 | 0.3343 | 0.238 | +40.4% | +2.4% |
| MuzzleWidth (merged section) | MuzzleWidth +85 | 0.2412 | 0.3316 | 0.238 | +39.3% | −1.8% |
| MuzzleDepth | MuzzleDepth +80 | 0.2310 | 0.4356 | 0.280 | +55.6% | +34.7% |
| MuzzleFrac | MuzzleLength 0 | 0.3435 | 0.3170 | 0.330 | −3.9% | −7.7% |
| CraniumWidth (dome shell) | CraniumWidth +25 | 0.4780 | 0.4871 | 0.400 | +21.8% | −8.3% |
| SkullHeight | CraniumHeight +35 | 0.3168 | 0.3597 | 0.352 | +2.2% | +0.0% |
| OrbitDiameter | EyeSize −10 | 0.1500 | 0.1400 | 0.140 | +0.0% | −0.0% |
| EarLength (stage-F) | EarHeight 0 | 0.3690 | 0.3488 | 0.400 | −12.8% | −5.5% |
| JawLength (stage-F origin) | JawLength 0 | 0.7104 | 0.6528 | 0.740 | −11.8% | −8.1% |
| JawWidth | JawWidth +50 | 0.5330 | 0.6023 | 0.470 | +28.1% | −3.8% |
| RamusDepth | JawDepth +40 | 0.2697 | 0.2891 | 0.328 | −11.9% | −8.5% |

Notes on the non-obvious rows:

- **MuzzleWidth is the build's best station**: +2.4% / −1.8% vs expected
  on the two rulers. The breed asks for a wider muzzle than the span
  was sized for (§5.1 flags the 0.24 target near the +100 ceiling);
  built 0.334 vs target 0.238 is the base's inherited deviation carried
  through the proportional convention, not overshoot.
- **MuzzleDepth +34.7% vs expected — decomposed, not a spike.** The
  depth factor (1.40 about the palate) was applied as specified. The
  ruler's slab window migrated onto the stop crest as L grew
  (CraniumLength +25) and the nose pitched (StopAngle +90), and the
  crest verts sit inside the depth field's y-only mask, so the station
  reads the amplified crest. Probed directly: the slab's top verts are
  a smooth symmetric edge loop, and the profile render shows a
  coherent deep stop→muzzle column. Judge the depth from the profile;
  the station number overstates it for window reasons.
- **Jaw stations.** JawLength's applied ratio about the node hinge is
  **1.000 vs 1.000 expected — exact** (the slider is 0). The stage-F
  rows read low because the stage-F hinge origin derives from the ear
  bases, and the folded ears moved that origin — the same ruler
  migration, now driven by the fold. JawWidth/RamusDepth (−3.8% /
  −8.5%) carry the same origin shift plus band-vs-field weighting.
- **Ears.** EarHeight 0 → applied length factor exactly 1.0; both ear
  rulers are unreliable on a folded ear (stage-F −5.5%, base→tip
  +12.3% — base-population artefacts). EarTilt −75 is realised as
  pitch −10.5° (Sen's map, held at the −30 value) + a **drop-fold
  extension [E]**: rotation about the head-y axis at 2.4°/unit of
  excess = **108°** for Jorge, tips ending below base height against
  the cheeks. First attempt at 1.5°/unit (67.5°) rendered as
  sideways wings and was raised; the shipped renders are the 108°
  version. This extension is new machinery, flagged as such — Sen's
  map never left the pitch range.
- **MuzzleFrac −7.7%** with MuzzleLength 0 is composition: the −5.6°
  stop pitch pulled nose_y back and CraniumLength grew L. **Interorbital:**
  centres +0.008 as ordered (EyeSpacing +10); gap +0.018 net with the
  EyeSize −10 ball shrink — composed exactly. Probes: NoseWidth ratio
  1.273 = expected exactly; RuffZone +16.1% (RuffVolume +35);
  StopBandZ −0.0343 (the +90 stop — deepest on the chart, and it reads
  in the profile); OcciputY −0.0469 (CraniumLength +25, factor 1.081).
  OrbitRise +0.0242 is CraniumHeight +35 legitimately raising the dome
  the ruler samples.

### Teeth / jaw

Upper arcade rides the muzzle metric fields; lower rides JawLength
(0 → unmoved). BVH overlap, upper vs lower:

| Jaw | −0° (rest) | −10° | −20° | −30° |
|---|---|---|---|---|
| Overlap pairs | 256 | 0 | 0 | 0 |
| Min clearance (L) | — | 0.0241 | 0.0476 | 0.0692 |

Open angles: **0 pairs with clearances identical to the raw base's
own**. Rest: the base itself carries 27 interpenetrating pairs by
construction (the v4 split was cut from one fused slab and certified
at open angles only); Jorge's widened upper arcade raises the rest
count to 256. The interpenetration is internal, clears by −10°, and
a true occlusion re-seat is a base-pass (v5) item — not per-character
surgery. Teeth-vs-tissue: 1 logical vertex outside (mask-edge root,
0.0039 L — negligible). Teeth visible through the jaw seam in the
profile render are base construction (0 upper verts outside the
tissue on the side that matters), not a build defect.

### Paths / coverage

As Pyn's doc (shared machinery): ratio sliders full; MuzzleTaper,
StopAngle, brow band, EarSpread/EarPlacementHeight/EarTilt (with the
fold extension above), EarTipPoint, RuffVolume partial [E];
BrowContinuity and EyeForwardness none/recorded. BrowScowl is 0 in
this vector on purpose (§5.1 — the batch's only 0-scowl adult male);
nothing was baked in its place. Tongue unscaled; NeckSocket untouched.
