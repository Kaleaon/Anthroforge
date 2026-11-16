# Species Head Spec — Editable Mammalian Base Head for AnthroForge

*Groundwork spec, Nov 12, 2026. Premise (Joe's direction): mammalian heads share one
structural plan, so species heads should be **editable deformations of a single base
head mesh** — shared skull/muzzle/ear/jaw topology plus per-species parameter sets,
the same learn-the-deformation philosophy as the body-morph pipeline. This document
is research + design only; it does not modify the app or any model.*

*Conventions: all proportions are ratios to total skull/head length **L** (nose tip →
occiput) unless stated otherwise. Every number is tagged **[S]** sourced (citation in
§2), **[D]** derived arithmetically from sourced numbers, or **[E]** estimate — an
informed design target with no direct measurement behind it. Estimates are never
presented as measured fact.*

---

## 1. Library inventory — head geometry we already own

Verified on disk Nov 12, 2026. Vertex/joint counts are from direct glTF/GLB header
parses (accessor counts), not catalogue copy.

### 1.1 Anthro (biped) full-body models with usable heads

| Model | Path | Species | Format | Rigged? | Size | Head notes |
|---|---|---|---|---|---|---|
| Codaj anthro fennec ("Pyn") | `stick-figure-avatar/furry-lineup/threejs-lineup/models/pyn_fennec.glb` (= `bodies-3d/parts-library/sketchfab/anthro-fennec-rigged-codaj/anthro_fennec_rigged.glb`) | **Fennec fox** | GLB, single skinned mesh, 41,304 verts | Yes — 107 joints | 3.96 MB | Best-in-library head rig: named bones `Head`, `Ear1–4_L/R` ear chains. Single mesh = cleanest registration candidate. CC-BY. |
| Bara wolf avatar | `…/threejs-lineup/models/bara_wolf_avatar.glb` | **Wolf** | GLB, 72,166 verts (main mesh 69,190 + 2 eye spheres) | Yes — 65 joints (Mixamo-style, `Head` bone) | 6.32 MB | Head is fused into the single body mesh; eyes are separate sphere meshes (1,488 verts each). No ear bones. |
| CVRxEarth wolf ("Big Bad Wolf / Death V2") | `…/threejs-lineup/models/wolf_cvrx/` (also `bodies-3d/parts-library/existing-haul/wolf-rigged-ccby/`) | **Wolf** | glTF + bin, 67,426 verts, 34 meshes | Yes — 222 joints | 13.3 MB bin | Most articulated wolf we own; head/ear/paw donor-grade. CC-BY. |
| AKM cat base | `…/threejs-lineup/models/cat_base.glb` (= `parts-library/sketchfab/anthro-female-cat-base-akm/`) | **Domestic cat** | GLB, 5,731 verts, 7 meshes | Yes — 63 joints | 530 KB | Named `head`, `ear_base`/`ear_tip` bones L/R; **ears are a separate mesh** (460 verts) — head/ear split is exactly the topology discipline the base head needs. CC-BY. |
| Kitty Base (ChocolateMilkCows) | `…/threejs-lineup/models/kitty_base.glb` (= `parts-library/sketchfab/kitty-base-chocolatemilkcows/`) | **Cat** | GLB, 15,890 verts, 1 mesh | **No** — 0 joints, static | 780 KB | Higher-res cat head shape, but unrigged; shape reference / registration target only. |
| Persipia (AKM) | `…/threejs-lineup/models/persipia.glb` | **Cat** (clothed character) | GLB, 29,105 verts, 11 meshes | Yes — 65 joints | 2.96 MB | Same AKM rig family as cat base + border collie (same bone names) — see §4 on the AKM family. Hair mesh dominates vert count. |
| Border Collie scientist (AKM) | `…/threejs-lineup/models/border_collie.glb` (= `parts-library/sketchfab/border-collie-scientist-akm/`) | **Dog** (collie) | GLB, 8,757 verts, 12 meshes | Yes — 66 joints | 1.69 MB | Named `head`, `ear_base`/`ear_tip` bones; separate `collie_ears` mesh. A pedigree mesaticephalic-ish dog head on the same rig family as the AKM cat — the library's best built-in canid-vs-felid comparison pair. |
| Female dog furry (RHL89RYO) | `parts-library/sketchfab/female-dog-furry-rhl89ryo/generic_productfemale_dog_furry.glb` | **Dog** | GLB, 58,032 verts, 16 meshes | Yes — 144 joints | 8.25 MB | Long ear bone chains (`Ear_L` + 6 segments). High-res anthro dog head donor. |
| Fox fem, full rig (Azuliezeiro) | `parts-library/sketchfab/fox-fem-full-rig-azuliezeiro/fox_fem._full_rig.glb` | **Fox** (generic/stylised red fox) | GLB, 5,802 verts, 8 meshes | Partially — 1 skin, low joint count in GLB parse | 301 KB | Lightweight fox; eyes are separate meshes. Usable fox shape reference. |
| Cute furry fox (Enotobuterbrodo) | `parts-library/sketchfab/cute-furry-fox-enotobuterbrodo/cute_furry_fox.glb` | **Fox** (stylised) | GLB, 19,209 verts, 2 meshes | No — static | 4.85 MB | **Head is a separate mesh** (`Lisa_low_Head`, 10,942 verts) — easiest head isolation in the library. Stylised proportions; shape reference only. |
| BVH rig fox/rabbit/cat (Kitsunzoro) | `parts-library/sketchfab/bvh-rig-fox-rabbit-cat-kitsunzoro/bvh_rig_models_update_fox_rabbit_and_cat.glb` | Fox + cat (+rabbit) | GLB | Rigged (BVH-derived) | 15.7 MB | Three species in one file; not yet dissected. CC-BY-SA ⚠️ (keep separate per library licence discipline). |
| Cat-person (hiamBoz) | `character_assets/catperson-furry-CC0.blend` (= `parts-library/existing-haul/catperson-furry-cc0/`) | **Cat** (anthro) | .blend, mesh + FK rig | Yes | 5.7 MB | CC0 anthro feline head/ear donor. |
| Toriel head rig (DM2206) | `parts-library/sketchfab/toriel-head-rig-dm2206/toriel_head_rig.glb` | Goat-like monster (not a target species) | GLB, 2,613 verts, 10 meshes | Yes — 46 joints | 281 KB | **Head-only rig** with `LeftEar`/`RightEar` + ear chains — the library's only head-only rigged asset; useful as a rig-design reference for the base head even though the species is off-list. |

### 1.2 Quadruped / statue / scan heads

| Model | Path | Species | Format | Rigged? | Size | Head notes |
|---|---|---|---|---|---|---|
| Leopard Animation Run (GremorySaiyan) | `parts-library/sketchfab/leopard-animation-run-gremorysaiyan/leopard_animation_run.glb` | **Leopard** | GLB, 3,644 verts | Yes — 47 joints (`Bip01_Head`, `BN_Ear_L/R`) | 951 KB | **The only true leopard geometry we own.** Low-poly quadruped, run animation. Rosette coat texture. CC-BY. |
| Cougar (GalileoGB) | `parts-library/sketchfab/cougar-galileogb/source/FemaleCougar_ForSale.blend` | **Cougar / puma** | .blend, 17.5k tris | Yes — 1 animation | — | Big-cat head geometry adjacent to leopard/lion; the Florida "panther" *is* a cougar, so this is also our nearest "panther" stand-in by that usage. CC-BY. |
| Leopard Hybrid A2 (Animated3D) | `parts-library/cgtrader/leopard-hybrid-a2-animated3d/` | Leopard hybrid (anthro humanoid) | FBX/Blend zips + optimised FBX (2.3 MB) | Yes (per pack name/contents) | ~700 MB of zips | Anthro leopard-hybrid; heavy archives, not yet extracted/verified at mesh level. |
| Lion Head (Poly Haven) | `parts-library/polyhaven/lion-head/lion_head_1k.gltf` | **Lion** | glTF, 25,380 verts, 1 mesh | No — static scan | 1.1 MB bin | **Head-only photogrammetry scan of a lion-head sculpture.** Highest-detail lion head shape we own; statue proportions, no rig, no separate jaw. CC0. |
| Roaring Lion (Siraliraza) | `parts-library/sketchfab/roaring-lion-siraliraza/roaring_lion.glb` | **Lion** | GLB, 33,392 verts, 1 mesh | No — static | 4.22 MB | Full-body statue scan; open-roar pose — expressive lion face/mane reference, not a neutral head. CC-BY. |
| Lion models (VladLarin326) | `parts-library/cgtrader/lion-models-vladlarin326/` | **Lion** | .blend (911 MB!) + FBX (2.3 MB) + OBJ (7.1 MB) + STL | Per source pack | ~925 MB | OBJ/FBX are the practical entry points; the .blend is outsized. Mesh-level verification not done. |
| Low-poly lion (UnityKing24) | `parts-library/cgtrader/low-poly-lion-unityking24/` | **Lion** | FBX + .blend, walk animation FBX | Animated | ~25 MB | Low-poly quadruped lion; proportion reference only. |
| Golden retriever (iRahulRajput) | `character_assets/golden-retriever-CCBY.zip` (parts library holds textures + scene.gltf only; full 42 MB bin in the zip) | **Dog** (retriever — a textbook mesaticephalic breed) | glTF, 423,175 verts | No — static | 40 MB zip | Very high-res quadruped dog; head shape reference for the dog preset. CC-BY. |
| Cat, rigged (Vr-cvantorium) | `parts-library/existing-haul/cat-rigged-ccby/` | **Domestic cat** | glTF, 1,750 verts | Yes — 35 joints + run anim | 243 KB | Low-poly quadruped cat. |
| Terris wolf (GalileoGB) | `parts-library/sketchfab/terris-wolf-galileogb/source/SKETCHFABVERSION.fbx` | **Wolf** | FBX | Rigged (per pack) | — | Additional wolf donor; FBX, not yet mesh-verified. |
| styloo animals | `parts-library/existing-haul/styloo-animals-cc0/cat.glb` / `dog.glb` (orig. `character_assets/styloo-animals-CC0.zip`) | Cat / dog | GLB, 2,547 / 3,344 verts | Yes (large joint counts, stylised) | 349 KB / 1.57 MB | CC0 low-poly proportion sketches; minor value for heads. |
| Bearyl Canine base (Jinxxy) | `parts-library/jinxxy/bearyl-canine-archa/` (`Canine_Blend_V4.0.0.zip` etc.) | **Dog/wolf** (canine avatar base) | Unity/Blend/Substance zips | Yes (avatar base) | ~2.7 GB total | A full canine avatar system — potentially a major head donor, but unextracted and licence is a purchase licence (see folder LICENSE.txt); treat as study-only until reviewed. |
| Hobkin community edit (Jinxxy) | `parts-library/jinxxy/wolfy527-hobkin-community/` | Canine (dogkin) | .unitypackage + Substance | Yes | ~185 MB | Unextracted; same caution as Bearyl. |

### 1.3 Species coverage verdict

| Species | Have a usable head? | Best asset(s) |
|---|---|---|
| Grey wolf | ✅ Yes, two rigged anthros + quadruped donors | CVRxEarth wolf; bara wolf |
| Red fox | ⚠️ Partial — generic/stylised foxes only, no red-fox-specific model | Fox fem full rig; cute furry fox (separate head mesh) |
| Fennec fox | ✅ Yes — the best head rig in the library | Codaj anthro fennec |
| Lion | ✅ Yes — head-only scan + statues + packs (no rigged anthro lion head) | Poly Haven lion head; Roaring Lion |
| Panther (melanistic leopard/jaguar) | ❌ **No melanistic model — and none needed geometrically** (see §3.4: melanism is coat, not shape). Leopard shape: ✅ leopard run GLB + cougar + leopard hybrid | Leopard Animation Run; Cougar |
| Domestic cat | ✅ Yes, several, incl. two rigged anthro bases | AKM cat base; Kitty Base; cat-person |
| Dog (mesaticephalic) | ✅ Yes | Border Collie (AKM); female dog furry; golden retriever (shape ref) |
| Bear | ❌ **No model** — known gap (Sen has no donor) | — |
| Badger | ❌ **No model** — known gap (Brand) | — |
| Owl | ❌ No model — and **out of scope for this spec**: avian skull (beak, no muzzle/jaw plan in the mammalian sense) does not deform from the mammalian base; it needs its own base if ever tackled. Stated once, per brief. | — |

---

## 2. Comparative proportions research

Ratios below are the load-bearing ones for the slider design in §3. Sources are
zoology / veterinary-anatomy literature and reference works; each fact carries its
source. Where a ratio could not be sourced it is marked **[E]** and excluded from
this section's claims (estimates live in §3's derivation column instead).

### 2.1 Canids

- **Grey wolf skull size/shape [S]** — 48 Iranian wolf skulls (Acta Theriologica,
  via ResearchGate): greatest length mean **235.65 mm**, max zygomatic width mean
  **125.18 mm** → **ZB/L = 0.53**; braincase (cranial) width 75.71 mm → **0.32 L**;
  rostrum width 43.08 mm → **0.18 L**; frontal breadth 58.56 mm → **0.25 L**.
  Bulgarian/European male compilation (Agric. Sci. & Technol. 2025): GL 250.17 mm,
  ZW 139.04 mm → ZB/L = 0.56; mandible length 184.97 mm → **mandible/L = 0.74**;
  mandible height 77.2 mm → 0.31 L.
- **Wolf ears are relatively small [S]** — ear height 90–110 mm against a skull of
  230–280 mm → **ear ≈ 0.36–0.40 L**, described as "relatively small and triangular"
  (ASM Mammal Diversity / iNaturalist species account).
- **Red fox skull [S]** — adult skull length **129–167 mm**; classic craniometry
  (Huxley 1880, Proc. Zool. Soc.): total length 143 mm, zygomatic width 74 mm →
  **ZB/L = 0.52**. Fox skulls are narrower-muzzled than dogs', with a concave
  (not convex) dorsal profile (Wikipedia species account summarising standard refs).
- **Red fox face proportion [S→D]** — Egyptian red fox morphometric study
  (J. Adv. VetBio Sci. Tech.): **facial index 62.7** (facial length ≈ 0.63 × cranial
  length), cephalic index 49.3 → derived facial fraction of total length ≈
  0.63/1.63 ≈ **0.39 L**. (That study's absolute lengths run large; the index, a
  ratio, is the usable part.)
- **Red fox mandible [S→D]** — Warsaw craniometric study (Animals/PMC 2024):
  mandible (LDA) length 105.45 mm; independent radiographic study gives red fox
  total skull length 139.22 mm → **mandible/L ≈ 0.76**.
- **Red fox ears [S]** — ears **7.7–12.5 cm** against skull 12.9–16.7 cm →
  **ear ≈ 0.6–0.75 L** — roughly double the wolf's relative ear size.
- **Fennec fox ears are the canid extreme [S]** — pinnae **10–15 cm** (Larivière
  2002, Mammalian Species 714, via EOL/IUCN accounts; San Diego Zoo factsheet
  range 8.6–9.7 cm on measured specimens) on a head-body length of 24–41 cm;
  **the largest ear-to-body ratio of any canid**, and the pinnae are **longer than
  the animal's face** (NR Wildlife species profile). Ear length approaches or
  exceeds total skull length — no other target species is close.
- **Dog cephalic classes [S]** — cephalic index = skull width × 100 / skull length;
  mesaticephalic = intermediate (Labrador, Golden Retriever are the textbook
  examples); brachycephalic threshold ≈ skull width ≥ 0.80–0.81 × length
  (Wikipedia "Cephalic index in cats and dogs" after Evans, Miller's Anatomy of
  the Dog; FECAVA brachycephaly expert report 2019). A mid-size dog skull in the
  FECAVA-cited post-mortem series: length 20.02 cm, width 10.04 cm → W/L ≈ 0.50.
- **Caniform vs feliform face growth [S]** — caniforms (dogs, bears, raccoons)
  show more positive facial allometry than feliforms: "compared to a cat, a dog
  shows more growth in the face relative to the braincase" (RUNX2 facial-length
  study, BMC Evol. Biol. 2012). This is the deep reason one base head can span
  both families: the muzzle-length axis carries most of the canid↔felid difference.

### 2.2 Felids

- **Domestic cat face is ~20% of head length [S]** — "a relatively short face,
  corresponding to approximately 20% of total head length," with a globular,
  rounded skull and protruding zygomatic arches (European Shorthair CT morphometry,
  Vet. Sci. 2021, MDPI). Same study: skull length 8.94 cm, cranial (braincase)
  width 4.28 cm → **braincase W/L = 0.48**, cranial index 52.2%.
- **Domestic cat orbit is huge [S]** — Baladi cat CT study (Slov. Vet. Res. 2019):
  skull length 10.05 cm, orbit height 2.07 cm → **orbit Ø ≈ 0.21 L**; width at
  orbit level 6.47 cm → 0.64 L. Cats' enlarged orbit faces rostrally, "giving cats
  the most highly developed binocular vision of all carnivores" (Dyce/Sack/Wensing
  comparative anatomy, via VeterianKey).
- **Cat brachycephaly range (within one species!) [S]** — Persian cranial index:
  doll-face 0.66 vs peke-face 0.97 (J. Vet. Intern. Med. 2017). Evidence that the
  cranium-width and muzzle-length sliders need wide ranges even inside a species.
- **Big-cat skull width ratios [S]** — zygomatic width / basal length (Wroe et al.
  bite-force dataset, via WildFact comparative-cats compilation): **jaguar 0.837,
  leopard 0.723, lion 0.743, cougar 0.77**. Felid heads are far wider relative to
  length than any canid's (wolf ZB/L ≈ 0.53) — cheek width is a family-level signal.
- **Lion has the long rostrum of the big cats [S]** — lions have statistically
  significantly longer rostra and longer mandibles relative to skull length than
  tigers (Christiansen 2008; PLOS ONE felid crania study): lion **mandible/CBL =
  0.743**; leopard mandible/CBL ≈ 0.73–0.74 (Stein & Hayssen 2010, Mammalian
  Species, Panthera pardus). Lion overall skull: length 39.7 cm, width 28 cm →
  W/L = 0.71 (FECAVA-cited series).
- **Leopard vs jaguar size [S]** — large male leopard skulls ≈ 221–244 mm total
  length vs jaguar ≈ 279–290 mm; jaguar rostrum notably wider (museum measurement
  series via WildAnimalWarfare compilation). The "panther" preset in §3 is built
  on the leopard (the usual referent for a melanistic "panther" alongside jaguar).

### 2.3 Cross-cutting

- **Stop (forehead break)** — no sourced numeric angles exist in the literature
  found; qualitatively: brachycephalic dogs show a "marked fold (stop) between
  cranium and nasal bridge" (FECAVA 2019); red fox profile is concave; felids run
  a nearly unbroken forehead→nose line. §3 stop values are therefore **[E]** by
  design, ordered by these qualitative sources.
- **Eye size in canids** — no sourced orbit/skull ratio for wolf/fox/dog was found
  in this pass; §3 uses **[E]** values anchored on the sourced cat orbit (0.21 L)
  and the general carnivore pattern (felids > canids). Flagged as the weakest
  numbers in the preset table.

---

## 3. Parameter spec — the editable base head

### 3.0 Design rules

- **One neutral base head**: a generic mesaticephalic mammal, deliberately parked
  between the canid and felid averages (muzzle fraction 0.33 L, ZB/L 0.58) so no
  species sits at a slider extreme except where the animal genuinely is extreme
  (fennec ears — by design, they pin the top of the range).
- **BodySlide-style sliders**: value −100…+100, **0 = neutral base**. Each slider
  below names its *anchor ratio* (the real proportion it controls), the neutral
  value of that ratio, and the ratio change spanned by ±100 ("span"). Preset value
  = 100 × (species ratio − neutral) / span, rounded to the nearest 5. This keeps
  every preset number traceable to §2 instead of hand-waved.
- Sliders deform **vertex regions of the shared topology** (muzzle block, cranium
  shell, ear meshes L/R, jaw mesh, cheek band, brow band). Ear and jaw are
  separate meshes on the base, as they already are in the AKM bases (§1.1).
- Overall head **scale** is not a slider here — species size (lion skull 39.7 cm
  vs cat 8.9–10 cm [S]) is a single uniform scale applied at export.

### 3.1 Slider set — 31 sliders

**Muzzle** (region: rostrum block, nose tip → stop)

| # | Slider | Deforms | Anchor ratio | Neutral | Span (±100) |
|---|---|---|---|---|---|
| 1 | MuzzleLength | Rostrum block forward/back along head axis | muzzle fraction of L | 0.33 | 0.20 (→0.13…0.53) |
| 2 | MuzzleWidth | Rostrum width at canine level | rostrum W / L | 0.17 | 0.08 |
| 3 | MuzzleTaper | Nose-end width vs muzzle base (+ = pointier) | taper index | 0.50 | 0.40 |
| 4 | MuzzleDepth | Vertical depth of rostrum | rostrum depth / L | 0.20 | 0.10 |
| 5 | NoseSize | Nose leather scale (geometry swell at tip) | nose W / muzzle W | 0.55 | 0.30 |

**Cranium** (region: braincase shell + forehead)

| # | Slider | Deforms | Anchor ratio | Neutral | Span |
|---|---|---|---|---|---|
| 6 | CraniumWidth | Braincase width | braincase W / L | 0.36 | 0.16 |
| 7 | CraniumHeight | Dome height incl. sagittal rise | skull height / L | 0.31 | 0.12 |
| 8 | CraniumLength | Occiput↔orbit length share | cranium fraction of L | 0.62 | 0.20 |
| 9 | StopAngle | Profile break at forehead→nose (+ = deeper stop) | stop depth index | 0.30 | 0.40 |
| 10 | ForeheadWidth | Frontal breadth between orbits | frontal W / L | 0.24 | 0.12 |

**Ears** (regions: ear meshes L/R, mirrored)

| # | Slider | Deforms | Anchor ratio | Neutral | Span |
|---|---|---|---|---|---|
| 11 | EarHeight | Pinna length | ear length / L | 0.40 | 0.65 (→0.40…1.05 at +100: sized so fennec ≈ +100) |
| 12 | EarWidth | Pinna breadth | ear W / ear length | 0.55 | 0.35 |
| 13 | EarPlacementHeight | Ear base up/down the cranium | placement index | 0.50 | 0.40 |
| 14 | EarSpread | Ear base lateral position + outward cant | spread index | 0.50 | 0.40 |
| 15 | EarTilt | Rotation: − = folded/flopped, + = pricked forward | tilt index | 0.55 | 0.50 |
| 16 | EarTipPoint | Tip rounding ↔ point (continuous part only — see §3.4) | tip radius index | 0.50 | 0.45 |

**Jaw / Cheeks** (regions: jaw mesh, zygomatic band, cheek/ruff soft tissue)

| # | Slider | Deforms | Anchor ratio | Neutral | Span |
|---|---|---|---|---|---|
| 17 | JawDepth | Ramus height (jaw depth under the ear) | mandible height / L | 0.28 | 0.12 |
| 18 | JawLength | Mandible length | mandible length / L | 0.74 | 0.10 |
| 19 | JawWidth | Bi-angular (jaw hinge) width | jaw W / L | 0.40 | 0.14 |
| 20 | CheekWidth | Zygomatic arch flare — the master head width | ZB / L | 0.58 | 0.20 |
| 21 | RuffVolume | Cheek/neck fur mass (soft tissue shell, not bone) | ruff index | 0.30 | 0.50 |

**Eyes / Brow** (regions: orbit band, brow band; eyeball meshes scale/move)

> **Revision, Nov 12, 2026 (per `brow-study.md` §6.1):** the single
> BrowRidge slider is retired and replaced by the seven-slider brow
> vector (#25–31) — this spec goes from 25 to 31 sliders. The brow
> sliders are hominin-calibrated (brow-study §5); canids and felids
> have no supraorbital torus, so all species presets carry *negative*
> BrowProjection and their brow emphasis is re-homed to BrowShelf,
> BrowScowl and BrowPadding (§3.3).

| # | Slider | Deforms | Anchor ratio | Neutral | Span |
|---|---|---|---|---|---|
| 22 | EyeSize | Eyeball/orbit scale | orbit Ø / L | 0.15 | 0.10 |
| 23 | EyeSpacing | Interorbital distance | interorbital W / L | 0.19 | 0.08 |
| 24 | EyeForwardness | Orbit convergence (− lateral … + forward-facing) | convergence index | 0.35 | 0.50 |
| 25 | BrowProjection | Brow band anterior projection — torus chord (skull layer) | midorbit projection chord (Smith & Ranyard) | 0 = recent modern human (12.5 mm) | range −50…+150 (Krapina +100 [D], gorilla +150 [E]) |
| 26 | BrowThickness | Torus vertical thickness (skull layer) | midorbit thickness chord | 0 = recent modern human (6.5 mm) | −100…+100 (Krapina +65 [D]) |
| 27 | BrowContinuity | Split superciliary components ↔ unbroken torus (skull layer) | brow component separation | −35 = pooled modern | −100…+100 (+100 = torus frontalis) |
| 28 | BrowShelf | Orbit overhang + post-toral sulcus depth (skull-led) | ledge/sulcus index | −20 = pooled modern | −100…+100 (gorilla +100 [E]) |
| 29 | BrowPosition | Soft brow-line height vs supraorbital rim (muscle/tissue) | brow-line offset | 0 = at rim (male pattern [S]) | ±0.028 L (female ≈ +50 [D]) |
| 30 | BrowPadding | Soft-tissue depth over the brow band (tissue layer) | supraorbital tissue depth | 0 = 6.0 mm | 3…9 mm |
| 31 | BrowScowl | Resting corrugator/procerus engagement (muscle layer) | medial brow depression | 0 = neutral rest | −100…+100 (full knit ≈ +85 [E]) |

### 3.2 Anchor-ratio table (the numbers the presets are computed from)

| Species | Muzzle frac | ZB/L | Braincase W/L | Ear/L | Orbit Ø/L | Mandible/L | Basis |
|---|---|---|---|---|---|---|---|
| Grey wolf | 0.42 [E] | **0.53 [S]** | **0.32 [S]** | **0.38 [S]** | 0.13 [E] | **0.74 [S]** | §2.1 |
| Red fox | **0.39 [D]** | **0.52 [S]** | 0.30 [E] | **0.65 [S]** | 0.14 [E] | **0.76 [D]** | §2.1 |
| Fennec fox | 0.36 [E] | 0.52 [E] | 0.34 [E] | **1.05 [D]** (ears ≥ skull length) | 0.17 [E] | 0.72 [E] | §2.1 |
| Lion | 0.28 [E] (longest felid rostrum [S-qual.]) | **0.70 [D]** (0.743 ZB/basal [S]; W/L 0.71 [S]) | 0.31 [E] | 0.22 [E] | 0.17 [E] | **0.74 [S]** | §2.2 |
| Panther (leopard) | 0.26 [E] | **0.67 [D]** (0.723 ZB/basal [S]) | 0.32 [E] | 0.22 [E] | 0.19 [E] | **0.74 [S]** | §2.2 |
| Domestic cat | **0.20 [S]** | 0.66 [D] (0.64 at orbit [S]) | **0.48 [S]** | 0.55 [E] | **0.21 [S]** | 0.72 [E] | §2.2 |
| Dog (mesaticephalic) | 0.44 [E] | 0.50 [D] (W/L 0.50 [S]) | 0.34 [E] | 0.40 [E] (erect-equivalent; see EarTilt) | 0.13 [E] | 0.74 [E] | §2.1 |

### 3.3 Species preset table

Slider values (−100…+100, 0 = neutral). Values in **bold** are computed directly
from a [S]/[D] anchor ratio via the §3.0 formula; the rest are design estimates
[E] set by the qualitative ordering in §2 (e.g. taper, stop, ruff have no numeric
literature — they are art-directed, and the table says so by leaving them unbolded).

| # | Slider | Wolf | Red fox | Fennec | Lion | Panther (leopard) | Cat | Dog |
|---|---|---|---|---|---|---|---|---|
| 1 | MuzzleLength | **+45** | **+30** | +15 | −25 | −35 | **−65** | +55 |
| 2 | MuzzleWidth | **+15** | −10 | −25 | +25 | +20 | −10 | +10 |
| 3 | MuzzleTaper | +10 | +35 | +40 | −10 | 0 | −20 | +5 |
| 4 | MuzzleDepth | +15 | −5 | −15 | +30 | +20 | −25 | +10 |
| 5 | NoseSize | +10 | 0 | −10 | +35 | +20 | −35 | +15 |
| 6 | CraniumWidth | **−25** | −35 | −10 | −30 | −25 | **+75** | −10 |
| 7 | CraniumHeight | 0 | −5 | +5 | +10 | 0 | +30 | 0 |
| 8 | CraniumLength | −10 | −10 | −5 | +10 | +10 | +40 | −10 |
| 9 | StopAngle | +10 | +5 | +15 | −25 | −15 | −30 | +25 |
| 10 | ForeheadWidth | **+5** | −10 | +20 | 0 | 0 | +50 | 0 |
| 11 | EarHeight | **0** | **+40** | **+100** | −30 | −30 | +25 | 0 |
| 12 | EarWidth | −10 | +10 | +60 | −20 | −15 | +5 | 0 |
| 13 | EarPlacementHeight | 0 | +5 | +20 | −5 | −5 | +15 | −5 |
| 14 | EarSpread | −5 | 0 | −10 | +20 | +15 | +20 | −10 |
| 15 | EarTilt | +5 | +5 | +10 | −10 | −5 | +5 | −65 |
| 16 | EarTipPoint | +15 | +30 | −5 | −60 | −50 | +35 | +5 |
| 17 | JawDepth | **+25** | −15 | −25 | +45 | +35 | −10 | +15 |
| 18 | JawLength | **0** | **+15** | −20 | **0** | **−5** | −20 | 0 |
| 19 | JawWidth | +10 | −15 | −20 | +30 | +15 | −5 | +10 |
| 20 | CheekWidth | **−25** | **−30** | −30 | **+60** | **+45** | **+40** | **−40** |
| 21 | RuffVolume | +35 | +15 | −10 | +90 | +10 | +5 | +5 |
| 22 | EyeSize | −25 | −10 | +20 | +20 | +40 | **+55** | −20 |
| 23 | EyeSpacing | **−5** | −25 | +10 | +25 | +10 | +50 | 0 |
| 24 | EyeForwardness | −10 | +15 | +25 | +50 | +55 | +70 | −5 |
| 25 | BrowProjection | −25 | −35 | −45 | −20 | −25 | −40 | −25 |
| 26 | BrowThickness | −20 | −30 | −40 | −15 | −20 | −35 | −25 |
| 27 | BrowContinuity | −20 | −35 | −50 | −25 | −30 | −55 | −30 |
| 28 | BrowShelf | +5 | −10 | −20 | +20 | +15 | −5 | 0 |
| 29 | BrowPosition | −10 | 0 | +10 | −10 | −5 | +15 | 0 |
| 30 | BrowPadding | +10 | 0 | −10 | +15 | +10 | +5 | +15 |
| 31 | BrowScowl | +10 | 0 | −10 | +20 | +15 | −5 | +5 |

Brow rows (#25–31) are per `brow-study.md` §6.1 [all E — design-equivalents
on a hominin-calibrated scale]: no canid or felid has a supraorbital torus,
so BrowProjection is negative (−20…−45) for every species, and the brow
emphasis the retired BrowRidge number carried now lives in BrowShelf,
BrowScowl and BrowPadding. **Compatibility shim (humanoid presets only):**
if an old preset file carries BrowRidge, map Projection ≈ 1.5 × BrowRidge —
and **never apply the shim to animals**; it would push a wolf's brow past a
modern human's, which is exactly backwards.

Worked derivations (spot checks):
- Wolf MuzzleLength: (0.42 − 0.33)/0.20 × 100 = **+45**. Cat: (0.20 − 0.33)/0.20 = **−65**.
- Fennec EarHeight: (1.05 − 0.40)/0.65 = **+100** — the range was sized around the
  fennec on purpose; it is the only preset that should ever pin a slider.
- Lion CheekWidth: ZB/L 0.70 [D] → (0.70 − 0.58)/0.20 = **+60**. Dog: 0.50 [D] → **−40**.
  This single slider carries most of the canid↔felid family signal (§2.2).
- Cat CraniumWidth: (0.48 − 0.36)/0.16 = **+75** — the cat's braincase really is
  that wide relative to its short skull [S].
- Dog EarTilt −65 encodes the Labrador-type **drop ear**: the dog baseline's ear
  *size* ratios are erect-equivalent (EarHeight 0), and the fold lives entirely in
  Tilt. An erect-eared mesaticephalic preset (shepherd-type) would set Tilt ≈ 0
  and EarTipPoint ≈ +20 — same base, no new geometry.

### 3.4 Discrete vs continuous — what sliders cannot do

These differences are **part variants or material variants**, not slider values.
Forcing them into sliders produces uncanny mush; they ship as swappable parts
riding on the same base topology.

| Difference | Why it's discrete | Treatment |
|---|---|---|
| **Lion mane** (adult male) | A whole fur shell with its own silhouette; RuffVolume +90 only fakes cheek fur | Separate mane shell mesh (several length variants), attached at cranium/neck region |
| **Ear tip families**: fully rounded (lion, leopard), pointed (cat, fox), **lynx tufts**, fold-ear (Scottish-fold type) | TipPoint covers the middle of the range; the extremes change topology/silhouette | Ear mesh variants: `ear_round`, `ear_point`, `ear_tuft`, `ear_fold` on identical ear-base topology |
| **Fennec inner ear** | The pinna's inner surface is enlarged, pale and furred — a surface/texture feature at a scale sliders don't address | Fennec ear variant with inner-ear material zone + fur card |
| **Nose leather shape** | Felid nose (wide, grooved philtrum, exposed) vs canid nose (narrower, different nostril plan) are different small meshes | `nose_canid`, `nose_felid` tip meshes, scaled by NoseSize slider |
| **Pupil shape** | Felid vertical slit vs canid round — iris geometry/shader, not head shape | Iris material/geometry variant on the shared eyeball mesh |
| **Whisker pads** | Felid muzzle has pronounced whisker pads; canid muzzle is comparatively smooth | Optional pad swell mesh for felid presets (vibrissae themselves are fur cards) |
| **Dog flews / jowls** | Loose lip geometry hangs past the jaw line; JawDepth scaling looks wrong | Lip drape variant mesh for flewed breeds |
| **Fangs / dentition sets** | Tooth size plan differs by family (felid short jaw, big canines; canid fuller tooth row) | Teeth set variants per family; jaw sliders only place them |
| **Sagittal crest** (large male lion) | A midline ridge — a crease feature, not a height change | Crest variant strip on cranium region (CraniumHeight gets you 80% there) |
| **Melanism ("panther" coat)** | Pure pigmentation — a black leopard/jaguar is geometrically a leopard/jaguar | **Material/texture only.** The panther preset = leopard geometry (§3.3) + melanistic coat. No panther geometry work is needed or should be scheduled. |

---

## 4. Fitting notes — applying the body pipeline to heads

The body pipeline has two cases; both transfer to heads directly.

**Case 1 — exact deltas (shared topology).** Once the §3 base head exists, any
*re-pose of that same base* (including each §3.3 preset, which is just a slider
vector) is exact by construction — presets ARE delta sets on the shared topology.
The interesting sub-case is the **AKM family** (§1.1): cat base, Persipia and
Border Collie share an author, a rig and bone naming (`head`, `ear_base`,
`ear_tip`), which smells like shared topology conventions. A cheap first check —
compare head-mesh vertex counts (cat base body mesh 3,749 verts vs collie 4,051)
— suggests the *bodies* differ, but the check has not been run per-head-mesh; if
the AKM **head** meshes turn out to share topology, cat↔collie exact head deltas
fall out for free and become the head pipeline's Fat-Males-style proof case.

**Case 2 — registration/fit (foreign topology).** Every library head in §1 is
foreign topology relative to the future base. The body method applies unchanged:
align by landmarks (nose tip, eye centres, ear bases, jaw hinge, occiput — all
present as bones in the rigged models), deform the base onto the target, report
**residual error** (mean/max surface distance) per fit, and keep only the learned
slider-vector + residual, per the learn-then-delete rule. Heads are actually the
*easier* registration problem: smaller area, rigid skull under the skin, and the
landmarks are unambiguous.

**Best first registration targets, in order:**
1. **Codaj fennec** — single skinned mesh, 107-joint rig with named head + ear
   chain bones (landmarks come free from the skeleton), clean 41k-vert geometry.
   It is also the highest-value fit: fennec anchors the extreme end of EarHeight,
   so its learned deltas calibrate the whole ear range.
2. **AKM cat base** — low vert count (fast fitting), ears already a separate mesh,
   head/ear bones named. The natural first felid fit.
3. **Border Collie (AKM)** — the canid counterpart on the same rig family; fitting
   cat + collie against one base gives the first measured canid↔felid delta pair.
4. **Cute furry fox** — head is already an isolated mesh (10,942 verts); zero
   dissection cost, stylised proportions (fit it, but weight its learned deltas
   below the realistic models').
5. **Poly Haven lion head** — the only lion *head-only* target and high detail
   (25,380 verts), but a statue scan: no rig, no jaw separation, sculptural
   proportions. Fit after the pipeline is proven on rigged models, and treat its
   residuals accordingly.
6. **Leopard run GLB** — the only leopard; low-poly quadruped (3,644 verts), so
   its fit calibrates proportions, not detail.

**What is missing before head-fitting can start:**
1. **The neutral base head mesh itself** — clean, symmetric, quad-dominant
   topology with named vertex regions matching §3.1 (muzzle block, cranium shell,
   ear L/R, jaw, cheek band, brow band), a jaw that opens, and a head bone set
   (skull, jaw, ear chains L/R, eye bones). **No library head can serve as-is:**
   the Codaj fennec is the closest in construction (single mesh, full head rig)
   but its proportions are the most extreme on the chart — adopting it as
   "neutral" would bake a fennec bias into every learned delta, and its mesh is a
   fused full body. The AKM heads are stylised low-poly. Verdict: **the base head
   must be authored** (or produced by retopologising + neutralising the Codaj
   head, which is authoring by another name). This is the head programme's
   critical-path item, exactly as the base body mesh was for bodies.
2. **Eyeball/teeth/tongue interior set** for the base (the library has standalone
   eyeball models — CrisLArt and Epim eyeballs in the parts library — but no
   base-fitted set).
3. **Bear and badger heads** (any quality) if Sen/Brand presets are ever to be
   *learned* rather than hand-estimated; both are currently absent (§1.3). Their
   presets can still be hand-authored from anatomy references when needed —
   absence blocks fitting, not preset-writing.
4. Nothing else. The slider maths, the fit machinery and the learn-then-delete
   discipline all carry over from the body side unchanged.

---

*End of spec. Companion work in flight: body-side PoC (Fat Males exact deltas +
HIMBO preset) — `~/workspace/character_assets/learned/`.*

## Addendum (Joe, Nov 12, 2026) — style axis: toony ↔ realistic

Most free fursuit head bases (Cults KilliansCorner set included) skew TOONY — chibi/kemono proportions: shortened muzzle, oversized eyes, rounded cranium. The creator must also serve REALISTIC styles. Design consequence: treat stylisation as its own axis layered over the species presets — the same species parameters interpolated between a realistic anchor (real skull proportions, per the sourced ratios in this spec; Poly Haven lion scan, leopard and wolf rigs in the library) and a toony anchor (fursuit-base proportions: eye size up, muzzle length down, cranium rounder). Species preset × style position = final head. When head-fitting starts, registration targets should include BOTH ends: realistic library heads and the toony Cults bases, so the learned deformation space covers the full span instead of only the stylised end.

## Addendum (Joe, Nov 12, 2026) — modularity: swappable parts

Body parts must be SWAPPABLE — Spore / Second Life model: parts attach and detach at sockets on the shared skeleton; a character is a base + a set of fitted parts, not one fused mesh. Rigged parts are preferred (a part carries its own skin weights to the shared skeleton and deforms with it); rigid bone-attached parts are the fallback tier. For heads this means ears, muzzle, jaw, nose and ruff are part groups with their own variants — which is exactly the discrete-variant list above. Deformation learning is per-part: a delta field learned on one part can be re-skinned and re-used on any body sharing the skeleton. (This reaffirms the Oct 3 CharMorph design doc's socket-based modular parts system + procedural genital species modules; genitalia sets are swappable species modules under the same rule.)

---

## 5. Vertical / profile placement (Nov 12, 2026) — eye height, ear height, and the crocodile test

*Prompted by Joe (Nov 12, 2026): "we also need eye height from muzzle, not
just flat like a crocodile, same with ear height, etc." §3 is strong on
plan-view widths and lengths but its only verticals are CraniumHeight,
MuzzleDepth, JawDepth and a stop index. This section adds the profile
family: where things sit **vertically** — eye above the muzzle line, eye
below the forehead line, ear base and ear tip as separate quantities.
Same [S]/[D]/[E] discipline; preset formula unchanged
(100 × (species ratio − neutral)/span, nearest 5).*

### 5.1 The measurement family

**Profile frame.** The *palatal line* (PL) is the line of the upper
alveolar margin (prosthion → staphylion direction); **z** = perpendicular
height above PL, **u** = distance along PL from prosthion. All values are
fractions of **L** (prosthion → inion, as everywhere else in this spec).

| Measurement | Landmarks / definition |
|---|---|
| **OrbitHeight** | z of the orbit (eyeball) centre above PL. The "eye height from muzzle" axis: how far the eye rides above the mouth line. |
| **OrbitRise** | Depth of the eye below the dorsal profile **at the orbit's own station**: dorsal midline z(u_orbit) − OrbitHeight. ≈ 0 = eye flush with the top line (crocodilian); 0.08–0.19 = eye sunk under a forehead (mammals). |
| **StopHeight** | z of the dorsal profile at the stop (the inflection where the nasal line meets the frontal rise); the stop's u-station is given in §5.3 notes. A *readout*, not a slider (see §5.4). |
| **StopDepth** | The vertical rise of the dorsal profile across the stop window: z_dorsal(u_stop + 0.05 L) − z_dorsal(u_stop − 0.05 L). The vertical component of the break — StopAngle (#9) tilts the nasal plane, StopDepth steps the frontal block up/down; they are different deformations. In short-faced felids the window captures the frontal *ramp* (the felid stop is a ramp, not a step — §2.3), which is the comparable quantity by construction. |
| **BraincaseRise** | Cranium top (max dorsal midline z, sagittal-crest variant excluded) − OrbitHeight: how much skull towers over the eye. Distinct from CraniumHeight (#7), which measures palate→top at the vault including below-orbit mass. |
| **EarBaseHeight** | z of the ear-base pivot — the pinna's insertion. Skull proxy: centre of the external acoustic meatus (EAM); the surface-head value adds the local tissue offset. This is the quantity EarPlacementHeight (#13) gestured at with its unitless "placement index"; it now has a real anchor (see rename, §5.4). |
| **EarTipHeight** | z of the pinna tip in natural carriage. **Not** ear length: tip height = EarBaseHeight + pinna length × vertical projection of the ear's carriage (EarTilt). A long ear folded low (badger) and a short ear held upright (bear) can share a tip height. |

### 5.2 What was measured, and what could not be

**Puma CT skull — measured [D].** *Puma concolor* MSB:Mamm:214485
(CC BY; `character_assets/head-hunt/skull-reference/`), 6.15 M-vertex CT
surface, cranium + articulated mandible. Method: PCA frame → palatal
line fitted by RANSAC to the upper tooth-row/alveolar sheet (43,411
inliers, residual σ 0.84 mm; the line threads the alveolar margin in
profile view) → frame rotated to PL, L = **183.0 mm**. Dorsal midline
profile extracted per 0.05 L bin. Orbit centre, coronoid top and the
TMJ/EAM complex read from profile + parasagittal-slab projections
against that profile. Reading error ≈ ±0.02 L. Results:

- Cranium top **0.383 L** above PL; total height incl. mandible 0.56 L.
- **OrbitHeight 0.19** (orbit centre u ≈ 0.40 L); **OrbitRise 0.19**
  (dorsal z at the orbit station 0.378 − 0.19); **BraincaseRise 0.19**.
- **StopHeight ≈ 0.20** (stop station u ≈ 0.13 L); **StopDepth 0.15**
  (dorsal 0.177 at u 0.10 → 0.323 at u 0.15 — the felid frontal ramp).
- **EarBaseHeight 0.05** (EAM centre z ≈ +0.01; +0.04 surface offset).
- **EarTipHeight 0.23** (derived: 0.05 + ear 0.22 × upright projection ≈ 0.8).
- **JawDepthProfile 0.19** (coronoid top z ≈ 0.19 above PL, u ≈ 0.58 L).

The puma stands in for the **panther (leopard)** row — the spec already
treats the cougar as our nearest panther geometry (§1.2); leopard is
expected within ±0.02 on these ratios by family pattern [E].

**Lion scan — attempted, not measurable.** The Poly Haven lion head
(§1.2) is a mane-dominated decorative carving at 25 k verts: no readable
palatal line, mouth line or orbit centre survives the mane and the
stylised face. Lion verticals below are therefore [E] on the felid
pattern (puma [D] + Christiansen's long-rostrum lion geometry), **not**
measurements — the honest status, recorded rather than papered over.

**Literature anchors used [S].** Wolf skull height (von den Driesch,
incl. crest) 0.29–0.35 L across Polish/Bulgarian/Japanese series → 0.32
adopted; wolf vertical-ramus height 0.31 L (Bulgarian series, §2.1).
Cat external cranium height **0.375 L** (European Shorthair CT, Vet.
Sci. 2021). Bear skull height 0.286 L and ramus 0.288 L; badger ramus
0.367 L (presets batch 1, §1–§2 of that doc). Everything else in §5.3 is
[E], ordered by these anchors and the family pattern (felid eyes higher
and more frontal than canid; low-skulled mustelid/ursid lowest) — the
same status stop and canid eye-size already carry in §2.3.

### 5.3 Species values — vertical family (fractions of L)

| Measurement | Neutral | Wolf | Red fox | Fennec | Lion | Panther | Cat | Dog | Bear | Badger | Crocodilian (outgroup) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OrbitHeight | 0.17 | 0.16 [E] | 0.16 [E] | 0.18 [E] | 0.18 [E] | **0.19 [D]** | 0.21 [E] | 0.16 [E] | 0.15 [E] | 0.13 [E] | 0.10 [E] |
| OrbitRise | 0.12 | 0.11 [E] | 0.10 [E] | 0.12 [E] | 0.13 [E] | **0.19 [D]** | 0.15 [E] | 0.11 [E] | 0.10 [E] | 0.08 [E] | **0.01 [E]** |
| StopHeight (readout) | 0.20 | 0.20 [E] | 0.18 [E] | 0.19 [E] | 0.19 [E] | **0.20 [D]** | 0.24 [E] | 0.21 [E] | 0.20 [E] | 0.17 [E] | — (no stop) |
| StopDepth | 0.06 | 0.04 [E] | 0.04 [E] | 0.04 [E] | 0.06 [E] | **0.15 [D]** | 0.05 [E] | 0.06 [E] | 0.08 [E] | 0.02 [E] | 0.00 [E] |
| BraincaseRise | 0.14 | 0.14 [E] | 0.13 [E] | 0.14 [E] | 0.15 [E] | **0.19 [D]** | 0.17 [E] | 0.14 [E] | 0.12 [E] | 0.10 [E] | 0.03 [E] |
| EarBaseHeight | 0.04 | 0.03 [E] | 0.03 [E] | 0.04 [E] | 0.02 [E] | **0.05 [D]** | 0.04 [E] | 0.03 [E] | 0.02 [E] | 0.01 [E] | 0.11 [E] (ear slit, no pinna) |
| EarTipHeight | 0.30 | 0.33 [E] | 0.58 [E] | 1.00 [E] | 0.14 [E] | 0.23 [D] | 0.51 [E] | 0.35 [E] | 0.22 [E] | 0.22 [E] | 0.11 [E] (= table level; nothing rises) |
| JawDepthProfile | 0.17 | 0.18 [D] | 0.15 [E] | 0.13 [E] | 0.20 [E] | **0.19 [D]** | 0.14 [E] | 0.17 [E] | 0.17 [D] | 0.21 [D] | 0.03 [E] |

Profile stations (approximate, for builders): orbit centre u/L — wolf
0.44, fox 0.42, fennec 0.40, lion 0.36, panther **0.40 [D]**, cat 0.42,
dog 0.45, bear 0.40, badger 0.42. Stop u/L — wolf 0.42, dog 0.45,
bear 0.38 (the grizzly dish), panther **0.13 [D]** (the felid ramp starts
right behind the short face), cat 0.30, badger 0.40.

Notes on the pattern:

- **The bony ear insertion barely varies** (0.01–0.05 across all nine):
  the meatus sits near palatal level on every one of these skulls. What
  reads as "ear height" in life is **tip height + carriage** — which is
  why EarHeight-as-length and tip height had to be separated (§5.4).
  Bear and badger land on the same EarTipHeight (0.22) by opposite
  routes: short ear held up vs longer ear folded low.
- **Badger is the mammal nearest the crocodile pole** (OrbitRise 0.08,
  BraincaseRise 0.10, skull height 0.25 [E]) — a genuinely flat skull —
  yet still 8× the crocodilian OrbitRise. The pole is far away from
  every mammal on the chart; see §5.6.
- **Fennec EarTipHeight = 1.00 L**: the tip sits a full skull length
  above the palatal line. EarLength already pins its slider by design;
  tip height nearly does too (+90, §5.5) — consistent, not a range bug.

### 5.4 Slider changes — two renames, six new sliders (31 → 37)

**Renames (slider registry — read before loading old preset files):**

| Old | New | Why |
|---|---|---|
| #11 `EarHeight` | **`EarLength`** | It always measured pinna *length* (ear/L); the name collided with the new vertical family. Values, neutral (0.40) and span (0.65) unchanged — a pure rename. `presets-titan-batch1.md` and `preset-orc-bara.md` still say EarHeight; read them as EarLength. |
| #13 `EarPlacementHeight` | **`EarBaseHeight`** | The "placement index" (neutral 0.50) had no physical anchor. It is replaced by the measured ratio (neutral **0.04 L**, span 0.10). **Old preset values do NOT carry over** — use the §5.5 row; the old index conflated pivot height with tip emergence, which now lives in EarTipHeight + EarTilt. |

**New sliders** (all deform in profile; layer = head layer stack of the
APP_BLUEPRINT — bone unless noted):

| # | Slider | Deforms | Anchor ratio | Neutral | Span (±100) |
|---|---|---|---|---|---|
| 32 | OrbitHeight | Orbit band + eyeball seats, vertically vs palatal line | OrbitHeight | 0.17 | 0.12 (→0.05…0.29) |
| 33 | OrbitRise | Frontal band vertically relative to the seated eye (the anti-crocodile slider) | OrbitRise | 0.12 | 0.16 (→−0.04…0.28; negative = eye proud of the line, turret-eyed/stylised territory) |
| 34 | StopDepth | Vertical step of the frontal block at the stop window | StopDepth | 0.06 | 0.12 (→−0.06…0.18) |
| 35 | BraincaseRise | Cranium shell above the orbit line only | BraincaseRise | 0.14 | 0.14 (→0.00…0.28) |
| 36 | EarTipHeight | Ear part placement: tip placed at this height (pivot + carriage compensation; composes with EarLength and EarTilt — editing tip height moves the pivot/tilt solution, editing length re-solves tilt) | EarTipHeight | 0.30 | 0.80 (→−0.10…1.10) |
| 37 | JawDepthProfile | Ramus/coronoid rise above the tooth line (jaw mesh) | JawDepthProfile | 0.17 | 0.12 (→0.05…0.29) |

StopHeight gets **no slider**: it is fully determined by where the
dorsal profile crosses the stop window (OrbitRise + StopDepth +
CraniumHeight compose it), so a separate control would fight them. It
ships as a measured readout in the app instead. Likewise JawDepth (#17,
whole-ramus height incl. below-line body) and JawDepthProfile (#37,
above-line rise only) are a pair, not a duplicate: #17 scales the jaw,
#37 reshapes its profile.

### 5.5 Preset values — vertical sliders

(−100…+100, 0 = neutral; **bold** = computed from a [S]/[D] anchor.
Bear/badger columns extend their vectors from `presets-titan-batch1.md`.)

| # | Slider | Wolf | Red fox | Fennec | Lion | Panther | Cat | Dog | Bear | Badger |
|---|---|---|---|---|---|---|---|---|---|---|
| 32 | OrbitHeight | −10 | −10 | +10 | +10 | **+15** | +35 | −10 | −15 | −35 |
| 33 | OrbitRise | −5 | −10 | 0 | +5 | **+45** | +20 | −5 | −10 | −25 |
| 34 | StopDepth | −15 | −15 | −15 | 0 | **+75** | −10 | 0 | +15 | −35 |
| 35 | BraincaseRise | 0 | −5 | 0 | +5 | **+35** | +20 | 0 | −15 | −30 |
| 13 | EarBaseHeight (renamed) | −10 | −10 | 0 | −20 | **+10** | 0 | −10 | −20 | −30 |
| 36 | EarTipHeight | +5 | +35 | +90 | −20 | **−10** | +25 | +5 | −10 | −10 |
| 37 | JawDepthProfile | **+10** | −15 | −35 | +25 | **+15** | −25 | 0 | **0** | **+35** |

Worked spot checks: panther OrbitRise (0.19 − 0.12)/0.16 = **+45** —
the biggest OrbitRise on the chart, the short-faced felid's eye sunk
under a high dome [D]. Badger JawDepthProfile (0.21 − 0.17)/0.12 =
**+35** — its coronoid rise is lion-class on the flattest skull, the
vertical half of the "longest and deepest mandible" signature. Fennec
EarTipHeight (1.00 − 0.30)/0.80 = **+90** — near-pin by the same design
that pins EarLength at +100.

### 5.6 The crocodile sanity anchor

Crocodilian row (§5.3, all [E], from the standard qualitative anatomy —
skull "characterised by its flat superior and palatal surfaces," orbits
dorsal and opening upward on a flat skull table, Miall 1878 and
successors): OrbitHeight ≈ 0.10, **OrbitRise ≈ 0.01** (in life the
eyeball protrudes *above* the table — rise is effectively zero or
negative), BraincaseRise ≈ 0.03, StopDepth 0.00, JawDepthProfile ≈ 0.03,
no pinna at all; total skull height incl. jaw ≈ 0.16–0.20 L against the
mammal range 0.45–0.56.

**The neutral base sits clearly off that pole, as required:**
OrbitHeight 0.17 vs croc 0.10; OrbitRise 0.12 vs 0.01 — a 12× margin;
BraincaseRise 0.14 vs 0.03. Even the flattest mammal preset (badger,
OrbitRise −25 → 0.08) stays 8× off the pole, and reaching crocodile
geometry from neutral takes OrbitRise to ≈ −70 with OrbitHeight and
BraincaseRise also driven deep negative — i.e. it is outside every
mammal preset's neighbourhood and cannot happen by accident while
tuning a species. If a future reptile base is ever built, it starts
from those outgroup numbers, not from the mammal neutral.

*Weak spots, stated plainly: one measured skull (puma) carries the
felid [D] column; lion verticals are unmeasured [E] (see §5.2); canid
orbit heights remain estimates, as they were in §2.3. The next
measurement pass should be a canid CT skull (wolf or dog) and a lion
skull (not the mane sculpture) through the same pipeline.*

