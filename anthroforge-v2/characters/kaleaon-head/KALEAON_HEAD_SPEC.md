# Kaleaon Head — Own-Build Spec (Phase 1: Study)

**Status:** Phase 1 complete. Phase 2 (build) is gated on `base-head-v5`
(BUILD_V5.md) — see §10.
**Ruling behind this work:** Joe, Nov 16, 2026 — *"build our own, carefully,
and as high quality as possible."* The donor-graft route is closed. Lion
Warrior / Leopard A2 / Cougar are **references**, not grafts. Nothing in this
spec copies a reference mesh; every number below is a measurement, a
literature anchor, or a derived target — the geometry will be ours.

## 0. Authority order (per head standards v2 §0)

1. **Canon character sheet** (`bodies-3d/references/kaleaon_canon_sheet_2015.jpg`)
2. **Reference album population** (tiebreaker where the sheet is silent)
3. **`kaleaon_head_standards_v2.md`** criteria (incl. Tinker's Nov 7, 2026
   reconciliation rulings at its foot)
4. **Measured reference anatomy** (this doc §2) and the species-head-spec's
   sourced ratios
5. Generic lion anatomy — last resort only

Where two references conflict and the sheet doesn't settle it, the conflict is
flagged in §9, never silently picked.

## 1. Canon — what this head must be

From the sheet, the album (as distilled in standards v2), and Joe's rulings:

- **Anthro lion × snow leopard.** White lion with snow-leopard spots;
  the hybrid half reads in the muzzle (slightly narrower than a full lion's,
  §3) and in the coat (markings are a later system — no geometry).
- **Deep, boxy muzzle in proportion; broad and soft in surface.** The survey
  yardstick says "deep boxy muzzle"; standards v2 says "broad and soft… a
  stylized lion muzzle, not a realistic wild-cat one." Both are honoured by
  splitting the claim: the *stations* (§4) are boxy — deep rostrum, low
  taper, wide at the canine level — while the *surface treatment* is soft:
  whisker-pad swells, a two-lobe upper lip, a gently curved smile line, no
  hard planes. See flag F1.
- **Heavy brow** — real mass in the muscle/tissue layer (brow shelf +
  padding), not texture and not a scowl baked into the rest pose. Rest pose
  is **neutral open** (Joe, Nov 7, 2026): upper lid covers the top ~15–20%
  of the iris. The sheet's relaxed part-lidded look is a morph (`Relaxed`),
  not the rest state.
- **Broad skull read** — carried, per the felid anchors, by zygomatic breadth
  (ZB/L 0.70), jaw width and the mane/ruff mass — *not* by braincase width
  (lion braincase W/L is only 0.31). Same lesson Sen's bear build proved:
  breadth is cheek + jaw + ruff, not bone width.
- **Small, rounded ears, sitting low, half-buried in the mane** — "only just
  peek out" (standards v2 §2.2). Ear tips at or just below the mane surface.
- **Mane: very full, voluminous, swept back and out**, framing the face as a
  big ruff that merges into the chest and shoulders. The mane **form** is
  geometry in this build (a sculpted shell, §6); the groom (hair curves)
  and the **central braid** (canon: one thick braid to the belly) are later
  systems. Cheek tufts and chin fur are **distinct masses** from the mane
  shell. Chin mass must be able to carry the goatee (colour still open —
  groom-tier, flag F5).
- **Head small relative to the bara torso** — assembly targets in §7.
- **Eyes green** (material, later); geometry: globes seated in sockets with
  real lid thickness, tear-duct corner, brow shadow (standards v2 §4.1).
- **Nose pink** (material, later); geometry: sculpted felid nose pad —
  defined nostrils, philtrum groove running to the upper lip, slight
  overhang (standards v2 §4.2). The v5 base's lip cage already carries
  philtrum support (§5).
- **No rosettes on the face** (confirmed, standards v2 ruling on Q5). One
  sheet head study shows faint spots at the cheek/forehead fur — flagged
  for the markings pass (F6); geometry is unaffected either way.
- **Glasses are canon** but are a **later accessory system** in this
  programme's order. This build must not block them: nose-bridge form that
  can carry a bridge rest, and a temple clearance corridor through the
  mane shell (no mane mass crossing the eye→ear line at temple depth).
  Glasses parent to the head bone, never the jaw (standards v2 §5).
- **Expression range the geometry must support:** smile, neutral, stern,
  eyes-closed, squint (standards v2 §2.2) — i.e. lids that can fully close,
  a lip line that is a structure (v5 cage), brow mass that can lower.

## 2. Reference measurements (Phase 1 probes — measured, not copied)

All probes run Nov 16, 2026, headless Blender 5.2.3, `--threads 2`.
Scripts in `/tmp` during the pass (probe_bones.py, probe_warrior.py,
probe_statues2.py, probe_leopard2.py); headline numbers below are the
record. **Learn-then-derive discipline:** measurements and derived targets
are ours to keep; no reference mesh is reused in the build.

### 2.1 Leopard Hybrid A2 — felid face stations (primary face reference)

Native `.blend` at `bodies-3d/kaleaon-rigged3/work/leopard/Blender/
Leopard_Hybrid_A2.blend`. **This landed copy is a single fused mesh**
(22,848 verts, 74-bone Bip01 rig) — the separate eye globes / teeth /
tongue the Nov 7 survey described are **not separate objects in this
copy** (flag F3). Head region isolated by `bip01_head` vertex weights
(> 0.4; 5,295 verts). L here = nose tip → back of the weighted head
region along the body axis = 0.576 file units (slightly short of true
prosthion→inion; ratios carry ≈ ±0.03 tolerance). Pose caveat: the head
rests in a part-open snarl — ventral and muzzle-depth reads are
pose-inflated and are marked as such.

| Station (u = fraction of L from nose) | Measured |
|---|---|
| Width at nose band (u 0.0–0.1) | 0.363 L |
| Width at canine/muzzle band (u 0.2) | 0.506 L |
| Width at orbit approach (u 0.4) | 0.677 L |
| **ZB max (u ≈ 0.55–0.65)** | **0.842 L (fleshed)** |
| Width at occiput band (u 0.9) | 0.459 L |
| Muzzle block width (anterior 30%) | 0.506 L |
| Muzzle block depth (anterior 30%, pose-inflated) | 0.606 L |
| Fleshed head height (jaw open, pose-inflated) | 0.782 L |
| Dorsal midline profile | smooth convex ramp, **no step**: nose 1.528 → crown plateau at u 0.5–0.6 (Δ ≈ 0.43 L over the rise); the felid stop is a ramp, not a break |
| Ears | top clusters at u 0.56–0.85, tips at crown height (z ≈ head top); visible ear above the skull line only ≈ 0.07–0.16 L — ears ride **low**, tips ≈ crown |

**Fleshed vs skull:** the fleshed ZB read (0.842) sits well above the
leopard's skull ZB/basal ratio 0.723 [S] — fur, cheek ruff and the short
measured L account for it. The build therefore keeps the species spec's
two-layer discipline: **bone-layer targets from the literature anchors
(§2.5), tissue/mane targets from the fleshed reads.** Conflating them is
how the v3/v4 MuzzleWidth artefact happened; it is not repeated here.

### 2.2 Poly Haven lion head (CC0) — brow plane + mane silhouette

Relief bust (25,380 verts; depth ≈ 0.47 × height, so only width/height
ratios are meaningful). Bust height H = 0.436 file units.

- Width profile by height band: chin/beard 0.30–0.49 H-wide → mane max
  **0.736 H at 0.60 H** → crown band 0.415 H. **Mane is widest at cheek
  level (~0.6 of head height) and ~1.8× the crown width.**
- Midline front profile: the **brow/forehead band is the most projecting
  surface above the muzzle** — it sits ≈ 0.015–0.030 (in H units ≈
  0.03–0.07 H) ahead of the muzzle front line. The heavy brow is a
  *projection*, measurable, not just shading.
- Chin/beard mass projects at the bottom band (front-most point of the
  whole bust at the lowest band is the chin beard).

### 2.3 Roaring Lion (CC-BY) — mane form, ear burial

Statue scan (33,392 verts), head zone isolated by axial slice.

- Mane width peaks at **z-fraction 0.62–0.75 of head height** (w 0.381)
  vs crown 0.294 → mane max ≈ **1.30× crown width**, agreeing with
  Poly Haven's "widest at cheek level" at a fuller mane volume.
- Ears: small, half-buried, the most canon ear/mane relationship in the
  set (survey) — consistent with A2's measured low ear ride.

### 2.4 Lion Warrior (CGTrader RF) — rig proportions, head/torso

Full character, 4.188 units tall, fused mesh, CC bone family (the family
our r3 rig was refit from — its *layout* is already our standard).

- Head-weighted verts (> 0.7): z 3.252–4.188 → head + mane shell ≈
  **0.94 units ≈ 22% of total height** (stylised; survey notes the
  skull/mane dome is outsized). Kaleaon's canon read is smaller (§7).
- `CC_Base_JawRoot` pivot sits **just below the head bone and ≈ 0.08
  ahead of the head axis** (head z 3.470 / jawroot z 3.458, forward
  offset 0.084) — the hinge is under the ear line, not at the neck.
- Tongue chain: JawRoot → Tongue01→02→03; Teeth02 (lower) under JawRoot;
  Teeth01 (upper) under UpperJaw. Eye spacing ≈ 0.19 at his scale
  (head width ≈ 0.98) → interorbital-centre spacing ≈ 0.20 × head width.

### 2.5 Literature anchors (from species-head-spec §2.2 / §5 — sourced)

| Anchor | Lion | Leopard (panther) | Note |
|---|---|---|---|
| Skull length | 39.7 cm | — (skulls ≈ 221–244 mm) | lion overall W/L 0.71 |
| ZB / basal length | **0.743 [S]** | **0.723 [S]** | Wroe bite-force dataset |
| ZB/L adopted (spec §3.2) | **0.70 [D]** | 0.67 [D] | preset anchor |
| Mandible / CBL | **0.743 [S]** | 0.73–0.74 [S] | Christiansen 2008; Stein & Hayssen 2010 |
| Muzzle fraction | 0.28 [E] (longest felid rostrum, qual. [S]) | 0.26 [E] | |
| Orbit Ø / L | 0.17 [E] | 0.19 [E] | cat orbit 0.21 [S] is the felid ceiling |
| Ear / L | 0.22 [E] | 0.22 [E] | |
| Verticals (OrbitHeight / OrbitRise / StopDepth / BraincaseRise / EarTipHeight / JawDepthProfile) | 0.18 / 0.13 / 0.06 / 0.15 / 0.14 / 0.20 — all **[E]** | 0.19 / 0.19 / 0.15 / 0.19 / 0.23 / 0.19 — **[D]**, measured on the puma CT skull (MSB:Mamm:214485) | lion verticals are *unmeasured* (spec §5.2: the Poly Haven scan is not measurable); the puma column carries the felid pattern |

## 3. The Kaleaon vector (37 sliders)

Base = **lion preset** (species-head-spec §3.3 + §5.5), with hybrid and
character deltas. Application method = the Sen build's convention:
proportional ratio factors from the spec neutral, preserving the base
head's deliberate deviations (see F4 on interorbital).

| # | Slider | Lion | **Kaleaon** | Why |
|---|---|---|---|---|
| 1 | MuzzleLength | −25 | **−25** | lion rostrum (frac 0.28) |
| 2 | MuzzleWidth | +25 | **+20** | **hybrid delta** — leopard's value; the snow-leopard narrower read inside the lion frame |
| 3 | MuzzleTaper | −10 | **−5** | hybrid midpoint; keeps the boxy (low-taper) read |
| 4 | MuzzleDepth | +30 | **+30** | the "deep" in deep boxy muzzle |
| 5 | NoseSize | +35 | **+35** | sheet: prominent nose pad |
| 6 | CraniumWidth | −30 | **−30** | braincase is *not* where lion breadth lives (§1) |
| 7 | CraniumHeight | +10 | **+10** | + crest strip (§6) for the large-male sagittal crest |
| 8 | CraniumLength | +10 | **+10** | |
| 9 | StopAngle | −25 | **−20** | felid ramp (A2 §2.1: no step); sheet shows a gentle forehead rise |
| 10 | ForeheadWidth | 0 | **0** | |
| 11 | EarLength | −30 | **−30** | ear/L 0.22 |
| 12 | EarWidth | −20 | **−20** | |
| 13 | EarBaseHeight | −20 | **−20** | 0.02 L — ears sit low (A2, Roaring) |
| 14 | EarSpread | +20 | **+20** | |
| 15 | EarTilt | −10 | **−10** | |
| 16 | EarTipPoint | −60 | **−60** | fully rounded → `ear_round` variant (§6) |
| 17 | JawDepth | +45 | **+45** | |
| 18 | JawLength | 0 | **0** | mandible/L 0.74 [S] |
| 19 | JawWidth | +30 | **+30** | breadth carrier |
| 20 | CheekWidth | +60 | **+60** | ZB/L 0.70 [D] — the master width |
| 21 | RuffVolume | +90 | **+90** | under-mane tissue mass; the mane shell itself is §6 |
| 22 | EyeSize | +20 | **+20** | orbit Ø 0.17 L |
| 23 | EyeSpacing | +25 | **+25** | applied proportionally — see F4 |
| 24 | EyeForwardness | +50 | **+50** | felid frontal orbits |
| 25 | BrowProjection | −20 | **−20** | no felid torus; emphasis re-homed below |
| 26 | BrowThickness | −15 | **−15** | |
| 27 | BrowContinuity | −25 | **−25** | |
| 28 | BrowShelf | +20 | **+20** | brow emphasis lives here (Poly Haven §2.2: projection over the orbit) |
| 29 | BrowPosition | −10 | **−10** | |
| 30 | BrowPadding | +15 | **+15** | soft-tissue brow mass |
| 31 | BrowScowl | +20 | **+10** | **character delta** — the sheet's default is gentle; heavy brow *read* comes from shelf+padding mass, not resting scowl. Stern stays a pose. [E] |
| 32 | OrbitHeight | +10 | **+10** | 0.18 L [E] |
| 33 | OrbitRise | +5 | **+5** | 0.13 L [E] — eye sunk under forehead, far off the crocodile pole |
| 34 | StopDepth | 0 | **0** | 0.06 L — a ramp, per A2 |
| 35 | BraincaseRise | +5 | **+5** | 0.15 L [E] |
| 36 | EarTipHeight | −20 | **−20** | 0.14 L — tips ≈ at/below crown, mane-buried |
| 37 | JawDepthProfile | +25 | **+25** | coronoid rise 0.20 L [E] |

**Build-level deltas (not sliders):**
- **Whisker-pad swells** — felid discrete (§3.4 of the species spec):
  tissue swell on the muzzle sides at the canine band; follicle dimples
  are a later texture pass.
- **Chin mass** — a soft tissue swell under the jaw front (+≈0.01 L) so
  the chin can carry the goatee and the sheet's chin tuft.
- **Smile line** — the v5 lip cage's line is shaped to the sheet's gentle
  upward curve at the commissures (rest = neutral, curve is in the line's
  *path*, not a baked smile expression).

## 4. Target stations (acceptance numbers for Phase 2)

Frame: head-local, L = nose tip → occiput = 1.000 (the v3/v4/v5 ruler
frame; L is tissue Y extent). Assembly scale in §7 turns L into metres.
Acceptance uses **two rulers**, per the v4 appendix lesson: the stage-F
vertex rulers *and* surface-true sections for widths. Gates: ±6% band
(house standard) against the proportional prediction from the v5 base's
own measured neutral — plus the absolute character gates marked ★.

| # | Station | Target (L) | Source |
|---|---|---|---|
| S1 | ZB, fleshed (surface-true section at zygomatic band) | 0.70 ± 6% of prediction | lion [D] |
| S2 | Muzzle width at canine station (surface-true, merged tissue+jaw) | ratio 0.186 (vector #2) ± 6% | hybrid [D] |
| S3 | Muzzle depth (rostrum, palate→dorsal at canine station) | 0.23 (vector #4: 0.20 + 30% span) ± 6% | lion [E] |
| S4 | Muzzle fraction (anterior orbit plane → nose, / L) | 0.28 ± 6% | lion [E] |
| S5 | Mandible length / L | 0.74 ± 6% | **[S]** |
| S6 | Orbit Ø | 0.17 ± 6% | lion [E] |
| S7 | Orbit centre height above palatal line (OrbitHeight) | 0.18 ± 0.02 | lion [E] |
| S8 | Orbit station u (from prosthion) | ≈ 0.36 | lion profile station [E] |
| S9 | Ear length | 0.22 ± 6% | lion [E] |
| S10 | Ear tip height above palatal line | 0.14 ± 0.02 | lion [E] |
| S11 | Full head height (palate→crown, jaw closed) | ≈ 0.72–0.76 | v4 base reads 0.7586 at neutral; lion vector moves it modestly |
| S12 ★ | Mane max width | **1.02 ± 0.05** at ≈ 0.60 of head height | Poly Haven + Roaring (§2.2/2.3) |
| S13 ★ | Mane crown width | ≤ 0.80 × S12 | statue profiles |
| S14 ★ | Ear tip vs mane surface | tips ≤ mane surface (peek ≤ +0.005) | canon: half-buried |
| S15 ★ | Brow projection | brow band front surface ahead of the nasal-bridge line by 0.02–0.05 at the orbit station | Poly Haven (§2.2) |
| S16 | Jaw hinge | v5 hinge (0, −0.2167, −0.1249), **unchanged** | pipeline constraint |
| S17 | Teeth clearance at jaw −10°/−20°/−30° | **0 overlapping triangle pairs** (BVH), min clearance reported | v4/v5 gate |
| S18 | Symmetry | max L/R vertex deviation ≤ 0.001 | v5 cage achieved 0.000133 |
| S19 | Fold gate | min normal dot ≥ +0.01 on tissue + jaw, rest and jaw −30° | house ship gate |
| S20 | Lip cage integrity | cage loop counts constant rest vs jaw-open; 0 inverted cage faces | v5 structure |

## 5. Mechanism blueprint — the face machine (ours, from working references)

Two reference rigs were probed bone-by-bone. Their **layouts** are adopted
and adapted; their meshes are not used. Licence note: catperson is **CC0**
(layout adoption is unrestricted); the Rigify lion is CGTrader RF —
studied for layout only, consistent with the standing study-tier rule.

### 5.1 Catperson (CC0) — primary layout

145 bones. Face-relevant layout (positions normalised: head-bone base =
origin, head length ≈ 0.18 file units):

- `defHead` ← `defNeck`; jaw pivot `defJawL` sits at head-base height,
  slightly forward of the head axis; jaw reach ≈ 0.53 × head length.
- `defteethLower` is a **child of the jaw bone** — the lower arcade rides
  the jaw as one rigid bone-parented unit.
- **Tongue: 4-bone chain rooted under `defteethLower`** (defTongue.000 →
  .003), total reach ≈ 0.51 × head length, running along the mouth floor.
- `defJawU` — a separate **upper-jaw bone** (child of defHead) carrying
  the upper lip chains: `defLipU` + .001 + .002 per side, following the
  lip line from centre to commissure.
- Eyeballs: `defEyeball.L/R` at ±0.29 × head-width, pointing forward.
- **Eyelids: a 5-bone fan per lid per side** — root at the globe centre
  height, two branches (lateral .001→.003, medial .002→.004) wrapping
  the globe, plus `ctrl` bones for lid targets. Upper and lower lids
  both fully boned. This is how its lids *follow the globes*.
- Ears: 3-bone chains (`defEar.000/.001/.002`) per side.
- A small `defNose` bone at the nose pad.

### 5.2 Low-poly lion Rigify face rig — the brow/cheek supplement

823 bones (full Rigify). Its face rig contributes what catperson lacks:

- **Forehead chains**: `ORG/DEF-forehead.L/R` × 3 bones per side,
  sweeping from the brow line up-outward — brow *deformation* bones.
- **Brow bones**: `brow.B.L/R` (+ ORG partners) hung under `master_eye` —
  the brow rides with the eye assembly's control, not the skull.
- **Cheek bones**: `cheek.T` / `cheek.B` per side.
- **Teeth as bones**: `teeth.T` / `teeth.B` (upper/lower arcade bones).
- **Lip bones**: `lip.T` / `lip.B` per side from the face root.
- Eyes: `eyes` master → `eye.L/R`, under an `MCH-eyes_parent`.

### 5.3 Zach set — mouth-part densities and proportions

Separate parts measured in `character_assets/drive-models/Zach (1).blend`
(licence UNKNOWN — proportions/densities only, no geometry reuse):

| Part | Verts | Proportions (arcade width W = upper teeth width) |
|---|---|---|
| Teeth top | 6,911 | W = 1.00; arcade length 1.20 W; height 0.54 W |
| Teeth bottom | 5,343 | width 1.09 W; length 1.00 W |
| Tongue | 602 | width 0.56 W; length 0.98 W |
| Eye (one) | 1,028 (pair mesh) | globe Ø ≈ 0.32 × W |

Density guidance for our own parts at Kaleaon's scale (arcade width
≈ 0.45 L): upper arcade 4–7k verts is the premium band; tongue ≈ 600
verts at 0.55 W wide is proven-sufficient; globes ≈ 1k verts each.

### 5.4 Our face-bone layout (mapped to the 89-bone rig family's naming)

Target layout for rig integration. Phase 2 delivers the **geometry +
node pivots** (the base-head line's established scope: jaw articulation
is the Jaw node's transform, TeethLower carries the copied pivot — the
v4/v5 pattern); skinning this layout onto the r3 rig is the rig pass
that follows, exactly as Sen's head shipped geometry-first.

```
CC_Base_Head
└─ CC_Base_FacialBone
   ├─ CC_Base_UpperJaw
   │  ├─ Teeth01                (upper arcade, rigid)
   │  └─ LipU01→02→03 .L/.R     (from catperson defLipU chains)
   ├─ CC_Base_JawRoot           (pivot = v5 hinge, §4 S16)
   │  ├─ Teeth02                (lower arcade, rigid; catperson defteethLower pattern)
   │  ├─ Tongue01→02→03         (r3 standard chain; catperson's 4th root bone
   │  │                          maps to the JawRoot-parented base segment)
   │  └─ LipL01→02→03 .L/.R     (from Rigify lip.B pattern)
   ├─ Eye.L / Eye.R             (globes; catperson defEyeball placement)
   ├─ LidU01…05 .L/.R           (catperson 5-bone fan: root, lat .001→.003,
   │                              med .002→.004 — renamed to our sequence)
   ├─ LidL01…05 .L/.R           (lower-lid fan, same pattern)
   ├─ Brow01→02→03 .L/.R        (Rigify forehead chains, muscle-layer drivers)
   ├─ CheekT / CheekB .L/.R     (Rigify cheek bones)
   ├─ Ear01→02→03 .L/.R         (catperson 3-bone ear chains)
   └─ Nose01                    (catperson defNose; nose-pad stability —
                                 glasses bridge rests on skin above it,
                                 glasses themselves parent to CC_Base_Head)
```

Rest-pose rules bound to this layout (standards v2 §4): jaw rotates
about S16 only; tongue stays inside the mouth through the full jaw
range; arcades never intersect lips or tongue at any tested angle;
lids meet along a continuous seam when closed (fan geometry sized to
the globe, §6).

## 6. Parts list (Phase 2 geometry deliverables)

Layered construction per the house rule — **skull → muscles → tissue**
(a surface merely wrapped over the form reads skeletal; that was v1's
failure). The v5 base already carries the layers: Skull 3,526 v,
SkullMandible 2,351 v, Muscles 763 v, TissueHead 4,096 v, Jaw 2,351 v,
plus the lip cage (tissue 405 / jaw 405 cage verts, philtrum column,
commissures at (±0.2285, 0.0953, −0.1868) in the v5 frame).

| Part | Source in build | Notes |
|---|---|---|
| Skull + SkullMandible | v5 layers, bone-layer sliders (Cranium*, JawDepth/Profile) | sagittal **crest strip** added (large-male lion variant, species spec §3.4): a subtle midline ridge mesh on the cranium |
| Muscles layer | v5 Muscles, muscle-layer sliders (Brow* muscle components, masseter via JawDepth) | brow mass lives here + tissue padding |
| TissueHead + Jaw | v5 surfaces with the **lip cage**, species-deformed by §3 | smile-line path per §3 build deltas |
| TeethUpper / TeethLower | v5 split arcades, following muzzle/jaw fields | felid dentition plan: large canines, short tooth row (§3.4 teeth variant `teeth_felid`); if the v5 arcades are generic-plan, a canine-emphasis pass is part of Phase 2, flagged in the build doc |
| Tongue | v5 tongue, re-proportioned per §5.3 | width ≈ 0.55 × arcade width, length ≈ 1.0 × arcade width; chain per §5.4 |
| Eyeball_L/R + Iris + Pupil | v5 eye assembly, scaled/moved by Eye* sliders | globe Ø 0.17 L; iris green (material later); **pupil shape: round per the sheet** — felid slit is the species-true alternative, flagged F7 for Joe |
| Eyelid + LidMargin_L/R | v5 lid assembly | must fully close (fan-sized to globe); rest coverage 15–20% of iris (neutral open ruling) |
| NoseLeather | v5 nose group, `nose_felid` form | sculpted pad: nostrils, philtrum groove to the upper lip (v5 cage has the philtrum column), slight overhang |
| Ear_L / Ear_R | v5 ears → `ear_round` variant | small, low, rounded; §4 S9/S10/S14 |
| **Mane shell** | **NEW geometry** (authored in Phase 2) | sculpted shell, not groom: silhouette per S12/S13, swept back and out, merging toward the neck/shoulders at its base; ears half-buried in it (S14); temple clearance corridor for glasses (§1); underside left open for the later groom + braid root |
| Cheek tufts L/R | NEW — distinct masses flanking the muzzle | per standards v2 §2.2 (not part of the mane shell) |
| Chin tuft mass | NEW — under-chin mass | carries the goatee later (F5) |
| Whisker pads | tissue field (§3) | geometry swell now; follicle dimples later |

**Explicitly NOT in this build:** glasses (accessory system), mane
groom / hair curves, the central braid (groom), markings / rosettes /
coat colours (materials), the `Relaxed` and expression morph set
(expression system — the geometry must *support* them, §1).

## 7. Assembly on the r3 body

- Body: `bodies-3d/kaleaon` r3, 89-bone rig (`kaleaon-rigged3`).
  Standing height ≈ **2.05 m** (crown 2.049 in the current build);
  rig jaw pivot `CC_Base_JawRoot` at body-space **(0, +0.055, 1.800)**,
  axis X (rigged3 REPORT).
- **Head L at assembly = 0.42 m** (nose tip → occiput). Consequences:
  height / L ≈ 4.9 (small-head bara read, canon); face height
  (S11 ≈ 0.72–0.76 L) ≈ 0.30–0.32 m — matching the r3 build's existing
  face height (0.30 m) so the swap doesn't rescale his presence;
  orbit Ø ≈ 7.1 cm; arcade width ≈ 19 cm.
- **Seat constraint:** at assembly, the head's hinge (S16) must land
  exactly on the rig's JawRoot pivot; the neck skirt blends down to
  NeckTwist02 (r3 pattern). The head-local hinge in L units is
  (0, −0.2167, −0.1249) — at L = 0.42 m that is 9.1 cm behind the
  occiput plane line and 5.2 cm below the frame origin height; the
  assembly transform is solved from these two fixed points, not eyeballed.
- Head/torso check is a **render gate** (§8), not just a ratio: the
  context render on the r3 body is where "small relative to the torso"
  gets judged.

## 8. Phase 2 — build procedure and QA gates

Machinery: the proof-pipeline head route (Sen's
`characters/sen/scripts/build_head.py` pattern — smooth-field
deformations with proportional ratio factors, per-object, with a
per-slider coverage report), adapted to the v5 object set (split teeth,
lip cage, layers in the .blend). Stage discipline per the quality bar:
**a .blend checkpoint per stage, verified before the next stage builds
on it.**

Stages:
1. **Base audit** — open v5 .blend; record objects, groups, hinge,
   pal_z, landmarks (the Phase A audit pattern, standards v2 §3).
2. **Skull + muscle layers** — bone/muscle-layer sliders; crest strip.
3. **Tissue + jaw** — tissue-layer sliders, whisker pads, chin mass,
   smile-line path check against the cage.
4. **Mouth machine** — teeth follow fields; tongue re-proportioned;
   jaw-open series.
5. **Eyes** — globes/lids seated; closure test; rest coverage measured.
6. **Ears** — `ear_round` shaping + placement (S9/S10).
7. **Mane shell + cheek tufts + chin tuft** — authored geometry (S12–S14).
8. **Export + gates + renders.**

QA gates (all numeric, reported in KALEAON_HEAD_BUILD.md):
- Station table §4 measured vs target (both rulers where width is
  concerned); every miss itemised, none averaged away.
- Jaw-open −10° / −20° / −30°: BVH teeth-overlap = 0 pairs (S17);
  tongue inside the mouth bounds at all three angles; lip-cage
  integrity (S20).
- Fold gate S19 on tissue + jaw at rest and at −30°.
- Symmetry S18.
- QA gauntlet on the exported GLB: parses, 0 degenerate, 0 NaN.
- **Clay renders** (headless, `--threads 2`, flat studio world, no
  HDRI): front / three-quarter / profile / jaw-open three-quarter,
  plus the **head-on-body context render** on the r3 body (§7 gate).
- Per-slider coverage report (full / partial / none) — the honest
  accounting the Sen build established; any slider that cannot take a
  geometry path is reported, never silently dropped.

## 9. Conflicts and flags register

- **F1 — "Deep boxy" vs "broad and soft" muzzle.** Survey yardstick vs
  standards v2 §2.2. Reconciled in §1/§3: boxy stations, soft surface.
  If Joe wants the surface harder/more realistic, that's a tissue-pass
  change, not a proportion change.
- **F2 — Fleshed vs skull ZB.** Leopard A2 fleshed read 0.842 vs skull
  anchor 0.723 [S] (§2.1). Two-layer discipline adopted; acceptance
  gates use the proportional method so the discrepancy can't
  masquerade as a build error (the v4 MuzzleWidth lesson).
- **F3 — Leopard A2 copy is fused.** The survey's "separate globes,
  teeth, tongue" are not separate objects in the landed native .blend.
  Orbit Ø therefore comes from the literature [E], not from this file.
- **F4 — Interorbital tension (standing).** The base head seats the eyes
  at 0.1122 L against the spec's 0.19 anchor; the spec ruling is still
  owed (v3/v4 docs). Kaleaon's EyeSpacing +25 is applied
  *proportionally* (Sen convention), preserving the base's physical
  seating. This build does not force or prejudge the ruling.
- **F5 — Goatee colour open** (white per sheet vs dark per album colour
  piece). Groom-tier; the chin *mass* is built either way (§6).
- **F6 — Faint spots on one sheet head study** vs the confirmed
  face-clean ruling. Markings-pass question; no geometry impact.
- **F7 — Pupil shape.** Sheet studies read round (stylised); species
  truth is a vertical slit. Default in this spec: **round, per the
  sheet** (authority order §0). Flagged for Joe — it's an iris-geometry
  variant, cheap to change later.
- **F8 — Lion verticals are [E].** No measurable lion skull pass exists
  (spec §5.2); the puma CT column [D] carries the felid pattern. If a
  lion CT skull is ever measured, S7/S10 and sliders #32–37 get a
  verification pass.
- **F9 — BrowScowl character delta** (#31: +10 vs lion preset +20) is
  an [E] art call from the sheet's gentle default, recorded here so it
  isn't mistaken for the species value.

## 10. Phase 2 gate — v5 status at spec time

Phase 2 builds **only** on base-head-v5, and only when its GLB/blend
**and BUILD_V5.md** are present (the doc is the verification record —
geometry without it is an unverified base).

At the time of writing: `base-head-v5/` contains
`neutral_base_head_v5.blend` + `.glb` + `groups.json` and a build log
showing the lip cage built (cage 405/405, philtrum column, symmetry
error 0.000133) — but **BUILD_V5.md is not yet present** and the v5
renders folder is empty. **Phase 2 therefore waits.** The moment
BUILD_V5.md lands, §8's procedure runs as written.
