# Face Craft — Anthro/Furry Face Construction Beyond the Layered Head

*Learning agent B12, model-craft wave, Nov 12, 2026. Scope: construction
study + topology annotation. **No geometry was rebuilt.** Companions:
`species-head-spec.md` (37 shape sliders), `expression-system.md`
(24 fine expression sliders E1–E24 + 7 masters), `base-head-v3/`
(BUILD_NOTES.md, proportions.json, groups.json), `brow-study.md`.*

*Conventions: **[S]** sourced, **[D]** derived/measured by me on the
v3 GLB, **[E]** estimate / art-directed. All lengths in fractions of
L (nose tip → occiput = 1.0) unless stated. Rule IDs are F-##.*

*Method honesty: v3 topology numbers below are my own measurements on
`neutral_base_head_v3.glb` (positions welded at 1e-4; scripts in
`work/`). One measurement bug was caught mid-run — a BFS that read
loop indices instead of vertex indices produced an empty adjacency;
it was found because its result contradicted the edge census, fixed,
and re-run. The numbers quoted are from the corrected pass. Vertex-to-
vertex distances (nose seating) overestimate true surface distances on
a coarse mesh and are labelled as such.*

---

## 1. The muzzle is a stack of five structures, not a tapered box

The single biggest lesson from the anatomy side: a mammal muzzle is
five separately-built structures stacked along one axis, and each of
our muzzle sliders actually addresses a different one. Treating the
rostrum as one tapered block (what a loft gives you) is why procedural
muzzles read wrong even at correct proportions.

### 1.1 The stop — a ledge, not a bend

The stop is the angle where the nasal bridge meets the forehead,
"between the eyes", varying by breed/species from near-flat
(dolichocephalic canids) to a near-90° step (brachycephalic, many
felids) [S: veterinary anatomy flashcards; spec §2]. Construction-wise
it is a **ledge**: the dorsal profile changes slope discontinuously
because the frontal bone steps back from the nasal bones. On v3 the
ledge is real and measurable [D]: the dorsal midline profile's maximum
curvature sits at **z = −0.27 L** (just in front of the orbit station),
where profile slope jumps **0.65 → 2.81** — a >4× break, not a sag
(fig. `annotation_profile_stop.png`).

- **F-M1 — Give the stop its own edge loop.** A ledge needs a loop
  *on* the break line, with one support loop above and below, or
  StopAngle (#9) / StopDepth (#34) fields smear the step into a ramp
  and the profile goes "anteater" in one direction and "ski-jump" in
  the other. The loop must run temple-to-temple across the bridge,
  following the frontal–nasal suture line, not a horizontal ring of
  the head — on wide-cheeked species the break line curves.
- **F-M2 — Stop position is set by OrbitRise + the frontal block, not
  by pushing the muzzle.** The break sits where the frontal block's
  front face is; muzzle sliders move what hangs below it. v3's
  measured stop at z = −0.27 vs muzzle fraction 0.344 (anterior-orbit
  ruler) is consistent: the stop lives at the orbit's front edge.

### 1.2 The bridge — a roof with two gutters

The nasal dorsum is a shallow roof (two nasal bones meeting at the
midline) flanked by the dorsolateral nasal cartilages that form the
nostril wings (ala nasi) [S: veteriankey, Nasal Planum ch.]. The
gutter between dorsum and cheek is where NoseWrinkle (E8) physically
gathers skin.

- **F-M3 — Model the dorsum as a roof: a centreline ridge row plus
  one row each side before the gutter.** E8's wrinkle field needs
  2–3 *transverse* rows across the bridge to fold into; longitudinal
  rows alone can only slide, not wrinkle.

### 1.3 The nose leather — a cap seated in a socket, with a philtrum

The nose leather (rhinarium / planum nasale) is hairless, often
crenellated skin wrapped around the nostrils, carried on the nasal
cartilage frame; in dogs and cats it has a **well-defined philtrum** —
the midline groove that runs from between the nostrils down through
the upper lip [S: veteriankey respiratory cheat-sheet; Wikipedia,
Rhinarium]. It is a separate sense organ, not a paint job: it has its
own outline (the planum's edge against furred skin), its own thickness,
and the nostril openings cut into it.

- **F-M4 — Seat the leather, don't float it.** The leather is a cap
  that sits *in* a shallow depression at the muzzle tip: the skin
  needs a seat ring (one loop following the planum outline, inset
  ~0.005–0.01 L) so the cap's rim lands in a groove. A cap placed on
  an undeformed tip reads as a sticker at glancing angles — which is
  v3's current state (§6.4).
- **F-M5 — The philtrum is a centreline crease loop, and it is a
  slider-serving structure.** One pinched centreline row from the
  planum's bottom edge to the lip line gives: the philtrum read at
  rest, the anchor LipLift (E9) parts around, and the midline the
  flehmen remap (expression-system §4.2) curls. Species with no
  philtrum (ruminant planum is continuous with the lip [S]) get it as
  a part variant, not a slider extreme.
- **F-M6 — Nostrils are openings, not texture.** Even a shallow
  nostril pocket (a 4–6 vert inset per side on the cap) catches light
  correctly; a normal-mapped nostril on a smooth cap does not, at
  avatar viewing distances [E].

### 1.4 The lip line — a loop with a corner, or nothing

Lips are musculo-membranous folds around the mouth orifice — skin
outside, orbicularis oris between, mucosa inside — meeting at the
left/right **commissures** [S: veterinary digestive anatomy]. The
upper lip overhangs the lower; the lower lip's mucosa is firmly
attached to the gum. Every lip expression slider (E9, E11–E17) and
every viseme acts on this one structure.

- **F-M7 — The lip line needs a closed elliptical loop cage: minimum
  3 loops (lip edge, lip body, outer support), poles only at the
  commissures** [S: topology canon — GitHub TOPOLOGY_REFERENCE;
  Tripo facial-loops guide]. This is the mouth equivalent of the eye
  rule (F-E1), and it is the single most consequential topology
  requirement in this document: **without a lip loop there are no lip
  sliders, only crease smears.** The loop must be a real opening or a
  welded-shut seam with margin thickness — a line *drawn* by a crease
  in a closed surface cannot part, pucker, or evert.
- **F-M8 — The commissure is a placed landmark, not an emergent
  corner.** Its position (under the eye's lateral third on most
  canids/felids at rest [E]) sets grin length for E11/E15 and the
  snarl's read. It should be a named vertex group on the base, and
  JawLength (#18) / MuzzleLength (#1) fields must carry it
  consistently.
- **F-M9 — Flews are a tissue-variant, not a slider.** The pendulous
  lateral upper lip of bloodhound/St. Bernard type [S] is a drape of
  extra tissue lateral to the loop cage. It composes with the Titan
  batch-1 Jorge spec (`flews_saintbernard` part variant) — keep it a
  part/tissue variant hanging off the cage, exactly as spec §3.4
  already rules for discrete traits.

### 1.5 The whisker pad — muscle under skin, and it needs density

The mystacial pad is a muscular cushion (intrinsic vibrissal muscles)
that protracts the whisker follicles [S: expression-system §2.3, E10].
It sits lateral to the nose, dorsal to the lip line, at canine-tooth
level.

- **F-M10 — Budget the pad like a feature, not like cheek.** E10's
  field is a forward push + fan over a pad-sized patch; it needs pad
  density comparable to the brow band (a distinct pad patch with its
  own boundary falloff), and whisker *card roots* anchor to pad verts
  (expression-system §2.3 already specifies the pad delta carries the
  card anchor frame). On v3 the pad zone is the **sparsest feature
  zone measured** (§6.2) — E10 is currently unbuildable at quality.

---

## 2. Eye socket construction — the expression engine room

### 2.1 What the canon requires

Production face topology is unambiguous about eyes [S: GitHub
TOPOLOGY_REFERENCE; Tripo guide; subdivision-topology reference]:

- **≥3 concentric loops around each eye** (lid margin loop, lid body
  loop, socket support loop), following the orbicularis oculi.
- **Poles only at the inner and outer canthi** — never on the lids
  themselves; a pole on a lid becomes a pinch in every blink.
- Loops must **continue into** brow, bridge, cheek and temple — a
  dense circular patch that terminates abruptly tears at its border
  under brow/cheek fields.
- Eyelid geometry must **conform to and cover the eyeball shell**,
  with real margin thickness where the eye opens.

The reason is mechanical: blink, squint and lid raise are *radial*
motions of the lid over a sphere. Concentric loops give the field
rings that can compress toward the margin (AU7 tighten), slide over
the ball (AU43 blink), and retract (AU5) without shearing. A grid or
a sculpt-noise mesh gives each vertex a different effective direction
and the lid crawls.

### 2.2 The construction that serves our slider set

- **F-E1 — Three loops minimum, four for hero heads.** Margin loop
  (the lid edge, ~16–24 verts), lid loop, socket loop, and a support
  loop that hands off to brow above and cheek below. EyeSize (#22),
  LidRaise (E4), LidTighten (E5), Blink (E7) all spend these loops;
  CheekRaise (E6) spends the support loop from below.
- **F-E2 — The eyeball is a separate sphere; the socket is a seat,
  not a hole the ball pokes through.** The skin should carry a shallow
  socket depression whose rim is the socket loop; the ball sits in
  it with its equator near the rim plane. EyeSpacing (#23) and
  EyeForwardness (#24) then move *ball + socket seat together* — a
  spec-consistent requirement, because on a skin with no seat, moving
  the ball leaves the surface behind (v3's disclosed EyeSpacing
  tension, §6.3, is exactly this).
- **F-E3 — Lids are shells with an edge, not closed blobs.** A lid
  that blinks needs a margin edge loop and enough radial rows (≥4)
  between margin and socket loop to fold over the ball. A closed
  sphere-cap can be *morphed* into a blink shape (and v3's grafted
  caps have clean sphere rows to do it with, §6.3) but it has no true
  margin: the lid edge is wherever the morph says, and the wet-line /
  margin read is lost.
- **F-E4 — Brow loops are the eye's upstairs neighbour.** BrowInner/
  OuterRaise and BrowLower (E1–E3) deform the brow band *against*
  the socket support loop; if brow rows and socket rows are the same
  rows, brow fields drag the upper lid. v3's brow band is its densest
  zone (§6.2) — the material is there; the *separation* of brow rows
  from lid rows is an assembly property (lids are separate objects),
  which accidentally satisfies this — at the price of F-E2/F-E3.
- **F-E5 — Felid/canid sockets are shallower and more lateral than
  the human template.** Orbit Ø/L runs 0.13 (wolf) to 0.21 (cat) in
  our anchors, convergence varies (EyeForwardness span covers it);
  the socket seat must be built at the *neutral* convergence (0.35)
  with rows that survive ±100 without the rim crossing the ball.

---

## 3. Ear cartilage — the pinna is three parts wearing one skin

Veterinary anatomy divides the auricular cartilage into three
continuous sections [S: veteriankey, Anatomy of the Ear]:

- **Concha** — the proximal trumpet: rolled cartilage forming the
  conchal cavity that funnels into the canal tube. This is the ear's
  *bowl*, and it is deep — on an erect canid/felid ear the cavity is a
  substantial fraction of pinna height.
- **Scapha** — the distal, flattened blade beyond the concha.
- **Antihelix** — a transverse cartilaginous **fold on the concave
  surface dividing scapha from concha**. It is the ear's main internal
  landmark: a ridge running across the bowl's upper edge.
- Plus the **tragus** (a projection guarding the canal opening at the
  rostral base), the **antitragus**, and in dogs/cats the **cutaneous
  marginal pouch** — a slit fold on the caudal margin [S].

The pinna is a *thin cartilage plate, skin both sides* — not a solid
and not a single-sided card: its rim (helix) is the plate edge rolled
slightly outward.

- **F-A1 — Build the ear as three zones with a fold between two of
  them.** Minimum viable grid: a base ring seated on the cranium, a
  concha bowl (≥3 rows deepening), an **antihelix ridge row** (one
  raised row across the bowl), then scapha rows (≥3) to the tip. The
  ridge row is what catches the light line that makes an ear read as
  an ear instead of a leaf.
- **F-A2 — EarFlatten (E23) folds at the antihelix and the base, not
  "somewhere".** Real flattening is a hinge at the base plus a fold
  along the antihelix line. E23's pose+delta record (expression-system
  §2.6) needs a **crease row at the base** and verts along the
  antihelix to fold against; a smooth plate can only bend like a
  spoon. EarTilt (#15) is the resting version of the same hinge.
- **F-A3 — The tip is a shape family, the margin is a loop.** EarTip-
  Point (#16) works on the last two rows; lynx tufts / folded tips
  stay part variants (spec §3.4). The helix margin should be a clean
  boundary loop with slight outward roll baked in — it is the ear's
  silhouette at every angle.
- **F-A4 — Thickness: give the pinna a solidify-style shell for hero
  heads.** Single-sided plates shade wrong at the rim and can't hold
  an inner-ear fur tuft or a folded margin. (v3's ear is single-sided,
  §6.5.)
- **F-A5 — Ear sliders are scale/pose over the grid; cartilage detail
  is *born in the base*, not slider-authored.** EarLength (#11) to
  fennec +100 stretches the scapha rows; if the antihelix row is a
  *named row* it can be held at concha scale while the blade grows —
  which is what real fennec ears do (the bowl stays ear-sized, the
  blade becomes a sail). Without named rows, length stretches the
  whole ear uniformly and big ears read as scaled, not grown.

---

## 4. Kemono vs realistic — structural differences, not just proportions

*Terminology warning [S]: "kemono" carries two usages. In avatar
commerce (BOOTH/Jinxxy/VRChat — the usage that matters for
AnthroForge's style axis) it means the anime-proportioned style: very
large eyes, short muzzle, large forehead, expression partly carried by
eye/mouth blendshapes and texture [S: Nyako kemono base listing;
terabox Chinese fursuit guide; Aesthetics Wiki]. In Western fursuit
usage (kfursuits) "kemono" is sometimes used for slim, animal-leaning
builds — the opposite pole. This section uses the avatar-commerce
meaning and says so wherever it matters.*

The styles differ in **where expression lives** and **which structures
exist at all**, not merely in slider values:

| Structure | Realistic (our neutral → species) | Kemono (avatar-commerce sense) |
|---|---|---|
| Cranium share | Cranium fraction 0.62 of L; forehead modest | Braincase dominates; "large foreheads" are a named style trait [S: Aesthetics Wiki]; muzzle fraction can fall to ~0.10–0.20 |
| Eye | Ø 0.13–0.21 L, ball in a socket seat, lids deform over it | Ø ~0.25–0.40 L [E], often a **dome/printed iris on a curved shell**; the eye is a graphic surface, not an anatomical ball-in-socket [S: kemono eye construction, printed iris on perforated material/tint] |
| Expression engine | FACS delta fields on muscle layer (our E1–E24) | **Blendshape set**: 15 VRChat visemes + emotion shapes, gesture/menu-triggered eye & mouth swaps; face-tracking shapes bolted on in newer bases [S: VRChat face-tracking wiki; Nyako listing] |
| Mouth | Lip-loop cage, cavity, teeth arcade, commissure landmark | Small mouth, often a short line or tiny open shape high on a short muzzle; mouth *shapes* are blendshapes on a smooth muzzle front; teeth usually absent or a single flat shape |
| Nose | Seated leather cap, philtrum, nostril pockets | Small triangle/heart leather, frequently flat or a minimal bump; philtrum usually absent; the "ω" mouth line replaces lip structure |
| Stop | A measured ledge (§1.1) | Often no ledge: forehead domes continuously into a short muzzle wedge; the "stop" is a shading crease at most |
| Ears | Cartilage zones (concha/antihelix/scapha) | Larger relative to head, inner ear simplified — flat colour or a single tuft; silhouette (shape + tip) carries the read |
| Topology consequence | Needs the full loop cage (eyes, lips), socket seats, ear grid | Needs **density smoothness** on the muzzle front (mouth shapes must not tear) and huge clean eye shells; can skip lip cage, cavity, ear cartilage — but *cannot* reuse a realistic base at slider extremes (see F-K2) |

- **F-K1 — Kemono is a different expression contract.** Our E-system
  assumes muscles under skin. Kemono faces emote by *swapping and
  blending authored face states* (including eye graphics). A kemono
  preset on our system should therefore ship as: shape vector (style
  region) + a **state library** of pre-authored fine-slider poses —
  which our masters already almost are (§3 of expression-system) —
  rather than expecting FACS fields to read at 0.35 L eye size.
- **F-K2 — The style axis cannot reach kemono from the current spans
  alone.** Measured against the spec: EyeSize (#22) spans orbit Ø
  0.05…0.25 L — kemono eyes start where the span ends. MuzzleLength
  (#1) floor is 0.13 — reachable. CraniumLength (#8) + ForeheadWidth
  (#10) can approach the dome but EyeSpacing (#23, span ±0.08 around
  0.19) and OrbitHeight (#32) were not designed for eyes that sit
  low-and-wide on a huge cranium. **Recommendation: the style axis
  needs either an EyeSize span extension for stylised bases or a
  style gain block in the preset record (like `expression_gains`)** —
  recorded here as a spec observation, not a change.
- **F-K3 — What kemono teaches the realistic base:** its muzzle-front
  smoothness discipline. Kemono mouths work because the muzzle front
  is an even, pole-free field. Our lip cage should keep its *outer
  support* region equally clean — poles belong at the commissures
  only (F-M7), never mid-cheek where E6/E11 fields sweep.

---

## 5. Slider → topology requirements (master table)

Status key for the v3 base: **✓** supported · **◐** partial — field
will apply but quality/structure is compromised · **✗** the required
structure does not exist on v3. (Detail in §6.)

### 5.1 Shape sliders (37)

| Slider(s) | Required underlying topology | v3 |
|---|---|---|
| #1 MuzzleLength, #2 MuzzleWidth, #3 MuzzleTaper, #4 MuzzleDepth | Rostrum with ≥4 lengthwise rows + ≥3 cross rings; taper needs its own ring near the tip | ◐ sculpt rows exist, irregular spacing |
| #5 NoseSize | Nose as socketed cap: seat ring in skin + ≥2 rings on cap (F-M4) | ◐ cap exists; no seat ring |
| #6 CraniumWidth, #7 CraniumHeight, #8 CraniumLength, #35 BraincaseRise | Broad smooth shell fields; low density acceptable | ✓ |
| #9 StopAngle, #34 StopDepth | Dedicated loop on the break line + supports (F-M1) | ◐ break exists in sculpt; no dedicated loop |
| #10 ForeheadWidth | Frontal band rows between orbits | ✓ |
| #11 EarLength, #12 EarWidth | Pinna grid with named antihelix row to hold while blade scales (F-A5) | ◐ gross scale ✓; no named rows |
| #13→EarBaseHeight, #14 EarSpread | Base ring seated on cranium that can translate/rotate | ◐ base is a hole edge in the skin, ear a separate shell |
| #15 EarTilt | Hinge at base crease row (F-A2) | ◐ pose works on the shell; no crease row |
| #16 EarTipPoint | ≥2 clean rows at the tip | ◐ tip rows exist but sparse (§6.5) |
| #36 EarTipHeight | Pivot solver over base + tilt; same needs as #13/#15 | ◐ |
| #17 JawDepth, #37 JawDepthProfile | Jaw as separate hinged mesh with ramus rows | ✓ split exists, origin on hinge |
| #18 JawLength | Jaw mesh + commissure landmark carried consistently (F-M8) | ◐ jaw ✓; no commissure landmark on skin |
| #19 JawWidth | Hinge-width field over jaw + cheek band | ✓ |
| #20 CheekWidth | Zygomatic band rows | ✓ |
| #21 RuffVolume | Tissue shell offset; topology-light | ✓ |
| #22 EyeSize | Ball + lid shells scale together; socket seat scales | ◐ assembly scales; no seat in skin |
| #23 EyeSpacing | Ball **and socket seat** translate together (F-E2) | ✗ seat does not exist — the v1/v3 tension (§6.3) |
| #24 EyeForwardness | Ball/seat yaw; skin rim must follow | ◐ balls yaw; skin static |
| #25–28 BrowProjection/Thickness/Continuity/Shelf | Brow band rows over the rim (skull-led fields) | ✓ densest zone on the head |
| #29 BrowPosition, #30 BrowPadding | Soft brow-line rows distinct from rim rows | ✓ |
| #31 BrowScowl | Corrugator mask over medial brow (shared with E3) | ✓ |
| #32 OrbitHeight | Orbit band + ball seats translate vertically as one | ◐ band ✓; seats = assemblies only |
| #33 OrbitRise | Frontal band restructures relative to seated eye | ◐ field-only (v3 BUILD_NOTES admits the band barely moved) |

### 5.2 Expression sliders (24)

| Slider(s) | Required topology | v3 |
|---|---|---|
| E1 BrowInnerRaise, E2 BrowOuterRaise, E3 BrowLower | Brow band density + separation from lid rows (F-E4) | ✓ (density) / ◐ (separation is by object split) |
| E4 LidRaise, E5 LidTighten, E7 Blink | Lid shell with margin edge loop + ≥4 radial rows over the ball (F-E3) | ◐ closed sphere-cap shells with clean rows, but **no margin edge** |
| E6 CheekRaise | Cheek density + support loop under the eye | ◐ mid density (1,102 verts/L²) |
| E8 NoseWrinkle | 2–3 transverse rows across the bridge (F-M3) | ◐ dorsum density ok (1,502/L²); rows are sculpt-irregular |
| E9 LipLift | Lip-loop cage + philtrum crease (F-M5, F-M7) | **✗ no lip loop exists** |
| E10 WhiskerPad | Pad patch at brow-band-class density (F-M10) | **✗ sparsest feature zone (816 verts/L²)** |
| E11–E15, E17 lip family | The lip cage (F-M7) + commissure poles (F-M8) | **✗** |
| E16 ChinRaise | Chin pad rows on jaw tissue | ◐ jaw tissue exists; chin group present in groups.json |
| E18 JawOpen, E19 JawShift, E20 JawProtrude | Hinged jaw part record | ✓ |
| E21 EarForward, E22 EarBack, E24 EarSwivel | Ear-base pivot (pose) | ✓ on the shell |
| E23 EarFlatten | Base crease row + antihelix fold line (F-A2) | **✗** folds as a spoon, not at cartilage lines |

**The pattern in the table:** v3 supports *shape* well (it is a
neutralised sculpt — broad fields are its home turf) and supports
expression exactly where expression lives on **separate parts** (jaw,
ear pose, brow density). It fails expression precisely where
expression needs **loop structure in the skin itself**: the lip cage,
the whisker pad, the lid margin, the ear fold. That is the v4 build
list, in priority order: **lip cage → lid margin/seat → pad density →
ear grid.**

---

## 6. Topology annotation of base-head-v3 (measured)

All numbers [D] from the GLB, welded; full dump in
`topology_stats.json` (copy beside this file). v3's construction recap
(from its BUILD_NOTES): tissue = neutralised GalileoGB cougar sculpt,
1,559 source verts → **962 welded tissue verts / 1,828 tris**; jaw
split on its hinge; eye assemblies, nose leather, throat and neck
socket grafted from v2's procedural parts; ears carried from the
cougar, rescaled.

### 6.1 Global character of the tissue mesh

- Valence median 6, but **311 of 962 verts are poles** (179 valence-5,
  132 valence-≥7, max 21). This is a sculpt's triangulation, not a
  loop cage: poles sit where the cougar sculpt put them, not at
  canthi/commissures where the canon wants them. Consequence: delta
  fields (ours are smooth-field authored) apply fine, but any future
  *loop-based* operation (edge-flow selection, ring-based weights,
  clean subdivision) will fight the mesh. Note base-head-v4 (sibling
  project) is doing the subdivide-and-sculpt pass — subdivision of a
  pole-heavy sculpt smooths the surface but does not create loops.
- Boundary loops (3): a **66-edge ventral seam** (the shell is open
  along the throat/underside where jaw and throat graft sit), and
  **two 16-edge loops at the ear bases** — i.e. the ears are separate
  shells plugged into holes in the cranium. **There are no eye or
  mouth openings in the skin at all.**

### 6.2 Density map — where the verts actually are

Verts per L² of surface, by zone (fig. `annotation_front_regions.png`):

| Zone | verts/L² | Serves | Verdict |
|---|---|---|---|
| Brow band | **2,535** | #25–31, E1–E3 | densest on the head — brow family is the best-supported system on v3 |
| Muzzle dorsum | 1,502 | #1–4, E8 | adequate; rows irregular |
| Eye zone (skin) | 1,447 | E6 support, #32/#33 fields | adequate for fields; structure absent (§6.3) |
| Lip-line zone | 1,368 | E9, E11–E17 | density is *not* the problem — the loop is (§6.4) |
| Cheek | 1,102 | #20, E6 | mid; E6 will be soft |
| **Whisker pad zone** | **816** | E10 | **sparsest feature zone — E10 unbuildable at quality (F-M10)** |
| Forehead | 647 | #10, #35 | fine (broad fields) |
| Cranium side | 581 | #6 | fine |

### 6.3 The eye station — a grafted assembly over unbroken skin

(Fig. `annotation_eye_station.png`.) The skin has **no socket**: no
opening, no rim loop. The eyeball (162-vert sphere, r = 0.075) is
embedded *into* the surface — **52 tissue verts lie inside the ball's
sphere** (min centre distance 0.033), i.e. the skin dips behind the
ball rather than seating around it. Around the station the skin does
have usable resolution: BFS from the rim band gives ~5–7 irregular
vertex rows between the ball and 0.20 L — row *count* near the
canon's 3-loop minimum, but they are sculpt rows, not concentric
loops, and they belong to the skin, not to any lid.

The actual lid system is v2's grafted assembly, three closed shells
per eye: **Eyelid** (478 welded verts, a sphere-cap with clean
latitude rows, *zero boundary edges* — a closed blob), **LidMargin**
(280 verts, also closed), plus Iris/Pupil spheres. Verdicts:

- **Supports:** E4/E5/E7 as *morphs of the cap* — the cap's sphere
  rows are genuinely good deformation stock, better than the skin's.
- **Hinders:** no margin edge (F-E3) — blink closure line is wherever
  the morph puts it; the skin contributes nothing, so lid–cheek
  interplay (E6 pushing tissue into the lower lid) cannot happen
  across the object split; EyeSpacing (#23) moves the assembly over a
  seatless skin — the geometric root of the interorbital deviation
  v3's notes disclose (measured 0.112 vs target 0.19: at 0.19 the
  assemblies would float off the surface, because there is no socket
  to be wide *in*).

### 6.4 The muzzle — real stop, floating nose, absent lips

(Figs. `annotation_profile_stop.png`, `annotation_muzzle_nose.png`.)

- **Stop: a genuine ledge** — max profile curvature at z = −0.27,
  slope 0.65 → 2.81 (§1.1). The cougar sculpt earns its keep here;
  StopAngle/StopDepth fields have a real break to push on, though
  with no dedicated loop (F-M1) their resolution is the local sculpt
  rows (~1,500 verts/L² on the dorsum).
- **Nose leather: a closed 162-vert cap** (UV-sphere-derived: 12
  valence-5 poles) placed over the tip. Vertex-to-vertex distance to
  the skin: median **0.0175 L**, p90 0.027, max 0.041; only 1.9% of
  cap verts within 0.005 L of a skin vertex. Vertex distances
  overstate surface gaps on coarse meshes, but the pattern is
  unambiguous: the cap is *proud* of the tip everywhere, seated in
  nothing (no seat ring, F-M4). There is **no philtrum crease** and
  **no nostril pocket** on the cap — both are texture/material
  problems as shipped. NoseSize (#5) scales a floating cap.
- **Lip line: a sculpted crease only.** No opening, no loop, no
  commissure landmark anywhere in the skin; the mouth's real geometry
  is the separate TeethArcade slab (719 verts, fused across both jaws
  — v3 limitation 1) and Tongue (457). Every lip slider in §5.2 is
  therefore a *field over a crease*: E11 can bulge the cheek end of
  the crease but cannot part, roll, or stretch a lip. **This is the
  head's largest expression gap** — larger than the teeth fusion,
  because the fusion is one part swap while the lip cage is a
  retopology of the whole muzzle front.
- **Whisker pad:** see §6.2 — 816 verts/L², roughly a 32-vert patch
  per side at pad scale. E10's protraction field would move a handful
  of verts; whisker card roots would anchor to nearly nothing.

### 6.5 The ears — a shaped plate, not yet a cartilage structure

(Fig. `annotation_ear_relief.png`.) Each ear: **76 verts / 134 tris**,
a single-sided open shell whose only boundary is the 16-edge base
loop. Relief across the ear plane spans **−0.037…+0.073 L** with a
centre-vs-rim differential of only ≈**0.018 L** — there *is* a shallow
cup (the cougar's concha, flattened by neutralisation), but at this
count the antihelix cannot exist as a row: the length-axis vert
distribution [10,10,11,10,3,7,5,4,4,4,4,4 per 12 bins] shows a
bottom-heavy sculpt strip — ~44% of all ear verts are in the basal
third (groups.json agrees: EarBase = 23 of 76), the blade runs at
~4 verts per row, and the tip (EarTip group, 33 verts) is a fan, not
rows. Verdicts:

- **Supports:** EarLength/Width/Tilt/Spread and the E21/E22/E24 poses
  — gross transforms of a light shell are cheap and stable; the base
  loop gives EarBaseHeight/EarSpread a clean seat edge to move.
- **Hinders:** EarFlatten (E23) has no base crease row and no
  antihelix to fold on (F-A2) — it will bend the plate like a spoon;
  EarTipPoint (#16) edits a fan; F-A5's "hold the bowl, grow the
  blade" is impossible without named rows — fennec at +100 stretches
  the cup too.

### 6.6 Jaw and mouth interior

Jaw: 538 verts, open shell (boundary loops 78 + 46 — the underside/
interior is open, normal for a jaw part), origin exactly on the hinge
— E18–E20 and the whole viseme family are structurally sound. Teeth
arcade and tongue as §6.4. The jaw split's zigzag cut edge (v3
limitation 2) crosses the cheek at coarse resolution — it is also the
seam any future lip cage must terminate into cleanly.

---

## 7. Build spec for the next base head (recommendations — not built)

Priority-ordered, each item traceable to a rule above:

1. **Lip cage first** (F-M7/F-M8): retopologise the muzzle front with
  a 3-loop elliptical lip cage around a real mouth opening, poles at
  placed commissures, philtrum centreline row (F-M5), terminating
  into the jaw seam. Unlocks 8 expression sliders + visemes honestly.
2. **Socket seats + margin-edged lids** (F-E2/F-E3): cut shallow
  socket seats with a rim loop into the skin; rebuild lids as shells
  with a margin edge and ≥4 radial rows, conforming to the ball.
  Unlocks #23/#24 as honest sliders and E6↔lid interplay.
3. **Whisker pad patch** (F-M10): raise pad density to brow-band
  class (~2,500 verts/L²) inside a bounded patch with falloff border;
  name the pad verts as the whisker-anchor group.
4. **Ear grid** (F-A1/F-A5): rebuild ears at ~250–400 verts as a
  two-sided shell: base ring, concha bowl (≥3 rows), named antihelix
  row, scapha rows (≥4), tip rows (≥2), base crease row for E23.
5. **Stop loop** (F-M1): one loop on the break line, temple to
  temple, + supports — cheap once the muzzle is open for work.
6. **Nose seat** (F-M4/F-M6): inset seat ring in the tip; rebuild the
  leather as a cap with ≥2 rings, philtrum groove, shallow nostril
  pockets.
7. **Pole discipline pass**: after 1–6, poles should exist only at
  canthi, commissures, and the ear base — audit against the §6.1
  census (311 poles is the number to beat down).

None of this invalidates v3 as the *shape* reference: its proportions,
stop, brow density and hinge are the measured ground truth the cage
should be built *onto* — which is why this study recommends cage
surgery on the v3 lineage rather than a new neutralisation.

---

## Sources

- Veterinary ear anatomy (pinna sections: scapha / concha / antihelix
  fold, tragus, marginal pouch): https://veteriankey.com/1-anatomy-of-the-ear/
- Nasal planum, philtrum, nasal cartilages, lip musculature:
  https://veteriankey.com/nasal-planum-nasal-cavity-and-sinuses/
- Rhinarium / philtrum morphology: https://en.wikipedia.org/wiki/Rhinarium
- Face topology canon (≥3 concentric eye loops, mouth loops, pole
  placement): https://github.com/73k-y/3d-workflow-pipeline/blob/HEAD/TOPOLOGY_REFERENCE.md
- Facial loops follow musculature (orbicularis oculi/oris):
  https://www.tripo3d.ai/blog/explore/smart-mesh-facial-topology-loops-basics
- Kemono style traits (anime eyes, chibi proportions, printed iris):
  https://news.terabox.com/hub/how-to-find-and-buy-highquality-chinese-fursuits-without-getting-scammed
  · https://aesthetics.fandom.com/wiki/Furry?file=Crazy_Creature_Costumes.jpg
- Conflicting Western usage of "kemono" (slim/animal-leaning):
  https://www.kfursuits.com/what-is-a-kemono-fursuit.html
- Kemono avatar practice (visemes, expression + face-tracking
  blendshapes, gesture-swapped eyes/mouth):
  https://jinxxy.com/Raideus/Nyako ·
  https://wiki.vrchat.com/index.php?title=Face_Tracking&diff=cur&oldid=29763
- Internal: `species-head-spec.md`, `expression-system.md`,
  `base-head-v3/BUILD_NOTES.md` + `proportions.json` + `groups.json`,
  and my measurements in `topology_stats.json` beside this file.
