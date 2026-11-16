# Fur Colour Patterning — FUR_COLOUR.md

*Learning agent A11, fur-craft wave, Nov 12, 2026. Extends
[MARKINGS.md](sandbox://workspace/anthroforge-v2/MARKINGS.md) §1.1/§9.5 and
[APP_BLUEPRINT.md](sandbox://workspace/anthroforge-v2/APP_BLUEPRINT.md) §9.5,
whose colour record — `{root, tip, pattern: agouti|solid|tipped|banded}` —
this document replaces with a band-profile model. Prototype code and assets
live in this folder (`work/gen_fur_colour.py`, `textures/`, `renders/`).*

---

## 0. The one idea everything hangs on

Real mammal pattern lives at **two independent levels**, and a fur system
that conflates them gets both wrong:

1. **The hair level** — each individual hair is *banded along its shaft*:
   alternating zones of eumelanin (black/brown) and pheomelanin
   (red/yellow/cream). This is the agouti mechanism, and it is a property
   of a single follicle's growth cycle.
2. **The coat level** — *which follicles* run which banding program varies
   across the body. A tabby's stripes are not dark pigment painted on the
   coat: stripe-zone follicles grow (nearly) **unbanded eumelanin hairs**,
   ground-zone follicles grow **banded agouti hairs**, and the pattern you
   see is the border between two hair populations. The pattern map is laid
   down in the *skin* before any hair grows (in cats, the Dkk4 prepattern).

Consequences that drive the whole design:

- **A stripe is a population switch, not a colour.** Any system that draws
  stripes only into a diffuse texture has the wrong artefact: at card and
  strand level the stripe must change the *shaft program* of the hairs in
  the zone, or close-ups will show banded hairs inside a "black" stripe.
- **Ticking is what banding looks like with no coat-level pattern.** The
  Abyssinian's shimmer is level 1 with level 2 turned off (Dkk4 loss of
  function): no populations, just every hair banded.
- **Distance behaviour is different per level.** Banding averages out with
  distance (§4); population borders do not — a tabby is visibly striped
  from across the room and merely *warm* up close in the ground areas.
  Our prototype's distance test (contact sheet panel 4) demonstrates both.

---

## 1. The biology, compressed

### 1.1 Two pigments, one switch

Melanocytes in the follicle make exactly two pigments: **eumelanin**
(black→brown) and **pheomelanin** (red→yellow→cream). During hair growth,
the **ASIP** protein (agouti signalling protein) is secreted in a *pulse*;
while ASIP is present it antagonises the MC1R receptor and the melanocyte
switches to pheomelanin. When the pulse ends, it switches back. The shaft
is therefore a **recording of the pulse train** laid down root→tip as the
hair grows:

```
root ───────────────────────────────────────► tip
[ eumelanin ][ pheomelanin ][ eumelanin ]   one ASIP pulse = one light band
     base          band            tip cap
```

- Most wild-type coats (wolf, tiger ground, tabby ground) have a **dark
  base and a dark tip with a sub-apical pheomelanin band** — the pulse
  fires mid-growth. Multiple pulses = multiple bands (dog/wolf agouti
  commonly shows 3–5 bands).
- **CORIN** suppresses ASIP: prolong the pulse and the light band widens —
  the "wideband" phenotype (golden tigers). One knob: **pulse width**.
- Turning the pulse **off** gives a solid eumelanin hair (stripe zones,
  recessive-black coats). Turning eumelanin off gives solid pheomelanin.

### 1.2 Space is two more knobs

ASIP expression is spatially patterned by separate promoters, which is why
a single animal runs different programs in different regions:

- **Dorsal** hairs: banded (hair-cycle promoter on).
- **Ventral** hairs (belly, chest, throat, inner legs, muzzle underside):
  **solid pheomelanin, no banding** (ventral promoter) — this is the
  developmental basis of countershading. A wolf's pale belly is not a
  marking laid over the coat; its hairs are a different type.
- **Pattern zones** (tabby stripes, tiger stripes): the embryonic skin
  prepattern modulates the pulse per follicle — in dark zones the pulse
  is suppressed toward zero. **Taqpep** variants decide the geometry
  (mackerel = narrow stripes, classic/blotched = swirls and bullseyes);
  **Dkk4** variants suppress the pattern itself (ticked).

### 1.3 Hair types: guard vs undercoat

A pelt is (at least) two hair populations with different jobs:

| | Guard hairs | Undercoat (underfur) |
|---|---|---|
| Form | long, straight, thick | short, fine, often crimped/"zigzag" |
| Share | minority of hairs, most of the visible surface | majority (tiger ≈ 90% zigzag underhairs) |
| Colour program | the full band profile — this is what pattern is made of | usually **near-solid**, often paler or contrasting; bands compressed/absent |
| Role in the read | pattern, sheen, silhouette | depth, matte body, the colour that shows where the coat parts |

The undercoat is why a coat reads differently where it parts or is ruffled:
you see the under-layer's colour, not skin. Any fur stack without an
undercoat layer will read thin and "wig-like" — the fur-prototype's cards
(render_cards in FUR_PROTOTYPE.md) show the coverage version of this.

---

## 2. The model: shaft profiles + a melanism field

### 2.1 Shaft profile (hair level)

A profile is a list of bands over hair parameter `t ∈ [0,1]`, root→tip.
Each band: `{centre, width, colour, pulse?}`. Evaluation paints bands in
order over the band marked `ground` (the eumelanin base state), with soft
edges (real band transitions are graded, ~a few % of shaft length).

```json
"colour": {
  "pattern": "agouti",
  "bands": [
    {"centre": 0.00, "width": 0.30, "colour": "#38312b", "ground": true},
    {"centre": 0.34, "width": 0.26, "colour": "#a97e4f", "pulse": true},
    {"centre": 0.60, "width": 0.24, "colour": "#d9c49a", "pulse": true},
    {"centre": 0.90, "width": 0.30, "colour": "#201c19"}
  ]
}
```

`pulse: true` marks the pheomelanin bands — the ones ASIP controls. The
**shaft-gradient atlas** is this profile sampled at 1024 points: a 1-D
function, one row of `textures/shaft_atlas.png` per profile. A card or
strand shader never needs the band list at runtime; it samples the atlas
at `(population_row, t)`. The band list is the *authoring* form (it is
what a species preset stores and what users edit as "band position /
width" sliders).

### 2.2 Melanism field (coat level)

Define **melanism `m ∈ [0,1]`** per follicle (in practice: per texel of
the coat mask, or per card column at bake time). The follicle's profile
is the ground profile with every pulse band's width scaled by
`(1 − m)^1.35`:

- `m = 0` → full agouti banding (ground zones, ticked coats everywhere).
- `m ≈ 0.5` → bands narrowed, dark bands merging — the *edge* of a stripe,
  and the mechanism behind "smoky"/ghost patterning.
- `m → 1` → pulse width zero → solid eumelanin hair (stripe zones).

This is deliberately **one mechanism for stripes, edges, and ghosting**,
because that is what the biology is: a spatial map of ASIP pulse
suppression. It also gives stripe *softness* for free: the mask's falloff
*is* the band-narrowing zone, which is why real stripe edges look graded
at hair level even when the skin-level border is sharp.

**How MARKINGS drives it:** a markings layer's mask (stripes, rosettes,
spots generators; MARKINGS.md §6.3) is consumed by the fur colour function
as `m = mask_strength × layer_melanism` (per-layer, default 1). The mask
was already the single source of truth for skin diffuse + fur colour +
shell tint (MARKINGS.md §1.1); A11 just specifies *what the fur colour
function does with it*: it doesn't tint hairs toward the marking colour,
it **reprograms** them toward melanic. (Tinting is still correct for
*colour* markings that aren't melanin patterns — white spotting, red-fox
stockings are melanocyte-absence/eumelanin-presence cases and map to
`m = 1` with an eumelanin colour swap; the leopard's rosettes on a black
coat are the same layers at low mask opacity over a melanic base palette,
per MARKINGS.md §4.)

Species pattern → field mapping (v1):

| Pattern | Melanism field | Notes |
|---|---|---|
| Ticked (Abyssinian) | `m ≈ 0` body-wide; barring masks on legs/tail/face at `m → 1` | banding alone reads as shimmer |
| Mackerel tabby | `stripes` generator, narrow, `m → 1` in stripe | wild type |
| Classic tabby | same generator, wide + swirl params | Taqpep geometry only — same hair model |
| Tiger | `stripes`, `m → 1` in stripe; ground profile has single sub-apical band | stripe hairs measured uniformly black |
| Leopard rosettes | `rosettes`: ring texels `m → 1`, centre `m ≈ 0.35` | matches the generator's weaker-centre mask |
| Wolf saddle | low `m` lift (≈0.25) + tip-band widening over the back | wolf "pattern" is mostly band-proportion change, not populations — see §5 |
| Solid / self | profile has no pulse bands at all | melanism field irrelevant |

### 2.3 The two hair types in the model

Each region carries **two profiles**: `guard` (banded, patterned by the
melanism field) and `undercoat` (near-solid, melanism applied at reduced
strength — underfur in stripe zones does darken, but less). Layer
assignment in the render stack (blueprint §9.3):

- **Shells**: inner shells sample the *undercoat* distance colour; outer
  shells sample the coat-level composite (ground/stripe integral colours
  mixed by the mask) — because a shell is a distance representation, it
  should carry level-2 information only.
- **Cards**: undercoat cards (short, dense, wavy) under guard cards
  (banded atlas). Blueprint card budgets should assume both sets.
- **Strands (hero)**: per-strand profile lookup with the follicle's `m`;
  undercoat strands drawn from the undercoat profile at high count.

---

## 3. Record format (extends §9.5)

Per region, replacing `colour: {root, tip, pattern}`:

```json
"fur_region": {
  "colour": {
    "guard":     {"pattern": "agouti", "bands": [ … ]},
    "undercoat": {"pattern": "solid",  "bands": [ … ]},
    "melanism_from": "lyr_stripes",        // markings layer id, or null
    "melanism_strength": 1.0,
    "undercoat_melanism_strength": 0.45
  }
}
```

`root`/`tip` survive as a *derived* shorthand (first/last atlas samples)
for cheap consumers (thumbnail renderer, SL bake of the texture floor).
Profiles for the prototype's species are in
`textures/fur_colour_profiles.json`, including each profile's measured
**distance colour** (§4).

---

## 4. Distance: the integral rule

When a hair is sub-pixel, the eye integrates along the visible shaft. The
coat's far colour is therefore the **length-weighted mean of the shaft
profile** — not the tip colour, not the root colour:

```
distance_colour = ∫₀¹ profile(t) dt        (per hair population)
coat_far(mask)  = mix(distance(ground), distance(stripe), mask)
```

Measured on the prototype profiles:

| Profile | Distance colour | Pheomelanin length share |
|---|---|---|
| wolf guard (dorsal) | `#76634a` grizzled tan-brown | 0.50 |
| wolf undercoat | `#9a8d78` pale warm grey | — (solid) |
| wolf ventral | `#c0a377` cream | — (solid) |
| tabby ground | `#6e5535` warm brown | 0.42 |
| tabby stripe (m = 0.97) | `#3e3124` dark umber | 0.004 |
| tiger ground | `#5d3f20` deep ochre-brown | 0.30 |

Readings:

- The wolf's countershading is *in the table*: ventral integral is two
  value-steps lighter than dorsal with zero markings involved.
- Tabby stripe vs ground integrals differ by ~2× in luminance — the
  population contrast that survives distance. The banding itself
  contributes *texture*, not contrast, at range.
- Use distance colours for: LOD3/texture-only floor, shell tints,
  thumbnail renders, and the SL bake. Using tip or root colour instead
  is the classic bug that makes game fur change colour as you approach.

**Caveat (honest):** the integral is over *guard* hairs. Real far colour
also mixes the undercoat where the coat parts and at grazing angles;
our `coat_wolf_dorsal.png` models that crudely (undercoat show-through
speckle at ~28% texels, mixed at 0.55). A Principled-Hair-style energy
accounting is beyond v1.

---

## 5. Species recipes (profile parameters)

Values are the prototype's shipped profiles (authored from the sources
in §7). `bands` abbreviated as centre/width/colour; P = pulse band.

**Wolf (grey wolf, dorsal guard)** — the multi-band grizzle:
eu base .00/.30 `#38312b` · P tan .34/.26 `#a97e4f` · P cream .60/.24
`#d9c49a` · eu tip .90/.30 `#201c19`. Undercoat solid `#6f6455`→`#a3967f`.
Ventral: solid pheomelanin `#8a6f4d`→`#c8ab7d`. The wolf's darker saddle
is *not* a population change: it is the same profile with the tip band
widened (≈ width .30→.42) and the cream band narrowed over the back —
a regional band-parameter gradient, which the record supports by letting
a region carry band overrides. This is the third spatial mechanism,
distinct from melanism: **band-proportion gradients** (also how "red"
vs "grey" wolf phases differ).

**Brown tabby (ground)** — fine multi-band ticking:
eu base .00/.26 `#453729` · P .30/.22 `#b0824a` · eu .50/.10 `#4c3b2a` ·
P .66/.20 `#c09a5c` · eu tip .90/.26 `#231b13`. Stripe = same profile at
m = 0.97. Legs/face barring: stripes generator at small scale.

**Tiger (ground)** — single sub-apical band (measured on real hairs):
eu base .00/.34 `#3d2c1c` · P .62/.30 `#c07f36` · eu tip .93/.26 `#191008`.
Golden-tiger variant = pulse width ×≈1.6 (wideband) — one parameter,
exactly the CORIN story.

**Fennec** — pheomelanin-dominant, banding vestigial: base `#c8ab7d`,
one weak P band .55/.30 `#e3cda3`, tip `#a98f66`; undercoat near-white.
Ear-backs are a markings layer at m = 1 with black eumelanin (MARKINGS §4).

**Lion** — near-solid tawny: eu-poor profile, base `#a8845c`, faint P
band .5/.4 `#c09a68`, tip `#8a6c46`; cub rosettes are a markings layer
whose melanism is weak (m ≈ 0.5) and age-faded (MARKINGS §4) — through
the pulse model, weak m *narrows bands* rather than drawing rings of
colour, which is why cub spots look like texture, not paint.

**Red fox** — dorsal: rufous pheomelanin profile, thin dark tip
(`#2a1e16` at .95/.12) over P-dominant shaft; the black stockings and
ear-backs are m = 1 layers; white tail tip / underside = pigment-off
regions (profile → unpigmented `#e8e2d4`), a third profile state the
atlas represents as its own row when a species needs it.

---

## 6. Prototype — what was built and what it proves

Pipeline: `work/gen_fur_colour.py` (PIL + numpy). Colour is applied to
the fur-prototype's **real baked strand alpha** (fur_card_texture_a/b),
so card strand layout, flow and clumping are production artefacts; only
the colour is A11's.

Artefacts (`textures/`):

| File | What |
|---|---|
| `shaft_atlas.png` | 7 profiles × 1024-sample strips (wolf guard/undercoat/ventral, tabby ground/stripe, tiger ground/stripe) |
| `fur_colour_profiles.json` | band lists in record format + measured distance colours + pheomelanin length shares |
| `card_wolf_agouti_a/b.png` | wolf guard cards, dense/sparse |
| `card_wolf_undercoat.png` | undercoat cards (own short wavy strand alpha) |
| `card_tabby_ground.png` | tabby ground-population cards |
| `card_tabby_boundary.png` | a follicle-zone patch: melanism sweeps 0→1 across the card; hairs grade banded→melanic through the edge |
| `coat_wolf_dorsal.png`, `coat_tabby.png` | coat-level diffuse (shell tint / texture floor); tabby's is the markings stripes mask driving integral colours |
| `coatmask_tabby_stripes.png` | the driving mask itself |
| `shell_alpha_l0..l3.png` | tileable shell alpha, erosion levels |

Two implementation details worth keeping:

- **Phase jitter is not optional.** Follicles are not band-synchronised —
  hairs sit at different growth phases and lengths. A first pass with
  synchronised bands produced clean horizontal strata that read as a
  *flag*, not fur. The shipped bake uses two-octave per-column phase
  jitter (±0.14 t); the atlas stays the single-hair truth, the card is a
  population. Any strand shader needs the equivalent (per-strand phase
  offset from the strand id).
- **The boundary card bug worth remembering:** interpolating profiles by
  summing segment lerps (instead of bilinear sampling a melanism×t LUT)
  silently over-accumulates colour and blows out to white. Profiles are
  functions; sample them, don't add them.

Renders (`renders/`, script `work/render_patches.py`): two dome "pelt
patches" — wolf (left) and tabby (right) — each = 3 shell layers (coat
diffuse, eroding alpha) + 170 cards, Cycles (`render_patch_near.png`;
a far variant is gated behind `A11_FAR=1` in the script). What the
render does prove: the full stack composites (shells carry the
coat-level pattern, cards carry the shaft colour), and the two
populations read differently at patch scale — the tabby patch is
visibly darker and warmer with melanic streaking against the wolf's
pale grizzle. What it does not do is look like a finished pelt: at 170
cards/patch over a steep dome the cards read as coarse fringe (a
card-budget and groom-flow artefact — the colour system's inputs are
correct; density/flow are the A1/A2 briefs, and FUR_PROTOTYPE.md §6
reached the same verdict about the source groom). The §4 distance
behaviour is verified independently by the optical-mix test in
`contact_sheet.png` panel 4. (Render cost note: the frame took three
restarts at reduced settings — the VM was running the full ~40-agent
craft wave at load > 25 on 1.5 shared CPUs.)

Honest limits:

- Cards reuse the prototype's strand alpha, whose strands are unusually
  straight/vertical; band phase decorrelation is therefore partly carried
  by jitter noise rather than strand wander. On production grooms the
  effect will be stronger, not weaker.
- The tabby boundary card sweeps melanism *across one card*. In
  production, melanism is sampled per card (or per strand) from the coat
  mask in UV space — the boundary card is a microscope slide of the edge
  mechanism, not the production layout.
- Distance integral is guard-hair only (§4 caveat); no anisotropic
  sheen/backscatter modelling (that's A12's shading brief).
- Tiger ground distance colour (`#5d3f20`) reads darker than a tiger's
  far coat because the real coat's far mix includes its pale zigzag
  undercoat majority — flagged, not fudged.

---

## 7. Sources

- Coats and Colors, "Agouti (aw)" — coatsandcolors.com/agouti — band
  structure, dorsal banding vs solid ventral tan, ASIP promoters.
- Xu et al. 2017, *Cell Research*, "The genetics of tiger pelage color
  variations" — tiger ground hairs agouti with sub-apical pheomelanin
  band, dark tips and bases; stripes uniformly black; CORIN wideband;
  guard vs zigzag underhair composition.
- Kaelin et al. 2012 (*Science*, Taqpep — mackerel vs classic) and
  Kaelin/Barsh 2021 (Dkk4 — ticked prepattern), via secondary summaries.
- Husky/wolf coat references (puppysimply.com husky colours) — banded
  guard hairs + dense undercoat in wolf-type coats.
- House documents: MARKINGS.md §1.1/§4/§6.3, APP_BLUEPRINT.md §9,
  FUR_PROTOTYPE.md §6 (flat single-colour hair = the gap this fills).

*All A11-generated textures are procedural from the cited band
parameters — no third-party texture assets are redistributed.*
