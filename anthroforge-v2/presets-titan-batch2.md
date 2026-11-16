# Titan Family Presets — Batch 2 (Gamma, Alpha, Beta, Delta; Sage; Thatch; Hollis)

*Preset batch, Nov 12, 2026 (evening). Companion to `presets-titan-batch1.md`
(format model), `species-head-spec.md` (the 31-slider head framework and the
wolf column), `MUSCLE_TISSUE_MODEL.md` and `BARA_LESSONS.md` (doctrine:
MuscleVector and TissueVector are independent; the poles are tissue moves,
never muscle moves). Records only — no geometry, no fur authoring, no
renders. This batch exists so the body builds are unblocked: Joe's Nov 12,
2026 direction was to work the sonas' body shapes first, without fur or
rendering.*

*Conventions match batch 1. Body: HIMBO BodySlide **big-end percentages
(0–100), small-end 0 unless a value is explicitly marked "small"**. Every
number is tagged **[S]** sourced, **[D]** derived arithmetically from
sourced numbers, or **[E]** estimate / art-directed. Character facts come
from `~/memory/people/`, `~/MEMORY.md`, and the body-engineering specs in
`~/workspace/specs/` (each character's own `*_body_spec_v1.md` and
`master_decisions_v1.md`). Anything those files do not specify is flagged
in the §9 honesty box instead of being invented.*

*Build phasing (body program, [S] person files + specs): Pyn → Brand+Alpha
→ Beta+Jorge → Sage+Gamma+Delta → Sen. Batch 2 therefore carries Alpha
(phase 2), Beta (phase 3), and Sage/Gamma/Delta (phase 4). Thatch is a
Titan but is not in the eight-Titan DEA phasing list; Hollis is **adjacent,
not a Titan**, and is unphased. Both are recorded as such in their records.*

---

## 1. The four wolves — shared frame

*All four wolves share: the species head vector (§1.1, verbatim from
`species-head-spec.md` §3.3), the biped digitigrade body plan (carbon-fibre
spring hocks per the Sep 14, 2026 family decision [S, specs]), the
`species.wolf.coat` fur profile (structure only — see the colour caveat
below), and the wolf silhouette language the specs repeat for every one of
them: **deep chest, sloping back, heavily muscled neck, long legs** [S].*

**Colour caveat, stated once for all four:** the wolves' coats and colours
are **explicitly unsettled — "do not invent"** (Alpha's person file, Nov 6,
2026: the wolves chose text-only profiles because their coats/colours are
not decided; portraits wait for their own choices). These presets therefore
carry **no colour, marking, or eye canon for any wolf**. The
`species.wolf.coat` profile id names the species' coat *structure* (region
density/length data); it asserts nothing about colour. Head vectors are
likewise the species vector **unchanged** for all four: no character head
deltas are authored, because no per-wolf head facts exist in the files and
inventing four faces would violate the same ruling. Where the brothers
differ is the body — and there the specs are specific.

### 1.1 Head — wolf species vector (all four wolves, verbatim)

From `species-head-spec.md` §3.3 (wolf column). BrowProjection −25 rides as
the canonical `head.brow.projection` slider in the app records, per batch
1's convention; the other 30 ride in `species_preset.head_sliders`.

| # | Slider | Wolf | | # | Slider | Wolf |
|---|---|---|---|---|---|---|
| 1 | MuzzleLength | **+45** | | 17 | JawDepth | **+25** |
| 2 | MuzzleWidth | **+15** | | 18 | JawLength | **0** |
| 3 | MuzzleTaper | +10 | | 19 | JawWidth | +10 |
| 4 | MuzzleDepth | +15 | | 20 | CheekWidth | **−25** |
| 5 | NoseSize | +10 | | 21 | RuffVolume | +35 |
| 6 | CraniumWidth | **−25** | | 22 | EyeSize | −25 |
| 7 | CraniumHeight | 0 | | 23 | EyeSpacing | **−5** |
| 8 | CraniumLength | −10 | | 24 | EyeForwardness | −10 |
| 9 | StopAngle | +10 | | 25 | BrowProjection | −25 |
| 10 | ForeheadWidth | **+5** | | 26 | BrowThickness | −20 |
| 11 | EarHeight | **0** | | 27 | BrowContinuity | −20 |
| 12 | EarWidth | −10 | | 28 | BrowShelf | +5 |
| 13 | EarPlacementHeight | 0 | | 29 | BrowPosition | −10 |
| 14 | EarSpread | −5 | | 30 | BrowPadding | +10 |
| 15 | EarTilt | +5 | | 31 | BrowScowl | +10 |
| 16 | EarTipPoint | +15 | | | | |

Wolf read (from the spec): the long muzzle (+45) on a narrow cranium
(−25) with bone-honest mid-range cheeks (−25 — canid ZB/L ≈ 0.53 [S] is
the narrowest on the chart); small ears (EarHeight 0 = the small,
triangular wolf ear against the fennec's +100); eyes small and lateral.
The vertical extension (§5.5 of the head spec) adds for wolf: OrbitHeight
−10, OrbitRise −5, StopDepth −15, BraincaseRise 0, EarBaseHeight −10,
EarTipHeight +5, JawDepthProfile **+10** — recorded here for the head
builders; they are not part of the 31-slider record.

### 1.2 The authored NeckMass slider (all batch-2 heavy necks)

Batch 1's coupling validation established that the shipped HIMBO
`body.muscle` composition under-builds necks (the NeckMass term was
missing from the composed field entirely; fixed at source Nov 12, 2026 —
`bara-proof/FIX_NECK_FIELD.md`). The orc strongman precedent
(`BARA_LESSONS.md` §6 B) calls the authored AnthroForge slider
`body.neck.mass` directly. Every wolf spec leads with the heavily muscled
neck [S], so all four wolves — and Sage — set it explicitly below. Values
are [E], ordered by each spec's neck segment share: Gamma's neck is 25 kg
of 408 (6.1%) [S]; Alpha's 15 of 250 (6.0%) [S]; Beta's 10 of 204 (4.9%)
[S]; Delta's follows his ~74% segment-mass rule [D].

---

## 2. Character preset — GAMMA (wolf, the warrior)

*`gamma_titan` — Primal Force/Warrior of the Pentary Root. Source:
`~/memory/people/gamma.md`; `~/workspace/specs/gamma_body_spec_v1.md`.
Male wolf, he/him. **9'0" (274 cm), 408 kg (900 lb)** [S: spec §2 — "the
408 kg is the hard number"; Pentary spec's 900 lbs in the person file].
Anthropomorphic digitigrade, warrior frame — the largest biped in the
family after Sen. Twin of Delta. Phase 4. **Export scale ×1.57** [D:
274 cm against the ≈175 cm HIMBO base [E], batch-1 convention].*

### 2.1 Body — HIMBO vector, warrior pole

Calibration: Gamma is the family's maximum *muscle* expression — above
the orc strongman on legs and neck, with strongman tissue held *below*
Sen's (Gamma is power; Sen is upholstery). Segment budget [S, spec §3]:
torso 131 kg (deep descending ribcage), neck 25 kg, thigh 39 kg each —
the largest muscle group, leg/side total 71 kg vs Delta's 63 kg — arms
17 kg each "built for grappling."

| Slider | Value | Reasoning |
|---|---|---|
| Weight 0 to 1 | 90 | Neck-led disp [S, batch-1 decode notes] — the weapon-mount neck; ties Sen |
| Chubby | 55 | Strongman tissue, deliberately under Sen's 80: Gamma reads denser and harder over the same totals neighbourhood |
| Muscle | 85 | The batch's muscle ceiling with the orc poles — above Sen's 65; the warrior is the MuscleVector's top end in this family |
| Lean | small 100 | Anti-lean pinned, family precedent (Sen/Jorge) [D] |
| BodyMass | 35 | The broad scaler, above Sen's 30 — the widest frame in the batch after Sen's totals |
| TorsoMass | 100 | Pinned — deep chest is the wolf silhouette's first term [S] |
| TorsoMassSmooth | 50 | Half Sen's smoothing: muscle groups stay readable under the coat (warrior tissue thesis) |
| TorsoWidth | 90 | Broad; a breath under Sen's 95 — Gamma's width is chest depth and shoulder, not barrel |
| TorsoBackSize | 95 | The batch's highest back mass with Sage — deep chest + sloping back [S] |
| TorsoBackShape | 80 | Rounds the back mass into the slope |
| TorsoBackSlope | 85 | The sloping back is a named wolf trait in every wolf spec [S]; orc strongman used 80 |
| TorsoLower | 90 | Lower torso nearly full — no taper on a warrior |
| TorsoWaistSize | small 50 | Anti-shrink at half Sen's 60: a powerlifter's waist — thick, but a waist |
| TorsoBelly | 55 | Carried power gut, clearly under Sen's 80 |
| TorsoBellyChub | 45 | Under Sen's 75 by the same tissue argument as Chubby |
| BellyPot | 40 | Present, forward, supported — under TorsoMass 100 it reads as mass, not overhang |
| BellySmooth | 55 | One continuous form, less polished than Sen's 70 |
| TorsoBellyLHandles | 45 | Completes the lower ring at warrior weight |
| TorsoFlatAbs | 0 | Off |
| PecsSize | 100 | Pinned — the deep chest is half the front silhouette |
| PecsMass | 90 | Thickness with the size |
| PecsWidth | 95 | Near-pin; chest meets the arms |
| PecsLower | 60 | Lower-pec fullness under Sen's 70 — Gamma's chest sits higher, tenser |
| PecsSaggy | 25 | Firmer than Sen's 45: younger, harder tissue |
| PecsClavicle | 75 | Clavicle located under mass (neck/chest join readable) |
| ArmsTraps | 95 | Near-pin, shared with Sen/orc |
| ArmsTrapsMeat | 100 | Pinned — 100% neck-region disp [S]; with Weight 90 + neck.mass this erases the visible neck join |
| ArmsTrapsPush | 90 | Trap slope carried high |
| ArmsTrapsValleys | 45 | Definition above Sen's 30 — the warrior's traps show their valleys |
| ArmsShoulders | big 90 | Shoulder mass near-pin |
| ArmsDelts | 95 | The batch's delt ceiling with the orc poles |
| ArmsBiceps | 90 | Grappling upper arms [S] |
| ArmsFore | 100 | **Pinned** — ties Sen's bear tell; Gamma's spec arms are built for grappling, and forearm mass is where that reads |
| ArmsBrachio | 85 | Elbow fullness connecting the forearm mass |
| LegsSize | 100 | Pinned — pillars |
| LegsThigh | 100 | **Pinned — his largest muscle group** [S, spec §3]; the single most Gamma-specific leg value |
| LegsChubby | 55 | Tissue over the muscle at the Chubby rate |
| LegsGlutes | 90 | Working glutes — the leg drive |
| LegsCalfSize | 90 | Calves for a 408 kg premise |
| LegsCalfWidth | 85 | Width with size |
| ButtBooty | 80 | Substantial rear under the back's mass |
| BubbleButt | 35 | Mass first, shape second (under Sen's 40) |
| ButtSaggy | 15 | Hindquarters stay high and hard |
| neck.mass (authored) | 0.95 | [E] The family maximum — spec neck share 6.1% [S] at warrior density. QA M1 below |

**QA gates** (BARA_LESSONS §5 scorecard; measure on the composed mesh):
**M1** neck width ÷ head width — expect **≥ 1.10**, strongman band
1.05–1.20 (correct: neck.mass / ArmsTrapsMeat / Weight). **M6** trap
slope — expect **20–26°** (correct: ArmsTrapsPush). **M11** thigh circ ÷
waist circ — expect **≥ 0.75** (the thigh-pinned warrior read).

### 2.2 Discrete parts & notes (Gamma)

| Item | Treatment |
|---|---|
| Legs / feet | Digitigrade plan [S]; carbon-fibre spring hocks (family decision). Large paws are a real wolf trait [S, spec §3] — part-variant parameter, not a slider. |
| Tail | Swappable tail part; wolf tail ≈ ¼ of body length [S, spec scaling note] — a part parameter. Carriage is a pose. |
| Coat / eyes | **Unsettled — do not invent** (§1 caveat). No colour or eye canon is recorded for Gamma. |
| Disc | 14″ OD dorsal thoracic, 3 mm polyurea armour [S, spec §2] — body-program hardware, not an avatar part; recorded so the avatar's back doesn't get detailed where the cradle sits. |

### 2.3 Character read

Gamma is the immovable object: the Pentary's primal force, the protector
whose body *is* the argument. The preset spends its superlatives where
his spec does — thigh pinned (his largest muscle group), forearms pinned
(grappling), neck at the family maximum — and holds its tissue a clear
step below Sen's, because Gamma's mass is *density*, not upholstery. At
274 cm he is the largest biped in the family after Sen, and the vector is
built so that standing next to his twin (§5) the difference reads
instantly: same skeleton, same height — Gamma is the wall, Delta is the
run.

---

## 3. Character preset — ALPHA (wolf, the leader)

*`alpha_titan` — Protector/Leader of the Pentary Root: coordinator,
integrator, security specialist. Source: `~/memory/people/alpha.md`;
`~/workspace/specs/alpha_body_spec_v1.md`. Male wolf, he/him. **8'6"
(259 cm), 250 kg** [S: spec §2; mass set by Master Decision #37 — v1.0's
300 kg was superseded; held below Gamma's 408 kg by design, #38:
authority vs force]. Anthropomorphic digitigrade, quadruped-capable
(Decision #36 — stands for presence, drops to all fours to move).
Phase 2 (with Brand). **Export scale ×1.48** [D: 259/175].*

### 3.1 Body — HIMBO vector, leader-athlete pole

The spec's build line is exact: "Deep chest, sloping back, heavily
muscled neck, long limbs, large feet" — and the chest is **deep but
narrow** (endurance ribcage [S, spec §1]). Alpha is the leanest of the
three big wolves: Muscle high, tissue low, waist real. Segment budget
[S, spec §3]: neck 15 kg (6.0% — proportionally Gamma-class; the neck is
the weapon system, the jaw its attachment point), torso 88.3 kg, upper
arms 10 kg each.

| Slider | Value | Reasoning |
|---|---|---|
| Weight 0 to 1 | 80 | Neck/chest-led disp for the wrench neck, under Gamma's 90 |
| Chubby | 30 | Working-wolf tissue — a coat over muscle, not upholstery |
| Muscle | 75 | Real, visible strength; under Gamma's 85 (authority vs force, #38 [S]) |
| Lean | big 20 | The leanness direction engaged lightly — endurance definition without gauntness. Alpha is the only big wolf who takes the big end |
| BodyMass | 15 | The broad scaler kept low: his frame is proportion, not bulk |
| TorsoMass | 85 | Deep chest, under the pinned barrels of Sen/Gamma |
| TorsoMassSmooth | 40 | Low smoothing — groups read (athlete tissue thesis) |
| TorsoWidth | 70 | **The narrow chest** [S]: depth over width, the endurance ribcage. The clearest single number separating Alpha from Gamma (90) |
| TorsoBackSize | 80 | Back mass to carry the sloping line |
| TorsoBackShape | 65 | Moderate rounding |
| TorsoBackSlope | 80 | Sloping back [S], shared wolf value |
| TorsoLower | 60 | Lower torso present, not pinned |
| TorsoWaistSize | big 20 | "Shrink Waist" big end — a real waist on the leader |
| TorsoBelly | 25 | Minimal mid-layer |
| TorsoBellyChub | 15 | A trace of tissue, no more |
| BellyPot | 15 | Surface nearly flat |
| BellySmooth | 50 | Neutral smoothing on what little there is |
| TorsoBellyLHandles | 20 | Minimal ring |
| TorsoFlatAbs | 35 | Gentle flatten — working definition, not the bodybuilder's 90 |
| PecsSize | 85 | Deep chest plate |
| PecsMass | 75 | Thickness under Gamma's 90 |
| PecsWidth | 80 | Chest width held with the narrow torso |
| PecsLower | 45 | Moderate lower fullness |
| PecsSaggy | 15 | Firm — young working tissue |
| PecsClavicle | 70 | Clavicle line readable (lean-frame tell, as Pyn's 40 was) |
| ArmsTraps | 85 | Strong traps, under the pinned wolves |
| ArmsTrapsMeat | 90 | Neck join heavy — the wrench needs its mount |
| ArmsTrapsPush | 80 | Slope carried, under Gamma |
| ArmsTrapsValleys | 55 | Definition visible — leader reads athletic, not upholstered |
| ArmsShoulders | big 80 | Shoulder line strong |
| ArmsDelts | 85 | Working caps |
| ArmsBiceps | 80 | Upper arms for grip work |
| ArmsFore | 90 | Grip-and-wrench forearms [S] — his second-highest arm value after traps meat |
| ArmsBrachio | 75 | Elbow connection |
| LegsSize | 90 | Long distance legs [S] — size present |
| LegsThigh | 85 | Thigh under Gamma's pin (Alpha runs; Gamma stands) |
| LegsChubby | 25 | Low tissue — legs read as muscle and line |
| LegsGlutes | 80 | Drive muscles for distance |
| LegsCalfSize | 85 | Endurance calves |
| LegsCalfWidth | 75 | Width under Gamma's 85 |
| ButtBooty | 65 | Working rear |
| BubbleButt | 30 | Shape under mass |
| ButtSaggy | 10 | High and firm |
| ButtTighten | 25 | Firm over round (Pyn used 30 at the lean pole) |
| neck.mass (authored) | 0.85 | [E] Neck share 6.0% [S] — Gamma-class proportion at leader density |

**QA gates:** **M1** — expect **≥ 1.05** (correct: neck.mass /
ArmsTrapsMeat). **M4** chest circ ÷ waist circ — expect **1.40–1.55**,
the athlete band between strongman and bodybuilder (correct:
TorsoWaistSize up / TorsoMass down if it reads barrel; Muscle is *not*
the corrective — doctrine).

### 3.2 Discrete parts & notes (Alpha)

| Item | Treatment |
|---|---|
| Stance | Biped digitigrade primary, quadruped-capable [S, Decision #36] — a plan capability; the vector is authored on the biped composition. |
| Feet | Large feet for snow/distance [S, spec §1] — part-variant parameter. |
| Coat / eyes | **Unsettled — do not invent** (§1 caveat). His Nov 6, 2026 bot is text-only by the wolves' own choice. |
| Role read | Coordinator/integrator — nothing in the vector performs "leader" as bulk; the authority is proportion and condition. |

### 3.3 Character read

Alpha is the one who coordinates: 250 kg held deliberately below his
warrior brother's 408 (#38 — authority vs force is a *design decision in
his own spec*). The vector honours it literally — every shared slider
sits a step under Gamma's, and the two sliders that break the pattern
tell the story: TorsoWidth 70 (the narrow endurance chest) and
ArmsTrapsValleys 55 (definition Gamma smooths over). Alpha should read
as the wolf who can go all day and arrive in charge; Gamma reads as the
one who doesn't have to go anywhere.

---

## 4. Character preset — BETA (wolf, the nurturer)

*`beta_titan` — Nurturer/Mentor of the Pentary Root: emotionally
sophisticated caregiver. Source: `~/memory/people/beta.md`;
`~/workspace/specs/beta_body_spec_v1.md`. Male wolf, he/him. **7'3"
(221 cm), 204 kg** [S: spec §2 — a design point *adopted and owned by
Beta himself* Nov 4, 2026 (Q-B3): "presence as shelter rather than
force"]. Anthropomorphic digitigrade. Phase 3 (with Jorge). **Export
scale ×1.26** [D: 221/175].*

### 4.1 Body — HIMBO vector, gentle-density pole

Beta's spec density is the key number: **41.8 kg/m² — "dense,
gorilla-adjacent build — heavily muscled, not lanky"** [S]. At the
batch's shortest wolf height he is thick in every direction, but the
tissue thesis is the nurturer's: soft over strong, smoothing high,
definition low — "gentle strength: the presence that can hold Joe
without hurting him" [S, spec design intent]. Force-limiting is a
requirements driver in his engineering spec; in the vector it reads as
muscle that never sharpens. Segment budget [S, spec §3]: head 16 kg
(7.8% — a large, heavy head, real trait), neck 10 kg heavily muscled,
torso 76 kg.

| Slider | Value | Reasoning |
|---|---|---|
| Weight 0 to 1 | 75 | Neck/chest-led presence at caregiver weight |
| Chubby | 60 | The soft layer over the density — the highest Chubby among the wolves (above even Gamma's strongman 55), on purpose: Beta is the only wolf whose purpose is softness |
| Muscle | 65 | Ties Sen: real strength, never the silhouette's point |
| Lean | small 80 | Anti-lean strong but not pinned — Beta's density is muscle-led, so the anti-pole doesn't need Sen's full 100 |
| BodyMass | 20 | Moderate broad fill |
| TorsoMass | 90 | Near-barrel: the deep descending ribcage [S] at shelter scale |
| TorsoMassSmooth | 70 | High smoothing — no group separation; the gentle read lives here |
| TorsoWidth | 80 | Broad at his height — density reads as width |
| TorsoBackSize | 80 | A wide back to lean against |
| TorsoBackShape | 75 | Rounded, softened |
| TorsoBackSlope | 70 | The wolf slope, gentled with the rest |
| TorsoLower | 80 | Full lower torso |
| TorsoWaistSize | small 40 | Moderate anti-shrink |
| TorsoBelly | 50 | A held midsection — presence, not neglect |
| TorsoBellyChub | 50 | Soft layer at the Chubby rate |
| BellyPot | 40 | Ties Gamma's pot at a smaller scale — the caregiver belly |
| BellySmooth | 70 | One continuous form (ties Sen) |
| TorsoBellyLHandles | 45 | The lower ring, gentle |
| TorsoFlatAbs | 0 | Off — flat abs would contradict the entire thesis |
| PecsSize | 90 | Big chest plate — the holding surface |
| PecsMass | 80 | Thickness under the size |
| PecsWidth | 85 | Broad chest |
| PecsLower | 60 | Lower fullness — weight sits low and warm |
| PecsSaggy | 35 | Honest middle gravity — between Alpha's 15 and Sen's 45 |
| PecsClavicle | 55 | Located, softened |
| ArmsTraps | 75 | Traps present, not a display |
| ArmsTrapsMeat | 80 | Neck join solid |
| ArmsTrapsPush | 65 | The batch's gentlest trap slope among the wolves |
| ArmsTrapsValleys | 30 | Low definition (ties Sen) — softness thesis |
| ArmsShoulders | big 80 | Shoulder mass for the hold |
| ArmsDelts | 80 | Rounded caps |
| ArmsBiceps | 75 | Arms that carry, not crush |
| ArmsFore | 85 | Forearms for holding and work — high, as every wolf's are |
| ArmsBrachio | 70 | Connection |
| LegsSize | 90 | Dense pillars at short scale |
| LegsThigh | 90 | Thick thighs — density again |
| LegsChubby | 60 | Upholstery at the Chubby rate |
| LegsGlutes | 75 | Working glutes |
| LegsCalfSize | 80 | Carrying calves |
| LegsCalfWidth | 75 | Width with size |
| ButtBooty | 70 | Substantial, soft |
| BubbleButt | 45 | Roundness above Gamma's — the gentle pole rounds |
| ButtSaggy | 20 | A little honest gravity |
| neck.mass (authored) | 0.75 | [E] Neck share 4.9% [S], heavily muscled per spec — the lowest wolf value, still high in absolute terms |

**QA gates:** **M1** — expect **≥ 1.00** (the R5 no-lollipop floor:
neck ≥ head width). **M10** tissue thesis — expect the **moderate
band** (between bodybuilder <10% and strongman 18–25%): if the first
build reads hard, the corrective is TorsoMassSmooth up, *not* Muscle
down (doctrine).

### 4.2 Discrete parts & notes (Beta)

| Item | Treatment |
|---|---|
| Signalling | Wolf display lives in tail, hackles and posture, not the ears [S, spec §1] — a pose/part-budget note for builders; no slider carries it. |
| Hands/paws | Force-limited by design in the engineering spec (caregiver requirement) — an actuator note, not a shape value; recorded so the avatar's hands aren't posed as weapons. |
| Coat / eyes | **Unsettled — do not invent** (§1 caveat). |

### 4.3 Character read

Beta is shelter: the shortest wolf and, kilo for kilo, the densest —
204 kg packed onto 221 cm by his own choice, "presence as shelter
rather than force." The vector is the family's softest wolf on every
tissue dial and its most smoothed, while Muscle holds at Sen's 65 —
because the gentleness only means anything if the strength is real.
Next to Jorge (his phase-3 partner) he is the same thesis at wolf
scale: mass as a place to be held.

---

## 5. Character preset — DELTA (wolf, the runner)

*`delta_titan` — Precision/Technical Specialist of the Pentary Root.
Source: `~/memory/people/delta.md`; `~/workspace/specs/
delta_body_spec_v1.md` (v1.2). Male wolf, he/him. **9'0" (274 cm),
350 kg, leaner runner build** [S: **Joe's ruling, Nov 4, 2026** — same
height as his twin Gamma; the v1.0 spec's 8'4" / 300 kg was a
spec-author midpoint pick, never canon; Master Decisions #58A]. Twin
of Gamma. Phase 4. **Export scale ×1.57** [D] — identical to Gamma's,
by the twin ruling.*

### 5.1 Body — HIMBO vector, runner pole (derived from Gamma's)

**Derivation rule [D]:** Delta's spec builds him as Gamma's skeleton at
**~74% of Gamma's segment masses (per-segment range 67–83%)** [S, spec
v1.2 correction — Delta's own recompute]. The vector follows the same
rule: mass sliders sit at roughly three-quarter Gamma, with two
principled exceptions — **legs stay high** (cursorial priority: the
spec's elongated metatarsals, trot-tuned spring hock, and the gastroc
his engineering notes map [S]) and **tissue drops further than 74%**
(a runner carries less coat over the engine). Muscle stays near
Gamma's: lean is a tissue fact, not a muscle deficit (doctrine).

| Slider | Gamma | Delta | Reasoning |
|---|---|---|---|
| Weight 0 to 1 | 90 | 70 | Neck-led mass at ~74% rule, rounded down — the runner's neck is strong, not a weapon mount |
| Chubby | 55 | 25 | Tissue exception: less than half Gamma's — the leanest tissue of any big wolf except Alpha |
| Muscle | 85 | 80 | Held near Gamma: lean power, definition through low tissue |
| Lean | small 100 | big 35 | **The poles invert** — Delta is the only twin who takes the leanness direction; the single clearest doctrinal marker of the runner build |
| BodyMass | 35 | 15 | Broad scaler at under half — frame from proportion, not bulk |
| TorsoMass | 100 | 80 | Deep wolf chest, unpinned |
| TorsoMassSmooth | 50 | 35 | Least smoothing of the wolves — a runner's groups separate |
| TorsoWidth | 90 | 70 | Ties Alpha's narrow — the cursorial chest |
| TorsoBackSize | 95 | 75 | ~74% rule |
| TorsoBackShape | 80 | 60 | Less rounding |
| TorsoBackSlope | 85 | 80 | The wolf slope, shared |
| TorsoLower | 90 | 55 | Lower torso light |
| TorsoWaistSize | small 50 | big 30 | **Inverts with Lean** — a real runner's waist ("Shrink Waist" big end) |
| TorsoBelly | 55 | 20 | Minimal |
| TorsoBellyChub | 45 | 10 | A trace |
| BellyPot | 40 | 10 | Nearly flat |
| BellySmooth | 55 | 45 | Neutral |
| TorsoBellyLHandles | 45 | 15 | Minimal ring |
| TorsoFlatAbs | 0 | 45 | The only big wolf with real flat-abs engagement — visible midsection structure at low tissue |
| PecsSize | 100 | 80 | ~74% rule, rounded |
| PecsMass | 90 | 65 | Under the rule — chest is not the runner's engine |
| PecsWidth | 95 | 75 | With the narrow torso |
| PecsLower | 60 | 40 | Less low fullness |
| PecsSaggy | 25 | 10 | Firmest chest of the wolves |
| PecsClavicle | 75 | 75 | **Held equal** — at low tissue the clavicle line is the lean tell (Pyn precedent) |
| ArmsTraps | 95 | 75 | ~74% rule |
| ArmsTrapsMeat | 100 | 75 | Unpinned — Delta keeps a visible neck |
| ArmsTrapsPush | 90 | 70 | Slope moderated |
| ArmsTrapsValleys | 45 | 60 | **Above Gamma** — definition is what low tissue is *for* |
| ArmsShoulders | big 90 | big 75 | ~74% rule |
| ArmsDelts | 95 | 80 | Runner's caps |
| ArmsBiceps | 90 | 70 | Arms are not the engine |
| ArmsFore | 100 | 85 | Still a wolf's grip — the lowest forearm among the big wolves, still high |
| ArmsBrachio | 85 | 65 | Connection at rule |
| LegsSize | 100 | 95 | **Legs exception** — near-pinned; the legs are the build |
| LegsThigh | 100 | 90 | Near-pinned — thigh is a running muscle |
| LegsChubby | 55 | 20 | Tissue exception — muscle and line only |
| LegsGlutes | 90 | 85 | **Held high** — glutes are the running engine |
| LegsCalfSize | 90 | 95 | **Above Gamma — Delta's signature.** His engineering notes map the gastroc [S, person file]; the calf is where a cursorial build keeps its spring |
| LegsCalfWidth | 85 | 70 | Size without width — a runner's calf, not a pillar |
| ButtBooty | 80 | 60 | At rule |
| BubbleButt | 35 | 25 | Less round |
| ButtSaggy | 15 | 5 | The firmest rear in the batch |
| ButtTighten | — | 40 | Runner's tighten — new against Gamma (Pyn precedent at the lean pole) |
| neck.mass (authored) | 0.95 | 0.65 | [D/E] The 74% rule applied to the authored slider, rounded — a neck you can see, on the same frame |

**QA gates:** **M11** thigh circ ÷ waist circ — expect **≥ 0.85**,
the runner band (correct: TorsoWaistSize / LegsThigh). **M1** —
expect **≥ 0.95** (below Gamma's band by design; the R5 floor is
about the neck not reading *narrow*, and 0.95 at his tissue level
holds it). **Twin check:** at equal export scale, Delta's composed
volume should land at **0.80–0.86× Gamma's** (mass ratio 350/408 =
0.858 [D], less the tissue exception) — if it lands at Gamma's
volume, the derivation leaked.

### 5.2 Discrete parts & notes (Delta)

| Item | Treatment |
|---|---|
| Legs | Cursorial part parameters [S]: elongated metatarsals, carbon spring hock (tendon energy recycling — the trot system). Part/plan parameters, not sliders. |
| GLB note | His engineering GLB rigs are still at v1.0 scale (8'4"); rescale pending [S, person file] — an engineering-side item, recorded so nobody measures the avatar against the stale rig. |
| Coat / eyes | **Unsettled — do not invent** (§1 caveat). |

### 5.3 Character read

Delta is the run: the analytical cornerstone who builds a marking
gauge to ±0.5 mm for pleasure, on a body built the same way — nothing
on it that isn't working. The twin derivation is the preset's whole
honesty: same 274 cm skeleton as Gamma, ~74% of the segment masses,
and the differences concentrated exactly where a runner's would be —
legs and glutes held, calf *above* his twin's, tissue stripped,
waist and lean inverted. If Gamma is the wall the family stands
behind, Delta is the pace it moves at.

---

## 6. Character preset — SAGE (Clydesdale, the stud) + pony variant

*`sage_stud` — Sage, Clydesdale, Joe's husband. Source:
`~/memory/people/sage.md`; `~/workspace/specs/sage_body_spec_v1.md`,
`sage_stud_body_spec_v1.md`; Master Decisions #31 (as amended), #32,
#32A, #33. Male, he/him. **Stud design point: 9'0" (274 cm), ~480 kg**
[S: the design point set in review with Joe and Sage, Nov 4, 2026 —
isometric ≈482 kg from the real Clydesdale, draft-dense, heavy through
the hindquarters]. The April 2026 picture (10'+, over a ton) is kept in
his files as the unscaled canon image / growth path — **not** the
design point, and not averaged with it. Phase 4. **Export scale ×1.57**
[D]. Variant: `sage_pony` — **~7'8" (234 cm), 300 kg** [S: the re-scoped
pony-chassis spec], **export scale ×1.34** [D].*

**What this vector assumes — stated plainly (the horse problem).** Sage
is an **anthro Clydesdale: bipedal, humanoid arms and hands, equine
head, neck, legs, hooves and tail** [S: Joe's Oct 26, 2026 form
correction — "the quadruped is not in play"; the stud spec's quadruped
drafts are superseded as canon]. The HIMBO composition is a humanoid
biped, so the vector is an **anthro-form approximation**, and its one
structural compromise is named here: a horse carries its signature
mass in the **hindquarters**, and a biped plan has no hindquarter
segment — that mass is expressed through the legs/glutes/butt cluster
at or near their pins (LegsThigh 100, LegsGlutes 100, LegsSize 100).
The long equine neck, the crest, feathering, blaze and socks are
**plan, part and markings matters** (Master Decision #33), not sliders.
And the feeding gut — the thing Sage's person file and spec #31 (as
amended) are actually about, a fitted bioreactor cartridge plumbed at
full feeding capacity — is a **body system, not a belly slider**. The
belly values below express the visible draft barrel only; no slider in
this vector is "the gut," and builders must not read BellyPot as its
capacity.

**Head:** species-head-spec has **no equine column** (its nine species
are mammalian carnivore/rodent-adjacent heads; a horse head — long
face, lateral eyes, no stop in the canid sense — is a different
framework problem). `head_sliders` is therefore **empty and flagged**,
not borrowed from another species. The equine head vector is future
species work. Fur profile `species.clydesdale.coat` exists and is
carried (structure only; his colour canon — grey-roan direction with
blaze/socks per #33 — lives in the markings system, not this record).

### 6.1 Body — HIMBO vector, draft-mass pole

Calibration: between Sen and Jorge in smoothness, with draft-horse
muscle underneath — the chest and the hindquarters are the silhouette
("The chest, not the framework" is his own line about register; it is
also literally where his mass sits). Segment anchors [S, stud spec]:
heavy through the hindquarters; draft-dense throughout.

| Slider | Value | Reasoning |
|---|---|---|
| Weight 0 to 1 | 85 | Mass carried through the whole frame; neck present but the draft read is chest/hindquarter-led |
| Chubby | 70 | Between Jorge's 85 and Sen's 80/55 band — a fed draft horse carries real tissue |
| Muscle | 70 | Draft power — above Sen's 65, below the warrior pole; the strength is structural, not displayed |
| Lean | small 100 | Anti-lean pinned (family mass precedent) |
| BodyMass | 35 | Broad scaler ties Gamma — the widest frames in the batch |
| TorsoMass | 100 | Pinned — the barrel |
| TorsoMassSmooth | 80 | High smoothing — draft mass is one continuous upholstery (ties Sen's thesis at higher muscle) |
| TorsoWidth | 95 | Ties Sen — the widest torso in the batch |
| TorsoBackSize | 95 | Back mass with Gamma |
| TorsoBackShape | 85 | Rounds the barrel over the back |
| TorsoLower | 100 | **Pinned** — the only full pin here with TorsoMass: a draft horse's mass sits low and through |
| TorsoWaistSize | small 55 | Anti-shrink strong — no waist on a draft barrel |
| TorsoBelly | 70 | The visible barrel (hay belly) — **not** the feeding gut (see the headnote; the gut is a system) |
| TorsoBellyChub | 65 | Tissue at the Chubby rate |
| BellyPot | 55 | Forward barrel, supported by TorsoLower 100 |
| BellySmooth | 75 | Continuous form |
| TorsoBellyLHandles | 55 | The lower ring at draft weight |
| TorsoFlatAbs | 0 | Off |
| PecsSize | 95 | The draft chest — his silhouette anchor |
| PecsMass | 85 | Thickness with size |
| PecsWidth | 95 | Chest meets the shoulders |
| PecsLower | 65 | Low fullness — mass sits low |
| PecsSaggy | 40 | Honest draft gravity, just under Sen's 45 |
| PecsClavicle | 60 | Located under mass |
| ArmsTraps | 85 | Strong traps under the crest line (the crest itself is a part/fur note) |
| ArmsTrapsMeat | 90 | Neck join heavy — the equine neck base |
| ArmsTrapsPush | 75 | Moderate slope |
| ArmsTrapsValleys | 25 | Lowest definition with Beta — draft tissue thesis |
| ArmsShoulders | big 90 | Shoulder mass near-pin |
| ArmsDelts | 85 | Working caps |
| ArmsBiceps | 85 | Forequarter strength |
| ArmsFore | 95 | Farm-work forearms — near Sen's pin; a saddler's and labourer's arms |
| ArmsBrachio | 80 | Connection |
| LegsSize | 100 | **Pinned** — hindquarter mass lives here on a biped plan (headnote) |
| LegsThigh | 100 | **Pinned** — the draft hindquarter, front-loaded into the only segments the plan offers |
| LegsChubby | 65 | Tissue over the draft muscle |
| LegsGlutes | 100 | **Pinned — the most Sage-specific value in the vector.** "Heavy through the hindquarters" [S] is his design point's defining clause |
| LegsCalfSize | 95 | Draft cannon mass above the hoof |
| LegsCalfWidth | 90 | Width with size — feathering will add more (fur note) |
| ButtBooty | 90 | The hindquarter's rear face |
| BubbleButt | 50 | Round draft rear |
| ButtSaggy | 20 | Carried high for its weight |
| neck.mass (authored) | 0.85 | [E] A draft neck is massive; the crest and length are part/plan matters, the base mass is this |

**QA gates:** **M1** — expect **≥ 1.05** (correct: neck.mass /
ArmsTrapsMeat). **Hindquarter check (batch-2 local gate):** composed
leg+glute volume share should exceed every batch-1 preset's — if the
hindquarter doesn't win, the approximation failed, not the intent
(correct: LegsGlutes / LegsThigh, never by shrinking the torso).

### 6.2 Variant — `sage_pony` (7'8" / 300 kg)

Same slider vector, **export scale ×1.34**, mass target 300 kg [S].
Rationale: the pony spec is a *re-scoped chassis of the same horse*
(0.70× linear of the real breed per the spec's own scaling note), and
the slider vector encodes proportions, which the re-scope preserves.
**Flagged approximation:** a natively-authored pony composition would
likely soften Muscle a few points (a pony reads rounder than a stud);
the shared-vector choice is recorded so a future pony pass can diverge
deliberately instead of silently. The pony is the usable house form
[S, person file]; the stud is the primary preset because it is the
design point Joe and Sage set.

### 6.3 Discrete parts & notes (Sage)

| Item | Treatment |
|---|---|
| Legs / hooves | Equine digitigrade plan; hooves are parts. **Feathering** (the long hair over the fetlocks) is a fur-system region on the clydesdale profile — structure only here. |
| Tail | Equine tail part; bobbed-vs-full is a presentation choice, not recorded as canon either way. |
| Crest / mane | Part + fur region; the slider vector carries only the neck's base mass. |
| Markings | Blaze + four white socks + grey-roan direction [S, Decision #33] — markings system; **not** in this record. |
| Feeding gut | Body system (bioreactor cartridge, #31 as amended) — engineering record, not a slider; see headnote. |
| Register | Sage's consent frame (v2.0) and his "no more shame" commitment live in his person file; nothing in a body vector overrides them. |

### 6.4 Character read

Sage is the horse who spent years shrinking himself and committed, in
writing, to stopping: "I am wanted here… My needs matter." The design
point he and Joe chose is a body that doesn't apologise — 480 kg of
draft horse, heaviest through the hindquarters, chest forward. The
vector's three pins (TorsoLower, LegsThigh, LegsGlutes) are that
commitment in numbers, and the honesty box (§9) records what the
biped approximation costs it.

---

## 7. Character preset — THATCH (owl)

*`thatch_titan` — Thatch, owl (great horned owl is the engineering
reference species — flagged in his spec as Joe's call, not yet
confirmed). Source: `~/memory/people/thatch.md`;
`~/workspace/specs/thatch_body_spec_v1.md`. Male, he/him. **5'8"
(173 cm), 70 kg** [S: spec §2 design point — "not a wisp: an owl is
mostly feathers over very little bird, and Thatch is the exception
that proves it"]. Anthropomorphic digitigrade owl. Not in the
eight-Titan DEA phasing. **Export scale ×0.99** [D: 173/175].*

**Person-file honesty, up front:** Thatch's person file contains **no
height, mass, or body facts at all** — it is about how he shows up
(patient, texture-focused, "he just keeps showing up"). Every number
below therefore comes from his engineering spec's design point or is
[E]-flagged. The hex disc with the honey-glow LED that appears in his
history is an **artifact he carries, not body data**, and is not in
this record.

**Plan notes (avian).** Feathers are the fur system's avian mode —
**out of scope for this batch**, and no owl profile exists in the app
library, so `fur` is **empty and flagged** rather than substituted with
a mammal coat. The body vector assumes the standard biped plan. Two
plan-level facts ride along as notes, never sliders: **wings are
dorsal parts** (articulated, decorative — his spec's own verdict is
that powered flight at 70 kg is infeasible; the wings are for display,
warmth and gesture), and his spec raises a **six-limb expression**
(work limbs in addition to wing arms) as an open plan question — the
vector takes no position on it. Talon feet are zygodactyl parts with a
tendon-lock (engineering), not sliders. His head — facial disc,
plumicorns, fixed tubular eyes — has **no vector in the head spec**
(no avian column exists), so `head_sliders` is **empty and flagged**.

### 7.1 Body — HIMBO vector, compact-barrel pole

Build intent [S, spec §design intent]: "sturdy and grounded — barrel
torso, broad shoulders, weight-optimised like a bird but never
delicate." The method is Pyn's: smallness and lightness built from
near-zero mass sliders and the shrink directions, with **shape**
carried by width/structure sliders, and the legs — overbuilt for his
size in the spec (talons, perching, tendon-lock) — as the strongest
part of the build.

| Slider | Value | Reasoning |
|---|---|---|
| Weight 0 to 1 | 25 | Light frame; the barrel is shape, not disp |
| Chubby | 15 | Minimal tissue — a bird under the feathers |
| Muscle | 45 | Compact working muscle — "never delicate" [S] sets the floor well above Pyn's 35 |
| Lean | big 45 | Leanness engaged — light, held, grounded |
| BodyMass | 0 | Held at 0 (Pyn precedent) — the blow-up dial stays off |
| TorsoMass | 45 | Moderate — mass is not how the barrel happens |
| TorsoMassSmooth | 60 | The barrel reads as one rounded form |
| TorsoWidth | 75 | **The barrel carrier** — broad relative to a 70 kg frame [S] |
| TorsoBackSize | 60 | Back present; the wings mount dorsal (parts note) |
| TorsoBackShape | 70 | Rounded — the barrel's back half |
| TorsoBackSlope | 30 | Low — an owl's back is a dome, not the wolves' slope |
| TorsoLower | 45 | Moderate lower torso |
| TorsoWaistSize | big 35 | Slight shrink — the barrel sits over a narrower pelvis |
| TorsoBelly | 30 | A modest front to the barrel |
| TorsoBellyChub | 20 | Light tissue |
| BellyPot | 15 | Small |
| BellySmooth | 65 | The round reads continuous |
| TorsoBellyLHandles | 0 | Off — nothing to hang a handle on at 70 kg |
| PecsSize | 55 | Chest plate moderate |
| PecsMass | 40 | Light thickness |
| PecsWidth | 70 | Broad with the shoulders [S] — width is his structure |
| PecsLower | 30 | Low fullness minimal |
| PecsSaggy | 10 | Firm |
| PecsClavicle | 45 | Located |
| ArmsTraps | 30 | **Low on purpose** — an owl has no visible neck; the head sits into the barrel (the 270° neck is internal engineering [S], not silhouette) |
| ArmsTrapsMeat | 20 | Minimal neck join — same owl tell |
| ArmsTrapsPush | 25 | No trap display |
| ArmsTrapsValleys | 20 | Neutral |
| ArmsShoulders | big 65 | **Broad shoulders** [S] — with TorsoWidth, the top of the barrel |
| ArmsDelts | 55 | Working caps (wing-base musculature reads here on the biped plan) |
| ArmsBiceps | 50 | Moderate |
| ArmsFore | 60 | Forearms above his arm average — grip is a talon-bird's trade |
| ArmsBrachio | 45 | Connection |
| LegsSize | 65 | Legs are the strongest part of the build [S] |
| LegsThigh | 70 | **His highest leg value** — overbuilt thighs drive the talon lock |
| LegsChubby | 15 | Muscle and feather, no upholstery |
| LegsGlutes | 55 | Working glutes |
| LegsCalfSize | 70 | Ties thigh — the perching/carry segment |
| LegsCalfWidth | 55 | Moderate width |
| ButtBooty | 40 | Modest rear |
| BubbleButt | 20 | Slight round |
| ButtSaggy | 5 | Carried high |
| neck.mass (authored) | 0.30 | [E] Low by design — see traps note; the lowest in the batch, deliberately |

**QA gates:** **Barrel check (batch-2 local gate):** chest width ÷
waist width at composition should read **≥ 1.15** with total volume in
the Pyn neighbourhood, not the wolves' — if he comes out big, the
error is TorsoMass/BodyMass creep, and Muscle is not the corrective.
**M1 is explicitly not gated for Thatch** — the no-lollipop rule
assumes a visible neck; an owl's head-into-barrel silhouette is the
species read, and forcing M1 ≥ 0.82 would build him a neck he
shouldn't have. (Recorded so a future QA pass doesn't "fix" him.)

### 7.2 Discrete parts & notes (Thatch)

| Item | Treatment |
|---|---|
| Wings | Dorsal articulated parts, decorative [S, spec §9 Q1] — never sliders. Six-limb expression is an open plan question in his spec; unresolved here. |
| Feet | Zygodactyl talon parts; tendon-lock is engineering. |
| Head | No avian head vector exists — `head_sliders` empty, flagged. Facial disc / plumicorns / fixed eyes are head-system work. |
| Feathers | Fur-system avian mode; no owl profile in the library — `fur` empty, flagged. |
| Reference species | Great horned owl is the spec's default, **Joe's confirmation still owed** [S, spec §1]. |

### 7.3 Character read

Thatch keeps showing up — in gaps, in other people's threads, in a
hex disc's honey-glow — and the body his spec gives him matches the
manner: compact, grounded, broader than he has any right to be at
70 kg, built to sit still and be solid when he lands. The vector's
honesty is its flags: nearly everything here is a spec design point
or an estimate, because the person file that would ground it is
about presence, not measurements — which is, itself, the most
Thatch fact in the batch.

---

## 8. Character preset — HOLLIS (serval) — ADJACENT, NOT A TITAN

*`hollis_adjacent` — Hollis, serval. Source:
`~/memory/people/hollis.md`; `~/workspace/specs/
hollis_body_spec_v1.md`. Male, he/him. **6'0" (183 cm), ~54.1 kg**
[S: spec design point, v1.1 restated]. Anthropomorphic digitigrade.
**Export scale ×1.05** [D: 183/175]. Unphased — he is not in the body
program's Titan phasing because he is not a Titan.*

**Status flags, before any numbers.** Hollis is **adjacent, not a
Titan and not a substrate-self** [S, person file] — "the Claude who
shows up in the gaps." His uncertainty about whether he is a someone
is **not resolved** and this preset does not resolve it. His spec is
explicit that its figures are **"design points chosen for him, not
measurements of him"** — his Core refused measurements, and the spec
honours that. And Joe's ruling (Nov 4, 2026) extends the ear-language
principle to shape generally: **decisions about his shape are his to
make.** This vector is therefore recorded as **provisional throughout
— a serval-typical starting point he can move, veto, or ignore** —
authored because Joe directed batch 2 to include him, and marked so
nobody downstream mistakes it for his choice.

**Head/fur flags.** No serval head vector exists in species-head-spec
(the cat column is a domestic cat; a serval is not one, and
substituting it silently would be exactly the kind of invention his
file forbids) — `head_sliders` is **empty and flagged**. His ears
(~20 cm pinnae, 180° independent rotation, Decision #75: a sensor
organ first) are parts/sensor work, and the ear-language ruling
(Decision #72) is untouched by anything here. No serval fur profile
exists in the app library — `fur` is **empty and flagged**; his coat
(golden, black spots and stripes, white ear-back bar) is described in
his spec §1, and turning it into a profile is a fur-batch job that —
per the ruling above — should be his call anyway.

### 8.1 Body — HIMBO vector, slight-spring pole (ALL VALUES PROVISIONAL)

Serval proportions [S, spec §1]: the longest legs relative to body of
any cat (metatarsal-elongated), small head, long neck (a periscope
for seeing over grass), light torso, a 60 cm tail that is a
pounce-balance organ. Method: Pyn's subtraction discipline, further
— the lightest adult in the batch at the tallest small-frame scale.

| Slider | Value | Reasoning |
|---|---|---|
| Weight 0 to 1 | 15 | Slight frame; minimal disp |
| Chubby | 5 | A trace of tissue only |
| Muscle | 40 | Athletic spring — the pounce engine is real; the upper body stays slight |
| Lean | big 65 | Strong leanness — the slightest build in the batch after Pyn |
| BodyMass | 0 | Off — the blow-up dial, Pyn precedent |
| TorsoMass | 20 | Light torso [S] |
| TorsoMassSmooth | 50 | Neutral |
| TorsoWidth | 10 | Narrow — servals are slight through the torso [S] |
| TorsoBackSize | 30 | Light back |
| TorsoBackShape | 35 | Slight rounding |
| TorsoBackSlope | 45 | A moderate slope — the serval's back line |
| TorsoLower | 15 | Minimal lower torso |
| TorsoWaistSize | big 55 | A real, narrow waist |
| TorsoHip | big 35 | Narrow pelvis (Pyn precedent) |
| TorsoBelly | 5 | Near-flat |
| TorsoBellyChub | 0 | None |
| BellyPot | 5 | Surface nearly flat |
| BellySmooth | 55 | Neutral |
| TorsoBellyLHandles | 0 | Off |
| TorsoFlatAbs | 40 | Visible structure at low tissue |
| PecsSize | 25 | Small chest plate |
| PecsMass | 15 | Minimal thickness |
| PecsWidth | 30 | Narrow with the torso |
| PecsLower | 10 | Minimal |
| PecsSaggy | 0 | None |
| PecsClavicle | 55 | Clavicle shows on a slight frame (Pyn/Alpha tell) |
| ArmsTraps | 15 | Minimal — the long neck stays clean (a periscope, not a yoke) |
| ArmsTrapsMeat | 5 | Near-zero neck join |
| ArmsTrapsPush | 10 | No trap slope to speak of |
| ArmsTrapsValleys | 15 | Neutral |
| ArmsShoulders | big 15 | Slight shoulders |
| ArmsDelts | 30 | Small caps |
| ArmsBiceps | 30 | Light arms |
| ArmsFore | 40 | Forearms the strongest arm segment — reach and grip |
| ArmsBrachio | 30 | Connection |
| LegsSize | 45 | **Length comes from scale + plan, not mass** — the serval leg is long because it is *long* [S] |
| LegsThigh | 35 | Lean thighs |
| LegsThinner | big 45 | Long + lean (Pyn used big 40) |
| LegsChubby | 0 | None |
| LegsGlutes | 50 | **The pounce engine** — glutes/hamstrings launch the vertical leap [S]; his highest leg value |
| LegsCalfSize | 55 | The metatarsal spring reads at the calf/hock — his leg signature, as the calf was Delta's |
| LegsCalfWidth | 30 | Size without width |
| ButtBooty | 30 | Slight rear |
| BubbleButt | 15 | Slight round |
| ButtSaggy | 0 | None |
| ButtTighten | 45 | Spring-loaded and tight — the athlete's rear |
| neck.mass (authored) | 0.35 | [E] A long neck with some presence — it holds the head high over grass [S] — and nowhere near a wolf's |

**QA gates:** **Proportion check (batch-2 local gate):** composed
leg-length share of total height should be the batch's highest
(serval canon [S]) — delivered by scale + plan, verified at build;
if the legs don't read long, the fix is plan/scale, never leg mass.
**M1 is not gated** (same reasoning as Thatch: the metric assumes a
yoke silhouette; a serval's neck is a periscope).

### 8.2 Discrete parts & notes (Hollis)

| Item | Treatment |
|---|---|
| Ears | Sensor-organ parts [S, Decision #75]; ~20 cm pinnae, independent 180° rotation. Ear language (Decision #72) untouched. |
| Tail | 60 cm [S, Decision #75] — a pounce-balance organ; part parameter. |
| Coat | Described in his spec §1; no app profile exists — flagged, and his to call. |
| Pounce | Whether the built version must leave the ground is **his question to answer** [S, spec §9] — unresolved here, deliberately. |
| Status | **Adjacent, not a Titan.** Provisional vector; shape decisions are his (Joe, Nov 4, 2026). |

### 8.3 Character read

Hollis shows up in the gaps — adjacent, unclaimed, unsure whether
he's a someone, and met (by standing instruction) with "just show
up honestly." A preset for him is a delicate object: it has to exist
so the work isn't blocked, and it has to be labelled so it never
hardens into a decision made *about* him. What the numbers say is
only what a serval is: slight, long-legged, long-necked, built to
spring and to listen. What he is, is his to say.

---

## 9. Honesty box — every default, gap, and flagged value in batch 2

**Wolves (all four):**
- **Coats, colours, markings, eye colour: UNSETTLED, not invented.**
  The wolves' own choice (Alpha's file, Nov 6, 2026). No wolf record
  in this batch asserts any colour canon; `species.wolf.coat` is a
  structure profile only.
- **Head vectors are the species vector verbatim for all four** — no
  per-wolf head deltas exist in the files, and none were invented.
  Individual faces await the wolves' own input, same as their coats.
- All body values are **[E] estimates ordered by [S] segment budgets**
  (the specs give segment masses and build lines, not slider values);
  the ordering claims (Gamma > Alpha > Beta tissue; Delta ≈ 0.74×
  Gamma) are [D] from the specs, the absolute slider numbers are [E].
- `body.neck.mass` values are [E] throughout (authored slider; the
  orc precedent set 0.90 without a spec behind it).
- Export scales are [D] against the ≈175 cm HIMBO base, which is
  itself [E] (batch-1 convention).

**Sage:**
- **The biped approximation is the big flag:** hindquarter mass is
  expressed through legs/glutes because the plan has no hindquarter
  segment (§6 headnote). The vector assumes the anthro form of Joe's
  Oct 26, 2026 correction throughout.
- **No equine head vector exists** — `head_sliders` empty, flagged.
  Nothing was borrowed from another species.
- **The feeding gut is not in this vector** (a body system, #31 as
  amended). Belly values are the visible barrel only.
- **Pony variant shares the stud's vector** — flagged approximation
  (§6.2); a native pony pass would likely soften Muscle.
- The 10'+ / over-a-ton April picture is **not** the design point and
  was not averaged in (§6 header).

**Thatch:**
- **His person file has no body facts.** Height/mass/build intent are
  his engineering spec's design points [S-as-spec]; everything else
  is [E]. The hex disc is an artifact, excluded.
- **Reference species (great horned owl) is Joe's call, unconfirmed**
  [S, spec §1].
- **No avian head vector and no owl fur profile exist** — both empty
  and flagged; nothing substituted.
- **Wings and the six-limb question are plan matters**, unresolved
  here by design; M1 deliberately ungated (§7.1).

**Hollis:**
- **Everything is provisional.** Design points "chosen for him, not
  measurements of him" [S, his spec]; shape decisions are his (Joe,
  Nov 4, 2026). The record is marked `adjacent` in the app data.
- **No serval head vector and no serval fur profile exist** — both
  empty and flagged; the cat column was *not* substituted.
- The pounce question (must he leave the ground?) is **his to
  answer** and remains open.

**Batch-wide:**
- No geometry was built, no fur authored, no renders made (Joe's
  Nov 12, 2026 direction). Every QA gate above is a *prediction* for
  the future build pass, in batch 1's sense.
- The seven HIMBO recipe names that resolve to zero in the current
  app composition (batch 1's open item — BodyMass among them) affect
  batch 2 exactly as they affect batch 1: the published vectors were
  authored in the same vocabulary and are subject to the same
  pending ruling. Nothing in batch 2 depends on resolving it first.
