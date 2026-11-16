# A15 — Hand-Painted Fur Textures: the 2D craft, distilled + one painted pelt

**Deliverables in this folder**
- `canine_back_diffuse.png` — hand-method painted canine back pelt, 1024² (sable/agouti)
- `canine_back_roughness.png` — matching roughness variation, painted from the same strokes
- `paint_pelt.py` — the recipe as code (seeded; re-runnable)
- `render_back_region.png`, `render_back_closeup.png` — the pair applied to a back-region dome in Blender/Cycles (Principled: diffuse + painted roughness + diffuse-as-bump 0.012, sheen 0.18; final renders at 16 samples/768×576 — the VM was running ~40 parallel agents and Cycles was CPU-starved; grain in shadow areas is sampling, not texture)
- `detail_crop.png` — 2× crop of the diffuse for stroke inspection

---

## 1. What the craft actually is (studied, then followed)

Every working fur painter — traditional, digital, or VRChat texture artist — converges on the
same discipline, and it is **not** "draw every hair":

1. **Pattern, direction, value — in that order.** Break the coat into those three before any
   detail (Escape Motions / Ryanne Levin's fur tutorial). Fur *reads* because of value and
   direction, not detail (Paint Coach's pet-portrait teaching: think in clumps and chunks,
   use a bigger brush than feels natural, ask "which way is the fur actually growing?"
   before each stroke).
2. **Form before strands.** Block the pelt as large 3D value masses first; texture that
   ignores the form underneath looks pasted on.
3. **A fixed value ladder.** Pick ~4 values up front — deepest crevice shadow, mid-dark,
   mid-light, highlight — and check in grayscale. Never pure black or pure white.
4. **Work dark → light in passes.** Dark base first, then mid-tones, then lit clump tops,
   then a sparse handful of individual strands — detail only at edges and focal areas.
5. **Clumps, not strands.** Fur groups into tufts/locks; each clump has a lit top and a
   dark gap beneath it. The gaps are painted *as shapes* (one tradition paints the shadows
   between strands with a dedicated "fur shadow" pass — Monika Zagrobelna's method).
6. **Direction discipline is absolute.** Every stroke, even in the block-in, follows the
   growth direction and the body's contours. Random-direction scribble is the #1 tell of
   fake fur.
7. **Unify, then re-detail.** A little blending/smudge across strokes knits them into one
   coat; then a few confident tapered strokes on top restore the strand read. Too much
   blending = mud; none = confetti.
8. **VRChat/avatar practice mirrors this.** Avatar texture artists paint fur in Substance
   Painter with fur-shaped blending brushes + blur for soft edges (KodawithSoda's fluffy
   technique), organise files as layered PSD/SPP with per-part folders, and fight the same
   seam/bleed issues in UV space (inpainting padding is the standard fix — beesbuzz's
   Krita/Blender workflow). Painted fur is the cheap-LOD-friendly way to get coat detail
   onto low-poly bases — which is exactly the AnthroForge use case.

## 2. The species layer (canine back, sable/agouti)

Painting a *specific* coat means painting its hair biology (dog-coat genetics/breed sources):

- **Double coat.** Stiff **guard hairs** on top (they carry the visible pattern), soft dense
  **undercoat** beneath (paler, warmer-grey; it is what shows in the gaps and at the part).
  Two passes, two stroke characters: undercoat = short, soft, low-contrast; guard = longer,
  tapered, higher contrast.
- **Agouti banding.** A wild-type guard hair is not one colour along its length: **dark at
  the root, a yellow/cream band in the middle, tipped dark-to-black** (Husky Club / GSD
  sable references). The black *tipping* is what makes the saddle read dark: the longer and
  blacker the tips, the darker the dog. Painting banded strokes — not solid strokes — is
  the single highest-value habit in this whole recipe.
- **The saddle/blanket.** Dorsal pattern: dark blanket centred on the spine, fading into
  tan flanks (countershading: upperside banded/dark, underside lighter). In texture space
  for a back patch: a *saddle factor* field — 1 at the spine, 0 at the flanks — that
  lengthens black tips, darkens roots, and deepens the block-in.
- **Flow on a back.** Hair streams from neck toward tail and *spills sideways off the
  spine* like water off a roof, splitting at the centre part. The spine part itself shows
  root shadow — a soft dark line down the middle is correct, not a seam error.

## 3. The recipe (repeatable; this is exactly what `paint_pelt.py` does)

Canvas 1024², texture space **u = flank→spine→flank, v = neck→tail**.

| # | Pass | Tool analogue | Settings that mattered |
|---|------|---------------|------------------------|
| 0 | **Flow field first** | the "which way does it grow?" question, answered once, globally | dir = toward tail + lateral spill `0.62·tanh(2.2·sx)`, slight large-scale wobble; everything downstream samples it — no stroke ever freelances direction |
| 1 | **Value block-in** | big flat/filbert, 4 values | saddle field darkens centre to deep brown; flanks warm tan; low-frequency blotches (±10%) so masses aren't a clean gradient; spine-part shadow band; slight lightening toward tail |
| 2 | **Clump map** | — (the planning painters do by eye) | ~625 tufts on a jittered 46 px grid; each clump owns a tone offset (±13%), warmth offset, direction bias (±0.10 rad), lit factor |
| 3 | **Clump shadows** | "fur shadow" brush | tapered dark wedge under each clump along flow, α≈80, softened 2.2 px — these gaps are the depth |
| 4 | **Undercoat** | soft round, low α | 14,000 short strokes (18–38 px), warm grey-tan, α≈58, blur 0.7 — deliberately boring; it's the filler light lives in |
| 5 | **Guard hairs** | rigger/liner, tapered | ~15,000 strokes *grouped by clump* (start σ≈8–11 px around seed, direction = flow + clump bias ± 0.055 rad jitter), length 46–94 px, width 3.4→0.9 taper, 11 segments so the **agouti banding** (root dark → tan/cream band → black tip, tip blackness ∝ saddle factor) gradients smoothly; α≈205 |
| 6 | **Lit clump tops** | dry-brush highlight | only on clumps with lit > 0.45: a few paler strokes + a faint pale kiss on the last third — light lives on tuft tops, not everywhere |
| 7 | **Unify** | smudge/blend pass | 28% blend of a 0.6 px blur — knits strokes into coat; do NOT skip, do NOT exceed ~30% |
| 8 | **Flyaways + edge break** | rigger, sparse | only ~220, α≈58, *shorter than you think*; plus pale strand-ends breaking the tail edge. (Iteration 1 had 700 at α120 — it read as lint/scratches. Sparseness is the lesson.) |
| 9 | **Roughness, painted not derived** | second canvas, same events | base 0.85; every guard stroke replayed root→tip 0.91→0.62 (tips sleeker), saddle zone sleeker still; clump gaps pushed rougher (dust/occlusion); ±2% noise. Roughness painted from the same stroke list stays registered with the diffuse by construction |
| 10 | **Tooth** | — | ±1.6% per-pixel value noise last; keeps the render from looking airbrushed |

**Iteration log (what the eye caught):** v1 was too sparse, strokes too thin/hard, flyaways
everywhere → "rain on cardboard". Fixes: 1.7× guard strokes, wider tapers, more segments per
hair, unify pass, flyaways cut to a third at half alpha. v2 reads as a coat at texture
distance. Known remaining limits: banding is slightly stepped at 2× zoom; mid-flank stroke
lengths are a bit uniform; the palette sits warm-brown — a grey-sable variant is a palette
swap away (cooler undercoat, longer black tips, less cream).

## 4. Rules to carry into AnthroForge

- Paint **flow fields per body region** (the markings system's landmark flow can drive them);
  fur texture without a flow field is noise.
- The **saddle factor pattern generalises**: any coat pattern (saddle, points, rosettes)
  becomes a scalar field that modulates banding/tipping parameters per stroke — pattern as
  *parameters*, not as painted shapes. This is the texture-space twin of the markings
  layer stack.
- **Diffuse + roughness must be painted in one pass from shared stroke events.** Filters
  derived afterwards never register as well and can't know roots from tips.
- For card/shell fur (other agents' tracks), this pelt is the **colour source**: card
  alpha curtains should sample the same banding gradient root→tip so geometry fur and
  painted fur agree at the LOD switch.
- Budget: one 1024² pelt ≈ 3 min of procedural painting on this VM; a full body set
  (back, flank, neck ruff, tail, legs) is the same recipe with per-region flow fields and
  length/tone parameters — the recipe is the asset, the PNGs are instances.

*Sources consulted: Escape Motions fur/feather tutorial; PaintingProGuide hair & fur;
Monika Zagrobelna fur method; 2DArtist wolf fur walkthrough; Paint Coach pet-portrait
teaching; KodawithSoda Substance fur technique; beesbuzz VRChat texturing workflow;
dog-coat genetics references (SHCA agouti description, GSD sable/saddle pattern guides,
Wikipedia "Coat (dog)").*
