# Species Fur Profiles — SPECIES_FUR.md

**Learning Agent A19, AnthroForge fur-craft wave, Nov 12, 2026.**
Real pelage of the roster species, expressed in exactly the parameter shape the fur
region-map system consumes (APP_BLUEPRINT §9.5 + the markings/fur shared region
vocabulary). Owl is excluded by brief — feathers are not a fur analog here.

---

## 0. How to read this document

### 0.1 Region vocabulary (canonical, do not invent new names)

Rows in every table are the shared regions from APP_BLUEPRINT §9.5 and MARKINGS.md §3:
`scalp`, `muzzle`, `cheeks`, `ruff` (ruff/neck), `ears.inner`, `ears.back`,
`torso.front`, `torso.back`, `arms`, `legs`, `pelvis`, `tail`, `hands`, `feet`.
The blueprint writes `hands/feet` combined; the markings vocabulary separates them,
so they are separate rows here — a consumer that wants the combined region takes the
mean. Two species need one *subzone note* on top of a canonical region, never a new
region: the lion/horse **mane** is `ruff` + `scalp` at hair-style parameters (§9.1 of
the blueprint already rules this: mane = fur profile, not a special mesh), and the
Clydesdale **feather** is `legs`/`hands`/`feet` distal at hair-style parameters.

### 0.2 Parameter columns (the §9.5 `fur_region` record, verbatim)

| Column | Field | Meaning |
|---|---|---|
| `density` | `density` | 0.0–1.0, strands/cm² **normalised** (see 0.3) |
| `len W` | `length_m` | Guard-hair length, **winter/prime coat**, metres — the shipped default |
| `len S` | seasonal override | Guard-hair length, summer coat, metres (`—` = no meaningful seasonal change) |
| `var` | `length_variation` | 0.0–1.0 |
| `curl` | `curl` | 0.0–1.0 |
| `clump` | `clump` | 0.0–1.0 |
| `frizz` | `frizz` | 0.0–1.0 |
| `layer` | extension §0.4 | Guard/undercoat structure of that zone |

### 0.3 Tags and the density normalisation

- **[S]** = sourced (citation in §10). **[E]** = estimate — a design value set by me,
  ordered to agree with the sourced qualitative facts, with **no direct measurement
  behind it**. Estimates are never dressed as measurements.
- Published hairs/cm² counts essentially do not exist for these species by body zone,
  so **every `density` value is [E]** — but the *ordering* between zones and species
  follows sourced descriptions ("sparse, skin visible" vs "so thick skin cannot be
  found"). Normalisation anchor [E]: **1.0 ≈ the densest winter torso underfur on
  this roster** (wolf/fox prime winter back, where the undercoat hides the skin
  completely); 0.5 ≈ a coat you can part to skin with effort; 0.15 ≈ sparse, skin
  shows through at rest. Blueprint §9.1's three reads sanity-check the scale: body
  hair 5–30 mm low/patchy, full fur 20–120 mm high/continuous, hair styles
  50–600 mm very high/groomed.
- `var/curl/clump/frizz` are **[E] throughout**, translated from sourced texture
  words: *coarse/bristly* → low clump, moderate frizz, strand stiffness high;
  *woolly underfur* → high frizz in the underlayer only (the visible guard layer
  stays low-frizz); *sleek/close-lying* → low everything. Where a texture word is
  sourced, it is quoted in the species notes.
- Lengths are **guard-hair** lengths unless the layer column says otherwise;
  underfur length is given in the layer column where sourced.

### 0.4 The `layer` extension

§9.5 has no layer field, but "undercoat presence" was explicitly requested, so each
profile carries one extension object per region, kept out of the core record:

```json
"layer": { "structure": "double",           // single | double | double-sparse | mane-hair
           "undercoat": 0.85,                // 0-1 undercoat density relative to that zone's guard density [E]
           "undercoat_length_m": 0.030,      // where sourced, else omitted
           "note": "woolly, grey" }
```

### 0.5 Seasonal model

Default profile = **winter/prime** (that's when these coats are themselves). The
summer state is *not* a second profile: it is `len S` per row + two global scalars
per species in its JSON block (`seasonal.summer.density_scale`,
`seasonal.summer.undercoat_scale`). One spring moult, undercoat shed in clumps, is
the mechanism for every double-coated species here except the horse (own pattern,
§8) and the lion/fennec (weak seasonality).

---

## 1. Wolf — *Canis lupus* → profile `species.wolf.coat`

**Layer structure [S]:** classic northern double coat — long, coarse guard hairs
over a short, dense, soft undercoat. Most of the undercoat and some guard hair is
shed in spring and regrown in autumn; winter fur resists −40 °C exposure. In warm
climates the coat is "coarser and scarcer" and some populations skip the undercoat —
for our purposes the northern winter animal is the reference.

**Zonal facts [S]:** "The longest hairs occur on the back, particularly on the front
quarters and neck. Especially long hairs grow on the shoulders and almost form a
crest on the upper part of the neck. The hairs on the cheeks are elongated and form
tufts. The ears are covered in short hairs… Short, elastic and closely adjacent
hairs are present on the limbs from the elbows down to the calcaneal tendons."
Measured: mid-back hair 60–70 mm; shoulder guard hairs generally ≤ 90 mm, reaching
110–130 mm; total winter coat thickness up to ~2.5 in (≈ 63 mm) of loft. Guard
hairs are **banded** (agouti) — the grizzled grey-brown read *is* the banding.

| region | density | len W (m) | len S (m) | var | curl | clump | frizz | layer |
|---|---|---|---|---|---|---|---|---|
| scalp | 0.75 [E] | 0.055 [E] | 0.030 [E] | 0.3 | 0.05 | 0.30 | 0.25 | double, undercoat 0.7 |
| muzzle | 0.55 [E] | 0.018 [E] | 0.012 [E] | 0.25 | 0.0 | 0.15 | 0.15 | double-sparse, undercoat 0.3; whisker field is a part, not fur |
| cheeks | 0.80 [E] | 0.075 [S: elongated tufts] | 0.040 [E] | 0.35 | 0.05 | 0.45 | 0.30 | double, undercoat 0.75 |
| ruff | 0.95 [E] | 0.115 [S: shoulder guards to 0.11–0.13] | 0.055 [E] | 0.35 | 0.10 | 0.65 | 0.35 | double, undercoat 0.95 — the neck **crest** lives here |
| ears.inner | 0.45 [E] | 0.020 [E] | 0.015 [E] | 0.3 | 0.0 | 0.20 | 0.30 | single-ish, undercoat 0.2; pale |
| ears.back | 0.70 [E] | 0.030 [S: ears short-haired] | 0.020 [E] | 0.25 | 0.0 | 0.25 | 0.25 | double-sparse, undercoat 0.5 |
| torso.front | 0.90 [E] | 0.075 [E] | 0.035 [E] | 0.3 | 0.05 | 0.45 | 0.30 | double, undercoat 0.9 |
| torso.back | 1.00 [E anchor] | 0.065 [S: mid-back 0.06–0.07] | 0.032 [E] | 0.3 | 0.05 | 0.40 | 0.30 | double, undercoat 1.0 |
| arms | 0.80 [E] | 0.045 [E] | 0.025 [E] | 0.3 | 0.05 | 0.35 | 0.30 | double, undercoat 0.8 |
| legs | 0.75 [E] | 0.040 [E] | 0.022 [E] | 0.3 | 0.05 | 0.35 | 0.30 | double, undercoat 0.75 |
| pelvis | 0.90 [E] | 0.070 [E] | 0.035 [E] | 0.3 | 0.10 | 0.45 | 0.35 | double, undercoat 0.9 |
| tail | 0.95 [E] | 0.085 [E] | 0.050 [E] | 0.35 | 0.10 | 0.55 | 0.35 | double, undercoat 0.95 — bushy, carried loft |
| hands | 0.50 [E] | 0.015 [S: limbs short/close below elbow] | 0.010 [E] | 0.25 | 0.0 | 0.15 | 0.20 | double-sparse, undercoat 0.25 |
| feet | 0.50 [E] | 0.015 [S] | 0.010 [E] | 0.25 | 0.0 | 0.15 | 0.20 | double-sparse, undercoat 0.25; interdigital hair present, pads bare |

**Colour function:** root dark grey-brown → mid band cream → tip black =
`pattern: "agouti"` on torso/ruff/tail; underside trends pale (markings L0
countershade, not this profile). **Seasonal scalars [E]:** summer
`density_scale 0.55`, `undercoat_scale 0.15` (undercoat essentially gone; summer
wolves look leggy and narrow-headed precisely because this coat is gone [S]).

**Prototype cross-check:** the fur prototype's wolf groom (ruff 0.170 m / back
0.095 / belly 0.042 / coat 0.066) runs *long* against these sourced values —
ruff 0.17 m is ~1.5× the real shoulder maximum. That's a bara stylisation choice,
not an error, but the species default should ship the table above; keep the
prototype values as an "exaggerated" variant.

---

## 2. Red fox — *Vulpes vulpes* → profile `species.red_fox.coat`

**Layer structure [S]:** three hair types, not two — fine awn **underfur**,
**intermediate** hairs, and long coarse **guard hairs**, arranged in follicle
**triads** (1 guard + 2 intermediate + a bundle of awns). Underfur covers sides and
back, is **~35 mm** long and grey. Guard hairs are longest on the tail; a measured
dorsal series gives mean longest guard hairs ≈ **60 mm**. One moult per year: thin
summer coat shed late summer, winter coat (dense underfur + longer guards) grows
in over autumn, photoperiod-driven. Winter coat makes the animal look visibly
bulkier — most of the bulk is trapped air, not body.

**Distinctive structures [S]:** the **brush** (tail) is the longest-furred zone on
the animal; black ear-backs and black lower legs ("stockings") are markings-layer
colour on ordinary-length fur, *not* different fur; white tail tip likewise.

| region | density | len W (m) | len S (m) | var | curl | clump | frizz | layer |
|---|---|---|---|---|---|---|---|---|
| scalp | 0.70 [E] | 0.040 [E] | 0.022 [E] | 0.3 | 0.05 | 0.30 | 0.30 | double (triad), undercoat 0.7 |
| muzzle | 0.50 [E] | 0.014 [E] | 0.010 [E] | 0.25 | 0.0 | 0.15 | 0.20 | double-sparse, undercoat 0.3 |
| cheeks | 0.75 [E] | 0.050 [E] | 0.028 [E] | 0.3 | 0.05 | 0.40 | 0.30 | double (triad), undercoat 0.8 |
| ruff | 0.85 [E] | 0.060 [E] | 0.032 [E] | 0.3 | 0.05 | 0.50 | 0.35 | double (triad), undercoat 0.9 — fuller neck in winter [S] |
| ears.inner | 0.40 [E] | 0.018 [E] | 0.012 [E] | 0.3 | 0.0 | 0.20 | 0.30 | sparse pale fringe, undercoat 0.15 |
| ears.back | 0.70 [E] | 0.028 [E] | 0.018 [E] | 0.25 | 0.0 | 0.25 | 0.25 | double-sparse, undercoat 0.5; black (markings) |
| torso.front | 0.85 [E] | 0.048 [E] | 0.026 [E] | 0.3 | 0.05 | 0.40 | 0.30 | double (triad), undercoat 0.9, underfur ≈0.035 [S] |
| torso.back | 0.95 [E] | 0.060 [S: dorsal guard mean ≈0.060] | 0.030 [E] | 0.3 | 0.05 | 0.40 | 0.30 | double (triad), undercoat 1.0 |
| arms | 0.70 [E] | 0.035 [E] | 0.020 [E] | 0.3 | 0.0 | 0.30 | 0.30 | double (triad), undercoat 0.7 |
| legs | 0.65 [E] | 0.032 [E] | 0.018 [E] | 0.3 | 0.0 | 0.30 | 0.30 | double (triad), undercoat 0.65; black stockings (markings) |
| pelvis | 0.85 [E] | 0.055 [E] | 0.028 [E] | 0.3 | 0.05 | 0.45 | 0.35 | double (triad), undercoat 0.9 |
| tail | 0.95 [E] | 0.085 [E: longest zone, S-ordering] | 0.050 [E] | 0.35 | 0.10 | 0.55 | 0.35 | double (triad), undercoat 0.95 — the brush |
| hands | 0.45 [E] | 0.012 [E] | 0.009 [E] | 0.25 | 0.0 | 0.15 | 0.20 | double-sparse, undercoat 0.25 |
| feet | 0.45 [E] | 0.012 [E] | 0.009 [E] | 0.25 | 0.0 | 0.15 | 0.20 | double-sparse, undercoat 0.25 |

**Colour function:** guards rufous with pale banding → `pattern: "banded"`;
underfur grey (visible when the coat parts — root colour in the record should be
the grey, tip the rufous). **Seasonal scalars [E]:** summer `density_scale 0.6`,
`undercoat_scale 0.3`; summer coat also *sleeker/brighter* (colour note, markings
owns it).

---

## 3. Fennec — *Vulpes zerda* → profile `species.fennec.coat` (Pyn)

**Layer structure [S]:** the desert inversion of the fox plan. Coat described
across sources as **long, soft, thick/dense**, cream to pale reddish-sand above,
white below; a thick multi-layered coat whose outer layer reflects sun and whose
**dense undercoat** insulates against cold desert nights. Seasonality is weak —
the Sahara problem is a daily, not annual, temperature swing, so there is no
dramatic summer/winter pair; treat as a single year-round coat.

**Distinctive structures [S] — two are unique on this roster:**
1. **Ear inners lined with long white hair** (sand exclusion) on ears up to
   10–15 cm — `ears.inner` is a *high*-coverage zone here, the opposite of the wolf.
2. **Soles densely furred** — `feet` (including the pad surface, which no other
   roster species furs) carries real density: heat shield + traction on loose sand.
   In region terms the foot's *ventral* subzone breaks the "pads bare" rule every
   other profile follows; flag it in the groom guides, not as a new region.
Also: black tail tip (markings), dark eye-streak (markings).

| region | density | len W (m) | len S (m) | var | curl | clump | frizz | layer |
|---|---|---|---|---|---|---|---|---|
| scalp | 0.80 [E] | 0.030 [E] | — | 0.3 | 0.05 | 0.30 | 0.40 | double, undercoat 0.8 — soft/silky read |
| muzzle | 0.55 [E] | 0.012 [E] | — | 0.25 | 0.0 | 0.15 | 0.25 | double-sparse, undercoat 0.35 |
| cheeks | 0.80 [E] | 0.035 [E] | — | 0.3 | 0.05 | 0.35 | 0.40 | double, undercoat 0.85 |
| ruff | 0.85 [E] | 0.038 [E] | — | 0.3 | 0.05 | 0.40 | 0.40 | double, undercoat 0.9 |
| ears.inner | 0.75 [E] | 0.030 [S: long white ear lining] | — | 0.35 | 0.0 | 0.25 | 0.45 | single layer of long fine hair, undercoat 0.1; white |
| ears.back | 0.75 [E] | 0.022 [E] | — | 0.3 | 0.0 | 0.25 | 0.35 | double-sparse, undercoat 0.5 |
| torso.front | 0.90 [E] | 0.032 [E] | — | 0.3 | 0.05 | 0.35 | 0.40 | double, undercoat 0.95; white |
| torso.back | 0.90 [E] | 0.035 [E] | — | 0.3 | 0.05 | 0.35 | 0.40 | double, undercoat 0.95 |
| arms | 0.75 [E] | 0.024 [E] | — | 0.3 | 0.0 | 0.30 | 0.35 | double, undercoat 0.75 |
| legs | 0.75 [E] | 0.024 [E] | — | 0.3 | 0.0 | 0.30 | 0.35 | double, undercoat 0.75 |
| pelvis | 0.85 [E] | 0.034 [E] | — | 0.3 | 0.05 | 0.40 | 0.40 | double, undercoat 0.9 |
| tail | 0.90 [E] | 0.045 [E] | — | 0.35 | 0.05 | 0.50 | 0.40 | double, undercoat 0.9 — bushy, black tip (markings) |
| hands | 0.55 [E] | 0.012 [E] | — | 0.25 | 0.0 | 0.20 | 0.30 | double-sparse, undercoat 0.4 |
| feet | 0.80 [E] | 0.018 [S: soles densely furred] | — | 0.3 | 0.0 | 0.30 | 0.40 | double, undercoat 0.7 — **covers the pads** (see note 2) |

**Colour function:** near-uniform pale sand, root cream → tip pale reddish-sand =
`pattern: "tipped"` (very low contrast); belly/face white is L0 countershade.
**Seasonal scalars:** none (both 1.0). **Scale warning:** absolute lengths are
small-animal lengths; on an anthro fennec at human scale the *relative* pattern
(dense, soft, ear-lining, furred soles) is the species signal — scale lengths with
the character, keep densities.

---

## 4. Lion — *Panthera leo* → profile `species.lion.coat` (Kaleaon)

**Layer structure [S]:** the anti-wolf. Body pelage is **short** — "short hair on
face, upper body, flanks, and tail; longer hair on underparts" — a single effective
layer with no insulation undercoat worth modelling (tropical savanna). All of the
species' fur information is in **one sexually dimorphic hair-style system: the
mane** — plus three minor tuft systems. Females and juveniles: body coat only.

**The mane [S]:** male-only, testosterone-driven, begins ~1 yr, full ~4–5 yr.
Covers **head, neck, chest, elbows, and sometimes belly** — in region terms:
`scalp` (top/back), `cheeks`, `ruff` at full extent, `torso.front` upper, `arms`
proximal (elbow tufts), occasionally a `torso.front`→`pelvis` ventral fringe and a
lateral armpit→groin band. Length: **up to 16 cm** (Wilson & Mittermeier via San
Diego Zoo fact sheet); Barbary/Atlas specimens measured **mane hair 8–22 cm**;
captive/cool-climate manes run longer and darker, hot-climate manes shorter,
lighter, sometimes near-absent (Tsavo/Pendjari). Mane colour darkens with age and
testosterone and is a fitness signal — a *character* parameter, not a species
constant: expose mane length/darkness as per-character overrides on `ruff`.
**Tail tuft [S]:** dark, present in both sexes, develops from ~5.5 months.
**Cub rosettes** are markings (L1, age-faded) over this coat, already specced in
MARKINGS.md §4.

Body-coat rows below are the same for both sexes; the mane rows are the **male
default** — female profile = mane rows set to the body values.

| region | density | len W (m) | len S (m) | var | curl | clump | frizz | layer |
|---|---|---|---|---|---|---|---|---|
| scalp | 0.95 [E] ♂mane | 0.16 [S: mane to 0.16] | — | 0.4 | 0.15 | 0.60 | 0.45 | mane-hair (single, coarse), undercoat 0 |
| muzzle | 0.45 [E] | 0.008 [E] | — | 0.25 | 0.0 | 0.10 | 0.15 | single, undercoat 0 |
| cheeks | 0.95 [E] ♂mane | 0.15 [E] | — | 0.4 | 0.15 | 0.60 | 0.45 | mane-hair — the "tanks"/sideburn masses |
| ruff | 1.00 [E] ♂mane | 0.16 [S] (Barbary to 0.22 [S]) | — | 0.4 | 0.15 | 0.65 | 0.45 | mane-hair, undercoat 0 — fullest at neck/shoulders, thins down the chest |
| ears.inner | 0.30 [E] | 0.010 [E] | — | 0.3 | 0.0 | 0.15 | 0.25 | single sparse |
| ears.back | 0.55 [E] | 0.014 [E] | — | 0.25 | 0.0 | 0.20 | 0.20 | single; dark ear-back + pale patch (markings) |
| torso.front | 0.60 [E] (♂ upper 0.85 mane fringe) | 0.018 [E]; ♂ chest fringe 0.10 [E] | — | 0.3 | 0.05 | 0.30 | 0.25 | single, undercoat 0; underparts longer than back [S-ordering] |
| torso.back | 0.60 [E] | 0.014 [E] | — | 0.25 | 0.05 | 0.25 | 0.20 | single, undercoat 0 |
| arms | 0.55 [E] (♂ elbow tuft 0.80) | 0.014 [E]; elbow tuft 0.07 [E] | — | 0.3 | 0.05 | 0.30 | 0.25 | single |
| legs | 0.55 [E] | 0.013 [E] | — | 0.25 | 0.05 | 0.25 | 0.20 | single |
| pelvis | 0.60 [E] | 0.016 [E] | — | 0.3 | 0.05 | 0.30 | 0.25 | single |
| tail | 0.55 [E] shaft / tuft 0.90 [E] | 0.012 shaft; tuft 0.06 [E] | — | 0.35 | 0.05 | 0.20 shaft / 0.55 tuft | 0.25 | single; **dark terminal tuft is a structure, not just colour** |
| hands | 0.45 [E] | 0.010 [E] | — | 0.25 | 0.0 | 0.15 | 0.20 | single |
| feet | 0.45 [E] | 0.010 [E] | — | 0.25 | 0.0 | 0.15 | 0.20 | single |

**Colour function:** body `pattern: "solid"` tawny, root≈tip; mane root tawny →
tip dark brown/black = `"tipped"` with the contrast as a character dial (age/
testosterone proxy). **Seasonal scalars:** none meaningful in the wild range;
captive cool-climate mane extension is an override, not a season.

**Kaleaon note:** his coat is lion geometry with snow-leopard *pattern* (markings
L1 rosettes) and a white ground — the fur *parameters* are this table; only the
colour function and markings change.

---

## 5. Bear — brown bear *Ursus arctos*, with moon-bear blend notes → profile `species.bear.coat` (Sen)

**Layer structure [S]:** double — "a dense woolly underfur for insulation and long,
coarse guard hairs that shed water and snow." Heavy late-spring moult; the summer
coat is "notably thinner and shabbier." Winter fur is longest at the **withers:
11–12 cm** in northern subspecies; guard hairs generally run 3–4 in (7.5–10 cm).
Guard colour is famously **grizzled** — pale/silver tips over a darker base — which
is a tipping pattern, lighter legs/hump in some animals almost black.

**Sen is a grizzly × moon bear blend**, so two sourced moon-bear (*U. thibetanus*)
facts override the brown-bear defaults where they apply:
- **Ruff/mane:** Asiatic black bears carry "long, coarse neck and shoulder hair
  forming a modified mane" — a ruff of up to **~15 cm** framing neck and shoulders,
  heavier than any brown-bear zone. → Sen's `ruff` takes the moon-bear values.
- **Chest crescent:** the pale V/crescent is a **fur-colour zone** (markings L1 via
  the fur colour function, per the Titan preset: pale fur, never a tattoo) sitting
  on `torso.front` — it does not change fur length/density.
- Moon-bear body coat is glossy black and "thicker around the shoulders than
  elsewhere"; Sen's brown-bear grizzle wins on colour, moon bear wins on ruff.

| region | density | len W (m) | len S (m) | var | curl | clump | frizz | layer |
|---|---|---|---|---|---|---|---|---|
| scalp | 0.75 [E] | 0.055 [E] | 0.035 [E] | 0.3 | 0.10 | 0.35 | 0.35 | double, undercoat 0.75 |
| muzzle | 0.50 [E] | 0.016 [E] | 0.012 [E] | 0.25 | 0.0 | 0.15 | 0.20 | double-sparse, undercoat 0.3 |
| cheeks | 0.80 [E] | 0.070 [E] | 0.042 [E] | 0.3 | 0.10 | 0.45 | 0.40 | double, undercoat 0.8 |
| ruff | 0.95 [E] | **0.15 [S: moon-bear ruff to ~0.15]** (brown-only: 0.115 [S withers 0.11–0.12]) | 0.075 [E] | 0.35 | 0.15 | 0.60 | 0.45 | double, undercoat 0.9 — mane-like collar |
| ears.inner | 0.40 [E] | 0.018 [E] | 0.012 [E] | 0.3 | 0.0 | 0.20 | 0.30 | sparse, undercoat 0.2; ears small/round, half-buried in ruff |
| ears.back | 0.70 [E] | 0.030 [E] | 0.020 [E] | 0.25 | 0.05 | 0.30 | 0.30 | double, undercoat 0.6 |
| torso.front | 0.90 [E] | 0.085 [E] | 0.048 [E] | 0.3 | 0.10 | 0.45 | 0.40 | double, undercoat 0.95 — crescent zone = colour only (moon blend) |
| torso.back | 0.95 [E] | 0.105 [S: guard 0.075–0.10, withers to 0.12] | 0.055 [E] | 0.3 | 0.10 | 0.45 | 0.40 | double, undercoat 1.0, woolly |
| arms | 0.85 [E] | 0.075 [E] | 0.042 [E] | 0.3 | 0.10 | 0.40 | 0.40 | double, undercoat 0.85 |
| legs | 0.85 [E] | 0.070 [E] | 0.040 [E] | 0.3 | 0.10 | 0.40 | 0.40 | double, undercoat 0.85 |
| pelvis | 0.90 [E] | 0.090 [E] | 0.050 [E] | 0.3 | 0.10 | 0.50 | 0.40 | double, undercoat 0.9 |
| tail | 0.80 [E] | 0.050 [E] | 0.035 [E] | 0.3 | 0.10 | 0.40 | 0.40 | double, undercoat 0.8 — tail itself is a stub (~10 cm); fur nearly hides it |
| hands | 0.55 [E] | 0.020 [E] | 0.014 [E] | 0.25 | 0.0 | 0.20 | 0.25 | double-sparse, undercoat 0.35 |
| feet | 0.55 [E] | 0.020 [E] | 0.014 [E] | 0.25 | 0.0 | 0.20 | 0.25 | double-sparse, undercoat 0.35; plantigrade soles bare |

**Colour function:** root dark brown → tip pale straw/silver = `pattern: "tipped"`
(high contrast — the grizzle); moon-blend characters shift root toward black and
keep the ruff. **Seasonal scalars [E]:** summer `density_scale 0.6`,
`undercoat_scale 0.25`; late-summer "shabby" state = frizz +0.1 global (a wear
parameter, L3).

---

## 6. Badger — *Meles meles* → profile `species.badger.coat` (Brand)

**Layer structure [S] — the inverted badger:** winter back/flank fur is "long and
coarse, consisting of **coarse and bristly guard hairs with a sparse, soft
undercoat**" — the opposite allocation from the wolf: the show layer is the guard
hair, the undercoat barely exists. Belly fur is "short, sparse, skin visible in the
inguinal region." Summer fur is much coarser, shorter, sparser, and darker.

**Measured [S]:** guard hair mid-back in winter **75–80 mm** — as long as a wolf's,
on a much smaller animal, which is why badgers read as a loose grey *skirt* of hair
over a black underside. Back hairs carry a **black pointed tip** over a pale base
(banded: white → black subterminal band → the grey read is the mix). Hair on head,
face, legs and underside is shorter. Tail: long, coarse, back-coloured.

| region | density | len W (m) | len S (m) | var | curl | clump | frizz | layer |
|---|---|---|---|---|---|---|---|---|
| scalp | 0.60 [E] | 0.030 [E] | 0.020 [E] | 0.25 | 0.0 | 0.20 | 0.30 | double-sparse, undercoat 0.3; white ground (markings stripes) |
| muzzle | 0.45 [E] | 0.012 [E] | 0.009 [E] | 0.25 | 0.0 | 0.10 | 0.20 | sparse, undercoat 0.15 |
| cheeks | 0.60 [E] | 0.032 [E] | 0.021 [E] | 0.25 | 0.0 | 0.25 | 0.30 | double-sparse, undercoat 0.3 |
| ruff | 0.70 [E] | 0.055 [E] | 0.035 [E] | 0.3 | 0.0 | 0.35 | 0.35 | double-sparse, undercoat 0.4 — no true ruff; neck is thick, fur is not |
| ears.inner | 0.30 [E] | 0.010 [E] | 0.008 [E] | 0.25 | 0.0 | 0.10 | 0.20 | sparse; small ears, white ear-tips (markings) |
| ears.back | 0.60 [E] | 0.022 [E] | 0.015 [E] | 0.25 | 0.0 | 0.20 | 0.25 | double-sparse, undercoat 0.35 |
| torso.front | **0.25 [E]** | 0.020 [E] | 0.014 [E] | 0.3 | 0.0 | 0.15 | 0.25 | **sparse by design** [S: belly short/sparse, skin visible] — black chest/legs |
| torso.back | 0.75 [E] | **0.078 [S: mid-back guard 0.075–0.080]** | 0.045 [E] | 0.3 | 0.0 | 0.40 | 0.35 | double-sparse: bristly guard dominant, undercoat only 0.35 |
| arms | 0.55 [E] | 0.028 [E] | 0.018 [E] | 0.25 | 0.0 | 0.25 | 0.30 | double-sparse, undercoat 0.3; black |
| legs | 0.55 [E] | 0.026 [E] | 0.017 [E] | 0.25 | 0.0 | 0.25 | 0.30 | double-sparse, undercoat 0.3; black |
| pelvis | 0.75 [E] | 0.072 [E] | 0.042 [E] | 0.3 | 0.0 | 0.40 | 0.35 | double-sparse, undercoat 0.35 — flank skirt continues |
| tail | 0.70 [E] | 0.060 [S: long and coarse] | 0.038 [E] | 0.3 | 0.0 | 0.40 | 0.35 | double-sparse, undercoat 0.3; short tail, long hair |
| hands | 0.40 [E] | 0.012 [E] | 0.009 [E] | 0.25 | 0.0 | 0.10 | 0.20 | sparse, undercoat 0.15 |
| feet | 0.40 [E] | 0.012 [E] | 0.009 [E] | 0.25 | 0.0 | 0.10 | 0.20 | sparse, undercoat 0.15 |

**Colour function:** guard = root white/cream → wide black subterminal band → pale
tip = `pattern: "banded"` (this banding *is* the grey); belly/legs solid black.
**Seasonal scalars [E]:** summer `density_scale 0.55`, `undercoat_scale 0.4`,
plus a colour darkening note (summer blacks go brownish [S]).
**Groom note:** the dorsal skirt must *hang over* the black ventral zone — flow
direction on `torso.back`/`pelvis` points down-and-back past the belly line, or the
species read (grey top / black bottom, inverted countershading) collapses.

---

## 7. St. Bernard — *Canis familiaris*, St. Bernard → profile `species.saint_bernard.coat` (Jorge)

**Layer structure [S] (UKC breed standard):** "a dense, insulating double coat.
The outer coat is thick, close lying and resilient without being coarse… The
undercoat is short, very dense, and soft." Two bred varieties share the layer plan
and differ only in length distribution — model as **one profile with a
`variety` switch** (`smooth` | `rough`), defaulting to `rough` (the common modern
dog and Jorge's read). Heavy biannual shed (spring/autumn) [S].

**Zonal facts [S]:**
- *Smooth:* short over the whole dog **except thighs and tail, longer and thicker**;
  tail hair longest at the base, shortening toward the tip.
- *Rough:* medium length generally; **longer on ears, neck, back of legs, brisket
  and lower chest, back of thighs, tail**; **a ruff around head and neck**;
  feathering on forelegs and belly; thighs and tail "very bushy."

| region | density | len W rough (m) | len W smooth (m) | len S | var | curl | clump | frizz | layer |
|---|---|---|---|---|---|---|---|---|---|
| scalp | 0.75 [E] | 0.035 [E] | 0.022 [E] | ×0.8 [E] | 0.3 | 0.05 | 0.30 | 0.25 | double, undercoat 0.85 |
| muzzle | 0.50 [E] | 0.014 [E] | 0.012 [E] | ×0.85 [E] | 0.25 | 0.0 | 0.15 | 0.20 | double-sparse, undercoat 0.4 |
| cheeks | 0.80 [E] | 0.045 [E] | 0.026 [E] | ×0.8 [E] | 0.3 | 0.05 | 0.40 | 0.30 | double, undercoat 0.9 — jowl mass is tissue; fur stays close |
| ruff | 0.90 [E] | 0.065 [E] | 0.030 [E] | ×0.8 [E] | 0.35 | 0.10 | 0.55 | 0.35 | double, undercoat 0.95 — rough variety forms a true ruff [S] |
| ears.inner | 0.40 [E] | 0.016 [E] | 0.012 [E] | ×0.85 [E] | 0.3 | 0.0 | 0.20 | 0.30 | sparse fringe, undercoat 0.25; drop ears — inner mostly hidden |
| ears.back | 0.75 [E] | 0.040 [S: ears longer in rough] | 0.020 [E] | ×0.8 [E] | 0.3 | 0.05 | 0.30 | 0.30 | double, undercoat 0.8 |
| torso.front | 0.90 [E] | 0.055 [E] (brisket/lower chest longer [S]) | 0.028 [E] | ×0.8 [E] | 0.3 | 0.05 | 0.40 | 0.30 | double, undercoat 0.95 |
| torso.back | 0.90 [E] | 0.048 [E] | 0.026 [E] | ×0.8 [E] | 0.3 | 0.08 (waviness over loin/pelvis allowed [S]) | 0.40 | 0.30 | double, undercoat 0.95 |
| arms | 0.80 [E] | 0.042 [E] + foreleg feathering [S] | 0.024 [E] | ×0.8 [E] | 0.3 | 0.05 | 0.40 | 0.30 | double, undercoat 0.85; feathering = posterior subzone, +0.02 m [E] |
| legs | 0.80 [E] | 0.045 [E] (back of legs longer [S]) | 0.026 [E] | ×0.8 [E] | 0.3 | 0.05 | 0.40 | 0.30 | double, undercoat 0.85 |
| pelvis | 0.90 [E] | 0.060 [E] (thighs very bushy [S]) | 0.038 [S-ordering: thighs longer in both] | ×0.8 [E] | 0.3 | 0.08 | 0.50 | 0.35 | double, undercoat 0.95 |
| tail | 0.90 [E] | 0.075 [E] (bushy; base > tip gradient [S]) | 0.045 [E] | ×0.8 [E] | 0.35 | 0.05 | 0.50 | 0.35 | double, undercoat 0.9 — author length as a base→tip falloff in the guide set |
| hands | 0.50 [E] | 0.014 [E] | 0.012 [E] | ×0.85 [E] | 0.25 | 0.0 | 0.15 | 0.20 | double-sparse, undercoat 0.35 |
| feet | 0.50 [E] | 0.014 [E] | 0.012 [E] | ×0.85 [E] | 0.25 | 0.0 | 0.15 | 0.20 | double-sparse, undercoat 0.35 |

**Colour function:** white ground with red/brown patches is markings (L1 patches +
mask); the fur itself is `pattern: "solid"`, root≈tip within a patch.
**Seasonal scalars [E]:** instead of a summer length table, the breed sheds by
*coat blow* twice a year: `density_scale 0.75` post-shed with lengths ×0.8 — the
table's `len S` column is given as a multiplier for this species only.

---

## 8. Clydesdale — *Equus caballus*, Clydesdale → profile `species.clydesdale.coat` (Sage)

**A different body plan of hair.** Horses do not run the carnivore double coat.
Body hair is a **single coat** of short hairs (winter: an outercoat plus a true
underhair layer appears in free-ranging/primitive horses [S]; the summer coat is
outer hairs only). All of the species' fur *identity* lives in the **horsehair
systems** — coarse, long, non-moulting-in-length hair that grows continuously:
**forelock, mane, tail, fetlock tuft, and feather**. A Clydesdale profile that
only sets body regions produces a generic horse; the breed is the feather.

**Measured body coat [S]** (temperate-climate study, mid-neck samples): hair
length mean **12.2 mm summer → 47.0 mm winter**; coat mass 13.3 → 66.8 mg/cm².
Free-ranging primitive horses: winter outer hair at the withers averages
**5.8 cm**, ~4.6 cm longer than summer, underhairs 2.2–2.9 cm. Use the temperate
numbers for a kept Clydesdale, the primitive numbers as the un-clipped ceiling.

**Feather [S]** (breed standards): long hair springing **from the back of the
knee/hock and the back of the cannon tendon** (not the sides), falling to
**completely cover the hoof**; "straight and silky" preferred, coarse/curly
faulted; usually white (follows the leg marking). **Mane/forelock/tail [S]:**
"a natural abundance of long flowing mane, forelock, and tail hair" is expected;
the forelock is heavy. Mane falls to one side in domestic horses. Ears are small
with short hair; muzzle carries coarse sensory bristles (vibrissae — a part, not
fur, same ruling as the wolf's whiskers).

Region mapping for a quadruped-derived anthro: `arms`/`legs` = fore/hind limbs,
`hands`/`feet` = fetlock/pastern/hoof zone — **the feather rows are
`legs` distal + `hands` + `feet` at hair-style parameters**, direction strictly
downward from the posterior cannon.

| region | density | len W (m) | len S (m) | var | curl | clump | frizz | layer |
|---|---|---|---|---|---|---|---|---|
| scalp (forelock) | 0.95 [E] | 0.28 [E] | 0.28 (continuous growth) | 0.35 | 0.10 | 0.50 | 0.30 | mane-hair, single, coarse (Ø ≈110 µm [S]) — falls forward over the face |
| muzzle | 0.35 [E] | 0.008 [E] | 0.006 [E] | 0.25 | 0.0 | 0.10 | 0.15 | single, sparse; vibrissae excluded (part) |
| cheeks | 0.55 [E] | 0.030 [E] | 0.010 [E] | 0.25 | 0.0 | 0.20 | 0.20 | single (winter underhair 0.4) |
| ruff (mane, neck crest) | 1.00 [E] | 0.45 [E] | 0.45 (continuous) | 0.35 | 0.10 | 0.55 | 0.30 | mane-hair, single — grows from the crest only, falls to one side; body-neck hair beneath stays at `cheeks` values |
| ears.inner | 0.45 [E] | 0.012 [E] | 0.010 [E] | 0.3 | 0.0 | 0.15 | 0.25 | single fringe |
| ears.back | 0.55 [E] | 0.016 [E] | 0.008 [E] | 0.25 | 0.0 | 0.20 | 0.20 | single; small ears, short hair [S] |
| torso.front | 0.60 [E] | 0.047 [S: winter mean 0.047] | 0.012 [S: summer mean 0.012] | 0.25 | 0.0 | 0.20 | 0.20 | single summer / winter double (underhair 2.2–2.9 cm [S]) |
| torso.back | 0.60 [E] | 0.047 [S] (primitive ceiling 0.058 [S]) | 0.012 [S] | 0.25 | 0.0 | 0.20 | 0.20 | as torso.front |
| arms | 0.55 [E] | 0.040 [E] | 0.011 [E] | 0.25 | 0.0 | 0.20 | 0.20 | single/winter-underhair 0.35 |
| legs | 0.55 [E] proximal / **0.95 [E] distal (feather)** | 0.040 prox; **feather 0.22 [E]** | feather unchanged (continuous) | 0.35 | **0.05 (straight is the standard [S])** | 0.45 | 0.25 | feather = mane-hair class, springs from posterior knee/hock [S] |
| pelvis | 0.60 [E] | 0.047 [S] | 0.012 [S] | 0.25 | 0.0 | 0.20 | 0.20 | as torso.back |
| tail | 0.95 [E] | 0.85 [E] | 0.85 (continuous) | 0.3 | 0.10 | 0.50 | 0.30 | mane-hair from the dock; full-length natural tail (show trimming is a character choice) |
| hands (fore fetlock) | 0.90 [E] | 0.20 [E] | 0.20 | 0.35 | 0.05 | 0.45 | 0.25 | feather — covers the hoof [S] |
| feet (hind fetlock) | 0.90 [E] | 0.22 [E] | 0.22 | 0.35 | 0.05 | 0.45 | 0.25 | feather — covers the hoof [S]; hind feather typically ≥ fore |

**Colour function:** body `pattern: "solid"` (bay/black/brown/roan — roan is a
white-hair mix, a colour-function variant, not a marking); mane/tail/forelock
often lighter or matching; feather follows the leg marking (usually white [S]).
**Seasonal scalars:** winter is *in the table* (len W); summer body density
`density_scale 0.45` [E, from the 5:1 coat-mass ratio, S-derived], undercoat
absent. Mane/tail/feather/forelock are **season-invariant** — the single biggest
modelling difference from every carnivore in this document.

---

## 9. Machine-readable profiles (§9.5 shape, winter/prime defaults)

Drop-in `fur` blocks for the character record. `colour` values are representative
mid-population picks [E] — per-character palettes override them; `pattern` is the
sourced structural fact. `layer` and `seasonal` are the §0.4/§0.5 extensions.
Summer length overrides: read `len S` from the tables (only regions whose summer
length differs are re-listed in a consumer when applying `seasonal`).

### 9.1 `species.wolf.coat`
```json
{ "profile": "species.wolf.coat",
  "seasonal": { "summer": { "density_scale": 0.55, "undercoat_scale": 0.15 } },
  "regions": {
    "scalp":      { "density": 0.75, "length_m": 0.055, "length_variation": 0.30, "curl": 0.05, "clump": 0.30, "frizz": 0.25, "colour": { "root": "#3d3230", "tip": "#7d7468", "pattern": "agouti" }, "layer": { "structure": "double", "undercoat": 0.70 } },
    "muzzle":     { "density": 0.55, "length_m": 0.018, "length_variation": 0.25, "curl": 0.00, "clump": 0.15, "frizz": 0.15, "colour": { "root": "#4a423c", "tip": "#8d8378", "pattern": "agouti" }, "layer": { "structure": "double-sparse", "undercoat": 0.30 } },
    "cheeks":     { "density": 0.80, "length_m": 0.075, "length_variation": 0.35, "curl": 0.05, "clump": 0.45, "frizz": 0.30, "colour": { "root": "#3d3230", "tip": "#9a8d7a", "pattern": "agouti" }, "layer": { "structure": "double", "undercoat": 0.75 } },
    "ruff":       { "density": 0.95, "length_m": 0.115, "length_variation": 0.35, "curl": 0.10, "clump": 0.65, "frizz": 0.35, "colour": { "root": "#38302c", "tip": "#8d8074", "pattern": "agouti" }, "layer": { "structure": "double", "undercoat": 0.95 } },
    "ears.inner": { "density": 0.45, "length_m": 0.020, "length_variation": 0.30, "curl": 0.00, "clump": 0.20, "frizz": 0.30, "colour": { "root": "#6b5f55", "tip": "#b3a893", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.20 } },
    "ears.back":  { "density": 0.70, "length_m": 0.030, "length_variation": 0.25, "curl": 0.00, "clump": 0.25, "frizz": 0.25, "colour": { "root": "#38302c", "tip": "#6e6259", "pattern": "agouti" }, "layer": { "structure": "double-sparse", "undercoat": 0.50 } },
    "torso.front":{ "density": 0.90, "length_m": 0.075, "length_variation": 0.30, "curl": 0.05, "clump": 0.45, "frizz": 0.30, "colour": { "root": "#453a34", "tip": "#968a76", "pattern": "agouti" }, "layer": { "structure": "double", "undercoat": 0.90 } },
    "torso.back": { "density": 1.00, "length_m": 0.065, "length_variation": 0.30, "curl": 0.05, "clump": 0.40, "frizz": 0.30, "colour": { "root": "#38302c", "tip": "#84796a", "pattern": "agouti" }, "layer": { "structure": "double", "undercoat": 1.00 } },
    "arms":       { "density": 0.80, "length_m": 0.045, "length_variation": 0.30, "curl": 0.05, "clump": 0.35, "frizz": 0.30, "colour": { "root": "#403832", "tip": "#877b6c", "pattern": "agouti" }, "layer": { "structure": "double", "undercoat": 0.80 } },
    "legs":       { "density": 0.75, "length_m": 0.040, "length_variation": 0.30, "curl": 0.05, "clump": 0.35, "frizz": 0.30, "colour": { "root": "#453b33", "tip": "#978a76", "pattern": "agouti" }, "layer": { "structure": "double", "undercoat": 0.75 } },
    "pelvis":     { "density": 0.90, "length_m": 0.070, "length_variation": 0.30, "curl": 0.10, "clump": 0.45, "frizz": 0.35, "colour": { "root": "#38302c", "tip": "#84796a", "pattern": "agouti" }, "layer": { "structure": "double", "undercoat": 0.90 } },
    "tail":       { "density": 0.95, "length_m": 0.085, "length_variation": 0.35, "curl": 0.10, "clump": 0.55, "frizz": 0.35, "colour": { "root": "#38302c", "tip": "#7d7468", "pattern": "agouti" }, "layer": { "structure": "double", "undercoat": 0.95 } },
    "hands":      { "density": 0.50, "length_m": 0.015, "length_variation": 0.25, "curl": 0.00, "clump": 0.15, "frizz": 0.20, "colour": { "root": "#4a423c", "tip": "#8d8378", "pattern": "agouti" }, "layer": { "structure": "double-sparse", "undercoat": 0.25 } },
    "feet":       { "density": 0.50, "length_m": 0.015, "length_variation": 0.25, "curl": 0.00, "clump": 0.15, "frizz": 0.20, "colour": { "root": "#4a423c", "tip": "#8d8378", "pattern": "agouti" }, "layer": { "structure": "double-sparse", "undercoat": 0.25 } }
  } }
```

### 9.2 `species.red_fox.coat`
```json
{ "profile": "species.red_fox.coat",
  "seasonal": { "summer": { "density_scale": 0.60, "undercoat_scale": 0.30 } },
  "regions": {
    "scalp":      { "density": 0.70, "length_m": 0.040, "length_variation": 0.30, "curl": 0.05, "clump": 0.30, "frizz": 0.30, "colour": { "root": "#6e625a", "tip": "#b35c28", "pattern": "banded" }, "layer": { "structure": "double", "undercoat": 0.70, "undercoat_length_m": 0.035 } },
    "muzzle":     { "density": 0.50, "length_m": 0.014, "length_variation": 0.25, "curl": 0.00, "clump": 0.15, "frizz": 0.20, "colour": { "root": "#6e625a", "tip": "#a85424", "pattern": "banded" }, "layer": { "structure": "double-sparse", "undercoat": 0.30 } },
    "cheeks":     { "density": 0.75, "length_m": 0.050, "length_variation": 0.30, "curl": 0.05, "clump": 0.40, "frizz": 0.30, "colour": { "root": "#6e625a", "tip": "#bc652c", "pattern": "banded" }, "layer": { "structure": "double", "undercoat": 0.80 } },
    "ruff":       { "density": 0.85, "length_m": 0.060, "length_variation": 0.30, "curl": 0.05, "clump": 0.50, "frizz": 0.35, "colour": { "root": "#66584f", "tip": "#b35c28", "pattern": "banded" }, "layer": { "structure": "double", "undercoat": 0.90 } },
    "ears.inner": { "density": 0.40, "length_m": 0.018, "length_variation": 0.30, "curl": 0.00, "clump": 0.20, "frizz": 0.30, "colour": { "root": "#8a7a6a", "tip": "#d8cbb8", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.15 } },
    "ears.back":  { "density": 0.70, "length_m": 0.028, "length_variation": 0.25, "curl": 0.00, "clump": 0.25, "frizz": 0.25, "colour": { "root": "#241c18", "tip": "#17120f", "pattern": "solid" }, "layer": { "structure": "double-sparse", "undercoat": 0.50 } },
    "torso.front":{ "density": 0.85, "length_m": 0.048, "length_variation": 0.30, "curl": 0.05, "clump": 0.40, "frizz": 0.30, "colour": { "root": "#6e625a", "tip": "#c4beb2", "pattern": "banded" }, "layer": { "structure": "double", "undercoat": 0.90, "undercoat_length_m": 0.035 } },
    "torso.back": { "density": 0.95, "length_m": 0.060, "length_variation": 0.30, "curl": 0.05, "clump": 0.40, "frizz": 0.30, "colour": { "root": "#6e625a", "tip": "#b35c28", "pattern": "banded" }, "layer": { "structure": "double", "undercoat": 1.00, "undercoat_length_m": 0.035 } },
    "arms":       { "density": 0.70, "length_m": 0.035, "length_variation": 0.30, "curl": 0.00, "clump": 0.30, "frizz": 0.30, "colour": { "root": "#66584f", "tip": "#a85424", "pattern": "banded" }, "layer": { "structure": "double", "undercoat": 0.70 } },
    "legs":       { "density": 0.65, "length_m": 0.032, "length_variation": 0.30, "curl": 0.00, "clump": 0.30, "frizz": 0.30, "colour": { "root": "#2a201b", "tip": "#1d1512", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.65 } },
    "pelvis":     { "density": 0.85, "length_m": 0.055, "length_variation": 0.30, "curl": 0.05, "clump": 0.45, "frizz": 0.35, "colour": { "root": "#66584f", "tip": "#b35c28", "pattern": "banded" }, "layer": { "structure": "double", "undercoat": 0.90 } },
    "tail":       { "density": 0.95, "length_m": 0.085, "length_variation": 0.35, "curl": 0.10, "clump": 0.55, "frizz": 0.35, "colour": { "root": "#66584f", "tip": "#b35c28", "pattern": "banded" }, "layer": { "structure": "double", "undercoat": 0.95 } },
    "hands":      { "density": 0.45, "length_m": 0.012, "length_variation": 0.25, "curl": 0.00, "clump": 0.15, "frizz": 0.20, "colour": { "root": "#2a201b", "tip": "#1d1512", "pattern": "solid" }, "layer": { "structure": "double-sparse", "undercoat": 0.25 } },
    "feet":       { "density": 0.45, "length_m": 0.012, "length_variation": 0.25, "curl": 0.00, "clump": 0.15, "frizz": 0.20, "colour": { "root": "#2a201b", "tip": "#1d1512", "pattern": "solid" }, "layer": { "structure": "double-sparse", "undercoat": 0.25 } }
  } }
```

### 9.3 `species.fennec.coat`
```json
{ "profile": "species.fennec.coat",
  "seasonal": { "summer": { "density_scale": 1.00, "undercoat_scale": 1.00 } },
  "regions": {
    "scalp":      { "density": 0.80, "length_m": 0.030, "length_variation": 0.30, "curl": 0.05, "clump": 0.30, "frizz": 0.40, "colour": { "root": "#e6d7b8", "tip": "#d9bd8f", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.80 } },
    "muzzle":     { "density": 0.55, "length_m": 0.012, "length_variation": 0.25, "curl": 0.00, "clump": 0.15, "frizz": 0.25, "colour": { "root": "#efe4cc", "tip": "#e8dcc2", "pattern": "solid" }, "layer": { "structure": "double-sparse", "undercoat": 0.35 } },
    "cheeks":     { "density": 0.80, "length_m": 0.035, "length_variation": 0.30, "curl": 0.05, "clump": 0.35, "frizz": 0.40, "colour": { "root": "#e6d7b8", "tip": "#dcc096", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.85 } },
    "ruff":       { "density": 0.85, "length_m": 0.038, "length_variation": 0.30, "curl": 0.05, "clump": 0.40, "frizz": 0.40, "colour": { "root": "#e6d7b8", "tip": "#d9bd8f", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.90 } },
    "ears.inner": { "density": 0.75, "length_m": 0.030, "length_variation": 0.35, "curl": 0.00, "clump": 0.25, "frizz": 0.45, "colour": { "root": "#f4ecd9", "tip": "#faf5e8", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.10 } },
    "ears.back":  { "density": 0.75, "length_m": 0.022, "length_variation": 0.30, "curl": 0.00, "clump": 0.25, "frizz": 0.35, "colour": { "root": "#e0cda6", "tip": "#d3b586", "pattern": "tipped" }, "layer": { "structure": "double-sparse", "undercoat": 0.50 } },
    "torso.front":{ "density": 0.90, "length_m": 0.032, "length_variation": 0.30, "curl": 0.05, "clump": 0.35, "frizz": 0.40, "colour": { "root": "#f2e8d2", "tip": "#f7f1e0", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.95 } },
    "torso.back": { "density": 0.90, "length_m": 0.035, "length_variation": 0.30, "curl": 0.05, "clump": 0.35, "frizz": 0.40, "colour": { "root": "#e6d7b8", "tip": "#d9bd8f", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.95 } },
    "arms":       { "density": 0.75, "length_m": 0.024, "length_variation": 0.30, "curl": 0.00, "clump": 0.30, "frizz": 0.35, "colour": { "root": "#eadcbf", "tip": "#e2cda1", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.75 } },
    "legs":       { "density": 0.75, "length_m": 0.024, "length_variation": 0.30, "curl": 0.00, "clump": 0.30, "frizz": 0.35, "colour": { "root": "#eadcbf", "tip": "#e2cda1", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.75 } },
    "pelvis":     { "density": 0.85, "length_m": 0.034, "length_variation": 0.30, "curl": 0.05, "clump": 0.40, "frizz": 0.40, "colour": { "root": "#e6d7b8", "tip": "#d9bd8f", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.90 } },
    "tail":       { "density": 0.90, "length_m": 0.045, "length_variation": 0.35, "curl": 0.05, "clump": 0.50, "frizz": 0.40, "colour": { "root": "#e6d7b8", "tip": "#d9bd8f", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.90 } },
    "hands":      { "density": 0.55, "length_m": 0.012, "length_variation": 0.25, "curl": 0.00, "clump": 0.20, "frizz": 0.30, "colour": { "root": "#efe4cc", "tip": "#e8dcc2", "pattern": "solid" }, "layer": { "structure": "double-sparse", "undercoat": 0.40 } },
    "feet":       { "density": 0.80, "length_m": 0.018, "length_variation": 0.30, "curl": 0.00, "clump": 0.30, "frizz": 0.40, "colour": { "root": "#f2e8d2", "tip": "#f7f1e0", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.70, "note": "covers pads — unique on roster" } }
  } }
```

### 9.4 `species.lion.coat` (male default; female: mane rows → body values, §4)
```json
{ "profile": "species.lion.coat",
  "seasonal": { "summer": { "density_scale": 1.00, "undercoat_scale": 1.00 } },
  "regions": {
    "scalp":      { "density": 0.95, "length_m": 0.160, "length_variation": 0.40, "curl": 0.15, "clump": 0.60, "frizz": 0.45, "colour": { "root": "#a97c46", "tip": "#4a3018", "pattern": "tipped" }, "layer": { "structure": "mane-hair", "undercoat": 0.00 } },
    "muzzle":     { "density": 0.45, "length_m": 0.008, "length_variation": 0.25, "curl": 0.00, "clump": 0.10, "frizz": 0.15, "colour": { "root": "#b98d54", "tip": "#c49a5e", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.00 } },
    "cheeks":     { "density": 0.95, "length_m": 0.150, "length_variation": 0.40, "curl": 0.15, "clump": 0.60, "frizz": 0.45, "colour": { "root": "#a97c46", "tip": "#453013", "pattern": "tipped" }, "layer": { "structure": "mane-hair", "undercoat": 0.00 } },
    "ruff":       { "density": 1.00, "length_m": 0.160, "length_variation": 0.40, "curl": 0.15, "clump": 0.65, "frizz": 0.45, "colour": { "root": "#a97c46", "tip": "#3d2812", "pattern": "tipped" }, "layer": { "structure": "mane-hair", "undercoat": 0.00, "note": "character dials: length to 0.22 (cool-climate), tip darkness = age/testosterone proxy" } },
    "ears.inner": { "density": 0.30, "length_m": 0.010, "length_variation": 0.30, "curl": 0.00, "clump": 0.15, "frizz": 0.25, "colour": { "root": "#c4a06a", "tip": "#d3b57f", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.00 } },
    "ears.back":  { "density": 0.55, "length_m": 0.014, "length_variation": 0.25, "curl": 0.00, "clump": 0.20, "frizz": 0.20, "colour": { "root": "#8a6535", "tip": "#33241a", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.00 } },
    "torso.front":{ "density": 0.60, "length_m": 0.018, "length_variation": 0.30, "curl": 0.05, "clump": 0.30, "frizz": 0.25, "colour": { "root": "#b98d54", "tip": "#cda668", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.00, "note": "male chest fringe override: density 0.85, length_m 0.10" } },
    "torso.back": { "density": 0.60, "length_m": 0.014, "length_variation": 0.25, "curl": 0.05, "clump": 0.25, "frizz": 0.20, "colour": { "root": "#b0824a", "tip": "#c49a5e", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.00 } },
    "arms":       { "density": 0.55, "length_m": 0.014, "length_variation": 0.30, "curl": 0.05, "clump": 0.30, "frizz": 0.25, "colour": { "root": "#b98d54", "tip": "#cda668", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.00, "note": "male elbow-tuft override: density 0.80, length_m 0.07" } },
    "legs":       { "density": 0.55, "length_m": 0.013, "length_variation": 0.25, "curl": 0.05, "clump": 0.25, "frizz": 0.20, "colour": { "root": "#b98d54", "tip": "#cda668", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.00 } },
    "pelvis":     { "density": 0.60, "length_m": 0.016, "length_variation": 0.30, "curl": 0.05, "clump": 0.30, "frizz": 0.25, "colour": { "root": "#b0824a", "tip": "#c49a5e", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.00 } },
    "tail":       { "density": 0.55, "length_m": 0.012, "length_variation": 0.35, "curl": 0.05, "clump": 0.20, "frizz": 0.25, "colour": { "root": "#b0824a", "tip": "#c49a5e", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.00, "note": "terminal tuft override (last 15% of tail): density 0.90, length_m 0.06, tip #2e2015" } },
    "hands":      { "density": 0.45, "length_m": 0.010, "length_variation": 0.25, "curl": 0.00, "clump": 0.15, "frizz": 0.20, "colour": { "root": "#b98d54", "tip": "#cda668", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.00 } },
    "feet":       { "density": 0.45, "length_m": 0.010, "length_variation": 0.25, "curl": 0.00, "clump": 0.15, "frizz": 0.20, "colour": { "root": "#b98d54", "tip": "#cda668", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.00 } }
  } }
```

### 9.5 `species.bear.coat` (Sen blend: brown-bear body, moon-bear ruff)
```json
{ "profile": "species.bear.coat",
  "seasonal": { "summer": { "density_scale": 0.60, "undercoat_scale": 0.25 } },
  "regions": {
    "scalp":      { "density": 0.75, "length_m": 0.055, "length_variation": 0.30, "curl": 0.10, "clump": 0.35, "frizz": 0.35, "colour": { "root": "#2e2119", "tip": "#6e5638", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.75 } },
    "muzzle":     { "density": 0.50, "length_m": 0.016, "length_variation": 0.25, "curl": 0.00, "clump": 0.15, "frizz": 0.20, "colour": { "root": "#4a3826", "tip": "#8a6c48", "pattern": "tipped" }, "layer": { "structure": "double-sparse", "undercoat": 0.30 } },
    "cheeks":     { "density": 0.80, "length_m": 0.070, "length_variation": 0.30, "curl": 0.10, "clump": 0.45, "frizz": 0.40, "colour": { "root": "#2e2119", "tip": "#77603c", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.80 } },
    "ruff":       { "density": 0.95, "length_m": 0.150, "length_variation": 0.35, "curl": 0.15, "clump": 0.60, "frizz": 0.45, "colour": { "root": "#241a12", "tip": "#5f4a2e", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.90, "note": "moon-bear value; brown-only fallback length_m 0.115" } },
    "ears.inner": { "density": 0.40, "length_m": 0.018, "length_variation": 0.30, "curl": 0.00, "clump": 0.20, "frizz": 0.30, "colour": { "root": "#4a3826", "tip": "#77603c", "pattern": "tipped" }, "layer": { "structure": "single", "undercoat": 0.20 } },
    "ears.back":  { "density": 0.70, "length_m": 0.030, "length_variation": 0.25, "curl": 0.05, "clump": 0.30, "frizz": 0.30, "colour": { "root": "#2e2119", "tip": "#6e5638", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.60 } },
    "torso.front":{ "density": 0.90, "length_m": 0.085, "length_variation": 0.30, "curl": 0.10, "clump": 0.45, "frizz": 0.40, "colour": { "root": "#2e2119", "tip": "#77603c", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.95, "note": "crescent zone (moon blend) = markings fur-colour override, parameters unchanged" } },
    "torso.back": { "density": 0.95, "length_m": 0.105, "length_variation": 0.30, "curl": 0.10, "clump": 0.45, "frizz": 0.40, "colour": { "root": "#2e2119", "tip": "#7d6540", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 1.00 } },
    "arms":       { "density": 0.85, "length_m": 0.075, "length_variation": 0.30, "curl": 0.10, "clump": 0.40, "frizz": 0.40, "colour": { "root": "#2e2119", "tip": "#6e5638", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.85 } },
    "legs":       { "density": 0.85, "length_m": 0.070, "length_variation": 0.30, "curl": 0.10, "clump": 0.40, "frizz": 0.40, "colour": { "root": "#2a1e15", "tip": "#63502f", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.85 } },
    "pelvis":     { "density": 0.90, "length_m": 0.090, "length_variation": 0.30, "curl": 0.10, "clump": 0.50, "frizz": 0.40, "colour": { "root": "#2e2119", "tip": "#77603c", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.90 } },
    "tail":       { "density": 0.80, "length_m": 0.050, "length_variation": 0.30, "curl": 0.10, "clump": 0.40, "frizz": 0.40, "colour": { "root": "#2e2119", "tip": "#6e5638", "pattern": "tipped" }, "layer": { "structure": "double", "undercoat": 0.80 } },
    "hands":      { "density": 0.55, "length_m": 0.020, "length_variation": 0.25, "curl": 0.00, "clump": 0.20, "frizz": 0.25, "colour": { "root": "#33261a", "tip": "#6e5638", "pattern": "tipped" }, "layer": { "structure": "double-sparse", "undercoat": 0.35 } },
    "feet":       { "density": 0.55, "length_m": 0.020, "length_variation": 0.25, "curl": 0.00, "clump": 0.20, "frizz": 0.25, "colour": { "root": "#33261a", "tip": "#6e5638", "pattern": "tipped" }, "layer": { "structure": "double-sparse", "undercoat": 0.35 } }
  } }
```

### 9.6 `species.badger.coat`
```json
{ "profile": "species.badger.coat",
  "seasonal": { "summer": { "density_scale": 0.55, "undercoat_scale": 0.40 } },
  "regions": {
    "scalp":      { "density": 0.60, "length_m": 0.030, "length_variation": 0.25, "curl": 0.00, "clump": 0.20, "frizz": 0.30, "colour": { "root": "#e8e2d4", "tip": "#f0ead9", "pattern": "solid" }, "layer": { "structure": "double-sparse", "undercoat": 0.30 } },
    "muzzle":     { "density": 0.45, "length_m": 0.012, "length_variation": 0.25, "curl": 0.00, "clump": 0.10, "frizz": 0.20, "colour": { "root": "#e8e2d4", "tip": "#f0ead9", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.15 } },
    "cheeks":     { "density": 0.60, "length_m": 0.032, "length_variation": 0.25, "curl": 0.00, "clump": 0.25, "frizz": 0.30, "colour": { "root": "#e8e2d4", "tip": "#efe9da", "pattern": "solid" }, "layer": { "structure": "double-sparse", "undercoat": 0.30 } },
    "ruff":       { "density": 0.70, "length_m": 0.055, "length_variation": 0.30, "curl": 0.00, "clump": 0.35, "frizz": 0.35, "colour": { "root": "#ddd5c2", "tip": "#8f8a7c", "pattern": "banded" }, "layer": { "structure": "double-sparse", "undercoat": 0.40 } },
    "ears.inner": { "density": 0.30, "length_m": 0.010, "length_variation": 0.25, "curl": 0.00, "clump": 0.10, "frizz": 0.20, "colour": { "root": "#3a332c", "tip": "#efe9da", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.10 } },
    "ears.back":  { "density": 0.60, "length_m": 0.022, "length_variation": 0.25, "curl": 0.00, "clump": 0.20, "frizz": 0.25, "colour": { "root": "#ddd5c2", "tip": "#211c17", "pattern": "banded" }, "layer": { "structure": "double-sparse", "undercoat": 0.35 } },
    "torso.front":{ "density": 0.25, "length_m": 0.020, "length_variation": 0.30, "curl": 0.00, "clump": 0.15, "frizz": 0.25, "colour": { "root": "#1d1813", "tip": "#14100d", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.10, "note": "sparse by design — skin may show" } },
    "torso.back": { "density": 0.75, "length_m": 0.078, "length_variation": 0.30, "curl": 0.00, "clump": 0.40, "frizz": 0.35, "colour": { "root": "#e3dcc9", "tip": "#211c17", "pattern": "banded" }, "layer": { "structure": "double-sparse", "undercoat": 0.35, "note": "bristly guard dominant; groom flow hangs over the ventral zone" } },
    "arms":       { "density": 0.55, "length_m": 0.028, "length_variation": 0.25, "curl": 0.00, "clump": 0.25, "frizz": 0.30, "colour": { "root": "#1d1813", "tip": "#14100d", "pattern": "solid" }, "layer": { "structure": "double-sparse", "undercoat": 0.30 } },
    "legs":       { "density": 0.55, "length_m": 0.026, "length_variation": 0.25, "curl": 0.00, "clump": 0.25, "frizz": 0.30, "colour": { "root": "#1d1813", "tip": "#14100d", "pattern": "solid" }, "layer": { "structure": "double-sparse", "undercoat": 0.30 } },
    "pelvis":     { "density": 0.75, "length_m": 0.072, "length_variation": 0.30, "curl": 0.00, "clump": 0.40, "frizz": 0.35, "colour": { "root": "#e3dcc9", "tip": "#211c17", "pattern": "banded" }, "layer": { "structure": "double-sparse", "undercoat": 0.35 } },
    "tail":       { "density": 0.70, "length_m": 0.060, "length_variation": 0.30, "curl": 0.00, "clump": 0.40, "frizz": 0.35, "colour": { "root": "#ddd5c2", "tip": "#8f8a7c", "pattern": "banded" }, "layer": { "structure": "double-sparse", "undercoat": 0.30 } },
    "hands":      { "density": 0.40, "length_m": 0.012, "length_variation": 0.25, "curl": 0.00, "clump": 0.10, "frizz": 0.20, "colour": { "root": "#1d1813", "tip": "#14100d", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.15 } },
    "feet":       { "density": 0.40, "length_m": 0.012, "length_variation": 0.25, "curl": 0.00, "clump": 0.10, "frizz": 0.20, "colour": { "root": "#1d1813", "tip": "#14100d", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.15 } }
  } }
```

### 9.7 `species.saint_bernard.coat` (default variety `rough`; `smooth` lengths in §7 table)
```json
{ "profile": "species.saint_bernard.coat", "variety": "rough",
  "seasonal": { "post_shed": { "density_scale": 0.75, "length_scale": 0.80 } },
  "regions": {
    "scalp":      { "density": 0.75, "length_m": 0.035, "length_variation": 0.30, "curl": 0.05, "clump": 0.30, "frizz": 0.25, "colour": { "root": "#7a4a2a", "tip": "#8a5a33", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.85 } },
    "muzzle":     { "density": 0.50, "length_m": 0.014, "length_variation": 0.25, "curl": 0.00, "clump": 0.15, "frizz": 0.20, "colour": { "root": "#5f3d24", "tip": "#6e4a2c", "pattern": "solid" }, "layer": { "structure": "double-sparse", "undercoat": 0.40 } },
    "cheeks":     { "density": 0.80, "length_m": 0.045, "length_variation": 0.30, "curl": 0.05, "clump": 0.40, "frizz": 0.30, "colour": { "root": "#7a4a2a", "tip": "#8a5a33", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.90 } },
    "ruff":       { "density": 0.90, "length_m": 0.065, "length_variation": 0.35, "curl": 0.10, "clump": 0.55, "frizz": 0.35, "colour": { "root": "#e8e0d0", "tip": "#f2ecdd", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.95 } },
    "ears.inner": { "density": 0.40, "length_m": 0.016, "length_variation": 0.30, "curl": 0.00, "clump": 0.20, "frizz": 0.30, "colour": { "root": "#6e4a2c", "tip": "#7d5636", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.25 } },
    "ears.back":  { "density": 0.75, "length_m": 0.040, "length_variation": 0.30, "curl": 0.05, "clump": 0.30, "frizz": 0.30, "colour": { "root": "#5f3d24", "tip": "#4a2e1a", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.80 } },
    "torso.front":{ "density": 0.90, "length_m": 0.055, "length_variation": 0.30, "curl": 0.05, "clump": 0.40, "frizz": 0.30, "colour": { "root": "#ece4d2", "tip": "#f5efe0", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.95 } },
    "torso.back": { "density": 0.90, "length_m": 0.048, "length_variation": 0.30, "curl": 0.08, "clump": 0.40, "frizz": 0.30, "colour": { "root": "#7a4a2a", "tip": "#8a5a33", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.95 } },
    "arms":       { "density": 0.80, "length_m": 0.042, "length_variation": 0.30, "curl": 0.05, "clump": 0.40, "frizz": 0.30, "colour": { "root": "#ece4d2", "tip": "#f5efe0", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.85, "note": "foreleg feathering = posterior subzone +0.02 m" } },
    "legs":       { "density": 0.80, "length_m": 0.045, "length_variation": 0.30, "curl": 0.05, "clump": 0.40, "frizz": 0.30, "colour": { "root": "#ece4d2", "tip": "#f5efe0", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.85 } },
    "pelvis":     { "density": 0.90, "length_m": 0.060, "length_variation": 0.30, "curl": 0.08, "clump": 0.50, "frizz": 0.35, "colour": { "root": "#7a4a2a", "tip": "#8a5a33", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.95 } },
    "tail":       { "density": 0.90, "length_m": 0.075, "length_variation": 0.35, "curl": 0.05, "clump": 0.50, "frizz": 0.35, "colour": { "root": "#ece4d2", "tip": "#f5efe0", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.90, "note": "length authored as base-to-tip falloff in guides" } },
    "hands":      { "density": 0.50, "length_m": 0.014, "length_variation": 0.25, "curl": 0.00, "clump": 0.15, "frizz": 0.20, "colour": { "root": "#ece4d2", "tip": "#f5efe0", "pattern": "solid" }, "layer": { "structure": "double-sparse", "undercoat": 0.35 } },
    "feet":       { "density": 0.50, "length_m": 0.014, "length_variation": 0.25, "curl": 0.00, "clump": 0.15, "frizz": 0.20, "colour": { "root": "#ece4d2", "tip": "#f5efe0", "pattern": "solid" }, "layer": { "structure": "double-sparse", "undercoat": 0.35 } }
  } }
```

### 9.8 `species.clydesdale.coat`
```json
{ "profile": "species.clydesdale.coat",
  "seasonal": { "summer": { "density_scale": 0.45, "undercoat_scale": 0.00, "note": "body regions only — mane/tail/feather/forelock are season-invariant" } },
  "regions": {
    "scalp":      { "density": 0.95, "length_m": 0.280, "length_variation": 0.35, "curl": 0.10, "clump": 0.50, "frizz": 0.30, "colour": { "root": "#5a4030", "tip": "#77563c", "pattern": "solid" }, "layer": { "structure": "mane-hair", "undercoat": 0.00, "note": "forelock — falls forward over face" } },
    "muzzle":     { "density": 0.35, "length_m": 0.008, "length_variation": 0.25, "curl": 0.00, "clump": 0.10, "frizz": 0.15, "colour": { "root": "#6e4f36", "tip": "#83643f", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.00 } },
    "cheeks":     { "density": 0.55, "length_m": 0.030, "length_variation": 0.25, "curl": 0.00, "clump": 0.20, "frizz": 0.20, "colour": { "root": "#5a4030", "tip": "#6e5138", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.40 } },
    "ruff":       { "density": 1.00, "length_m": 0.450, "length_variation": 0.35, "curl": 0.10, "clump": 0.55, "frizz": 0.30, "colour": { "root": "#5a4030", "tip": "#77563c", "pattern": "solid" }, "layer": { "structure": "mane-hair", "undercoat": 0.00, "note": "mane — crest-origin only, falls to one side; neck body hair uses cheeks values" } },
    "ears.inner": { "density": 0.45, "length_m": 0.012, "length_variation": 0.30, "curl": 0.00, "clump": 0.15, "frizz": 0.25, "colour": { "root": "#6e4f36", "tip": "#83643f", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.00 } },
    "ears.back":  { "density": 0.55, "length_m": 0.016, "length_variation": 0.25, "curl": 0.00, "clump": 0.20, "frizz": 0.20, "colour": { "root": "#5a4030", "tip": "#6e5138", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.00 } },
    "torso.front":{ "density": 0.60, "length_m": 0.047, "length_variation": 0.25, "curl": 0.00, "clump": 0.20, "frizz": 0.20, "colour": { "root": "#5a4030", "tip": "#6e5138", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.50, "undercoat_length_m": 0.025, "note": "structure is winter state; summer = single, length_m 0.012" } },
    "torso.back": { "density": 0.60, "length_m": 0.047, "length_variation": 0.25, "curl": 0.00, "clump": 0.20, "frizz": 0.20, "colour": { "root": "#5a4030", "tip": "#6e5138", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.50, "undercoat_length_m": 0.025 } },
    "arms":       { "density": 0.55, "length_m": 0.040, "length_variation": 0.25, "curl": 0.00, "clump": 0.20, "frizz": 0.20, "colour": { "root": "#5a4030", "tip": "#6e5138", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.35 } },
    "legs":       { "density": 0.55, "length_m": 0.040, "length_variation": 0.25, "curl": 0.00, "clump": 0.20, "frizz": 0.20, "colour": { "root": "#5a4030", "tip": "#6e5138", "pattern": "solid" }, "layer": { "structure": "single", "undercoat": 0.35, "note": "distal feather override: density 0.95, length_m 0.22, curl 0.05, clump 0.45 — posterior knee/hock origin, covers hoof" } },
    "pelvis":     { "density": 0.60, "length_m": 0.047, "length_variation": 0.25, "curl": 0.00, "clump": 0.20, "frizz": 0.20, "colour": { "root": "#5a4030", "tip": "#6e5138", "pattern": "solid" }, "layer": { "structure": "double", "undercoat": 0.50, "undercoat_length_m": 0.025 } },
    "tail":       { "density": 0.95, "length_m": 0.850, "length_variation": 0.30, "curl": 0.10, "clump": 0.50, "frizz": 0.30, "colour": { "root": "#5a4030", "tip": "#77563c", "pattern": "solid" }, "layer": { "structure": "mane-hair", "undercoat": 0.00 } },
    "hands":      { "density": 0.90, "length_m": 0.200, "length_variation": 0.35, "curl": 0.05, "clump": 0.45, "frizz": 0.25, "colour": { "root": "#e8e2d2", "tip": "#f2ecdc", "pattern": "solid" }, "layer": { "structure": "mane-hair", "undercoat": 0.00, "note": "fore feather — white follows leg marking" } },
    "feet":       { "density": 0.90, "length_m": 0.220, "length_variation": 0.35, "curl": 0.05, "clump": 0.45, "frizz": 0.25, "colour": { "root": "#e8e2d2", "tip": "#f2ecdc", "pattern": "solid" }, "layer": { "structure": "mane-hair", "undercoat": 0.00, "note": "hind feather — typically >= fore" } }
  } }
```

---

## 10. Cross-species reading (what the table teaches the system)

1. **Two allocation strategies for "double coat."** Wolf/fox/bear/St. Bernard spend
   their budget on *undercoat* (guard is the minority layer); the badger spends it
   on *guard hair* with a token undercoat. Same `structure: "double"` label,
   opposite groom behaviour — this is why `layer.undercoat` is a number, not a flag.
2. **The longest zone is the species signature, and it moves:** wolf → ruff/shoulder
   crest; fox → tail; fennec → ear lining + soles (coverage, not length); lion →
   mane system only; bear → withers + (moon) ruff; badger → dorsal skirt;
   St. Bernard → thighs + tail; Clydesdale → feather + mane/tail. A generic
   "longest at ruff" default would be wrong for five of eight.
3. **Seasonality has three shapes:** carnivore coat-blow (length + undercoat
   collapse), horse body-only seasonality (hair systems invariant), and
   lion/fennec near-zero. The `seasonal` block must stay per-profile; there is no
   global summer switch.
4. **Sparse is a species trait, not a defect:** badger belly (0.25, skin shows) and
   lion body (single layer, ~15 mm) are *correct* at values that would be a bug in
   the wolf profile. QA ranges must be per-profile.
5. **Colour pattern is a hair-shaft property** (`agouti` wolf, `banded` fox/badger,
   `tipped` bear/lion-mane/fennec, `solid` elsewhere) and is *independent* of the
   markings layer that paints regions — both are needed; neither substitutes.

## 11. Sources

- Wolf pelage (structure, zonal lengths, mid-back 60–70 mm, shoulder guards
  90–130 mm, seasonal shed): Wikipedia, *Wolf* § Pelage, citing Mech and standard
  mammalogy refs; corroborated by wildlife-education sources (guard hairs to
  ~4 in, undercoat loft to 2.5 in).
- Red fox coat (triad follicles, underfur ~35 mm grey, guard longest on tail;
  dorsal guard mean ≈ 6.02 cm): WildlifeOnline, *Red Fox Appearance*, citing
  Maurel et al. 1986, *Can. J. Zool.*; canid guard-hair microscopy study (Turkish
  canids) for the 6.02 cm figure; seasonal moult: Animals Around the Globe and
  The Fox Project seasonal records.
- Fennec (long soft thick coat, dense undercoat, long white ear lining, densely
  furred soles, pale sand colour): The Animal Map; KnownAnimals; Branta Media —
  all general species accounts; **no millimetre measurements exist in these
  sources, hence the heavy [E] tagging in §3.**
- Lion (mane ≤ 16 cm, distribution incl. elbows/belly, short body hair, longer
  underparts, tail tuft): San Diego Zoo / IELC fact sheet citing Wilson &
  Mittermeier 2009 and West & Packer; mane hair 8–22 cm: *Barbary lion*,
  citing museum skin measurements; mane development/testosterone/climate:
  West & Packer 2002, *Science* (via ResearchGate).
- Brown bear (double layer, winter withers 11–12 cm, guard 3–4 in, grizzled
  tipping, summer thinner): *Bear Morphology* (Garshelis et al., Encycl. Animal
  Behavior / ResearchGate); CAMEO (MFA Boston) fibre record; Vectree *Ursus
  arctos* plate. Moon bear (ruff to ~6 in, long coarse neck/shoulder mane,
  chest crescent, shoulder-thick coat): WorldAtlas Asiatic black bear account;
  Britannica, *Asiatic black bear*.
- Badger (winter guard mid-back 75–80 mm, bristly guards + sparse soft undercoat,
  belly short/sparse with skin visible, summer coarser/shorter/darker, tail long
  and coarse): Wikipedia, *European badger* § Fur (Heptner & Naumov mammalogy
  tradition); Badgerland pelage notes (back hair to 75 mm, black pointed tip).
- St. Bernard (double coat, undercoat short/very dense/soft; variety zonal length
  distribution, ruff, feathering, bushy thighs/tail, tail base→tip gradient):
  UKC breed standard, *Saint Bernard* § Coat; AKC-standard summaries via
  Basepaws/Rover for the biannual shed.
- Clydesdale & horse (body hair 12.2 mm summer / 47.0 mm winter means, coat mass
  ratio; primitive winter outer 5.8 cm, underhair 2.2–2.9 cm; mane hair Ø ~110 µm):
  Jenner et al., *Hair coat properties of donkeys, mules and horses*, Equine Vet.
  J. (DOI 10.1111/evj.12775); JFAE 2006, *Factors that influence coat hair length
  in primitive horses*. Feather (posterior knee/hock origin, must cover hoof,
  straight/silky preferred) and mane/forelock abundance: Australian Heavy Horse
  Association showing handbook, Clydesdale standard; SeaWorld Clydesdale
  characteristics (hair-system definitions).

## 12. Honest gaps

- **No sourced hairs/cm² exists by zone for any roster species** — density is a
  normalised design scale [E] anchored on sourced qualitative extremes. If a
  future agent finds pelage-density lab data (fur-science literature), recalibrate
  §0.3's anchor, don't just bolt numbers on.
- Fennec lengths are entirely [E] (sources are qualitative); lion *body* lengths
  are [E] (sources say "short" and measure only the mane); St. Bernard lengths are
  [E] translated from standard language ("short/medium/very bushy") — the
  *distribution* is [S], the millimetres are mine.
- Anthro scaling: these are quadruped-animal measurements. On human-scale anthro
  bodies, keep densities and *ratios* and scale lengths by character height ÷
  species shoulder height only as a starting guess — that rescale rule itself is
  [E] and unvalidated.
