# Expression System — FACS-Based Slider Family for the Layered Head

*Design spec, Nov 12, 2026. Sits on top of the layered head construction
(skull → muscle → tissue) and the 31-slider shape spec in
`species-head-spec.md`. Companions: `brow-study.md` (brow layer anatomy),
`ELDRITCH_FOUNDRY.md` §3/Rule EF3 (two master emotion sliders over fine
sliders beat a mouth-part library), `CREATOR_LESSONS.md` R6 (asymmetry
must be complete or it reads as broken), `MAKEHUMAN_OMNIVERSAL.md` §6.1
(canonical slider record — every slider here is a record in that format).*

*Conventions: **[S]** sourced, **[D]** derived, **[E]** estimate /
art-directed. Expression values are engagement percentages (0–100)
unless stated. All species weighting numbers are **[E]** design values —
they encode published qualitative anatomy (cited where it exists) as
gains, and are flagged as such wherever they appear.*

---

## 0. Design principles

1. **Expression is muscle, full stop.** Every slider in this document
   lives on the **muscle layer**, with its visible effect carried by the
   **tissue layer** riding on top. **No expression slider deforms the
   skull layer** — bone is shape, and shape is the 31-slider spec's job.
   Two apparent exceptions are not exceptions: the jaw sliders move the
   jaw *bone as a rigid part* (pose, driven by muscle — masseter,
   digastrics, pterygoids); they never deform it. The ear sliders rotate
   the pinna on its base via the auricular muscles; they never reshape
   the ear (EarHeight/EarTilt etc. in the shape spec do that).
2. **Shape sliders are the resting face; expression sliders are deltas
   on it.** The head spec already contains two expression-*shaped*
   sliders — BrowScowl (#31, resting corrugator engagement) and EarTilt
   (#15, resting ear carriage). They are the **baseline**. Expression
   sliders in the same muscle region sum with the baseline and clamp:
   a character with BrowScowl +35 (the orc's resting menace,
   `brow-study.md` §5.9) who then gets Angry does not get a second,
   unrelated knit — he gets *more of the same muscle*, up to the
   anatomical ceiling. This is stated per-slider in §2 where a region
   is shared.
3. **Masters are vectors, not geometry** (the Eldritch Foundry lesson,
   EF3). EF beat a much larger competitor's face with two master
   sliders — Happy and Angry — over a fine brow/cheek/jaw layer. We
   ship **7 masters** over **24 fine sliders**. A master is pure data:
   a named weight vector in fine-slider space. It owns no delta field,
   needs no per-base instance of its own, and is retargeted for free
   wherever the fine sliders exist.
4. **Species is a gain table, not a second system** (§4). The same
   masters and fine sliders run on every head. What changes per species
   is a set of channel gains (ears matter more on a cat, brow matters
   more on a dog and an orc, whiskers matter on felids) plus two named
   remapping rules (felid flehmen, canid snarl). One system, weighted.
5. **Fine sliders are unipolar engagement (0…+100)** — a deliberate
   deviation from the shape spec's −100…+100 convention. Muscles only
   contract one way; bipolarity in a face comes from *antagonist pairs*
   (inner-brow raise vs brow lower; lip-corner pull vs depress), not
   from negative contraction. The three exceptions are stated where
   they occur (JawShift is genuinely lateral; nothing else is).
   Composition is additive with clamping (§1.3), so masters can only
   *engage* muscles — a master that wants a muscle *off* expresses that
   by engaging its antagonist or by leaving weight 0 against a low
   resting baseline. This matches how faces actually work and keeps
   every intermediate pose anatomically reachable.
6. **Blink is animation, not a pose.** Blink is authored as a delta
   field like everything else, but its record carries
   `"drive": "animation"` — the runtime drives it from a blink curve
   (and the felid slow-blink is a *tempo* applied to that curve, §4.2),
   not from the pose panel. It is in the fine set because masters and
   viseme work need to reference the field, and because a held
   eyes-closed pose is a legitimate still.

---

## 1. Architecture

### 1.1 The three tiers

| Tier | Contents | Count | Owns geometry? |
|---|---|---|---|
| **Shape** (existing) | 31 head sliders, `species-head-spec.md` | 31 | Yes — delta fields on skull/muscle/tissue |
| **Fine expression** (this doc) | Muscle-engagement sliders, §2 | **24** | Yes — delta fields (muscle/tissue) or pose records (jaw, ears) |
| **Masters** (this doc) | Named emotion vectors over the fine set, §3 | **7** (+1 shipped variant) | **No** — pure weight vectors |

### 1.2 Record kinds

Following `MAKEHUMAN_OMNIVERSAL.md` §6.1/§6.5, expression sliders are
canonical records with three payload kinds:

- `"kind": "delta"` — a per-vertex delta field on the tissue surface
  (authored from the muscle layer, §6). Most of the set.
- `"kind": "pose"` — a bone-motion record (jaw rotation/translation,
  ear-base rotation) with an angle/offset curve instead of a delta
  field. Same record shell, same provenance/QA discipline — the
  sibling-record pattern §6.5 established for parts.
- `"kind": "vector"` — a master: weights over other slider IDs. No
  instance files; QA is a render check (§6.5).

### 1.3 Composition order (normative)

```
final = shape_spec_vector                     (resting anatomy)
      + Σ master_intensity × master_weights   (species gains applied, §4)
      + user fine-slider offsets
      → clamp each fine slider to its range
      + asymmetry offsets (§5)                (per-side, applied last)
      + blink curve value                     (animation tier)
```

- Masters sum in fine-slider space; two masters at partial intensity
  blend (Happy 50 + Surprised 50 is a real, reachable face — EF's
  reviewers demonstrated exactly these compound reads).
- User fine offsets apply *after* masters: grabbing BrowLower directly
  always wins locally over whatever Angry said.
- **Couplings** (soft, composition-layer only — records stay pure, per
  the omniversal rule that instances never bake interactions):
  - *Lip press fades with jaw opening:* LipTighten's effective value
    scales by `1 − max(0, JawOpen − 40)/60` — you cannot press lips
    shut over a wide-open jaw.
  - *Pressed smile:* LipCornerPull over LipTighten ≥ 60 reads as a
    suppressed smile automatically (both fields are real); no rule
    needed, noted so nobody "fixes" it.
  - *Glare co-contraction:* LidRaise + BrowLower co-engagement is
    legal and is how the angry stare is built (real faces do AU4+AU5
    together); no clamp between them.
  - *Felid flehmen remap:* §4.2.

---

## 2. The fine set — 24 sliders

All ranges 0…+100 (engagement) except JawShift (−100…+100). Layer is
**muscle** for every entry; "tissue effect" notes where the visible
displacement mostly lives. Anchor displacements are at human scale and
are the QA targets for `author_slider.py` (§6); animal heads inherit
them scaled by L via the canonical endpoint-anchor mechanism.

### 2.1 Brow (3) — frontalis vs corrugator/procerus

The expression twins of the shape spec's brow band (#25–31). Shape
sliders set the *bone and resting tissue*; these move the soft brow
line over whatever bone is present. On canids/felids, whose
BrowProjection is negative (no torus — `brow-study.md` §6.1), these
sliders act on the frontal-sinus eminence and brow fur line — they are
exactly as meaningful there, because they were never about bone.

| # | Slider (ID) | FACS / anatomy | Range | What it deforms, in plain terms |
|---|---|---|---|---|
| E1 | BrowInnerRaise (`expr.brow.inner_raise`) | AU1; frontalis (medial) — in dogs, the LAOM [S: Kaminski 2019, via brow-study §2] | 0…100 | The inner third of each brow lifts and the brow line peaks toward the middle — the "sad eyebrows", puppy-dog raise, appeal look. Medial brow point rises ≈4 mm at +100 [E, cf. brow-study §5.7 raise anchors]. |
| E2 | BrowOuterRaise (`expr.brow.outer_raise`) | AU2; frontalis (lateral) | 0…100 | The outer brow lifts; with E1 gives the full raised brow of surprise. Weaker alone — frontalis is deficient laterally [S: brow-study §4], so its anchor displacement is ≈3 mm and its falloff is wide and soft. |
| E3 | BrowLower (`expr.brow.lower`) | AU4; corrugator supercilii + procerus + depressor supercilii | 0…100 | Brow pulls down and in, knits toward the glabella, vertical furrow hints in the tissue. **Shares its muscle region and delta-field mask with shape slider #31 BrowScowl** — BrowScowl is this muscle's *resting* engagement baked into the shape vector; E3 is the dynamic range on top. Sum clamps at the anatomical ceiling (≈4 mm medial depression at combined +100 [E: brow-study §5.7]). |

### 2.2 Lids & cheeks (4) — orbicularis oculi and friends

| # | Slider (ID) | FACS / anatomy | Range | What it deforms, in plain terms |
|---|---|---|---|---|
| E4 | LidRaise (`expr.lid.raise`) | AU5; levator palpebrae | 0…100 | Upper lid retracts, more iris/sclera shows — the wide-eyed stare of surprise, fear, or threat. Acts on the lid shells, not the eyeball (EyeSize #22 is never touched by expression). |
| E5 | LidTighten (`expr.lid.tighten`) | AU7; orbicularis oculi (palpebral part) | 0…100 | Lids squeeze: lower lid rises, aperture narrows, the glare/squint. The "eyes narrow" half of anger and suspicion, and — at low values with E6 — the smile squint. |
| E6 | CheekRaise (`expr.cheek.raise`) | AU6; orbicularis oculi (orbital part) + cheek tissue | 0…100 | Cheek mass pushes up into the lower lid, infraorbital region bunches — the Duchenne marker that separates a felt smile from a mouth-only grin. On muzzled heads this is the cheek/ruff tissue under the eye riding up. |
| E7 | Blink (`expr.lid.blink`) | AU43/45; orbicularis + levator release | 0…100, `"drive": "animation"` | Both lids close over the eyeball. Authored as a field, driven by curve (§0.6). At a held 100 it is the closed-eyes pose (sleep, contentment, the felid slow-blink's bottom). |

### 2.3 Nose & muzzle (3)

| # | Slider (ID) | FACS / anatomy | Range | What it deforms, in plain terms |
|---|---|---|---|---|
| E8 | NoseWrinkle (`expr.nose.wrinkle`) | AU9; levator labii superioris alaeque nasi | 0…100 | The top of the muzzle/nose bridge gathers into wrinkles, nose leather tips back slightly. Half of the snarl, most of disgust. On long muzzles the wrinkle field sits on the dorsal rostrum and reads at a distance — it is the threat signal other animals actually watch. |
| E9 | LipLift (`expr.lip.lift`) | AU10; levator labii superioris | 0…100 | Upper lip rises and everts, exposing the upper canines. **The snarl slider.** On the orc it exposes the upper teeth row (the tusks are *lower* canines — tusk display is E9's partner move, JawOpen + E17, §4.3). Felids remap this at high values into flehmen (§4.2). Famously asymmetric in real animals — a first-class asymmetry citizen (§5). |
| E10 | WhiskerPad (`expr.muzzle.whisker_pad`) | Mystacial pad musculature (intrinsic vibrissal muscles) | 0…100 | The whisker pads push forward and the vibrissae fan protracts (whisker *card roots* rotate with the pad — the pad delta carries the card anchor frame). Curiosity, hunting focus, social interest. Retraction is the 0 state — there is no negative; a defensive cat's swept-back whiskers are "E10 at 0 while ears flatten", which is why masters express it by omission (Principle 5). |

### 2.4 Lips & mouth (7)

| # | Slider (ID) | FACS / anatomy | Range | What it deforms, in plain terms |
|---|---|---|---|---|
| E11 | LipCornerPull (`expr.lip.corner_pull`) | AU12; zygomaticus major | 0…100 | Mouth corners pull up and back. Human: the smile. Canid: the commissure stretches long and back — the submissive/play "grin". The same field, read by species (§4). |
| E12 | LipCornerDepress (`expr.lip.corner_depress`) | AU15; depressor anguli oris | 0…100 | Corners pull down — sadness, grimace, the downturned "worried mouth". |
| E13 | LipPucker (`expr.lip.pucker`) | AU18 (+ AU22 funnel at high values); orbicularis oris | 0…100 | Lips push forward into a pucker/funnel — the "oo" shape, blowing, the investigative pushed-forward muzzle of an animal scenting. Primary viseme component (§5 of visemes, below §4). |
| E14 | LipTighten (`expr.lip.tighten`) | AU23/24; orbicularis oris | 0…100 | Lips press together and flatten, mouth line goes thin and straight — suppressed anger, determination, the closed-mouth "no". Faded by jaw opening (§1.3 coupling). |
| E15 | LipStretch (`expr.lip.stretch`) | AU20; risorius/platysma | 0…100 | Mouth stretches wide and thin horizontally, corners retract without rising — the fear grimace. In canids this plus commissure retraction is the classic fear grin (and is *not* E11: direction and lid/brow context differ, which is why both exist). |
| E16 | ChinRaise (`expr.chin.raise`) | AU17; mentalis | 0…100 | Chin boss pushes up, lower lip rides up and out — pout, doubt, the pre-cry tremble, and the felid/ungulate lip-curl assist. On muzzled heads the field sits on the chin/lower-lip pad of the jaw mesh's tissue. |
| E17 | LowerLipDepress (`expr.lip.lower_depress`) | AU16; depressor labii inferioris | 0…100 | Lower lip pulls down, exposing lower teeth/gum — pant-adjacent openness, the lower half of tusk display, and a viseme workhorse (F/V family). |

### 2.5 Jaw (3) — pose records, muscle-driven

Kind `"pose"`: these write jaw-bone rotation/translation curves, not
delta fields. Layer: muscle (the movers are masseter, digastric,
pterygoids); the jaw mesh follows its bone exactly as it does for the
shape spec's jaw sliders.

| # | Slider (ID) | FACS / anatomy | Range | What it deforms, in plain terms |
|---|---|---|---|---|
| E18 | JawOpen (`expr.jaw.open`) | AU26/27 | 0…100 | Jaw drops on its hinge. 100 = full gape for this head (bounded per base by the jaw part record, not a universal angle — a lion's gape and a cat's differ and the record says so). Carries speech, panting, roaring, yawning. |
| E19 | JawShift (`expr.jaw.shift`) | Lateral pterygoid (unilateral) | **−100…+100** | Jaw slides sideways — chewing, jaw-wagging threat in some species, lopsided chewing gum energy. The one inherently asymmetric slider; exempt from the §5 asymmetry system because it *is* lateral. |
| E20 | JawProtrude (`expr.jaw.protrude`) | Pterygoids + masseter set | 0…100 | Jaw thrusts forward, underbite deepens dynamically. The dynamic twin of the orc spec's static JawProtrusion extension — an orc at rest has his prognathism in the shape vector; this is him *jutting* it at you. |

### 2.6 Ears (4) — auricular muscles; pose + base delta

Ears are half the emotional vocabulary of a furry character — a human
face has nothing equivalent, and no master in §3 is complete without
them. Kind: `"pose"` (ear-base bone rotation, per side) plus a small
pinna-base delta field so the pinna *folds* rather than rotating as a
rigid card. Layer: muscle (auricularis group). Baseline is shape
slider #15 EarTilt — exactly the BrowScowl/E3 relationship (§0.2):
EarTilt is where the ear lives; these are where it *goes*.

DogFACS/CatFACS formalise the same movements as Ear Action Descriptors
(ears forward / adductor / rotator / flattener) [S] — the four sliders
below are those descriptors, generalised.

| # | Slider (ID) | Anatomy / EAD | Range | What it deforms, in plain terms |
|---|---|---|---|---|
| E21 | EarForward (`expr.ear.forward`) | Auricularis anterior; EAD "ears forward" | 0…100 | Pinnae rotate forward, ear openings face front — attention, interest, approach; the offensive-threat ear. |
| E22 | EarBack (`expr.ear.back`) | Auricularis posterior; EAD "ears back" | 0…100 | Pinnae rotate rearward, tips point back, openings still open — listening behind, mild appeasement, low-grade annoyance. The everyday ear, not the emergency one. |
| E23 | EarFlatten (`expr.ear.flatten`) | Auricularis + pinna fold; EAD "ears flattener" | 0…100 | Pinnae press down and back against the skull, folding at the base — fear, defensive threat, strong appeasement. The loudest ear signal there is. Per-species ceilings apply (§4: a fennec's 1.05 L pinna cannot plaster flat; its record caps the effective range). |
| E24 | EarSwivel (`expr.ear.swivel`) | Auricularis superior; EAD "ears rotator" | 0…100 | Pinnae yaw outward laterally — bilateral E24 at mid values with a touch of E22 is the famous felid **airplane ear** of annoyance; unilateral, it's an ear turned toward a side stimulus. |

**Fine-set total: 24** (brow 3, lids/cheeks 4, nose/muzzle 3, lips 7,
jaw 3, ears 4).

---

## 3. The masters — 7 emotion vectors

Each master is a `"kind": "vector"` record: weights (0–1) over the
fine set; master value 0…100 scales the whole vector. Weights below are
the value at master = 100, before species gains (§4) and clamping.
Zeros are omitted from the tables for readability — an omitted slider
has weight 0. **Blink (E7) appears in no master**: it is animation-tier
(§0.6); lid *sliders* carry each emotion's eye look statically.

### 3.1 Happy — contentment, play, affiliation

*What you see:* cheeks up, soft squint, mouth corners long and lifted,
ears pricked toward you, muzzle relaxed and whiskers forward.

| Slider | E6 CheekRaise | E11 LipCornerPull | E5 LidTighten | E21 EarForward | E10 WhiskerPad | E18 JawOpen | E1 BrowInnerRaise |
|---|---|---|---|---|---|---|---|
| Weight | 0.80 | 0.75 | 0.25 | 0.45 | 0.35 | 0.15 | 0.10 |

The E6-before-E11 ordering is deliberate and FACS-honest: the felt
smile is cheek-led (AU6), the mouth follows. A grin built from E11
alone is the polite/fake smile — reachable by hand, not via this master.

### 3.2 Angry — rage, frustration, humanoid menace

*What you see:* brow knitted down, glare (lids tight *and* raised —
co-contraction), lips pressed thin, jaw set forward, ears half back.

| Slider | E3 BrowLower | E5 LidTighten | E4 LidRaise | E14 LipTighten | E8 NoseWrinkle | E20 JawProtrude | E22 EarBack | E12 LipCornerDepress |
|---|---|---|---|---|---|---|---|---|
| Weight | 0.90 | 0.70 | 0.30 | 0.65 | 0.35 | 0.25 | 0.30 | 0.20 |

### 3.3 Threat — the agonistic display (the animal master)

EF doesn't need this one; a furry creator does. Threat is a
*display* — evolved signalling, not felt emotion — and it is the
single most-posed expression in furry art (the snarl). Brow is
secondary; the money is lip lift + nose wrinkle + stare + ear posture.

*What you see (offensive form):* upper lip lifted off the canines,
nose wrinkled, hard stare, ears forward and stiff, jaw set.

| Slider | E9 LipLift | E8 NoseWrinkle | E4 LidRaise | E5 LidTighten | E3 BrowLower | E21 EarForward | E20 JawProtrude | E17 LowerLipDepress |
|---|---|---|---|---|---|---|---|---|
| Weight | 0.90 | 0.75 | 0.55 | 0.45 | 0.55 | 0.60 | 0.30 | 0.20 |

**Shipped variant — Threat (defensive):** same record family, variant
flag set: E21→0 replaced by **E23 EarFlatten 0.70**, E11 LipCornerPull
**0.35** added (the long retracted commissure), E18 JawOpen 0.25.
Offensive vs defensive threat is *the* foundational distinction in
canid/felid body language [S-qual.]; shipping both as named vectors
costs nothing and prevents the classic error of snarling a frightened
animal with confident ears.

### 3.4 Fearful — fear, appeasement, submission

*What you see:* inner brow up, eyes wide, mouth stretched thin, ears
flat, whiskers withdrawn (by omission).

| Slider | E23 EarFlatten | E1 BrowInnerRaise | E4 LidRaise | E15 LipStretch | E18 JawOpen | E2 BrowOuterRaise | E12 LipCornerDepress | E24 EarSwivel |
|---|---|---|---|---|---|---|---|---|
| Weight | 0.80 | 0.75 | 0.70 | 0.55 | 0.35 | 0.40 | 0.30 | 0.25 |

### 3.5 Surprised — startle, wonder

*What you see:* whole brow up, lids retracted, jaw dropped, ears
pricked hard forward.

| Slider | E4 LidRaise | E21 EarForward | E2 BrowOuterRaise | E1 BrowInnerRaise | E18 JawOpen | E13 LipPucker |
|---|---|---|---|---|---|---|
| Weight | 0.85 | 0.85 | 0.80 | 0.70 | 0.55 | 0.15 |

### 3.6 Sad — grief, disappointment, the appeal face

*What you see:* the grief-muscle combination — inner brow raised
*and* slightly knitted (AU1+AU4 is the sourced sadness signature, and
the reason E1 and E3 are separate sliders), corners down, ears low
and back.

| Slider | E1 BrowInnerRaise | E12 LipCornerDepress | E22 EarBack | E16 ChinRaise | E3 BrowLower | E24 EarSwivel | E5 LidTighten | E18 JawOpen |
|---|---|---|---|---|---|---|---|---|
| Weight | 0.65 | 0.60 | 0.45 | 0.35 | 0.15 | 0.20 | 0.15 | 0.05 |

### 3.7 Disgusted — contamination, contempt

*What you see:* nose wrinkled hard, upper lip up, chin pushed,
corners down — the face that evolved around spoiled food.

| Slider | E8 NoseWrinkle | E9 LipLift | E16 ChinRaise | E12 LipCornerDepress | E3 BrowLower | E5 LidTighten | E17 LowerLipDepress | E22 EarBack |
|---|---|---|---|---|---|---|---|---|
| Weight | 0.90 | 0.70 | 0.45 | 0.40 | 0.35 | 0.30 | 0.25 | 0.25 |

**Master total: 7** — Happy, Angry, Threat, Fearful, Surprised, Sad,
Disgusted (+ Threat-defensive as a flagged variant of #3, not an
eighth master). The six Ekman-style basics are all present except
that *joy* is Happy and *anger* splits into Angry (affect) and Threat
(display) — the split is the furry-specific design decision, justified
in §3.3. Contempt, interest, and sleepiness are deliberately *not*
masters: contempt is Disgusted + asymmetry (§5), interest is
EarForward + WhiskerPad by hand, sleepiness is a blink-curve tempo —
all reachable, none needing a vector slot.

---

## 4. Species translation — gains, not systems

A species' expression profile is stored **inside its existing species
preset record** (the §3.3 vector in `species-head-spec.md`) as an
`expression_gains` block: one multiplier per *channel*, plus the
remap rules in §4.2/§4.3 where they apply. Channels group the fine
set by anatomy:

| Channel | Fine sliders |
|---|---|
| Brow | E1, E2, E3 |
| Lids | E4, E5, E6, E7 |
| Snarl | E8, E9 |
| Lips | E11–E17 (mouth/lip set) |
| Jaw | E18, E19, E20 |
| Ears | E21–E24 |
| Whisker | E10 |

Master application becomes: `effective_weight = master_weight ×
channel_gain(species, channel_of(slider))`, with the per-slider
exceptions noted below the table. Same vectors, same sliders — a wolf
and a cat given "Angry 70" are running identical data through
different gains. **[All gains E]** — art-directed values encoding the
qualitative anatomy cited in the notes.

### 4.1 Gain table

| Species | Brow | Lids | Snarl | Lips | Jaw | Ears | Whisker | Notes (exceptions & reasons) |
|---|---|---|---|---|---|---|---|---|
| Wolf | 0.7 | 0.9 | 1.1 | 0.9 | 1.0 | 1.1 | 0.5 | **E1 exception: 0.5** — the LAOM is only scant fibres in wolves [S: Kaminski 2019]; the wolf literally cannot do the dog's inner-brow raise at full strength. Whisker musculature modest. |
| Red fox | 0.7 | 1.0 | 1.0 | 0.9 | 0.9 | 1.2 | 0.7 | Ear-led reader; lighter jaw. |
| Fennec | 0.6 | 1.0 | 0.9 | 0.9 | 0.8 | 1.3 | 0.7 | **E23 exception: ceiling 0.7** — a pinna at 1.05 L cannot plaster flat against the skull; its record caps effective flatten. Everything else about the ears is *more* expressive for their size. |
| Lion | 0.8 | 1.0 | 1.2 | 0.8 | 1.2 | 0.9 | 1.1 | Snarl/jaw-led: the big-canine display is the lion's whole threat vocabulary. Brow read comes mostly from the shape-side BrowShelf (+20) shadow, not from E-sliders. Small rounded ears partly mane-occluded (mane is a part, §3.4 of head spec). |
| Panther (leopard) | 0.8 | 1.0 | 1.2 | 0.8 | 1.1 | 1.0 | 1.2 | As lion, whisker channel stronger (protraction is a hunting-focus tell). |
| Cat | 0.6 | 1.2 | 1.0 | 0.7 | 0.9 | 1.3 | 1.3 | **The lid/ear/whisker species.** Affect is read in slow blinks (blink-curve tempo, §4.2), airplane ears, and whisker protraction; brow and lip channels are genuinely weak anatomy and are gained down, not up. Flehmen remap applies (§4.2). |
| Dog | 1.1 | 1.0 | 1.1 | 1.0 | 1.0 | 1.2 | 0.6 | **The brow species** — LAOM is fully developed in domestic dogs [S: Kaminski 2019]; E1 is the dog's signature signal and gains *above* 1. Ear gains act on the ear-base rotation — drop-ear builds (EarTilt −65) swing a floppy pinna from that base, which is correct: the base moves, the flop follows. |
| Orc | 1.3 | 1.1 | 1.1 | 1.0 | 1.2 | 0.4 | 0.0 | Brow-led and jaw-led: E3 rides on the torus shape vector (Proj +135 / Scowl +35 baseline) and reads enormous; masseter-driven jaw gains up. Ears are small, pointed, and comparatively immobile — gains near-zero but **not deleted**: an orc ear twitch at 0.4 is a subtlety feature. No mystacial pad system → Whisker 0.0 (honest absence, recorded, not faked). |

### 4.2 Felid remaps (rules, not sliders)

- **Flehmen:** when a felid's E9 LipLift passes ≈60, the *flehmen
  profile* engages: lip curl profile switches from evert to
  curl-back, E18 JawOpen gains +15, E4 LidTighten +10 (the
  half-closed "stink face"). Implemented as a coupling in the felid
  gain profile — E9's field is authored with both profiles and the
  remap cross-fades them. Ungulate-style flehmen is out of scope
  until an ungulate preset exists.
- **Slow blink:** the cat's affiliation signal is Blink (E7) driven
  at ≈0.3× tempo with E5 at ~20 — a *usage pattern* of existing
  records, shipped as a named animation preset in the cat profile.
  No slider exists for it, correctly: it is timing, not shape.

### 4.3 Orc tusk display (a composition, not a slider)

Tusks are *lower* canines (teeth system: one universal arcade, lowers
ride the jaw — TEETH.md). Displaying them is therefore: E17
LowerLipDepress (lower lip drops off the tusks) + E18 JawOpen small +
E20 JawProtrude — all already in Threat's vector at orc gains. No
tusk slider is authored; the display falls out of the composition,
which is the test that the fine set is complete.

### 4.4 What does *not* translate

- **Markings are not expression.** Tan pips, forehead stripes, ear-back
  patches belong to the material layer (`brow-study.md` §4) and track
  BrowPosition; no expression slider may write to them. A surprised
  wolf's pips rise only because the tissue under them does.
- **The mane/ruff is not expression.** RuffVolume (#21) is shape.
  A lion's mane bristling is a fur-system behaviour (piloerection is
  real — arrector pili — and belongs to the fur spec as a body-level
  channel, not to this head system).

---

## 5. Visemes — the minimal speech set

Eleven shapes: the classic Preston Blair set, pruned to what our fine
sliders can actually articulate. Each viseme is a *static vector over
the jaw/lip fine sliders* (same `"kind": "vector"` record type as
masters, group `viseme/`) — speech animation is a timed sequence of
viseme vectors, authored elsewhere; this spec defines the shapes.

Tongue positions are **part poses**, not sliders: the tongue is a
swappable part on the teeth-arcade model (TEETH.md), and visemes that
need it name the tongue pose (`tongue: tip_up`, `tongue: between_teeth`,
`tongue: low`) as part-record state alongside the slider vector.

| Viseme | Sounds | E18 JawOpen | Key fine settings | Tongue |
|---|---|---|---|---|
| Rest | silence, pauses | 5 | all others 0 (LipTighten 5 to keep the mouth closed) | low |
| MBP | m, b, p | 0 | E14 LipTighten 60 (lips pressed — the closure *is* the shape) | low |
| FV | f, v | 10 | E16 ChinRaise 40 + E17 LowerLipDepress 25 (lower lip drawn up/in to the upper teeth) | low |
| TH | th (θ/ð) | 15 | E11 LipCornerPull 10 | **between_teeth** |
| LNTD | l, n, t, d | 20 | E13 LipPucker 0; mouth corners neutral | **tip_up** (to alveolar ridge) |
| KG | k, g, ng | 30 | no lip action — the shape is jaw + open back of mouth | low/back |
| S | s, z | 15 | E15 LipStretch 30, teeth near-closed (JawOpen low is the point) | low |
| CH | ch, sh, j | 25 | E13 LipPucker 35 + E15 LipStretch 15 | low |
| R | r | 30 | E13 LipPucker 25 | low |
| AA | a, æ (open vowels) | 70 | E17 LowerLipDepress 15 | low |
| EE | i, e (spread vowels) | 25 | E11 LipCornerPull 40 + E15 LipStretch 20 | low |
| OH | o | 45 | E13 LipPucker 50 | low |
| OO | u, w | 20 | E13 LipPucker 85 | low |

(12 rows counting Rest — the spoken set is 11. This is the standard
minimal inventory; productions needing /aʊ/ or /ɔɪ/ diphthongs get
them as timed AA→OO / OH→EE blends, not new shapes.)

**Muzzle caveat (normative):** on long-muzzled heads the lip line is
long and the commissure sits far back; lip sliders alone under-read
on camera. Viseme application therefore passes through a **speech
gain profile** per species, same mechanism as §4: canids/felids take
Jaw × 1.2, Lips × 0.8 (speech reads through the jaw on a muzzle);
short-faced and humanoid heads (cat at the short end, orc) take
Jaw × 1.0, Lips × 1.0. The vectors don't change; the gains do. One
system, again.

---

## 6. Asymmetry — per-side offsets

The Saints Row lesson (CREATOR_LESSONS §2.6, R6): asymmetry shipped
for *some* features (brow/ears/eyes but not nose/mouth/jaw) read as
**broken**, not charming. Our rule is therefore absolute:

> **Every bilateral fine slider supports per-side offsets. No
> exceptions.** A slider that cannot be asymmetric does not ship.

### 6.1 Representation

Bilateral fine sliders are authored as **one symmetric delta field**
plus the canonical record's symmetry block (extending
MAKEHUMAN_OMNIVERSAL §6.1):

```json
"symmetry": "bilateral_x",
"asymmetry": {
  "mode": "offset_pair",
  "applies_after": ["masters", "fine"],
  "fields": "instance carries L/R half-masks; runtime evaluates
             value_L = clamp(v + dL), value_R = clamp(v + dR)
             against the mirrored half-fields"
}
```

- Per-base instances of a bilateral slider ship **two half-fields**
  (left verts, right verts, mirrored index map) instead of one full
  field — same total data, addressable halves. Pose records (ears)
  carry per-side bone curves identically.
- Character files store asymmetry sparsely:
  `expr.<slider_id>.asym = [dL, dR]` (integers, −100…+100), present
  only when non-zero. Share codes inherit this for free — the vector
  was always serialisable (R2).
- **Masters never write asymmetry.** Masters are symmetric by
  definition; character comes from the asym layer on top.

### 6.2 Stock asymmetry presets (vectors in the asym layer)

Shipped as named data, because the useful ones recur constantly:

| Preset | Content | Use |
|---|---|---|
| Smirk | E11 asym [+0, +35] (one corner) + E5 asym matching side +10 | contempt, amusement — this plus Disgusted *is* the contempt master we declined to ship (§3.7) |
| SnarlLeft / SnarlRight | E9 asym [±55, ∓0] + E8 asym same side +20 | the one-sided snarl real canids actually show |
| Wink | E7 driven one side only (animation-tier, per-side drive flag) | play, signalling |
| EarPerk | E21 asym one side 40 | listening askew; the head-tilt's partner |
| BrowQuirk | E1 *or* E2 asym one side 30 | scepticism, the raised-single-brow |

### 6.3 Exemptions, stated

JawShift (E19) is exempt — it is lateral by definition. Midline
sliders (E13 Pucker, E14 Tighten, E16 ChinRaise, E18 JawOpen,
E20 JawProtrude) are exempt — they have no sides. Everything else —
brow ×3, lids ×3 (Blink via per-side drive), nose wrinkle, lip lift,
whisker pad, corners ×2, stretch, lower-lip, ears ×4 — is bilateral
and asymmetric-capable. Count: 16 of 24 carry the asym block.

---

## 7. Authoring method — building each fine slider

Everything below is the slider-lab pipeline (SLIDER_ENGINEERING.md,
in progress; tools referenced by their pipeline names —
`mask_tools.py` exists in `slider-lab/`; the record format is
MAKEHUMAN_OMNIVERSAL §6.1 regardless of that doc's state). The
layered head is what makes expression authoring *mechanical* rather
than sculptural: **the masks come from the muscle layer's geometry.**

### 7.1 The five steps (per fine slider)

1. **Name the muscle, take its mesh.** The muscle layer of the base
   head carries named muscle bodies (frontalis L/R, corrugator,
   orbicularis oculi, levator labii, zygomaticus, masseter…). The
   slider's region *is* that muscle's footprint: project the muscle
   body's surface verts onto the tissue surface (nearest-surface +
   geodesic dilation by the muscle's known reach) — `mask_tools.py`
   builds exactly this: landmark set → geodesic falloff field.
   The canonical record stores the *rule*, not the indices:
   `"region": {"landmarks": ["muscle:corrugator_supercilii"],
   "mask_rule": "footprint of named muscle mesh, geodesic falloff
   r = 0.5 x muscle length"}` — portable to any base that carries
   the same named muscle layer (which is every base, by the layered
   construction rule).
2. **Set the contraction direction.** A muscle slider's delta field
   displaces tissue *along the muscle's line of pull, toward its
   origin*, magnitude ∝ mask falloff × endpoint anchor. Frontalis
   pulls up; corrugator pulls down-and-in; zygomaticus pulls
   up-and-back. The direction is read off the muscle mesh's
   origin→insertion axis at authoring time and stored in the record's
   semantics text; the field itself is generated, not hand-sculpted,
   for v1 — hand-refinement is a later pass on sliders whose QA
   renders read wrong (§7.3).
3. **Set the endpoint anchor (metres, at +100).** From anatomy where
   it exists (brow: ≈4 mm medial depression for E3 [E from
   brow-study §5.7]; lid aperture changes and lip displacements are
   authored at 3–6 mm class magnitudes and flagged [E]) — the anchor
   is what `author_slider.py` verifies: apply at +100, measure the
   named landmark's displacement, compare to the record. A slider
   whose measured anchor misses its declared anchor fails QA like
   any other omniversal slider.
4. **Emit the record + instances.** `author_slider.py` writes the
   canonical JSON (id `expr.*`, group `expression/<channel>`,
   `layer: "muscle"` — or `"muscle+tissue"` for E6/E10 — range,
   symmetry + asymmetry block where §6 applies, provenance
   `{method: "procedural muscle-region offset", licence: "original"}`)
   and per-base instances (npz delta fields; two half-fields for
   bilateral sliders; pose-curve JSON for jaw/ear records).
5. **QA gates** (same gates as all omniversal sliders, plus two
   expression-specific ones):
   - fold test at +100 (negative-volume triangle check) — lip and
     lid fields are the risk;
   - anchor displacement check (step 3);
   - **pairwise interference render:** the slider at 100 against
     each master it participates in at 100 (a master's worst case
     is all its weights live at once);
   - **resting-sum check:** shape baseline + slider at 100 must not
     exceed the anatomical ceiling where a shape twin exists
     (E3 + BrowScowl; ear sliders + EarTilt).

### 7.2 Worked examples (the pattern, three ways)

- **E3 BrowLower (delta, muscle):** mask = corrugator + procerus
  footprint; direction = down-and-medial along the corrugator axis;
  anchor 4 mm medial brow depression; half-fields shipped (quirk
  preset needs one side); record cross-references shape slider #31
  (`"baseline_twin": "head.brow.scowl"`) so the resting-sum QA gate
  can find the pair.
- **E18 JawOpen (pose, muscle):** no mask, no field — the record
  carries a hinge curve (rotation about the jaw bone's hinge landmark
  pair, angle at +100 = per-base gape bound from the jaw part record)
  and a small *secondary* delta field for the chin/throat tissue that
  stretches as the jaw drops (authored by the same mask method over
  the submental region — jaw pose without tissue follow-through is
  the v1-head "solid bar jaw" failure in miniature).
- **E23 EarFlatten (pose + delta, muscle):** ear-base rotation curve
  (posterior + lateral, per side) + pinna-base fold field (mask =
  auricular muscle footprint at the pinna base, direction = fold
  line). Per-species ceiling lives in the *species gain profile*
  (fennec 0.7, §4.1), not in the record — the record is species-free;
  profiles are where species lives. That separation is the whole
  architecture in one sentence.

### 7.3 Masters and visemes as data

Masters and visemes are authored **last and cheapest**: weight tables
(§3, §5) entered as `"kind": "vector"` records, then QA'd by the
only test that matters for a vector — render every master at
25/50/100 on every species preset and read the faces (silhouette +
read test: can a viewer name the emotion with the UI hidden?). A
master that fails the read test gets its weights re-tuned, never a
new slider. EF's entire commercial proof (ELDRITCH_FOUNDRY §3) is
that this layer, tuned well, outperforms part inventory; budget the
tuning passes accordingly — masters are few, and they are the face
of the product.

---

## 8. Summary counts

| Thing | Count |
|---|---|
| Master emotion sliders | **7** (Happy, Angry, Threat, Fearful, Surprised, Sad, Disgusted) + 1 flagged variant (Threat-defensive) |
| Fine sliders | **24** (brow 3 · lids/cheeks 4 · nose/muzzle 3 · lips 7 · jaw 3 · ears 4) |
| Viseme shapes | 11 spoken + Rest |
| Sliders carrying the asymmetry block | 16 of 24 |
| Expression sliders on the skull layer | **0** |

*End of spec. Build order note: fine sliders author alongside the
base head v2 (the muscle layer must carry named muscle bodies for
§7.1 step 1 to work — that requirement is hereby part of the v2
head's acceptance criteria), masters after the first species fits,
visemes with the first speech-animation work.*
