# Fur Pipeline Prototype — FUR_PROTOTYPE.md

**Status:** complete. Strand groom → baked hair cards, end to end, on a real library body.
**Subject:** Bara Wolf base (`stick-figure-avatar/furry/bara_wolf_base.blend`, object `BaraWolfBody`) — the lineup's bara wolf, groomed in the pose the source file carries.
**Pipeline scripts:** `work/s2_regions.py` → `s3_groom.py` → `s5_cards.py` + `s5b_bakefix.py` → `s6_render.py`, finished by `work/s7_finish.py` after the original run was lost to a runtime restart (see "Verification & recovery" below).

---

## 1. Method in one paragraph

Five analytic region maps are painted onto the body as vertex groups. Each region gets its own Blender particle-hair system whose **density and length are both driven by that region's vertex group** — one groom, regionally art-directed. The strand groom is the master. Cards are then *derived from the groom, not authored separately*: two card alpha textures are baked by rendering a curtain of the same hair, and card geometry is sampled directly from the groom's parent strands (each card follows a real strand's curve), at three LOD densities. Everything downstream of the groom is mechanical.

## 2. Region maps (stage 1 — `fur_stage1.blend`)

Regions are smoothstep fields over world-space height bands, surface facing (front/back), and lateral distance from the spine plane — no hand-painting, fully reproducible from `s2_regions.py`. The same five weights are also baked into a `FUR_regions` colour attribute (R=ruff, G=back, B=belly, A=coat) for inspection.

| Region | Covers | Character |
|---|---|---|
| `FUR_ruff` | cheeks, jaw underside, throat, neck, upper chest | longest, wavy, clumped |
| `FUR_back` | dorsal torso, shoulders, rear | medium, curled |
| `FUR_belly` | front torso | short, fine, flat |
| `FUR_coat` | everything else (max of the others subtracted, floored at 0.04) | medium-short base coat |
| `FUR_bodyhair` | chest patch + forearms only | the body-hair variant — see §5 |

## 3. Strand groom (stage 2 — `fur_stage2.blend`)

One particle system per region, Principled Hair BSDF (brown, roughness 0.42), Cycles curve hair. Each system's vertex-group fields bind **both density and length** to its region map, so region borders feather instead of stepping.

| System | Parents | Length | Rendered children | Rendered strands | Notes |
|---|---:|---:|---:|---:|---|
| ruff | 2,400 | 0.170 m | ×6 | 14,400 | clump 0.65, WAVE kink |
| back | 3,400 | 0.095 m | ×6 | 20,400 | clump 0.45, CURL kink |
| belly | 2,800 | 0.042 m | ×6 | 16,800 | clump 0.25, no kink |
| coat | 5,600 | 0.066 m | ×6 | 33,600 | clump 0.40, CURL kink |
| bodyhair | 1,300 | 0.018 m | ×3 | 3,900 | clump 0.10, no kink |
| **Total** | **15,500** | | | **89,100** | |

## 4. Cards (stage 3 — `fur_stage3.blend`)

**Textures.** Two 512×1024 alpha cards (`fur_card_texture_a.png`, dense — 800 emitter parents; `fur_card_texture_b.png`, sparser — 380) baked by rendering an actual hanging curtain of the production hair shading against transparency (the v2 bake in `s5b_bakefix.py` fixed the v1 bake, whose emitter sheet occluded its own hair). Cards pick A or B at random per card.

**Geometry.** Each card is a 4-segment tapered ribbon (root width by region: ruff 0.030 m → belly 0.016 m, tapering to 15% at the tip, random ± twist) built along a **real parent strand's hair-key curve** sampled from the evaluated groom — so cards inherit the groom's flow, clumping direction, and regional length for free. The sparse `bodyhair` system is excluded from cards (at 18 mm it is below card scale; it stays a strand-only garnish).

| LOD | Cards | Vertices | Triangles | File |
|---|---:|---:|---:|---|
| LOD0 | 1,700 | 17,832 | 13,600 | `fur_cards_lod0.glb` (2.0 MB) |
| LOD1 | 680 | 7,212 | 5,440 | `fur_cards_lod1.glb` (2.5 MB) |
| LOD2 | 255 | 2,694 | 2,040 | `fur_cards_lod2.glb` (2.4 MB) |

GLB sizes are texture-dominated (both 512×1024 card textures embed in every file); geometry itself is tiny. All three validated with the QA gauntlet: parse clean, 0 degenerate triangles, 0 NaN, textures embedded, extent ≈ 2.13 m.

## 5. Body-hair variant

"Body hair" is not a second system — it is the same machinery with a sparser, shorter map. The `FUR_bodyhair` region (chest patch + forearms) runs 1,300 parents at 18 mm with light clumping against the coat's 5,600 parents at 66 mm. Turning a full pelt into body hair is purely a region-map + length edit; no new tooling. Evidence: `render_bodyhair.png` (bodyhair system alone) vs the full groom in `render_strands.png`.

## 6. Visual verdict — honest

`render_side_by_side.png` puts the two hero renders next to each other, same camera, same studio.

- **Strands (`render_strands.png`)** — a complete, silhouette-filling coat with visible regional structure: the ruff genuinely reads as a ruff, belly fur lies shorter. Weaknesses are groom-tuning, not pipeline: the WAVE/CURL kink at these amplitudes makes the coat read *woolly/poodle* rather than wolf-sleek, density swallows the muzzle and facial structure, and there is no colour variation (single flat brown hair colour, no root/tip gradient). All three are parameter and shader work on top of a pipeline that demonstrably delivers coverage.
- **Cards (`render_cards.png`)** — the honest failure of the pair. At 1,700 cards over a whole 2.1 m body, coverage is far too thin: the render reads as a bare clay body with sparse spiky tufts at the ruff and shoulders. The machinery is right (cards follow real strand curves, textures are real baked hair, alpha is clean) but game-viable card coats need an order of magnitude more cards, cross-plane card pairs, and a shell/underfur layer — or a much smaller subject area. As shipped, LOD0 cards would work for a *ruff-and-tufts* garnish, not a full pelt.
- **Boundary close-up (`render_boundary_closeup.png`)** — at 70 mm the frame fills entirely with hair: individual strands read cleanly (smooth curves, plausible thickness falloff, no faceting or card-like flatness) and the coat is fully opaque — no skin peeks through anywhere. What it does *not* show is flow: the kink/roughness settings make strands wander in every direction, so up close it reads as a tangled mat rather than combed, directionally-laid fur. Density and strand quality pass; groom directionality is the fixable flaw.
- **Body-hair variant (`render_bodyhair.png`)** — the variant works mechanically: with every other system hidden, short sparse hair appears exactly on the chest patch and forearms and nowhere else, proving the region map gates placement precisely. Two honest caveats: at 18 mm the hairs render as thin dark strokes that read more like drawn stubble than soft body hair (they want lower contrast against the skin and more randomness), and "forearms" on this posed, muscular base lands partly on the upper arm/shoulder mass. Placement system: proven. Look: first-draft.

## 7. Recommendation for D4 (fur primary)

**Strand-authored → baked to cards. Not close.** The strand groom is the only artefact in this prototype that looks like fur, and every card asset already derives from it mechanically — textures baked from its hair, geometry sampled from its curves, LODs by stride. Authoring cards directly would mean hand-placing the very thing the groom generates for free, and would strand the film-quality strand render that the same groom produces at zero extra cost. The card path's problem is budget (card count, cross-planes, shells), not authorship — fix the budget in the card baker, keep the groom as the single source of truth.

## 8. Deliverables

| File | What |
|---|---|
| `fur_prototype.blend` | deliverable scene: groom + cards + studio, hero strand configuration |
| `render_strands.png` / `render_cards.png` | hero renders, 720×900 |
| `render_side_by_side.png` | labelled montage of the two heroes |
| `render_boundary_closeup.png` | ruff/coat boundary, strands, 800×800 |
| `render_bodyhair.png` | body-hair variant alone, 800×800 |
| `fur_cards_lod0/1/2.glb` | card meshes, QA-validated |
| `fur_card_texture_a/b.png` | baked card alpha textures |
| `work/fur_stage1/2/3.blend` | stage files (regions / groom / cards) |
| `work/s*.py`, `work/studio.py` | full reproducible pipeline |

## 9. Verification & recovery notes

The original agent died in a runtime restart mid-`s6_render.py`: hero renders 1–2 and all stage files survived; the boundary close-up, body-hair render, and deliverable blend did not. This finish pass verified every surviving artefact (GLB via the QA gauntlet; all PNGs opened and inspected; stage blends and scripts audited), exported the missing LOD1/LOD2 GLBs from stage 3, and produced only the missing renders + deliverable blend (`work/s7_finish.py`; the final blend save was split into `work/s8_save_deliverable.py` after the combined run was killed by a runtime session limit just before the save step — both renders had already landed). Nothing completed was redone.

Known limits to carry forward: groom authored on the source file's posed frame rather than a neutral bind pose; single hair colour (no root/tip gradient or markings hookup — the markings system's fur-colour function belongs here); card density budget is a prototype value, not a production one.
