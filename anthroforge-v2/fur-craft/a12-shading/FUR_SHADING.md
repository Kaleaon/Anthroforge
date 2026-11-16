# Fur Shading Models — A12 (Fur-Craft Wave)

**Question:** which shading model should AnthroForge's fur use, given that the
shipped artefact is *alpha cards in Babylon.js / glTF*, while the offline
reference renders are Blender Cycles?

**Answer in one line:** ship **anisotropic GGX + Charlie sheen** on the cards
(both are ratified glTF extensions, both are native in Babylon's PBR material),
treat **rim/fuzz as an engine-only garnish that defaults OFF**, and reserve the
**Marschner family for offline strand-groom renders only** — it is the wrong
tool for cards physically, computationally, and in interchange.

Testbed: `fur_shading_testbed.blend`, renders in `renders/` (see §4).
Parameter proposals for `materials-lab/materials.json`: §6 (exact JSON).

---

## 1. The two classical fiber models

### 1.1 Kajiya–Kay (1989) — the empirical model

Fibers are cylinders; there is no cross-section and no interior. Two terms:

- **Diffuse** ∝ `sin(T, L) = sqrt(1 − (T·L)²)`, where `T` is the fiber tangent
  and `L` the light direction. A fiber lit from the side glows; lit along its
  axis it goes dark. This single term is most of why hair reads as hair.
- **Specular** ∝ `( sqrt(1 − (T·H)²) )^p` — one lobe whose highlight is a band
  where the half-vector `H` is perpendicular to `T`: a streak that runs along
  the fiber direction's perpendicular cone.

Properties: one white-ish lobe, no Fresnel, no absorption colour, no
transmission, no secondary highlight. Cost: a few dot products — which is why
real-time hair ran on it for two decades. Its direct descendant in production
is TressFX's *enhanced* Kajiya: a second lobe, shifted toward the tip and
tinted, fakes Marschner's TRT path at Kajiya prices.

### 1.2 Marschner et al. (2003) — the physical model

"Light Scattering from Human Hair Fibers." The fiber is a transparent
dielectric cylinder (IOR ≈ 1.55) with a pigmented interior (absorption σa)
and cuticle scales tilted by angle α. Scattering factorises into longitudinal
× azimuthal functions over **three paths**:

| Path | Route | Look |
|---|---|---|
| **R** | reflect off the surface | white (takes the light's colour); cone shifted **2α toward the root** |
| **TT** | transmit in → transmit out | forward-scattering backlight glow, coloured by absorption |
| **TRT** | transmit → internal reflection → transmit | coloured, glinty secondary highlight; cone shifted **toward the tip**, opposite to R — so the two highlights visibly separate |

### 1.3 Why Marschner is too heavy for us — four independent reasons

1. **Category error on cards.** It is a BCSDF *over fiber geometry*: it needs
   real strands with tangents and a circular cross-section to refract through.
   An alpha card is a textured quad — there is no interior, no cross-section,
   so TT and TRT cannot exist on it. Shading cards with Marschner isn't an
   approximation of the model; it's a different model wearing its name.
2. **Cost lands on the wrong side of our split.** Every practical
   implementation is per-strand path tracing: Blender's Principled Hair BSDF
   is Chiang et al. (2015)'s energy-conserving approximation of Marschner, and
   Yan et al.'s double-cylinder model (2015/2017) adds a scattering **medulla**
   — extra lobes (TTs, TRTs) — because animal fur is *not* human hair. Our
   strand groom is ~89k strands (fur prototype): a fine offline render, a
   non-starter for a Babylon scene or a phone GPU in the Telegram Mini App.
3. **Nothing to export to.** glTF has no hair/fur BCSDF extension, and
   Babylon's PBR material has no Marschner mode. Work authored in it dies at
   the export step — the exact step this project lives on.
4. **Even offline it's the wrong fiber.** Fur's medulla scatters light and
   desaturates it; vanilla Marschner (a human-hair model) over-glistens on
   pelage. If a hero groom render ever needs a fiber model, Principled Hair
   (Chiang-family, parameterised) is the closest available tool — still
   strand-only, still Cycles-only.

**Verdict:** Marschner-family = offline strand renders only. Never cards,
never glTF, never the creator app.

---

## 2. What actually ships: the three terms the testbed compares

### 2.1 Plain alpha-card PBR (setup A — the baseline)

Isotropic GGX on a textured quad. The highlight is a directionless blob: it
does not know which way the strands run, so under a long softbox the coat
reads as overlapping leaves/scales rather than fibers. This is the floor
everything else is measured against.

### 2.2 Sheen (setup B) — retroreflective microfibers

The Charlie sheen BRDF models a microfiber layer that returns light toward
the source, strongest at grazing angles: the soft halo around a backlit coat
and the general "downy" lift of real pelage. It is the single cheapest term
that makes a surface read as *fur-covered* rather than *fur-textured*.

- **glTF:** `KHR_materials_sheen` (ratified). `sheenColorFactor` — linear RGB,
  default `[0,0,0]` (black = layer off); `sheenColorTexture` (sRGB);
  `sheenRoughnessFactor` — default `0`; `sheenRoughnessTexture` — **alpha**
  channel. Sheen layers over the base and scales its albedo accordingly.
- **Blender:** Principled `Sheen Weight / Sheen Roughness / Sheen Tint`;
  the exporter folds weight × tint into `sheenColorFactor` — author the
  product, not the parts.
- **Babylon:** `PBRMaterial.sheen` is native (enable, colour, roughness) and
  the glTF loader wires the extension automatically.
- **Authoring rule** (already in the materials lab, kept): sheen tint = the
  coat's guard-hair highlight colour, never white.

### 2.3 Anisotropic GGX (setup C, first half) — Kajiya–Kay's insight, modern form

Anisotropy is the one idea from Kajiya–Kay that survives intact: *direction
matters*. The modern form stretches the GGX roughness along a tangent, so
highlights smear along the strand direction instead of blobbing. It is what
stops a coat looking like scales under directional light.

- **glTF:** `KHR_materials_anisotropy` (ratified). `anisotropyStrength`
  [0–1, default 0]; `anisotropyRotation` (radians); `anisotropyTexture` —
  **RG = direction** (remapped [0,1]→[−1,1]), **B = strength**.
- **Hard requirement:** a `TANGENT` vertex attribute, or a `normalTexture`
  the loader can derive MikkTSpace tangents from. Without tangent data the
  effect is *silently wrong* — this is the extension's main footgun.
- **Blender:** Principled `Anisotropic / Anisotropic Rotation / Tangent`;
  exporter support for the extension since Blender 4.2 (we run 5.2.3).
- **Babylon:** PBR anisotropy is supported in current Babylon.js and the glTF
  loader auto-wires strength + rotation. ⚠️ Verify against the creator app's
  *pinned* Babylon version before exposing the control in the UI.
- **On cards the tangent is free:** card authoring already fixes a strand
  direction — UV **V along the strand** — so UV-derived tangents carry the
  flow. A baked `anisotropyTexture` (the flow-map form) covers combed
  direction changes across a pelt (that texture is the natural output of the
  card-texture / flow workstreams).

### 2.4 Rim / fuzz (setup C, second half) — the cheat, with measurements

A Fresnel-weighted term added at grazing view angles fakes the silhouette
fuzz of fibers poking past the surface edge. It is **not energy-conserving,
not in glTF, and has no slot in Babylon's PBR material** (it needs a Node
Material block or custom shader chunk; OpenPBR's `fuzz` term likewise has no
glTF carrier). The testbed produced a clean, quantified failure and a usable
form — see §4.3. Short version: *never* as a Mix-Shader replacement (it
deletes the shading it should soften); additive-only, low strength, and only
where sheen is unavailable — sheen already produces a physical version of
the same halo.

---

## 3. Shippability matrix

| Term | Cycles | Eevee | Babylon PBR | glTF export (Blender 5.2) |
|---|---|---|---|---|
| Plain PBR + alpha `MASK` | ✅ | ✅ (Dithered method) | ✅ | ✅ core spec |
| Sheen | ✅ | ✅ | ✅ native | ✅ `KHR_materials_sheen` |
| Anisotropic GGX | ✅ | ✅ | ✅ (pin-check version) | ✅ `KHR_materials_anisotropy` (≥4.2), needs tangents |
| Rim/fuzz (additive) | ✅ nodes | ✅ nodes | ⚠️ Node Material only | ❌ dropped silently |
| Principled Hair (Marschner-family) | ✅ strands only | ❌ | ❌ | ❌ |

Eevee column is by node construction: every setup uses only Principled
features Eevee implements. This VM cannot render Eevee (no libEGL), so no
Eevee stills exist — do not cite the testbed as Eevee-verified.

---

## 4. Testbed

### 4.1 Method

`fur_shading_testbed.blend` + `scripts/build_testbed.py`. A spherical-cap
pelt patch (a full sphere was v1 and was discarded: every tangent flow field
on a sphere has a whorl singularity, and its crown rendered bald — the patch
is also how production swatches are built). **1,150 cards, one seed → the
geometry is bit-identical across setups**; only the card material changes.
Cards use the root-normal trick (custom normals = underlying surface normals,
so cards light as part of the coat volume, not as flat planes) and a
procedurally generated strand texture (`textures/fur_card_a12.png`,
512×1024 RGBA, root→tip gradient). Undercoat in all three setups is the
materials-lab `skin_furred_base` record as-is. Studio rig: long key softbox
(anisotropy needs a streak source), cool fill, warm back-rim light. Cycles,
512², 64 spp adaptive, OIDN denoise.

Setups: **A** plain · **B** + sheen (weight 0.6, roughness 0.5, guard tint
#d9ae7a) · **C** + anisotropic 0.7 (UV tangent) + additive rim (Fresnel
IOR 1.35 → ramp 0.62→1.0 × guard tint, emission 0.35, Add Shader).

### 4.2 Measured results

Pixel statistics over the identical-geometry renders (`scripts/measure.py`;
subject = luminance mask; silhouette band = outer ~6 px of the subject;
"control" = the bare-undercoat dome top, whose material never changes):

| Metric | A plain | B +sheen | C +aniso/rim | C v1 rim (Mix) |
|---|---|---|---|---|
| Subject mean luminance | 59.2 | 60.1 | **63.7** | 59.1 |
| Silhouette band mean | 62.3 | 63.9 | **72.8** | 64.8 |
| Silhouette band p95 | 185.7 | 186.5 | **191.1** | **159.8** |
| Control region mean | 122.3 | 125.3 | 130.8 | 112.0 |

Reading them honestly:

- **The control region spreads ±3% between renders of an *unchanged*
  material** — that is the noise floor (denoise + card fragments at the
  region's edge). Any delta under ~3% is not evidence.
- **Sheen's lift under this broad soft key is small**: +1.5% subject mean
  (inside noise), +2.6% in the silhouette band (marginal). Visually it is a
  softening/lifting of the whole coat, clearest at the rim crops in
  `comparison_strip.png`. This is expected physics, not a failed test: sheen
  is a *grazing-angle, toward-the-light* effect, and a big softbox key is the
  lighting that flatters it least. Its value concentrates in backlit and
  directional setups — the BackRim light here is deliberately modest. The
  case for sheen rests on that grazing behaviour + zero-risk portability
  (§3), not on a dramatic delta in this strip.
- **C's additive rim is the only term that moves numbers decisively**:
  silhouette mean +17% vs A, subject +7.7%, highlights preserved (p95 up,
  not capped). It reads as a downy bright fringe — at 0.35 strength it is
  already slightly too eager at the patch's lower edge; production default
  should be ≤ 0.25.
- The card-band gradient-orientation ratio (0.90 A / 0.91 B / 0.85 C) is
  dominated by the texture's own strands and does **not** isolate the aniso
  lobe; the anisotropy's contribution here is the directional smear visible
  in the mid-band under the long key, not a number this testbed can defend.
  Treat aniso's case as resting on §2.3 + the scales-vs-fibers read.

### 4.3 The rim failure mode (a result, not an embarrassment)

Setup C v1 mixed the BSDF and a Fresnel-driven Emission with a **Mix
Shader**. At grazing angles the Fresnel factor saturates across entire
texel-thin card fragments, so the mix *replaced* their shading with flat
emission: olive-brown cardboard patches at the dome's top and a hard curtain
fringe at the bottom (`renders/c_rim_mix_failure.png`). Quantified:
silhouette p95 collapsed 186 → 160 (highlights deleted exactly where rim
should glow) and the control region *darkened*. **Rule: rim is additive or
it is wrong.** Any future fuzz implementation — Babylon Node Material
included — must add, never blend-replace, and must be checked at the
silhouette first.

### 4.4 Per-setup cost notes

Wall-clock render times from the testbed run (A 530 s, B 634 s, C 434 s)
are **not usable as a benchmark**: machine load swung between ~4 and ~42
during the run (two agent waves sharing 1.5 CPUs). Structural costs instead:

- **A:** 1 texture fetch + isotropic GGX + alpha test. The baseline.
- **B:** +1 Charlie lobe evaluation, no extra textures, no extra memory.
  In Babylon it stays inside the standard PBR shader — effectively free.
  In Cycles it is one more lobe per bounce.
- **C:** anisotropic GGX is the most expensive lobe of the three, and it
  needs tangent data (a `TANGENT` attribute is 16 B/vertex if baked; free
  when derived from UVs). The additive rim is trivial ALU but costs a
  separate material/program variant in Babylon (Node Material).
- **The dominant cost of card fur in Cycles is none of these** — it is alpha
  transparency (transparent bounces through ~1,150 cards). Lobe choice is a
  second-order cost everywhere; pick lobes for looks and portability.
- **LOD guidance:** LOD0 = sheen + aniso · LOD1 = sheen only · LOD2+ =
  sheen only with anisotropy off (it is already off if tangents are dropped)
  · rim: off at every LOD by default.

### 4.5 Card-set caveat

The testbed's cards are prototype-grade: they read rectangular at glancing
range and coverage thins where cards stream away at the cap's upper rim.
Card *geometry and texture* quality belongs to the card-texture/clump
workstreams, not this one; because geometry is bit-identical across A/B/C,
the shading comparison is isolated regardless.

---

## 5. Recommendation

1. **Production fur material (Babylon / glTF / creator): anisotropic GGX +
   sheen, rim off.** The testbed separated B and C to isolate effects; the
   shipped stack combines them — sheen 0.6 / roughness 0.5 tinted to the
   guard colour, anisotropy ≈ 0.55 with UV-V tangents.
2. **Rim/fuzz: engine-only option, additive-only, strength ≤ 0.25, default
   off**, for targets with no sheen support. Never Mix-Shader. Never baked
   into an exported record as if portable.
3. **Marschner-family: offline strand renders only** (Blender Principled
   Hair), documented as non-exportable wherever it is used.
4. **Guard the anisotropy footgun in the pipeline:** any fur GLB export must
   carry `TANGENT` or a `normalTexture`, or the anisotropy values must be
   stripped — silently-wrong beats absent only in demos.
5. **Re-run this testbed backlit** (strong rim light, weak key) before
   finalising sheen weight for the creator defaults: that is the regime
   sheen lives in, and this strip's broad key understates it.

---

## 6. Exact parameter additions for `materials-lab/materials.json`

Proposed, in the file's existing schema. Not applied by this agent — for the
materials-lab owner to merge.

### 6.1 New record: `fur_card`

```json
{
  "category": "fur",
  "display_name": "Fur — Card/Shell Coat (shaded)",
  "gltf_export": "Base/rough + alpha MASK survive. Sheen -> KHR_materials_sheen; anisotropy -> KHR_materials_anisotropy (requires TANGENT attribute or normalTexture, else silently wrong — strip values if neither ships). rim_fuzz is DROPPED on export (engine-only, no glTF carrier).",
  "id": "fur_card",
  "intended_parts": [
    "all card/shell fur LODs — the visible coat surface (see fur prototype + fur-craft A8/A12)"
  ],
  "justification": "Cards are not fibers: no cross-section, no interior, so fiber BCSDFs (Marschner/Principled Hair) cannot apply and do not export. The shippable fur look on a quad is two surface terms: a retroreflective microfiber sheen (the coat's grazing halo, physical and portable via KHR_materials_sheen) and an anisotropic GGX lobe (Kajiya-Kay's one surviving insight — direction matters — as KHR_materials_anisotropy, tangent from the card's strand-direction UVs). Base colour defaults are the A12 testbed coat and are MULTIPLIED by the card texture, which carries the root->tip gradient. Rim/fuzz is recorded only to fence it: additive, engine-side, default off — the A12 testbed shows a Mix-Shader rim deleting the shading it should soften.",
  "normal": {
    "recipe": "none on the card itself — the lighting normal is the underlying surface normal (root-normal authoring rule for cards)",
    "source": "geometry (custom normals)",
    "strength": 0.0
  },
  "pbr": {
    "alpha": {
      "cutoff": 0.45,
      "double_sided": true,
      "mode": "MASK",
      "note": "Blender: surface_render_method DITHERED. Babylon: alphaCutoff from glTF alphaMode; disable backface culling. Use MASK, not BLEND — sorting artifacts at card crossings are worse than a hard edge.",
      "source": "baseColor texture alpha channel"
    },
    "anisotropy": {
      "gltf": "KHR_materials_anisotropy: anisotropyStrength = strength, anisotropyRotation = rotation_rad, optional anisotropyTexture (RG = direction remapped [-1,1], B = strength)",
      "lod": "LOD0 full, LOD1 optional, LOD2+ off",
      "range": [0.3, 0.8],
      "rotation_rad": 0.0,
      "strength": 0.55,
      "tangent_source": "card UV: V axis along strand direction (authoring rule); bake a TANGENT attribute or ship a normalTexture so loaders can build MikkTSpace tangents"
    },
    "base_color": {
      "note": "Multiplied by the card texture (root->tip gradient lives in the texture). Species/character tint replaces these defaults.",
      "srgb_default": "#8a6844",
      "srgb_high": "#c39a68",
      "srgb_low": "#4c3520"
    },
    "coat": { "roughness": 0.4, "weight": 0.0 },
    "ior": 1.45,
    "metallic": 0.0,
    "rim_fuzz": {
      "gltf": null,
      "recipe_babylon": "Node Material: Fresnel -> ramp 0.62..1.0 -> x guard tint -> ADD into PBR output. Or fold into sheen (preferred).",
      "recipe_cycles": "Fresnel (IOR 1.35) shaped by ramp 0.62->1.0, x guard tint, Emission strength <= 0.35, combined with Add Shader over the BSDF. NEVER a Mix Shader (A12 failure mode).",
      "status": "ENGINE-ONLY — no glTF representation; do not treat as portable",
      "strength_default": 0.0,
      "strength_max": 0.35,
      "warning": "Additive and non-physical: glows in dark scenes and double-counts the sheen halo. Ship only where the target has no sheen; production default <= 0.25 when on."
    },
    "roughness": { "default": 0.85, "high": 0.92, "low": 0.8 },
    "sheen": {
      "color_rule": "guard-hair highlight tint of the coat, never white",
      "gltf": "KHR_materials_sheen: sheenColorFactor = tint (linear) x weight; sheenRoughnessFactor = roughness; optional sheenColorTexture (sRGB) / sheenRoughnessTexture (alpha channel)",
      "roughness": 0.5,
      "weight": 0.6
    },
    "specular_level": 0.35
  },
  "shading_model": {
    "offline_strands": "Principled Hair (Chiang/Marschner family) — hero strand-groom renders only; non-exportable",
    "shipped_cards": "anisotropic GGX + Charlie sheen (this record)"
  },
  "textures_on_disk": [
    "anthroforge-v2/fur-craft/a12-shading/textures/fur_card_a12.png (testbed card texture, procedural)"
  ]
}
```

### 6.2 Amendments to `skin_furred_base`

Its `pbr.anisotropy` is currently a bare scalar (`0.3`) and its `sheen`
block lacks the export mapping. Replace/extend with:

```json
"anisotropy": {
  "strength": 0.3,
  "rotation_rad": 0.0,
  "tangent_source": "uv_flow (the record's strand-grain normal direction)",
  "gltf": "KHR_materials_anisotropy — same tangent requirement as fur_card"
},
"sheen": {
  "weight": 0.6,
  "roughness": 0.55,
  "note": "Sheen colour should be set to the coat's highlight tint (guard-hair colour), not white.",
  "gltf": "KHR_materials_sheen: sheenColorFactor = tint (linear) x weight; sheenRoughnessFactor = 0.55"
}
```

(unchanged fields of the existing `sheen` block are kept; only `gltf` is new
there. The `anisotropy` scalar becomes the object above so the undercoat and
the cards speak the same shape.)

### 6.3 Standing rules this implies for the pipeline

- Fur GLB exports are QA-gated on: `alphaMode == MASK`, sheen extension
  present when weight > 0, and (TANGENT attribute OR normalTexture) whenever
  anisotropy strength > 0.
- `rim_fuzz.strength_default` stays `0.0` in every exported record.

---

## 7. Sources

- Marschner, Jensen, Cammarano, Worley, Hanrahan — *Light Scattering from
  Human Hair Fibers*, SIGGRAPH 2003. (cs.cornell.edu/~srm/publications/sg03-hair-lr.pdf)
- Kajiya & Kay — *Rendering Fur with Three Dimensional Textures*, SIGGRAPH
  1989 (model summary as carried in the Marschner paper's §2 and the TressFX
  lighting implementation, github.com/o3de/o3de — Atom TressFX HairLighting).
- Khronos glTF extensions: `KHR_materials_sheen` and
  `KHR_materials_anisotropy` READMEs (github.com/KhronosGroup/glTF,
  extensions/2.0/Khronos/).
- Babylon.js feature comparison (doc.babylonjs.com, Babylon Lite vs
  Babylon.js): PBR anisotropy ✅ in BJS; glTF loader auto-wires
  `KHR_materials_anisotropy` strength + rotation.
- Chiang et al. 2015 (Principled Hair basis) and Yan et al. 2015/2017
  (double-cylinder fur) as surveyed in GAMES101 advanced-rendering notes.

*Agent A12, fur-craft wave, Nov 12 2026. Renders: Cycles on Blender 5.2.3;
Eevee not rendered on this VM (no libEGL) — §3's Eevee column is
construction-level, not measured.*
