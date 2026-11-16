# Paintable Fur Maps — PAINTMAPS.md

**A7, fur-craft wave, Nov 12, 2026.** The fur equivalent of the paintable
mobility fields (`first-proof/GRAVITY_WEIGHTS.md` §3): a set of painted
per-vertex maps on the groom surface that *are* the groom's parameters,
plus the tool that converts them into a groom. Prototype on the bara
wolf body (the fur prototype's subject): maps seeded procedurally,
repainted, converted — before/after renders in `out/`.

**Verdict up front:** the mobility pattern transfers one-for-one.
Painted fields + an analytic consumer beat both poles of the current
fur prototype: the five hand-tuned per-region particle systems (groom
parameters scattered across five system panels, region borders baked
into the setup) and pure guide grooming (hero-only, unrecordable).
With paint maps, the groom is *data on the mesh*: repaint the maps and
the groom — parameters, particle binding, guides, previews — re-derives
mechanically, and the character record stores a revisioned reference
instead of a groom.

---

## 1. What production tools actually do (study)

**XGen (Maya)** is the reference design. A description's primitives are
driven three ways, used in combination: *guides* (spline placement/shape),
*expressions*, and *painted maps*. The maps are per-attribute: a density
map (black = no growth, white = full), length, width, and modifier maps
for clump / curl / noise / cut — each created with Create Map, painted
in the 3D paint tool, and consumed through expressions of the form
`$a = map('${DESC}/paintmaps/stubbleDensity')`. Three details matter
for us:

- **The groomable-splines workflow replaces sliders with maps.** Brushes
  (length, density, comb…) write PTEX maps; the slider values become
  defaults the maps override. Painting is not an adjunct to the groom —
  it *is* the groom. Our map set follows the same inversion: the
  profile supplies defaults, the maps are the authority.
- **The Region Map is a colour map, not a mask.** Each colour defines a
  growth region with its own direction/flow (it sets the parting), and a
  companion Region Mask softens the boundaries. Direction as a *painted
  colour field* is exactly our `FURP_direction` layer (§2) — and XGen's
  region colours are the precedent for our colour-zone layers: colour
  painted on the surface carries groom semantics, not just albedo.
- **Clumping maps are generated, then painted over.** XGen's Setup Maps
  generates clump maps from the clump guides; artists refine by hand.
  Same authority ladder as the gravity fields: procedural seed →
  human repaint → learned.

**Blender** exposes the same model twice, and the differences are
load-bearing for our binding:

- *Legacy particle hair* binds vertex groups by name for **Density,
  Length, Clump, Kink, Roughness (×3), Twist, Velocity…** — one group
  per attribute, painted in Weight Paint. This is the fur prototype's
  system, and it is the cheapest possible consumer of scalar paint
  maps: the map *is* the input, no conversion. (Blender 5.2 API note:
  the bindings live on the **ParticleSystem** object —
  `psys.vertex_group_density` etc., each with an `invert_` twin — not
  on ParticleSettings. The fur prototype's `s3_groom.py` already uses
  the system-level properties; scripts that set them on the settings
  fail silently into AttributeError.)
- *Hair Curves + Geometry Nodes* (the modern system, and Blender's
  own "Quick Fur") consumes **named attributes** instead: a density
  mask attribute feeds Interpolate Hair Curves, Store Named Attribute
  writes painted fields the node graph reads. Same painted-field idea,
  attribute plumbing instead of group slots. Our colour-attribute
  layers (direction, zones) are already in this idiom, and the scalar
  groups can be mirrored to float attributes losslessly when the
  curves pipeline needs them (`FURP_density` group ↔ `furp_density`
  attribute is a rename, not a re-author).

**The pattern across all three:** scalar groom attributes are painted
per-vertex (or per-texel) fields; direction is a painted colour/vector
field or guide set derived from one; colour zones are painted colour.
Nobody ships a groom as a panel of global sliders. AnthroForge's
gravity work reached the same conclusion independently for flesh;
this document applies it to fur.

---

## 2. The map set (spec)

All layers live on the groom surface mesh, POINT domain, prefix
`FURP_`. A map set belongs to a *base instance* (like slider and
marking instances): same set id, per-base painted data.

### 2.1 Scalar maps — vertex groups (Weight Paint targets)

| Layer | Range | Meaning | Consumer binding |
|---|---|---|---|
| `FURP_density` | [0,1] | strand density, normalised against the fur profile's density scale | particle `vertex_group_density` (per-region baked, §4); GN density mask |
| `FURP_length` | [0,1] | strand length × profile `length_ref_m` (0.20 m in the prototype set) | particle `vertex_group_length` with `hair_length = length_ref_m` |
| `FURP_clump` | [0,1] | clumping strength | particle `vertex_group_clump` at `clump_factor = 1.0` (the map is absolute, the system scalar is a pass-through) |
| `FURP_curl` | [0,1] | curl/kink amount | particle `vertex_group_kink` when the region's mean curl arms the CURL kink (§4) |

Vertex groups, not textures, for the scalars — three reasons, all
inherited from the mobility decision: (1) they are paintable *on the
3D surface* with Blender's stock brush, no UV seam can tear them;
(2) they survive morphs perfectly (they ride vertices, and our
sliders are vertex fields all the way down); (3) the particle binding
consumes them with zero conversion. **Cost, stated honestly:** a
map's resolution is the mesh's vertex density — fine at our bases'
60k verts, coarse on a 2k-vert low-poly base. The escape hatch is the
same one markings use: a UV-space texture *variant* of the same layer
(§5.3), resolved to the vertex field at groom-build time. The layer
semantics don't change; only the storage raster does.

### 2.2 Direction — colour attribute `FURP_direction` (FLOAT_COLOR, POINT)

Direction cannot be a scalar. Encoding (tangent-space flow, per
blueprint §9.6):

- **R, G** = the flow direction in the vertex's UV tangent frame:
  `(d·T, d·B)` mapped [−1,1] → [0,1]. Decode: rebuild
  `d = c·T + s·B`, renormalise. (T from the base's UV layer; bases
  without usable UVs fall back to any stable perpendicular frame —
  flagged in the set's provenance, because the encoding is only as
  portable as the frame.)
- **B** = **lift** [0,1]: how much the strand stands on the surface
  normal vs lies along the flow. Strand root direction =
  `normalize(lift·N + (1−lift)·d)`. This one channel is the difference
  between a ruff (lift ≈ 0.55) and a slicked flank (lift ≈ 0.15), and
  it is what the fur prototype lacked — its coat read "woolly" partly
  because every strand left along the normal with kink noise on top.
- **A** = 1 (reserved).

Painting direction is a **comb brush**: the stroke direction writes
the flow (stroke-sampled, XGen comb / particle-edit comb semantics),
a modifier key paints lift instead. Nobody paints raw RG values.

### 2.3 Colour zones — colour attributes `FURP_zone_root`, `FURP_zone_tip`

The coat's colour as two painted tint fields: colour at the strand
root and at the tip (linear RGB, A=1). Zones are not IDs and there is
no zone palette stored in the set: a "zone" is simply where the
painted colour is roughly constant — the fennec's black ear-backs are
a region of near-black in both layers, the silvered belly in the
prototype repaint is a tip layer driven pale. This is the markings
system's fur-colour function (§1.1 of MARKINGS.md) given an authoring
surface: **the markings stack writes into these layers** (a marking
layer's mask modulates root/tip), and the groom consumes them, so a
striped tiger is striped *in the coat* at every representation —
strands, cards, shells — because all three read the same fields.
`FURP_zone_tip` is optional: absent, the converter derives tips by the
profile's `tip_lighten` from the root layer.

### 2.4 Derived layer

`FURP_viz` — heat-viz of density (mobility's `mobility_viz` pattern),
regenerated by tools, never painted, never stored in the record.

### 2.5 Brush semantics (app + paintable blend)

| Brush | Action | Notes |
|---|---|---|
| **Paint Density / Length / Clump / Curl** | add/sub the active scalar map | strength-scaled; maps clamp [0,1] |
| **Comb** | stroke direction → flow; stroke speed → confidence blend | writes `FURP_direction` RG; hold-modifier paints lift (B) |
| **Paint Zone** | colour brush on root *or* tip layer (toggle) | colour picker is the species palette by default |
| **Smooth** | graph-Laplacian relaxation of the active map | kills vertex-scale steps (the fold-makers of the gravity work) |
| **Flood** | set region / selection / flood-by-angle to a value | blocking-in: bare muzzle, shaved patch |
| **Sample** | read the map stack at a point into the groom panel | the panel shows *measured* params (§4), closing the loop |

Invariants: scalars stay in [0,1]; direction renormalises on write;
every committed repaint bumps the set's **revision** and author tag
(`procedural-seed` / `hand-painted` / `learned`), exactly the mobility
field discipline. A paintable deliverable blend ships the layers + a
`FURP_NOTES` text block + the viz layer, mirroring
`body.belly.protrusion_paintable.blend`.

---

## 3. Storage in the canonical character record

Extends blueprint §9.5's `fur` block and §3.3's per-base instance
rule. The record stores the *reference and the parameters*; the
painted data lives with the base instance in the library — a
character file stays small and share codes stay meaningful.

```json
"fur": {
  "profile": "species.wolf.coat",
  "paintmaps": {
    "set": "furp.wolf.bara",
    "base": "bara_wolf",
    "revision": 2,
    "author": "hand-painted",
    "layers": ["density", "length", "clump", "curl",
               "direction", "zone_root", "zone_tip"],
    "data": "library/fur/furp.wolf.bara@bara_wolf.npz",
    "seed": {"kind": "region-fields", "recipe": "fur-prototype-table-v1"}
  },
  "overrides": { "torso.back.density": 0.9 }
}
```

Rules:

- **`fur.paintmaps` is optional.** No paintmaps ⇒ the profile's
  region parameters drive the groom directly (today's behaviour).
  Paintmaps present ⇒ they are the authority; `overrides` still apply
  on top at evaluation time (they are record-level tweaks, the maps
  are base-level data — the same split as sliders vs instances).
- **Per-base data file** (`furp.<set>@<base>.npz`): scalar maps as
  sparse vertex lists (verts where the map differs from the seed —
  kilobytes, the mobility storage pattern); direction + zone layers
  as dense float16 arrays (they are near-dense by nature). Vertex
  order is the base's, versioned with the base.
- **Groom parameters are derived, never stored in the record.** The
  §9.5 per-region parameter table (density, length_m, clump, colour…)
  is what the converter *measures from the maps* (§4) — storing it
  would create a second, driftable truth. Tools that need parameters
  (MCP `fur_set`, perf estimates) run the aggregation; it is cheap
  (one weighted pass per region).
- **Provenance rides along**: set id + revision + author are recorded;
  a profile update may re-seed an *unpainted* set (author =
  `procedural-seed`) but must never touch a hand-painted one
  (HF9 discipline, same as markings generators vs painted masks).
- **Share codes** carry `profile` + `overrides` + the paintmap
  *reference*; a recipient without the data file gets the profile
  groom with the set listed as missing — the parts/markings graceful
  degradation, verbatim.

### 3.1 Relationship to markings

One vocabulary, two systems, no overlap: markings (§3 of MARKINGS.md)
own *pattern* (stripes, rosettes, ear-backs as species art — defined
in UV space, region-anchored, morph-proof by construction). Paint
maps own *groom mechanics* (how much hair, how long, which way, what
tint field). The seam is §2.3: at groom-build time the markings stack
is sampled into `FURP_zone_*` (and may modulate `FURP_density` —
long fur over a marking is still the marking's colour). A hand-painted
zone layer and a markings-derived zone layer are the same data type;
the record's provenance says which wrote it last.

---

## 4. The converter — `fur_paint_convert.py`

```
blender -b --python fur_paint_convert.py -- \
    --input fur_paintable_rev2.blend --outdir out --tag rev2 [--strands 9000]
```

Reads the FURP layers off the body mesh and emits:

1. **`groom_params_<tag>.json`** — the §9.5 parameter table *measured
   from the maps*: per region (the shared region vocabulary, fields
   carried as `FUR_*` groups on the paintable mesh), region-weighted
   means of density / length (× `length_ref_m`, in metres) / clump /
   curl / lift, region mean root/tip colours (exported as sRGB hex;
   the layers store linear), plus guide-set reference and a perf
   estimate calibrated on the fur prototype's strand counts.
2. **Production binding** (in the groom blend): one legacy particle
   system per region on a duplicated body. Density is the one map
   that must be region-baked — a particle system has a single density
   slot, so the converter writes `FURP_eff_density_<region>` =
   `FURP_density × region` and binds it; length/clump/curl bind the
   global FURP groups directly (their values are already absolute).
   Per-region hair material: Principled Hair BSDF, colour ramped
   root→tip (Hair Info intercept) through the region's measured
   colours. Systems ship `show_render = False`: they are the binding
   proof, not the verification render (see 3).
3. **Strand preview** (`FURP_groom_<region>` hair curves): emitters
   sampled ∝ face area × painted density; each strand grown from the
   interpolated maps — length from `FURP_length`, root direction from
   lift/flow, gravity sag ∝ (1 − lift), clump attraction to its
   7 cm cell's mean strand line, curl as a bitangent wiggle, and a
   surface-skim cap (a point's height above its root's tangent plane
   is capped ∝ length × lift, so the coat hugs the body instead of
   dangling in free space beside the limbs). This is
   the verification representation: *every* map, direction included,
   is visible in it, which the particle binding alone cannot show
   (particles leave along normals until combed — §6).
4. **Guides** (`FURP_guides`): streamlines integrated over the painted
   flow field from density-weighted seeds — the record's `guide_set`,
   ready for guide-based grooming or card baking downstream.

Re-running the converter after a repaint is the whole workflow:
**paint → convert → groom.** Deterministic per revision (seeded RNG),
so before/after comparisons are honest.

---

## 5. Prototype — what was actually done

Subject: `BaraWolfBody` (63,557 verts) from `bara_wolf_base.blend`,
the fur prototype's mesh, groomed in its source pose (same stated
limitation as the prototype).

1. **`seed_paintmaps.py`** → `fur_paintable_rev1.blend`. Region fields
   recomputed with the prototype's own formulas; scalar maps blended
   from its groom table (ruff 17 cm / clump 0.65 … bodyhair 18 mm);
   flow seeded as the canonical slick (backward + down, projected);
   lift 0.30 base, 0.55 on the ruff; zone palette seeded per region.
   Resulting map stats: density mean 0.80, length mean 0.42
   (max 0.83 = the ruff's 17 cm against the 20 cm reference), clump
   mean 0.42.
2. **`apply_repaint.py`** → `fur_paintable_rev2.blend`. A scripted
   stand-in for an artist session (no interactive Blender exists on
   this VM — stated plainly, as with the gravity repaint tooling).
   Four named ops, each exercising a different map:
   *mane_grow* (length +0.38, density +0.18 over ruff+spine),
   *shave_patch* (density → 0.025 across a 1,031-vert disc on the
   left shoulder), *chest_comb* (flow rotated −65° on the chest, lift
   settled 0.35 → 0.16), *zone_silver* (belly roots cooled, belly tips
   silvered to #B7B5B0, ruff tips creamed to #B4A993).
3. **`fur_paint_convert.py`** on both revisions → params JSONs, groom
   blends (5 region systems bound; 9,000 preview strands distributed
   ruff 1.2k / back 1.7k / belly 0.7k / coat 4.9k / bodyhair 0.5k;
   116 → 112 guide streamlines).

**Measured parameter deltas, rev 1 → rev 2** (converter output, the
groom *as the record would see it*):

| Region | density | length | root | tip |
|---|---|---|---|---|
| ruff | 0.878 → 0.925 | **12.6 → 17.0 cm** | #43392D | #867761 → **#B4A993** |
| back | 0.874 → 0.951 | **9.8 → 15.1 cm** | #3E352B | #766753 → #8F826E |
| belly | 0.747 → 0.752 | 4.3 → 4.6 cm | #544A3C → **#433F3A** | #80715C → **#B7B5B0** |
| coat | 0.754 → 0.759 | 7.3 → 8.2 cm | #443A2D | #796A56 → #867866 |
| bodyhair | 0.642 → 0.696 | 5.7 → 8.1 cm | #453B2F | #746653 → #999082 |

Every repaint op shows up in the measured parameters, in the right
region, at a plausible magnitude — the maps are not decoration, they
are the groom's source of truth, and the converter is a pure function
of them.

### 5.1 Renders (verified by inspection, Nov 12)

- `out/render_before.png` / `out/render_after.png` — the strand
  preview groom for rev 1 vs rev 2, same camera/lighting. The rev 2
  frame shows the *mane_grow* edit plainly: the ruff/back fur mass is
  larger, longer and hangs lower (ruff 12.6 → 17.0 cm, back
  9.8 → 15.1 cm per §5), and the coat reads as warm brown with the
  lighter rev 2 back tips. Two honest caveats: the silvered belly
  does **not** show in this frame — the camera is a back
  three-quarter view and the belly faces away; that edit is verified
  in the §5 parameter record (belly tip #80715C → #B7B5B0) and in
  the converted material (belly Hair BSDF Tint ≈ (0.85, 0.84, 0.83)),
  not in the picture. And at 9k preview strands the pair proves
  parameter response, not final fur quality — the production strand
  counts live in the fur-prototype pipeline.
- `out/render_maps_viz.png` — rev 2 density heat view (`FURP_viz`):
  hot orange over back/ruff/head (dense + long), cooling to
  pink/purple at hands, feet and lower legs (sparse + short), and
  the *shave_patch* edit visible as a small blue cold spot at the
  chest/shoulder edge — the clearest single-frame proof that a
  painted edit lands where it was painted.
- `out/render_guides_rev2.png` — the flow field as guide streamlines.
  The weakest frame: 112 guides over a whole body is sparse, most of
  each guide lies on the surface (hidden by the mesh), and mainly
  the silhouette-crossing segments read, as wisps off the back and
  arms. The guides' value is as data — they are in
  `out/groom_from_paint_rev2.blend` as `FURP_guides`, ready to comb
  against — more than as a picture; the *chest_comb* sweep is
  verified numerically (chest lift mean 0.17 after the pass) rather
  than claimed from this frame.

---

## 6. Honest limits

- **Particle direction.** Legacy particles cannot consume a flow
  field — they emit along normals and get direction from combing
  (particle edit) or kink. The converter therefore treats direction
  as *guide data* (streamlines + the preview) for the particle path.
  The curves/GN path can consume the field directly (interpolated
  curves follow guide/flow attributes), which is one more argument
  for the §9.3 strand-authored pipeline: direction painting is fully
  live there, advisory here. Stated, not hidden.
- **Preview curl is a wiggle, not a kink.** The strand preview bends
  strands along the bitangent with a sine; the particle binding
  carries the real CURL kink. They agree in spirit, not in silhouette.
- **Vertex resolution.** 63k verts paint a smooth field; a 2k-vert
  game base would not. §2.1's UV-texture variant is specced but not
  prototyped.
- **The repaint is scripted.** The ops are real edits to real layers
  with real falloffs, and the converter treats them identically to
  hand painting — but no human hand held a brush. The paintable
  blends are the deliverable an artist opens; rev 2 exists to prove
  the loop, not to claim an art pass happened.
- **Posed frame.** As with the fur prototype, maps were authored on
  the source file's pose, not a neutral bind pose. Map data rides
  vertices, so it transfers with the mesh; the *flow seed's* world-
  space assumptions (down = −Z) would need re-derivation on a
  bind-pose base.
- **Hair colour needs the melanin model.** Principled Hair BSDF in
  COLOR parametrization leaves the specular lobe untinted, so dense
  strands blow out to white and painted zone colours never read —
  proven with a constant dark-brown control patch (0.05 albedo
  rendered pale grey). The converter's materials therefore use the
  MELANIN parametrization (zone colour → melanin graded root→tip by
  Hair Info Intercept, tip colour → Tint), and the comparison
  renders pull exposure down (−0.8) for the same reason. The map
  data and the parameter JSON are identical either way; this is a
  shading-model requirement for *displaying* painted colour, and
  any future groom renderer in the stack inherits it.

---

## 7. Deliverables

| File | What |
|---|---|
| `PAINTMAPS.md` | this spec |
| `fur_paint_convert.py` | the tool: paint maps → groom params + groom scene |
| `seed_paintmaps.py` | procedural seed → `fur_paintable_rev1.blend` |
| `apply_repaint.py` | scripted artist pass → `fur_paintable_rev2.blend` |
| `render_compare.py` | before/after + guides + maps-viz renders |
| `furp_common.py` | shared layer I/O, region fields, direction codec |
| `fur_paintable_rev1.blend` / `fur_paintable_rev2.blend` | paintable deliverables (layers + `FURP_NOTES`) |
| `out/groom_params_rev1.json` / `groom_params_rev2.json` | measured groom parameters per revision |
| `out/groom_from_paint_rev1.blend` / `..._rev2.blend` | converted groom scenes (particle binding + strand preview + guides) |
| `out/render_before.png` / `render_after.png` / `render_maps_viz.png` / `render_guides_rev2.png` | verification frames |
