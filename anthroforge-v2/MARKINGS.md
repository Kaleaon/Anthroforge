# Markings & Decals — the AnthroForge pattern layer system

*Design spec, Nov 12, 2026. Companion to [APP_BLUEPRINT.md](sandbox://workspace/anthroforge-v2/APP_BLUEPRINT.md) §10 (materials) — this document is the full treatment of what the blueprint sketches in §10.3. Built on Rule HF5 from [HEROFORGE.md](sandbox://workspace/anthroforge-v2/HEROFORGE.md). Prototype: `markings-lab/` in this folder.*

---

## 0. The rule we are implementing

**HF5 — Zones for rigid parts, decals for morphing surfaces.**

Hero Forge shipped animal-head colour markings as *colour zones* (fixed regions painted into the part) for years. When its heads became morphable (Face Customizer), the zones smeared and slid under morphs, and HF **migrated the markings to the decal system**. That migration is the most expensive way to learn a lesson we can have for free:

- **Rigid parts** (horns, claws, teeth, armour, props): markings are **zones** — named regions in the part's own texture/materials, painted by number. No morph, no problem.
- **Anything that morphs, skins, or grows fur** (heads, bodies, ears, tails): markings are **layers** — masks defined against the base, composited at render time, baked at export. Never zones, never painted into the base diffuse.

Everything below is the layer system for morphing surfaces. Zones for rigid parts are already covered by the blueprint §10.1 material model and are not re-specified here.

---

## 1. The layer stack

A character's surface colour is an **ordered stack**, bottom to top. Each layer is a mask + a colour/material treatment; the stack composites in order. This stack *is* part of the character record (§3).

| # | Layer | What it is | Typical source |
|---|---|---|---|
| L0 | **Base coat** | The species/character ground colour: skin palette (§10.2) + fur root/tip + pattern function (§9.5). Includes plain countershading if the species profile defines it as base. | Species preset / palette pick |
| L1 | **Markings** | Species pattern: stripes, rosettes, stockings, ear-backs, face stripes, saddles. Defined per species preset, adjustable per character. | Preset, procedural generator, or painted mask |
| L2 | **Decals / tattoos** | Deliberate, placed art: tattoos, warpaint, scars-as-art, clan marks, makeup. Placed by the user (or a preset) at an anatomical address. | Stamp library, paint mode, imported PNG |
| L3 | **Wear** | Accumulated life: grime, sun-fade, scar tissue (the *material* kind — roughness/SSS change, not just colour), wetness state, dirt on paws/feet. Mostly procedural/parameterised. | Parameter set + optional mask |

Rules of the stack:

- **Order is semantic, not cosmetic.** Warpaint (L2) goes *over* the stripes (L1) — a tattooed tiger's tattoo sits on top of its striping, which is how pigment on skin over a patterned coat actually reads, and it's the order users expect when they reorder layers in the UI. Wear (L3) is always last: dirt covers everything.
- **Every layer is optional and independently removable.** Deleting L1 gives a plain-coated animal of the same species — the preset's markings are a default, never a lock (same discipline as HF1 species bundles).
- **Layers are per-surface-class.** The stack exists separately for head, body, and each part that carries its own texture space — but marking *presets* are authored across the whole animal at once (§4), so a tiger is striped coherently head-to-tail even though the masks live in two texture spaces.

### 1.1 The fur problem (read this before designing anything)

On a fully furred character, **the skin is invisible**. Tiger stripes are not skin decals — they are the *colour of the fur*. A markings system that only touches the skin diffuse will produce a striped skin under a plain coat, i.e. an unstriped tiger.

Therefore every marking layer's mask is consumed by **three render targets at once**:

1. **Skin diffuse/roughness** — for bare-skinned regions and skin-only characters (orc, human, scaleless areas, inner ear, paw pads).
2. **Fur colour function** — the mask modulates the fur root/tip colours (§9.5) per region, so the pattern appears *in the coat*: stripes darken the fur, rosettes ring it, stockings blacken leg fur. Agouti banding already lives here as a pattern function; markings are the spatial mask that pattern functions lacked.
3. **Shell/card tint** — the baked fur representations (blueprint §9) sample the same mask so LODs don't lose the pattern.

The mask is the single source of truth; which targets consume it is a render decision. A "markings" slider set that only works on skin is a bug, and the spec tests against it (§8).

---

## 2. How a marking is defined so it survives morphs

Three candidate definitions were evaluated against our bases (single-UV per mesh, 2k head / 2k body per blueprint §10.5; morphs from the learned pipeline routinely move surface points by centimetres; extremes regime pushes further).

### 2.1 Painted masks in base UV space

The marking is a grayscale (or RGBA) texture painted in the base mesh's UV layout — the same space as the diffuse.

- **Morph survival: perfect by construction.** The texture is glued to the surface by UV; wherever a vertex goes, its texel goes. A belly that grows 22 cm carries its stripes with it.
- **Cost: zero at runtime** (it *is* the texture, after baking; before baking it's one extra texture sample per layer).
- **Export survival: total.** Every format we ship takes textures. Nothing to convert.
- **Weaknesses:** resolution ceiling (2k head ≈ fine for face stripes, coarse for full-body fine striping on a bara frame — mitigated by per-region detail masks, §2.4); distortion follows UV distortion (a badly-unwrapped region smears markings exactly as it smears diffuse — our bases' UV quality is the real constraint, and it's already a constraint for everything else); painting *across* UV seams is painful in 2D (mitigated by paint mode painting on the 3D surface, §6.2, which projects into UV internally).

### 2.2 Placed decals with UV-space transforms

A small decal texture (a tattoo, a scar, a warpaint motif) plus a placement: an anchor region + a transform *in the base's UV space* (position, rotation, scale in UV units), composited into the mask stack at render/bake time. This is the blueprint §10.3 model, made precise.

- **Morph survival: as good as painted masks** — the decal lives in UV space, so it rides the surface. Region anchoring (§5) means "left brow" stays the left brow because the *anchor* is anatomical, not a raw coordinate.
- **The catch — seams and stretch:** a decal whose UV footprint crosses a chart boundary tears; a decal in a high-stretch UV region distorts with the morph. Both are *authoring-time detectable*: the app can warn "this placement crosses a seam" and the extremes-fit re-solve (§7) can flag decals whose local stretch exceeds a threshold.
- **Benefit over painting everything:** decals stay *editable objects* — move, rotate, recolour, delete — instead of being baked into a mask the moment they're placed. This is HF's decal UX (layered, re-orderable, per-part or across parts) and it's why users can iterate.

### 2.3 Triplanar / world-space projection

The pattern is defined in 3D space (projected from three axes, or a single projector box) and sampled by world/object position.

- **Morph survival: fails.** The pattern is anchored to *space*, not to the *animal*. Grow the belly and the stripes stay where they were in space — the surface slides through them ("swimming"). Shrinkwrap-style re-projection per morph state is a bake step, not a definition, and it drifts.
- **Where it's genuinely good:** rigid or near-rigid things (statues, armour grime, the print profile's airbrush-stencil preview), and *authoring* — projecting a reference pattern onto a posed mesh to *capture* it into UV space.
- **Cost:** runtime shader cost per layer, and no clean export story (every target needs a bake anyway).

### 2.4 Verdict

> **Canonical definition: everything lives in base UV space — painted masks for fields (stripes, rosettes, countershading) and placed UV-transform decals for objects (tattoos, scars, motifs). Triplanar is an authoring tool only: project to aim, bake to UV to keep.**

Concretely:

- A marking layer's stored form is one of: `{mask_file}` (painted/generated, full-UV), `{decal: {texture, region_anchor, uv_transform}}` (placed object), or `{generator: {kind, params}}` (procedural, §6.3 — resolved to a mask at load/bake).
- The viewport may *preview* with projection tricks; the **record never stores a projection**. What the record stores is what survives: UV-space data.
- **Detail masks:** for fine pattern on big bodies, a layer may carry a second, tiling detail mask multiplied over a region (e.g. rosette breakup noise) — the one sanctioned use of tiling, because it's a *modulator* in UV space, not a placement.

---

## 3. The character record

Extends blueprint §3.1's `materials.layers` (which already reserves an ordered list with `kind`/`id`/`opacity`). Full layer record:

```json
"materials": {
  "skin": { "palette": "species.tiger", "base": "#C8892B" },
  "layers": [
    { "id": "lyr_stripes", "stack": "markings", "kind": "generator",
      "generator": { "kind": "stripes", "seed": 4177,
                   "params": { "count": 46, "width_px": 15, "branch_prob": 0.4,
                               "colour": "#241407", "softness": 0.35 } },
      "regions": ["torso.back", "torso.front", "tail", "head.top"],
      "opacity": 0.92, "mirror": false },

    { "id": "lyr_earbacks", "stack": "markings", "kind": "preset",
      "preset": "marking.tiger.ear_back_spot", "opacity": 1.0 },

    { "id": "lyr_warpaint", "stack": "decals", "kind": "decal",
      "decal": { "texture": "decal.orc.clan_stripe", "anchor_region": "head.face",
                 "uv_transform": { "pos": [0.31, 0.62], "rot_deg": -12, "scale": [0.16, 0.05] },
                 "colour": "#7A1F1F" },
      "opacity": 0.85, "mirror": true },

    { "id": "lyr_grime", "stack": "wear", "kind": "preset",
      "preset": "wear.paws_grime", "opacity": 0.5 }
  ]
}
```

Field rules:

- `stack` ∈ `markings | decals | wear` (base coat is L0 and lives in `skin`/`fur`, not the layer list). **Stack order is fixed**; within a stack, array order is paint order.
- `kind` ∈ `preset | generator | decal | painted`. `painted` references a user mask file in the library (`"mask": "user/masks/chr_…_lyr3.png"`).
- `regions` uses the **fur-region vocabulary** (blueprint §9.5: `scalp, muzzle, cheeks, ruff, ears.inner, ears.back, torso.front, torso.back, arms, legs, tail, pelvis, hands, feet` — extended here with `ears.back`, `head.top`, `head.face`). One vocabulary for fur, markings, and wear: a region means the same patch of animal everywhere in the app.
- `mirror: true` mirrors the layer across the sagittal plane *in UV space* — valid only because our bases' UV layouts are symmetric by authoring rule (add to base-mesh checklist: **head/body UVs must be mirror-symmetric** or mirrored decals land wrong; asymmetric markings set `mirror: false` and carry both sides explicitly).
- Layers carry **provenance** like everything else in the record (which preset/generator version produced them) so a pack update can re-resolve generators without touching painted work (HF9 discipline).
- Share codes (§3.2) carry the layer list verbatim; generator layers travel as *params* (tiny), painted masks travel as library references (recipient without the file gets the layer listed as missing, same graceful degradation as parts).

---

## 4. Species marking presets

A species preset (§3.1 `species_preset`) ships a default L1 layer set. Each entry: what the marking *is* anatomically, which regions, and how it's defined (generator kind or painted/preset mask). All are starting points — every one is deletable/recolourable per §1.

| Species | Marking | Regions | Definition |
|---|---|---|---|
| **Fennec** | Black ear-backs (dorsal pinna near-black) | `ears.back` | Preset mask (sharp region fill) |
| | Dark eye-line (tear mark, inner eye → muzzle side) | `head.face`, `muzzle` | Preset mask, thin stroke |
| | Cream countershading (belly, inner legs pale) | `torso.front`, `legs`, `ears.inner` | Painted gradient mask, low opacity |
| | Rusty dorsal tint | `torso.back`, `head.top` | Painted mask, colour-only |
| **Badger** (Brand) | White head ground with **two black eye-stripes** running eye → ear, the family's signature | `head.face`, `ears.back` | Preset mask — stripe pair, must track eye/ear anchors (§5) |
| | Grey dorsal saddle, black ventral (inverted countershading) | `torso.back` / `torso.front`, `legs` | Painted masks |
| **Tiger** | Branching dorsal stripes, fading at belly | `torso.back`, `torso.front`, `tail`, `head.top`, `arms`, `legs` | **Generator: `stripes`** (§6.3) — parametric because stripe layout is individual, like fingerprints |
| | White muzzle/belly ground | `muzzle`, `torso.front` | Base-coat countershade (L0 variant) |
| | Black ear-back with **white ocellus spot** | `ears.back` | Preset mask (fill + spot) |
| **Lion** | Dark eye-lines (black liner extending from eye corners) | `head.face` | Preset mask, thin stroke |
| | Dark ear-backs with pale central patch | `ears.back` | Preset mask |
| | **Cub spotting** — faint rosettes over body, fading with age | `torso.*`, `legs` | **Generator: `rosettes`**, opacity driven by an `age` parameter in the preset instance (adult ≈ 0.05, cub ≈ 0.5) — a marking with a life-history dial |
| | Dark tail tuft | `tail` (tip region) | Preset mask |
| **Red fox** | **Black stockings** (lower legs black) | `legs` (distal), `hands`, `feet` | Preset mask with soft proximal edge |
| | Black ear-backs | `ears.back` | Preset mask |
| | White tail tip | `tail` | Preset mask |
| | White underside | `torso.front`, `muzzle` (chin) | Painted mask |
| **Leopard / jaguar** ("panther" coat) | Rosettes over whole coat; solid spots head/limbs | all | **Generator: `rosettes`** (+ `spots` for head/limbs). Melanism is an L0 palette (§10.2) — rosettes stay faintly visible *in* the black coat, as on a real panther: same layers, darker palette |
| **Wolf** | Dark saddle + pale underside countershading; facial mask (pale brow/cheek vs darker cap) | `torso.back`, `head.top`, `cheeks` | Painted masks |
| **Domestic cat** | Tabby: forehead "M", spine line, leg barring | `head.face`, `torso.back`, `legs` | Generator: `stripes` (low count, high regularity) + preset M mask |
| **Orc** | *No species markings* — orc pattern is cultural: clan warpaint, scarification | — | Ships as **decal library** entries (L2), not L1. The distinction matters: biology vs choice |

Authoring note: preset masks are painted **once, per base**, in that base's UV space (head preset masks on the head base, body on the body base) — they are per-base instances like slider instances (§3.3), with the species preset record pointing at each base's instance. New base ⇒ marking presets need an instance pass, same cost model as sliders: bounded, known, and reported by the library checker.

---

## 5. Placement is anatomical, not coordinate-based

Raw UV coordinates rot: a new base, a re-unwrapped region, or an extreme morph invalidates them. So decals and preset strokes are placed by **anchor**:

- Each base publishes **anchor points/regions in UV space** alongside its region map: `eye.L`, `eye.R`, `ear.base.L`, `brow.line`, `muzzle.bridge`, `jaw.angle`, `spine.dorsal`, `tail.tip`, etc. (The head spec's landmark set already names most of these; anchors are their UV projections.)
- A decal record stores `anchor_region` + a **relative** transform (offset in region-local units, rotation, scale relative to region size). The badger eye-stripe is "from `eye` toward `ear.base`, width 0.6× eye height" — true on any base that publishes those anchors, at any head size the sliders produce.
- This is what blueprint §10.3 means by "placement is region-anchored, so layers follow morphs instead of floating" — followed here to its conclusion: layers follow *bases*, too.
- **Anatomy-line rule** (orc spec §5.2): warpaint and face decals snap to / align with anatomy lines (brow torus line, jaw line, spine line) as guides in the editor — the same lines a real painter would follow on a real face.

---

## 6. Authoring UX — three modes, one stack

### 6.1 Stamp library (the default door)

Pre-made decals and marking presets in a browsable library: scars, clan marks, warpaint sets, makeup, species marking variants. Pick → click an anchor region → adjust size/rotation/colour/opacity → done. This is HF's model (paint-by-numbers for non-artists, HF3/HF5) and it serves ~90% of use. Stamps are *objects* (§2.2) — they stay editable and re-orderable forever.

### 6.2 Paint mode (the power door)

Brush directly on the 3D surface in the viewport; strokes project into the current layer's UV mask (blueprint §10.4 infrastructure — same brush engine as fur region painting). For custom tattoos, freehand warpaint, fixing a preset. Painting on the model (not the flat UV) is non-negotiable: nobody can paint a badger stripe on a UV chart. Seams: the projector blends across chart boundaries; the saved artifact is still a plain UV mask.

### 6.3 Procedural generators (the species door)

Patterns no one should paint by hand — striping, rosetting, spotting, countershade gradients — are **generators**: a parameter set resolved to a UV mask. Parameters are the character's (seed, count, width, branching, softness, colour), so:

- every tiger is striped *differently* (seed = individual variation, the fingerprint property);
- the pattern **re-resolves cleanly on a new base** (the generator works in region/anchor terms + UV, not pixels of one base);
- the record stays tiny (params, not a 2k PNG) and share codes carry the pattern exactly.

Generator catalogue (v1): `stripes` (tiger/tabby — branching tapered bands from a spine anchor), `rosettes` (broken-ring clusters), `spots` (solid, size falloff by region), `countershade` (dorsal↔ventral gradient by region set), `saddle` (dorsal field with soft edge). The `markings-lab/` prototype implements `stripes` and `rosettes`/`spots` and proves the output format (§8).

UX shape: generators appear in the markings panel as named patterns with 4–6 sliders — deliberately the same interaction grammar as body sliders (a pattern *is* a slider vector over a mask).

---

## 7. Baking, export, and the extremes regime

- **Viewport:** layers composite live (mask textures + decal sprites in UV space — cheap, no projection shaders needed precisely because everything is already in UV space).
- **Export:** layers **bake into the exported diffuse/roughness** per format profile (blueprint §10.3 already mandates this — targets don't carry our layer system). Bake resolution follows §10.5 (2k/2k/1k). The record keeps the layers; the export is a snapshot. BLEND interchange may optionally carry the unbaked stack.
- **SL profile:** bake is mandatory and total (≤8 material faces, §11) — markings become part of the skin texture, which is exactly how SL applier culture already works; our advantage is the bake is generated, not hand-painted per body.
- **Print/fursuit profile:** beyond the colour bake, the marking masks export as **stencil PNGs** (one per layer, at declared scale) — a fursuit maker airbrushes markings through stencils; a mini painter gets a painting guide. Costs us one render pass; nobody else in the creator survey does this.
- **Extremes (R4):** the fit re-solve that fires at extreme slider values also reports **decal stretch**: any placed decal whose local UV stretch factor exceeds ~2.5× is listed in the conformance report (not blocked — flagged, per the extremes regime's philosophy).
- **Fur LODs:** card/shell bakes sample the composited mask stack (§1.1 target 3), so a striped tiger stays striped at every LOD and in every export.

---

## 8. Prototype — `markings-lab/`

`generate_markings.py` (PIL + numpy, no other deps) implements two generator kinds end-to-end:

- **`stripes`** — tiger-style: tapered, wavy bands emanating from a dorsal spine, ~40% forking mid-length (branching), width tapering root→tip, spacing/length jittered by seed. Output: grayscale strength mask.
- **`rosettes` / `spots`** — jittered-grid distribution with wrap-around drawing (the spot field **tiles seamlessly** — proven by a 2×2 tile panel in the preview sheet); rosettes are broken rings of 5–7 blobs around a weaker centre (mask value ≈0.35), spots are solid discs.

Outputs (`markings-lab/out/`): `stripes_mask.png`, `rosettes_mask.png`, `spots_tiled_2x2.png`, and `preview_sheet.png` — masks composited over a tawny base coat and placed through an animal silhouette (placement proof), rosette/tiger composites, and the tiling proof, on one labelled sheet.

The generator functions take exactly the parameter dicts the character record stores (§3 `generator.params` + `seed`), so the prototype is the spec's reference implementation, not a sketch of one.

---

## 9. Open questions / honest limits

- **UV quality is the ceiling.** Markings inherit every flaw of the base UVs (stretch, seams). If head v2's UVs are weak in the muzzle, face markings will show it first. Mitigation is base-side (unwrap standards), not markings-side.
- **Resolution on huge bodies.** A 2k body texture on a 2.4 m bara orc makes fine striping soft. Per-region detail masks (§2.4) help; a 4k body option exists in §10.5's budget. We accept softness at extremes rather than inventing a second texture system.
- **Fur length hides pattern.** Long dense fur visually flattens colour pattern (real long-haired cats' tabby is muted). The fur colour function should attenuate marking contrast with fur length — a shader detail, flagged for the fur workstream, not solved here.
- **Asymmetric painted work doesn't port across bases** the way anchors and generators do; a hand-painted tattoo is per-base-instance data. Accepted: it's the user's art on that base, like a real tattoo on that body.
