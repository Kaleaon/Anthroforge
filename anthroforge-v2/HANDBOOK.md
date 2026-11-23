# AnthroForge Handbook — The One-Page Map of the Whole Project

*Consolidated Nov 12, 2026 from the full doc set in this folder. This handbook
indexes and summarises; it does not override any source doc. Where docs
disagree, the disagreement is flagged in §5, not smoothed over.*

**Status as of Nov 12, 2026 (evening)** — §2, §5 and §6 refreshed against
the files on disk after the day's build/study waves (sliders, hyper, fur
A1–A20, model craft B1–B20, app integration, Sen). Doctrine (§1, §3) is
unchanged except where a ruling landed today and is marked as such.

---

## 1. Project summary

**AnthroForge is a parametric avatar creator for anthropomorphic and fantasy
characters** — a real installable app (Windows first), not a web page. A
character is *created*, not loaded: a base body/head + a vector of sliders +
a manifest of swappable rigged parts + a material stack, serialised into a
small portable **character record** that doubles as a share code.

Four load-bearing ideas, in the order the project adopted them:

1. **Learn, don't guess.** Slider deformations are *measured* from real
   models by the learn-then-delete pipeline — fit a base over a target,
   extract the per-vertex deformation, delete the target, keep the data.
   Exact same-topology pairs give exact deltas (Fat Males); foreign topology
   goes through registration/fitting and ships with a measured residual
   (foreign-fit POC: median 0.05 cm, p95 0.28 cm) — never a fake "100%".
2. **Omniversal sliders.** One slider vocabulary across every base. A slider
   is a *semantic record* (name, region mask, endpoint anchor in metres,
   range, provenance); each base mesh holds a generated **instance** of it
   with its own QA numbers. "Belly" means the same thing on our base, on
   MakeHuman's hm08, and in Skyrim BodySlide data.
3. **Layered anatomy.** Heads (and later bodies) are built skull → muscles
   → tissue. A brow ridge is bone, a scowl is muscle, padding is tissue —
   a surface merely wrapped over the form reads too skeletal (Joe's rule).
4. **Swappable parts.** Body parts attach/detach at named sockets on the
   shared skeleton (Spore/SL model). Rigged parts (own skin weights) are
   preferred; rigid bone-attached is the fallback tier. Parts carry conflict
   metadata and a visible complexity cost.

Supporting stances: stylisation (realistic ↔ toony) is its own axis over the
species presets; agents are first-class users — the whole creator surface is
exposed over an **MCP connector** so the family can build characters without
the GUI; everything is offline-first, files-are-the-truth, and every asset
in the library carries a licence **tier** (build / study / reference) that
the export pipeline enforces.

---

## 2. Status table — every doc & system

State key: **spec** = written design, not yet built · **prototype** = partial
build exists · **built** = working artifact exists · **verified** = build
checked against its own acceptance criteria.

| Doc / system | Covers | State | Link |
|---|---|---|---|
| APP_BLUEPRINT.md | The master build spec: product, Tauri+Python+Blender architecture, data model, full MCP design (28 tools), exports (GLB/DAE/FBX/BLEND/STL), fur, skinning, roadmap, D1–D8 decisions | **spec** (complete; 8 decisions pending Joe) | [APP_BLUEPRINT.md](sandbox://workspace/anthroforge-v2/APP_BLUEPRINT.md) |
| anthroforge_3d_pro_v2.html | The working web prototype: real 36-bone Babylon skeleton, skinned meshes, validated GLB export | **built + verified** (headless-Chrome checks passed; becomes the read-only viewer fallback in the app plan; loads shared classic IIFE codec/vocabulary/preset/record scripts from `../anthroforge-app/telegram-miniapp/`, so run local HTTP servers from the repository root — `file://` opens also work in Chromium) | [anthroforge_3d_pro_v2.html](sandbox://workspace/anthroforge-v2/anthroforge_3d_pro_v2.html) |
| MAKEHUMAN_OMNIVERSAL.md | MakeHuman/MPFB2 research, licence table (assets CC0, output disclaimed), the canonical slider record format, retargeting design, first-proof spec | **spec → executed** (canonical record format is the production format of the app library; first proof complete, see first-proof/) | [MAKEHUMAN_OMNIVERSAL.md](sandbox://workspace/anthroforge-v2/MAKEHUMAN_OMNIVERSAL.md) |
| CREATOR_LESSONS.md | Teardowns of the 10 deepest commercial creators (BG3, SF6, WWE 2K, Starfield, Cyberpunk, Saints Row, Dragon Age, Monster Hunter, Soulcalibur, GTA Online + Sims 4/Elden Ring) → 12 rules (R1–R12) for AnthroForge | **complete** (research) | [CREATOR_LESSONS.md](sandbox://workspace/anthroforge-v2/CREATOR_LESSONS.md) |
| HEROFORGE.md | Hero Forge teardown: parts-first creator, species = preset bundle, body-plan partition, paywall-on-export model; §9 = honest "can we grab the parts" answer (no) | **complete** (research) | [HEROFORGE.md](sandbox://workspace/anthroforge-v2/HEROFORGE.md) |
| ELDRITCH_FOUNDRY.md | Eldritch Foundry teardown: slider-forward rival, ancestry = commitment, Ancestry→Lineage taxonomy, free-routes audit (none exist; cheapest file $5) | **complete** (research) | [ELDRITCH_FOUNDRY.md](sandbox://workspace/anthroforge-v2/ELDRITCH_FOUNDRY.md) |
| species-head-spec.md | The head system: comparative skull proportions, **31-slider** base-head spec (Muzzle/Cranium/Ears/Jaw-Eyes + 7 brow sliders), 7 species presets (wolf, red fox, fennec, lion, panther, cat, dog), style-axis + modularity addenda | **spec** (complete; brow-reconciled) | [species-head-spec.md](sandbox://workspace/anthroforge-v2/species-head-spec.md) |
| brow-study.md | Supraorbital spectrum from craniometry (modern human 0, Neanderthal +56…+100, gorilla ≈+150 [E]), 7-slider brow design with layer assignments, revision verdicts on both head specs | **complete** (research; verdicts applied) | [brow-study.md](sandbox://workspace/anthroforge-v2/brow-study.md) |
| preset-orc-bara.md | First full character-family preset: bara orc — head vector on the 31-slider frame (incl. a flagged `JawProtrusion` extension), two body sub-presets (Strongman / Bodybuilder) on HIMBO data, teeth + materials | **spec** (complete; honesty box flags weakest numbers) | [preset-orc-bara.md](sandbox://workspace/anthroforge-v2/preset-orc-bara.md) |
| base-head/ (v1) | Procedural neutral base head: .blend/.glb, 20 vertex groups, proportions on-spec | **built + measured — rejected by Joe** (too cartoony/inaccurate); superseded by v2 | [base-head/BUILD_NOTES.md](sandbox://workspace/anthroforge-v2/base-head/BUILD_NOTES.md) |
| base-head-v2/ | Layered (skull→muscle→tissue) rebuild anchored on a real rigged cougar neutralised to spec | **prototype — superseded by v3** (v2 never met the spec it was built to; the line continued in v3/v4) | [base-head-v2/](sandbox://workspace/anthroforge-v2/base-head-v2/) |
| base-head-v3/ | Layered rebuild continued: real cougar neutralised to the head spec | **built + measured** — 8 of 14 proportion gates inside ±6%, every miss named with its reason; clears the construction/proportion bar with disclosed exceptions | [base-head-v3/BUILD_NOTES.md](sandbox://workspace/anthroforge-v2/base-head-v3/BUILD_NOTES.md) |
| base-head-v4/ | v3 subdivided/smoothed (v3 verts pinned as anchors), fused teeth slab split into separate upper/lower arcades | **built + verified** — teeth split confirmed from geometry (lowers ride the jaw pivot, 0 overlaps at −10°/−30° jaw rotation), gates held vs v3, facet angles ~halved. MuzzleWidth "regression" resolved as a **ruler artefact** (appendix verdict: surface-true merged width 0.2413 v3 vs 0.2412 v4). Biggest open gap: the **lip-line loop cage** (B12 F-M7) was not built. Interorbital uses physical seating 0.1122; the 0.19 spec ruling is still Joe's (see §5). No renders shipped — verification is numeric | [base-head-v4/BUILD_V4.md](sandbox://workspace/anthroforge-v2/base-head-v4/BUILD_V4.md) |
| slider-lab/ | Slider authoring code: `author_slider.py`, `mask_tools.py`, outputs | **prototype** — the SLIDER_ENGINEERING.md manual has landed (root docs, below); production slider records now live in the app library | [slider-lab/](sandbox://workspace/anthroforge-v2/slider-lab/) |
| first-proof/ | The omniversal first proof, grown into the belly lineage: Fat Males belly → whole-torso gravity field → limbs → terminal hand/foot tissue | **built + verified** — lineage v1→**v5.1** shipped (whole-body distribution from learned fields, 0 flips at +1 on both bases), plus the **v5.2 contact corrective** variant; slider records + targets on disk | [first-proof/](sandbox://workspace/anthroforge-v2/first-proof/) |
| SLIDER_ENGINEERING.md / PARTS_STANDARD.md / MARKINGS.md / expression-system.md | Slider authoring manual, parts/socket standard (28 sockets, 128-pt cost pool), markings/decals, expression system | **complete** (written; all four landed today) | [PARTS_STANDARD.md](sandbox://workspace/anthroforge-v2/PARTS_STANDARD.md) |
| MUSCLE_TISSUE_MODEL.md / BODY_PLANS.md / SPORE_AND_PARTS.md / WEIGHT_CRAFT.md / BARA_LESSONS.md | Muscle×Tissue two-vector model, body-plan partition, parts-system design notes, weight-slider craft, bara study lessons | **complete** (design/research) | [MUSCLE_TISSUE_MODEL.md](sandbox://workspace/anthroforge-v2/MUSCLE_TISSUE_MODEL.md) |
| presets-titan-batch1.md | Titan family presets batch 1: bear + badger species vectors; Pyn, Sen, Jorge character vectors | **complete** (spec; Sen since built — see characters/sen/) | [presets-titan-batch1.md](sandbox://workspace/anthroforge-v2/presets-titan-batch1.md) |
| masculine-base/ | Masculine variant of the hm08 base (gender 1.0 the only change) + belly instance re-derived per base | **built + verified** — belly re-validation 12.43 cm measured vs 12.45 cm canonical anchor (5 mm tolerance), 0 flips; frame-alignment shift documented in the folder | [masculine-base/MASCULINE_BASE.md](sandbox://workspace/anthroforge-v2/masculine-base/MASCULINE_BASE.md) |
| bara-proof/ | The bara composition proof (muscle + chest.width + tissue.strongman on hm08) + definition-relief geometry (flat abs, trap valleys, pec crease, back) | **built + verified** — coupling claims validated on mesh (COUPLING_VALIDATION.md: submergence matches the model to 3 decimals; pecs-crease coupled ratio measured 0.7347 vs predicted 0.7347; distribution axis redistributes, not scales). **Neck-field fix landed** (FIX_NECK_FIELD.md): a silent name miss had zeroed the authored neck field — combined neck girth 36.44 → **43.01 cm**, M1 0.711 → **0.853**, app packs regenerated, suite green. Seven other recipe names also resolve to zero — flagged, **Joe's decision** (see §5) | [bara-proof/BARA_PROOF.md](sandbox://workspace/anthroforge-v2/bara-proof/BARA_PROOF.md) |
| hyper/ | Hyper-range architecture: sliders as piecewise regimes past +1 | **built + verified** — belly segmented (base 0–1 shipped + authored hyper segment 1–2, ceiling 2×): naive 2× = 75 flipped faces, segment-solved 2× = **0 flips** (min_dot 0.0215) on both bases, contact re-solved per segment (0 crossings, 5.9 mm min gap). Schema gains segments, corrective validity envelopes, total-field corrective keys. Open: hyper muscle segment unauthored, belly 2→3, ear/tail onsets | [hyper/HYPER_RANGES.md](sandbox://workspace/anthroforge-v2/hyper/HYPER_RANGES.md) |
| parts-lab/kaleaon-anatomy/ | Kaleaon canon as swappable parts: quad shafts (bone-articulated, girth blendshape pair, no erection morphs) + sac-udder (209.46 L, bottom 0.0309 m) + 4 teats on own bones | **built + verified** — GLB QA-gauntlet clean (9 meshes, 93 joints, 8 morphs); zero *new* interpenetration vs the canon host file; assembly cost 39 / 128 pool | [parts-lab/kaleaon-anatomy/KALEAON_ANATOMY.md](sandbox://workspace/anthroforge-v2/parts-lab/kaleaon-anatomy/KALEAON_ANATOMY.md) |
| dynamics/ | Soft-tissue dynamics: spring-chain secondary motion (sag, lag, overshoot) for heavy soft parts + the hyper-animation research trio (scene survey / craft / techniques) | **built (prototype) + research complete** — angular-stiffness verlet chains baked exact (0.0 mm vs sim); settle time is the honest stiffness readout; Kaleaon sac anchors computed (period ≈1.95 s — needs more drag, not stiffness; a real 4–5 segment sac chain is wanted, not the r3 single bone). No collider pass yet | [dynamics/SOFT_DYNAMICS.md](sandbox://workspace/anthroforge-v2/dynamics/SOFT_DYNAMICS.md) |
| characters/sen/ | Sen end-to-end build: body composed on hm08, bear head on base-head-v3, strand groom, LOD fur cards + renders | **built + verified (stages 1 + 2)** — body 0 flipped faces, 98.9 L; head 31-slider vector ruler-verified; preset vectors match the app library exactly. Scope: the GLBs are **unrigged static bakes** (proof-of-composition, not a deployable character). Card debit: LOD0 1,700 cards ≈ ⅓ of A5's placement budget — a silhouette/tuft layer, not a continuous coat. §4.2 gates M1/M5/M6 still miss (neck/trap vocabulary ceiling; M1 improved by the neck fix, not closed) | [characters/sen/SEN_BUILD.md](sandbox://workspace/anthroforge-v2/characters/sen/SEN_BUILD.md) |
| fur-craft/ (wave A1–A20) | The fur study wave: shells/fins, card geometry, GeoNodes grooms, clumps, budgets, flow, paintmaps, card bakes, photo-fur, shell shader, colour, shading, atlas, short fur, hand-paint, two-layer, states, print fur, species profiles, fur QA | **complete** — all 20 documented in-folder. Load-bearing verdicts: **grooms are authored in Geometry Nodes** (A3; particle groom = legacy reference — evidence for D4); two-layer coat is per-species data with undercoat as the seasonal variable (A16); fur QA harness reproduces deterministically, 9 PASS / 8 FAIL on the prototype chain, gate graduations proposed (A20); strand-authored → baked cards is the shipping route (A8/A13) | [fur-craft/a3-geonodes/GEONODES_FUR.md](sandbox://workspace/anthroforge-v2/fur-craft/a3-geonodes/GEONODES_FUR.md) |
| model-craft/ (wave B1–B20) | The model-craft study wave: topology, retopo, QA gauntlet v2, anatomy passes, export standards, LOD, UV, baking, edges, blocking, hands/feet, face, digitigrade legs, appendages, clothing, morphs, rig audit, sculpt, scan cleanup, critique | **complete** — all 20 documented in-folder. Load-bearing results: retopo chain (voxel → QuadriFlow → shrinkwrap pin) hits 0.058% mean deviation (B2); QA2 found 7 library models wound inside-out + graduated checks to fail-status for our exports (B3); **B13 digitigrade legs mirror defect found and FIXED** (pair is a true pair now); clothing: plain delta transfer wins at +1, offset maintenance is worse, hyper clothing needs per-segment re-fit (B15); LOD integrity is set by LOD0's skeleton/topology, decimation only chooses what stays recognisable (B6); high→low bake pipeline run end-to-end, silhouette IoU 0.987 (B8) | [model-craft/b5-standards/STANDARDS.md](sandbox://workspace/anthroforge-v2/model-craft/b5-standards/STANDARDS.md) |
| materials-lab/ | Material records + swatch renders (skin/fur material stack) | **prototype** — MATERIALS.md + materials.json on disk; the fur_coat record stays blocked on the SL wear-scan (see adjacent table) | [materials-lab/MATERIALS.md](sandbox://workspace/anthroforge-v2/materials-lab/MATERIALS.md) |

**Adjacent systems (outside this folder, part of the same project):**

| System | State | Where |
|---|---|---|
| Learned-morph library (Fat Males exact deltas, HIMBO .osd decode, fit POC) | built + verified | `~/workspace/character_assets/learned/` |
| Teeth library (15 CC sets + TEETH.md design notes) | complete | `~/workspace/character_assets/teeth/TEETH.md` |
| Orc reference haul (5 Sketchfab CC BY models + manifest) | complete | `~/workspace/character_assets/orc/MANIFEST.md` |
| LoversLab haul (15 files: Khajiit digitigrade/head, morph systems) | complete | `~/workspace/character_assets/loverslab/` |
| SL grabber app + full inventory catalogue (65,503 items, 41,143 full-perm) | built + verified | `~/workspace/sl-client/grabber/`, `CATALOGUE.md` |
| Wear-scan queue (9,356 unique full-perm objects, 62 batches) | spec (session plan ready; runs on Joe's Windows/Firestorm) | `~/workspace/sl-client/WEAR_SCAN_QUEUE.md` |
| App core (Python Core, character record, share-code codec, geometry/build layer, MCP) | **built + verified** — suite **87 tests, all passing**; **74 slider records** (20 seed + 49 HIMBO vocabulary + composed bara builds), **11 carry hm08 geometry** (float64 canonical packs — shipped .target files' 0.1 mm rounding flips the belly's thinnest gate face, so the app never builds from them); **6 presets** (orc strongman/bodybuilder, Pyn, Sen, sen_muscle_bear, Jorge) as .afchar.json + AF1- share codes, round-tripping bit-exact; both bases registered (hm08 + masculine); MCP `export_run` + `validate_character` live, the other 30 tool names stay loud stubs. Not yet: head slider records (37 specced, 1 exists — the blocker for registering head v4), Babylon frontend wiring (5-step spec in INTEGRATION.md) | `~/workspace/anthroforge-app/INTEGRATION.md` |
| Telegram Mini App (@anthroforge_bot) | **bot live; hosting blocked on Joe** — bot answers and saves pasted AF1- share codes today; the studio page can't deploy until Joe re-authenticates the Vercel team scope (`kaleaons-projects`) on the *existing* connection (do not disconnect/reconnect); 5 finish steps scripted in BOT.md | `~/workspace/anthroforge-app/telegram-miniapp/BOT.md` |

---

## 3. Decision log

### 3.1 The blueprint decisions — D1–D8 (APP_BLUEPRINT §16.2)

All eight are **Joe's call, pending** as of Nov 12, 2026. The blueprint's
body text already *assumes* the recommendation for D6 and D7; if Joe rules
otherwise, those sections need amending.

| # | Decision | Options | Blueprint recommendation |
|---|---|---|---|
| D1 | App shell | Tauri 2 / Electron | **Tauri 2** (small, WebView2 = Chromium we already target) |
| D2 | Blender supply | Bundle pinned portable (~1 GB) / detect external | **Detect + guided download** |
| D3 | MCP HTTP exposure | Loopback-only / loopback + LAN toggle w/ token | **Loopback + toggle** (family bots are remote by design) |
| D4 | Fur primary | Strand-authored→cards / cards-authored | **Strand-authored** (Blender-native pipeline; cards bake down) |
| D5 | FBX path | Blender exporter / Autodesk SDK | **Blender exporter** (SDK unnecessary + proprietary) |
| D6 | Study-tier sliders in shipped default library | Include flagged / internal-only until re-derived clean | **Internal-only by default**; a slider graduates to the shipped library only when re-authored from build-tier sources. (Blueprint assumes this.) |
| D7 | MVP base | hm08 dev base first (fast, CC0) / wait for our neutral body | **hm08 first** — the engine proves out in Phase 1 while base authoring runs parallel in Phase 2. |
| D8 | Public gallery/server someday | Never / local-only packs / hosted gallery | **Local packs only** for v1 scope; revisit after v1.0. |

*Evidence update (Nov 12 evening): no D-decision has been taken yet, but
D4 now has a landed study behind its recommendation — A3
(fur-craft/a3-geonodes/) built the same groom both ways and ruled for
Geometry-Nodes (strand) authoring on structural grounds, and A8/A13
proved the bake-down to cards/atlas. D4's recommendation stands on
evidence, not preference; the call is still Joe's.*

### 3.2 Rulings already in force (made today, scattered across docs)

| Ruling | Substance | Source |
|---|---|---|
| **Teeth = one universal arcade** (Joe, Nov 12, 12:16 CST) | One arcade pair for everything: uppers ride the skull, lowers ride the jaw object. Diet (canine/omnivore/herbivore) is *morph axes on the shared arcade* (`TeethCanine`/`TeethMolar`/`TeethIncisor`/`TeethWear`), not separate systems. An orc tusk is the lower canine at the axis extreme — mandible-socketed, splay angle a function of jaw width. No bespoke per-species teeth rigs. | preset-orc-bara.md §4; TEETH.md |
| **Species = preset bundle** (our stance in the HF-vs-EF split) | AnthroForge adopts Hero Forge's model: a species is a named bundle of part choices + a slider vector, every element overridable afterwards; mixing is total *within* a body plan, impossible across plans. Eldritch Foundry's opposite model (ancestry = commitment, curated "Half-" blends) is **not** adopted as the primary regime — EF's own rule EF2 ("offer two mixing regimes, and say which is which") leaves a committed-ancestry mode as an undecided extra. | HEROFORGE.md HF1/HF2; APP_BLUEPRINT.md §1.1; ELDRITCH_FOUNDRY.md EF1/EF2 |
| **BrowRidge is retired** | The single BrowRidge slider is replaced by a 7-slider brow vector (BrowProjection / Thickness / Continuity / Shelf / Position / Padding / Scowl), each assigned to its layer (bone / muscle / tissue). Head spec goes 25 → **31 sliders**. All seven animal species take *negative* BrowProjection (−20…−45) — canids/felids have no torus; the orc decomposes to Projection +135 (the old +90 survives only as a legacy macro label). Humanoid-only shim for old files: Projection ≈ 1.5 × BrowRidge; never apply to animals. | brow-study.md §5–§6; applied in species-head-spec.md §3 and preset-orc-bara.md §2 |
| **Study-tier graduation rule** | Data learned from study-tier sources (e.g. Skyrim mod deltas) is internal-only; a slider **graduates** to the shipped library only when re-authored from build-tier sources. Provenance + licence tier are data-model fields enforced at export, not conventions. (This is also D6's recommendation — the underlying study-only status of the learned Skyrim data is already in force regardless of how D6 lands.) | MAKEHUMAN_OMNIVERSAL.md §3; APP_BLUEPRINT.md §13, D6 |
| **Layered construction** (Joe) | Heads/bodies are authored skull → muscle → tissue; sliders deform the stack coherently. Heavy brow = bone, scowl = muscle (corrugator ≈1.6 mm — meaning, not mass), finish = tissue 3–9 mm, which must never fake a torus or erase one. | species-head-spec.md; brow-study.md §4; APP_BLUEPRINT.md §7 |
| **Modularity** (Joe) | Parts are swappable at sockets; rigged (own weights) preferred, rigid bone-attached fallback; deformation learning is per-part so learned parts re-skin across bodies. | species-head-spec.md addendum; APP_BLUEPRINT.md §1.1 |
| **Share codes ship with the creator** | A character is a serialisable vector, so share codes are a v1 feature, not a later add-on (Elden Ring's missing-sharing fiasco is the cautionary tale). | CREATOR_LESSONS.md R2; APP_BLUEPRINT.md §1.1/§3 |
| **No ripping, no purchases** (asset acquisition stance) | Hero Forge / Eldritch Foundry parts are never extracted (proprietary, ToS, same-use-case); both are study-by-observation only — and with no funds available, no STL purchases either. Cheapest legal EF file is $5 à-la-carte; HF STL $7.99 — both declined for now. | HEROFORGE.md §9; ELDRITCH_FOUNDRY.md §6 |
| **Ship gates run on shipped numbers** (Nov 12 evening) | Fold/QA gates are evaluated on the *quantised* .target files that actually ship, never on in-memory float fields. The coupling targets passed in float space at min_dot +0.0006…+0.0018 and the format's 0.1 mm quantisation pushed them over (bigchest 1 flip, gachidebu 3); repairs are done in quantised space with a ≥0.01 margin floor. The app obeys the same lesson from the other side: it builds from float64 canonical packs because the rounded files flip the belly's thinnest gate face. | hyper/HYPER_RANGES.md; bara-proof/COUPLING_VALIDATION.md; anthroforge-app/INTEGRATION.md |
| **Hyper is a segmented regime** (Nov 12 evening) | Past +1, sliders are piecewise: separately authored segments with their own validity envelopes, not extrapolation (naive belly 2× = 75 flipped faces; solved segment = 0). Corrective keys are **total fields** — a key replaces the base corrective at its value, stacking is unrepresentable. Contact is re-solved per segment, and the contact solve, not the fold solve, sets the ceiling. Length past range goes to bone scale, which cannot fold. | hyper/HYPER_RANGES.md (rules H1–H8) |
| **Fur authoring route: Geometry Nodes** (Nov 12 evening, study verdict) | Grooms are authored in Geometry Nodes; the particle groom is the legacy reference. Blender's direction of travel, one deterministic script vs scattered UI state, attachment survives re-posing. Cards/shells remain *outputs* baked from the strand groom (A8/A13), never the authoring source. | fur-craft/a3-geonodes/GEONODES_FUR.md §6 |

---

## 4. Glossary

- **Omniversal slider** — a slider defined once, semantically, that works
  across every base mesh (ours, MakeHuman's, Skyrim's). One vocabulary;
  "belly", "muzzle length", "masseter" mean the same shape change anywhere.
- **Canonical record** — the base-independent definition of a slider: id,
  label, group, semantics in words, region (landmarks + mask rule), range
  with endpoint anchor in metres, symmetry, provenance/licence. Identity of
  a slider = semantics + region + anchor, never a file.
- **Instance** — one base mesh's generated realisation of a canonical
  slider: the actual per-vertex delta file for that base (.target, .npz),
  cached, carrying its own QA numbers (residual, fold count, safe_max).
- **Fit residual** — the measured surface error after transferring a
  deformation onto a foreign-topology base (mean/median/p95/max, in cm).
  How honest a transferred slider is; dead zones (flank, genital patch)
  are masked and named, never silently transferred.
- **Tier (licence tier)** — every asset/slider carries one: **build** (CC0 /
  CC BY / CC BY-SA — usable in shipped output, attribution kept where
  required), **study** (learned/measured for internal design knowledge;
  never shipped verbatim — e.g. Skyrim mod deltas), **reference** (look,
  measure proportions, do not derive files — e.g. NC/ND/NoAI items, Hero
  Forge geometry).
- **Body plan** — the structural partition a part belongs to (biped,
  digitigrade, quadruped/taur…). Mixing is free *inside* a plan and
  impossible *across* plans; parts carry plan-fit metadata (HF2).
- **Socket** — a named attachment point on the shared skeleton where a
  swappable part mounts (ear, tail, jaw/teeth arcade, genital module…).
  Rigged parts bring their own skin weights to the skeleton; rigid parts
  bone-attach at the socket.
- **Share code** — the serialised character record (base + slider vector +
  parts manifest + materials) as a portable string/file. Characters are
  vectors, so sharing is nearly free — and re-editing a shared character
  is always possible (R2, R7).
- **Learned delta** — a per-vertex deformation field extracted from a real
  model by the learn-then-delete pipeline (exact for same-topology pairs,
  fit-with-residual for foreign topology).
- **Preset** — a named point in slider space (+ part choices): a species,
  a character, a sub-style. Never a separate mode; always still editable.
- **Lineage** — (EF term, adopted as a design option) a named variant set
  *inside* a species — variety without new base geometry; maps to our
  species presets × style axis.
- **safe_max** — the slider value beyond which the deformation starts
  folding/breaking on that base; instances ship it, exports flag
  exceedances instead of silently breaking (conformance flag, R4).
- **hm08** — MakeHuman's base mesh (via MPFB2), CC0; the MVP dev base
  (D7) and the first-proof target base.
- **MCP connector** — the app's Model Context Protocol surface (28 tools
  in the blueprint) exposing the full creator to AI agents; GUI and MCP
  call the same Core Service.

---

## 5. Conflicts & stale spots — flagged, not smoothed

1. **Slider-count labels lag the reconciliation.** The brow verdicts were
   applied to the *content* of both head specs, but preset-orc-bara.md §2
   is still titled "HEAD — orc on the 25-slider framework" and its closing
   line still calls species-head-spec.md "the 25-slider framework". The
   framework is 31 sliders. Labels only — the values are the reconciled
   ones.
2. **APP_BLUEPRINT hasn't absorbed the brow study.** §16.3 still lists
   "Brow study results may add head sliders (BrowContinuity/BrowShelf)"
   as an open question, and §7.4 reserves brow sliders as `provisional`.
   Resolved downstream: the study landed, added 7 brow sliders (net
   25 → 31), and both specs were reconciled. The blueprint text is stale
   on this point.
3. **Orc honesty box cites a retired slider.** preset-orc-bara.md §6
   still names "BrowRidge 0.75" among its weakest-sourced numbers.
   BrowRidge no longer exists as a slider; the underlying estimate lives
   on as the decomposed brow vector (Projection +135 etc., all [E]).
   The honesty concern stands; the name is residue.
4. **Head line status (supersedes the old v2 item).** v2 never met its
   spec and is superseded. v3 clears the construction/proportion bar
   with disclosed exceptions (8/14 gates in ±6%). v4 holds v3's gates,
   splits the teeth into two arcades and resolves its one apparent
   regression (MuzzleWidth) as a ruler artefact — the gate's ruler
   samples TissueHead only while the widest surface at that station is
   jaw, so the appendix recommends redefining the gate as the
   surface-true section over the merged surface (under it, v3 and v4
   are identical). Still genuinely open on the head: the **lip-line
   loop cage** (B12 F-M7 — without it there are no lip sliders, "only
   crease smears"), the **Interorbital spec ruling** (0.19 anchor vs
   0.1122 physical seating in use), and v4 has **no renders** — all its
   verification is numeric, so the visual-acceptance gate that killed
   v1 has not been run on v4 either.
5. **D7 vs "our head is primary" — apparent, scoped.** APP_BLUEPRINT
   §16.1 says our own head is the primary and MakeHuman is a partner,
   while D7 recommends hm08 first. Not a contradiction once scoped:
   D7 governs the *body* MVP in Phase 1; the head line runs on our own
   base in parallel. Flagged because the docs don't say this in one place.
6. **Two mixing regimes vs one adopted stance.** §3.2 records the bundle
   regime as adopted (HF1). ELDRITCH_FOUNDRY EF2 recommends offering
   *both* regimes and labelling them. Whether AnthroForge also ships a
   committed-ancestry mode is genuinely undecided — it is not D-listed,
   and no doc resolves it.
7. **Seven HIMBO recipe names resolve to zero — Joe's call.** The neck
   fix's new loud warning exposed seven more names that silently
   resolve to zero against the Vanilla OSD: BodyMass, PecsLower,
   ArmsDeltsShape, BubbleButt, TorsoShoulderInc, TorsoMassSmooth,
   BellySmooth. Every published bara number was measured with them at
   zero, so they are part of the as-validated composition; several have
   plausible-but-unproven alternates (e.g. PecsLower → PecsLowerSide).
   They were deliberately *not* "fixed" inside the neck change —
   changing any of them re-opens the validated numbers. Listed in
   bara-proof/FIX_NECK_FIELD.md as an explicit decision for Joe.
8. **Sen is a proof-of-composition, not a character yet.** The composed
   GLBs are unrigged static bakes (no skin, morphs or textures), the
   fur cards sit at ≈⅓ of A5's placement budget, and the app presets
   mislabel the bases (they say af_body_neutral_v1 / af_head_neutral_v2;
   the actual build is hm08 + base-head-v3). Also: anthroforge-app/
   INTEGRATION.md still says SEN_BUILD.md "has not landed" — it has,
   stages 1 + 2; INTEGRATION.md is stale on that one point.

---

## 6. Where to start — reading orders

**A builder agent** (you're about to write code):
1. This handbook (§1, §3, §5).
2. APP_BLUEPRINT.md — §2 architecture, §3 data model, §15 roadmap, §16
   decisions/risks.
3. MAKEHUMAN_OMNIVERSAL.md §6 (canonical format) + §8 (first proof).
4. slider-lab/ code + SLIDER_ENGINEERING.md.
5. species-head-spec.md §3 + brow-study.md §5 for the head slider set.
6. anthroforge-app/INTEGRATION.md — what the app actually builds today,
   its canonical-pack rule, and the 5-step frontend spec.

**A designer** (you're shaping characters/presets):
1. CREATOR_LESSONS.md (the 12 rules) — then HEROFORGE.md + ELDRITCH_FOUNDRY.md
   rule lists (HF1–HF10, EF1–EF10).
2. species-head-spec.md (species vectors, style axis).
3. brow-study.md §0 verdicts + §5 slider design.
4. preset-orc-bara.md as the worked example of a full preset.

**Joe** (decisions + state of play):
1. §3.1 above — the eight calls (D1–D8); the build order locks when
   they're answered.
2. APP_BLUEPRINT.md §1 (what the app is) + §15 (roadmap/MVP).
3. brow-study.md §0 — the verdicts in five bullets.
4. Status table §2 for anything else. Newer calls waiting on you, in
   the order they unblock work: **Vercel team re-auth** (Mini App
   hosting — §2 adjacent table), the **seven zero-resolving HIMBO
   names** (§5.7), and the **Interorbital spec ruling** (§5.4).

---

*Handbook compiled from the doc set as it stood on Nov 12, 2026;
status sections refreshed the same evening against the files on disk.
Where a summary number matters, the cited source doc carries the full
measurement — re-check it before quoting the handbook second-hand.*
