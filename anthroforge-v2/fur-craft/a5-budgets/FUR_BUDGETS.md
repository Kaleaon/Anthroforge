# Fur LOD & Performance Budgets — FUR_BUDGETS.md

**Agent A5, fur-craft wave (Nov 12, 2026).** Real-time fur performance engineering for AnthroForge:
the technique ladder (strands → cards → shells → texture-only → impostor), per-platform budgets,
per-zone budgets, an LOD switching spec, and a measured audit of our own fur assets against all of it.

**Labels:** **[M]** measured on our assets in this pass · **[S]** sourced (citation in §9) ·
**[E]** estimate/derived by arithmetic from [M]/[S] values. Nothing in the budget tables is a guess
dressed as a fact: derived numbers show their inputs.

**Subjects measured:** `fur-prototype/` (strand groom + `fur_cards_lod0/1/2.glb` + both card textures)
on the bara wolf body (`stick-figure-avatar/furry/bara_wolf_avatar.glb`: the rigged avatar build of
the groom's subject).

---

## 1. The cost model — what fur actually spends

Fur is never one cost. Four independent budgets, and each technique spends them differently:

| Cost | Unit | What drives it | Fur's trap |
|---|---|---|---|
| Vertex/triangle | tris on screen | geometry count × LOD | shells **multiply** the base mesh (§2) |
| Fill / overdraw | fragment layers per pixel | transparent quad area overlapping the screen | alpha-blended cards shade *every* texel, including fully transparent ones [S] |
| Draw calls | calls/frame | meshes × materials | trivial for fur if cards are one merged mesh (ours are) |
| Memory | VRAM MB + download MB | texture resolution (VRAM is `w×h×4×1.33` with mips, **independent of file compression**) [S]; GLB payload = geometry + embedded textures | our LOD files are texture-dominated (§7) |

**Overdraw factor** used throughout: `O = visible transparent-quad area ÷ visible body projected area`.
O = 1.0 means the fur layer re-shades every body pixel once extra. Blended fur at production density
is the classic mobile frame-killer precisely because O grows linearly with card count while triangle
count stays modest [S].

**Frame context [S]:** mid-tier phone WebGL scenes target ≤ ~250k tris and ≤ ~80 draw calls total,
with fill rate — not triangles — the usual binding constraint; DPR capping is the single biggest
mobile lever. A single hero character in a Telegram webview gets most of that scene budget, but not
all of it, and the webview shares the phone with Telegram itself.

---

## 2. The technique ladder and its scaling laws

| Rung | Representation | Triangle law | Fill law | Where it belongs |
|---|---|---|---|---|
| 0 | **Strand groom** (Blender particles/curves) | strands × segments; our groom converted naively = **0.36M–0.89M tris** [E: 89,100 strands × 4–10 tris] | n/a (offline) | Authoring master only. Never ships. |
| 1 | **Cards** (curved ribbons, baked strand texture) | placements × 8 tris (4-segment card, ours [M]) or × 16 for cross-plane pairs | blended: full quad area rasterised; cutout: ≈ opaque texel fraction | Long/medium fur: ruff, back, coat, tail, ears |
| 2 | **Shells + fins** (Lengyel) | zone tris × shell count — a 9,406-tri model became 129,466 tris at 16 shells [S]; practical interactive cap ≈ **8 shells** [S] | each shell re-rasterises the whole zone → O_zone ≈ shell count at grazing density | Short fur only (belly, body hair, muzzle) where cards can't resolve |
| 3 | **Texture-only** (fur painted into diffuse/normal/roughness + fresnel fuzz) | 0 extra tris | 0 extra fill | Distant LOD, very short fur, low-end fallback |
| 4 | **Impostor** (cross-quads with baked full-body fur render) | 2–12 tris | one quad layer | Beyond texture-only range; SL "Lowest" slot; multi-character crowd views |

Nonuniform-layer research refines rung 2: layer density should follow *projected fur length*
(16/31/61 layers in the paper's tiers), i.e. shells are spent near silhouettes, not uniformly [S].
We adopt the cheap version: shells only on short-fur zones, fins/cards only at silhouette zones.

**Alpha mode is a budget decision [S]:** alpha-*blend* = softest, unsorted, full-quad fill;
alpha-*cutout* (threshold ~0.4–0.5, + alpha-to-coverage where available) writes depth, sorts
correctly, and discards transparent texels early — strictly preferred wherever the texture has a
real opaque core. Our current textures fail that precondition (§7), which is a bake problem,
not a reason to keep blending.

---

## 3. Platform budgets

### 3a. Desktop GLB (AnthroForge app, Babylon; showcase renders)

External anchors [S]: desktop hero characters 20k–50k tris (games) up to ~150k for a purpose-built
hero; VRChat PC ranks ≈ 32k tris / 4 materials (Excellent), ~70k / 8 (Good).

| Item | Budget | Notes |
|---|---|---|
| Whole character incl. fur | ≤ 150k tris | our wolf body alone is 128.5k [M] — headroom is thin, see §7 |
| Fur, LOD0 | ≤ 48k tris | cards + cross-planes; §5 zone split |
| Fur textures VRAM | ≤ 16 MB | = e.g. 2× 2048² RGBA+mips, or 4× 1024² + atlases |
| Fur draw calls | ≤ 3 | one per technique (cards / shells / impostor) |
| Shells | ≤ 8 layers, short zones only | [S] |

### 3b. WebGL / mobile — Telegram Mini App (phone webview, Babylon)

The binding platform. One hero character, framed large (screen-height fraction ≈ 0.7–0.95), on
mid-tier phone GPUs, inside Telegram's webview. The page already renders at half device resolution
(`setHardwareScalingLevel(dpr / 2)`) [M] — keep that; it is worth more than any fur optimisation.

| Item | Budget (high tier) | Budget (low tier / old phones) |
|---|---|---|
| Whole character incl. fur | ≤ 60k tris on screen | ≤ 25k tris |
| Fur LOD0 | ≤ 24k tris | LOD1 only: ≤ 12k |
| Blended overdraw O | ≤ 2.0 (cutout core mandatory, §6) | ≤ 1.0, shells off |
| Fur textures VRAM | ≤ 4 MB (KTX2/Basis required; raw RGBA 512×1024 pair = 5.6 MB [M] already busts this) | ≤ 2 MB |
| Character payload (body+fur+textures, first load) | ≤ 3 MB | ≤ 1.5 MB, progressive |
| Fur draw calls | 1 (cards merged, one material) | 1 |

Anchors [S]: scene totals ≤ 100–250k tris and ≤ 80 draw calls on mobile WebGL; 3D payload before
first interaction < 3–5 MB; hero characters on mobile games 5k–15k tris *in multi-character scenes* —
our single-hero framing justifies the higher 60k, and only because DPR is halved.

### 3c. Second Life (Bento export profile)

SL doesn't take our LOD chain; it imposes its own [S]:

- **4 LOD slots** (High / Medium / Low / Lowest), swap distances driven by object size.
- **Halving rule:** each lower LOD may carry ~half the triangles of the one above with no download-
  weight penalty; a lazy/auto-decimated Lowest is the classic LI blow-up.
- Rule of thumb ≈ **1,000 tris ≈ 1 LI** at High for ordinary objects; download weight is computed
  across all four LODs, and for small items the Lowest dominates (~90%). Worn attachments pay no LI
  but still cost every nearby viewer the render time — treat the LI-shaped budget as a render budget.
- ≤ **8 material faces** per mesh; ~**21,800 tris per face** before the uploader splits the mesh.

| Fur attachment | High | Medium | Low | Lowest |
|---|---|---|---|---|
| Tris budget | ≤ 20k | ≤ 10k | ≤ 5k | ≤ 500, **hand-authored** (impostor-grade cross-quads or a slim shell of the silhouette) |
| Technique | cards | cards (½ placements) | texture-only + silhouette cards | impostor |

A full-pelt SL attachment at 20k High is realistic; shells are effectively unusable in SL
(they'd have to be baked as separate stacked meshes — 8 shells × body tris at High slot pricing).

---

## 4. Budgets by body zone

Zone shares derive from the prototype groom's parent distribution [M] (coat 36%, back 22%,
belly 18%, ruff 15%, bodyhair 8% of 15,500 parents), re-weighted for technique: belly and bodyhair
leave the card system entirely (below card scale [M, prototype §5]), and their budget moves to
shells (desktop/WebGL) or texture (SL/mobile-low).

**Card placements & triangles, LOD0** (8 tris/card; ×2 where cross-planed):

| Zone | Fur length (ours [M]) | Technique | Desktop 48k | WebGL 24k | Notes |
|---|---|---|---|---|---|
| Ruff / mane / cheeks | 170 mm | cards, cross-plane | 1,500 pl. ≈ 18k tris | 800 pl. ≈ 9.6k | silhouette-critical; longest fur earns the most tris |
| Back / dorsal | 95 mm | cards | 1,100 pl. ≈ 8.8k | 550 pl. ≈ 4.4k | |
| Coat (general body) | 66 mm | cards | 1,600 pl. ≈ 12.8k | 800 pl. ≈ 6.4k | |
| Tail / ear tufts / limb feathering | varies | cards | 500 pl. ≈ 4k | 250 pl. ≈ 2k | from coat share; tail is a silhouette feature |
| Belly | 42 mm | **shells ×6** (desktop/WebGL-high) / texture (else) | zone tris × 6 | texture-only | shell cost rides on the *body* LOD's zone tris, not a card count |
| Body hair (chest patch, forearms) | 18 mm | texture + fresnel fuzz; shells ×4 max on desktop | ~0 card tris | 0 | prototype proved placement; look is a shader problem, not geometry |
| Muzzle / paws / inner ear | < 10 mm | texture-only | 0 | 0 | never geometry |
| **Card subtotal** | | | **≈ 43.6k tris** | **≈ 22.4k tris** | inside the §3 fur budgets with margin for fins |

**Density reality check [E]:** production LOD0 ≈ 4,700 placements vs the prototype's 1,700 —
≈ 2.8× the cards. At the prototype's mean card area (2.30 m² ÷ 1,700 = 0.00135 m² [M]) that yields
≈ 6.3 m² of quad area over a 4.93 m² body [M] = **1.28× body-surface quad ratio**, vs the
prototype's 0.47× (§7). That is the minimum at which a card coat stops reading as tufts on clay;
ruff-heavy species should push toward 1.5×.

---

## 5. LOD switching spec

**Switch on screen-height fraction** `f = character height ÷ viewport height` (renderer-agnostic,
resolution-independent), not raw distance. Distance equivalents for our 2.13 m character [M] at
60° vertical FOV: `d = 1.845 / f` metres [E].

| Tier | f range | Distance (2.13 m char) | Fur content |
|---|---|---|---|
| LOD0 | f ≥ 0.50 | ≤ 3.7 m | full cards (§4) + shells on |
| LOD1 | 0.25 – 0.50 | 3.7 – 7.4 m | ½ card placements, shells ×3, texture mip bias +1 |
| LOD2 | 0.10 – 0.25 | 7.4 – 18.5 m | ¼ placements (silhouette zones only), shells off, bodyhair/body zones texture-only |
| LOD3 | f < 0.10 | > 18.5 m | texture-only fur; impostor cross-quads if the naked body silhouette reads wrong |

Rules:
- **Hysteresis:** switch down at `f`, switch back up at `f × 1.15`; minimum dwell 0.5 s per tier.
  Fur LOD popping is unusually visible (silhouette change), so bias one tier *up* within 10% of a
  boundary when the camera is moving toward the character.
- **Per-zone independence:** zones may sit on different tiers (ruff holds LOD0 one tier longer than
  coat — it carries the silhouette). Zone tier = global tier, +1 for ruff/tail, −1 for belly/bodyhair.
- **Textures are NOT per-LOD.** All geometry LODs share one texture set; LOD reduces placements,
  never re-embeds textures (§7 shows why). Texture resolution steps down via mip bias, not new files.
- **Platform mapping:** WebGL/mobile ships LOD0–LOD2 + texture-only (no impostor mesh — the
  character is the whole scene; if f < 0.10 in a lineup view, texture-only suffices). SL ignores
  this table and uses §3c's four slots; author SL Lowest by hand from the LOD3 recipe.
- **Mini App reality:** the creator view lives at f ≈ 0.7–0.95 → LOD0 permanently. LOD1/2 exist
  for multi-character/lineup views and future social surfaces; do not spend payload on LOD3 there.

---

## 6. Overdraw & alpha rules (the mobile section that matters most)

1. **Cutout-first.** Card textures must bake with a genuine opaque core: ≥ 15% of texels at
   alpha > 0.5 [E target]. Render cards alpha-*tested* (threshold 0.45) with alpha-to-coverage
   where MSAA is on; reserve true blending for a single outer "halo" card layer if the look
   demands it, capped at O ≤ 0.5.
2. **O budget:** total blended+cutout fur overdraw at LOD0 ≤ 2.0 layer-equivalents over the visible
   body (§4's production density lands ≈ 1.3–1.6 [E] — inside, with the cutout core converting most
   of that from blended cost to early-discarded cost).
3. **Shells are fill, not tris:** 6 shells over a zone rasterise that zone ~6×. Only short-fur
   zones, only while their screen area is small or the tier is high. Never shell the whole body
   (a 25k-tri body at 12 shells = 300k tris and a fill disaster [S] — the most common way furry
   avatars become unshippable).
4. **Sort once:** one merged card mesh, one material, depth-write on (cutout) → no per-card sorting,
   no flicker. Blended halo layer, if any, is a second mesh, depth-write off, drawn last.

---

## 7. Measured audit — our assets vs these budgets

All figures [M], measured this pass from the GLB binaries and texture files.

### 7a. The body

| | Value | vs budget |
|---|---|---|
| Bara wolf avatar GLB | 72,166 verts / **128,550 tris** / 3 meshes / 65 joints / 6.32 MB / surface 4.93 m² | Desktop: inside 150k, barely. **WebGL: 2.1× over the 60k whole-character budget before any fur. SL: needs the §3c chain; as-is it is a High slot with no authored lowers.** |
| LODs | none | The body — not the fur — is our biggest LOD gap. A 60k/30k/12k body chain is prerequisite to every mobile fur budget above. |

### 7b. The strand groom (fur-prototype stage 2)

15,500 parents → **89,100 rendered strands** (ruff 14.4k, back 20.4k, belly 16.8k, coat 33.6k,
bodyhair 3.9k). As geometry that is 0.36M–0.89M tris [E] — **offline-only by design, PASS as a
master.** Its cost is authoring-time only; the D4 verdict (strand-authored → baked to cards) stands.

### 7c. The card LODs (fur-prototype stage 3)

| | LOD0 | LOD1 | LOD2 | Verdict |
|---|---|---|---|---|
| Cards | 1,700 | 680 | 255 | stride ratios 0.40 / 0.15 — reasonable steps |
| Triangles | 13,600 | 5,440 | 2,040 | **PASS** vs WebGL fur budget (≤24k) with room to spare |
| Card quad area | 2.30 m² | 0.92 m² | 0.35 m² | LOD0 = **0.47× body surface** → coverage FAIL (production needs ≥ ~1.28×, §4) |
| File size | **2.00 MB** | **2.55 MB** | **2.38 MB** | **FAIL — inverted.** Geometry buffers shrink correctly (652 → 263 → 98 KB) but each file re-embeds both textures, and LOD1/2's PNGs re-encoded *larger* (2.28 MB vs LOD0's 1.35 MB). LOD switching as shipped saves vertex work and **negative** download bytes. |
| Textures | 2× 512×1024 PNG in every LOD | same | same | VRAM 2 × 2.80 MB = **5.6 MB** regardless of LOD [M]; busts the WebGL fur-texture budget (≤4 MB) and is ~8× what KTX2 needs (~0.7 MB/texture [E]) |

### 7d. The card textures — the deepest problem

| | Texture A (dense) | Texture B (sparse) |
|---|---|---|
| Mean alpha | 0.064 | 0.032 |
| Texels alpha > 0.5 | **0.0%** | **0.0%** |
| Texels alpha > 0.05 | 39.7% | 19.8% |
| Fully transparent | 40.6% | 58.2% |

Consequences, all arithmetic from the table [E]:
- **Cutout is impossible.** At any sane threshold (0.4–0.5) these cards discard to nothing. They
  only render alpha-blended — the expensive, unsorted mode §6 forbids as the primary layer.
- **Effective coverage ≈ 14% of the body.** Cards picked A/B ~50/50 → mean visible-texel fraction
  ≈ 0.30; 2.30 m² × 0.30 ≈ 0.69 m² of actual fur over a 4.93 m² body. This number *is* the
  prototype's "bare clay with spiky tufts" verdict, quantified.
- **Fill efficiency ≈ 1 : 3.3.** Blending rasterises the full 2.30 m² of quads (visible half
  ≈ 1.15 m²) to deliver ≈ 0.35 m² of visible fur from a typical view. Two-thirds of the fragment
  work buys transparent texels.

### 7e. Scoreboard

| Asset | Tris | Coverage | Payload | Alpha/fill | Overall |
|---|---|---|---|---|---|
| Strand groom | offline ✓ | ✓ (hero renders prove it) | n/a | n/a | **PASS as master** |
| Cards LOD0 | ✓ 13.6k | ✗ 0.47× area, ~14% effective | ✗ 2.0 MB | ✗ blend-only | **FAIL — budget misspent, not overspent** |
| Cards LOD1/2 | ✓ | (inherits LOD0) | ✗ heavier than LOD0 | ✗ | **FAIL on payload only** |
| Body (wolf) | ~ desktop only | n/a | ✗ 6.3 MB for mobile | n/a | **NEEDS LOD CHAIN** |

The headline: **our fur does not have a triangle problem; it has a density, alpha, and packaging
problem.** Triangles are the one budget we're *under*.

---

## 8. Fixes, ranked by payoff (for the card/build agents)

1. **Re-bake the card textures dense.** Target: mean alpha ≥ 0.25, ≥ 15% of texels > 0.5, strand
   curtain packed so cards read as clumps, not mist. This single fix unlocks cutout rendering
   (→ sorted, early-discard, ~3× fill efficiency) and triples effective coverage at the *same*
   card count.
2. **Share textures across LODs.** One texture download, three geometry files (652/263/98 KB [M]).
   Kills the size inversion and cuts fur payload from ~2–2.5 MB to ~0.75–1.4 MB per character.
3. **Raise LOD0 to ~4,700 placements with cross-planes on ruff/tail** (§4 table) — now affordable
   because fix 1 makes each card carry ~3× the visible fur.
4. **KTX2/Basis for WebGL exports.** 5.6 MB VRAM → ~1.4 MB; also shrinks payload. Desktop GLB
   keeps PNG.
5. **Body LOD chain** (60k/30k/12k) — prerequisite for the Mini App ever holding its 60k
   whole-character budget with fur on top.
6. **Shells for belly/bodyhair on desktop tier only** (×6 / ×4 over the body LOD's zone tris),
   texture+fresnel elsewhere.
7. **SL export:** hand-author the Lowest slot (≤500 tris impostor-grade); never let the uploader
   auto-decimate it.

---

## 9. Sources

- Lengyel, Praun, Finkelstein, Hoppe — *Real-Time Fur over Arbitrary Surfaces* (2001): shells +
  fins, lapped textures. https://archive.org/download/random-papers14/Real-Time%20Fur%20over%20Arbitrary%20Surfaces%20%282001%29.pdf
- *Interactive Fur Shaping and Rendering Using Nonuniform-Layered Textures*, IEEE CG&A (2008):
  16/31/61 layer densities by projected fur length. http://www.researchgate.net/publication/3210694_Interactive_Fur_Shaping_and_Rendering_Using_Nonuniform-Layered_Textures
- TU Wien hair/fur state-of-the-art report: Lengyel LOD ladder (geometry → lines → shells →
  texture); 9,406-tri model → 129,466 tris at 16 shells. https://www.cg.tuwien.ac.at/courses/Seminar/SS2007/Hair-Brandorff.pdf
- Threedium fursona avatar guide: shell-count cap (~8 interactive), full-body shell blow-up
  (25k × 12 = 300k), VRChat rank anchors, cutout threshold 0.4–0.5 + alpha-to-coverage.
  https://threedium.io/create/3d-models/avatars/fursona
- Godot character-rendering playbook: per-platform character tri budgets (mobile hero 5–15k).
  https://github.com/xyrces/godot-ecs-gamedev-playbook/blob/HEAD/skills/3d_character_rendering/SKILL.md
- Stem Studio WebGL art specs: mobile draw calls 25–100, scene tris ~100–200k mobile, alpha
  Mask over Blend. https://github.com/stem-studio/engine/blob/HEAD/blog/docs/assets/10-art-specs.md
- Web3D performance budget skill: mobile ≤250k tris / ≤80 calls, DPR as primary lever, payload
  targets. https://github.com/ydabas-hue/portfolio-test/blob/HEAD/.agents/skills/web3d-performance-budget/SKILL.md
- Second Life mesh cost discussions (download weight across the 4 LODs, ~1,000 tris ≈ 1 LI
  heuristic, per-LOD halving allowance, Lowest-LOD dominance for small items):
  https://community.secondlife.com/profile/1262976-chinrey/content/page/2/?type=forums_topic_post
  and https://community.secondlife.com/profile/1116461-aquila-kytori/content/page/3/?type=forums_topic_post
- Second Life upload limits (4 LOD slots, ≤ 8 material faces, ~21,800 tris per face):
  https://www.snapshapy.com/use-cases/second-life

---

## 10. Open items / handoffs

- **To the card-baker agent:** §8 fixes 1–3 are yours; the acceptance numbers are §7d's targets
  (mean alpha ≥ 0.25, ≥ 15% texels > 0.5, LOD0 quad-area ratio ≥ 1.28× body surface).
- **To the body/retopo agents:** the body LOD chain (60k/30k/12k) gates every mobile fur budget.
- **To the Mini App work:** keep `setHardwareScalingLevel(dpr / 2)`; add fur LOD by screen-height
  fraction (§5) only when multi-character views land — the creator view is LOD0-locked.
- **Not verified in this pass:** SL viewer default avatar-complexity (jellydoll) threshold — SL
  budgets here are built from upload-side costs (LI/download weight), which we control, rather
  than viewer-side render-weight defaults, which vary by viewer and user setting.
- Disk discipline: analysis only, nothing downloaded or built; free space unchanged (~56 GB).
