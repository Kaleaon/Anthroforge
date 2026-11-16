# Two-Layer Fur — Guard Hair + Undercoat as Separate Systems

**Learning Agent A16, AnthroForge fur-craft wave, Nov 12, 2026.**
The double coat studied as what it is: **two hair populations with different
jobs, grown by the same follicles, read by the eye as one coat.** This doc
(a) fixes the layer model and its parameter rules, (b) derives per-species
layer parameters for the roster from A19's profiles and A11's colour model,
(c) maps the split onto every implementation family in our stack (strands,
cards, shells, texture), and (d) proves the read on a two-patch prototype —
the same guard groom with and without its undercoat.

Companion data: [`layer_params.json`](layer_params.json) (machine-readable
per-species layer table) · prototype in
[`build_twolayer.py`](build_twolayer.py) / `prototype_twolayer.blend` /
[`renders/`](renders/).

---

## 0. Headline findings

1. **The undercoat is the majority population and the minority surface.**
   Guard hairs are few, long, thick, and carry pattern/sheen/silhouette;
   undercoat hairs are the bulk of the follicle count (tiger ≈ 90% underhairs
   [S, A11 §1.3]), short, fine, crimped, near-solid in colour — and mostly
   invisible until the coat parts, ruffles, gets wet, or is seen at grazing
   range. A fur stack with no undercoat layer reads thin and "wig-like"
   (A11's verdict, confirmed by the prototype below).
2. **The layer split is data, not a universal.** A19's roster spans the full
   range: wolf/bear/St. Bernard run undercoat coverage ratios of 0.85–1.0
   against guard; the badger *inverts* the allocation (0.15–0.4, guard is
   the whole show); the lion runs **zero** undercoat anywhere. Any pipeline
   that always builds two layers wastes the lion's budget and starves the
   wolf's.
3. **One ratio rules the geometry: undercoat length ≈ 0.45–0.6× guard
   length.** The roster's one measured pair — red fox [S]: underfur ~35 mm
   under ~60 mm dorsal guards = 0.58 — and the horse's winter underhair
   (2.2–2.9 cm under a 4.7 cm outer mean = ~0.54) bracket it. Default 0.5.
4. **The undercoat is the seasonal variable.** Per A19: wolf summer
   `undercoat_scale` 0.15, bear 0.25, fox 0.3, horse body underhair absent
   in summer — while guard length/density move far less. A "summer coat"
   is mostly a coat with its underlayer removed; implement seasons as an
   undercoat density/length morph, never a second groom.
5. **Every implementation family has a natural layer split** (§4) — the
   strand groom splits by curve set, cards by a second cheaper card set,
   shells by shell-index range, and A14's texture pelt *already is* the
   two-layer model in pigment (undercoat colour field + guard speckle).
   The layers should be authored once, in the region record, and each
   renderer takes its slice.

---

## 1. The biology in one page

A double coat is two (fox: three) hair populations interleaved on the same
skin, in most carnivores emerging from **compound follicles** — one primary
guard hair with a cluster of finer secondary (undercoat) hairs around it.
The red fox's unit is the cleanest statement of the plan [S, A19 §2]: a
**triad** of 1 guard + 2 intermediate hairs + a bundle of fine awn underfur.

| | Guard hairs | Undercoat (underfur) |
|---|---|---|
| Form | long, straight, thick medulla, stiff | short, fine, often crimped/"zigzag" |
| Share of hairs | minority | **majority** (tiger ≈ 90%) |
| Length | the region's `length_m` (A19) | **0.45–0.6× guard** |
| Radius | reference Ø | ≈ 0.5× guard Ø |
| Colour program | the full band profile — agouti/banded/tipped; this is what pattern is made of (A11) | **near-solid**, bands compressed or absent; often paler or contrasting (fox underfur is grey under rufous guards; wolf undercoat is pale warm grey, A11 distance colour `#9a8d78`) |
| Job | pattern, sheen, silhouette, water/snow shedding, the "lie" of the coat | trapped-air loft (insulation), matte body/depth, and **the colour you see where the coat parts** |
| Behaviour | lies flat in flow lanes, clumps when wet (A17) | stands more upright, collapses/mats when wet, sheds in clumps at the moult |

Two consequences that are easy to miss:

- **Coverage is an undercoat property; appearance is a guard property.**
  A19's density normalisation is anchored on underfur for exactly this
  reason (1.0 = densest winter torso underfur, where the skin cannot be
  found). Skin show-through is what the eye reads as "thin fur," and skin
  show-through is decided by the underlayer, not by adding more guards.
- **The layers age differently.** The undercoat is shed and regrown on the
  moult cycle; guard hairs persist longer. Seasonal states (A19 §0.5) and
  wear states (A17) are therefore *layer-asymmetric*: a state record that
  morphs the whole groom uniformly will get the moult wrong.

## 2. How the layers interact visually

- **Partings and ruffling.** Wherever guard hairs separate — a centre
  parting, a hand or muzzle pushed through, wind lifting the lay, the
  inside of a bend — the visible surface is undercoat: paler, matte,
  unpatterned. This is the single most diagnostic two-layer cue; the
  prototype (§5) is built around it. Guard-only fur parts to *skin*,
  which no real double coat ever shows at prime density.
- **Belly and ventral zones.** Ventral guard profiles are already solid
  pheomelanin with no banding (A11 §1.2, ventral promoter), and the belly
  is where the coat is most often seen *through* (legs part it, the animal
  rolls). Ventral undercoat is correspondingly important out of proportion
  to its length — and on the badger the belly is the inverse case: sparse
  by design, skin visible, because there the *absence* of undercoat is the
  species read.
- **Silhouette.** The guard layer defines the outline (length + lie), but
  the undercoat sets the outline's *softness*: crimped underfur pokes
  between guard tips and breaks the edge into fuzz. At the silhouette the
  two layers trade places — the outermost visible hairs at a rim are
  disproportionately undercoat tips and guard side-profile.
- **Grazing angles.** At glancing view the layered depth compresses and
  the eye integrates more of the underlayer (A11 §2.3: coat-level mixes
  "also mix the undercoat where the coat parts and at grazing angles").
  This is why A11's shell rule assigns inner shells the *undercoat*
  distance colour — a distance/grazing representation should carry the
  underlayer's integral, not the guard's.
- **Wet.** Water clumps the guard layer into spikes and collapses the
  undercoat's loft (A17: wet is a parameter morph over one groom). The
  wet read — dark, spiky, body form showing through — is the two layers
  failing in opposite directions; a one-population groom can only fake
  half of it.
- **Colour at distance.** Far colour is a population mix: A11's measured
  wolf integrals put guard at `#76634a` and undercoat at `#9a8d78`-family
  pale grey — a coat's distance colour is *lighter and greyer* than its
  guard profile alone predicts, by an amount set by the undercoat's
  show-through fraction. Species whose undercoat contrasts hard (fox:
  grey under rufous) shift hue, not just value, at partings and distance.

## 3. Per-species layer parameters

Derived from A19's layer extensions (density ratios, sourced lengths) and
A11's profiles (layer colours); full machine-readable table in
[`layer_params.json`](layer_params.json). Lengths are torso values;
ratios marked [S] are sourced, [E] are estimates ordered to agree.

| Species | Structure | Undercoat density (rel. guard) | Undercoat length | Undercoat colour | The layer story |
|---|---|---|---|---|---|
| Wolf | double | 1.0 back / 0.95 ruff / 0.3 muzzle / 0.25 hands-feet | ~0.030 m [E] (0.46×) | pale warm grey `#9a8d78`, solid | the reference double coat; summer scale 0.15 |
| Red fox | double — **triads (3 populations)** | 1.0 back / 0.9 front / 0.3 muzzle | **0.035 m [S] (0.58×)** | grey, solid | guard + intermediate + awn bundle per follicle; the intermediate hairs are a real third layer |
| Fennec | double | 0.95 torso / 0.1 ears.inner / 0.7 soles | ~0.019 m [E] (0.54×) | cream-white, solid | insulation both ways in the desert; ear lining is single-layer, soles are furred — both exceptions live in the layer data |
| Lion | **single** | **0.0 everywhere** | — | — | the control case: all information is guard-class (body + mane); spend nothing on a second layer |
| Bear | double | 1.0 back / 0.9 ruff / 0.3 muzzle | ~0.052 m [E] (0.5×) | grey-brown wool, solid | loft engine under long guards; the famous grizzle is guard *tipping*, not undercoat; summer scale 0.25 |
| Badger | double-sparse, **inverted** | 0.35 back / 0.15 belly & muzzle | ~0.035 m [E] (0.45×) | pale, solid | guard is the show layer and the silhouette; belly sparse by design — undercoat geometry is unjustified, texture-floor only |
| St. Bernard | double | 0.95 torso / 0.85 scalp / 0.4 muzzle | ~0.024 m [E] (0.5×) | follows patch colour, solid | bred plan: "short, very dense, soft" undercoat [S]; smooth/rough variety changes lengths, never the layer plan |
| Clydesdale | single (summer) / double (winter, body only) | 0.4 winter body / **0.0 mane, tail, feather, forelock always** | **0.022–0.029 m [S] (~0.54×)** | follows body colour | not the carnivore plan: a seasonal underhair under body coat only; the identity hair systems never grow an underlayer |

**Reading the table as rules:**
- The undercoat *density ratio* is a coverage dial (A19 §0.4), not a strand
  count. Undercoat strands are ~half guard radius, so a groom or card set
  needs a strand-count ratio of roughly **2.5–4×** the guard count to
  deliver a coverage ratio near 1.0.
- Where the ratio is ≥ 0.85 **and** guard length ≥ 25 mm, the underlayer is
  a visible surface in its own right (partings, bends, belly) — it earns
  geometry. Where guard length < 15 mm, no camera resolves two populations
  — the layer split belongs in texture/shell tint only (§4).
- Fox is the standing warning against over-fitting the model: a strict
  two-layer record *simplifies* the triad. The record (§6) therefore
  allows an optional `intermediate` population; fox uses it, nobody else
  on the roster does.

## 4. Implementation options for our stack

One authoring source — the region record carries both populations
(A11 §3 already splits `colour.guard` / `colour.undercoat`; §6 below adds
the layer geometry fields) — and each renderer takes its slice:

### 4.1 Strand groom (hero / authoring master) — split by curve set
Two curve sets per region, sharing A7's `FURP_` paintmaps and flow field:
the guard set as today, plus an undercoat set at 2.5–4× strand count,
0.5× length, 0.5× radius, high crimp, near-flat colour ramp. This is a
per-region checkbox on the existing region-split architecture (A3's
Geometry-Nodes verdict, A7's converter), not new machinery — the undercoat
set can even reuse the guard set's guide field at higher child density.
Cost: +40–60% strand count but at ~half the segments per strand; the
undercoat set is also the first thing a groom LOD drops. States (A17)
need a layer dimension: wet/matted deltas are layer-asymmetric by
construction (§2).

### 4.2 Cards (the shipping LOD0/LOD1 technique) — two card sets
Per A11 §2.3: **undercoat cards (short, dense, wavy) under guard cards
(banded atlas)**. A8 already baked the undercoat card texture
(`card_wolf_undercoat.png`, its own short wavy strand alpha), so the
split costs art nothing — it costs placements. Rules:
- Undercoat cards sit 2–4 mm *below* the guard card surface, are smaller,
  and can use the cheap alpha (near-solid colour, no banding detail).
- Both sets merge into the one card mesh / one atlas material (A5: fur
  draw calls stay at 1; A13's atlas gains an undercoat row set).
- LOD descent spends the undercoat first: LOD1 halves undercoat
  placements, LOD2 removes them — their information folds into the
  texture floor's root colour (§4.4), exactly the A5 ladder
  (cards → texture-only + silhouette cards). Silhouette cards are always
  guard cards; undercoat cards never carry silhouette.

### 4.3 Shells (short-fur zones) — split by shell index
Shells are already a radial stack, so the layer split is a *tint split*:
inner shells sample the undercoat distance colour, outer shells the
coat-level composite (A11 §2.3's rule). Within A5's ≤8 interactive shell
cap, a double coat spends roughly the inner 40% on undercoat (e.g. 3 of
8). Best fit where guard length is 6–15 mm — too long for pure texture,
too short for cards to resolve two populations. A14's shell caveats
(overdraw, medium-distance alpha-stack failure) apply unchanged.

### 4.4 Texture-only (the floor, and short coats entire) — already two-layer
A14's verdict was that short fur is a two-layer answer, and its T3 pelt
*is* the two-layer model in pigment: base fill = undercoat distance
colour (the root field), directional strokes on top = guard speckle,
root AO gradient selling the depth. Every LOD chain bottoms out here:
at LOD2/impostor and on all sub-10 mm zones, the double coat is a
two-tone texture construction, and the undercoat's only parameters are
its distance colour and the root-gradient depth. Getting the root colour
from the *undercoat profile* (not from darkening the guard colour) is
the whole trick — a darkened-guard root reads as dirt; the real
undercoat root reads as depth.

### 4.5 Decision table (per region)

| Undercoat ratio | Guard length | Treatment |
|---|---|---|
| ≥ 0.7 | ≥ 25 mm | **true two-layer geometry** — strand split (hero) / two card sets (LOD0–1) |
| ≥ 0.7 | 6–25 mm | shells split by index, or cards + texture floor doing the underlayer |
| ≥ 0.7 | < 6 mm | texture-only two-tone (A14 stack) |
| 0.3–0.7 | any | guard geometry + texture floor with true undercoat root colour (partings read via texture; geometry underlayer not worth it) |
| < 0.3 or `single` | any | single layer; lion/badger-belly rule — spend nothing |

Platform notes: Babylon/Mini App take the card route with the LOD
descent above (A5 budgets: fur ≤ 24k tris high tier, 1 draw call) — the
undercoat card set is inside that budget only if LOD1 sheds it as
specified. SL takes the same descent across its 4 LOD slots; shells are
effectively unusable in SL (A5), so SL double coats are cards over the
two-tone texture floor.

## 5. Prototype — one patch, with and without its undercoat

**Setup.** A wolf `torso.back` flank patch (0.52 × 0.38 m dome, dark skin)
built as scripted hair curves (Blender 5.2.3, Cycles, flat studio world,
key/fill/rim areas, 720², 64 samples, `--threads 2`). The guard groom was
generated **once** and instanced onto both patches unchanged — 2,200 guard
strands, 70 mm, A11's agouti band profile (root `#38312b` → pulses
`#a97e4f`/`#d9c49a` → tip `#201c19`), exit angle 30° easing to −6° (the
low shingled lie). Patch B adds the undercoat: 5,481 strands (2.5× the
guard count), 30 mm (0.43× length), half radius, crimped (2.2 cycles,
1.6 mm amplitude), exit 58°→12°, near-solid pale warm grey. A 40 mm
centre **parting band carries no guard roots on either patch** — the
guards lean away from it (parting-aware flow) — so the band is a
controlled window into what each stack shows when a coat is opened.
Renders: `renders/{guardonly,twolayer}_{close,medium,grazing}.png`.

**What the renders show** (judged on the frames):

- **Close, the parting.** Guard-only: the parting is a *runway of bare
  dark skin* — clean, hard-edged, unambiguous, and exactly what a prime
  double coat never does (renders/guardonly_close.png). Two-layer: the
  runway is gone as a clean shape — the band floor is a thin grey mat
  with pale crimped wisps standing in it, and guard tips lean over it
  (renders/twolayer_close.png). The direction is right and the mechanism
  is proven, but honestly: **the mat is thinner than a real prime coat**
  — at this magnification you can still find skin between undercoat
  strands, where a real wolf parting finds none. Cause is parametric,
  not structural: 2.5× count ratio is the bottom of the §3 band, the
  undercoat's 58° exit still lies too flat to mat, and 0.4 mm root radius
  is fine even for underfur at this zoom. Production values: count ratio
  3.5–4×, exit ~70°, radius +25%.
- **Medium, the whole coat.** This is the unambiguous frame. Guard-only
  reads as a sleek pelt of distinct strands over visible skin gaps —
  good fur, slightly *wig-like* at the parting, exactly A11's predicted
  failure. Two-layer reads **denser, matter, and greyer**: the undercoat
  fills the inter-guard space everywhere (not just the parting), the
  surface texture goes finer, and the far colour shifts toward the
  undercoat's pale grey — the population-mix effect of §2, visible
  without instrumentation. The top rim softens: guard-only ends in a
  clean line of separate tips; two-layer ends in fuzz.
- **Grazing.** Guard-only: sparse guard arcs over an empty dark dome —
  at grazing range the coat nearly *evaporates*, leaving skin and hoops.
  Two-layer: a continuous pale mat under the guard canopy; the parting
  becomes a shallow valley in a filled surface instead of a gap to
  skin. This is the grazing-angle undercoat show-through A11's shell
  rule encodes, here in geometry.
- **Cost.** Same scene, same machine: guard-only frames rendered in
  3:07 / 5:18 / 6:30 (close/medium/grazing); two-layer in 10:56 /
  13:42 / 15:24 — the undercoat roughly **doubles to triples strand-
  render time** at 2.5× count and half segments. Offline that's a
  fine trade; it is also the quantitative reason §4 sheds the undercoat
  first on every real-time LOD descent.

**Verdict.** The two-layer split is not a polish item; at partings, at
grazing angles, and in distance colour it is the difference between a
coat and a wig. Author both populations wherever the species data says
they exist (§3), at count ratio ≥ 3.5× for hero work, and let each
renderer take its slice (§4).

## 6. Record extension (proposal, extends A19 §0.4 + A11 §3)

A19's `layer` object already carries `structure` and the `undercoat`
coverage ratio. A16 adds the minimum geometry/colour fields a consumer
needs to *build* the second population, per region:

```json
"layer": {
  "structure": "double",                 // A19: single|double|double-sparse|mane-hair
  "undercoat": 1.0,                      // A19: coverage ratio vs guard density
  "undercoat_length_m": 0.030,           // absolute, or derive: guard length x ratio
  "undercoat_length_ratio": 0.46,        // keep both honest — sourced pairs win
  "undercoat_colour": {"pattern": "solid", "bands": [ … ]},  // A11 profile shape
  "intermediate": null                   // fox triads only: {length_ratio, density}
}
```

Rules: (1) `undercoat_melanism_strength` stays 0.45 (A11) — markings
reprogram the undercoat at reduced strength, never full. (2) Seasonal
states scale `undercoat` (density) and `undercoat_length_m` via A19's
`undercoat_scale`; guard fields are not seasonal except where A19's
`len S` says so. (3) `structure: "single"` means the undercoat fields
must be absent/zero — a lion record carrying an undercoat block is a
data error, and consumers should treat it as one.

## 7. Honest limits

- **One species, one region, one groom.** The prototype is wolf
  torso.back only. Badger (inverted) and fox (triad) layer behaviour
  are argued from A19/A11 data, not rendered; the intermediate fox
  population exists in the record proposal but was not prototyped.
- **The undercoat mat is under-dense** at close range (see §5) — the
  comparison proves the mechanism and the direction of every effect,
  but the absolute coverage of patch B's parting is ~half of prime-coat
  real. The fix is parametric and listed; it was not re-rendered.
- **Stylised strand scale.** Prototype strands are ~0.75 mm root radius
  — several real hairs wide. This is the wave's house stylisation (A7's
  grooms use the same order), fine for layer *interaction* claims, not
  for absolute density claims: real follicle counts are far higher and
  are what A19's normalised density abstracts.
- **No dynamics.** Layers are static here; how the two populations
  separate under motion/wind (guard lifts, undercoat stays) is A17/A6
  territory and untested for the split groom.
- **Colour carried as melanin ramps.** Per A7's verified route, banding
  is value banding under one tint per layer; A11's shaft atlas carries
  full per-band colour and is the production path for cards/strands
  that need hue-accurate bands.
- **Render times are this-VM numbers** (1.5 CPU quota, shared) — the
  ~2–3× undercoat cost ratio is the portable figure, not the minutes.

