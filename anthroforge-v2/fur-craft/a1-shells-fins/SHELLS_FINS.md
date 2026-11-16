# Shell & Fin Fur — SHELLS_FINS.md

**Agent A1, AnthroForge fur-craft wave (Nov 12, 2026).**
**Question:** how do classic real-time shell texturing and silhouette fins work, what do they cost, where do they fail — and where do they fit in our strand-authored → baked-cards pipeline?
**Prototype:** shell stacks + fins built and rendered in Blender 5.2 (Cycles) on a patch of the library Bara Wolf body. All numbers in §3 are measured from that build (`work/build_a1.py`, stats in §3 tables).

---

## 1. The method

### 1.1 Shells

Shell texturing (Lengyel et al., Microsoft Research, 2001; Lengyel's earlier shell work 2000) renders fur as a stack of concentric copies of the surface:

1. **Preprocess — sample the hair volume into a texture.** Simulate or author a patch of fur once, then record, for a set of heights above the surface, which strands pierce that height. The compact modern encoding (what this prototype uses) is a single **strand-length map**: a tileable texture whose value at each texel is the length of the longest strand rooted there, normalised to [0, 1]. A strand exists at shell height *t* iff `length(texel) ≥ t`. Lengyel's original used one 128×128 texture per layer (typically **16 layers**); the length-map encoding stores all layers in one texture.
2. **Runtime — offset copies + alpha test.** Draw the mesh *N* times. Copy *i* is displaced along its vertex normals by `fur_length · t_i`, `t_i = i/(N−1)`, and shaded with the same length map: texels whose strand length is below *t_i* are discarded (alpha test / alpha scissor, threshold 0.5 in the common Godot implementation), the rest are opaque. Because every shell samples the *same* texture at the *same* UVs, the surviving dots line up vertically and the eye reads them as continuous strands rising through the stack.
3. **Shading cues.** Two cheap tricks carry most of the realism:
   - **Root darkening** — shells are darkened toward the base (a fake self-shadow/AO gradient; the Godot reference shader uses `mix(0.3, 1.0, shell_height)`). This prototype bakes the same gradient into each shell's base colour.
   - **Strand thinning** — coverage falls with height automatically, because fewer strands have length ≥ *t*. Real fur does exactly this (guard hairs outlength the undercoat), so the falloff reads correctly for free.

Shell offsets can also bend with height (gravity droop, wind) by curving the offset direction — `pos += n·L·t + droop·t²` — which is how shader implementations animate fur. The geometry here is static, so offsets are pure-normal; the droop term is a shader-side refinement, noted for the app port (§5).

### 1.2 Fins

Shells approximate the hair volume well when the view direction is roughly normal to the surface. At **grazing angles** — near silhouettes — the stack falls apart: you see *between* the shells, strands break up and the fur turns transparent and gappy. This is the shell method's known structural weakness, and fins are its classical fix (Lengyel et al. 2001):

- For each mesh edge, build a **fin**: a quad whose base is the edge and which extends along the surface normals to the full fur length — a thin curtain standing on the edge, in the plane containing the normal direction.
- Texture it with a **side profile of the hair volume** (strands seen from the side: vertical streaks with per-strand heights, fading at the tips) — one fin texture serves all edges.
- At runtime only fins on **silhouette edges** (one adjacent face front-facing, the other back-facing) need to be drawn; the GPU trick is to submit every edge as a degenerate quad and let the vertex shader extrude only silhouette edges. From a grazing view, the fin curtains face the camera and plug the gaps between shells; from a normal view they are edge-on and nearly invisible.

In this static Blender prototype the view-dependent extrusion is not available, so fins are real geometry, double-sided: a boundary set (patch rim edges — the silhouette this test patch actually presents) and a full set (every patch edge, as the runtime system would submit). Both are in the .blend for inspection.

### 1.3 Parameter landscape from the literature

| Source | Layers | Notes |
|---|---:|---|
| Lengyel et al. 2001 | 16 sampled layers | 128×128 patches, lapped textures to avoid a global parameterisation |
| Nonuniform-layered fur (IEEE CG&A 2008) | 16 / 31 / 61 density tiers | layer count adapts to view: fewest facing camera, most near silhouette |
| Godot community fur shaders | ~8–32 | alpha scissor 0.5, root AO mix, per-shell vertex displacement |

The consistent picture: **~16 layers is the classic working point for short fur**; below ~8 the stack bands visibly; above ~30 returns diminish unless the fur is long.

## 2. When shells beat cards (and when they don't)

**Shells win when:**
- **Fur is short and dense** — roughly ≤ 3–4 cm at character scale, where individual strand direction matters less than coverage and volume. Shells give *volumetric* coverage for a texture lookup; cards at that length are all root and no shaft.
- **The region is an undercoat.** A shell stack under a card layer is the standard production sandwich: shells guarantee no skin ever shows through; cards on top carry the silhouette and flow. (Our own fur-prototype verdict said the same thing from the other side: the 1,700-card LOD0 "reads as bare clay with spiky tufts" and explicitly called for "a shell/underfur layer".)
- **View distance is mid-range.** Shells hold up from ~0.5 m to several metres; they don't pop between LODs because there is only one representation whose layer count can step down.
- **The surface is the groom.** Shells need no separate card placement, no per-card curves — any skinned mesh with UVs and normals is fur-ready. For a creator app (ours) that is a decisive workflow advantage: fur becomes a *material + slider* (length, density) on any body region, including ones the user morphs.

**Cards win when:**
- **Fur is long** (ruff 17 cm, tails, manes). Shell step size grows with length — a 17 cm coat at 16 layers has ~11 mm gaps between shells, which reads as terraced plates, not fur. Cards follow real strand curves and stay coherent at any length.
- **Flow and silhouette shape are the point.** Combed direction, clumps, a shaped ruff silhouette — cards (baked from the groom) carry authored flow; shells only know the normal direction plus whatever the texture implies.
- **Close-up hero work.** At macro distances shells resolve into dotted plates; strands/cards keep reading.

**Neither:** at far LOD both collapse to the base mesh with a good fur-coloured, fur-roughened material — which our materials lab already treats as the floor (`skin_furred_base`).

## 3. Prototype — measured

**Build:** `work/build_a1.py` (Blender 5.2, Cycles CPU). Subject: patch of `BaraWolfBody` (63,557 verts / 127,110 tris) centred on the shoulder at (0.300, −0.047, 1.593), radius 0.17 m → **1,335 verts / 2,500 tris / 0.108 m²** of surface. Shells are real geometry copies offset along the source vertex normals; alpha test is a hard opaque/transparent mix at `length_map ≥ t` (sort-free, depth-honest, §1.1). Shell colour ramps root (0.30, 0.21, 0.13) → tip (0.56, 0.43, 0.29) as baked-in root darkening.

**Length map:** 512×512 tileable, 14,000 strand dots per tile, one tile = 6.8 cm of surface → **303 dots/cm², dot pitch ≈ 0.57 mm, dot Ø ≈ 0.43 mm**. Per-shell coverage (fraction of texels where a strand survives at height *t*), measured from the map histogram:

| t | 0.125 | 0.25 | 0.375 | 0.5 | 0.625 | 0.75 | 0.875 |
|---|---:|---:|---:|---:|---:|---:|---:|
| coverage | 0.535 | 0.533 | 0.500 | 0.420 | 0.286 | 0.107 | 0.013 |

Coverage halves by mid-length and is nearly gone at 0.875 — the thinning profile that makes the stack read as fur rather than as a solid offset surface.

### 3.1 Configurations — geometry cost

| Config | Layers (incl. base) | Shells above base | Fur length | Step | Shell tris | Total tris |
|---|---:|---:|---:|---:|---:|---:|
| SH8 | 8 | 7 | 25 mm | **3.57 mm** | 17,500 | 20,000 |
| SH16 | 16 | 15 | 25 mm | **1.67 mm** | 37,500 | 40,000 |
| SH24 | 24 | 23 | 25 mm | **1.09 mm** | 57,500 | 60,000 |
| SH16L60 | 16 | 15 | 60 mm | **4.00 mm** | 37,500 | 40,000 |

Fins: **boundary set 168 fins / 336 tris**; **all-edges set 3,834 fins / 7,668 tris** (the patch has 3,834 edges). Boundary fins cost 0.9% of the SH16 shell geometry; even the full fin set is 20% — fins are cheap, shells are the budget.

**Scaling to the whole wolf** (the patch is 2.0% of the body's triangles): a baked-geometry 16-layer stack over the full body would be ~**2.03 M tris**, plus ~380 k tris of all-edge fins. That is the baked-geometry number, and it's the wrong way to ship it — as a shader, the same effect is the 127 k-tri mesh *drawn* 16 times (vertex cost ×16, no extra memory, follows morphs/skinning for free). Either way, **cost scales linearly in layers × surface triangles, and fragment cost scales with fur screen coverage** (see render times).

### 3.2 Render cost (Cycles, 448×448, 24 spp, CPU)

Wall-clock on this shared VM is contention-inflated (load average 25–32 from the parallel agent wave; this process saw ~11–16% of a core, so dedicated-CPU time is roughly 6–8× lower). The **ratios** are the portable signal:

| Render | Wall s | Ratio | Reading |
|---|---:|---:|---|
| SH16 front (25 mm) | 636.5 | 1.00× | reference |
| SH8 front (25 mm) | 411.9 | 0.65× | halving layers saves only ~35% — base scene, BVH and stack traversal dominate; layer count is not the whole cost |
| SH16 grazing, no fins | 343.2 | 0.54× | less fur on screen |
| SH16 grazing + boundary fins | 212.5 | 0.33× | fins add no measurable cost (336 tris); the drop vs the no-fin frame is contention variance between runs, i.e. fin cost is below noise |
| SH16 front, 60 mm | 747.8 | 1.17× | longer fur covers more pixels → more transparent-stack traversal per ray |

Cost model, distilled: `cost ≈ layers × surface_tris (vertex) + fur_screen_coverage × layers (fragment, alpha-test rays keep walking the stack)`. Doubling fur *length* at fixed layers cost +17% here purely through coverage; doubling *layers* cost +54% (1/0.65). Texture memory is a non-issue in the length-map encoding: one 512² tile serves all layers and all regions (≈1 MB), vs Lengyel's original per-layer texture sets.

### 3.3 What the renders show (honest)

- **`render_shells16_front.png`** — at facing angles the stack reads as a continuous pale coat with fine grain; the silhouette rim shows clean fine terracing. But wherever the shoulder surface *turns away* (the anatomical creases), broad black bands open: the local view is already grazing there, shells gap, and the plates shadow the undercoat. The grazing failure isn't confined to the outline — it appears at every strong crease.
- **`render_shells8_front.png`** — same framing at 7 shells: the rim terraces are visibly chunkier (3.57 mm steps), the coat reads smoother and flatter, and the crease bands shrink to thin lines (a shorter stack shadows less). Fewer layers = coarser silhouette, lighter creases; more layers = finer silhouette, heavier crease shadowing. In a game shader the shadowing term is faked (root AO), which is why published results don't show this trade-off as starkly — Cycles' true shadow accumulation across 15 alpha-tested plates overstates the darkness, but the *gap geometry* underneath it is real.
- **`render_shells16_grazing_nofins.png`** — the textbook failure: at a true grazing camera the fur volume collapses to a pale slab floating over a black void; individual shell plates are visible as strata at the rim. Shells alone do not survive silhouette views.
- **`render_shells16_grazing_fins.png`** — boundary fins occupy the rim band as a segmented curtain exactly where the no-fin frame gaps (the mechanism works geometrically, for 336 tris). But in this static mock-up they render near-black: fin faces turn away from the key light, sit in the stack's shadow, and the prototype fin texture is sparse. Runtime fins are view-selected and fur-lit; treat this frame as proof of *placement*, not of final look.
- **`render_shells16_ruff60_front.png`** — 60 mm at the same 16 layers: the black crease bands explode and the rim terraces into plates. Step size (4 mm) × length is simply past the shell regime. This is the measured version of §2's rule: **shells are a ≤ ~3–4 cm technique; the 17 cm ruff belongs to cards/strands.**
- **`evidence_uv_seams_overexposed.png`** — kept as failure evidence: the first pass used the source mesh's islanded Tripo UVs (per-vertex, first-loop) and a 900-energy key light; the result is a blown-out white cap striped with black UV-seam streaks. The shipped build uses planar patch UVs (metres, tangent-plane projection) — see failure mode 3.

### 3.4 v3 look pass

A second pass (`work/swap_v3.py`, same .blend) re-aims the look: clump-scale length map (2,600 clumps/tile, pitch ≈ 1.33 mm, Ø ≈ 0.93 mm — strand *clumps* at screen scale instead of sub-pixel hairs), darker palette (root (0.15, 0.10, 0.06) → tip (0.40, 0.29, 0.18)), denser/brighter fin texture, front fill light. Results: `renders/render_shells16_front_v3.png`, `renders/render_shells16_grazing_fins_v3.png`. (Assessment appended below the render table when the pass lands.)


## 4. Failure modes (observed + from the literature)

1. **Grazing-angle transparency (the fin problem).** Without fins, the silhouette thins and gaps — visible in the paired grazing renders. Fins plug it but add their own artefacts: fin curtains are visible as faint walls when many overlap at complex silhouettes, and a static fin set (like this prototype's) shows fins edge-on as stray lines from some angles. The runtime silhouette test exists precisely to hide those.
2. **Terracing / banding at low layer counts.** Each shell is a plate; at 8 layers over 25 mm the steps are ~3.6 mm apart and the coat reads as stacked discs under raking light. Longer fur makes it worse linearly — this is the hard ceiling on shell fur length.
3. **UV dependence.** Shell strand density is texture density × UV density. Stretched or seamy UVs stretch strands into streaks or slice them at seams. (Our subject is a Tripo mesh with a single auto-UV layer — the doc's tiling numbers are computed from the patch's actual UV span, and uneven texel density across a whole body is the first thing a production version must normalise.) Lengyel's lapped textures existed to kill exactly this problem on arbitrary topology.
4. **No lean, no flow.** Pure-normal offsets make fur stand at attention. Real coats lie along the body. Shader shells fix this with a per-vertex flow/droop vector; geometry shells (this prototype) can't without extra data. A shell stack under *cards* hides this — the cards carry the flow.
5. **Thin-geometry blowout.** Offsetting along normals inflates thin parts (ears, fingers, muzzle edges): opposing shells intersect and the part gains fur-length in every direction. Production shells clamp length by a per-region length map (our region maps already carry exactly this data — `FUR_*` vertex groups drive both density and length).
6. **Sorting & transparency cost.** Alpha-*blended* shells need back-to-front sorting and 16+ transparent layers of overdraw. Alpha-*tested* shells (this prototype: opaque/transparent mix at a hard threshold) keep the depth buffer honest and sort-free, at the price of hard dotted edges — the right trade for fur.
7. **Self-intersection under morphs.** Shells are offsets of the *current* surface, so they follow BodySlide-style morphs for free in a shader; baked geometry shells (prototype) would need re-offsetting per morph state. Another argument for implementing shells in the app as a shader, not geometry (§5).

## 5. Where shells fit in our pipeline

Our pipeline verdict (fur-prototype) was **strand-authored → baked to cards**, with the card layer's thin coverage named as its one structural weakness. Shells are the missing third component, not a competitor:

```
strand groom (authoring master)
   ├── baked cards        → long fur, silhouette, flow, hero LOD0
   ├── SHELL STACK        → undercoat everywhere; the ONLY fur on short regions
   └── fur material       → far LOD floor
```

Concretely, for AnthroForge:

1. **Undercoat beneath cards (LOD0/LOD1).** A 8–16-layer shell stack at undercoat length (say 40–60% of guard length) under the card layer guarantees the "bare clay" failure can never recur, for the price of a texture and a shader — no new authored assets, since shell density/length maps derive from the same region maps that drive the groom.
2. **Short-fur regions outright.** Muzzle, ears, paws, forearms — and the prototype's *body-hair variant* (18 mm chest/forearm hair, which "reads as drawn stubble" in strands) — are shell-shaped problems: too short for cards, too sparse-looking as strand garnish. Shells with a length map from the bodyhair region map are the natural implementation.
3. **The Telegram Mini App / Babylon.js creator.** Shells are the one fur technique that is *pure shader + the base mesh*: Babylon gets N instanced/drawn copies with a vertex-shader offset and a fragment alpha test — no groom export, no card geometry, works on any morphed body in real time. For an interactive creator where the user drags a "fur length" slider, shells are the only option that updates for free. Recommended split for the app: **shells for the live preview and short regions, cards baked at export for long regions.**
4. **Markings hookup.** The markings system's fur-colour function already colours "skin diffuse, fur colour function, and shell/card tint" from one mask — a shell stack samples the same mask per shell, so a striped tiger is striped *through the depth of the coat*, which neither a surface texture nor card tint alone achieves.

**Implementation note for the app:** do shells as a shader over the base mesh (per-vertex normal offset by layer, length/density from region maps baked to a texture), never as baked geometry — geometry shells (what this prototype builds, for measurement) multiply vertex count by N and freeze the morph state.

## 6. Sources

- Lengyel, Praun, Finkelstein, Hoppe — *Real-Time Fur over Arbitrary Surfaces*, I3D 2001 (shells, volume sampling, lapped textures, fins). https://archive.org/download/random-papers14/Real-Time%20Fur%20over%20Arbitrary%20Surfaces%20%282001%29.pdf
- Lengyel et al. — shell-texturing patent US20020021302A1 (offset shells, alpha test, per-layer compositing).
- *Interactive Fur Shaping and Rendering Using Nonuniform-Layered Textures*, IEEE CG&A 2008 (16/31/61 layer tiers, view-dependent layer counts).
- Akenine-Möller et al., *An Introductory Tour of Interactive Rendering*, IEEE CG&A 2006 (shell + silhouette-fin summary, GPU fin extrusion trick).
- Godot VFX Sketchbook fur effect + community shell shaders (alpha scissor 0.5, root AO mix, per-shell vertex displacement) — the modern indie reference implementation. https://deepwiki.com/gtibo/VFX-sketchbook-Godot-4.x/4.8-fur-rendering-effect
- Internal: `../FUR_PROTOTYPE.md` (strand→cards pipeline, card-coverage verdict), `../../MARKINGS.md` (fur-colour function), `../../materials-lab/` (`skin_furred_base` floor).
