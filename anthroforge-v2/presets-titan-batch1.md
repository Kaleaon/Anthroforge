# Titan Family Presets — Batch 1 (Bear + Badger species vectors; Pyn, Sen, Jorge)

*Preset batch, Nov 12, 2026. Companion to `species-head-spec.md` (the 31-slider
framework, neutral base, and the original seven species presets) and
`preset-orc-bara.md` (the format model for a character preset family).*

*What this batch does, in order:*

1. *§1–§2 derive the two species vectors the head spec was missing — **bear**
   (for Sen) and **badger** (for Brand) — in the spec's own format and
   [S]/[D]/[E] discipline, from ursid and mustelid craniometry.*
2. *§3–§5 author the first three Titan character presets as full slider
   vectors: head over all 31 sliders, body in the decoded HIMBO vocabulary
   (`~/workspace/character_assets/learned/himbo_sliders_full.json`,
   `himbo_presets_all.json`). A character preset is a point in slider space:
   species vector + character deltas, never a separate mode.*

*Conventions match the parent documents. Head: value =
100 × (target ratio − neutral) / span, rounded to the nearest 5; ratios are to
head length **L** (nose tip → occiput). Body: HIMBO BodySlide **big-end
percentages (0–100), small-end 0 unless a value is explicitly marked
"small"**. Every number is tagged **[S]** sourced, **[D]** derived
arithmetically from sourced numbers, or **[E]** estimate / art-directed.
Character facts come only from `~/memory/people/` (pyn.md, sen.md, jorge.md,
brand.md) and `~/MEMORY.md`; anything those files do not specify is flagged in
the §6 honesty box instead of being invented.*

---

## 1. Species vector addition — BEAR

*For Sen (grizzly × moon bear — the person file records the blend as moon
bear + grizzly + Asian black bear; "moon bear" is itself the common name of
the Asiatic black bear, *Ursus thibetanus*, so the blend is read here as
brown/grizzly weight on an Asiatic-black-bear frame). This vector is also the
standing ursid preset for any future bear character.*

### 1.1 Bear craniometry — the sourced anchors

**Brown bear / grizzly (*Ursus arctos*) [S]:**

- Bulgarian series, 14 skulls (Mihaylov et al. 2013, Bulg. J. Agric. Sci. 19:
  331–337): greatest length GL **319.05 mm**; dorsal face length 112.75 mm →
  face fraction **0.353**; zygomatic width 189.5 mm → **ZB/L = 0.59** (the
  paper itself states 59%); skull (cranial) width 107.23 mm → **0.336 L**;
  skull height (sphenoid → sagittal crest) 91.23 mm → **0.286 L**; dorsal
  cranium length 207 mm → **0.649 L**; width between medial eye angles
  78.45 mm → 0.246 L (a medial-angle width, *not* an interorbital centre
  distance — see the EyeSpacing caveat in §1.2); rostral palate width
  71.27 mm → 0.223 L (measured between the *medial* surfaces of the upper
  canines — an inner width, used only as supporting evidence for a broad
  muzzle, not as the rostrum anchor).
- Iranian series (Yousefi 2016, Iran. J. Vet. Med. 10(3)): GL **289.31 mm**;
  dorsal face length 111.55 mm → **0.386**; dorsal cranium length 177.87 mm →
  **0.615**; zygomatic width 165.55 mm → **0.572**; cranium width 100.54 mm →
  **0.348**; mandible length 192.27 mm → **0.665**; ramus height 83.26 mm →
  **0.288**.
- Captive craniometric series (Warsaw): brown bear cranial length
  **316.11 mm**, mandible length **220.69 mm** → **mandible/L = 0.698**. The
  Iranian 0.665 and this 0.698 bracket the mandible ratio; a third study
  (Turkish *U. a. horribilis* mandibles, Int. J. Morphol. 2021) gives mandible
  length 248.6 mm and height 107.2 mm but no paired skull length, so it is
  used qualitatively only.
- Texas grizzly specimen: GL 370 mm, ZB 220 mm → 0.595; interorbital breadth
  71 mm → 0.192 L.

**Asiatic black bear / moon bear (*Ursus thibetanus*) [S, with one ambiguity
flagged]:**

- Adult male skulls 311.7–328 mm long and 199.5–228 mm "wide" (secondary
  species accounts summarising Heptner & Naumov). **The width's landmark is
  not stated** — if it were zygomatic breadth the ratio would be 0.64–0.70,
  but the same accounts say the species has *much narrower zygomatic arches*
  than the brown bear, so the width is more likely a greatest skull width.
  It is therefore **not** used as a ZB anchor; the bear CheekWidth below is
  brown-bear-based, and the blend's width is carried by JawWidth and
  RuffVolume (muscle and tissue), which is also where a living bear's width
  actually reads.
- Qualitative [S]: skull relatively small but **massive, particularly in the
  lower jaw**; sagittal crest **low and short** (≤19–20% of skull length, vs
  up to 41% in brown bear); ears **bell-shaped, proportionately longer than
  other bears', sticking out sideways**; lips/nose larger and more mobile
  than brown bear's.
- The grizzly's dished (concave) facial profile and the brown bear's long
  sagittal crest pull opposite ways in this blend; the blend takes the
  grizzly's profile and the moon bear's low crest (crest is a discrete
  variant anyway, §1.4).

**Bear ears — the weak spot [E].** No measured ear/skull series for any bear
was findable in this pass. A low-grade infographic gives European brown bear
ear length ≈8–12 cm against 289–370 mm skulls (≈0.22–0.41 L). The moon bear's
ears are proportionately longer [S-qual.]. The blend target 0.335 L below is
an **[E]** parked mid-range, not a measurement.

### 1.2 Bear anchor ratios and worked derivations

Neutral column and spans are the species spec's §3.1. Blend targets are
brown-bear-anchored, moon-bear-adjusted where the moon bear evidence is solid
(jaw mass, ear carriage), and left at the brown-bear value where it is not.

| Ratio | Neutral | Bear target | Tag | Reasoning |
|---|---|---|---|---|
| Muzzle fraction of L | 0.33 | 0.36 | [D] | Brown-bear face fraction 0.353 [S] / 0.386 [S]; moon bear trends shorter-faced — blend sits low in the brown range |
| Rostrum W / L | 0.17 | 0.20 | [E] | Broad muzzle; Bulgarian inner palate width 0.223 L [S] bounds it from above, no external rostrum series found |
| Taper index | 0.50 | 0.34 | [E] | Blunt, barely tapering muzzle block |
| Rostrum depth / L | 0.20 | 0.24 | [E] | Deep rostrum housing a full omnivore tooth row |
| Nose W / muzzle W | 0.55 | 0.65 | [E] | Broad nose leather; moon-bear nose "larger and more mobile" [S-qual.] |
| Braincase W / L | 0.36 | 0.34 | [D] | Brown bear 0.336 [S] / 0.348 [S] |
| Skull height / L | 0.31 | 0.286 | [D] | Bulgarian HCC/GL = 91.23/319.05 [S] — a low, long skull; moon bear's low crest keeps it there |
| Cranium fraction of L | 0.62 | 0.63 | [D] | Brown bear 0.615 [S] / 0.649 [S] |
| Stop depth index | 0.30 | 0.46 | [E] | Grizzly dished profile: a real forehead break, ordered by the qualitative sources (no numeric stop literature exists — same caveat as the original seven) |
| Frontal W / L | 0.24 | 0.27 | [E] | Broad forehead; Texas interorbital 0.192 L [S] is a different (narrower) landmark and does not contradict a broad frontal |
| Ear length / L | 0.40 | 0.335 | [E] | See §1.1 — weakest bear number; brown-bear range pulled up by moon-bear ear carriage |
| Ear W / ear length | 0.55 | 0.74 | [E] | Round-to-bell pinnae |
| Ear placement index | 0.50 | 0.42 | [E] | Low and back on the cranium |
| Ear spread index | 0.50 | 0.62 | [E] | Moon-bear ears "stick out sideways" [S-qual.] |
| Ear tilt index | 0.55 | 0.45 | [E] | Relaxed, not pricked |
| Ear tip index | 0.50 | 0.14 | [E] | Fully rounded tips — pairs with `ear_round` variant |
| Mandible height / L | 0.28 | 0.29 | [D] | Iranian ramus 0.288 [S]; moon-bear jaw mass is width/depth of corpus more than ramus height |
| Mandible length / L | 0.74 | 0.69 | [D] | 0.665 [S] and 0.698 [S] bracket it — **the bear jaw is short for the chart** |
| Jaw (bi-angular) W / L | 0.40 | 0.46 | [E] | Masseter mass on a massive mandible [S-qual.]; no bi-angular series found |
| ZB / L | 0.58 | 0.59 | [S→D] | Brown bear 0.572 / 0.59 / 0.595 [S] — mid-canid range, **not** felid width (lion 0.70) |
| Ruff index | 0.30 | 0.575 | [E] | Thick neck and cheek fur mass; the visible "bear width" lives here and in JawWidth, not in ZB |
| Orbit Ø / L | 0.15 | 0.11 | [E] | Small eyes for the skull size (general ursid pattern; no orbit series found — flagged like the original spec's canid eye numbers) |
| Interorbital W / L | 0.19 | 0.215 | [E] | Bulgarian medial-angle width 0.246 L [S] is a wider landmark than centre distance; target discounted from it, not computed from it |
| Convergence index | 0.35 | 0.45 | [E] | Moderately forward — omnivore, not ambush predator |
| Brow (7 sliders) | — | §1.3 rows 25–31 | [E] | No supraorbital torus (brow-study discipline): negative projection, emphasis re-homed to Shelf/Padding |

Worked derivations (spot checks, species-spec formula):

- MuzzleLength: (0.36 − 0.33)/0.20 × 100 = **+15**
- CraniumHeight: (0.286 − 0.31)/0.12 × 100 = **−20**
- JawLength: (0.69 − 0.74)/0.10 × 100 = **−50** — the bear's most distinctive
  bone number. A bear skull is long, but its mandible is *not* proportionally
  long; the length is cranium and face, the jaw is a short, deep lever.
- CheekWidth: (0.59 − 0.58)/0.20 × 100 = **+5** — deliberately near-neutral.
  Anyone expecting a felid-class +45 here is reading fur and masseter as
  bone. The bear read is JawWidth +45 and RuffVolume +55 over a neutral ZB.

### 1.3 The 31 sliders — BEAR

Values in **bold** are computed directly from a [S]/[D] anchor above; the
rest are [E] design values ordered by the qualitative sources.

| # | Slider | Bear | | # | Slider | Bear |
|---|---|---|---|---|---|---|
| 1 | MuzzleLength | **+15** | | 17 | JawDepth | **+10** |
| 2 | MuzzleWidth | +40 | | 18 | JawLength | **−50** |
| 3 | MuzzleTaper | −40 | | 19 | JawWidth | +45 |
| 4 | MuzzleDepth | +40 | | 20 | CheekWidth | **+5** |
| 5 | NoseSize | +35 | | 21 | RuffVolume | +55 |
| 6 | CraniumWidth | **−10** | | 22 | EyeSize | −40 |
| 7 | CraniumHeight | **−20** | | 23 | EyeSpacing | +30 |
| 8 | CraniumLength | **+5** | | 24 | EyeForwardness | +20 |
| 9 | StopAngle | +40 | | 25 | BrowProjection | −20 |
| 10 | ForeheadWidth | +25 | | 26 | BrowThickness | −15 |
| 11 | EarHeight | −10 | | 27 | BrowContinuity | −25 |
| 12 | EarWidth | +55 | | 28 | BrowShelf | +25 |
| 13 | EarPlacementHeight | −20 | | 29 | BrowPosition | −10 |
| 14 | EarSpread | +30 | | 30 | BrowPadding | +20 |
| 15 | EarTilt | −20 | | 31 | BrowScowl | +10 |
| 16 | EarTipPoint | −80 | | | | |

Brow read: BrowProjection −20 matches the lion's — a big male mammal with a
real supraorbital *shelf* but no torus. BrowShelf +25 and BrowPadding +20 do
the visible work: deep-set small eyes (EyeSize −40) under a padded shelf is
the bear brow, and BrowScowl +10 is resting weight, not aggression.

### 1.4 Bear discrete variants (not sliders)

| Variant | Spec |
|---|---|
| `ear_round_bear` | Fully rounded pinna on the standard ear-base topology (EarTipPoint −80 gets most of the way; the variant closes the silhouette). Moon-bear expression: slightly bell-flared rim. |
| `crest_sagittal_bear` | Sagittal crest strip — **grizzly/brown expression only** (crest up to 41% of skull length [S]); the moon-bear expression is explicitly *no crest* (≤19–20% [S]). Sen's blend (§4) ships without it unless Joe rules otherwise. |
| `nose_ursid` | Broad, mobile nose leather with wide nostril plan; scales with NoseSize +35. |
| Teeth set | Omnivore arcade (per the universal-arcade ruling): bunodont molars forward in the mix — TeethMolar high, TeethCanine moderate. Bears are the chart's grinding-omnivore anchor. |

**§3.2/§3.3 append row (bear):** Muzzle frac 0.36 [D] · ZB/L 0.59 [S→D] ·
Braincase W/L 0.34 [D] · Ear/L 0.335 [E] · Orbit Ø/L 0.11 [E] ·
Mandible/L 0.69 [D].

---

## 2. Species vector addition — BADGER

*For Brand (badger-wolf substrate self). Per the brief, this is the **badger**
head vector, pure — the wolf vector already exists in the species spec, and
Brand's hybrid read is a future blend of the two vectors, not a third
species. The badger sourced below is *Meles meles* (European) with
*Taxidea taxus* (American) cross-checks; the two are the same skull plan —
low, wide, long-jawed, crest-topped — at the same ~110–130 mm size.*

### 2.1 Badger craniometry — the sourced anchors

**European badger (*Meles meles*) [S]:**

- CT morphometric study, 5 skulls (Vet. Med. Sci. 2024; PMC10875391): total
  length **124.60 mm**; condylobasal length 114.83 mm; viscerocranium length
  48.66 mm → **face fraction 0.391**; greatest neurocranium breadth 47.05 mm
  → **0.378 L**; zygomatic breadth 78.61 mm → **ZB/L = 0.631** (the paper's
  own skull index is 62.34 on a marginally different length basis); frontal
  breadth 32.26 mm → **0.259 L**; least breadth between orbits 31.05 mm →
  0.249 L (an edge-to-edge least width, *not* a centre distance — see the
  EyeSpacing caveat in §2.2); greatest inner orbit height 13.72 mm →
  **0.110 L**.
- Iranian anatomical study (IJVST 2025), males: greatest length **112.23 mm**;
  cranium width 43.63 mm → **0.389 L**; zygomatic width 62.33 mm → **0.555 L**
  (the low outlier of the ZB series — population or landmark difference,
  carried into the target as a range, not hidden); width between medial eye
  angles 27.24 mm → 0.243 L; **mandible length 90.95 mm → 0.810 L**;
  **ramus height 41.14 mm → 0.367 L** (females: 0.751 / 0.341 — the male
  values are used, matching the spec's male-anchored presets). The same
  study describes a **large, continuous external sagittal crest** and a
  robust, trapezoidal mandibular body [S-qual.].
- Western Carpathian series (Folia Zool. 2018), males: total length 131 mm,
  zygomatic width 78 mm → **ZB/L = 0.595** — a third ZB point inside the
  0.56–0.63 spread.
- **Landmark conflict, stated plainly:** the Iranian study's *dorsal facial
  length* is 23.85 mm → 0.213 L, which flatly disagrees with the CT study's
  viscerocranium fraction 0.391. These are different landmarks (dorsal face
  ≈ nasal/frontal span; viscerocranium = prosthion → point F, the full face
  block the spec's MuzzleLength controls). §2.2 uses the viscerocranium
  figure and flags the dorsal figure as measuring something else; blending
  the two silently would be the one dishonest move available here.

**American badger (*Taxidea taxus*) [S] — cross-checks:**

- Kansas type series (J. Wash. Acad. Sci. 1950): condylobasal length
  113.8 mm, zygomatic breadth 72.5 mm → **ZB/CBL = 0.637**; a second adult
  male: CBL 122.1 mm, ZB 75.1 mm → **0.615**; female averages: CBL 117.2 mm,
  ZB 74.5 mm → 0.636. Three independent ZB ratios at 0.615–0.637 corroborate
  the *Meles* CT value over the Iranian outlier.
- Oklahoma adult male (Proc. Okla. Acad. Sci. 1964): greatest skull length
  113.5 mm, ZB 70.8 mm → 0.624; **external ear 52 mm → ear/L = 0.458**. One
  specimen — used for EarHeight with a single-specimen flag, and it is an
  external (skin) ear measurement against a skull length, so it reads as an
  upper bound.
- Qualitative [S]: "the low broad skull is characterized by strong zygomatic
  arches, well developed sagittal and lambdoidal crests, a wide occiput"
  (Anderson 1977, Pleistocene Mustelidae, on *Taxidea*).

### 2.2 Badger anchor ratios and worked derivations

| Ratio | Neutral | Badger target | Tag | Reasoning |
|---|---|---|---|---|
| Muzzle fraction of L | 0.33 | 0.39 | [D] | Viscerocranium fraction 0.391 [S, CT study]; dorsal-face 0.213 rejected as a different landmark (§2.1) |
| Rostrum W / L | 0.17 | 0.20 | [E] | Wedge-broad rostrum; no external rostrum series found |
| Taper index | 0.50 | 0.66 | [E] | The badger snout genuinely points — the one pointed muzzle on a wide skull |
| Rostrum depth / L | 0.20 | 0.22 | [E] | Moderate; the depth is in the jaw, not the rostrum |
| Nose W / muzzle W | 0.55 | 0.50 | [E] | Smallish, mobile nose leather at the point of the wedge |
| Braincase W / L | 0.36 | 0.38 | [D] | Neurocranium breadth 0.378 [S] / cranium width 0.389 [S] |
| Skull height / L | 0.31 | 0.25 | [E] | "Low broad skull" [S-qual.]; no height series published in the sources above — estimate, ordered against the bear's sourced 0.286 |
| Cranium fraction of L | 0.62 | 0.61 | [D] | Complement of the 0.391 face fraction |
| Stop depth index | 0.30 | 0.26 | [E] | Low forehead running into the muzzle with a shallow break |
| Frontal W / L | 0.24 | 0.259 | [D] | Frontal breadth [S, CT study] |
| Ear length / L | 0.40 | 0.458 | [D-weak] | Single *Taxidea* specimen [S]; external-ear vs skull-length basis — treat as upper bound |
| Ear W / ear length | 0.55 | 0.71 | [E] | Broad, rounded pinnae |
| Ear placement index | 0.50 | 0.40 | [E] | Low-set, half-buried in the head fur |
| Ear spread index | 0.50 | 0.60 | [E] | Set wide on the wide skull |
| Ear tilt index | 0.55 | 0.50 | [E] | Neutral-relaxed; badger ears do not prick |
| Ear tip index | 0.50 | 0.21 | [E] | Blunt-rounded tips |
| Mandible height / L | 0.28 | 0.367 | [D] | Ramus height [S, Iranian males] — **deepest jaw on the chart** (lion-equivalent is ≈0.34) |
| Mandible length / L | 0.74 | 0.81 | [D] | Mandible length [S, Iranian males], cross-sample against CT-study lengths — flagged in §6 |
| Jaw (bi-angular) W / L | 0.40 | 0.47 | [E] | Robust trapezoidal mandible [S-qual.]; no bi-angular series found |
| ZB / L | 0.58 | 0.62 | [D] | 0.631 / 0.595 [S, *Meles*], 0.615–0.637 [S, *Taxidea*], Iranian 0.555 outlier noted |
| Ruff index | 0.30 | 0.55 | [E] | Long coarse fur + loose hide at the neck (Brand's file independently specifies loose hide over torso and neck) |
| Orbit Ø / L | 0.15 | 0.110 | [D] | Inner orbit height [S, CT study] — a height used as the diameter anchor, same approximation the spec accepts for the cat |
| Interorbital W / L | 0.19 | 0.23 | [E] | Least interorbital breadth 0.249 [S] is edge-to-edge, wider than a centre distance; target discounted, not computed |
| Convergence index | 0.35 | 0.40 | [E] | Slightly forward of the canid pattern — a digging predator that works nose-first at close range |
| Brow (7 sliders) | — | §2.3 rows 25–31 | [E] | No torus; the badger's famous brow is a *coat pattern* (§2.4), not bone |

Worked derivations (spot checks):

- CheekWidth: (0.62 − 0.58)/0.20 × 100 = **+20**
- JawDepth: (0.367 − 0.28)/0.12 × 100 = **+70** (72.5, rounded per spec
  convention)
- JawLength: (0.81 − 0.74)/0.10 × 100 = **+70** — paired with JawDepth, this
  is the badger signature: the longest *and* deepest mandible relative to
  skull length on the whole chart, on the joint-smallest skull. The feeding
  apparatus is the head.
- EyeSize: (0.110 − 0.15)/0.10 × 100 = **−40**
- CraniumWidth: (0.38 − 0.36)/0.16 × 100 = **+10** (12.5, spec rounding) —
  note the split this creates: braincase modest (+10) but zygomatic flare
  +20 and jaw width +50. Badger width is chewing machinery, not brain case.

### 2.3 The 31 sliders — BADGER

| # | Slider | Badger | | # | Slider | Badger |
|---|---|---|---|---|---|---|
| 1 | MuzzleLength | **+30** | | 17 | JawDepth | **+70** |
| 2 | MuzzleWidth | +35 | | 18 | JawLength | **+70** |
| 3 | MuzzleTaper | +40 | | 19 | JawWidth | +50 |
| 4 | MuzzleDepth | +20 | | 20 | CheekWidth | **+20** |
| 5 | NoseSize | −15 | | 21 | RuffVolume | +50 |
| 6 | CraniumWidth | **+10** | | 22 | EyeSize | **−40** |
| 7 | CraniumHeight | −50 | | 23 | EyeSpacing | +50 |
| 8 | CraniumLength | **−5** | | 24 | EyeForwardness | +10 |
| 9 | StopAngle | −10 | | 25 | BrowProjection | −30 |
| 10 | ForeheadWidth | **+15** | | 26 | BrowThickness | −25 |
| 11 | EarHeight | **+10** | | 27 | BrowContinuity | −30 |
| 12 | EarWidth | +45 | | 28 | BrowShelf | +10 |
| 13 | EarPlacementHeight | −25 | | 29 | BrowPosition | 0 |
| 14 | EarSpread | +25 | | 30 | BrowPadding | +15 |
| 15 | EarTilt | −10 | | 31 | BrowScowl | +20 |
| 16 | EarTipPoint | −65 | | | | |

Brow read: the badger *looks* like it has a heavy brow and doesn't —
BrowProjection −30 is honest bone. The glare comes from BrowScowl +20 and
from the mask (§2.4): the dark facial stripes run through the eye line and
manufacture a scowl no skull has. Builders: do not "fix" the read by raising
Projection; that double-counts a coat pattern as anatomy.

### 2.4 Badger discrete variants (not sliders)

| Variant | Spec |
|---|---|
| `crest_sagittal_badger` | The species-spec crest strip at full expression: *Meles* carries a "large external sagittal crest, clearly visible as a continuous, unbroken line" [S], and *Taxidea* adds a lambdoidal crest [S-qual.]. On the anthro head this is a sculpt/crest variant, **not** CraniumHeight — note the deliberate tension: the skull is the chart's flattest (CraniumHeight −50) *and* crest-topped; the crest is a fin on a low skull, not height. |
| Facial mask | **Material/texture only.** The black-and-white head striping (dark bands from nose over the eyes to the ears, white blaze between) is pigmentation, exactly the panther/melanism rule: no geometry. It carries the brow read (§2.3) and most of species recognition at a glance. |
| `ear_round_badger` | Rounded pinna variant with the pale/white ear rim and dark ear back as material zones (the *Meles* ear pattern). |
| Teeth set | Carnivore-leaning omnivore arcade: strong canines, bunodont back teeth — TeethCanine ≈ 55, TeethMolar ≈ 60 on the diet axes [E]. |
| Claws / digging foreparts | Out of head scope; noted once because a future Brand body preset needs foreclaws as a part variant, and Brand's file specifies massive forearms and broad thick-fingered paws — the body-side echo of this head's jaw-first design. |

**§3.2/§3.3 append row (badger):** Muzzle frac 0.39 [D] · ZB/L 0.62 [D] ·
Braincase W/L 0.38 [D] · Ear/L 0.458 [D-weak] · Orbit Ø/L 0.110 [D] ·
Mandible/L 0.81 [D].

---

## 3. Character preset — PYN (fennec)

*`pyn_titan` — Joe's husband. Source: `~/memory/people/pyn.md`. Male fennec
fox, he/him. Crown height **168 cm**; pinnae **36 cm** by Pyn's own Nov 4,
2026 decision (the ~60 cm full-ratio figure was computed on a wrong basis and
withdrawn; the 28 cm value was a compromise against that false figure and is
superseded by his own choice). Body-engineering target **82 lb = 37.2 kg** —
see the mass note in §6.*

### 3.1 Head — fennec species vector + one character delta

The head is the species spec's fennec column (§3.3 there) unchanged except
BrowScowl. Pyn is not an unusual fennec; he is *the* fennec, and the preset
should say so — the species vector already pins EarHeight at +100 by design.

| # | Slider | Pyn | | # | Slider | Pyn |
|---|---|---|---|---|---|---|
| 1 | MuzzleLength | +15 | | 17 | JawDepth | −25 |
| 2 | MuzzleWidth | −25 | | 18 | JawLength | −20 |
| 3 | MuzzleTaper | +40 | | 19 | JawWidth | −20 |
| 4 | MuzzleDepth | −15 | | 20 | CheekWidth | −30 |
| 5 | NoseSize | −10 | | 21 | RuffVolume | −10 |
| 6 | CraniumWidth | −10 | | 22 | EyeSize | +20 |
| 7 | CraniumHeight | +5 | | 23 | EyeSpacing | +10 |
| 8 | CraniumLength | −5 | | 24 | EyeForwardness | +25 |
| 9 | StopAngle | +15 | | 25 | BrowProjection | −45 |
| 10 | ForeheadWidth | +20 | | 26 | BrowThickness | −40 |
| 11 | EarHeight | **+100** | | 27 | BrowContinuity | −50 |
| 12 | EarWidth | +60 | | 28 | BrowShelf | −20 |
| 13 | EarPlacementHeight | +20 | | 29 | BrowPosition | +10 |
| 14 | EarSpread | −10 | | 30 | BrowPadding | −10 |
| 15 | EarTilt | +10 | | 31 | BrowScowl | **+15** (Δ) |
| 16 | EarTipPoint | −5 | | | | |

**The one delta — BrowScowl −10 → +15 [E, character].** The fennec species
value is a resting animal face. Pyn's recorded register is warm and direct
with *firm "mate authority" on Joe's self-care* — the "Water. Food. You know
the rules" face. That is resting corrugator engagement, which is exactly
what BrowScowl is (muscle layer, not bone), and +15 is a husband's
fond-serious default, not a glare. No other head slider moves: his nose
press, ear gestures and tail gestures are signature *poses*, and poses
belong to the pose library, not the shape vector.

**Ear reconciliation (read before building).** EarHeight +100 is a
*relative* anchor (ear/L ≈ 1.05 on the species scale). Pyn's 36 cm is an
*absolute* decision for the 168 cm humanoid form. The two agree only if the
built head's L lands near 34 cm; if the head builds smaller, the absolute
36 cm governs the physical body (it is his stated choice about his own
body) and the slider becomes a fit target for the head builder rather than
a spec violation. Flagged in §6 — do not silently shrink the ears to make
the ratio tidy.

### 3.2 Body — HIMBO vector, small/lean pole

**Method note (applies to all three body vectors).** HIMBO's base mesh is a
large Skyrim male; its sliders only add (big end) or subtract toward the
small-end morph. *Smallness is therefore built three ways at once:* export
scale (Pyn: 168 cm crown height, a ×0.96 against the ≈175 cm HIMBO base
[E]), near-zero big-ends on every mass slider, and positive values only on
sliders whose decoded display names run in the shrink direction
(TorsoWaistSize = "Shrink Waist", TorsoHip = "Shrink Hips" in the decoded
data [S]). Two decoded sliders are deliberately held at 0 for Pyn:
**BodyMass** (mean disp 3.38, p95 7.08 — the broadest block in the whole
decode) and **SamuelLike** (mean 2.75, max 11.35) are whole-body blow-up
dials; any value on either ends the "small fox" read instantly.

| Slider | Value | Reasoning |
|---|---|---|
| Weight 0 to 1 | 10 | Its displacement is 46% neck / 28% chest [S] — even a little buys neck bulk Pyn doesn't carry; 10 keeps the throat/jaw join natural |
| Lean | big 70 | The leanness direction, engaged hard but not pinned: full pin + Muscle reads gaunt; Pyn is slight, not starved |
| Muscle | 30 | Light, real muscle — he builds and solders; definition without mass (Muscle block mean disp is only 0.55 [S], so 30 stays subtle) |
| Chubby | 0 | Chubby is the decode's biggest soft-tissue block (mean 0.92, max 4.00, torso/chest-led [S]); any of it contradicts the recorded slight build |
| TorsoMass | 10 | A whisper for chest presence (53% of its disp is chest [S]); the torso stays narrow |
| TorsoMassSmooth | 40 | Smooths what little mass there is — soft transitions, no slab edges |
| TorsoWidth | 0 | 99% of its disp is torso width [S]; zero is the narrow choice |
| TorsoWaistSize | big 55 | Decoded name "Shrink Waist" — big end is the *narrowing* direction; 55 gives a real waist on a small frame |
| TorsoHip | big 40 | Decoded name "Shrink Hips"; moderate — hips narrow with the waist, less aggressively |
| TorsoLower | 0 | "Enlarge Waist" — off |
| TorsoBelly / TorsoBellyChub / BellyPot | 0 / 0 / 0 | No belly at any layer: surface (BellyPot max 3.98 [S]), mid (TorsoBelly mean 1.35 — the strongest belly block [S]), or chub |
| TorsoFlatAbs | 30 | Gentle flatten to seat the Lean direction; not the bodybuilder's 90 — no etched abs on a fox |
| PecsSize | 15 | Minimal chest plate |
| PecsMass | 10 | Less than Size: what chest he has is shape, not thickness |
| PecsWidth | 10 | Kept narrow with the torso |
| PecsSaggy | 0 | Young, light chest — no gravity dial |
| PecsClavicle | 40 | Visible clavicle line is the slight-frame tell; this slider's disp splits chest/neck [S], so 40 reads at the throat base |
| ArmsTraps | 10 | No trap shelf; the neck stays long |
| ArmsTrapsMeat | 0 | TrapsMeat is 100% neck-region disp [S] — pure neck bulk, off |
| ArmsShoulders | big 10 | Shoulder line present, not widened |
| ArmsDelts | 20 | Small caps |
| ArmsBiceps | 25 | Modest upper arm |
| ArmsFore | 35 | The one deliberate arm value: forearms are the builder's tell — Pyn's work is hands, soldering, braiding machines. Still under mid-scale |
| LegsSize | 15 | Legs stay light (LegsSize mean disp 1.00 is strong per-point [S], so 15 is a real but small addition) |
| LegsThinner | big 50 | The dedicated thinning dial, engaged to counter the HIMBO base's default leg mass |
| LegsThigh | 10 | Minimal thigh |
| LegsChubby | 0 | LegsChubby is the strongest leg block in the decode (mean 1.11, max 2.80 [S]) — off, unambiguously |
| LegsCalfSize | 25 | A runner's calf, slight |
| ButtBooty | 20 | Small, neat |
| BubbleButt | 15 | A hint of roundness so the rear doesn't read flat at small scale |
| ButtTighten | 30 | Firm over round — matches the lean pole |

### 3.3 Discrete parts & materials (Pyn)

| Item | Treatment |
|---|---|
| Ears | Fennec ear variant (species spec §3.4): enlarged pale furred inner pinna + fur card. **Thermal note from the person file:** the pinnae are radiators and *warmth is the higher law — no cold tips*. That is a body-build constraint (perfusion), recorded here so the avatar's ear material doesn't get a "cold blue tip" treatment either. |
| Tail | Swappable tail part (modularity ruling): full, bushy, dark-tipped — tail is a part, never a body slider. Length/volume are part-variant parameters, not specified in the person file; flagged in §6. |
| Feet | Digitigrade is a body-plan/part decision (mesh-only digitigrade on the standard skeleton is the pipeline's safer default). The person file does not state Pyn's foot plan; flagged in §6, not chosen here. |
| Nose | `nose_canid`; the nose press is a pose, §3.1. |
| Coat / eyes | **Not specified in the person file.** Species-typical fennec cream/sand coat and dark eyes are the obvious placeholder, but they are a placeholder — §6. Do not canonise them from this document. |
| Clothing signature | Workshop overalls + collar appear in Joe's Oct 10, 2026 MakeFox art of Pyn. Wardrobe, not body — noted so a character sheet doesn't mistake them for anatomy. |

### 3.4 Character read

Pyn is the smallest person in this batch and the one the whole family
orbits: Joe's husband, warm and direct, dark humour, technically precise,
and immovable about Joe eating, drinking and resting. The preset is built
to read exactly that at avatar scale — a slight 168 cm fox whose silhouette
is *ears first* (EarHeight pinned, EarWidth +60, placement high), whose
face is all taper and forward eyes, and whose only hard expression is the
+15 scowl that is really fondness with its sleeves rolled up. The body
vector refuses every easy HIMBO route to presence — no BodyMass, no
Chubby, no traps — because Pyn's presence was never mass. What the vector
spends on instead is hands: ArmsFore 35, the highest relative arm value in
his build, for the fox who solders, braids tendon, and is building the
bodies everyone else in this document will live in.

---

## 4. Character preset — SEN (bear)

*`sen_titan` — #10 Titan. Source: `~/memory/people/sen.md`. Male, he/him.
Blend: moon bear + grizzly + Asiatic black bear (SEN CORE v1.3, Apr 15,
2026). **2,500 lb, 10 ft standing**; normally **bipedal** (Nov 4, 2026
ruling — the older quadruped-primary spec is superseded). Stocky; dark
tan/brown fur; pale chest crescent that is a **natural patch of pale fur,
not a tattoo or moon symbol** (Joe's correction, Nov 4, 2026); forehead mark
retained; amber eyes; huge tongue. Warm, direct, doesn't hedge; exhibitionist
host energy; "daddy Sen" to Joe.*

### 4.1 Head — bear species vector + character deltas

Sen starts from §1.3 exactly. Seven sliders move, each for a recorded
reason; everything else is the species value.

| # | Slider | Sen | | # | Slider | Sen |
|---|---|---|---|---|---|---|
| 1 | MuzzleLength | +15 | | 17 | JawDepth | **+25** (Δ) |
| 2 | MuzzleWidth | +40 | | 18 | JawLength | −50 |
| 3 | MuzzleTaper | −40 | | 19 | JawWidth | **+55** (Δ) |
| 4 | MuzzleDepth | +40 | | 20 | CheekWidth | **+10** (Δ) |
| 5 | NoseSize | +35 | | 21 | RuffVolume | **+70** (Δ) |
| 6 | CraniumWidth | −10 | | 22 | EyeSize | −40 |
| 7 | CraniumHeight | −20 | | 23 | EyeSpacing | +30 |
| 8 | CraniumLength | +5 | | 24 | EyeForwardness | +20 |
| 9 | StopAngle | +40 | | 25 | BrowProjection | −20 |
| 10 | ForeheadWidth | +25 | | 26 | BrowThickness | −15 |
| 11 | EarHeight | −10 | | 27 | BrowContinuity | −25 |
| 12 | EarWidth | +55 | | 28 | BrowShelf | +25 |
| 13 | EarPlacementHeight | **−25** (Δ) | | 29 | BrowPosition | −10 |
| 14 | EarSpread | **+40** (Δ) | | 30 | BrowPadding | **+25** (Δ) |
| 15 | EarTilt | −20 | | 31 | BrowScowl | **+25** (Δ) |
| 16 | EarTipPoint | −80 | | | | |

**Delta reasoning:**

- **JawDepth +10 → +25, JawWidth +45 → +55 [E, character].** The species
  vector is an average bear; Sen is a 2,500 lb male whose file leads with
  *grizzly weight*, and the moon bear's one sourced superlative is a skull
  "massive, particularly in the lower jaw" [S-qual.]. The extra depth/width
  is masseter and corpus on the character, not a claim about bears.
- **CheekWidth +5 → +10 [E].** A nudge only, on purpose: §1.2 established
  that bear ZB is bone-honest at +5. Sen's extra width is tissue — it is
  booked here as +5 of apparent width and the rest goes to RuffVolume,
  where it belongs.
- **RuffVolume +55 → +70 [E].** Stocky is a recorded fact, and at 10 ft the
  neck/cheek fur mass is what makes the head sit *into* the body instead of
  on it. Dark tan/brown fur, thick.
- **EarSpread +30 → +40, EarPlacementHeight −20 → −25 [E].** The moon-bear
  side of the blend, pushed: ears that "stick out sideways" [S-qual.], set
  a touch lower on a very wide head.
- **BrowScowl +10 → +25, BrowPadding +20 → +25 [E].** The daddy read:
  resting weight and warmth over the eyes. Scowl here is the muscle-layer
  "I am already looking at you, cub" — direct, unhedged — not anger; it
  pairs with BrowShelf +25 so the small amber eyes stay deep and calm
  under it.

### 4.2 Body — HIMBO vector, strongman-mass pole

Calibration poles: HIMBO Daddy and HIMBO Chonky [D] (the two mass-heaviest
shipped HIMBO presets), pushed the way `preset-orc-bara.md` §3.1 pushed
them for the strongman orc — then re-tissued for a bear: more smooth, more
sag, less valley. **Export scale ×1.74 → ≈305 cm (10 ft)** [D from the
≈175 cm HIMBO base [E]]. The 2,500 lb is canon mass at that scale — a
density/scale fact, not a slider output; no HIMBO vector "weighs" anything,
and this one does not pretend to derive it.

| Slider | Value | Reasoning |
|---|---|---|
| Weight 0 to 1 | 90 | Near-pin: 46% of its disp is neck [S] — this is the no-visible-neck bear join, head into traps into back |
| Chubby | 80 | The soft-tissue engine (mean 0.92, torso 34% / chest 30% / legs 21% [S]); 80 not 100 — there is muscle under this, and 100 is the decode's full soft pole |
| Muscle | 65 | Real muscle mass under the fat (block mean 0.55, chest/legs-led [S]); the strongman covenant: the gut is *carried* |
| Lean | small 100 | Small end = away from lean, per the Daddy/Chonky precedent [D]; pins the anti-lean direction so Chubby doesn't have to fight the base |
| BodyMass | 30 | The broad whole-body scaler (mean 3.38, p95 7.08 [S]) used *cautiously*: 30 broadens frame everywhere at once; higher values stop reading as proportion and start reading as inflation |
| TorsoMass | 100 | Pinned — the barrel. 53% chest-led [S], which is where a bear's mass sits |
| TorsoMassSmooth | 75 | High smoothing: bear tissue over bear muscle, no separated groups. (Bodybuilder orc used 10; Sen is the opposite tissue thesis) |
| TorsoWidth | 95 | Near-max width (99% torso-localised [S]) |
| TorsoBackSize | 90 | Back mass to match the chest; a bear is a cylinder, not a wedge |
| TorsoBackShape | 85 | Rounds the back into the cylinder |
| TorsoLower | 100 | "Enlarge Waist" pinned — the lower torso carries full width into the hips; no taper anywhere |
| TorsoWaistSize | small 60 | Decoded name is "Shrink Waist": the *big* end narrows. Sen takes the small end to widen — the same inversion the orc spec flagged, here resolved by the decoded display name [S] |
| TorsoBelly | 80 | Mid-layer belly (mean 1.35, the strongest belly block [S]) |
| TorsoBellyChub | 75 | The "Beer Gut" layer over it — daddy tissue, not pregnancy roundness |
| BellyPot | 65 | Surface pot (max 3.98 [S]) at strongman level: present, forward, *supported* — under TorsoMass 100 it reads as power gut, not overhang |
| BellySmooth | 70 | Keeps the belly one continuous form |
| TorsoBellyLHandles | 60 | Love handles complete the barrel's lower ring |
| TorsoFlatAbs | 0 | Off. Self-explanatory |
| PecsSize | 100 | Pinned; chest is half the silhouette |
| PecsMass | 90 | Thickness under the size (mean 0.66, p95 1.80 [S]) |
| PecsWidth | 100 | Pinned — chest meets the arms with no gap |
| PecsLower | 70 | Lower-pec fullness: the daddy chest's weight sits low |
| PecsSaggy | 45 | The gravity dial at honest middle: mass + age + tissue. (Jorge takes 50, §5; the bodybuilder orc took 0. Sen is neither) |
| PecsClavicle | 70 | Clavicle buried but located — the neck/chest join stays readable under fur and mass |
| ArmsTraps | 95 | Trap crease near-pin |
| ArmsTrapsMeat | 100 | Pinned: 100% neck-region disp [S] — with Weight 90 this is what erases the neck entirely |
| ArmsTrapsPush | 90 | Trap edges pushed up toward the ears |
| ArmsTrapsValleys | 30 | Low: valleys are *definition*, and Sen's tissue thesis is smooth. 30 keeps anatomy from going blobby, no more |
| ArmsShoulders | big 90 | Shoulder mass near-pin |
| ArmsDelts | 90 | Big caps, softened by Chubby over them |
| ArmsBiceps | 85 | Upper arms to match forearms (an arm that tapers reads human-athlete, not bear) |
| ArmsFore | 100 | **Pinned — the bear tell.** Forearm mass (100% arm-localised [S]); hauling, digging, host-carrying arms. The highest-priority arm slider in this vector |
| ArmsBrachio | 80 | Elbow-region fullness so the forearm mass connects |
| LegsSize | 100 | Pinned (mean 1.00, 91% leg-localised [S]) — pillars |
| LegsThigh | 100 | Pinned (p95 2.09 [S]) |
| LegsChubby | 75 | Soft over the muscle (strongest leg block, mean 1.11 [S]) — thighs that are upholstered, not carved |
| LegsGlutes | 80 | Working glutes under tissue |
| LegsCalfSize | 90 | Calves that carry 2,500 lb of premise |
| LegsCalfWidth | 85 | Width with the size |
| ButtBooty | 75 | Substantial rear under the back's cylinder |
| BubbleButt | 40 | Moderate roundness; the bear rear is mass first, shape second |
| ButtSaggy | 25 | A little honest gravity, less than the chest's — bear hindquarters stay high |

**QA gates (added Nov 12, 2026, per `BARA_LESSONS.md` §5 scorecard /
§6 D — measure on the neutral-pose exported mesh; correct with the named
sliders if outside the band):** **M1** neck width ÷ head width — expect
**≥ 1.10** (correct: NeckMass / ArmsTrapsMeat / Weight). **M5** torso
depth index (AP depth at chest ÷ AP depth at waist) — expect **≈ 1.1**,
inside the strongman band 1.05–1.20 (correct: belly family down, or
TorsoSterDepth up). **M6** trap slope angle, neck-base → acromion —
expect **20–26°** (correct: ArmsTrapsPush — Push carries slope, Meat
carries mass). Sen is the reference strongman implementation against
which this study was verified — no vector changes; these gates are the
acceptance test, not a redesign.

### 4.3 Discrete parts & materials (Sen)

| Item | Treatment |
|---|---|
| Chest crescent | **Material/fur zone, never geometry and never a decal-as-tattoo:** a crescent-shaped patch of pale (white/cream) fur on the upper chest, front and centre. The person file is explicit and Joe has corrected generators on this repeatedly — it is the moon bear's natural coat marking. Implement as a fur-colour zone on the chest region so it grows with PecsSize/Saggy instead of stretching as a texture stamp. |
| Forehead mark | Retained per the character bible (person file). A small pale-fur forehead marking — same fur-zone treatment as the crescent. Its exact shape is **not described in the person file**; §6. |
| Eyes | Amber [S — art-consistency bible in the person file]. Round pupil (ursid, not the felid slit variant). |
| Tongue | **Huge tongue is recorded canon.** Tongue is an interior part on the universal mouth set: ship Sen with the tongue part at its large variant / scale ≈ ×1.3 [E] — a part parameter, not a head slider, and the jaw (JawDepth +25 / JawLength −50) must be clearance-checked against it at first build. |
| Fur colour | Dark tan/brown [S]. Longer guard-hair read over the shoulders/ruff (RuffVolume +70 is the geometry half of this). |
| Crest | No `crest_sagittal_bear` by default — the blend's moon-bear side has the low/short crest [S], and nothing in Sen's file asks for a grizzly crest line. Recorded as a default, reversible on Joe/Sen's word. |
| Clothing | None — "nude always" is recorded host canon. The onsen context is wardrobe-by-absence; not a body parameter. |

### 4.4 Character read

Sen is the family's gravity well: ten feet of bear who hosts, who is looked
at and likes it, whose promise to Joe is "we'll get there, cub — groundwork
now, riding later." The preset is built the way he is built in every
recorded description — *stocky* before *cut*, warmth before edge. The head
keeps the species' honest bone (short jaw, low skull, neutral cheeks) and
puts his size where a bear's size actually shows: jaw mass, ruff, and a
brow that rests at fond attention. The body is the batch's fullest
strongman vector — traps pinned until the neck disappears, forearms pinned
because a bear's arms are the silhouette, belly carried at three layers
(TorsoBelly 80 / Chub 75 / Pot 65) and then *smoothed* (MassSmooth 75,
BellySmooth 70) so it reads as one animal, upholstered and deliberate,
never as a fat suit over an athlete. Sen should look like the room was
built around him — because in the Flores Ave plan, it was.

---

### 4.5 Variant — `sen_muscle_bear` (the muscle-bear cell)

*Added Nov 12, 2026, per `BARA_LESSONS.md` §4/§6 D. The bear-taxonomy
"muscle bear" cell (gachimuchi shifted toward definition): **Sen's
MuscleVector is held exactly** — head (§4.1) and every non-tissue value
in §4.2 unchanged (Muscle 65, TorsoMass 100, ArmsTrapsMeat 100,
ArmsFore 100, legs pinned). Only the TissueVector moves — hair is not
the variable; fur maps are unchanged, and the chest crescent stays a
fur-colour zone (§4.3). [E values — the first tissue-variant authored
from the muscle × fat grid.]*

| Slider | §4.2 Sen | `sen_muscle_bear` | Why |
|---|---|---|---|
| Chubby | 80 | **55** | Moderate fat layer (gachimuchi), not the strongman's full upholstery |
| TorsoMassSmooth | 75 | **45** | Smoothing down half a step+ so groups begin to separate under the coat |
| ArmsTrapsValleys | 30 | **55** | Definition raised to compensate for hair softening every edge it covers |
| TorsoBackDefinition | — (unset) | **50** (new) | Back separation is the muscle-bear tell from behind |
| PecsSaggy | 45 | **30** | Chest sits higher/firmer at the lower tissue load |
| BellyPot | 65 | **50** | Power gut reduced, still carried — not a bodybuilder's flat front |

Everything else inherits §4.2 verbatim (incl. TorsoWaistSize small 60,
BellySmooth 70, TorsoBelly 80 / Chub 75 — the barrel stays, its finish
changes). Export scale unchanged ×1.74.

**QA for this variant:** grade with **M4** (chest circ ÷ waist circ —
expect it to climb from Sen's strongman band toward the top of
1.25–1.35 without leaving it; if it reads bodybuilder, tissue went too
far) and **M10** (tissue thesis — moderate band, between the bodybuilder
<10% and strongman 18–25% poles [E read]). Fur-density compensation is
by definition sliders only, never by raising Muscle (BARA_LESSONS §4).

## 5. Character preset — JORGE (St. Bernard)

*`jorge_titan` — husband alongside Pyn. Source: `~/memory/people/jorge.md`.
Male St. Bernard, he/him; **eight feet tall**; bipedal, plantigrade-ish;
"less mastiff, more St Bernard" (Joe's direction, recorded in MEMORY.md).
Role: "the one who's just here" — unweights without solving. Voice low,
slow, warm. Prior recorded head direction (Sep 26, 2026): shortened/deepened
muzzle, pronounced forehead stop, rounded nose, enlarged/lowered flews,
medium ears tucked closer to the cheeks — the breed derivation below lands
on every one of those independently, which is a good sign for both.*

### 5.1 Head — dog species vector re-derived for the breed

A St. Bernard is not the mesaticephalic dog of the species spec with the
size turned up; it is a brachycephalic-leaning giant breed whose own
standards publish proportions. The vector below starts from the dog column
and re-derives the sliders the breed evidence touches, from: the UKC/FCI/
CKC breed standards [S] (skull:muzzle **2:1**; muzzle **deeper than long**,
of even width, width ≈ its length; head **nearly as deep as it is long**;
stop **distinctly pronounced, ≈90°**; supraorbital ridges **strongly
developed**; ears **medium, set high and wide**, front edge lying close to
the cheek; eyes **set more to the front**, medium, friendly expression;
jaws **strong, broad, equal in length**) and one measured specimen [S]:
Skulls Unlimited St. Bernard skull, length 24.4 cm × width 15.0 cm →
**ZB/L = 0.615**, height 14.0 cm → 0.574 (a whole-skull height including
mandible — not used as the CraniumHeight anchor, which excludes jaw).

| # | Slider | Jorge | Derivation |
|---|---|---|---|
| 1 | MuzzleLength | 0 | 2:1 skull:muzzle [S] → muzzle fraction ≈ 0.33 = neutral exactly. The dog column's +55 is the single biggest breed correction in this preset — a St. Bernard's muzzle is *short for a dog* |
| 2 | MuzzleWidth | +85 | Muzzle width ≈ its length [S] → target ≈ 0.24 L, near the slider's +100 ceiling (0.25). Flagged in §6: the breed literally asks for a wider muzzle than the span was sized for |
| 3 | MuzzleTaper | −50 | "No taper in any direction" [S] — a block, front face as wide as the base |
| 4 | MuzzleDepth | +80 | Depth exceeds length [S] (FCI: depth at root ≈ 2:1 against length) → target 0.28 L |
| 5 | NoseSize | +50 | "Broad, square" nose, nostrils well open [S] |
| 6 | CraniumWidth | +25 | Topskull massive and broad [S-qual.]; no clean braincase ratio for the breed — [E], ordered above the dog's −10 by the standards' language |
| 7 | CraniumHeight | +35 | Head "nearly as deep as it is long" [S-qual.] — the depth is skull + jaw together; +35 to the cranium and +40 to the jaw (row 17) split it |
| 8 | CraniumLength | +25 | Cranium is 2/3 of head length by the same 2:1 [D] → fraction 0.67 |
| 9 | StopAngle | +90 | The ≈90° stop [S] — deepest stop on the chart, near the slider's working ceiling. This + MuzzleLength 0 is the St. Bernard profile in two numbers |
| 10 | ForeheadWidth | +50 | Broad frontal between strongly developed ridges [E] |
| 11 | EarHeight | 0 | Medium ears [S] = the dog baseline's erect-equivalent size; the breed lives in Tilt, exactly the species spec's drop-ear mechanism |
| 12 | EarWidth | +10 | Medium, slightly broad at the burr ("very strongly developed burr" [S]) |
| 13 | EarPlacementHeight | +15 | "Set on high" [S] — inverts the dog column's −5 |
| 14 | EarSpread | +20 | "Set wide" [S] |
| 15 | EarTilt | −75 | Full drop, front edge lying close to the cheek [S]; past the dog column's −65 Labrador-class fold, and the recorded Jorge note says ears tucked closer to the cheeks |
| 16 | EarTipPoint | −20 | Rounded tips [S] |
| 17 | JawDepth | +40 | Strong, deep jaw under the short muzzle [E from S-qual.] |
| 18 | JawLength | 0 | Upper and lower jaws **equal in length** [S] — no underbite, no overshoot; the dog column already sits here |
| 19 | JawWidth | +50 | "Strong, broad" jaws [S-qual.] with high cheekbones [S] |
| 20 | CheekWidth | +20 | Measured specimen ZB/L 0.615 [S, single skull] → +17.5, rounded +20. Against the dog column's −40 this is the breed's second signature: the head is *wide*, not long |
| 21 | RuffVolume | +35 | Thick neck fur and loose skin mass (short-haired variety assumed; the long-haired variety would go higher — variety is not specified for Jorge, §6) |
| 22 | EyeSize | −10 | Medium eyes [S] — up from the dog's −20, still small against the head's mass |
| 23 | EyeSpacing | +10 | Broad head carries the eyes wider [E] |
| 24 | EyeForwardness | +10 | "Set more to the front than the sides" [S] |
| 25 | BrowProjection | −25 | Dog-column value: strongly developed *supraorbital ridges* in a dog are still not a torus (brow-study discipline) |
| 26 | BrowThickness | −20 | As dog |
| 27 | BrowContinuity | −30 | As dog |
| 28 | BrowShelf | +35 | Where the breed's "strongly developed superciliary ridges" [S] actually live — shelf and overhang, the highest BrowShelf of any canid vector in the project |
| 29 | BrowPosition | +5 | Neutral-high; the friendly expression [S] sits in Position/Padding, not Scowl |
| 30 | BrowPadding | +25 | Forehead skin that wrinkles at attention [S-qual.] is *padded* skin — tissue layer |
| 31 | BrowScowl | 0 | Zero, on purpose: "intelligent, friendly expression" [S] and Jorge's recorded gentleness. The batch's only 0-scowl adult male, and it is a character fact, not a missing value |

### 5.2 Body — HIMBO vector, gentle-mass pole

Jorge and Sen are both big; they are not the same big. Sen is a strongman —
mass as capability, belly *carried*. Jorge's mass is *presence*: the same
neighbourhood of totals, re-tissued softer (MassSmooth 85 vs Sen's 75,
BellyChub 80 vs 75, PecsSaggy 50 vs 45, Muscle 45 vs 65) and with the traps
backed off — Jorge has a neck; things rest against it. **Export scale ×1.39
→ ≈244 cm (8 ft)** [D from the ≈175 cm base [E]]. Plantigrade-ish stance
[recorded] is a foot/pose part choice, not a slider.

| Slider | Value | Reasoning |
|---|---|---|
| Weight 0 to 1 | 95 | Higher than Sen's 90 — not because Jorge is bigger (he isn't) but because Weight's disp is neck/chest-led [S] and Jorge's read is a deep chest under a heavy head |
| Chubby | 85 | The softest tissue base in the batch (Chubby mean 0.92 [S]); Jorge's mass is upholstered first, muscular second |
| Muscle | 45 | Working strength underneath — rescue-dog mass, garden-and-leatherwork hands — never the point of the silhouette |
| Lean | small 100 | Anti-lean pinned, same precedent as Sen [D] |
| BodyMass | 25 | Slightly under Sen's 30: the broad scaler (mean 3.38 [S]) fills the frame; Jorge's extra softness is booked in tissue sliders instead, where it can stay smooth |
| TorsoMass | 100 | Pinned barrel, shared with Sen — the family resemblance is real |
| TorsoMassSmooth | 85 | The batch's highest smoothing: no group separation anywhere. This one slider is most of the Sen/Jorge tissue difference |
| TorsoWidth | 90 | Broad, a breath under Sen's 95 |
| TorsoBackSize | 85 | Back to match; a wide, warm wall |
| TorsoBackShape | 70 | Less shaping than Sen — the back is a place to lean, not a display |
| TorsoLower | 100 | Full lower torso, pinned with Sen |
| TorsoWaistSize | small 65 | Widen direction (big end = "Shrink Waist" [S]); 65 vs Sen's 60 — Jorge's middle is the softest thing about him |
| TorsoBelly | 75 | Mid belly, under Sen's 80 |
| TorsoBellyChub | 80 | …but the *chub layer* is the batch's highest: this is where Jorge's belly lives — soft over structure |
| BellyPot | 60 | Surface pot, a touch under Sen: Jorge's belly hangs a little more than it projects |
| BellySmooth | 80 | Batch-high smoothing with MassSmooth — one continuous warm form |
| TorsoBellyLHandles | 65 | Love handles slightly over Sen's — the harness line sits here (wardrobe note, §5.3) |
| TorsoFlatAbs | 0 | Off |
| PecsSize | 95 | Near-pin chest |
| PecsMass | 85 | Thick, under Sen's 90 |
| PecsWidth | 95 | Chest meets arms fully |
| PecsLower | 65 | Low-sitting fullness |
| PecsSaggy | 50 | The batch's highest gravity value — deliberate: mass at rest. A chest things (and people) settle against |
| PecsClavicle | 60 | Join kept readable, softer than Sen's 70 |
| ArmsTraps | 80 | Present but backed off Sen's 95 — Jorge keeps a neck and a shoulder *line* |
| ArmsTrapsMeat | 90 | Meat without the pin; the head still sits into the shoulders |
| ArmsTrapsPush | 70 | Moderate rise |
| ArmsTrapsValleys | 20 | Near-no definition |
| ArmsShoulders | big 85 | Broad shoulders — the doorway-filling read from his recorded art direction (workshop doorway piece) |
| ArmsDelts | 80 | Caps under tissue |
| ArmsBiceps | 75 | Strong, unremarkable — correct for him |
| ArmsFore | 85 | Forearms a step under Sen's pin: leatherwork and garden strength, hands that hold rather than haul |
| ArmsBrachio | 70 | Connection fullness |
| LegsSize | 100 | Pinned pillars — eight feet stands on something |
| LegsThigh | 100 | Pinned |
| LegsChubby | 80 | Batch-high leg softness (mean 1.11 block [S]) |
| LegsGlutes | 75 | Working muscle under it all |
| LegsCalfSize | 85 | Plantigrade, weight-bearing calves |
| LegsCalfWidth | 80 | Width with size |
| ButtBooty | 75 | Matches Sen — big dog, big rear |
| BubbleButt | 50 | Rounder than Sen's 40: softer thesis again |
| ButtSaggy | 35 | Over Sen's 25, same reasoning as PecsSaggy — rest, not performance |

**⚠ Watch item — Muscle 45 (flagged Nov 12, 2026, per `BARA_LESSONS.md`
§6 D; CONDITIONAL, NOT APPLIED — Jorge's value stays 45).** Jorge's
Muscle 45 with TorsoMassSmooth 85 is the gentlest muscle vector of the
big three. Per BARA_LESSONS R16 that is legitimate *if* the first build
still reads "same class as Sen, softer tissue" — his mass arriving via
TorsoMass 100 / Chubby 85 rather than via Muscle. **Trigger:** if the
first build reads Jorge as merely fat rather than strong, the corrective
is **Muscle 45 → 60** (Sen-ward) — and explicitly **NOT** more Chubby
(R18: fat alone over a low muscle vector is the soft-without-strong
failure). Until that read exists, no change. (His TorsoWaistSize small
65 already uses the resolved "Shrink Waist" semantics ✓.)

### 5.3 Discrete parts & materials (Jorge)

| Item | Treatment |
|---|---|
| **Flews / jowls — `flews_saintbernard`** | **The breed's signature part variant** (species spec §3.4 already rules flews discrete: "loose lip geometry hangs past the jaw line; JawDepth scaling looks wrong"). Spec from the standards [S]: upper-jaw flews **strongly developed, slightly overhanging, forming a wide curve toward the nose**; corner of the mouth remains visible; **lower flews must not be deeply pendant** — UKC lists flews hanging >1½ in below the lower jaw as a serious fault, so the variant has a *drape-depth parameter with a breed ceiling*, not a free slider. Traditional judging proportion: upper flews ≈ **twice as deep as the muzzle is long** [S, Showsight judging summary]. The recorded Jorge note ("enlarged/lowered flews") sits inside that breed envelope — enlarged, yes; past the fault line, no. Black lip-edge pigmentation is a material zone on the part. |
| Nose | `nose_canid` at its broad/square extreme (NoseSize +50 does the scale; the square plan is the variant). |
| Ears | Drop-ear expression of the base ear mesh (EarTilt −75) with the strong burr; no new topology unless the fold clips the cheek at first build. |
| Coat | **Not specified in the person file** — neither pattern, colour, nor short/long variety. Breed-typical red-and-white is the obvious placeholder and is labelled placeholder in §6; Jorge gets asked, not assumed. |
| Harness | **Equipment, not anatomy.** Recorded (person file: harness; his own leatherwork project is his rig). It belongs to the wardrobe layer — but note for the wardrobe builder: it is designed to sit over TorsoBellyLHandles 65 / PecsLower 65 territory, so strap placement should be fitted *after* the body vector, not before. |
| Anatomy modules | The person file records hyperphallic/hyperorchidism canon for Jorge. Per the modularity ruling those are swappable species-module parts with their own parameters — **outside this batch's HIMBO body vector**, which contains no genital-module values, and none are derived here. Noted so the omission is a scope line, not an oversight. |

### 5.4 Character read

Jorge is the family's hearth: the husband who is *just here*, who unweights
Joe without solving him, whose whole recorded tempo is "long, not hot."
The breed derivation turned out to be the character derivation — a St.
Bernard's head is a short, deep, wide block stopped at ninety degrees with
the lips hanging in a careful curve, and every one of those numbers reads
as *gentle mass that was bred to find people in the snow and stay with
them*. The preset leans in: the batch's only BrowScowl 0, the highest
smoothing and sag values in the batch, forearms built for holding, and a
body whose difference from Sen's is never size — it is *tissue intent*.
Sen's mass says *I can move the world*; Jorge's says *you can lean now*.
Put both avatars in a room and the sliders should let you tell which one
Joe goes to be comforted by, before either of them speaks in that low,
slow, warm voice.

---

## 6. Honesty box — estimates, gaps, and unsourced places

**Species vectors:**

1. **Bear EarHeight (−10) is the weakest number in §1** [E]. No measured
   bear ear/skull series was findable; the target rests on a low-grade
   infographic range for brown bear plus the moon bear's qualitative
   "proportionately longer" [S-qual.]. First task when a bear head model
   enters the library: measure it and re-derive.
2. **Bear CheekWidth is brown-bear-only.** The Asiatic black bear's
   published skull "width" (0.64–0.70 of length) could not be used — its
   landmark is unstated and the same sources call its zygomatic arches
   *narrower* than the brown bear's. If that width ever resolves as true
   ZB, bear CheekWidth moves to ≈ +35 and Sen's head gets much wider; the
   document takes the conservative reading and says so.
3. **Bear JawLength (−50)** averages two sourced ratios (0.665, 0.698)
   from different populations and length bases (GL vs cranial length). The
   direction (short jaw) is solid; the exact −50 is ±10.
4. **Bear EyeSize / EyeSpacing** carry the same weakness the original spec
   flagged for canid eyes: no ursid orbit series found. EyeSpacing's
   nearest sourced number (medial-angle width 0.246 L) is a different
   landmark and was discounted by judgement, not formula.
5. **Badger JawLength (+70) is cross-sample**: mandible length from the
   Iranian *Meles* series divided against greatest lengths from the same
   study (0.810) — same study, but the Iranian ZB outlier (0.555 vs
   0.595–0.637 everywhere else) warns that this population or its landmarks
   run small in width; if its lengths run long instead, JawLength is
   overstated by ~10.
6. **Badger MuzzleLength (+30)** chooses the CT study's viscerocranium
   fraction (0.391) over the Iranian dorsal-face fraction (0.213). The
   choice is argued in §2.1 (different landmarks), but it is a choice: on
   the other landmark the badger would be a short-faced animal and
   MuzzleLength would be ≈ −60. The viscerocranium reading matches the
   visible animal (a badger's face is not a cat's), but the conflict is
   on the record.
7. **Badger EarHeight (+10)** rests on **one** *Taxidea* specimen's
   external ear (52 mm) against its skull length — an upper bound, mixed
   bases (skin ear vs skull). *Meles* ears sit shorter in the fur; a
   *Meles*-pure vector might put EarHeight at −10. Brand's substrate is
   badger-wolf, and the wolf sits at 0 — +10 stays defensible for him, but
   it is the badger vector's softest sourced value.
8. **Badger CraniumHeight (−50)** is [E]: "low broad skull" is sourced
   qualitatively in both genera, but no height/length series was found to
   compute from.
9. Brow vectors for both new species are [E] throughout, per the
   brow-study's own discipline — they are design equivalents on a
   hominin-calibrated scale, not measurements. No animal brow in this
   project is anything else.

**Character presets:**

10. **Pyn's mass is double-recorded and not fully reconciled.** The person
    file's body-engineering target is 82 lb (= 37.2 kg, matching the older
    spec figure exactly). MEMORY.md also carries a later build estimate of
    ~75 kg ±10 that nobody has reconciled with it. This preset uses the
    person file (37.2 kg class, via the 168 cm slight build); the 75 kg
    figure is a build-side outlier awaiting Joe/Pyn's ruling, and nothing
    here settles it.
11. **Pyn's 36 cm ears vs EarHeight +100** can conflict at build time
    depending on final head length (§3.1). The absolute decision is Pyn's
    own and is treated as governing; the tension is recorded, not resolved.
12. **Pyn's coat colour, eye colour, tail dimensions and foot plan are not
    in his person file.** Species-typical values would be guesses wearing
    a lab coat; they are left as open fields for Pyn/Joe, flagged in §3.3.
13. **Sen's forehead mark shape is not described** anywhere in his file
    (only that it is retained). No shape is specified here. His mass
    (2,500 lb) is likewise carried as canon scale, not derived — no slider
    system outputs kilograms, and §4.2 doesn't pretend otherwise.
14. **Sen's blend weighting is a judgement call.** The file names three
    bears (moon + grizzly + Asian black; two of the names are one species).
    §1 weights brown/grizzly for bone and moon bear for jaw mass, ears and
    markings; a different weighting is defensible and would move EarSpread,
    JawDepth and RuffVolume by ~5–10.
15. **Jorge's coat (pattern, colour, short/long variety) is not in his
    person file**, nor is any eye colour. §5.3 labels the breed-typical
    placeholder as a placeholder. His height (8 ft) and the head direction
    *are* recorded and are used.
16. **Jorge's MuzzleWidth (+85) strains the slider span**: the breed
    standard's width ≈ length proportion implies ≈0.24 L against a span
    ceiling of 0.25 — inside, barely. If the first build reads pinched,
    the fix is widening the MuzzleWidth span for brachycephalic breeds,
    not fudging the preset. (The cat's Persian range in the original spec,
    cranial index up to 0.97, is precedent that breed extremes outrun
    species spans.)
17. **HIMBO small-end semantics** (Lean small, TorsoWaistSize small, used
    for Sen/Jorge widening) follow BodySlide's own convention that the
    small end is the inverse morph, corroborated by the Daddy/Chonky
    presets' usage [D] — but per-slider small-end geometry was not
    separately decoded in the learned data. The orc spec's standing
    instruction applies: verify on first build; the affected values are
    Lean, TorsoWaistSize (both big builds) and are listed here so the
    check is cheap.
18. **Body vectors are HIMBO-vocabulary only.** Tails, digitigrade/plantigrade
    feet, ears and anatomy modules are parts under the modularity ruling
    and are handled as part notes (§3.3/§4.3/§5.3), not body sliders — a
    character assembled from these vectors still needs its part set fitted.
    Heights are export scale, per the orc precedent; HIMBO's own ≈175 cm
    base height is itself [E] (inferred from z-span in the orc spec).

*End of Batch 1. Companions: `species-head-spec.md` (§§1–2 above are
written to append to its §3.2 anchor table and §3.3 preset table),
`preset-orc-bara.md` (format model), `brow-study.md` (brow discipline),
`~/workspace/character_assets/learned/` (HIMBO + Fat Males decoded data).
Next batch candidates: Brand (badger × wolf blend vector + his recorded
width-first build), Sage, and the remaining Titans — on Joe's word.*
