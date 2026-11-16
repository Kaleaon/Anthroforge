# Card Texture Baking v2 — CARD_TEXTURES.md (A8)

**What this replaces.** The fur prototype's two card textures
(`fur-prototype/fur_card_texture_a/b.png`, 512×1024) were honest bakes —
a rendered curtain of the production groom — but flat: a single hair
colour (no root→tip gradient, no per-strand variation — called out in
FUR_PROTOTYPE.md §6), one density character per sheet, and no normal map.
This set keeps the "derive from strands" doctrine but authors the strands
*for the card*: simulated strand clusters with the colour structure real
fur has, baked at 512² in five behaviour variants, each with a tangent-
space normal. Pipeline: `scripts/bake_cards.py` (deterministic seeds),
test render: `scripts/render_strip.py` → `test_strip.png`.

## The set

| File (`card_<name>_diffuse.png` + `_normal.png`) | Strands | α coverage (>0.5) | Character / use |
|---|---:|---:|---|
| `straight` | 950 | 0.82 | sleek coat cards — backs, flanks, limbs |
| `wavy` | 880 | 0.82 | loose wave — neck, chest, general coat |
| `clumped` | 1,050 | 0.79 | 15 clump tips, toothed silhouette — ruff, cheeks, wet-look coats |
| `tail_plume` | 760 | 0.81 | swept lean + sparse clumps — tail plumes, ear tufts, feathering |
| `guard_ruff` | 520 | 0.74 | coarse thick strands, 16% pale guard hairs — mane/ruff top layer |

Palette is the bara wolf's brown, structured as real pelage: near-black
root → warm mid-brown → pale tan tip, per-strand value jitter ±18%,
agouti banding (2 dark bands) on 20–40% of strands, pale guard hairs
6–16% by variant. Recolouring = re-run with ROOT/MID/TIP/GUARD swapped;
the markings system's fur-colour function should drive those four stops
per species/character, exactly as it drives the strand groom.

## Bake recipe (what production card authoring does, and what we do)

1. **Strand-cluster simulation, not a photo and not a noise fill.**
   Each strand is a tapered polyline grown root→tip under variant
   behaviour: sinusoidal sway (wavy), convergence to shared clump-tip
   points from 25% length onward (clumped — this is what carves the
   toothed silhouette; gaps between clumps must reach the background or
   the card reads as a solid sheet), a unidirectional lean (plume),
   and a tip envelope that narrows lateral spread as t^1.4 so cards
   taper instead of ending in a blunt curtain edge. Strand *lengths*
   are drawn from a t^1.5-skewed distribution — uniform length jitter
   produces a visible "curtain line" of synchronised tips (v1 flaw,
   fixed after first inspection of this bake).
2. **Root→tip gradient is three-stop, not two.** Root shadow (also an
   AO band baked into the bottom 28% of the colour, darkening to 0.55×)
   grounds the card on the body; the pale tip stop sells translucency
   under rim light. Single-colour cards (the prototype's) read as felt.
3. **Rasterise at 2× and downsample.** Strokes drawn at 1024² with
   per-segment width taper (100% → 18%) and per-segment colour, then
   Lanczos to 512². Supersampling is what keeps individual strands
   readable instead of aliasing into mush at mip 1–2.
4. **Alpha shaping.** Coverage gets a contrast curve (opaque core below
   0.18 coverage → 0, full at 0.8) so alpha-test cutout keeps a solid
   core with a feathered silhouette; the root edge is faded over the
   bottom 4% so card bases don't draw a hard line on the skin.
5. **Edge bleed is not optional.** After downsampling, colour is
   iteratively diffused (14 blur-composite passes) into every texel
   with α < 0.03. Without it, mip levels sample the transparent-black
   RGB and every card fringes dark at distance — the classic card-fur
   bug. Alpha itself is never bled.
6. **U tiles, V does not.** Strands are drawn three times (x, x±W), so
   the texture wraps horizontally for wide card strips; vertically it
   is a root→tip ramp and must never repeat.
7. **Normals from height.** Normal map = gradient of the blurred
   coverage height field, strength per variant (clumped/guard 2.0–2.2,
   plume 1.5). This gives statistical across-strand shading — strands
   catch light as ridges. It is *not* true anisotropic strand shading;
   that belongs in the shader (flow-map direction), and the strand
   tangent field is the obvious v3 addition (the bake already computes
   per-segment tangents; exporting a flow map is a small change).

## Test strip

`test_strip.png` — Blender Workbench render (a Cycles pass was started
but the VM's CPU is shared across the whole fur-craft wave; Workbench
answers the strip's actual questions — coverage, gradient, fringe —
and Eevee is unavailable headless here), the `clumped` texture on
crossed-plane clusters (3 planes at 60° + 3 tilted fillers per cluster,
0.30 m cards) at three scene depths: **close ≈1.6 m, mid ≈3.4 m,
far ≈6.8 m**. Verified from the render: the root→tip gradient reads at
all three distances; mid-distance clump teeth still separate; no dark
fringing anywhere (edge bleed working); the far cluster holds together
as one fur mass instead of dissolving into speckle (the alpha-contrast
curve doing its job). Framing caveat: the close cluster is cropped at
frame left — the strip is a texture check, not a beauty shot.

## Honest limits

- Simulated-stroke baking vs the prototype's rendered-curtain bake:
  strokes give art-directable clumps/gradients the curtain lacked, but
  strands are 2D-clean — no self-shadowing *within* the card beyond the
  baked root AO. A hybrid (render this strand set in 3D for one
  hero variant) is the v3 experiment.
- Normal-from-height flattens where strands overlap densely; fine at
  card scale, wrong for macro close-ups (which should be real strands
  anyway, per the D4 strand-primary doctrine).
- Coverage 0.74–0.82 is dense — these are coat cards. For sparse
  garnish (ear tufts, chin), cut strand count ~40% rather than
  alpha-eroding these; erosion eats the tip gradient first.
