# Brow Study — Supraorbital Spectrum & Slider Design for AnthroForge

*Focused study, Nov 12, 2026. Joe's direction: "look at brow size, such as
neanderthal, and so on." The brow is currently the most under-specced signal on
the head: `species-head-spec.md` carries one slider, **BrowRidge** ("ridge
index," neutral 0.40, span 0.40), and `preset-orc-bara.md` leans on it hard
(BrowRidge **+90**, from a target "ridge index" of 0.75). This study measures
the real brow spectrum — hominids, great apes, and the anthro-relevant
mammals — assigns each component to its anatomical layer (Joe's
skull → muscle → tissue rule), and replaces the single slider with a
decomposed set whose ranges are anchored to published craniometry.*

*Conventions: **[S]** sourced (citation in §7), **[D]** derived arithmetically
from sourced numbers, **[E]** estimate / art-directed — an informed design
target with no direct measurement behind it. Estimates are never presented as
measured fact. Head proportions are ratios to head length **L** where the
implementation needs a scale-free number.*

---

## 0. Verdicts up front

1. **"Brow size" is at least four independent variables, not one.** Anterior
   projection, vertical thickness, continuity (split arches ↔ unbroken
   torus), and shelf/overhang vary independently across the spectrum — the
   orangutan is the standing proof: non-trivial glabellar bone thickness in
   old comparative tables, yet a brow that modern anatomy texts describe as
   weak or absent, because its *projection and relief* are low. Any single
   "ridge index" conflates them and will misbuild at least one end of the
   range.
2. **On the calibrated BrowProjection scale proposed here (§5.1), classic
   Neanderthals (Krapina) land at +100, late Neanderthals (Vindija) at +56,
   and the gorilla at ≈ +150 [E]** — extrapolated past the hominin chord
   data, flagged as such. The orc belongs at **≈ +135 [E]**: past any
   Neanderthal, just under gorilla.
3. **The orc spec's BrowRidge +90 does NOT survive as a literal
   BrowProjection.** +90 on the new scale sits between Vindija (+56) and
   Krapina (+100) — a strong Neanderthal, short of the gorilla-anchored orc
   brief. It survives only decomposed (§6.2): BrowProjection +135,
   BrowThickness +85, BrowContinuity +100, BrowShelf +90. The "+90" may be
   kept as a legacy macro label; it must not remain a deformation value.
4. **The species spec's BrowRidge values do not transfer as projection at
   all** (§6.1). Canids and felids have no torus; their visible "brow" is a
   frontal-sinus ridge, an orbit-rim/frontal-depression read, muscle
   (notably the dog's inner-brow raiser), and fur markings. Their
   BrowProjection equivalents are all *negative* — below the modern-human
   zero. Replacement vectors are given in §6.1.
5. **Layer rule:** the heavy end of the brow is **bone** (frontal torus);
   the *expression* end is **muscle** (corrugator/procerus lower and knit
   the brow; frontalis raises it — the muscles are only ~1–2 mm thick and
   create no Neanderthal-scale mass); the *finish* is **tissue** (skin +
   brow fat pad, ~3–9 mm total over the landmark). A scowl is not a torus,
   and padding is not bone. Each slider in §5 names its layer.

---

## 1. The hominid spectrum — measured

### 1.1 The one comparable dataset: Smith & Ranyard chords

Almost everything quantitative in this section comes from one measurement
protocol, which is what makes the numbers comparable: Smith & Ranyard's
(1980) supraorbital chords, as tabulated by Ahern, Lee & Hawks (2002) for
Krapina and Vindija Neanderthals against Central European Upper Paleolithic
and Neolithic (Altendorf) modern humans. Three parasagittal planes —
**medial**, **midorbit**, **lateral** — each get a *projection* chord and a
*vertical thickness* chord (thickness = anterior orbital margin to the
superior aspect of the torus). This study calibrates on the **midorbit
projection** chord: it is the best-sampled, and midorbit is where the brow
bar reads visually.

> **Metric honesty:** these chords are standardised fossil measurements of
> the torus as a whole. They are **not** "millimetres the brow sticks out
> past the eyeball," and no slider should be documented as if they were.
> They are used here as an *index with real units* — an ordering with
> published means and standard deviations. Ahern et al. report absolute
> chords, not chords normalised by skull length; the samples are adult
> hominins of broadly similar cranial size, so the ordering is usable, and
> §5.1 gives the implementation a length-normalised form.

### 1.2 Measured spectrum table

BrowProjection values are computed with the §5.1 calibration
(`100 × (midorbit projection − 12.5 mm) / 11.4 mm`); the Altendorf recent
sample is the zero by definition and the Krapina mean falls at +100 by
construction of the span.

| Form / sample | Midorbit projection (mm) | Midorbit thickness (mm) | BrowProjection [D] | Continuity | Source |
|---|---|---|---|---|---|
| Recent modern humans (Altendorf, Neolithic) | **12.5 ± 3.5** (n=32) | 6.5 ± 1.3 | **0** (zero anchor) | Split: medial superciliary arches + central ridge + lateral trigonum as separate components; glabellar hiatus common | Ahern et al. 2002, Table 2 [S] |
| Upper Paleolithic modern humans (Central Europe) | **15.7 ± 4.2** (n=8) | 6.1 ± 1.1 | **+28** | Robust but already divided in plan; midorbit relatively reduced (mid/lat projection index 78.1) | Ahern et al. 2002 [S] |
| Early *H. sapiens*, Skhul/Qafzeh sample | **20** (sample mean) | — (central torus thickness for 3 Skhul crania averages 11.1 mm, a different chord — see §1.3) | **+66** | Variable: glabellar prominence + superciliary arch from substantial (Qafzeh 6, 3) to slight (Qafzeh 9) | Curnoe et al. 2012 [S]; PNAS 2009 survey [S] |
| Jebel Irhoud early *H. sapiens* (~300 ka) | not published on this protocol | thick (central torus below the Bodo group's 17.1 mm mean; exact value not carried here) | *not assigned* | **Continuous supraorbital torus** — the trait that marks Irhoud as archaic against later, discontinuous, *H. sapiens* | Hublin et al. 2017 reports [S-qual.]; PNAS 2009 survey [S] |
| Late Neanderthals (Vindija) | **18.9 ± 2.9** (n=6) | 8.9 ± 0.8 | **+56** | Continuous, double-arched; metrically between Krapina and moderns on most measures | Ahern et al. 2002 [S] |
| Classic Neanderthals (Krapina) | **23.9 ± 1.2** (n=11) | 10.7 ± 1.8 | **+100** (span anchor) | Continuous, uniformly thick, double-arched, no glabellar depression | Ahern et al. 2002 [S]; Athreya 2012 [S-qual.] |
| Archaic *Homo* (Bodo group; Kabwe 1) | not on this protocol | **central torus thickness averages 17.1 mm** (Bodo group) — a different chord, not comparable to the midorbit column | *not assigned* | Massive continuous torus; Kabwe's ridge is far larger than any spatial/mechanical minimum (§3) | PNAS 2009 survey [S]; Godinho et al. 2018 [S] |

Supporting chords from the same table (Ahern et al. 2002), for builders who
want the full profile rather than the midorbit point alone — lateral
projection: Krapina 24.3 ± 1.4, Vindija 22.1 ± 1.8, UP 19.8 ± 3.2, Altendorf
17.0 ± 3.1; medial projection: Krapina 19.8 ± 2.3, UP 11.5 ± 3.7, Altendorf
9.8 ± 2.8. Note the *shape* signal inside the numbers: the Neanderthal torus
is nearly level across its width (midorbit/lateral projection index 99.6 at
Krapina), while modern samples dip at midorbit (Altendorf 72.7, UP 78.1).
That dip — not raw size — is most of what BrowContinuity (§5.2) has to
encode.

### 1.3 Other published measures — deliberately NOT on the scale

Mixing metrics is how brow numbers turn into mush. These are real, sourced,
and useful — for thickness and plausibility checks — but they are different
measurements and are kept off the BrowProjection axis:

- **Vertical torus thickness, archaic range 10–17 mm** for Steinheim, most
  Sima de los Huesos, and Neanderthal tori; individual Sima fragments at
  11.0 mm and 7.7 mm (Walker & Gibert, Internet Archaeology 5) [S].
- **Guattari / Circeo C4 torus height:** medial 15.8 mm, maximum 18.7 mm,
  lateral 15.4 mm; described as thick, wide, continuous, no glabellar
  depression (Research Square preprint) [S].
- **Dmanisi D3444:** brow maximum thickness ≈ 12 mm, 10 mm at mid-orbit,
  lateral portion thinner and bar-like (Anatomical Record, 2006) [S].
- **Historical glabellar bone thickness** (Science Progress, Vol. 3, via
  Wikisource — an old source, quoted as historical ranges, not modern
  craniometry): Neanderthal/Spy 24–30 mm; modern European seldom over
  20 mm; **gorilla 30–35 mm; chimpanzee 25–28 mm**; orangutan 16–20 mm;
  gibbon 12–14 mm [S-historical]. Its ordering (gorilla > Neanderthal ≈
  chimp > modern) is the directional support for placing the gorilla past
  +100 in §2 — it is not the calibration.
- **Bodo-group central torus thickness 17.1 mm** and **Skhul 11.1 mm**
  (PNAS 2009 survey of Middle/later Pleistocene hominins) [S] — central
  chords; they corroborate that
  early *H. sapiens* brows were genuinely thick even where the torus was
  already breaking up.

### 1.4 The modern end: reduction, split, dimorphism

- **The split is the derived trait.** Athreya's frontal-bone review (2012):
  the Neanderthal condition is a uniformly thick, double-arched, continuous
  torus; the modern condition is *separation* into medial (superciliary
  arches), central (supraorbital ridge) and lateral (supraorbital trigonum)
  components with virtual absence of supraorbital relief — and early modern
  humans (Jebel Irhoud, Skhul, Qafzeh) still had thick, large brow ridges.
  The reduction is a gradient across ~300 ka, not a species switch. Design
  consequence: "early human" is a legitimate mid-range preset, not a
  rounding error between Neanderthal and modern.
- **Sexual dimorphism is real and brow-led.** Del Bove et al. (2023, 228
  sex-known crania, 3D landmark mapping): the glabellar and supraciliary
  regions are among the most sexually dimorphic parts of the cranium (the
  central supraorbital region alone classifies sex at ~76% in shape space).
  The forensic contrast: gracile pattern = sharp thin supraorbital margin,
  smoothed glabella **without anterior projection**; hypermale pattern =
  rounded/blunted margin, **massive glabella with marked anterior
  projection**. Ahern et al.'s samples are sex-mixed and their paper is
  largely *about* that bias problem, so **no honest male/female mm offset
  can be read out of §1.2** — the sex offsets in the §5 reference vectors
  are [E] design values in the sourced direction, and are labelled so.
- **Brow position is dimorphic too — in soft tissue.** Surgical/aesthetic
  literature (Zins et al. 2022 and the Westmore criteria it reviews): the
  male brow sits **at** the supraorbital rim, flatter and fuller; the
  female brow sits **above** the rim (on average ~2–3 mm higher; ≥5 mm
  above the rim is the cited female aesthetic ideal), arched with its apex
  toward the lateral third. This is the *hair-bearing brow line*, not the
  bone — it calibrates BrowPosition (§5.4), and it does not fossilise:
  no position values are claimed for Neanderthals or apes beyond "the bar
  sits on the rim."
- **Age:** supraorbital development continues remodelling into adulthood
  and older age in at least some populations (Russell 1983, via Ahern et
  al.), so older samples read more robust — one of the bias scenarios the
  Vindija paper had to exclude. Separately, the *soft* brow descends with
  age, most at the lateral end (clinical sources put lateral drop at
  roughly 2–3 mm per 20 years — a soft, clinic-grade figure), producing
  lateral hooding. Brow size alone is therefore a weak age signal; brow
  *position + hooding* is the usable one (§5.4, §5.6).

---

## 2. Great apes and the mammal range

| Form | Brow construction | BrowProjection | BrowContinuity | Source / tag |
|---|---|---|---|---|
| Gorilla (adult male) | Supraorbital tori linked medially by a glabellar ridge into one unified **torus frontalis**; orbits overhung by the massive bar; pronounced frontal sinuses. Reference specimen: cranial length incl. brow 221 mm, external biorbital breadth 150 mm | **+150 [E]** — extrapolated past the hominin chord range; direction supported by the historical glabellar-thickness ordering (gorilla 30–35 mm > Neanderthal 24–30 mm) [S-historical] | **+100** [S-qual.] | 3B Scientific gorilla skull manual (SNSB Munich) [S]; ScienceDirect primate skull overview [S-qual.] |
| Chimpanzee | Large continuous bar of bone set off from the braincase by a distinct **supratoral sulcus**; brow is large relative to a small braincase (~367 cc) | **+120 [E]** — between Krapina and gorilla; historical thickness range (25–28 mm) sits at the Neanderthal level | **+90** [S-qual.] | ScienceDirect *Pan* overviews [S-qual.]; historical table [S-historical] |
| Orangutan | Brow ridges **missing or only weakly developed** in modern anatomy accounts, despite the historical table's 16–20 mm glabellar thickness — the discrepancy is the lesson: thickness without projection/relief does not read as brow | **−20 [E]** | **−25 [E]** | ScienceDirect primate skull overview [S-qual.] vs historical table [S-historical] — tension flagged, not resolved away |
| Gibbon | Small; historical glabellar thickness 12–14 mm, lowest of the set | **−35 [E]** | **−40 [E]** | Historical table [S-historical] |

**Sagittal crest interaction.** In adult male gorillas (and chimps), a
sagittal crest rises from the parietals as **origin area for the
temporalis**; it grows with masticatory and neck musculature, not with the
brow. Brow and crest *co-vary* in big male apes — both track the same
robusticity complex — but they are different structures on different bones
(frontal vs parietal) driven by different muscles (none vs temporalis).
Design rule: **BrowProjection must never drive the crest automatically.**
Couple them only inside presets (orc §6.2: `crest_sagittal` enters when
BrowProjection ≥ +120 and JawDepth is also high [E]), and expect the
temporalis fan that justifies a crest to *pinch the forehead* — in the orc
spec that pinch is ForeheadWidth −35, and it narrows the brow band the
torus is built on. A wide brow bar on a pinched forehead is a contradiction
the builder should flag, not smooth over.

**The anthro-relevant mammals have no torus.** What reads as "brow" in the
species spec's animals is three other things:

- **A frontal-sinus eminence.** In the dog, the superciliary ridge is an
  eminence on the frontal bone *caused by the projection of the frontal
  sinus*, the two ridges joined by the glabella (Collinge 1896) [S]. It is
  a modest bony undulation, not a bar — and the dog's supraorbital margin
  is *incomplete*, with a very short zygomatic process [S]. The cat's
  margin is complete with a prominent frontal zygomatic process [S]; the
  lion's frontal carries a **deep longitudinal depression** dorsally and an
  incomplete bony orbit (Mohamed 2019) [S] — the felid "heavy brow" read
  is that depression plus the orbit rim plus fur, i.e. mostly **shelf and
  shadow**, not projection. The wolf's frontal is slightly concave and its
  external sagittal crest is very well developed (USAMV 2013 comparative
  neurocranium study) [S] — crest, again, is not brow.
- **Muscle that moves.** Kaminski et al. (2019, PNAS): the levator anguli
  oculi medialis (LAOM), which raises the *inner* eyebrow, is uniformly
  present in domestic dogs but only scant fibres in wolves; dogs produce
  the inner-brow raise more often and at higher intensity. The most
  expressive "brow" in our whole species list is a few fibres of muscle
  and zero additional bone. In AnthroForge terms that is BrowScowl run in
  reverse (a medial *raise*), plus eyelid work — never BrowProjection.
- **Pigmentation.** The tan "pips" above the eyes in black-and-tan dogs
  (Rottweiler, Doberman, Bernese) are agouti tan-point markings — a coat
  pattern, not anatomy. They belong to the material/marking layer
  alongside felid forehead striping. Any preset that raises BrowProjection
  to imitate eyebrow *markings* is building bone where the animal has
  dye.

---

## 3. What the brow signals — and what it doesn't

- **Dominance / menace is the best-supported read.** Godinho, Spikins &
  O'Higgins (2018) virtually reduced Kabwe 1's browridge and found it is
  **much larger than the minimum required to join orbits to frontal bone**
  and that browridge size has **little impact on biting mechanics** —
  i.e. the big archaic brow is not structural necessity. Their proposal:
  a pronounced, permanent ridge is a **dominance/aggression signal**,
  traded in modern humans for a vertical forehead and highly mobile
  eyebrows that display subtle *affiliative* signals instead. Browridges
  also scale allometrically with face/cranial size. Design moral: brow
  exaggeration past anatomy is legitimate character design — the trait
  evolved partly *as* exaggeration — but the menace read is completed by
  the muscle layer (lowered, knitted brow, §5.6) and by shelf shadow
  (§5.3), not by bone alone. A torus worn high and open reads "archaic";
  the same torus lowered reads "threat."
- **Masculinity:** sourced (§1.4) — glabella/supraciliary form is one of
  the strongest cranial sex signals, in the direction bigger/more
  projecting = male-typical. Treat it as a *dial with overlap*, not a
  binary: Vindija-vs-Krapina shows within-species sample spread of the
  same order as the sex effect.
- **Age:** weak from size (§1.4), stronger from position and lateral
  hooding. An "old" read = BrowPosition slightly down, lateral segment
  down more, BrowPadding redistributed into hood — not a bigger torus.
- **"Primitive":** a perceptual shorthand the audience brings from the
  fossil gradient (§1.2), not a biological ranking — the study uses
  "archaic" for the anatomy and reserves the signal language for what a
  viewer reads. Worth one line in the doc because character creators
  trade in exactly that shorthand, knowingly.

---

## 4. Layer anatomy — which layer owns which part of the brow

Per Joe's rule (skull → muscles → tissue; the tissue surface is the
deliverable, and a surface merely wrapped over bone reads skeletal), the
brow decomposes as follows. Forehead layer stack, superficial to deep:
skin, subcutaneous tissue, galea/muscle layer, loose areolar tissue,
periosteum, frontal bone (surgical anatomy of the forehead) [S].

**Bone (skull layer) — owns the mass.** The frontal torus / superciliary
arches / glabella are frontal bone, expanded in archaic forms by the
frontal sinus; the supraorbital margin, the lateral trigonum, the
post-toral (supratoral) sulcus behind the bar, and the slope of the
frontal squama above it are all bone. Every millimetre of §1.2's chords
lives here. Sliders: BrowProjection, BrowThickness, BrowContinuity
(bone-led), BrowShelf (bone-led).

**Muscle (muscle layer) — owns position and expression, not mass.**
Frontalis is the brow's **only elevator** (and is deficient laterally,
which is why the lateral brow drops first with age). The depressors:
corrugator supercilii — measured at only **1.62 ± 0.4 mm thick**, 29.2 mm
long, 12.6 mm wide (cadaver study, Surgical & Radiologic Anatomy) [S] —
originates on the medial superciliary arch and pulls the brow down and
in: it is the scowl. Procerus depresses the medial brow; depressor
supercilii and the orbital part of orbicularis oculi depress the medial
and lateral brow respectively. Total muscle contribution to brow *bulk*
is a few millimetres at most; its contribution to brow *meaning* is most
of it. Sliders: BrowPosition (shared with tissue), BrowScowl.

**Tissue (tissue layer) — owns padding, hood, and finish.** Measured
soft-tissue depths over the brow region are millimetric and variable:
forensic facial-tissue tables put total soft tissue at the **supraorbital
landmark at ≈ 4.5–8.25 mm** and at the **glabella at ≈ 3.2–6.25 mm**
across populations and sexes (Rhine & Campbell; Suzuki; Phillips &
Smuts; Sahni et al.) [S]. The brow fat pad (ROOF, retro-orbicularis oculi
fat) is described in surgical anatomy as ≈ **5 mm thick** over ~1 cm
vertical extent [S]; one ultrasound study reports much thinner point
values (≈ 1.3–1.4 mm) at mid-pupillary/lateral-canthus points — different
points and methods; both are reported here rather than averaged into a
fiction. A 2025 ultrasound study (238 volunteers) measured the component
layers directly above the brow arch: skin 0.95 mm (male) / 0.73 mm
(female), frontalis 0.35 / 0.25 mm, subcutaneous layers ~0.7–1.4 mm [S].
Design conclusion: in a modern human the *visible* brow is a few
millimetres of tissue over a small bony arch — tissue can plausibly
double the apparent brow. At Neanderthal-and-up settings the bone is
10–24 mm of chord and tissue is a finish coat: **never let BrowPadding
erase a torus** (the orc spec's §2.3 rule, now with numbers behind it),
and never use BrowPadding to *fake* a torus on a gracile head — the
silhouette gives it away at the sulcus, which padding cannot carve.

**Hair / markings (material layer) — owns the drawn brow.** Eyebrow hair
position, density and angle; canid tan pips; felid forehead stripes. No
geometry. BrowPosition moves the hair line *with* the tissue it sits in;
marking placement should track BrowPosition so pips/stripes stay glued
to the brow they decorate.

---

## 5. Slider design — the brow set

Replace species-spec slider #25 (BrowRidge) with **seven sliders**:
four bone-led, one positional, one tissue, one muscle/expression. The
Eyes/Brow group becomes EyeSize, EyeSpacing, EyeForwardness + the seven
below (head total 25 → 31 sliders). All use the house −100…+100
convention except BrowProjection, whose range is sized around its extreme
anchor the way EarHeight was sized around the fennec.

### 5.1 BrowProjection — bone

*What it does:* moves the brow band (medial + midorbit + lateral segments)
forward on the skull layer and scales the torus's anterior chord;
post-toral sulcus stays registered to the squama so projection reads as
bar growth, not forehead translation.

- **Range:** −50 … +150. **Zero:** recent modern human mean.
- **Calibration [D from S]:** `value = 100 × (P − 12.5) / 11.4`, where P =
  Smith & Ranyard midorbit projection chord in mm (Altendorf 12.5 mm = 0;
  Krapina 23.9 mm = +100).
- **Anchors:** recent modern **0** [S] · Upper Paleolithic **+28** [D] ·
  Skhul/Qafzeh **+66** [D] · Vindija **+56** [D] · Krapina **+100** [D] ·
  chimp **+120** [E] · **gorilla +150 [E]** (implied chord ≈ 29.6 mm) ·
  **orc +135 [E]** (implied ≈ 27.9 mm).
- **Implementation form (scale-free):** at the AnthroForge base head,
  target chord ≈ L × (0.066 + 0.00060 × value) — 0 ≈ 0.066 L, +100 ≈
  0.126 L, +150 ≈ 0.156 L [D, using ~190 mm hominin cranial lengths as
  the normaliser; treat the normaliser itself as approximate].
- **Layer:** skull. **Do not** couple to EyeSize or crest (§5.7).

### 5.2 BrowContinuity — bone

*What it does:* morphs the brow band's crosswise profile from three
separate components (superciliary arch / central ridge / trigonum, with a
glabellar dip and a midorbit waist) to one level, unbroken bar; fills the
glabellar dip and evens medial↔midorbit↔lateral height.

- **Range:** −100 … +100. **Zero:** the common modern mixed pattern —
  arches present, weakly bridged.
- **Anchors:** gracile modern **−75** [E] · pooled modern **−35** [E] ·
  robust modern **−10** [E] · early *H. sapiens* (Skhul/Qafzeh) **+35**
  [E on S-qual. variability] · Jebel Irhoud **+80** [S-qual.: continuous
  torus] · Vindija **+85** [S-qual.] · Krapina **+100** [S-qual.] ·
  chimp **+90** [S-qual.] · gorilla **+100** [S-qual.: torus frontalis] ·
  orangutan **−25** [E] · orc **+100** [E].
- **Layer:** skull. Continuity is a *shape* axis, independent of size: a
  small continuous bar (Jebel Irhoud direction) and a huge split brow are
  both buildable, and both occur in the record's logic.

### 5.3 BrowShelf — bone-led, tissue-softened

*What it does:* the ledge geometry — how far the brow's inferior edge
overhangs the orbit, how deep the post-toral sulcus cuts behind the bar,
and how recessed the orbital opening sits beneath it. This, more than
projection, is what makes eyes read **deep-set** and puts the eye in
shadow.

- **Range:** −100 … +100 (dimensionless ledge/sulcus index; no published
  chord isolates it, so anchors are ordered design values on sourced
  morphology — labelled accordingly). **Zero:** mild modern ledge.
- **Anchors:** gracile modern **−55** [E] · pooled modern **−20** [E] ·
  robust modern **+10** [E] · Upper Paleolithic **+25** [E] · Vindija
  **+65** [E] · Krapina **+85** [E] · chimp **+80** [E on S-qual.
  sulcus] · gorilla **+100** [E] · orc **+90** [E]. Felid shelf reads
  (§6.1) are this slider doing honest work where projection cannot.
- **Layer:** skull (ledge + sulcus), tissue may soften the edge by at
  most the BrowPadding depth.

### 5.4 BrowPosition — muscle/tissue (the "BrowHeight")

*What it does:* vertical placement of the soft brow line relative to the
supraorbital rim — the hair-bearing brow and its fat pad, riding over
whatever bone is present. Positive = higher.

- **Range:** −100 … +100 ≙ **−5 … +5 mm** at human scale
  (implement as ±0.028 L). **Zero:** brow line at the rim — the male
  pattern [S].
- **Anchors:** adult male **0** [S] · adult female **+50** (≈ +2.5 mm,
  the sourced average offset) [D from S] · high aesthetic brow **+100**
  (≥ +5 mm) [S] · aged/lateral ptosis **−40**, lateral segment **−70**
  [E on soft clinical figures]. Fossil/ape bone bars sit on the rim by
  construction; no soft-tissue position is claimed for them.
- **Layer:** tissue position over muscle tone (frontalis resting length).
  Independent of BrowProjection: a Neanderthal bar with a high soft brow
  is buildable and reads "surprised archaic," which is correct — the
  axes really are separate.

### 5.5 BrowThickness — bone

*What it does:* vertical thickness of the torus (orbital margin to
superior aspect), the chord that makes a brow read *tall* rather than
*far-forward*. Kept separate from projection because the fossil table
shows them moving semi-independently (Upper Paleolithic thickness is at
the recent level — 6.1 vs 6.5 mm — while its projection is +28).

- **Range:** −100 … +100; anatomical safe range ≈ −60 … +100.
- **Calibration [D from S]:** `value = 100 × (T − 6.5) / 6.5`, T =
  midorbit vertical thickness in mm (Altendorf 6.5 mm = 0).
- **Anchors:** recent modern **0** [S] · Upper Paleolithic **−6** [D] ·
  Vindija **+37** [D] · Krapina **+65** [D] · chimp **+75** [E] ·
  gorilla **+100** [E] (≈ 13.0 mm) · orc **+85** [E] (≈ 12.0 mm — inside
  the sourced archaic 10–17 mm band, §1.3).
- **Layer:** skull.

### 5.6 BrowPadding — tissue

*What it does:* total soft-tissue depth over the brow band (skin +
subcutaneous + ROOF), including redistribution into an upper-lid hood at
high values with low BrowPosition.

- **Range:** −100 … +100 ≙ total supraorbital soft tissue **3 … 9 mm**,
  0 = 6.0 mm [D, centred on the sourced forensic range §4].
- **Anchors:** lean modern **−25** (≈ 4.5 mm) [D from S range] · full
  modern **+35** (≈ 7.5 mm) [D from S range] · bulky/bara styling
  **+75** (≈ 8.5 mm) [E]. **No values are assigned to fossils or apes** —
  soft tissue does not fossilise and ape brow fat is unmeasured in this
  pass; presets for them choose padding as styling and must say so.
- **Layer:** tissue only. Hard rule from §4: padding softens, it never
  creates or erases a sulcus.

### 5.7 BrowScowl — muscle (expression-coupled shape)

*What it does:* resting corrugator/procerus engagement: medial brow
pulled down and in, brow angle steepened, glabellar furrow hinted in the
tissue above the muscle. Negative values run the axis the other way —
frontalis raise, open brow (the direction the dog's LAOM exploits,
§2).

- **Range:** −100 … +100. **Zero:** neutral rest.
- **Anchors:** open/raised **−60** [E] · resting menace (orc) **+35**
  [E] · full knit **+85** [E] (≈ 4 mm medial depression at human scale).
- **Layer:** muscle, with tissue furrow as a secondary effect. This is
  the slider that turns an archaic brow into a *threatening* one (§3);
  presets should set it deliberately, never inherit it from projection.

### 5.8 Interactions and builder checks

- **EyeSize / deep-set eyes.** The eyeball does not shrink when the brow
  grows. Apparent eye size falls because BrowShelf + BrowProjection
  occlude and shadow the orbit. Rule: when Shelf ≥ +60 and Projection
  ≥ +80, take the "small eye" read from **eyelid aperture** (−10 to −20
  aperture [E]) and shelf shadow, *not* from EyeSize. The orc is the
  worked case: its EyeSize −40 is a real orbit ratio (0.11 L, orc spec
  §2.1) and stays; the deep-set read is Shelf +90's job. Compensating
  for a torus by enlarging eyeballs breaks the skull.
- **EyeSpacing / ForeheadWidth.** A continuous bar (Continuity +100)
  spans the interorbital width but does not move the eyeballs; the brow
  band's width is bounded by the ForeheadWidth deformation. Orc check:
  ForeheadWidth −35 (temporalis pinch) + Continuity +100 is legal — the
  bar is *narrow and unbroken*. If a build needs the bar wider than the
  forehead region, the forehead is wrong, not the brow.
- **StopAngle.** A heavy brow on a sloping forehead flattens the visible
  stop. Orc StopAngle −25 holds, but implement it as forehead slope +
  shelf; BrowProjection must not write into the stop region, or every
  high-brow preset inherits a felid profile.
- **Sagittal crest / CraniumHeight.** Independent (§2). Preset-level
  coupling only.
- **Jaw robusticity.** Brow and jaw co-signal (§3) and the orc couples
  them, but the sliders stay independent — the lion (§6.1) is a heavy
  jaw with essentially no torus, and it must remain buildable.
- **Markings.** Tan pips, forehead stripes and eyebrow hair track
  BrowPosition (§4); they never feed back into geometry sliders.

### 5.9 Reference vectors (for preset authors)

Order: **Projection / Thickness / Continuity / Shelf / Position /
Padding / Scowl.** "—" = not claimable for that form.

| Preset | Vector | Notes |
|---|---|---|
| Recent modern, pooled | 0 / 0 / −35 / −20 / +25 / 0 / 0 | Zero point of the system |
| Recent modern, gracile female-type | −20 / −25 / −75 / −55 / +50 / −10 / −10 | P/T offsets [E] in the sourced dimorphic direction (§1.4) |
| Recent modern, robust male-type | +15 / +20 / −10 / +10 / 0 / +10 / +5 | P/T offsets [E], same caveat |
| Upper Paleolithic | +28 / −6 / +10 / +25 / — / — / — | Fossil: bone sliders only |
| Vindija late Neanderthal | +56 / +37 / +85 / +65 / — / — / — | Fossil: bone sliders only |
| Krapina classic Neanderthal | +100 / +65 / +100 / +85 / — / — / — | The +100 anchor |
| Gorilla (adult male) | +150 / +100 / +100 / +100 / — / — / — | P/T [E] (§2); continuity [S-qual.] |
| **Orc (bara)** | **+135 / +85 / +100 / +90 / −20 / +10 / +35** | §6.2; padding low on purpose — skin stays thin over the bar |

---

## 6. Revision verdicts on the existing specs

### 6.1 `species-head-spec.md` — BrowRidge is retired, values do not hold

The old slider's "ridge index" (neutral 0.40, span 0.40) was never tied
to a published measure, and §1–§2 show it conflates projection,
thickness, continuity, shelf, and the fur/muscle/marking read. **As
BrowProjection, none of the seven species values hold** — every one of
these animals sits *below* the modern-human zero on the torus axis,
because none of them has a torus. Their old numbers were honestly
capturing *visual brow emphasis*; the replacement vectors below keep
that emphasis and put it on the sliders that actually produce it
(Shelf, Scowl, Padding). All values [E] — design-equivalents on a
hominin-calibrated scale, not cross-species measurements; no
Smith & Ranyard-protocol data exists for these animals.

| Species | Old BrowRidge | New vector (Proj / Thick / Cont / Shelf / Pos / Pad / Scowl) | Where the old read actually lives |
|---|---|---|---|
| Wolf | +15 | −25 / −20 / −20 / +5 / −10 / +10 / +10 | Slight frontal concavity + stop; crest is separate |
| Red fox | −5 | −35 / −30 / −35 / −10 / 0 / 0 / 0 | Near-flat frontal line |
| Fennec | −15 | −45 / −40 / −50 / −20 / +10 / −10 / −10 | Open, raised, gracile — the anti-torus |
| Lion | +20 | −20 / −15 / −25 / **+20** / −10 / +15 / +20 | Frontal longitudinal depression → shelf + shadow (§2) |
| Panther (leopard) | +10 | −25 / −20 / −30 / +15 / −5 / +10 / +15 | Same felid mechanism, weaker |
| Cat | −20 | −40 / −35 / −55 / −5 / +15 / +5 / −5 | Complete orbit margin, no bar |
| Dog | +10 | −25 / −25 / −30 / 0 / 0 / +15 / +5 | Frontal-sinus eminence (bone, small) + LAOM muscle + pips (material) — three layers, one old number |

If a compatibility shim is unavoidable for old preset files, apply it
**only to humanoid presets** (Projection ≈ 1.5 × BrowRidge, Continuity ≈
min(100, 1.1 × BrowRidge)) and never to the animal table above — the
shim would push a wolf's brow *past* a modern human's, which is exactly
backwards.

### 6.2 `preset-orc-bara.md` — the +90, decomposed

- §2.1's "Brow ridge index 0.75" and §2.2's **BrowRidge +90 are
  replaced** by: **BrowProjection +135 [E], BrowThickness +85 [E],
  BrowContinuity +100, BrowShelf +90 [E], BrowPosition −20 [E],
  BrowPadding +10 [E], BrowScowl +35 [E].** On the measured scale, +90
  as projection = a 22.8 mm midorbit chord — Krapina-class Neanderthal.
  The orc brief is gorilla-class; +135 (≈ 27.9 mm) is the honest
  placement, 15 points under the gorilla anchor to leave the animal
  its crown.
- §2.1's claim that the orc brow is "the chart's maximum — nothing real
  exceeds it" **does not hold** under the new calibration: the gorilla
  anchor (+150) exceeds the orc, and Kabwe-class thickness exceeds the
  orc's on its own chord (§1.3). Correct the line to "near-gorilla,
  past every Neanderthal."
- §2.4's `brow_torus` variant trigger changes from "BrowRidge > +70" to
  **BrowContinuity ≥ +80 AND BrowProjection ≥ +80** — continuity is
  what the variant enforces; size alone never needed it.
- §2.3's tissue rule ("skin is thinnest over the bar") is preserved as
  BrowPadding +10 — low against the head's otherwise thick tissue —
  and §5.4's "EyeSize −40 under BrowRidge +90" becomes "EyeSize −40
  under BrowShelf +90" (§5.8: the deep-set read was always the shelf).
- §6 (honesty box) already flags BrowRidge 0.75 as load-bearing and
  least-sourced; this study is the re-derivation it asked for. The
  number's *role* survives — the brow is still one of the orc's two
  defining dials — its value and its decomposition do not.

---

## 7. Sources

- Ahern, Lee & Hawks 2002, "The late Neandertal supraorbital fossils
  from Vindija Cave, Croatia: a biased sample?", *Journal of Human
  Evolution* 43:419–432 — Smith & Ranyard (1980) chord definitions and
  Table 2 means/SDs used throughout §1. (faculty.ucr.edu PDF.)
- Curnoe et al. 2012, "Human remains from the Pleistocene-Holocene
  transition of Southwest China…", *PLoS ONE* 7(3):e31918 — Table 5
  supraorbital projection/thickness comparisons incl. the Skhul/Qafzeh
  (WAEHS) and Neanderthal sample means.
- "Middle and later Pleistocene hominins in Africa and Southwest Asia",
  *PNAS* 106 (2009), Out of Africa special feature — central torus
  thickness (TOR): Bodo group 17.1 mm mean; Skhul 11.1 mm mean;
  Skhul/Qafzeh brow variability.
- Athreya 2012, frontal-bone review, *Journal of Anthropological
  Sciences* 90:59–80 — torus vs split-component morphology.
- Godinho, Spikins & O'Higgins 2018, *Nature Ecology & Evolution*
  2:956–961 — Kabwe 1 virtual manipulation; spatial/mechanical
  insufficiency; social-signalling hypothesis.
- Del Bove et al. 2023, *Scientific Reports* 13:16847 — cranial sexual
  dimorphism, glabellar/supraciliary regions.
- Zins et al. 2022, *Clinics in Plastic Surgery* 49:339–348 — brow
  position aesthetics (Westmore criteria): male at rim, female above.
- Walker & Gibert, Sima de las Palomas, *Internet Archaeology* 5 —
  archaic torus thickness 10–17 mm. Guattari/Circeo C4 torus heights
  (Research Square preprint). Dmanisi D3444 brow thickness,
  *Anatomical Record* (2006).
- Historical comparative glabellar thickness table, *Science Progress*
  Vol. 3 (via Wikisource) — flagged historical wherever used.
- 3B Scientific gorilla skull manual (SNSB Munich specimen) — torus
  frontalis construction, sagittal crest as temporalis origin, specimen
  dimensions. ScienceDirect primate-skull overviews — Pan/Gorilla
  overhung orbits, Pongo brow weak/absent, chimp supratoral sulcus.
- Collinge 1896, dog skull manual (archive.org) — superciliary ridge as
  frontal-sinus eminence. Comparative neurocranium studies (USAMV 2013;
  Mohamed 2019, *J. Morphological Sciences* 36:174–181) — canid/felid
  orbit margins, wolf frontal concavity and crest, lion frontal
  depression.
- Kaminski et al. 2019, *PNAS* 116:14677–14681 — LAOM presence in dogs
  vs wolves; inner-brow raise.
- Forehead/brow soft-tissue anatomy: *Plastic Surgery Key*, Forehead
  chapter (layer stack; ROOF ≈ 5 mm); corrugator morphometry,
  *Surgical & Radiologic Anatomy* (1.62 ± 0.4 mm); forensic facial
  tissue-depth tables (Rhine & Campbell et al., via FBI archive);
  2025 ultrasound layer study, *Aesthetic Surgery Journal Open Forum*
  (238 volunteers).

*End of study. Companions: `species-head-spec.md` (§3.1 slider #25 is
superseded by §5 here), `preset-orc-bara.md` (§2 brow entries revised
per §6.2), `MAKEHUMAN_OMNIVERSAL.md` (slider-record format — the seven
brow sliders should be registered as semantic records with the §5
anchors as their provenance).*
