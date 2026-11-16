# Rigged Head Hunt — Local Library Sweep

**Date:** Nov 16, 2026 · **Requested by:** Joe ("look into and find rigged heads from resources")
**Scope:** `~/workspace/character_assets/` + `~/workspace/bodies-3d/` (plus the furry-lineup
models folder under `~/workspace/stick-figure-avatar/`, which holds working copies of
library items). Read-only: nothing downloaded, nothing extracted into the workspace
(zip members were probed from single-file extracts in scratch and deleted).
**Excluded by brief:** the 7 candidates already covered by the Nov 7 donor survey
(`bodies-3d/head-survey/SURVEY.md`) — Lion Warrior, Leopard Hybrid A2, GalileoGB Cougar,
True Furry raw head, Vladlarin lioness, Roaring Lion, Poly Haven Lion Head. They are
referenced where relevant, not re-probed.
**Method:** filename/manifest inventory first; GLB/glTF/VRM parsed directly from their
JSON chunks (skins, joint names, mesh/vert counts, morph counts); `.blend`/`.fbx`
probed headless in Blender 5.2.3 (armature bone names, mesh vert counts, verts weighted
>0.3 to head/jaw/eye/tongue/ear groups = "head-weighted verts", shape keys).
Prior verified work folded in: Nov 9 fennec scout (`bodies-3d/fennec-scout/SCOUT.md`),
Nov 10 furry-lineup inventory, Nov 12 library audit (`character_assets/MASTER_INDEX.md`)
and head-hunt spectrum (`character_assets/head-hunt/SPECTRUM.md`).

**"Jaw machine"** below = jaw bone + teeth + tongue articulation. VRChat-standard
avatars usually have *no* jaw bone — the mouth is viseme blendshapes; those are marked
"mouth = morphs" and ranked below true bone jaws for Kaleaon, whose head must carry a
working jaw/tongue/teeth machine.

---

## Headline finds (new since the Nov 7 survey)

1. **Catperson (hiamBoz, CC0)** — anthro cat-person `.blend` with a **complete jaw
   machine**: `defJawL` + `defJawU` + `defteethLower` bones, a 4-bone tongue chain,
   eyelid and eyeball bones, 145 bones total. CC0 — the cleanest licence in the library.
2. **Panda Girl (Futaba, CC BY)** — the landed GLB carries a **full Rigify face rig
   (742 joints)**: `jaw_master`, `DEF-jaw`, jaw.L/R, teeth.T/B bones, tongue chain, full
   lip system. A prior inventory called this GLB "lightweight, rig unavailable" — direct
   parsing contradicts that; the rig is in the file. It is also the library's **only
   bear** (see Sen note).
3. **KFM-G-A001 "Tiger" head (BOOTH, 黒鳥ケモノ工房)** — a **head-only felid export**:
   tiger head + separate ear and eye meshes on a 53-bone VRChat skeleton, 32 viseme/blink
   shape keys. Mouth is morph-driven (no jaw bone).
4. **Low-poly lion (unityking24, CGTrader RF)** — a **feral lion carrying a full Rigify
   face rig** (823 bones: ORG-teeth.T/B, lip chains, forehead, ears, eyes). Only 1,510
   verts — the *rig* is the asset, not the geometry.
5. **Bork (BOOTH, 黒鳥ケモノ工房)** — muscular wolf with a `Mouth` bone, a 5-bone tongue
   chain, two eye-bone sets and a separate eye mesh. The strongest jaw anatomy of any
   canid in the library.
6. **VRCFox (GearBoxFox, CC BY-NC)** — fox with `jaw` + `tongue` bones and 100 shape
   keys. **Kobult (BOOTH)** — kobold with `Jaw` + 4-bone tongue + 279 shape keys.
   **Awtter (otter)** and **Zach** also carry true Jaw + tongue chains (see table).

---

## Ranked shortlist — for Kaleaon (lion × snow leopard)

Ranking rule: felid > canid > other · anthro > feral · complete jaw machine > partial.
The Nov 7 survey's #1 (Lion Warrior) remains the only candidate that is simultaneously
lion + anthro + mechanically complete; this sweep widens the pool around it rather
than replacing it.

| # | Candidate | Why | Costs |
|---|---|---|---|
| 1 | **Catperson — hiamBoz (CC0)** | Anthro felid with the only *complete, cleanly-licensed* jaw machine found: upper+lower jaw bones, lower-teeth bone, tongue chain, eyelid + eyeball bones. CC0 — no attribution, no restrictions. | Low-poly toon (5,160 verts total, ~2,434 head-weighted); head is fused into the single body mesh — harvest means cutting + reweighting; simple/cat-generic face, not a lion sculpt. |
| 2 | **KFM-G-A001 Tiger Head (BOOTH)** | Head-only tiger: nothing to amputate. Separate ears (544 v) + eye mesh (228 v), full viseme set, eye shape keys (CatsEye/OpenPupil). 5,909 head verts. | No jaw bone (viseme morphs only); kemono-toon style; BOOTH terms — VRChat public use allowed only if the avatar name includes "kurotori"; treat as study-tier for grafting. A second head variant (A002) is in the same zip. |
| 3 | **Panda Girl face rig — Futaba (CC BY)** | Not a lion donor — the **mechanism reference**: the most complete face rig owned (Rigify jaw/tongue/teeth/lips, 742 joints). If Kaleaon's jaw machine gets built rather than grafted, this (with the BVH pack) is the blueprint. | Bear, female, toon; 148k verts of clothed avatar around the head; head is not a separable part as landed. |
| 4 | **Low-poly lion — unityking24 (CGTrader RF)** | Actual lion + full Rigify face rig (teeth/lip/forehead/ear deform bones). Rig-donor: the face rig could be transferred to a better lion sculpt. | Feral quadruped; 1,510 verts total (~190 head-weighted) — geometry is unusable as a graft; CGTrader RF = no raw-file redistribution (AI-training ban only per licence family — not a blocker per Joe's Nov 12 ruling; the no-redistribution term still binds). |
| 5 | **AKM cat base / Persipia (CC BY)** | Anthro felid, rigged (63–65 joints, ear chains), separate eye + whisker meshes; Persipia adds blink/smile/mouth shape keys. A workable anthro felid head if a jaw is built into it (same surgery class as the Codaj fennec). | No jaw bone, no teeth/tongue meshes; female toon bases; heads fused to body meshes. |
| 6 | **Leopard Animation Run — GremorySaiyan (CC BY)** | Rigged leopard (47 joints, ear/eye bones, run cycle) — big-cat *shape* reference. | Feral, 3,644 verts low-poly; no jaw machine. Reference class only. |

---

## Full table

Head verts = head-weighted verts where probed in Blender; for GLB skins, total verts
are given and head separation is noted (fused vs separate mesh). Sizes are the model
file unless marked "folder".

### Felid

| Candidate | Path | Format / size | Species / form | Rigged | Jaw bone | Teeth / tongue / eyes | Head verts | Licence |
|---|---|---|---|---|---|---|---|---|
| Catperson — hiamBoz | `bodies-3d/parts-library/existing-haul/catperson-furry-cc0/catperson-furry-CC0.blend` | .blend, 5.5 MB folder | Cat-person, anthro | **Yes — 145 bones** | **Yes — defJawL + defJawU** | Teeth: `defteethLower` bone (mesh fused); tongue: 4-bone chain; eyes: eyeball + eyelid bones, fused mesh | ~2,434 of 5,160 | **CC0** |
| KFM-G-A001 Tiger Head | `character_assets/booth/KFM-G-A001_Tiger_Parts.zip` → `FBX_Exports/Models/KFM-G_A001_TigerHead.fbx` (+ `KFM-G-A001_Head.blend`, A002 variant) | FBX 0.8 MB (zip 100 MB) | Tiger, anthro, **head-only** | **Yes — 53-bone skeleton** | No — mouth = 32 viseme/blink morphs | Teeth/tongue: none separate; eyes: separate mesh (228 v) + Eye_L/R bones; ears separate mesh (544 v) | 5,909 (all head) | BOOTH creator terms (Google Doc): VRChat public use if avatar named "kurotori" — study-tier |
| Low-poly lion — unityking24 | `bodies-3d/parts-library/cgtrader/low-poly-lion-unityking24/low_poly_lion.fbx` (+ .blend, Walk_Animation.fbx) | FBX, 28 MB folder | Lion, **feral** | **Yes — Rigify, 823 bones** incl. full face rig | Face rig has teeth/lip/forehead deform bones (Rigify jaw via face rig) | Teeth.T/B + lip bones; eyes via eye.L/R bones; all fused in one mesh | ~190 of 1,510 | CGTrader Royalty Free (no AI) |
| Anthro Female Cat Base — AKM | `bodies-3d/parts-library/sketchfab/anthro-female-cat-base-akm/anthro_female_cat_base.glb` | GLB 0.5 MB | Cat, anthro ♀ | Yes — 63 joints, ear chains | No | Eyes: separate mesh (74 v); whiskers separate (32 v); no teeth/tongue | Fused (5,731 total) | CC BY (AKM) |
| Persipia — AKM | `bodies-3d/parts-library/sketchfab/persipia-akm/persipia.glb` (working copy in furry-lineup) | GLB 3.0 MB | Siamese cat, anthro ♀ | Yes — 65 joints, ear chains | No — 9 morphs (blink/smile/mouth) | Eyes separate (74 v); ears separate (460 v); whiskers (64 v) | Fused (29,105 total, clothed) | CC BY (AKM) |
| Leopard Animation Run — GremorySaiyan | `bodies-3d/parts-library/sketchfab/leopard-animation-run-gremorysaiyan/leopard_animation_run.glb` | GLB 1.0 MB | Leopard, feral | Yes — 47 joints, ear/eye bones | No | All fused | Fused (3,644 total) | CC BY |
| Cat rigged — Vr-cvantorium | `bodies-3d/parts-library/existing-haul/cat-rigged-ccby/scene.gltf` (dup: `bodies-3d/harvest/cat/`, zip in character_assets root) | glTF, 71 KB zip | Cat, feral, low-poly | Yes — 35 joints, ear bones, 3 anims | No | All fused | Fused (1,750 total) | CC BY |
| Styloo cat | `bodies-3d/parts-library/existing-haul/styloo-animals-cc0/cat.glb` | GLB 0.3 MB | Cat, feral, low-poly game | Yes — Rigify-style (283 joints incl. MCH) | No | All fused | Fused (2,547 total) | CC0 |
| Kitty Base — chocolatemilkcows | `bodies-3d/parts-library/sketchfab/kitty-base-chocolatemilkcows/kitty_base_v1.0.glb` | GLB 0.8 MB | Cat, anthro | **No skin in the landed GLB** (listed elsewhere as rigged — not in this file) | — | None separate | 15,890 (single mesh) | CC BY |

### Bear

| Candidate | Path | Format / size | Species / form | Rigged | Jaw bone | Teeth / tongue / eyes | Head verts | Licence |
|---|---|---|---|---|---|---|---|---|
| Panda Girl — Futaba | `bodies-3d/parts-library/sketchfab/panda-girl-futaba/panda_girl_-_stylizedfree_blender_rig.glb` | GLB 27.7 MB | Panda, anthro ♀, toon | **Yes — Rigify, 742 joints** | **Yes — jaw_master, DEF-jaw, jaw.L/R** | Teeth.T/B bones; tongue chain (tongue_master + .001/.002); full lip system (lip.T/B, lips.L/R, mouth_lock) | Fused (148,234 total, clothed avatar) | CC BY (futaba@blender) |

*The library's only ursid. See the Sen note below.*

### Canid

| Candidate | Path | Format / size | Species / form | Rigged | Jaw bone | Teeth / tongue / eyes | Head verts | Licence |
|---|---|---|---|---|---|---|---|---|
| Codaj "Anthro Fennec Rigged" | `bodies-3d/parts-library/sketchfab/anthro-fennec-rigged-codaj/anthro_fennec_rigged.glb` | GLB 4.0 MB | **Fennec**, anthro | Yes — 107 joints, 4-bone ear chains, eye bones | **No** | None separate; painted irises; vertex-colour coat | Fused (41,304 total) | CC BY (Codaj) |
| Bork — 黒鳥ケモノ工房 | `character_assets/booth/Bork_v1.0.zip` → `Relase/Bork.fbx` (+ .blend, Bork_Naked.fbx) | FBX 1.4 MB (zip 87 MB) | Wolf, muscular anthro | **Yes — 93 bones** | **Mouth bone** (jaw function) | Tongue: 5-bone chain; eyes: separate mesh (290 v) + LeftEye/RightEye + Eye.L/R bones; 32 morphs (visemes + expressions) | ~3,412 of 8,843 | BOOTH terms: redistribution/resale prohibited (modified or not) — study-tier |
| Big Bad Wolf / Death V2 — CVRxEarth | `bodies-3d/parts-library/existing-haul/wolf-rigged-ccby/scene.gltf` (working copy: furry-lineup `wolf_cvrx/`) | glTF + bin, 14 MB folder | Wolf, anthro | **Yes — 222 joints** (Mixamo + control rig) | No — face = 64 morphs | Eyes: separate mesh; teeth fused | Fused (67,426 total) | CC BY |
| Terris, Wolf — GalileoGB | `bodies-3d/parts-library/sketchfab/terris-wolf-galileogb/source/SKETCHFABVERSION.fbx` | FBX, 1.7 MB folder | Wolf, anthro | Yes — 79 bones, Eye/Ear bones | No — 16 face morphs (MouthOpen, Eye_Close, brows, smirk) | Head is a **separate mesh** (Head_Combined, 1,412 v); eyes fused | Head mesh 1,412 (7,631 total) | CC BY (SKYE/GalileoGB) |
| Terris (old) — GalileoGB | `bodies-3d/parts-library/sketchfab/terris-old-galileogb/source/Wolf.blend` | .blend, 4.6 MB folder | Wolf, anthro | Yes — 81 bones | No — **25 face morphs** (MouthOpen, Wink, Snarl, brows, Pupil_Dilation) | Head_Combined separate (3,202 v) | Head mesh 3,202 (7,468 total) | CC BY |
| Tarris Grey — GalileoGB | `bodies-3d/parts-library/sketchfab/tarris-grey-galileogb/source/SF_Wolf.fbx` | FBX, 4.8 MB folder | Wolf, anthro (armoured) | Yes — 111 bones, Eye/Ear bones | No | Head_Mas separate (1,920 v); **eye globes separate** (2× Sphere, 964 v each) | Head mesh 1,920 (9,190 total) | CC BY |
| Bearyl Canine / Archa base | `bodies-3d/parts-library/jinxxy/bearyl-canine-archa/` (Canine_Blend_V4.0.0.zip, ArchaType_Blend.zip, Unity pkg) | .blend in zip, 103 MB / 200 MB | Canid anthro base | Yes — VRChat base rig (documented) | **Unverified** — probe blocked (see Not probed) | — | — | Bearyl terms: **no redistribution of base files** — donor/study only |
| Border Collie Scientist — AKM | `bodies-3d/parts-library/sketchfab/border-collie-scientist-akm/border_collie_scientist.glb` | GLB 1.7 MB | Border collie, anthro | Yes — 66 joints, ear chains | No — 12 morphs | Eyes separate mesh; ears separate (352 v); mane separate | Fused (8,757 total) | CC BY (AKM) |
| Female Dog Furry — rhl89ryo | `bodies-3d/parts-library/sketchfab/female-dog-furry-rhl89ryo/generic_productfemale_dog_furry.glb` | GLB 8.2 MB | Dog, anthro ♀ | Yes — 144 joints | No jaw bone — but **Tongue bone chain (8)** | **Teeth + tongue + eye meshes separate**; Eye_R/L bones; ⚠ author-noted face-mesh defect | Fused (58,032 total) | CC BY |
| Mesh 9 furry — keh | `bodies-3d/parts-library/sketchfab/mesh-9-furry-keh/mesh_9_furry.glb` | GLB 1.4 MB | White fox/wolf, anthro, toon WIP | Yes — 61 joints | **Yes — `b_Jaw`** + b_Eye.L/R | Eyes separate (916 v); whiskers; one fang hangs below the closed mouth at rest | Fused (7,200 total) | CC BY |
| VRCFox 2.3 — GearBoxFox | `character_assets/social-freebies/vrcfox-2.3_gearboxfox_github.zip` → FBX / .blend / VRM inside | FBX 6.8 MB (zip 13 MB) | Fox, anthro, minimalist | **Yes — 85 bones** | **Yes — `jaw`** | Tongue bone; eye bones; **100 shape keys** (visemes + expressions + brow set) | ~1,806 of 5,651 | **CC BY-NC 4.0** |
| Fox Fem. Full Rig — azuliezeiro | `bodies-3d/parts-library/sketchfab/fox-fem-full-rig-azuliezeiro/fox_fem._full_rig.glb` | GLB 0.3 MB | Red fox, anthro ♀ | **No** — rig did not survive (1-bone metarig, empty groups; scout-verified) | — | **Teeth (310 v) + gums (47 v) separate**; eyes separate (916 v) but blank white globes | Parts only (5,802 total) | CC BY |
| Peridot (BOOTH, coinbattery) | `character_assets/booth/peridot_v1.1.zip` → VRM | VRM 4.6 MB (zip 3.7 MB) | Dog (genderless, green), anthro | Yes — 56 joints, 5-bone ear chains | No — 48 morphs | All fused (single baked mesh) | Fused (21,309 total) | Creator terms: **no combining with other models** (no chimera) |
| inuinu (BOOTH, zuchicorn) | `character_assets/booth/VRM0615_inuinu1.003.zip` → VRM (VRChat pkg also on disk) | VRM 12.8 MB | Shiba dog, anthro | Yes — 55 joints, ear bones | No — 53 morphs | All fused | Fused (8,045 total) | UV licence (per BOOTH manifest) |
| Styloo dog | `bodies-3d/parts-library/existing-haul/styloo-animals-cc0/dog.glb` | GLB 1.6 MB | Dog, feral, low-poly game | Yes — 46 joints, 6 anims | No | All fused | Fused (3,344 total) | CC0 |
| Golden Retriever — iRahulRajput | `bodies-3d/parts-library/existing-haul/golden-retriever-ccby/scene.gltf` (+ full bin in `character_assets/golden-retriever-CCBY.zip`) | glTF, 38 MB zip | Dog, feral, photoreal | **No skin as landed** | — | Coat PBR texture donor | 423,175 (scan-density) | CC BY |
| Bara Wolf (Joe's upload) | `stick-figure-avatar/furry-lineup/threejs-lineup/models/bara_wolf_avatar.glb` (+ .blend set in `stick-figure-avatar/furry/`) | GLB 6.3 MB | Wolf, bara anthro | Yes — 65 joints (Mixamo) | No | Two sphere meshes (1,488 v ea — eye globes); head fused to body mesh | Fused (72,166 total) | User-provided (Tripo sculpt + Mixamo rig); provenance terms unverified |

### Other anthro (complete jaw machines and notable rigs)

| Candidate | Path | Format / size | Species / form | Rigged | Jaw bone | Teeth / tongue / eyes | Head verts | Licence |
|---|---|---|---|---|---|---|---|---|
| Kobult — jackcanty (BOOTH) | `character_assets/booth/Kobult.zip` → `Kobult.fbx` / `Kobult Digi.fbx` (+ .blend projects) | FBX 2.0 MB (zip 88 MB) | Kobold (reptilian), anthro, + digitigrade variant | **Yes — 108 bones** | **Yes — `Jaw`** | Tongue_01–04 + End; Eye_Root + Eye_L/R; ear control chains; **279 shape keys** | ~4,460 of 9,209 | Creator licence (Pastebin): public uploads encouraged — most permissive BOOTH item |
| Awtter base 2.9.71 | `character_assets/drive-models/Awtter_base_2.9.71_8EO9CA7.blend` | .blend 25 MB class | **Otter**, anthro (VRChat base) | **Yes — 78 bones** | **Yes — `Jaw`** | Tongue1–4 chain; LeftEye/RightEye bones; ear chains; 67 shape keys (full VRC visemes) | ~6,340 of 25,256 | **UNKNOWN** — no licence record in drive-models |
| Minotaur — Bearyl | `bodies-3d/parts-library/jinxxy/bearyl-minotaur/Minotaur_Blend_1.2.1.zip` → Minotaur.blend | .blend 151 MB in zip (folder 3.5 GB w/ Substance+Unity) | Minotaur (bovine), anthro, big-body | **Yes — 150 bones** | **Yes — `LowerJaw`** | Tongue.001–006; Eye + EyeShocket bones; **Eyes separate mesh (2,432 v)**; Body has 260 shape keys | ~12,408 of 53,920 (incl. clothing/accessories) | Bearyl terms: no redistribution of base files — donor/study only |
| Dragon Model Base — Zairiza | `character_assets/drive-models/Dragon Model Base (Zairiza).zip` → SFW/NSFW .blend + FBX | .blend 5.0 MB (zip 292 MB) | Dragon, anthro | **Yes — 146 bones** | **Yes — `Jaw`** | **BottomTeeth separate (695 v)**; ForkedTongue separate (386 v) + 6-seg tongue + split-tongue chains; REye/LEye bones; Headgeo 12 expression keys | ~20,135 of 54,121 (incl. fluff/spike meshes) | **UNKNOWN** — no licence record in drive-models |
| Zach (rigged) | `character_assets/drive-models/Drake_Model_and_dick.zip` → `Zach Rigged NO IK.blend` (unrigged sibling: `drive-models/Zach (1).blend`) | .blend 44.5 MB in zip | Anthro avatar (species not determined by probe; packaged with Drake/dragon material) | **Yes — 123 bones** | **Yes — `Jawbone`** | Tongue1–4; EyeLeft/EyeRight; ear chains; 19 shape keys (visemes). Unrigged sibling file holds **separate Teeth top (6,911 v) / Teeth bottom (5,343 v) / Tongue (602 v) meshes** — premium parts | ~33,362 of 72,404 (incl. clothing) | **UNKNOWN** — no licence record in drive-models |
| Lesser Mokuri (BOOTH, MOKURI project) | `character_assets/booth/Lesser_Mokuri_v2.22.0_.zip` → FBX / .blend | FBX 1.3 MB (zip 74 MB) | Kemono (cat-like), anthro | Yes — 144 bones, ear + eye bones | No — 19 morphs (incl. fang key) | Eyes fused; hair/helmet separate | ~2,732 of 7,653 | UV licence; creator terms allow personal commercial use + derivative distribution |
| Carbuncle (BOOTH, udon-cat-works) | `character_assets/booth/Carbuncle_package.zip` → `Source/carbuncle.blend` (+ unitypackage) | .blend 15.1 MB (zip 50 MB) | Carbuncle (small fox/cat-like creature, forehead jewel), anthro | Yes — 75 bones (hi + low armatures), eye + ear bones | No — 29 morphs on Head (visemes/blink/smile) | **Head separate mesh (1,586 v)**; Ear1/Ear2 separate; jewel separate | Head mesh 1,586 | No explicit terms on page — **UNKNOWN** |
| Fox Girl (BOOTH, asdfg21) | `character_assets/booth/Fox_Girl_v1.1.zip` → `fox_girl.fbx` | FBX 1.4 MB (zip 19 MB) | Fox girl, kemono anthro | Yes — 189 bones, 3-bone ear chains, Eye_L/R | No — 69 morphs | All fused | ~6,336 of 12,601 | No terms block on page — **UNKNOWN** |
| Kachua (BOOTH, らてのすのショップ) | `character_assets/booth/kachua.zip` → VRM (+ PMX, unitypackage) | VRM 13.4 MB | Cat girl, kemono anthro | Yes — 73 joints, Eye_L/R + Ears bones | No — **638 morphs** | All fused (single baked mesh) | Fused (88,176 total) | Terms: no redistribution of unmodified model; no sale; VRChat OK |
| Maromage (BOOTH, zuchicorn) | `character_assets/booth/maromage_01.vrm` (+ VRC data zip) | VRM 21.4 MB | Mochi/cat-like avatar, anthro | Yes — 64 joints | No — 174 morphs | All fused | Fused (17,576 total) | UV licence |
| Otter-Chan — AKM | `bodies-3d/parts-library/sketchfab/otter-chan-akm/otter-chan.glb` | GLB 1.9 MB | Otter, anthro, toon | Yes — 65 joints, eyes_target bones | No — 2 morphs | Eyes separate (74 v); ears separate (218 v); whiskers (86 v) | Fused (20,431 total) | CC BY (AKM) |
| Oracle — GalileoGB | `bodies-3d/parts-library/sketchfab/oracle-galileogb/source/Orical.fbx` | FBX, 1.9 MB folder | Anthro (GalileoGB felid line; species read unverified in this sweep) | Yes — 107 bones, Eye.L/R bones | No | **Eyes separate mesh (1,928 v)** | ~3,350 of 8,153 | CC BY |
| Protogen base — radthezealot | `bodies-3d/parts-library/sketchfab/lowpoly-base-male-protogen-radthezealot/lowpoly_base_male_protogen.glb` | GLB 0.5 MB | Protogen (synthetic), anthro | Yes — 56 joints, ear fins | No (visor face) | All fused | Fused (6,290 total) | CC BY |
| Bunny — Colin Greenall | `bodies-3d/parts-library/sketchfab/bunny-furry-commission-colin-greenall/bunny_furry_commission.glb` | GLB 7.2 MB | Rabbit, anthro (VRChat) | Yes — 67 joints, 4-bone ear chains, EyeJoints | No | All fused | Fused (10,646 total) | CC BY |
| Bunny — azuliezeiro | `bodies-3d/parts-library/sketchfab/bunny-azuliezeiro/bunny.glb` | GLB 0.6 MB | Rabbit, anthro | **No** — 1 joint (rig lost, same failure as Fox Fem) | — | — | 11,900 | CC BY |

### Head-only rigs & part donors

| Candidate | Path | Notes |
|---|---|---|
| **KFM Tiger Head A001/A002** | see Felid table | The only rigged head-only felid export on disk. |
| Toriel Head Rig — dm2206 | `bodies-3d/parts-library/sketchfab/toriel-head-rig-dm2206/toriel_head_rig.glb` (GLB 0.3 MB) | **Head-only goat**: 46 joints incl. jaw + Tongue bone, Eye/Eyelash/Eyebrow bones, ear chains, horns; tongue separate (155 v), eyes separate (2× 596 v); 2,613 verts total. CC BY — **but a franchise character (Undertale): rig/mechanism reference only, never ship the character.** |
| BVH Rig pack (fox/rabbit/cat) — kitsunzoro | `bodies-3d/parts-library/sketchfab/bvh-rig-fox-rabbit-cat-kitsunzoro/bvh_rig_models_update_fox_rabbit_and_cat.glb` (GLB 15.7 MB) | Most complete face *mechanism* owned alongside Panda Girl: 318 joints across the pack, Rigify face rig (lip/lid/brow deform bones), separate eyelid meshes, separate teeth (2,592 / 2,916 v), mouth-interior meshes. Assembled build reads as a cat. **CC BY-SA — quarantined from combined GLBs under standing licence discipline; reference only.** |
| Fox Fem teeth/gums | see Canid table | Teeth (310 v) + gums (47 v) as separate modelled parts in an otherwise unrigged file. |
| Zach (unrigged) teeth/tongue | `character_assets/drive-models/Zach (1).blend` | Teeth top 6,911 v / bottom 5,343 v / tongue 602 v as separate meshes — the densest mouth parts on disk. |
| Eyeball meshes | `bodies-3d/parts-library/sketchfab/eyeball-brown-iris-epim/`, `eyeball-crislart/` | Standalone eye globes (5,444 v / —), unrigged parts. |
| Teeth sets | `character_assets/teeth/` (TEETH.md) | 15+ sets, CC BY / CC BY-SA per set — parts library, not heads. |

### Unrigged heads catalogued (no rig in the landed file)

| Candidate | Path | Read |
|---|---|---|
| Zaba Soda fursuit bases (head-hunt) | `character_assets/head-hunt/{realistic-wolf,realistic-canine-v3-package,realistic-canine,realistic-feline,semitoon-leopard,kemono-feline,feline-moving-jaw,toony-canine}-zaba/` | STL print bases — unrigged by format. The **Realistic Canine V3 Package (CC BY)** is a full kit: upper + jaw + nose + upper/lower teeth as separate STLs; **Realistic Feline (CC BY)** likewise (upper/jaw/teeth/hinge). Jaw *geometry* exists as separate parts — rigging would be ours. Full grading in `head-hunt/SPECTRUM.md`. |
| Tioh fursuit bases (head-hunt) | `character_assets/head-hunt/tioh-v{51,55,66,84}-*/` | STL, separate jaw STLs included. CC BY-NC / NC-SA — reference-tier. |
| Cults3D fursuit bases | `character_assets/cults3d/*.stl` + `angry_wolf_krapette.obj` | Sampled 4 STLs (KemonoCat 491k tris, HoneyBear 24k, TiredCanine 1.28M, ChibiBlank 23k) — all single-solid print files; STL carries no rig. Angry Wolf OBJ: 728,666 v, single group, unrigged sculpt. KilliansCorner terms: personal use; commercial needs separate licence. Includes bear (HoneyBear, VintageTeddyBear), canine, feline (KemonoCat), dragon and other head bases — **form reference only**. |
| Orc heads/skulls | `character_assets/orc/*.zip`, `drive-models/orc_skull.zip` | Print/sculpt files (CC BY per manifest) — unrigged. |
| Cute Furry Fox "Lisa" | `bodies-3d/parts-library/sketchfab/cute-furry-fox-enotobuterbrodo/cute_furry_fox.glb` | Separate head mesh (10,942 v) but **no skin**; baked pose; chibi — style rejected in the fennec brief. |
| True Furry "rig version" GLBs | `character_assets/drive-models/true_furry_rig_version.glb`, `drive-models/furry.glb`, `parts-library/sketchfab/true-furry-rig-julianemilioqwe/extracted/source/model.glb` | **No skin in any landed GLB copy** — the rig did not survive export (the survey's copy likewise). Wolf sculpt, 175–268k verts. |
| FREE Horse — DinoReplicas | `bodies-3d/parts-library/sketchfab/free-horse-dinoreplicas/free_horse_3d_model.glb` | **No skin** — 23,893 verts, separate meshes (mouth/eye parts per inventory). The only horse on disk, and it is unrigged + feral. |
| Julianemilioqwe bara sculpts ×3 | `bodies-3d/parts-library/sketchfab/{alternative-bara,bara-earthquake,furry-dad}-julianemilioqwe/` | Static sculpts (423k–630k verts), no skins — bara form reference. |
| Muscular Heroic Male — braineybites | `bodies-3d/parts-library/cgtrader/muscular-heroic-male-braineybites/MascularMale.glb` | Human sculpt, no skin. |

---

## Notes for the other sonas

- **Pyn (fennec):** Codaj remains the anchor — true fennec, 107 joints, mouth closes at
  rest — but it has **no jaw bone and no teeth/tongue meshes**; a jaw machine would be
  built (Catperson/Panda rigs are the mechanism references) or borrowed. Jaw-boned
  canid alternatives if species-truth relaxes: Mesh 9 (`b_Jaw`, toon, WIP) and VRCFox
  (jaw + tongue bones, CC BY-NC).
- **Jorge (St. Bernard):** no St. Bernard exists on disk. Nearest rigged canids by
  *build*: **Bork** (muscular wolf — Mouth bone + tongue chain; the anatomy is right,
  the breed isn't). By *head shape*: Border Collie (AKM). By *face system*: Terris /
  Terris-old / Tarris Grey (GalileoGB shape-key faces, separate head meshes — the
  easiest heads to harvest mechanically).
- **Wolves (Alpha/Beta/Gamma/Delta):** supply is adequate — CVRxEarth (222 joints),
  Terris ×2, Tarris Grey, Bork, bara wolf. Canon coat colours are unsettled — assign
  bodies, do not invent coats (standing rule).
- **Sen (grizzly × moon bear):** the Nov 10 verdict "no bear has ever landed" is now
  *half* corrected — **Panda Girl is a real ursid with the best face rig in the
  library**, but she is a toon female panda; her head is no graft for a 10-ft,
  2,500-lb grizzly×moon bear. Bear head *geometry* otherwise exists only as unrigged
  Cults3D print bases (HoneyBear, VintageTeddyBear). The gap stands for geometry;
  the jaw-machine mechanism now has a bear-family reference.
- **Brand (badger):** **no badger anywhere on disk** — the gap is unchanged. Nearest
  family (Mustelidae): **Awtter** (otter — and it has a true Jaw + tongue chain) and
  Otter-Chan (AKM). Wrong animal, right family, right machinery.
- **Sage (Clydesdale):** only the feral FREE Horse, **unrigged as landed**. No anthro
  horse exists in the library. Gap unchanged.
- **Thatch (owl):** **no bird model of any kind on disk.** Gap unchanged.
- **Hollis (serval):** no serval. Nearest small-felid heads: Catperson (CC0, jaw
  machine), AKM cat base, Persipia. (The survey's cougar/leopard are the larger-cat
  stretches.)

## Not probed, and why

- **The survey's 7** — excluded by brief (covered in `head-survey/SURVEY.md`).
- **Bearyl Canine.blend** — probe attempted; Blender load fails on a shape-key fault
  (`KEKey.005 has an invalid 'from' pointer`) — the same corruption class as the
  GalileoGB Cougar blend. Rig is documented (VRChat canine base) but jaw-bone
  presence is unverified by direct probe. **ArchaType.blend** (200 MB in zip) not
  probed for the same family reason + size.
- **Nix (CloudGazerr, Jinxxy)** — FBX exists inside the unitypackages, but its TOS
  forbids taking parts for other models: reference only, deliberately not probed
  as a donor.
- **Hobkin / Dogkin community package (Wolfy527)** — FBXs listed inside the
  unitypackage; terms unclear in local records — deprioritised.
- **Orca (GalileoGB)** — author-flagged as possibly broken; cetacean, no sona slot.
- **Escanor (CGTrader)** — franchise human, reference-only tier.
- **Valence "Prisoner" (Beast Beat)** — human; already triaged by the survey. (The
  drive-models zip is the same asset as `parts-library/valence-beastbeat/`.)
- **Kemono base (らてのすのショップ, BOOTH)** — PMX/MMD package; a `Sotai.blend`
  exists inside `kemono_base.zip` but was not probed (generic kemono base, MMD-rig
  class, low sona value).
- **1024Flat (BOOTH)** — not probed; generic flat-style kemono avatar, low priority.
- **inuinu VRChat unitypackage** — the same avatar's VRM was probed instead.
- **Vix, Taro, Rabi, Chimera MK2, Lumelana (BOOTH manifest)** — **not on disk**;
  the manifest records downloads that landed on Joe's Windows machine only.
- **Dragon NSFW variants (Zairiza)** — SFW base probed; the NSFW files are body
  variants of the same rig.
- **Leopard Hybrid A2's FBX format packs** — the native .blend was the survey's
  subject; excluded.
- **Z-Anatomy / HIMBO / Skyrim NIF sets** — human anatomy/game rigs, not anthro
  head candidates.

## Licence cautions (from local records — not legal advice)

- **CC BY-SA quarantine:** the BVH Rig pack (kitsunzoro) — reference only, never
  mixed into combined GLBs under standing discipline.
- **No-redistribution bases:** Bearyl (Canine/Minotaur), Bork, CGTrader RF items —
  study/donor use in Joe's own builds; raw base files don't travel.
- **Peridot's terms forbid combining with other models** — it cannot be a chimera
  donor at all.
- **UNKNOWN licences:** Awtter, Dragon (Zairiza), Zach, Carbuncle, Fox Girl —
  all in `drive-models/` or unstated BOOTH pages. Do not assume terms.
- **Toriel** is CC BY but a franchise character — mechanism reference only.
