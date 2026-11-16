# Preset Spec — BARA ORC for AnthroForge

*Preset family spec, Nov 12, 2026. Joe's direction: "a big bara orc design would
work great in avatar creator," plus his teeth ruling (Nov 12, 12:16 CST): one
universal jaw arcade, diet types are morphs of it, the orc tusk is the lower
canine scaled on that same axis — no bespoke orc teeth rig.*

*This is a **preset family on the existing systems**, not a new species base:
the head is extreme settings on the 25 sliders of
`species-head-spec.md` §3.1 plus discrete part variants; the body is slider
vectors in the decoded HIMBO vocabulary
(`~/workspace/character_assets/learned/himbo_sliders_full.json`,
`himbo_presets_all.json`); the teeth are extreme values on the shared arcade
(§4). Nothing here needs new topology except the part variants in §2.4/§5.3.*

*Conventions: head proportions are ratios to head length **L** (nose tip →
occiput); head slider values use the species-spec formula
`value = 100 × (target ratio − neutral) / span`, rounded to the nearest 5.
Body values are HIMBO BodySlide **big-end percentages (0–100), small-end 0
unless stated**. Every number is tagged **[S]** sourced, **[D]** derived from
sourced numbers, **[E]** estimate / art-directed. Estimates are never presented
as measured fact — and for orc, most head numbers are [E] by necessity: no
craniometry of a fictional species exists. What anchors them is (a) the nearest
real biological analogue, the gorilla (§1.1), and (b) 40 years of consistent
orc art direction (§1.2), cross-checked so no orc value exceeds the most
extreme real anchor on the head chart by more than the fiction requires.*

---

## 1. Reference anchors

### 1.1 The biological anchor — gorilla [S-qual.]

The orc head is, anatomically, the gorilla plan pushed onto a humanoid frame:
a masticatory apparatus oversized relative to the braincase. Sourced
qualitative facts (comparative primate anatomy; 3B Scientific gorilla skull
manual; ScienceDirect *Troglodytes* overview):

- **Face/jaw disproportionately large vs the cerebral cranium** in mature
  males; the braincase is the small part of the skull. [S-qual.]
- **Continuous supraorbital torus** — one heavy brow bar linked by a glabellar
  ridge, not two separate bumps. [S-qual.]
- **Marked prognathism**, especially males: the mandible projects forward of
  the cranial base. [S-qual.]
- **Sagittal crest + nuchal crest in adult males**, grown as attachment area
  for hypertrophied temporalis/neck musculature. [S-qual.]
- **Mandible square and massive, chin absent** (simian shelf instead). [S-qual.]
- **Nasal aperture large and broad.** [S-qual.]
- **Canines large, dagger-like, longer in males**, extending past the occlusion
  plane; upper jaw carries a **diastema** the lower canine closes into.
  [S-qual.] — this is the real-world template for the tusk (§4).

### 1.2 The muscle anchor — human masseter, measured [S]

Ultrasound studies of healthy adult men (PubMed 1918575; Int. J.
Odontostomat. 2021; MDPI Diagnostics 2024):

| State | Masseter thickness (male) |
|---|---|
| Relaxed | **9.7–11.6 mm** [S] |
| Contracted | **13.0–15.1 mm** [S] |
| Clinical hypertrophy, contracted | **≈16.5 mm** [S] |

The orc masseter target is set at **24–30 mm at rest [E]** — roughly 1.6–2×
the human *hypertrophy* case. This single number is the engine of the whole
orc head: it is what JawDepth, JawWidth and CheekWidth are actually drawing
(§2.3).

### 1.3 The fiction anchor — orc canon [E, art-directed]

Consistent across Warhammer (Orks, 1987–), Warcraft (Blizzard, 1994–) and
film orcs (Weta LOTR, 2001–03): protruding lower jaw with underbite, upturned
lower-canine tusks clearing the upper lip, heavy unbroken brow, low sloping
forehead, wide flat nose with flared nostrils, small deep-set eyes, pointed
ears swept back, head carried small on a trap-dominated neck. No numeric
proportions are published by any of these sources — every canon-derived
number below is **[E]**, set by eye against that body of reference and
sanity-checked against §1.1/§1.2 and the species head chart.

### 1.4 The body anchor — HIMBO, decoded [S — our own measurements]

From `learned/` (Skyrim units; 1 unit ≈ 1.428 cm; base mesh 9,346 verts,
z-span 102.6 units):

| HIMBO block | Diff verts | Mean disp | p95 | Max | Displacement lives in |
|---|---|---|---|---|---|
| BodyChubby | 9,229 | 0.92 | 2.65 | 4.00 | torso 34%, chest 30%, legs 21% |
| BodyMuscle | 9,080 | 0.55 | 1.24 | 1.71 | chest 35%, legs 29%, arms 20% |
| BodyLean | 9,111 | 0.86 | 1.99 | 2.82 | chest 45%, torso 16% |
| BodyWeight 0 to 1 | 7,797 | 0.26 | 1.21 | 1.91 | **neck 46%**, chest 28% |

Calibration presets on disk [D]: **HIMBO Daddy** (Chubby big 100, TorsoMass
small+big 100, LegsSize 100) and **HIMBO Chonky** (TorsoMass 100, PecsSize
100, LegsThigh 100, ArmsTrapsMeat big 100) are the two fattest/mass-heavy
shipped HIMBO shapes — the two orc sub-presets in §3 start from these two
poles and push past them in opposite tissue directions.

---

## 2. HEAD — orc on the 25-slider framework

> **Revision, Nov 12, 2026 (per `brow-study.md` §6.2):** the single
> BrowRidge +90 is replaced by the decomposed brow vector —
> BrowProjection +135, BrowThickness +85, BrowContinuity +100,
> BrowShelf +90, BrowPosition −20, BrowPadding +10, BrowScowl +35.
> Read as projection, +90 was only Krapina-class Neanderthal; the
> gorilla anchor (+150) exceeds the orc (+135). Brow entries in
> §2.1/§2.2/§2.4/§5.4 below are updated accordingly.

### 2.1 Orc anchor ratios

Neutral column and spans are the species spec's (§3.1 there). Orc targets:

| Ratio | Neutral | Orc target | Tag | Reasoning |
|---|---|---|---|---|
| Muzzle fraction of L | 0.33 | 0.30 | [E] | The orc "muzzle" is short — the protrusion is *jaw*, not rostrum (§1.1 prognathism lives in the mandible) |
| Rostrum W / L | 0.17 | 0.23 | [E] | Wide, blunt snout block; exceeds every chart species except jaguar-class felids |
| Taper index | 0.50 | 0.30 | [E] | Squared-off, barely narrows toward the nose (canon §1.3) |
| Rostrum depth / L | 0.20 | 0.26 | [E] | Deep enough to house the upper canine roots + diastema |
| Nose W / muzzle W | 0.55 | 0.70 | [E] | Broad nasal aperture [S-qual. §1.1] + flared nostrils (canon) |
| Braincase W / L | 0.36 | 0.32 | [E] | Braincase small vs face [S-qual. §1.1]; near wolf's 0.32 [S] |
| Skull height / L | 0.31 | 0.27 | [E] | Low, back-sloping forehead (canon); no dome |
| Cranium fraction of L | 0.62 | 0.60 | [E] | Slightly face-heavy length split |
| Stop depth index | 0.30 | 0.20 | [E] | Forehead runs into the brow bar with almost no break — the felid-style unbroken line, but from slope, not flatness |
| Frontal W / L | 0.24 | 0.20 | [E] | Narrow forehead pinched between brow bar and temporalis |
| Ear length / L | 0.40 | 0.46 | [E] | Moderate pointed ears — longer than wolf's 0.38 [S], nowhere near canid extremes |
| Ear W / ear length | 0.55 | 0.45 | [E] | Narrow blades |
| Ear placement index | 0.50 | 0.40 | [E] | Set low and back, behind the jaw angle line |
| Ear spread index | 0.50 | 0.58 | [E] | Wide-set to clear the wide skull |
| Ear tilt index | 0.55 | 0.43 | [E] | Swept back (negative = away from pricked) |
| Ear tip index | 0.50 | 0.80 | [E] | Hard point — pairs with `ear_point` variant (§2.4) |
| Mandible height / L | 0.28 | 0.36 | [E] | **The orc feature.** Gorilla mandible "square and massive" [S-qual.]; deepest on the chart (lion 0.34-equiv. is next) |
| Mandible length / L | 0.74 | 0.80 | [E] | Prognathic overshoot past the upper tooth row (underbite) |
| Jaw (bi-angular) W / L | 0.40 | 0.50 | [E] | Masseter + ramus flare (§1.2: muscle alone adds ~30–40 mm of width at orc scale) |
| ZB / L | 0.58 | 0.68 | [E] | Zygomatic + masseter mass; level with leopard 0.67 [D], below jaguar 0.837-equiv. — wide, not widest |
| Ruff index | 0.30 | SM 0.42 / BB 0.28 | [E] | Not fur — this slider is re-read as **jowl/neck soft tissue** for orc (§2.3); sub-presets differ |
| Orbit Ø / L | 0.15 | 0.11 | [E] | Small eyes (canon); smallest on the chart, below wolf/dog 0.13 [E] |
| Interorbital W / L | 0.19 | 0.17 | [E] | Eyes close-set under the single brow bar |
| Convergence index | 0.35 | 0.55 | [E] | Forward-facing, predator read |
| Brow (supraorbital torus) | — | decomposed — §2.2 brow vector | [E] | Continuous torus [S-qual.]; near-gorilla, past every Neanderthal — **not** the chart's maximum: the gorilla anchor exceeds it (BrowProjection +150 vs orc +135; brow-study.md §6.2) |

### 2.2 The 25 sliders — orc values

One orc head serves both sub-presets; the three sliders where they differ are
split. Worked derivations (species-spec formula):

- JawDepth: (0.36 − 0.28)/0.12 × 100 = **+65**
- JawWidth: (0.50 − 0.40)/0.14 × 100 = **+70**
- Brow: no single derivation — BrowRidge is decomposed per brow-study.md §6.2 into BrowProjection **+135**, BrowThickness **+85**, BrowContinuity **+100**, BrowShelf **+90**, BrowPosition **−20**, BrowPadding **+10**, BrowScowl **+35** [all E]. (The retired BrowRidge +90, read as projection, is a 22.8 mm midorbit chord — Krapina-class Neanderthal, short of this brief.)
- EyeSize: (0.11 − 0.15)/0.10 × 100 = **−40**

| # | Slider | Orc | Notes |
|---|---|---|---|
| 1 | MuzzleLength | −15 | Short rostrum; length is in the jaw, not the snout |
| 2 | MuzzleWidth | +75 | |
| 3 | MuzzleTaper | −50 | Blunt, squared nose end |
| 4 | MuzzleDepth | +60 | |
| 5 | NoseSize | +50 | Pairs with `nose_orc` variant (§2.4) |
| 6 | CraniumWidth | −25 | |
| 7 | CraniumHeight | −35 | Low sloping forehead |
| 8 | CraniumLength | −10 | |
| 9 | StopAngle | −25 | Brow bar overhangs a near-absent stop |
| 10 | ForeheadWidth | −35 | |
| 11 | EarHeight | +10 | |
| 12 | EarWidth | −30 | |
| 13 | EarPlacementHeight | −25 | Low, behind the jaw |
| 14 | EarSpread | +20 | |
| 15 | EarTilt | −25 | Back-swept |
| 16 | EarTipPoint | +65 | Plus `ear_point` variant at this extreme |
| 17 | JawDepth | +65 | Chart maximum class |
| 18 | JawLength | +60 | Underbite overshoot |
| 19 | JawWidth | +70 | |
| 20 | CheekWidth | +50 | SM +50 / BB +55 (BB reads wider — less tissue over the same flare) |
| 21 | RuffVolume | SM +25 / BB −5 | Jowl + submental tissue, not fur (§2.3) |
| 22 | EyeSize | −40 | Small, deep-set under the torus |
| 23 | EyeSpacing | −25 | |
| 24 | EyeForwardness | +40 | |
| 25 | BrowProjection | +135 | Bone layer; past Krapina (+100), under gorilla (+150) [E] |
| 26 | BrowThickness | +85 | Bone layer [E] |
| 27 | BrowContinuity | +100 | Unbroken bar — drives the `brow_torus` variant (§2.4) |
| 28 | BrowShelf | +90 | Carries the deep-set eye read (§5.4) [E] |
| 29 | BrowPosition | −20 | Soft brow low on the rim [E] |
| 30 | BrowPadding | +10 | Skin thinnest over the bar (§2.3) [E] |
| 31 | BrowScowl | +35 | Resting menace, muscle layer [E] |

**Builder flag — one extension the 25 cannot express:** prognathism is a
*forward translation* of the whole mandible, and no slider in the set moves
the jaw forward (JawLength lengthens it in place). The orc preset needs
either a 26th slider, **JawProtrusion** (mandible forward offset, anchor
0.00–0.06 L, orc ≈ 0.045 L → +75 on a 0.06 span [E]), or the equivalent fixed
offset baked into the orc jaw-region weights. Without one of these the head
reads as a wide-jawed human, not an orc. This is the single most important
line in §2.

**Chin:** the base jaw's chin point must be flattened to a simian shelf
[S-qual. §1.1] — handled as a sculpt note on the jaw region at JawDepth
extremes, or via the `jaw_orc` jaw-mesh variant (§2.4). A chin bump at these
settings breaks the read instantly.

### 2.3 Layered construction (Joe's rule: skull → muscles → tissue)

- **Skull layer.** Braincase small relative to the face block [S-qual.];
  continuous supraorbital torus as one bar; mandible thickened in corpus
  *and* ramus, chin absent; optional **sagittal crest strip** variant for
  the largest males [S-qual.]; nasal aperture broad. The skull alone should
  already read "orc-shaped, but skeletal" — per Joe's rule it is *not* the
  surface.
- **Muscle layer — where the orc actually lives.** Masseter: **24–30 mm at
  rest [E]** against the human 9.7–11.6 mm [S] — model it as a distinct
  slab from zygomatic arch to jaw angle; it, not bone, produces most of
  JawWidth +70 / CheekWidth +50. Temporalis: a full fan rising to the crest
  line, pinching the forehead (ForeheadWidth −35 is temporalis bulk seen
  from the front, not a narrow skull). Buccinator and orbicularis oris thick
  — the lips are muscular, which is what lets them clear the tusks (§4).
  Neck musculature continues unbroken into the traps (body §3) — no visible
  "neck gap" between head muscle layer and torso.
- **Tissue layer.** Thick skin over everything; the brow torus stays legible
  through it (skin is thinnest over the bar). **This layer is the sub-preset
  switch:** Strongman adds fat pads over the lower masseter edge and under
  the chin (RuffVolume +25), rounding the jaw angle; Bodybuilder thins the
  tissue to skin-over-muscle (RuffVolume −5), so masseter/temporalis
  separation reads. Same skull, same muscles — only tissue and slider
  vectors change. Never ship the muscle layer as the surface (too skeletal,
  Joe's rule) and never let tissue erase the torus.

### 2.4 Discrete part variants (head)

| Variant | Spec |
|---|---|
| `ear_point_orc` | Long-point ear on the standard ear-base topology; tip length +30% over the EarTipPoint +65 deformation [E]; slight backward hook. (Ear *shape* variants beyond this — Warhammer-style ragged/notched edges — are a texture-alpha + notch morph, not new topology.) |
| `nose_orc` | Flat, wide nose-leather tip mesh: nostrils flared laterally, philtrum short, nose sits *upturned* ~15° [E] so the upper lip line stays clear of the tusks. Scales with NoseSize. |
| `brow_torus` | Brow-region variant enforcing the continuous bar (no medial dip) at BrowContinuity ≥ +80 AND BrowProjection ≥ +80; below that the sliders alone suffice. |
| `jaw_orc` | Jaw-mesh variant: chin flattened to simian shelf, chin-point verts pulled back 0.02 L [E]. Use when JawProtrusion extension (§2.2 flag) is not implemented; the two together are the full solution. |
| `crest_sagittal` | Midline crest strip on the cranium (species spec §3.4 already defines the treatment) — adult-male, largest-scale orcs only; pairs with topknot hair (§5.3). |
| Brow horns / ridge horns | **Not canon orc** in any of §1.3's sources — orcs do not grow brow horns. Listed only to close the question: do not build. (If a horned variant is ever wanted it belongs to a different preset family — oni/tiefling territory — reusing the crest-strip attachment.) |
| Tusks | **Not a head part variant.** Tusks are the lower canines of the universal arcade — §4. |

---

## 3. BODY — bara on the HIMBO vocabulary

### 3.0 Shared orc body rules

- **Scale/height.** HIMBO base ≈ 175 cm human [E]. Orc export scale:
  Strongman **×1.20 → ≈210 cm**, Bodybuilder **×1.15 → ≈200 cm** [E].
  Head scale **×0.95 relative** [E] — the head reads small on the trap mass;
  ~8 head-heights total vs the human 7.5 [E]. Apply scale at export, never
  in the slider vectors.
- **The neck gap.** HIMBO has **no neck slider** — but its Weight block puts
  46% of its displacement in the neck region [S §1.4], and the traps family
  (ArmsTraps / TrapsMeat / TrapsPush / TrapsValleys) does the visible work.
  Both presets pin traps near maximum; if the neck still reads thin, the
  builder should add a **NeckMass** extension slider reusing the Weight
  block's neck-region verts [D]. Flagged, not assumed.
  **Update, Nov 12, 2026:** NeckMass is promoted to *required* by
  `BARA_LESSONS.md` §6 A2, and its canonical record now exists —
  `body.neck.mass` in `~/workspace/anthroforge-app/library/sliders/` —
  carrying the build spec and acceptance metrics (M1 ≥ 1.05 and
  M7 ≤ 0.25 at full value with traps pinned, SCM V-groove preserved).
  Record only; no geometry instance built yet. When it lands, the orc
  strongman calls it at **90** (BARA_LESSONS §6 B).
- **Posture note.** Canon orcs are often drawn hunched; that is a *pose*
  (spine/neck bone rotation), not a shape slider. Ship the presets upright;
  hunch belongs to the pose library. [E]

> **Revision, Nov 12, 2026 (per `BARA_LESSONS.md` §6 B/C; Shrink-Waist
> semantics resolved [S] by the decoded HIMBO display names in
> `presets-titan-batch1.md`):** TorsoWaistSize's decoded name is
> **"Shrink Waist"** — its big end *narrows* the waist, the opposite of
> this spec's original assumption. Three values corrected:
> **Bodybuilder TorsoWaistSize 15 → 85** (15 was a nearly unshrunk, wide
> waist — the widest of the two presets, the inverse of the V-taper
> design; 85 = strong shrink); **Strongman TorsoWaistSize 45 → 25**
> (the barrel wants minimal shrink; TorsoLower 100 already supplies the
> width); **Strongman TorsoHip 40 → 20** (TorsoHip is likewise
> "Shrink Hips"; strongman hips/glutes carry mass, and ButtBooty 70 is
> already set). This closes the §3.2 semantics flag and §6 item 4.

> **Revision, Nov 12, 2026 (per `BARA_LESSONS.md` §6 B/C + §6 A1/R16;
> muscle unification, and R13):** the two sub-presets now share one
> **MuscleVector — Muscle 80, ArmsTraps 95, ArmsTrapsMeat 100,
> ArmsTrapsPush 90, ArmsDelts 95, LegsSize 100, LegsThigh 100** [E —
> builder verifies the M-gates at both tissue settings]. The map's
> "traps family 95/100/90" is read in the §3.0 family order (ArmsTraps /
> TrapsMeat / TrapsPush); TrapsValleys is *not* unified — §6 C counts it
> tissue ("already tissue-correct" at 85), so it stays 40 (SM) / 85 (BB)
> with the definition family. Strongman changes: **Muscle 55 → 80**,
> ArmsTraps 90 → 95, ArmsDelts 90 → 95 (ArmsTrapsMeat 100, ArmsTrapsPush
> 90, LegsSize 100, LegsThigh 100 already at the shared values).
> Bodybuilder changes: **Muscle 100 → 80**, ArmsTraps 100 → 95,
> ArmsTrapsMeat 85 → 100, ArmsTrapsPush 100 → 90, ArmsDelts 100 → 95,
> LegsThigh 95 → 100. The poles now differ by TissueVector, not muscle,
> within the families the map names. Also applied from §6 B:
> **Strongman ArmsBicepsBack 60 → 75** (R13 — triceps carriers ≥ 0.7 ×
> ArmsBiceps 90, with margin; ArmsSide 75 already complied).
> *Scope note on the map's wording:* §6 C says the sub-presets "then
> differ ONLY in" its tissue list, but it names shared values only for
> Muscle / traps / delts / legs. Muscle-adjacent sliders it does not
> name (Weight, ArmsShoulders, ArmsDeltsUpper, ArmsBiceps, ArmsFore,
> ArmsBrachio, the TorsoBack and Pecs families) still differ between
> the tables below; the most literal reading — unify exactly the named
> components — is what was applied, and the rest is flagged here rather
> than silently harmonised. Revisit if the map is ever amended with
> shared values for those families.

### 3.1 Sub-preset A — `orc_bara_strongman` "Bara Orc — Strongman"

*Power-gut bara: maximal total mass, muscle under a working layer of fat.
Calibration pole: HIMBO Daddy + Chonky [D]. Tissue layer thick everywhere
(head §2.3 applies to the whole body).*

| Slider | Value | | Slider | Value |
|---|---|---|---|---|
| Weight 0 to 1 | 85 | | TorsoBackSize | 90 |
| Chubby | 65 | | TorsoBackShape | 85 |
| Muscle | 80 | | TorsoBackSlope | 80 |
| Lean | small 100 | | TorsoBackDefinition | 35 |
| TorsoMass | 100 | | TorsoShoulderInc | 75 |
| TorsoMassSmooth | 65 | | TorsoSterWidth | 90 |
| TorsoWidth | 85 | | TorsoSterHeight | 85 |
| TorsoLower | 100 | | TorsoSterDepth | 80 |
| TorsoBelly | 70 | | TorsoWaistSize | 25 |
| TorsoBellyChub | 65 | | TorsoHip | 20 |
| BellyPot | 55 | | ArmsTraps | 95 |
| BellySmooth | 60 | | ArmsTrapsMeat | 100 |
| TorsoBellyLHandles | 55 | | ArmsTrapsPush | 90 |
| TorsoFlatAbs | 0 | | ArmsTrapsValleys | 40 |
| TorsoVLine | 10 | | ArmsShoulders | big 85 |
| TorsoRibsDefinition | 15 | | ArmsDelts | 95 |
| PecsSize | 95 | | ArmsDeltsUpper | 70 |
| PecsMass | 80 | | ArmsBiceps | 90 |
| PecsWidth | 95 | | ArmsBicepsBack | 75 |
| PecsLower | 60 | | ArmsFore | 95 |
| PecsSaggy | 35 | | ArmsBrachio | 80 |
| PecsClavicle | 80 | | ArmsSide | 75 |
| LegsSize | 100 | | ButtBooty | 70 |
| LegsThigh | 100 | | BubbleButt | 45 |
| LegsChubby | 70 | | ButtSaggy | 20 |
| LegsGlutes | 75 | | LegsCalfSize | 85 |
| LegsCalfWidth | 80 | | | |

Read: belly is *carried*, not hidden — BellyPot 55 + TorsoBelly 70 under
TorsoMass 100 gives the strongman silhouette (gut inside a barrel torso,
never a Fat-Males-style soft overhang alone; the Fat Males learned morph —
mean disp 2.59, max 10.93 units, torso-concentrated [S, learned/] — is the
reference for what *pure* fat looks like, and this preset deliberately stays
short of it).

### 3.2 Sub-preset B — `orc_bara_bodybuilder` "Bara Orc — Bodybuilder"

*Cut-mass bara: same skeleton of mass, tissue layer stripped so muscle
groups separate. Calibration pole: HIMBO Muscle block, run at the shared
MuscleVector value (Muscle 80 — see the muscle-unification revision note
above §3.1), Lean shape partially engaged [D].*

| Slider | Value | | Slider | Value |
|---|---|---|---|---|
| Weight 0 to 1 | 70 | | TorsoBackSize | 100 |
| Chubby | 5 | | TorsoBackShape | 100 |
| Muscle | 80 | | TorsoBackSlope | 60 |
| Lean | big 40 | | TorsoBackCenter | 80 |
| TorsoMass | 90 | | TorsoBackDefinition | 95 |
| TorsoMassSmooth | 10 | | TorsoBackSerratusMid | 75 |
| TorsoWidth | 75 | | TorsoBackObliques | 80 |
| TorsoBelly | 5 | | TorsoShoulderInc | 90 |
| TorsoBellyChub | 0 | | TorsoSterWidth | 95 |
| BellyPot | 0 | | TorsoSterHeight | 90 |
| TorsoFlatAbs | 90 | | TorsoSterDepth | 85 |
| TorsoVLine | 85 | | TorsoWaistSize | 85 |
| TorsoRibsDefinition | 80 | | ArmsTraps | 95 |
| PecsSize | 100 | | ArmsTrapsMeat | 100 |
| PecsMass | 95 | | ArmsTrapsPush | 90 |
| PecsWidth | 100 | | ArmsTrapsValleys | 85 |
| PecsLower | 70 | | ArmsShoulders | big 100 |
| PecsMinor | 70 | | ArmsDelts | 95 |
| PecsCrease | 75 | | ArmsDeltsUpper | 90 |
| PecsSaggy | 0 | | ArmsDeltsShape | 80 |
| PecsClavicle | 90 | | ArmsBiceps | 100 |
| LegsSize | 100 | | ArmsBicepsBack | 85 |
| LegsThigh | 100 | | ArmsFore | 100 |
| LegsChubby | 10 | | ArmsBrachio | 90 |
| LegsGlutes | 90 | | ButtBooty | 80 |
| LegsCalfSize | 95 | | BubbleButt | 60 |
| LegsCalfWidth | 85 | | ButtTighten | 70 |

Read: the V-taper is TorsoWaistSize 85 against SterWidth 95 / ShoulderInc
90 — under the resolved "Shrink Waist" semantics [S], 85 is the strong
shrink, and this *is* the narrowest waist either orc preset carries (the
original 15 was the widest — see the revision note above §3.1). It is also
the *only* structural difference from Strongman besides tissue: same traps
ceiling, same leg mass, definition sliders (Valleys 85, BackDefinition 95,
VLine 85) doing the "cut" work that TorsoMassSmooth 65 does in reverse for
Strongman.

*Semantics flag — CLOSED Nov 12, 2026: the earlier assumption (big end
widens) was wrong. The decoded display name is "Shrink Waist"
(`presets-titan-batch1.md`, [S]); corrections applied in §3.1/§3.2 per
`BARA_LESSONS.md` §6 B/C. Do not re-open without new decode evidence.*

---

## 4. TEETH — the universal arcade, orc at its extreme (per Joe's ruling)

### 4.0 The system (shared, not orc-specific)

- **One arcade pair.** Upper arcade is part of the skull/head object; lower
  arcade is part of the **jaw object** and rides it through open/close and
  through every jaw slider (its verts carry the jaw region's weights).
- **Diet is morphs, not meshes.** Three morph axes on the shared arcade
  (0–100 each) + one wear axis:

| Morph axis | What it deforms |
|---|---|
| `TeethCanine` | Canine crown length/point (upper + lower, lower weighted stronger) |
| `TeethMolar` | Molar/premolar crown breadth and flatness (grinding surface) |
| `TeethIncisor` | Incisor width/protrusion (cropping front) |
| `TeethWear` | Crown height loss + edge rounding, all teeth |

- **Diet presets on those axes** [E]:

| Diet | Canine | Molar | Incisor | Wear | Reads as |
|---|---|---|---|---|---|
| Carnivore | 85 | 30 | 40 | 20 | Feline/canid plan |
| Omnivore | 45 | 55 | 50 | 25 | Human plan |
| Herbivore | 5 | 95 | 70 | 45 | Flat mill + cropping front |

### 4.1 Orc on that system — the tusk is a value, not a rig

- Orc diet base = **omnivore**, with `TeethCanine` pushed and its
  **lower-canine component** driven to the axis extreme. The tusk *is* the
  mandibular canine: it emerges from the **mandibular canine socket** of the
  lower arcade, inherits the jaw object's transform and deformations, and
  needs no mesh, bone or socket of its own.
- **Tusk size = `TeethCanine` lower-canine value:**

| Setting | TeethCanine (lower) | Exposed tusk crown | Tag |
|---|---|---|---|
| Subtle | 60 | ≈0.05 L | [E] |
| **Standard orc (ship default)** | **80** | **≈0.08 L** | [E] |
| Full tusk | 100 | ≈0.11 L | [E] |

  (Upper canines at the same preset: `TeethCanine` 55 — present, hooked,
  clearly secondary [E]. The gorilla plan agrees: lower canine closes into
  an upper **diastema** [S-qual. §1.1] — the arcade morph must open a
  matching gap between upper lateral incisor and upper canine at
  TeethCanine-lower ≥ 70, or the jaw won't close. Builder: this clearance is
  a hard constraint, check it like the v2 head's teeth/tongue clearances.)
- **Emergence angle is a function of jaw width, not a free parameter.**
  Tusks angle outward as the mandible widens (the socket itself rotates with
  the jaw's bi-angular flare):

  `outward tilt from vertical ≈ 5° + 0.25° × JawWidth slider` [E]

  → at the orc JawWidth +70: **≈22° outward**, plus a fixed **forward rake
  of 10°** [E]. Narrower-jawed characters on the same system get straighter
  tusks automatically. Implement as rotation of the lower-canine verts
  about the socket point, coupled to the JawWidth deformation — a morph
  coupling inside the arcade system, still not a separate rig.
- **Lip clearance.** At jaw-closed, tusk tips must clear the upper lip and
  the `nose_orc` nose line: with JawDepth +65 / MuzzleDepth +60 / standard
  tusk 0.08 L, tips land just outside the upper-lip line (the canon read —
  tusks visible against the upper lip, §1.3). At Full tusk (0.11 L) the
  upper lip needs the lip-parting morph (orbicularis thickening, §2.3) —
  flag for the first build's fit check; if it clips, cap shipping default
  at 0.09 L rather than shrinking the jaw.
- **Broken tusk — `TeethDamage` morph (0–100), one side only.** Crown
  truncated at 35–55% of full length with a jagged fracture cap and a
  darker exposed-dentine core (material zone, §5). Side is a variant flag
  (`damage_L` / `damage_R`), never both by default — symmetric damage reads
  as a style, asymmetric reads as a *history*. Same morph serves chipped
  fangs for the carnivore diet presets; orc just uses it hardest.

---

## 5. MATERIALS / LOOK

### 5.1 Skin

Art-directed ranges [E], anchored to canon palettes (§1.3). One skin
material, hue picked per character; roughness 0.55–0.70, skin-pore normal
from the humanoid skin set, SSS tint one step warmer than base.

| Palette | Base hex | Range | Canon source |
|---|---|---|---|
| Classic green | #6B8E3D | #55702E – #84A856 | Warcraft orc |
| Olive | #7A7D3A | #62642C – #94975A | Warhammer ork (darker, yellow-shifted) |
| Moss / deep green | #4C6633 | #3D5229 – #5F7A42 | Film orc (Weta) |
| Grey | #6F7268 | #595B54 – #8B8E84 | Blackrock-type |
| Brown | #8A5A3B | #6E452B – #A9714B | Unfel / Mag'har-type |
| Fel red | #93392B | #752C21 – #B0503C | Fel-touched variant — flag as *variant*, not a default |

### 5.2 Surface layers (material stack, never geometry)

| Layer | Content | Controls |
|---|---|---|
| Scars | 6 placement decals (brow, cheek, jaw, chest, shoulder, back) [E], raised-edge normal + lighter diffuse | per-scar on/off, opacity 0–100 |
| Warpaint / tattoos | Tribal bands (arm, chest), clan-mark face paint, jaw stripe | layer colour independent of skin, opacity 0–100; face paint must respect the brow-torus line |
| Grime/wear | Dirt in creases, tooth-adjacent gum darkening | global 0–50, default 20 [E] |

### 5.3 Hair — part variants on the head

| Variant | Notes |
|---|---|
| `hair_bald` | Default for crest-strip orcs (§2.4) |
| `hair_topknot` | Single knot at the crest line; pairs with `crest_sagittal` |
| `hair_mohawk` | Centre strip, sides shaved to skin |
| `hair_topknot_sideshave` | Topknot + shaved sides (the modern canon default) |
| `hair_mane` | Long back fall from the occiput, no top tie — elder/shaman read |

Colours [E]: black #1A1512 (default), dark brown #2E1D12, blood red #6E1F16,
ash white #CFCFC8 (elder). Beards: **none** — orc canon is clean-jawed (the
jaw is the silhouette; a beard would hide JawDepth +65). Chin-strap scruff
is a texture layer if ever wanted, not a hair part.

### 5.4 Eyes

Iris palette [E]: amber #C78A2D (default), red #A8232A, brown #4A2C17,
gold #D9A62E. Round pupil (the felid slit-pupil variant in the species spec
does not apply). Deep-set placement is already in the head sliders
(EyeSize −40 under BrowShelf +90); do not compensate with larger eyeballs.

---

## 6. Honesty box — weakest numbers in this spec

1. **Every orc head anchor ratio (§2.1) is [E].** No orc has ever been
   measured; the values are art-directed against gorilla anatomy [S-qual.]
   and canon art. JawDepth 0.36 L and BrowRidge 0.75 are the two most
   load-bearing and the least sourced — if the first build reads wrong,
   these are the dials to re-derive from renders, in that order.
2. **Masseter 24–30 mm [E]** is an extrapolation (1.6–2×) from a sourced
   human hypertrophy case [S]; plausible for the fiction, unverifiable.
3. **Tusk crown lengths (0.05/0.08/0.11 L) and the angle formula
   (5° + 0.25° × JawWidth) are [E]** — invented couplings, chosen so the
   *system* behaves sensibly across species; validate visually at first
   build and re-fit the constants, don't defend them.
4. **TorsoWaistSize direction — RESOLVED Nov 12, 2026.** No longer an
   assumption: the decoded display name is "Shrink Waist" [S,
   `presets-titan-batch1.md`], so the big end narrows. Values corrected
   (BB 15 → 85, SM 45 → 25, SM TorsoHip 40 → 20) per `BARA_LESSONS.md`
   §6 B/C; see the revision note above §3.1.
5. **Heights/scales (§3.0) are [E]** — HIMBO's base height is itself
   inferred from its z-span, not documented.
6. What is *not* weak: the HIMBO slider statistics and preset calibration
   points (§1.4) are measured from the decoded data on disk [S/D], and the
   head-slider arithmetic is exact given the ratios — the uncertainty is
   entirely in the orc target ratios, where it is labelled.

*End of spec. Companions: `species-head-spec.md` (the 25-slider framework
and neutral base), `~/workspace/character_assets/learned/` (HIMBO + Fat
Males learned data). Teeth geometry itself comes from the parallel
teeth-library hunt — this spec only fixes the categories it must fill:
one universal arcade (upper + jaw-riding lower), diet morphs, lower-canine
tusk extreme, broken variant.*
