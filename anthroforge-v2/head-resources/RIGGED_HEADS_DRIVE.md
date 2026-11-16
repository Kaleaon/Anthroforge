# Rigged Head Hunt — Drive Models + Parts Library + Harvest + Furry Lineup

**Date:** Nov 16, 2026 · **Scope:** widen the Nov 7 donor survey's pool for Kaleaon's head
(and every other sona's) from resources already on disk / in Joe's Drive Models folder.
**Territory swept:** (1) Google Drive **Models** folder — remote listing re-verified
Nov 16 (49 items, **nothing added since the Nov 12 mirror**; local mirror at
`~/workspace/character_assets/drive-models/` is current) incl. the BOOTH pulls in
`~/workspace/character_assets/booth/`; (2) `~/workspace/bodies-3d/parts-library/` +
`~/workspace/bodies-3d/harvest/`; (3) furry-lineup GLBs at
`~/workspace/stick-figure-avatar/furry-lineup/threejs-lineup/models/`.
**Method:** GLB/glTF = JSON parse (skins, joint names, mesh names, morphs, vert counts).
.blend/.fbx = headless Blender 5.2.3 probe (`--threads 2`): armature bone names filtered
for jaw/mouth/eye/tongue/ear/teeth/head, mesh list + vert counts + shape keys. Zip
contents listed without extraction except small/single entries probed in /tmp
(all probe scratch deleted; disk held at the 55 GB floor).
**Probe key:** ✅ probed this pass · 📄 from the Nov 12 drive-models MANIFEST / Nov 6
parts-library INVENTORY / Nov 7 survey (not re-probed) · 👁 listing only.

Licences are stated **only where recorded** in a LICENSE.txt / manifest. "Not recorded"
means exactly that — do not assume terms.

---

## Headline finds (not in the Nov 7 survey)

1. **catperson-furry (CC0)** — an anthro felid with a *complete bone face machine*:
   `defJawL` + `defJawU`, `defteethLower`, `defTongue.000–003`, `defEyeball.L/R`, and a
   full per-lid eyelid rig, in a 145-bone armature. Sat in the parts library inventoried
   as a "donor reference" and never probed until now. Low-poly (single 5,160-vert body
   mesh, head not separable) — it's a **jaw-machine donor**, not a face graft. CC0.
2. **Low-poly lion (unityking24) carries a full Rigify face rig** — jaw_master, jaw
   L/R, teeth.T/teeth.B, tongue chain, brows, lids, cheeks, nose — the complete Rigify
   facial system on a 1,510-vert feral lion mesh (823 bones incl. Rigify widgets).
   A clean blueprint of a production felid face rig. CGTrader Royalty Free (no AI).
3. **KFM-G "Tiger" heads (BOOTH)** — two **head-only** rigged units (A001/A002):
   53-bone head armature, 5,137-vert head mesh with 31–35 shape keys (full VRChat
   viseme set + blinks), separate Ears (544 v) and Eye (228 v, CatsEye key) meshes.
   No jaw bone — mouth is viseme-driven. Felid, kemono style, graft-shaped by design.
4. **Bearyl Canine V4 (Jinxxy)** — the strongest canid machine in the library:
   159 bones with **LowerJaw**, Tongue.001–006, Snout, Eye.L/R; Body (17,207 v) carries
   **189 shape keys** (full visemes + ear/face sets); separate Eyes mesh (2,432 v,
   79 keys). Study-tier terms (no redistribution of base files).
5. **Zach / Drake set (Drive)** — anthro dragon with **Jawbone** + Tongue1–4 + eye
   bones (123-bone rig, visemes). The sculpt version holds the library's best
   *separated* face parts: Teeth top 6,911 v / Teeth bottom 5,343 v / Tongue 602 v /
   Eyes 1,028 v as their own meshes.
6. **Zairiza Dragon Base (Drive)** — Jaw + Jaw_End, six-segment tongue + split-tongue
   bones, separate Headgeo (5,280 v, 11 expression keys) and BottomTeeth (695 v);
   ~70 swappable part meshes. The parts-standard made real.
7. **Awtter (Drive)** — rigged otter base: **Jaw** bone, Tongue1–4, eye bones, ear
   chains, 66 shape keys (full VRChat visemes). A mustelid — same family as Brand's
   badger; the closest jaw machine to Brand in the whole sweep.
8. **Valence "Prisoner"** — the face-rig ceiling of the library: 1,242-bone rig,
   jawbone + teeth-top/bottom master bones, separate upper teeth (2,452 v), under
   teeth (2,274 v), tongue (162 v), eyes (964 v), per-lid/brow/cheek bone systems.
   Human male, game asset, **reference only** — a rig reference, never a donor.

---

## Ranking — Kaleaon (felid first · anthro · jaw machine)

| # | Candidate | Why | Cost / caveat |
|---|---|---|---|
| 1 | **Lion Warrior** — `parts-library/cgtrader/medieval-fantasy-pack-ivarnvim/lionRIGGED.fbx` ✅ | Still the only **anthro lion** with a complete bone jaw machine — probe re-verified: `CC_Base_JawRoot`, Tongue01–03, Teeth01/02, UpperJaw, L/R Eye (71 bones). Same CC rig family Kaleaon's 89-bone armature derives from. | Stylised game face, stern expression baked, coat textures missing from the download (re-download or repaint). Single 27,497-v mesh — teeth/tongue are bone-driven regions, not separate meshes. CGTrader RF (no AI). |
| 2 | **catperson-furry** — `parts-library/existing-haul/catperson-furry-cc0/` ✅ | **CC0** anthro felid whose rig has the whole machine boned (jaw L + upper jaw, lower teeth, tongue ×4, eyeballs, full lids). Best *machine donor* in the pool — the jaw/teeth/tongue bone design can be lifted wholesale. | Low-poly stylised (5,160 v whole body, single mesh) — geometry is a reference, not a graft. |
| 3 | **Leopard Hybrid A2** — `parts-library/cgtrader/leopard-hybrid-a2-animated3d/` ✅ (native .blend probed) | Best-modelled felid face, full stop: realistic snow leopard (Kaleaon's other half), modelled open mouth/teeth/tongue/interior, globe eyes, 4K PBR. | Probe tempers the survey's rig read: the 74-bone Bip01 rig has **no named jaw bone** — head detail bones are unnamed, per-bone jaw articulation unverified. Feral neck junction = hardest graft; rest pose is a part-open snarl. Single 22,848-v mesh. CGTrader RF (no AI). |
| 4 | **Low-poly lion Rigify** — `parts-library/cgtrader/low-poly-lion-unityking24/low_poly_lion.blend` ✅ | A **lion** wearing the complete Rigify face rig (jaw, teeth.T/B, tongue, brows, lids, cheeks, nose). Cleanest felid face-rig blueprint we own. | Feral quadruped, 1,510-v mesh — rig-design donor only. CGTrader RF (no AI). |
| 5 | **KFM Tiger heads A001/A002** — `character_assets/booth/KFM-G-A001_Tiger_Parts.zip` ✅ (FBX exports probed) | **Head-only** felid units built to be grafted: 53-bone head rig, viseme mouths, separate ears + eye meshes. | No jaw bone (visemes only); kemono/toony style — wrong end of Kaleaon's realism axis. Terms: VRChat public use allowed if avatar name includes "kurotori" (BOOTH manifest). |
| 6 | **Zach set** — `character_assets/drive-models/` ✅ | Not felid, but its separated teeth/tongue/eyes are donor-grade parts for *whatever* head wins: teeth top 6,911 v / bottom 5,343 v / tongue 602 v / eyes 1,028 v; rigged version bones them (Jawbone, Tongue1–4). | Dragon, anthro, VRChat-stylised. Licence not recorded. |
| 7 | **Zairiza Dragon Base** — `character_assets/drive-models/Dragon Model Base (Zairiza).zip` ✅ (SFW .blend probed) | Jaw + 6-segment tongue + split-tongue bones; Headgeo 5,280 v with 11 expression keys; BottomTeeth separate; modular parts throughout. | Dragon; commercial base, "Terms of Use.jpg" inside the zip not read — licence not verified. |
| 8 | **Cougar** — `parts-library/sketchfab/cougar-galileogb/` 📄 | Anthro felid, separate eye globes + mouth-interior piece, heavy brow (survey #3). | **No jaw bone**, short narrow muzzle, and the .blend is corrupt (invalid shape-key pointer — the same KEKey fault the Bearyl Canine throws on load; Blender deletes the key and continues, but the file intermittently aborted Blender in the survey). CC-BY. |
| — | **Valence Prisoner** — `parts-library/valence-beastbeat/raw/Prisoner.blend` ✅ | Listed for completeness: the most complete jaw machine we hold (see headline 8). | Human; reference-only licence; **excluded as a donor** (survey triage stands). |
| — | Roaring Lion / Poly Haven Lion Head 📄 | Mane/brow/face-plane reference gold. | Both static scans, no rig, no separable parts — reference only. |

## Ranking — other sonas

- **Pyn (fennec):** **Codaj Anthro Fennec** (`parts-library/sketchfab/anthro-fennec-rigged-codaj/`, CC-BY) ✅ — 107 joints, 4-segment ear chains, Eye bones; single 41,304-v mesh. Caveat: **no jaw bone and 0 morphs** — the mouth does not open in this export. The **BVH fox** (below) is the fennec-relevant jaw machine. Fox Fem Full Rig (Azuliezeiro, CC-BY): its GLB skin collapsed to 1 joint on export — rig unusable as held. Cute Furry Fox (CC-BY): static, but head is a separate 10,942-v mesh with ARKit/lipsync blendshapes.
- **Wolves — Gamma / Alpha / Beta / Delta:** **Bearyl Canine V4** (headline 4) is the
  machine to beat. CC-BY alternatives from GalileoGB ✅: **Terris-old** (.blend —
  separate Head_Combined 3,202 v with **24 face shape keys**: MouthOpen, brows, winks,
  smirks; 81 bones, Ear/Eye bones), **Taryk** (separate Head 3,683 v, 12 face keys,
  separate Eyes 1,928 v), **Terris** FBX (79 bones, 15 face keys on the body mesh),
  **Tarris Grey** (111 bones, separate Head_Mas 1,920 v + two 964-v eye globes),
  **Oracle / Orca** (Eye bones + separate 1,928-v Eyes; no jaw). All GalileoGB mouths
  are shape-key, not jaw-boned. **Mesh 9 Furry** (keh, CC-BY) ✅ — white fox/wolf anthro
  with an actual **`b_Jaw`** bone + eye bones + separate Eyes mesh (916 v), 61 joints.
  **Bork** (BOOTH, muscular wolf) ✅ — **Mouth** bone + Tongue–Tongue.004 chain, eye
  bones, 31 viseme keys; terms prohibit redistribution (study tier). **CVRxEarth Big
  Bad Wolf** (`existing-haul/wolf-rigged-ccby/` = lineup `wolf_cvrx/`, CC-BY) ✅ —
  222 joints, 64 morphs, feral; no jaw bone.
- **Jorge (St. Bernard):** Bearyl Canine (canid machine, floppy-ear capable) and Bork
  (muscular wolf build) lead; **Female Dog Furry** (rhl89ryo, CC-BY) ✅ — 144 joints,
  Tongue chain ×8 bones, separate teeth/tongue/eye meshes flagged in the GLB, 4 morphs;
  no jaw bone.
- **Brand (badger):** no badger exists anywhere in the sweep. Nearest family donor is
  **Awtter** (mustelid, Jaw + tongue chain + visemes — headline 7); canid machines
  (Bearyl/Bork) are the fallback.
- **Sen (bear):** **the gap stands** — no bear rig in Drive, parts library, harvest or
  lineup. Closest relative: **Panda Girl** (futaba, CC-BY) ✅ — anthro panda wearing the
  full Rigify face rig (742 joints incl. widgets; teeth.T/B, jaw_master, tongue chain).
  Stylised; the 172 MB full-Rigify .blend was never downloaded (GLB probed).
- **Sage (horse):** **Free Horse** (DinoReplicas, CC-BY) ✅ — the GLB export has **no
  skin** (7 meshes, 23,893 v, static); modelled mouth interior/teeth per the parts
  INVENTORY, but no rig as held. No rigged equine head in the sweep. (Jinxxy Minotaur
  is bovine, not equine — listed only, §Unprobed.)
- **Thatch (owl):** nothing avian anywhere in the sweep. Gap stands.
- **Hollis (serval):** felid small-cat options — **cat-rigged** (Vr-cvantorium, CC-BY) ✅
  feral cat, 35 joints, ear chains, no jaw (also at `bodies-3d/harvest/cat/` — same
  file); **anthro-female-cat-base** (AKM, CC-BY) ✅ 63 joints, ear chains, separate
  eyes mesh (74 v) — identical file to lineup `cat_base.glb`; **Persipia** (AKM Siamese,
  CC-BY) ✅ 65 joints + 9 morphs (blink/smile/mouth-open face keys per INVENTORY);
  **Kitty Base** GLB lost its skin in export (no skin in either copy held).
- **Otter (library bonus):** Awtter (headline 7) + **Otter-chan** (AKM, CC-BY) ✅ —
  65 joints, eyes_target/eyes_base bones, separate eyes mesh, 2 morphs.

---

## Full candidate tables

### A. Drive Models folder (local mirror `~/workspace/character_assets/drive-models/` + BOOTH pulls)

| Candidate | Source / format | Species · anthro/feral | Rigged | Jaw | Teeth / tongue / eyes | Head verts | Licence | Size |
|---|---|---|---|---|---|---|---|---|
| Zach Rigged NO IK ✅ | Drake_Model_and_dick.zip → .blend | Dragon · anthro | **Yes — 123 bones** | **Jawbone** | Tongue1–4 bones; EyeLeft/Right bones; parts separate in sculpt ver. (below) | n/a (Body single mesh 57,937 v; 18 shape keys incl. visemes) | Not recorded | zip 46.5 MB |
| Zach (1) sculpt ✅ | loose .blend | Dragon · anthro | No (5-bone placeholder "Test Rig (Dont use)") | — | **Teeth top 6,911 / bottom 5,343 / Tongue 602 / Eyes 1,028 — all separate meshes** | n/a (Body 42,993 v) | Not recorded | 39.8 MB |
| Awtter base 2.9.71 ✅ | loose .blend | Otter · anthro | **Yes — 78 bones** | **Jaw** | Tongue1–4 bones; LeftEye/RightEye bones; ear chains; 66 shape keys (full visemes + blinks) | n/a (single Body mesh 25,256 v) | Not recorded | 19.8 MB |
| Zairiza Dragon Base SFW ✅ | zip → .blend (probed from zip) | Dragon · anthro | **Yes — 146 bones** | **Jaw + Jaw_End** | TongueBase–Tongue6 + split-tongue bones; REye/LEye bones; **BottomTeeth separate (695 v)**; ForkedTongue part (386 v) | **Headgeo 5,280 v** (11 expression keys) | Terms of Use.jpg in zip, not read — not verified | zip 291.6 MB |
| Valence "Prisoner" ✅ | zip / parts-library copy | Human · anthro | **Yes — 1,242 bones** | **jawbone.x + masters** | **Upper teeth 2,452 / under teeth 2,274 / tongue 162 / eyes 964 — separate meshes**; teeth top/bot master bones; full lid/brow/cheek systems | n/a (body_low 23,686 v) | Game asset — **reference only** | zip 148.3 MB |
| Kobult ✅ | BOOTH zip → .fbx | Kobold · anthro kemono | **Yes — 108 bones** | **Jaw** | Tongue_01–04 + End bones; Eye_Root L/R; ear chains; 278 shape keys (visemes etc.) | n/a (single Body 9,209 v) | Pastebin licence: public uploads encouraged (BOOTH manifest) | zip 88.1 MB |
| KFM Tiger Head A001 ✅ | BOOTH zip → .fbx | Tiger · **head only** | **Yes — 53 bones** | No (visemes) | Eye_L/R bones; **Ears separate 544 v; Eye separate 228 v** | **5,137 v** (31 keys: visemes + blinks) | VRChat public use w/ "kurotori" in avatar name | zip 100.5 MB |
| KFM Tiger Head A002 ✅ | BOOTH zip → .fbx | Tiger · **head only** | **Yes — 53 bones** | No (visemes) | Same as A001 | **5,137 v** (35 keys) | Same | (same zip) |
| Bork ✅ | BOOTH zip → .blend (FBX imported empty headless) | Wolf (muscular) · anthro kemono | **Yes — 73 bones** | **Mouth bone** | Tongue–Tongue.004 bones; LeftEye/RightEye + Eye.L/R; **Eye separate 290 v**; 31 viseme keys | n/a (Body 4,228 v) | Redistribution/resale prohibited — study tier | zip 86.6 MB |
| Lesser Mokuri ✅ | BOOTH zip → .fbx | Kemono original · anthro | **Yes — 144 bones** | No | Eye_L/R bones; ear + hair-ear chains; 18 expression keys | n/a (Body 3,792 v) | UV licence; personal commercial + derivative distribution allowed (BOOTH manifest) | zip 73.6 MB |
| Maromage ✅ | BOOTH, loose .vrm | Kemono chibi · anthro | **Yes — 64 joints** | No | Cheek (hoppe) + hair (mage) bones; face via **174 morph targets** | n/a (single mesh 17,576 v; 0.9 m) | UV licence (BOOTH manifest) | 21.4 MB |
| perfect-bara (Mixamo) ✅ | zip → .fbx | Human bara · anthro | Yes — 65 bones (Mixamo) | No | Head/Neck only | n/a (single mesh 63,557 v) | Not recorded (Tripo-AI geometry on Mixamo rig) | zip 6.7 MB |
| furry.glb ✅ | loose .glb | Unnamed sculpt | **No skin** | — | — | n/a (268,301 v static) | Not recorded | 11.8 MB |
| true_furry_rig_version.glb ✅ | loose .glb | Wolf (survey) | **No skin despite the name** | — | — | n/a (198,572 v static) | CC-BY (parts-library copy) | 9.0 MB |
| BBW bulky gray werewolf 👁 | .7z (no 7z tooling on VM) | Werewolf · Skyrim NIF | Game skeleton (unverified) | — | NIF head mesh inside (maleheadwerewolff) | — | Not recorded | 9.7 MB |
| orc_skull 📄 | zip → glTF | Orc skull (no flesh) | No — static | — | Teeth as scan surface | 799,388 tris | **CC BY 4.0** (licence.txt in zip) | 14.0 MB |
| CustomHumanHorsePenis 📄 | .7z / in Drake zip | Equine anatomy **part** (not a head) | 48-bone rig | — | — | — | Not recorded | 1.6 MB |

### B. Parts library (`~/workspace/bodies-3d/parts-library/`) + harvest

| Candidate | Source / format | Species · anthro/feral | Rigged | Jaw | Teeth / tongue / eyes | Head verts | Licence | Size |
|---|---|---|---|---|---|---|---|---|
| Lion Warrior ✅ | cgtrader .fbx | Lion · anthro | **71 bones** | **JawRoot** | Tongue01–03, Teeth01/02, UpperJaw bones; L/R Eye bones | n/a (single mesh 27,497 v) | CGTrader RF (no AI) | pack ~1.28 GB total |
| Leopard Hybrid A2 ✅ | cgtrader .blend (native) | Snow leopard · **feral** | 74 bones (Bip01) | No named jaw bone | Mouth/teeth/tongue modelled as mesh regions; globe eyes | n/a (single mesh 22,848 v) | CGTrader RF (no AI) | Blender.zip in folder |
| Low-poly lion ✅ | cgtrader .blend | Lion · **feral** | **823 bones (Rigify, incl. widgets)** | **jaw + jaw_master** | **teeth.T / teeth.B bones; tongue chain; brow/lid/cheek/nose systems** | n/a (lion mesh 1,510 v) | CGTrader RF (no AI) | folder |
| Cougar 📄 | sketchfab .blend | Cougar · anthro | Rigify-style (survey) | **No jaw bone** | Separate mouth-interior piece; teeth piece 68 v; eye globes 964 v | ~2,450 head-zone | CC-BY | folder (blend corrupt) |
| catperson-furry ✅ | existing-haul .blend (itch.io) | Cat person · anthro | **145 bones** | **defJawL + defJawU** | **defteethLower; defTongue.000–003; defEyeball L/R; full eyelid rig** | n/a (single body mesh 5,160 v) | **CC0** | 5.5 MB |
| Codaj Anthro Fennec ✅ | sketchfab .glb | Fennec · anthro | **107 joints** | No (0 morphs — mouth static) | Eye_L/R + LeftEye/RightEye bones; Ear1–4 chains | n/a (single mesh 41,304 v) | CC-BY 4.0 | 4.0 MB |
| BVH Rig Fox/Rabbit/Cat ✅ | sketchfab .glb | Fox + rabbit + cat · anthro | **318 joints total; main skin 299** | **jaw_master + jaw L/R (Rigify)** | **teeth.T/B, tongue chain (Rigify face)** | n/a (163,838 v across 25 meshes / 3 models) | **CC-BY-SA ⚠️** | 15.7 MB |
| Panda Girl ✅ | sketchfab .glb | Panda · anthro | **742 joints (Rigify incl. widgets)** | **jaw_master + jaw (Rigify)** | **teeth.T/B, tongue chain** | n/a (148,234 v) | CC-BY | 27.7 MB |
| Mesh 9 Furry ✅ | sketchfab .glb | Fox/wolf · anthro | 61 joints | **b_Jaw** | b_Eye.L/R bones; **Eyes separate 916 v** | n/a (body 6,284 v) | CC-BY | 1.4 MB |
| Female Dog Furry ✅ | sketchfab .glb | Dog · anthro | 144 joints | No | **Tongue chain ×8 bones; teeth/tongue/eye meshes present**; Eye_R/L bones; 4 morphs | n/a (58,032 v) | CC-BY | 8.2 MB |
| Toriel Head Rig ✅ | sketchfab .glb | Goat-like · **head only** | 46 joints | (jaw flag from joint names) | **Tongue bone + tongue mesh 155 v; eye/eyelash/eyebrow bones; eyes separate 596 v ×2** | **2,613 v total (head parts)** | CC-BY — ⚠️ franchise character, reference only | 0.3 MB |
| Terris-old ✅ | sketchfab .blend | Wolf · anthro | 81 bones | No (shape keys) | Ear/Eye bones; **24 face keys** (MouthOpen, brow, wink, smirk) | **Head_Combined 3,202 v** (separate mesh) | CC-BY | folder |
| Taryk ✅ | sketchfab .fbx | Wolf-line (GalileoGB) · anthro | 73 bones | No (shape keys) | Ear/Eye bones; **12 face keys**; **Eyes separate 1,928 v** | **Head 3,683 v** (separate mesh) | CC-BY | folder |
| Terris ✅ | sketchfab .fbx | Wolf · anthro | 79 bones | No (shape keys) | Ear/Eye bones; 15 face keys incl. MouthOpen | Head_Combined piece 1,412 v | CC-BY | folder |
| Tarris Grey ✅ | sketchfab .fbx | Wolf · anthro | 111 bones | No | Ear/Eye bones (+ends); **eye globes separate 964 v ×2** | **Head_Mas 1,920 v** | CC-BY | folder |
| Oracle ✅ | sketchfab .fbx | (GalileoGB) · anthro | 107 bones | No | Eye.L/R bones; **Eyes separate 1,928 v** | n/a (Mesh 6,225 v) | CC-BY (+ author no-NFT term on Orca) | folder |
| Orca ✅ | sketchfab .fbx | Orca · anthro | 81 bones | No | Eye.L/R bones; **Eyes separate 1,928 v** | n/a (Mesh 6,264 v) | CC-BY + no-NFT | folder |
| Wolf CVRxEarth ✅ | existing-haul .gltf (= lineup wolf_cvrx) | Wolf "Big Bad Wolf/Death" · feral | **222 joints** | No | Ear/head bones; 64 morphs; eye mesh flagged | n/a (67,426 v) | CC-BY 4.0 | 13.3 MB bin |
| Border Collie Scientist ✅ | sketchfab .glb (= lineup copy) | Border collie · anthro | 66 joints | No | Ear base/tip chains; eye mesh; 12 morphs | n/a (8,757 v) | CC-BY | 1.7 MB |
| Anthro Female Cat Base ✅ | sketchfab .glb (= lineup cat_base) | Cat · anthro | 63 joints | No | Ear chains; **eyes separate 74 v**; whiskers mesh | n/a (5,731 v) | CC-BY | 0.5 MB |
| Persipia ✅ | sketchfab .glb (= lineup copy) | Siamese cat · anthro | 65 joints | No (9 morphs — face keys) | Ear chains; eyes separate 74 v | n/a (29,105 v) | CC-BY | 3.0 MB |
| Otter-chan ✅ | sketchfab .glb | Otter · anthro | 65 joints | No | eyes_target/eyes_base bones; eyes separate 74 v; 2 morphs | n/a (20,431 v) | CC-BY | 1.9 MB |
| Bunny Furry Commission ✅ | sketchfab .glb | Rabbit · anthro | 67 joints | No | EyeJoint_R/L; Ear1–4 chains | n/a (10,646 v) | CC-BY | 7.2 MB |
| Leopard Animation Run ✅ | sketchfab .glb | Leopard · feral | 47 joints | BN_Mouth bone only | Eye/ear (beard) bones | n/a (3,644 v) | CC-BY | 1.0 MB |
| Cat rigged ✅ | existing-haul .gltf (= `harvest/cat/`) | Cat · feral | 35 joints | No | Ear chains; head bone | n/a (1,750 v) | CC-BY 4.0 | 0.2 MB |
| Styloo cat ✅ | existing-haul .glb | Cat · feral low-poly | Skin (283 joints — Rigify widgets incl.) | No | Head/neck bones | n/a (2,547 v) | CC0 | 0.3 MB |
| Styloo dog ✅ | existing-haul .glb | Dog · feral low-poly | 46 joints, 6 anims | No | — | n/a (3,344 v) | CC0 | 1.6 MB |
| Cute Furry Fox 📄/✅ | sketchfab .glb | Fox · anthro | **No skin** | — (ARKit/lipsync blendshapes) | **Head separate mesh** | **Lisa_low_Head 10,942 v** | CC-BY | 4.8 MB |
| Fox Fem Full Rig ✅ | sketchfab .glb | Fox · anthro | ⚠️ skin = 1 joint (export lost the rig) | — | Eyes mesh 916 v | n/a (5,802 v) | CC-BY | 0.3 MB |
| Kitty Base ✅ | sketchfab .glb (= lineup copy) | Cat · anthro | ⚠️ **No skin** in GLB | — | — | n/a (15,890 v) | CC-BY | 0.8 MB |
| Free Horse ✅ | sketchfab .glb | Horse · feral | ⚠️ **No skin** in GLB | — | Mouth interior/teeth modelled 📄 | n/a (23,893 v) | CC-BY | 1.4 MB |
| Golden Retriever ✅ | existing-haul .gltf (= `harvest/retriever/`) | Dog · feral | **No skin** (textures-only extraction; full 42 MB bin stayed in the source zip) | — | Coat/eye PBR textures only | n/a (423,175 v in held gltf) | CC-BY 4.0 | textures ~9.6 MB |
| Roaring Lion 📄 | sketchfab .glb | Lion · feral statue | No | — | Scan surface only | 33,392 v | CC-BY | 4.2 MB |
| Poly Haven Lion Head 📄 | polyhaven .gltf | Lion head bust (relief) | No | — | Sculpted shut | 25,380 v | **CC0** | ~4 MB |
| Z-Anatomy atlas 👁 | existing-haul pointer | Human/animal anatomy structures | n/a | — | Teeth/skull/eye structures harvestable in Blender | — | **CC-BY-SA ⚠️** (ship separately) | 306 MB zip at character_assets root |
| Eyeball (CrisLArt) / Eyeball brown iris (Epim) ✅ | sketchfab .glb | Eye parts | No | — | Cornea + iris separate (1,042 v ea.) / 2-mesh eye 5,444 v | — | CC-BY | 3.9 / 2.3 MB |
| Carnassial microCT 📄 | sketchfab | Canid tooth scan | No | — | Real carnassial/fang form (2M tris — decimate) | — | CC-BY | folder |

### C. Furry lineup (`threejs-lineup/models/`) — all duplicates of parts-library files

| Lineup file | Same as | Note |
|---|---|---|
| pyn_fennec.glb | Codaj Anthro Fennec (B) | Identical probe: 107 joints, 41,304 v |
| border_collie.glb | Border Collie Scientist (B) | Identical |
| cat_base.glb | Anthro Female Cat Base (B) | Identical |
| persipia.glb | Persipia (B) | Identical |
| kitty_base.glb | Kitty Base (B) | Identical (no skin) |
| wolf_cvrx/scene.gltf | Wolf CVRxEarth (B) | Identical: 222 joints, 64 morphs |
| bara_wolf_avatar.glb ✅ | = Drive "perfect-bara" FBX, re-exported | 65 Mixamo joints, 72,166 v, 4 anims (Idle/Walk/Wave/Dance); head = Mixamo Head bone only, **no jaw**; two 1,488-v sphere meshes (eyes?) unnamed |

The lineup's other 7 avatars are procedural-primitive placeholders (no GLB) — no heads to probe.

---

## Gaps that did not close

- **Bear (Sen):** nothing. Panda Girl's Rigify face machine is the only bear-family rig.
- **Badger (Brand):** nothing. Awtter (mustelid cousin) is the nearest jaw machine.
- **Owl (Thatch):** nothing avian anywhere.
- **Horse (Sage):** the one horse model held is an unrigged GLB export.
- **Second Life inventory heads:** the SL catalogue (`~/workspace/sl-client/`) holds
  head/asset names, but SL meshes are export-blocked grid-side (object asset UUIDs
  withheld over HTTP; only a Firestorm wear-scan on Joe's Windows machine can extract
  them). Noted per brief — no work done here.

## Unprobed — and why

| Item | Why |
|---|---|
| Drive: **30 Stylized Animal Character Base Meshes** zip (277 MB) | Drive-resident only; disk floor forbids the pull. 30 species bases (.blend/FBX/OBJ) — species list not published and not enumerable without downloading. **Highest-value unprobed item in the folder.** |
| Drive: BOOTH big five — **Vix** 190 MB (fox), **Taro** 175 MB (silver fox), **Rabi** 283 MB (deer), **Lumelana** 168 MB, **ChimeraMK2** 136 MB | Drive-resident only (disk floor). All VRChat avatar products (rigged by type, PhysBone) — heads unprobed. |
| Drive: **Complete Animals Pack 1+2** (4.08 GB multipart RAR) | Drive-resident; needs ≥5 GB headroom above the floor **and** unrar tooling (none installed). Contents unverified — MakeHuman community packs (Joe: Pack 1 CC0, Pack 2 CC-BY — unverified from the files). |
| Drive: Download+sample+1.stl (16.9 MB) | STL is a static format — no rig is possible; identity unknown. |
| Jinxxy **ArchaType.blend** (199.8 MB in zip) | Listed only — the Canine V4 probe was prioritised (Archa is its variant). |
| Jinxxy **Minotaur.blend** (151.1 MB in zip) | Listed only — bovine; no bovine sona. |
| Vladlarin lion.blend (869 MB) | Survey-established static feral lioness (no rig/parts); not re-probed. |
| Cougar .blend | Not re-probed: corrupt shape-key pointer; survey data stands (same KEKey fault seen live on the Bearyl Canine, which loads past it with the key deleted). |
| Escanor (cgtrader) | Human franchise character — reference only per INVENTORY; RARs unextracted (no rar tooling). |
| Realistic Male Full Body Sculpt (daniartist) | Human ZBrush sculpt in a 115 MB zip — no head rig relevance. |
| Muscular Heroic Male (BraineyBites) ✅ spot-checked | Static GLB (no skin), human — not a head candidate. |
| Julianemilioqwe bara sculpts (alternative-bara / bara-earthquake / furry-dad) ✅ spot-checked | All static POSITION-only GLBs — form reference only. |
| Protogen base (radthezealot) ✅ spot-checked | 56 joints, ear/head bones, no jaw — robot sona, no matching Titan. |
| Bearyl Substance/Unity packages; Drake unitypackage; Zach clothing | Texture/app packages of models already probed in .blend/.fbx form. |

## Method notes

- "Head verts" is exact only where the head is a separate mesh; single-mesh avatars
  report total mesh verts and say so.
- Rigify bone counts (Panda Girl 742, low-poly lion 823, BVH main skin 299) include
  Rigify's ORG/MCH/widget bones — the *deform* face set (jaw/teeth/tongue/brow/lid)
  is what the jaw/teeth/tongue columns describe.
- Two GLB exports in the library have **lost their rigs** (Fox Fem Full Rig → 1 joint;
  Kitty Base → no skin) and one is a static export of a rigged product (Free Horse).
  The rig may exist in source files we don't hold — flagged, not assumed.
- All /tmp probe extractions (Zach Rigged, Leopard A2, Dragon SFW, Bearyl Canine,
  KFM/Bork/Kobult/Mokuri FBXs — ~340 MB) were deleted after probing; free space
  verified back at the 55 GB floor line.
