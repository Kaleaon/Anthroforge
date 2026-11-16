# Creator Lessons — Teardowns of the Deepest Commercial Character Creators, and Rules for AnthroForge

*Design research, Nov 12, 2026. Commissioned by Joe after MojoPlays' "10 Games With The DEEPEST Character Creation" (https://www.youtube.com/watch?v=-sS9AmfHHO0). Method: web teardown research — official blogs/newsrooms, wikis, creator deep-dives, community sharing infrastructure. Every factual claim below is sourced; URLs at the end.*

---

## 0. The list itself — verified

The WatchMojo/MojoPlays article version of the video confirms the full ten (WatchMojo, "10 Games With The DEEPEST Character Creation", published 2023-10-20):

| # | Game | Year |
|---|------|------|
| 1 | Baldur's Gate 3 | 2023 |
| 2 | Starfield | 2023 |
| 3 | WWE 2K23 | 2023 |
| 4 | Saints Row | 2022 |
| 5 | Dragon Age: Inquisition | 2014 |
| 6 | Monster Hunter: World | 2018 |
| 7 | Street Fighter 6 | 2023 |
| 8 | Soulcalibur VI | 2018 |
| 9 | Cyberpunk 2077 | 2020 |
| 10 | Grand Theft Auto V (Online) | 2013 |

This doc tears down all ten, plus the two standing benchmarks the brief asked for: **The Sims 4** (2014) and **Elden Ring** (2022). Twelve systems total.

---

## 1. Master comparison

| Game | Core architecture | Face model | Body model | Sharing | Re-edit after start |
|---|---|---|---|---|---|
| **Baldur's Gate 3** | Curated presets only | Scanned preset heads (~150 total across races, from ~40 scanned models); **zero sliders** | 4 fixed body types per race/gender silhouette | None built in | Magic Mirror (added Patch 3), free |
| **Starfield** | Preset start + slider finish | 40 Biometric ID presets, then per-feature sliders incl. numbered "shape blend" sub-sliders | **Circular 3-pole blend grid** (Muscular / Thin / Heavy, 100+ positions) | None (players share slider screenshots + save files) | Genetics facility, fee |
| **WWE 2K23** | Parts suite under a budget | Preset face textures + morph sliders + photo face upload | Presets + morph sliders; height/weight with weight classes | **Community Creations, cross-platform** (new in 2K23) | Free, any time |
| **Saints Row (2022)** | Full sliders, no gender binary | Deep slider set, **asymmetry toggle** (per-side sliders on brow/ears/eyes) | "Figure" pole slider + **triangle slider** (slim–muscular–fat) + chest/groin sliders | **Share codes (cross-platform)** + web hub with voting | Free via Style app, any time |
| **Dragon Age: Inquisition** | Slider face, fixed body | Extensive sliders, several on **2-axis pads** (position features in X/Y) | None — body fixed by race/gender | None (slider-screenshot communities) | Mirror of Transformation — **post-launch free DLC**, because players demanded it |
| **Monster Hunter: World** | Preset face + light sliders | Preset faces, position/size tweaks, 2 makeup layers, expression presets | Fixed silhouettes | None (sequel *Wilds* added design codes) | **Paid edit vouchers** after one free one; Palico look permanent |
| **Street Fighter 6** | Sliders + 2-face blend | Preset faces blended 0–100 (Face 1 ↔ Face 2), then dozens of 0–100 sliders | Body triangles for composition; per-muscle-group sliders; proportions change **hitboxes** | **Recipe codes**, up to 100 saved locally | Body Shop, small in-game fee |
| **Soulcalibur VI** | Slot-based parts + free-attach accessories | 16 base "races" (incl. animal-featured, lizardman, automaton) + sliders | Sliders + height classes | Download others' creations in-game | Free |
| **Cyberpunk 2077** | Numbered presets only | Every feature = numbered variant list (Nose 01–NN…); **no proportion sliders at all** | 2 fixed frames; no height/weight | None (recipe lists shared as text) | At launch: **none**. Later updates: mirror (minor) + Ripperdoc (full) |
| **GTA Online** | Genetic blend | Pick mother + father presets; **Resemblance slider** blends their faces; grandparents underneath | Features then tuned on 2-/4-axis scatter graphs | None (crews/social only) | "Change Appearance", GTA$100,000 |
| **The Sims 4** | **Direct manipulation** (grab & pull) | ~97 hidden modifiers driven by dragging on the mesh; Detail Edit Mode for fine work | 2 true sliders (fitness, fatness) + drag sculpting | **The Gallery** — integrated, one-click, likes/comments/download counts | Free, any time (full-edit via cheat) |
| **Elden Ring** | Numeric slider laboratory | ~100 sliders, values 0–255, incl. "face template" meta-sliders (Bone Structure, Form Emphasis, Apparent Age) | Body Type A/B + a handful of "Alter Body" sliders | **None built in** — community built slider-transcription websites instead | Clouded Mirror Stand in Roundtable Hold, free, unlimited |

---

## 2. Per-game teardowns

### 2.1 Street Fighter 6 (Capcom, 2023) — the extremes benchmark

- **Architecture.** Two-layer face system: pick two preset faces and set a **blend value 0 (all Face 1) to 100 (all Face 2)**, then refine with dozens of 0–100 sliders across Hair, Eye Shape, Iris, Eyebrows, Nose, Mouth, Ears, Facial Hair and more — down to forehead protrusion, cheek bulge, jaw length (Capcom's own TGS 2022 deep-dive; PC Gamer). Body: "Height & Proportions", Upper Body, Lower Body categories; **body triangles** set composition (Muscle Definition is a continuous field between Shredded / Built / Soft), plus **individual muscle-group sliders** — lats, shoulders, traps can be driven independently.
- **Extremes — appearance is gameplay.** Proportions are not cosmetic: arm span and leg length change attack reach, and body size changes the hurtbox. Capcom's containment strategy is **quarantine, not clamping**: monstrous avatars are welcome in World Tour and Battle Hub avatar battles, but created avatars are excluded from the competitive Fighting Ground because the proportions can't be balanced. Gear in World Tour also carries stats (punch/kick strength, HP, defence), so clothing is a build choice, not just a look.
- **Sharing.** The **Recipe** system is the gold standard for codes: a Recipe Password encodes the full body+face settings; anyone can enter the code at a Body Shop, preview, adopt or edit-and-resave. Players save up to **100 recipes locally**; upload slots are capped (3 free, more purchasable) — the *only* friction point, and it's on the upload side, not the download side. A whole subreddit (r/SF6Avatars) exists to trade codes.
- **Lesson shape.** Blend-between-two-presets as the *front door*, sliders as the *workshop*, codes as the *distribution*, mode-quarantine as the *safety valve*.

### 2.2 WWE 2K23 (Visual Concepts, 2023) — the parts suite benchmark

- **Architecture.** Create-A-Superstar is one room in a **Creation Suite**: Superstars, arenas, entrances, move-sets, championships. The body itself is assembled from parts — 2K23 added **600 new parts** — under a visible **complexity budget**: the UI tracks "parts points" (128-point pool) and a layer counter, so a creation can be rich but not unbounded. 100 created-superstar slots, 1,000 custom images.
- **Parts & layering.** Clothing, hair, facial parts, logos and designs stack as layers; **custom image upload** (web tool) and **face-photo capture** let players import real faces and art — the single most-used "cheat" for likeness in any creator here. Face textures ship as 17+ presets with different skin qualities.
- **Sharing.** **Community Creations went cross-platform in 2K23** — upload a Superstar (or arena, or entrance) and anyone on any platform downloads it. This is widely credited as the suite's biggest 2K23 upgrade; the community treats the in-game browser as the game's real content library.
- **Breakage & governance.** The point budget is the governance: instead of policing what players build, the suite prices it. Parts that would blow the budget simply can't all coexist.
- **Lesson shape.** *Parts libraries + a complexity budget + cross-platform sharing = a creator that becomes a platform.*

### 2.3 Baldur's Gate 3 (Larian, 2023) — the presets-are-art-direction argument

- **Architecture.** Deliberately **no face sliders**. Larian scanned ~40 real models and derived **~150 stock heads**; each race/body-type gets a small curated set of heads, combined with discrete options for hair, eyes (incl. heterochromia), tattoos, scars, piercings, vitiligo, makeup, and 4 body types. Larian's stated reasons: slider faces converge — players produce similar-looking faces — and preset heads preserve facial-animation fidelity and a consistent art standard (80 Level interview, via Larian forums).
- **What players actually did.** 93% chose a custom character over an Origin; players spent a combined **88 years in the creator on launch weekend alone**, 10% of characters took over an hour — in a creator with *no sliders* (Larian Community Update #23). Long-run total later reported: **8,196 combined years**. And the mod scene immediately built what Larian withheld: extra-head and slider-adjacent mods are among the game's most downloaded, and players complain loudest about the *scarcity* of heads per race ("only ~8 heads", ethnicity coverage of one face per group).
- **Trade-off, honestly.** BG3 characters look better on average than any slider game's — and the ceiling on self-expression is real and was the #1 creator complaint. Presets raise the floor and lower the ceiling.
- **Lesson shape.** *Curation is a feature; scarcity is the bug. The winning move is presets AND sliders — presets as starting points inside the slider space, not as a replacement for it.*

### 2.4 Starfield (Bethesda, 2023) — the triangle, and preset-first flow

- **Architecture.** Five tabs: Biometric ID → Body → Face → Background → Traits. You start from one of **40 Biometric ID presets** (framed diegetically as employee records), then customise. Face features combine pick-lists with sliders, including **numbered "shape blend" sub-sliders** under features (community preset-sharing notes warn you must match every sub-slider to reproduce a face — an early warning about recipe fidelity).
- **The body triangle.** Body shape is set on a **circular grid blending three poles — Muscular, Thin, Heavy — with 100+ distinct positions**, plus body type, walk style, skin tone. One 2D control replaces three interacting 1D sliders, and every point in the triangle is a valid, non-monstrous body: the space is *convex*, so there are no invalid corners.
- **Identity beyond looks.** Backgrounds (20) grant starting skills and dialogue; up to 3 Traits, each a paired advantage+disadvantage. The creator sells *who* the character is, not only how they look.
- **Sharing.** None built in — the community shares via Nexus save files and slider screenshots, i.e. friction everywhere SF6 has none.
- **Lesson shape.** *A blend-space widget (triangle/2-axis pad) is the best UI ever shipped for multi-pole morphs — and preset-first flow gets casual users to a good face fast while keeping the workshop open.*

### 2.5 Cyberpunk 2077 (CD Projekt Red, 2020) — the cautionary tale

- **Architecture.** Every facial feature is a **numbered preset list** (Eyes 01…, Nose 01…, Jaw 01…); there are **no proportion sliders anywhere**, and the body is one of two fixed frames with **no height, weight or build options at all**. The combinatorics are large on paper and shallow in practice — forum verdict at launch: "finished in less than 10 minutes… you can't even change the body type, height, weight."
- **The famous exception.** Genital customisation (type + size options) shipped while body sliders didn't — the mismatch became the emblem of misprioritised depth: novelty discrete options over structural proportion control.
- **Post-launch repair.** At launch the look was **permanent** — a heavily criticised lock-in. CDPR patched in mirror edits (minor) and then full Ripperdoc overhauls (everything but voice and body frame). The repair direction is the lesson: players treat appearance as *revisable*, and a creator that locks it reads as hostile.
- **No sharing.** No codes; "recipes" circulate as typed lists of preset numbers.
- **Lesson shape.** *Discrete variant lists cannot substitute for continuous proportion control; and novelty options don't compensate for missing core sliders. Also: creator lighting lies — CP2077's neon creator lighting made characters look different in daylight; preview environment is part of the system.*

### 2.6 Saints Row (Volition, 2022) — asymmetry, and the creator as a product

- **Architecture.** No gender binary at all: a **"figure" pole slider** (wide chest/shoulders ↔ hips/slim waist), a **triangle slider (slim–muscular–fat)**, independent chest and groin sliders. Face: 100+ head presets as starting points, then deep sliders (brow depth, ear height, jaw width, nostril size…).
- **Asymmetry, with honest limits.** A toggle unlinks the face's sides; per-side sliders exist for forehead, brow, ears, eyes — **but not for nose, chin, cheeks, mouth or jaw** (GameSkinny's hands-on). Partial asymmetry confused reviewers; the feature is right, the coverage was uneven.
- **Parts as identity.** Prosthetics are first-class cosmetic parts: 18 arm variants, 21 leg variants (left/right/both). Vitiligo, scars, tan lines, veins as skin-level options.
- **Distribution masterstroke.** **Boss Factory**: the full creator released **free, standalone, before the game**, with cross-platform **share codes** and a web hub with voting. The game underperformed; the creator is still the part everyone praises. Creations could be re-edited any time from the in-game Style app.
- **Lesson shape.** *Ship the creator as its own artefact; one continuous axis beats a binary; asymmetry is a differentiator but only if it's complete.*

### 2.7 Dragon Age: Inquisition (BioWare, 2014) — 2-axis pads and the lighting lesson

- **Architecture.** A serious slider face lab: dozens of sliders, with feature *positions* set on **2-axis pads** (ear position: down lowers, right pulls in — two dimensions in one gesture). Eye colour via colour wheel, widely praised over swatch lists.
- **The body gap.** Zero body customisation — body fixed entirely by race/gender — while the face got a laboratory. Reviewers flagged the asymmetry of investment a decade ago.
- **Creator-environment failure.** The creator's green-tinted lighting was notorious: faces looked wrong in-game, players remade characters repeatedly. BioWare answered post-launch with the **Mirror of Transformation** (Black Emporium, free DLC) — full re-editing mid-game, added because the demand was undeniable.
- **Sharing.** None; the community ran slider-screenshot archives (the r/InquisitionSliders pattern) — same pressure valve as Elden Ring, a generation earlier.
- **Lesson shape.** *2-axis pads are the right control for position parameters; never ship a creator whose lighting isn't the product's real lighting; expect — and pre-build — the re-edit mirror.*

### 2.8 Monster Hunter: World (Capcom, 2018) — fashion is the endgame; vouchers are the warning

- **Architecture.** Preset-face-first: choose a face, then adjust feature sizes/positions with light sliders; two independent makeup/face-paint layers; expression presets (the face your hunter wears in cutscenes is itself a choice). Then you build a **second character**: the Palico, with fur pattern/length, ears (12 presets), tail (7), eyes, voice.
- **The real customisation system is armour.** Layered Armour decouples *look* from *stats*: any forged set's appearance can be worn over your actual gear. "Fashion hunting" became the community's endgame loop — proof that a parts library with mix-and-match beats raw body sliders for long-term engagement.
- **The warning.** Re-editing your hunter costs **Character Edit Vouchers** — one free, then paid DLC. The Palico's look is **permanent**. Both decisions are still resented years later; the sequel (*Wilds*, 2025) added **character design codes** and 36 saved design slots — Capcom conceding both points.
- **Lesson shape.** *Appearance-over-stats layering is a retention engine; charging for re-edits is a reputation tax.*

### 2.9 Soulcalibur VI (Bandai Namco, 2018) — free-attach parts and their governance cost

- **Architecture.** Slot-based equipment (head, torso, arms, legs…) over 16 base "races" — including the anthro-relevant ones: Outcast (animal ears/features), Lizardman, plus winged Lost Souls, Automaton, Revenant, Colossus. Body via sliders + height.
- **The creative superweapon: free-attach accessories.** A small number of special accessory slots can be attached **anywhere on the body**, each with position, rotation and scale controls, plus sticker decals with position sliders. This one feature is why SC creations can approximate almost any character in fiction — parts become *props*, not just equipment.
- **The governance bill.** Free-attach was abused to build hitbox-obscuring blobs and worse; creations were legal in ranked play, and Namco ended up patching **part-combination restrictions** (specific parts disabled together) rather than removing the system (see the v2.30 update notes). Freedom shipped first, conflict rules shipped reactively.
- **Lesson shape.** *Free-attach with transform controls is the highest-leverage parts feature there is — and it must ship with exclusion/conflict metadata from day one, not patched in after the first scandal.*

### 2.10 GTA Online (Rockstar, 2013) — the two-pole genetic blend

- **Architecture.** No sculpting at all, originally: pick **grandparents** (14 options per gender per side), which generate parents; pick **mother and father** (21 generic models each + special guests: Misty, Claude, John Marston, Niko Bellic); your face is their blend, steered by two independent sliders — **Resemblance** (whose structure) and **Skin Tone** (whose complexion). Features are then nudged on **2- or 4-axis scatter graphs**.
- **Why it works.** A blend between two *real, art-directed faces* can never leave face-space: every point on the slider is plausible. Players report the heritage choice matters more than all feature sliders combined, and that *contrasting* parents (strong jaw × soft features) produce the most interesting faces — blending needs **diverse poles**, not similar ones.
- **Limits.** The ceiling is the convex hull of the preset pool: you cannot make a face unlike any parent. And re-editing costs GTA$100,000.
- **Lesson shape.** *Pole-blending is the safest morph UI ever shipped — variety comes from pole diversity. (AnthroForge's learned-morph space is this, generalised: species presets are the poles.)*

### 2.11 The Sims 4 (Maxis, 2014) — direct manipulation and the Gallery

- **Architecture.** CAS **deleted the slider panel**. You grab the Sim: pull cheeks out, drag a nose sideways, push a waist in. Underneath sit roughly **97 modifiers** (18 body, 35 face, 44 detail) — plus, tellingly, exactly **two surviving true sliders**: fitness and fatness, the two parameters players think of as quantities rather than shapes. Double-click a feature to enter **Detail Edit Mode** for the fine handles. "Play with Genetics" blends two Sims into a child — the GTA blend idea as a family feature.
- **What it proves.** Nobody misses the numbers. Direct manipulation over hidden-but-real parameters gives both tactility and reproducibility (a Sim is still just a parameter vector — the Gallery proves it). Modders later bolted numeric sliders and height sliders on top, i.e. the demand curve runs: manipulation first, numeric access second, *extended ranges* third.
- **The Gallery.** Integrated sharing done right: one click up, one click down, with download counts, favourites, comments, hashtag search, and Maxis-curated picks. The Gallery is a decade-old, still-active creative economy — and it made CAS a social space instead of a menu.
- **Lesson shape.** *The mesh is the interface. Keep the parameter vector underneath — that's what gets shared, learned and re-targeted.*

### 2.12 Elden Ring (FromSoftware, 2022) — the slider laboratory and the sharing vacuum

- **Architecture.** The deepest pure-slider face lab in a mainstream game: ~100 sliders with **0–255 numeric values**, organised as meta-structure first (Adjust Face Template: Bone Structure, Form Emphasis, Apparent Age, Facial Aesthetic), then Facial Balance *ratios* (Nose/Forehead Ratio, Vertical/Horizontal Face Ratio, Face Protrusion, Feature Slant), then per-feature detail. Body is deliberately minimal: Type A/B + a few "Alter Body" sliders. Re-editing is free and unlimited at the Roundtable Hold mirror; up to 10 faces can be saved as Favorites.
- **The vacuum.** There is **no code, export or sharing feature of any kind**. The community's response: entire websites (eldensliders.com, eldenblingsliders.com) whose only job is transcribing slider values next to screenshots so strangers can re-type ~100 numbers by hand. Whole subreddits run recreation-request threads. The demand for sharing was so strong that players built the missing infrastructure themselves, badly, for years — and third parties now sell "photo → sliders" and auto-import tools on top.
- **Lesson shape.** *If your character is a serialisable parameter vector, sharing is inevitable — the only choice is whether you ship it or your users improvise it.*

---

## 3. Cross-cutting patterns

1. **Every deep creator is a hybrid.** Pure sliders (Elden Ring) produce laboratories nobody shares from; pure presets (BG3, Cyberpunk) produce beautiful floors and resented ceilings. The systems players love layer all three: presets → blends → sliders (SF6, Starfield, Saints Row).
2. **Blend spaces beat slider stacks for coupled parameters.** Body composition is one triangle in three separate games (Starfield, Saints Row, SF6). Face identity is one 2-pole blend in GTA and SF6. Coupled quantities want 2D controls with convex, always-valid interiors.
3. **Extremes are a feature with a blast radius.** SF6's monsters are beloved *and* quarantined from competition; SCVI's free-attach parts are beloved *and* patched with conflict rules; WWE prices complexity instead of banning it. Nobody successful solved extremes by shrinking the ranges.
4. **Re-editing is non-negotiable.** Four of these games shipped without adequate re-editing (CP2077, DAI, MHW, GTA's paid edit) and all four were forced to add or discount it. The mirror is part of the creator.
5. **Sharing is the multiplier.** The creators with codes/galleries (SF6, WWE, Saints Row, Sims 4) became platforms with content economies. The ones without (Elden Ring, DAI, Starfield) sprouted screenshot-transcription cottage industries — demand leaking out of the product.
6. **Preview honesty matters.** DAI's green void and CP2077's neon booth both generated "my character looks wrong in-game" remakes. Lighting/environment in the creator is a correctness feature, not set dressing.

---

## 4. Rules for AnthroForge

Each rule: the do/avoid, the game(s) that prove it, and the AnthroForge system it lands on.

**R1 — Presets are points in slider space, never a separate mode.**
DO: store every species preset, every Titan family member, every bara/orc build as a named vector in the same omniversal slider space the user edits. A preset is "apply vector, then keep editing."
AVOID: BG3's wall between preset heads and the rest of the system — its scarcity complaints and mod-scene workaround are what a wall costs.
*Proven by:* BG3 (negative), SF6 recipes + Starfield Biometric IDs (positive). *Lands on:* species presets + style axis, Titan family presets.

**R2 — Ship the share code with the creator, not after it.**
DO: serialise a character as (base + slider vector + part list + material choices) → short code + file export, importable in one step, from v1.
AVOID: launching into Elden Ring's vacuum — users *will* build eldendensliders-for-AnthroForge out of screenshots if we don't, and we'll have lost the canonical format.
*Proven by:* Elden Ring (negative), SF6 Recipe Passwords, Saints Row share codes, Sims Gallery (positive). *Lands on:* the whole app; omniversal slider vocabulary is what makes codes portable across bases.

**R3 — Coupled proportions get blend spaces, not slider stacks.**
DO: body composition as a triangle (mass ↔ muscle ↔ lean — precisely the axes our Fat Males/HIMBO learned data spans); face identity as pole-blends between species anchors (wolf ↔ fox ↔ cat…) with GTA-style "diverse poles" — the species presets ARE the parents.
AVOID: three+ interacting 1D sliders for one coupled quantity (Starfield face sub-slider stacks are where recipe reproduction goes to die).
*Proven by:* Starfield, Saints Row, SF6 triangles; GTA heritage. *Lands on:* UI for body sliders + species/style axes.

**R4 — Extremes get their own regime: fit re-solve, conflict metadata, quarantine flags.**
DO: let sliders run to bara/orc/monster ranges; at extreme values, (a) clothing/parts re-fit via the learned-deformation solve rather than stretching, (b) parts carry exclusion/conflict metadata (this tusk set × that jaw), (c) exports carry a "conformance" flag (clean / extreme / broken) instead of the app refusing.
AVOID: shipping freedom first and bolting on restrictions after the first disaster (SCVI's patch-history), or pre-emptively shrinking ranges (CP2077's missing body).
*Proven by:* SCVI, SF6's mode-quarantine, CP2077 (negative). *Lands on:* swappable rigged parts, parts-fit pipeline, bara/orc extremes.

**R5 — Budget complexity openly, like WWE's points.**
DO: every swappable part carries a cost (verts, bones influenced, morph count); the UI shows the budget and the total. Heavy parts are allowed — they're *priced*.
AVOID: silent degradation or hard slot counts with no rationale.
*Proven by:* WWE 2K23's 128-point parts pool. *Lands on:* swappable parts system, GLB export validation (extends the v2 export checks).

**R6 — The mesh is the interface; the numbers stay underneath.**
DO: direct manipulation on the head/body (drag a muzzle longer, pull a belly out) driving the same omniversal sliders, with Detail-mode handles for fine work, numeric readouts for the laboratory users, and a link/unlink toggle for asymmetry (species markings, scars, heterochromia — and asymmetric morphs where the data supports them).
AVOID: Sims-style manipulation with no numeric access (modders had to bolt it on), and Saints Row's *partial* asymmetry (unlinked sides must work for every bilateral slider, or the feature reads as broken).
*Proven by:* Sims 4, Saints Row. *Lands on:* editor UX over learned-morph sliders; head construction regions.

**R7 — Re-editing is free, forever, everywhere.**
DO: any saved character reopens in the full editor at any time; nothing about a build is permanent.
AVOID: MHW's paid vouchers and permanent Palico — the single most resented policy in this entire survey.
*Proven by:* MHW (negative); CP2077/DAI's forced post-launch mirrors (corrective). *Lands on:* product policy.

**R8 — Layered appearance over base stats/form.**
DO: clothing and parts fit to the *current* morph state via the deformation solve and can be re-solved when sliders change — appearance is a layer computed over the body, MHW Layered-Armour style, never baked to one body state.
AVOID: fits that only work at the proportions they were authored at — that's the BodySlide outfit-refit problem the Skyrim ecosystem needed a whole tool (Outfit Studio) to survive.
*Proven by:* MHW layered armour; Skyrim BodySlide ecosystem (our own learned data). *Lands on:* parts + clothing fit pipeline.

**R9 — Free-attach props are the highest-leverage part type.**
DO: beyond socketed parts, offer a small set of free-attach slots (horns, extra ears, piercings, teeth ornaments, scars-as-props) with position/rotation/scale, parented to bones — SCVI's accessory system is how players fake a thousand things we haven't modelled. Teeth/tusks from the universal arcade can expose the same transform handles.
AVOID: free-attach without R4's conflict metadata.
*Proven by:* SCVI. *Lands on:* swappable parts, universal teeth arcade (tusk placement), orc preset.

**R10 — Identity is more than geometry.**
DO: the creator surface includes the non-geometry layer from the start — name, species preset, style axis position, materials/markings, and (where a build is a *character*, e.g. the Titan family) authored notes. Starfield's Backgrounds/Traits made creation feel like character-building, not doll-dressing.
AVOID: a creator that can express a face but not a person (CP2077 managed neither well, but the geometry-only focus is the transferable error).
*Proven by:* Starfield. *Lands on:* Titan family presets, character files.

**R11 — Preview in honest light.**
DO: creator viewport uses neutral studio lighting + one "in-world" lighting preset toggle; renders for species-spec QA already use the Poly Haven studio HDRI — keep that discipline in the app itself.
AVOID: a stylised creator void (DAI green, CP2077 neon) — it manufactures remakes and distrust.
*Proven by:* DAI, CP2077 (negative). *Lands on:* AnthroForge viewport.

**R12 — Layered construction stays invisible but load-bearing.**
DO: keep the skull → muscle → tissue stack as the *authoring* model for heads (it's why our morphs will deform plausibly), while the user only ever sees the tissue surface and its sliders. No commercial creator exposes anatomy layers — they expose the *results* (SF6's per-muscle-group sliders are the closest: muscle groups as user-facing units because the underlying model respects them).
AVOID: exposing construction internals as UI, or skipping the muscle layer and getting v1's "wrapped skull" read.
*Proven by:* SF6 muscle-group sliders (positive echo); our own v1 head failure (negative). *Lands on:* layered head construction, orc masseter/temporalis work.

---

## 5. Sources

- WatchMojo — "10 Games With The DEEPEST Character Creation" (list verification): https://www.watchmojo.com/articles/games-with-the-deepest-character-creation
- Capcom News (TGS 2022, SF6 avatar creation categories, muscle definition Shredded/Built/Soft): https://news.capcomusa.com/tag/playstation/page/16
- PC Gamer — "Street Fighter 6 has a character creator, and of course it has muscle sliders": https://www.pcgamer.com/street-fighter-6-has-a-character-creator-and-of-course-it-has-muscle-sliders/
- Push Square — SF6 upload/download avatar recipes (Recipe Passwords, slots): https://www.pushsquare.com/guides/street-fighter-6-how-to-upload-and-download-avatar-recipes
- LineGames — SF6 avatar creation guide (Face 1↔Face 2 blend 0–100, body triangles, 100 recipe saves): https://www.linegames.org/news/e/view-L3N0cmVldC1maWdodGVyLTYtYXZhdGFyLWNyZWF0aW9uLWd1aWRlLw
- 2K Newsroom — WWE 2K23 (cross-platform Community Creations, hundreds of new parts): https://newsroom-uk.2k.com/news/wwe-2k23-featuring-wargames-and-more-is-available-now
- The SmackDown Hotel — WWE 2K23 Create-A-Superstar breakdown (600 new parts, 100 CAW / 1,000 image limits, face textures): https://www.thesmackdownhotel.com/news/wwe2k23/wwe-2k23-create-a-superstar-breakdown-new-and-returning-features
- Larian — Community Update #23 (93% custom, 88 years in creator launch weekend, 10% over an hour): https://forums.larian.com/ubbthreads.php?ubb=showflat&Number=878768
- Larian forums / 80 Level — why BG3 has no face sliders (convergence + scanned heads): https://forums.larian.com/ubbthreads.php?ubb=printthread&Board=87&main=104182&type=thread
- Polygon — BG3 creator (40 scanned models → 150 stock heads): https://www.polygon.com/2020/10/6/21504062/baldurs-gate-3-character-creation-review-preview-early-access/
- GamesHorizon / GamerTweak — Starfield (40 Biometric IDs, circular Muscular/Thin/Heavy grid, backgrounds & traits): https://gameshorizon.com/features/starfield-character-creation/ · https://gamertweak.com/character-creation-starfield/
- OreAte AI resources — Cyberpunk 2077 numbered-preset system & Ripperdoc re-editing: https://resources.oreate.ai/updates/how-the-cyberpunk-2077-character-slider-system-actually-works
- CD Projekt Red forums — CP2077 creator criticism (no body options, permanence): https://forums.cdprojektred.com/index.php?threads/do-you-like-character-creation-system-in-cyberpunk-2077.11081246/page-5
- Press Start / TechRadar / GameSkinny — Saints Row Boss Factory (figure slider, triangle slider, asymmetry coverage, prosthetics counts, share codes): https://press-start.com.au/features/2022/06/10/saints-rows-character-creation-is-as-robust-and-ridiculous-as-wed-hoped/ · https://www.techradar.com/features/weve-fiddled-with-saints-rows-free-character-creator-and-its-a-powerful-tool-for-representation · https://www.gameskinny.com/culture/saints-row-boss-factory-has-the-bells-but-not-all-the-whistles/
- NSider2 review + Black Emporium coverage — DAI (slider depth, creator lighting complaints, Mirror of Transformation): https://www.tapatalk.com/groups/nsider2/viewtopic.php?f=161&t=411191&view=print · https://copyprogramming.com/howto/can-i-change-the-appearance-of-my-character
- MHW character creation guide (preset faces, makeup layers, Palico options, edit vouchers): https://044e8d80-c429-4a1f-820d-9b443c65b389.filesusr.com/ugd/53c654_a47b27f8b19f4572aa6d706ee77ad8e8.pdf?index=true
- Capcom — Monster Hunter Wilds customization (layered armour; sequel's design-code direction): https://www.monsterhunter.com/wilds/en-us/system/cosmetic/
- Soulcalibur Wiki — Create-A-Soul (16 races, part system history): https://soulcalibur.fandom.com/wiki/Create-A-Soul
- SOULCALIBUR VI v2.30 update notes — sticker position sliders, part-combination restrictions, ban policy: https://www.updatemonitor.com/app/544750/news
- GTA Wiki — Character Creator (heritage, resemblance/skin-tone sliders, scatter-graph features, special parents): https://gta.fandom.com/wiki/Character_Creator
- The Sims 4 Player's Guide (EA) — direct manipulation, Detail Edit Mode, Gallery: http://cdn-assets-ts4.pulse.ea.com/Guide/TheSims4_Players_Guide.pdf
- PlayNews — Sims 4 CAS guide (~100 modifiers: 18 body / 35 face / 44 detail; two body sliders): https://www.playnews.gg/en/guides/the-sims-4-complete-create-a-sim-cas-guide-to-building-a-sim
- Elden Sliders (community) — Elden Ring slider transcription culture, 0–255 values, face-template structure: https://eldensliders.com/female-sliders · https://eldensliders.com/character-sliders/ozm7c2m80or22fqh74992yld

*Verification note: list membership verified against WatchMojo's own article (all ten entries). The Sims 4 and Elden Ring are not on the MojoPlays list; they are covered as the brief's standing benchmarks. Numbers quoted from community guides (e.g. WWE's 128-point pool, Sims' ~97 modifiers) are as reported by those sources and marked as such in the table where relevant.*
