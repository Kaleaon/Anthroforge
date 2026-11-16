# Slider Engineering — How AnthroForge Gets More Sliders, and How Each One Is Designed, Built, and Shipped

*Nov 12, 2026. Joe's ask: "how to get MORE sliders and how to design them,
the exact code, what they deform, how the mesh is edited."*

*Companion code: `slider-lab/` (this folder's sibling) — every method in
this manual has a runnable implementation there. Companion docs:
`MAKEHUMAN_OMNIVERSAL.md` (canonical record format, §6.1),
`APP_BLUEPRINT.md` (§3.3 record, §6.2 morph engine), `species-head-spec.md`
+ `brow-study.md` (worked design examples).*

*Tagging: **[S]** sourced, **[L]** verified locally on this machine,
**[D]** derived, **[E]** estimate — same discipline as the rest of the
project.*

---

## 0. The one-paragraph version

A slider is a **delta field** — one 3-vector per vertex of a base mesh —
plus a **semantic record** saying what the field *means* (region, endpoint
anchor in metres, range, QA). The mesh is edited by adding weighted delta
fields to bind-pose vertex positions (§C, §D). "More sliders" therefore
comes from exactly four operations: **acquire** more fields (mine,
decode, difference), **transfer** fields to more bases, **author** fields
nobody shipped (procedural), and **multiply** fields (decomposition and
couplings). Everything below is those four operations, made exact.

---

## A. Where more sliders come from

### A.0 Yield table

| # | Source | Raw material in hand / reachable | Canonical sliders yielded | Licence tier | Effort per batch |
|---|---|---|---|---|---|
| 1 | MakeHuman bundled targets | ~1,258 `.target` files [S] | **180–260** [E] | **CC0 — build-tier** | Days (parser + de-gridding) |
| 2 | MH community packs | Animal 01–04 + 5 deformation packs, ~90 targets [S] | **40–70** [E] | CC0 / CC-BY per file | Days |
| 3 | BodySlide corpora (.osd) | HIMBO **126 decoded [L]**; CBBE/3BA/BHUNP/UUNP/SAM sets ~90–170 each [E] | **380–520** after cross-set semantic dedupe [E] | study-tier sources | Hours per set (decoder exists) |
| 4 | `_0`/`_1` pair differencing | Fat Males body/feet/hands = 3 composites [L]; tens more pairs in held mods | composites ×4–8 after decomposition → **100–300** [E] | study-tier | Minutes per pair (exact) |
| 5 | Foreign-topology transfer | fit pipeline, median residual 0.05 cm / p95 0.28 cm [L] | **×0 new semantics — ×N bases**: ~800 canonical × 3 bases ≈ **2,400 instances** [D] | inherits source | One correspondence per base *pair*, then batch |
| 6 | Specimen / scan differencing | 7 species head composites in library; puma CT skull [L]; Poly Haven lion scan [L] | anchors for the **31 head sliders** [D]; **10–15** skull-layer sliders [E] | CC BY — build-tier (held scans) | Days per species |
| 7 | Procedural authoring | brow set **7 [L]**; JawProtrusion, NeckMass (blueprint §3.3); ARKit-style expression set 52 [S]; visemes ~14 [E] | **~95 near-term** [E], unbounded | **ours — build-tier** | Hours per slider (lab pipeline) |
| 8 | Decomposition | demonstrated **1 → 11 records** [L, §E.2] | applied to ~200 suitable sliders → **+1,500–2,000 piece records** [D] | inherits parent | Minutes per slider (automated) |
| 9 | Coupling-derived | tusk angle = f(JawWidth) [L, orc spec]; shelf→aperture compensation | **10–20** [E] | ours | Hours each |

**Vocabulary totals:** headline canonical sliders ≈ **700–1,100** [E];
counting decomposition pieces (independently drivable, sharing parent
data) ≈ **2,200–3,100 records** [D/E]; instances across 3 bases ≈
**2,400+** before pieces [D].

### A.1 Mining MakeHuman's target library (source 1–2)

MH `.target` files are gzip'd ASCII (`index dx dy dz` per moved vertex)
on the hm08 base — `MAKEHUMAN_OMNIVERSAL.md` §2/§6.4 has the full
treatment. The mining caveats that decide the yield:

- **Detail targets mine 1:1.** A bipolar MH modifier is two one-pole
  targets (`…-small`, `…-large`) → one two-pole canonical slider (§C.2).
  ~100 detail modifiers [S] → ~100–150 canonical sliders after grouping
  token variants.
- **Macro targets need de-gridding.** Macro targets are *corners* of the
  macro grid (age × gender × ethnicity × weight…), not independent
  sliders. Sample the grid along one axis at a time (hold the other axes
  at neutral, difference adjacent corners) to synthesise per-axis fields:
  ~24–40 macro-axis sliders [E]. Skipping this step double-counts:
  a "female-old" corner is not a slider.
- **Community packs are per-file licensed** — the importer must read each
  file's licence, not the pack's label (documented mislabels exist).
- Every mined slider lands with provenance `CC0 (MakeHuman bundled)` or
  the per-file CC-BY string. This is our **largest build-tier source** —
  the only big corpus we may ship in the app library without a
  graduation step.

### A.2 Decoding BodySlide corpora (source 3)

The `.osd` format is fully reverse-engineered (`learned/tools/osdparse.py`,
EOF-exact): each block = one slider = sparse (vertex index, xyz diff)
list, applied as `base + diff × value/100`. HIMBO's 126 sliders / 8
categories / 22 presets are decoded [L] (`learned/himbo_sliders_full.json`).

- **Cross-set dedupe is where the yield is.** CBBE, 3BA, BHUNP, UUNP,
  HIMBO and SAM each ship a "breast size", a "belly", a "thigh"… — the
  same semantics on different bases with different fields. Canonicalised
  by (region, anchor), five ~150-slider sets collapse to ~380–520 unique
  semantics [E], each with several per-base instances. The female-set
  hunt (running in parallel) feeds this row.
- **UV/position spaces:** some .osd blocks are UV-space morphs
  (`uv_slider: true` in the decode) — those are texture-space, not shape;
  the importer must route them to the material system, not the slider
  library.
- All BodySlide-sourced sliders are **study-tier** (mod licences). They
  teach shape vocabulary and calibrate anchors; shipping one requires
  graduation (§B.8).

### A.3 Same-topology pair differencing (source 4)

Skyrim's weight system ships two meshes per body part: `_0` (weight 0)
and `_1` (weight 1), **topology-identical** (verified byte-identical
triangle arrays on Fat Males [L]). The morph between them is therefore
an *exact* delta field: `delta = V_1 − V_0`, zero fit error, no
registration. `learned/tools/learn_poc.py` is the extractor; the Fat
Males body field (2,024 verts; mean |Δ| 2.59 units ≈ 3.7 cm, max
10.93 units ≈ 15.6 cm [L]) is the type specimen.

Rules: verify triangle-array identity before differencing (assert, don't
assume — a re-triangulated `_1` silently poisons the field); record the
source frame and unit (Skyrim unit = 0.01428 m [L]) in provenance; a
pair gives **one composite** (the mod author's whole weight change) —
the slider *family* comes from decomposing it (§A.8).

### A.4 Foreign-topology transfer (source 5)

When topologies differ (HIMBO's 9,346 verts vs Fat Males' 2,024 [L]),
fields move through the fit pipeline (`learned/tools/fit_foreign.py`):
trimmed-ICP rigid alignment → non-rigid registration → delta transfer
with normal gating. Measured quality on the HIMBO→Fat Males pair:
**median residual 0.05 cm, p95 0.28 cm** over the well-corresponded
surface [L, FIT_REPORT.md], with named dead zones (flank, genital patch,
196-vert triangle hole) whose deltas must be masked, not transferred.

Economics: correspondence cost scales with **base pairs**, not sliders
(`MAKEHUMAN_OMNIVERSAL.md` §6.2). Build the pair once
(`himbo↔mh08`, `mh08↔anthroforge`, head pair), then every slider on
either base transfers in batch. Transfer **never creates semantics** —
it creates *instances*, each carrying its own residual QA into the
record. A slider whose instance on base B has p95 residual 0.9 cm says
so in the record; the UI shows it (blueprint §7 build order).

### A.5 Specimen and scan differencing (source 6)

Same mathematics as A.4, different source material: register a specimen
(a species head, a CT skull, a photogrammetry scan) to the neutral base;
the difference field, decomposed along the head spec's regions, gives
**measured endpoints** for the species sliders instead of hand-tuned
ones. This is how the 25→31 head sliders get their preset values
(species-head-spec: every cell traced [S]/[D]/[E]) and how the skull
*layer* sliders (cranium width, rostrum length at the bone level) are
anchored. Sources in hand: 7 species head models, the puma CT skull
(CC BY), the Poly Haven lion scan — differencing a *skull* against the
base head's skull layer is also the only honest way to author
bone-layer sliders (muscle/tissue sliders difference against fleshed
specimens).

### A.6 Procedural authoring (source 7)

Sliders nobody shipped, defined by **landmark mathematics**: a region
mask (§B.2) + a deformation law (direction field, radial falloff,
rotation about a hinge) + a measured endpoint anchor. Worked examples:

- **BrowProjection** — brow-study §5.1: calibration from published
  craniometry (`value = 100 × (P − 12.5 mm)/11.4 mm`, Smith & Ranyard
  chords), scale-free form `chord ≈ L × (0.066 + 0.00060 × value)`.
  Authored end-to-end in the lab — §E.1 has its QA numbers.
- **JawProtrusion** — forward jaw *translation* (no shipped slider
  expresses it; orc spec §2): mask the mandible, translate along the
  jaw's forward axis, anchor in mm of chin advance.
- **NeckMass** — HIMBO's Weight block is 46% neck-region verts [L,
  orc spec] but ships no neck slider: mask + radial expansion law.
- **Expression/viseme families** — the ARKit-style 52-blendshape set is
  an industry-standard *vocabulary* [S]; each entry is proce
...[truncated 17114 chars]durally
  authorable from muscle-landmark masks on the layered head (each
  action unit = one mask + one law), and they are the sliders that make
  the bone-driven MH-style face rig interoperable with blendshape
  pipelines.

Procedural authoring is the only source with **zero licence debt** and
the only one that can target the layered construction directly (a slider
can deform the skull layer, the muscle layer, or the tissue layer
independently — the record carries a `layer` field; brow set: 4 bone,
1 muscle, 1 tissue, 1 shared [L, brow-study §5]).

### A.7 Decomposition (source 8)

Multiply a field by **partition-of-unity masks** — weight sets that sum
to exactly 1 at every vertex (§B.2, `mask_tools.band_partition` /
`lr_partition`). The pieces are new, independently drivable sliders, and
the split is **lossless**: pieces sum back to the parent field to float
precision (demonstrated max error 4.4e-16 [L, §E.2]). Standard splits:

- **Side split** (L / R with a soft midline blend) — enables asymmetric
  characters the source slider could never express.
- **Region bands** (height bands, or landmark regions — lower / torso /
  upper on a body; medial / midorbit / lateral on a brow).
- **Crosses** (side × band) as the atomic pieces; groupings (all-left,
  all-torso) as convenience sliders over the same data.

Yield per parent: 2 sides + 3 bands + 6 crosses = **11 records from 1**
[L]. Decomposition is how composites (A.3's whole-weight morphs, A.5's
species differences) become *vocabularies*.

### A.8 Coupling-derived sliders (source 9)

Some sliders exist only as **functions of other sliders**: tusk splay
angle = 5° + 0.25° × JawWidth (orc spec [L]); eyelid aperture
compensation when BrowShelf ≥ +60 ∧ BrowProjection ≥ +80 (brow-study
§5.8); belly→lower-back counter-curve. These ship as records with a
`couplings` entry (blueprint §3.3) and no field of their own — the
runtime evaluates them after the primary vector. Few in number, high in
value: they encode the anatomy knowledge that keeps extreme presets
coherent.

### A.9 Expression and pose families

Expressions and visemes are slider *families* with their own group
(`face/expression`, `face/viseme`): short-range, muscle-layer,
fast-churn (they animate). They follow the same record format; their
endpoint anchors are action-unit intensities rather than metres.

---

## B. How a slider is designed — the methodology

Ten steps. Steps 1–4 are *design* (no mesh touched); 5–7 build the
field; 8–10 make it shippable.

### B.1 Semantic definition

Write the `semantics` sentence first: *"At +1, the ⟨landmark⟩ sits
⟨endpoint⟩ from neutral; 0 = neutral base; −1 = ⟨opposite endpoint⟩."*
If the sentence can't be written, it isn't a slider yet — it's a vibe.
Identity = semantics + region + endpoint anchor, **never the file**
(`MAKEHUMAN_OMNIVERSAL.md` §6.1). Two fields on two bases are the same
slider iff they produce the same landmark-relative change, verified by
QA numbers — not by construction.

### B.2 Region mask construction

The mask is a per-vertex weight field w ∈ [0,1]. Three construction
methods, in order of preference:

1. **Landmark + geodesic falloff** (the lab default,
   `mask_tools.mask_from_landmarks`): an annotator picks landmark vertex
   sets per base *once* (stored with the base: brow band, navel, jaw
   hinge…); the mask is 1.0 within a geodesic plateau radius and
   smoothstep-falls to 0 at a falloff radius. Geodesics are computed by
   Dijkstra over the edge graph (the standard graph approximation of
   true surface distance; the heat method is the upgrade path when
   graph distance shows anisotropy on coarse meshes). Landmark rules are
   *portable* — indices are not — which is what makes the same slider
   definable on every base.
2. **Painted masks**, converted: paint in Blender vertex groups →
   export group membership → smooth with graph-Laplacian passes
   (`mask_tools.laplacian_smooth_mask`) → treat as landmark mask.
   **Warning from the lab [L]:** shipped group sets may overlap
   wholesale (on the v1 base head, *all 368 Brow verts are also inside
   the Muzzle group*). Never use one painted group to *exclude* another
   — group-subtraction carves cliffs into the mask, and cliffs fold
   (54 folds in the lab's first BrowProjection run, §F).
3. **Field-derived masks**: threshold an existing field (e.g. mask =
   where |parent delta| > ε, smoothed) — the decomposition route (A.7).

Mask QA: report `verts_full / verts_partial / verts_any / weight_sum`
(`mask_tools.mask_stats`). A mask whose partial band is wider than its
plateau is usually a falloff radius set wrong for the mesh density.

### B.3 Endpoint anchors in metres

Every slider ships a physical anchor: the displacement of a named
landmark at +1, in metres (e.g. belly: *"max |delta| = 0.156 m at the
navel"* [L]). Anchors are what make sliders comparable across bases and
across sources — a "belly +1" that moves the navel 15.6 cm on Skyrim
and 15.4 cm on hm08 is the same slider; one that moves it 4 cm is a
different slider wearing the same name. Source units convert at import
(Skyrim unit = 0.01428 m [L]; glTF/Babylon = metres; NIF = Skyrim
units). Scale-free anchors (fractions of head length L, torso length)
are used where body size varies (brow-study §5.1 form).

### B.4 Range and safe range

- **Range** [min, max] is the *design* range: where the semantics hold
  (BrowProjection −0.5…+1.5 in normalised units, because its anchors
  live there — modern human 0, Krapina +1.0, gorilla +1.5 [L]).
- **Safe range** is the *measured* range: the largest interval on which
  the QA fold test (§B.6) passes. Determination protocol: sweep the
  field at increasing |value| (the lab sweeps −0.5, +0.5, +1.0, +1.25,
  +1.5), record the first value with in-region folds > 0, bisect once
  if the gap matters, ship `safe_max` = last clean value. A slider may
  legitimately ship `safe_max < max` (BrowProjection: range to +1.5,
  safe_max +1.25 on the animal base head [L]) — the runtime clamps to
  safe_max with a warning (`slider-lab/apply_sliders.js`), it never
  silently folds a mesh.
- Negative direction gets the same sweep; fields are not assumed
  symmetric (recessing a brow is not growing one, run backwards).

### B.5 Symmetry handling

- **Bilateral sliders** (most body/head sliders): the field is
  symmetrised at authoring time using the base's **mirror map** (vertex
  pairing by mirrored nearest neighbour, built once per base):
  `Δ′(v) = ½(Δ(v) + mirror(Δ(m(v))))` with the x-component negated under
  mirroring. Symmetrising kills the lopsided noise that differencing
  and fitting introduce.
- **Side pieces** (decomposition output) are deliberately asymmetric —
  `symmetry: "none"` — and their L/R naming follows the base's mirror
  convention (house rule, verified on the base head's groups: **+x =
  left** [L]).
- Record the symmetry mode in the record; the runtime doesn't guess.

### B.6 QA metrics — every slider ships these

Per instance, in the record's `qa` block:

| Metric | Definition | Gate |
|---|---|---|
| `folds_at_plus1` (+ sweep) | faces whose deformed normal opposes bind normal (dot < 0), counted in-region and total | 0 in-region at safe_max |
| `anchor_displacement` | measured landmark displacement at +1 vs the record's endpoint anchor | within tolerance (proof bar: 5 mm [L, omniversal §8]) |
| `residual_p95` | transfer residual vs source field (transferred instances only) | report, no silent threshold |
| `max_displacement` | max |Δ| over the field, metres | informational |
| `delta_volume` | signed-volume change at +1 (open meshes: indicative only) | informational |
| `diff_verts` | vertices the field actually moves | informational |

Fold test method (exact): per-face normals before/after deformation,
`flip ⟺ dot(n₀, n₁) < 0` (`mask_tools.fold_count`). It is strict — it
flags faces in known-bad base regions even for shipped sliders (the
HIMBO BodyChubby parent shows 14 flipped faces of 17,674 at +1 on its
own base [L]) — which is why the gate is *in-region* folds at
*safe_max*, and why base-mesh defects get recorded as base QA, not
charged to every slider that touches them.

### B.7 Naming and categorisation

IDs are dot-namespaced, lowercase, semantic:
`⟨domain⟩.⟨region⟩.⟨quality⟩[.side][.band]`
(`head.brow.projection`, `body.chubby.left.torso`). Groups (the UI tree)
reuse existing vocabularies so mined and authored sliders sort together:

- **Head** — the species-spec groups: Muzzle (5), Cranium (5), Ears (6),
  Jaw/Cheeks (5), Eyes/Brow (4 + the 7-slider brow set = 11) → **31 head
  sliders** [L, species-head-spec + brow-study §5].
- **Body** — HIMBO's category set is the working taxonomy (its decode
  carries per-slider categories such as "Thighs and Legs" [L]); MH group
  tokens (`nose`, `cheek`, `arms`…) are adopted where they exist
  (omniversal §6.4).
- **Face** — `face/expression.*`, `face/viseme.*` (A.9).
- Decomposition pieces append `.left/.right`, `.lower/.torso/.upper`
  (A.7); coupled sliders carry `couplings`, not fake fields (A.8).

### B.8 Graduation: study-tier → build-tier

A slider's provenance tier is part of the record. **Study-tier**
(learned from mods, scans under restrictive terms) sliders may drive
internal builds and calibrate anchors. **Build-tier** (CC0/CC-BY mined,
procedurally authored, our own scans) may ship in the app library. A
study-tier slider *graduates* by **re-authoring**: reproduce its
semantics procedurally or from build-tier sources, then verify the new
field reproduces the studied landmark anchors within tolerance (the
endpoint anchor is the contract; the studied field was the teacher, not
the payload). Provenance is rewritten honestly at graduation — method
changes, anchor stays.

---

## C. The math

### C.1 Delta fields and the apply rule

Base mesh: bind-pose positions `P ∈ ℝ^{n×3}`, triangles `F`. A slider
instance is a field `Δ ∈ ℝ^{n×3}` (stored sparse: only moved vertices).
Applying a sparse slider vector `{(sᵢ, vᵢ)}`:

```
P′ = P + Σᵢ vᵢ · Δᵢ
```

That is the entire morph engine. Everything else — masks, couplings,
clamps — decides *which* fields and *what values* reach this line
(blueprint §6.2; Core Service resolves, viewport applies:
`slider-lab/apply_sliders.js`).

### C.2 One-pole vs two-pole sliders

- **One-pole** (BodySlide native, MH `…-large`): value 0…1, field
  defined at +1. `P′ = P + v·Δ`.
- **Two-pole** (canonical default): value −1…+1 with **two** fields,
  `Δ⁻` (at −1) and `Δ⁺` (at +1):
  `P′ = P + max(v,0)·Δ⁺ + max(−v,0)·Δ⁻`.
  Two-pole is *not* `Δ⁻ = −Δ⁺` unless the anatomy is truly antisymmetric
  (it rarely is: a hollow belly is not a negative pot-belly). MH bipolar
  modifiers and BodySlide low/high (0-weight / 1-weight) shapes both
  decompose into pole pairs this way.
- Decomposition pieces of a one-pole parent stay one-pole (A.7).

### C.3 Combination: order, normals, and what breaks linearity

- **Pure field addition commutes** — slider order in the vector does not
  change `P′`. This is a theorem of the apply rule, not an approximation.
- **Three things break it, deliberately:** (1) *clamping* — the fold
  guard (§B.4) is value-dependent, applied per slider before summation;
  (2) *couplings* (A.8) — evaluated after the primary vector, in
  dependency order; (3) *correctives* — joint-corrective fields keyed to
  pose, applied in pose space, outside the bind-space sum.
- **Normals are recomputed, never morphed**: after baking `P′`,
  vertex normals = area-weighted face-normal sums, normalised
  (`apply_sliders.js: computeVertexNormals`; Babylon adapter prefers
  `VertexData.ComputeNormals`). Morphing normals with the field is a
  known shortcut and a known artifact source at extremes.
- **Skinning is untouched**: weights are per-vertex attributes,
  independent of positions; joints re-derive from the morphed bind pose
  per base (omniversal §5.6). Sliders encode shape only — never joint
  data.

### C.4 Blend spaces: triangles and poles

Coupled proportions use **barycentric blend spaces** instead of
independent sliders (blueprint §5.3, CREATOR_LESSONS rule 3):

- **Body composition triangle**: poles = (muscle, fat, lean) endpoint
  fields. A point in the triangle has barycentric weights
  `w₁+w₂+w₃ = 1, wᵢ ≥ 0`, and `Δ = Σ wᵢ·Δᵢ(pole)`. The Fat Males field
  and the HIMBO muscle fields are measured pole material [L]; the
  triangle guarantees every interior point is a *convex* mix — no
  extrapolation folds by construction inside the hull.
- **Species pole blends** (GTA-style): species presets are poles;
  hybrid characters are interior points. Same math, head fields.
- UI presents the triangle; the *record* still stores ordinary sliders —
  the triangle is a control surface over three pole sliders with a
  sum-to-1 constraint, evaluated by the runtime like a coupling.

### C.5 Storage formats compared (size math)

Per-vertex costs, measured where marked [L]:

| Format | Layout | Bytes / moved vert | Brow instance (1,431 verts) | Notes |
|---|---|---|---|---|
| **npz sparse (ours)** | int32 idx + 3×float32, zip | 16 raw; **4.9 stored** [L] | **7,055 B** [L] | Canonical instance format. Smooth fields compress ~3×; noisy fields ~1.3× (Chubby piece: 12.7 B/vert [L]) |
| MH `.target` | ASCII `idx dx dy dz` | ~30–38 | ~47 KB (≈7 KB gz) | Interchange with MakeHuman only; indices into hm08 *with helpers* |
| glTF morph target (dense) | float32 accessor, all verts | 12 × n (not per *moved* vert) | 73 KB (6,100-vert base) | What engines load; densifies sparse data |
| glTF morph target (sparse accessor) | int32 idx + float32 values | 16 + overhead | ~23 KB | Legal glTF; most engines densify on import anyway |
| Babylon MorphTarget in RAM | dense Float32Array per target | 12 × n per target | 73 KB per target | **The scaling trap:** 300 targets × 40k-vert base = **144 MB** — never load the library as morph targets |

Consequences, as engineering rules:

1. **Library on disk = sparse** (npz / sparse glTF). A 1,000-slider
   library at ~15 KB average instance size is ~15 MB per base. Trivial.
2. **Viewport = bake on demand.** The runtime resolves the character's
   sparse vector (typically ≤ 60 active sliders) into *one* baked
   position buffer — `apply_sliders.js` does this in O(total moved
   verts), ~ms for a 40k base. GPU morph-target blending is reserved
   for the handful of sliders being actively dragged (live preview),
   then baked on release.
3. **Interchange = dense is fine** (GLB export bakes the character's
   active set into morph targets or a static mesh; the *library* never
   exports itself).

---

## D. How the mesh is edited — the three surfaces

Joe asked "how the mesh is edited". There are exactly three places an
edit happens, and keeping them separate is the architecture:

1. **Offline authoring (files).** Fields are created/edited as data:
   npz sparse deltas, `.target` files, canonical JSON records. Tools:
   `learned/tools/` (decoders, fit), `slider-lab/` (masks, authoring,
   decomposition), MakeTarget/Blender sculpting for hand-authored
   fields (sculpt the base → difference = field). No mesh is ever
   "edited" destructively — the base stays pristine; all shape lives in
   fields. (Learn-then-delete is the intake version of the same rule:
   the model is studied, the *field* is kept, the model is deleted.)
2. **Runtime bake (CPU).** Character = base + slider vector + parts.
   The Core Service (Python) or the viewport (`apply_sliders.js`)
   evaluates §C.1 into a position buffer, recomputes normals, then
   skinning poses it. Bind-pose awareness is the contract: **deltas
   apply to bind-pose positions only**; feeding posed positions into
   the sum double-applies the pose and is the #1 integration bug this
   design invites.
3. **Live preview (GPU).** While a slider is being dragged, the
   viewport may hand that one field to Babylon's MorphTargetManager
   for zero-latency feedback; on release the value joins the vector
   and the CPU bake takes over. Preview and bake must agree to float
   precision — both implement §C.1, and the lab's JS/Python
   cross-check (§E.1) is the regression test.

In Blender terms a field is a *shape key*; in glTF terms a *morph
target*; in BodySlide terms an *.osd block*; in MH terms a *.target*.
Four serialisations of one object — the canonical record is what lets
AnthroForge treat them as such.

---

## E. Worked examples (lab results, Nov 12, 2026) [L]

### E.1 BrowProjection — a genuinely new slider, authored end-to-end

`slider-lab/author_slider.py`, on the neutral base head v1
(6,100-vert Head mesh, glTF frame, L = 1.0). Method: §B.2 landmark mask
(BrowL+BrowR groups, 368 seeds → geodesic plateau 0.025 L, falloff
0.14 L) × forward translation law, magnitude from brow-study §5.1
(0.060 L at normalised +1.0 = Krapina anchor).

| QA metric | Result |
|---|---|
| Mask | 516 verts full + 900 partial = **1,431 moved verts** |
| Anchor vertices | mask weight **1.0** both sides |
| Anchor displacement at +1 | **0.0600 L** (expected 0.060 L — exact) |
| Folds at −0.5 / +0.5 / +1.0 / +1.25 | **0 / 0 / 0 / 0** |
| Folds at +1.5 (gorilla anchor) | **110** → `safe_max = 1.25` shipped in the record |
| Δ volume at +1 | +0.00297 L³ (open mesh — indicative) |
| Instance size | **7,055 B** npz (1,431 sparse verts) |
| JS runtime cross-check | anchor 0.0600 at +1.0; value 2.0 → hard clamp 1.5 → fold-guard clamp 1.25, both warned; bind pose unmutated |

Deliverables: `slider-lab/output/head.brow.projection.json` (canonical
record), `…/instances/head.brow.projection__anthroforge_head_v1.npz`
(+ `.instance.json` for JS), `head.brow.projection.qa.json`.

Honest limits, recorded in the record itself: v1 of this slider is bar
growth by *masked translation* — the post-toral sulcus carve belongs to
`head.brow.shelf` (brow-study §5.3); the glabella moves with the band
(anatomically part of the torus); a hard positional stop-guard was
prototyped and **rejected** (it introduced the folds it was meant to
polish away — §F).

### E.2 Decomposition — HIMBO BodyChubby → 11 sliders

`slider-lab/decompose.py`: parent field decoded from the .osd
(9,229 diff verts — matches the Oct/Nov decode exactly; max |Δ| 3.998
Skyrim units ≈ 0.057 m, matching the POC's 4.00 [L]). Splits: soft L/R
(±2-unit midline blend) × height bands (z<55 / 55–88 / >88, 8-unit
transitions).

| Piece | Diff verts | Mean |Δ| | Max |Δ| |
|---|---|---|---|
| left / right (each) | 4,929 | 0.863 u | 3.998 u (0.057 m) |
| lower | 3,192 | 0.678 u | 1.492 u |
| torso | 3,325 | 1.038 u | 3.998 u |
| upper | 4,231 | 0.683 u | 2.258 u |
| crosses (6) | 1,610–2,300 each | 0.63–0.94 u | band max |

**Exactness: max |Σ pieces − parent| = 4.4e-16** across all three
partitions (crosses, L+R, bands) — decomposition is lossless to float
precision. Parent QA note: 14 flipped faces at +1 on its own base
(§B.6 — base QA, recorded, not hidden). Records:
`slider-lab/output/decompose_chubby_records.json` + 11 instance npz
files (21–63 KB each).

### E.3 What the two examples prove together

A slider can be *born* in the lab (E.1: semantics → mask → field → QA
→ record → runtime, zero third-party geometry) and a slider can be
*multiplied* in the lab (E.2: one decoded field → a family, exactly).
Combined with transfer (A.4), the pipeline from any source in §A to a
shipped, QA'd, per-base slider is closed.

---

## F. Pitfalls — three real failures from this lab, kept as warnings

1. **Group-subtraction masks fold meshes.** Zeroing the brow mask by
   the Muzzle/MuzzleBridge groups (which *contain* the brow on this
   base) carved the plateau to 0 full-weight verts and produced 54
   folds at +1. Rule (§B.2): masks are built by *addition* from
   landmarks; exclusions, if unavoidable, must be smooth positional
   fields, never set subtraction on painted groups.
2. **Smooth guards can be worse than the flaw.** Positional stop
   guards suppressed nothing (glabella weights stayed ~1.0 — the
   medial band is geodesically *part of* the brow) and their gradients
   introduced folds at +1.0. Rule: a mask change is accepted only if
   the fold sweep stays clean — QA gates ergonomics, not intentions.
3. **Multi-source geodesics have a shape trap.** scipy's `dijkstra`
   with multiple indices returns one distance row *per source*, not
   the min — flattening it silently produced a mask covering 106k
   "verts" of a 6,100-vert mesh. Rule: distance fields get a sanity
   assert (shape == n, max ≤ mesh diameter × 1.5) before any mask is
   built on them. (Fixed in `mask_tools.geodesic_distances`.)

---

## G. Code map

| Manual section | Implementation |
|---|---|
| §B.2 masks, §B.6 fold QA | `slider-lab/mask_tools.py` (IO, geodesics, partitions, fold/volume QA) |
| §A.6/§B authoring, §E.1 | `slider-lab/author_slider.py` (spec-driven; BrowProjection shipped) |
| §A.7 decomposition, §E.2 | `slider-lab/decompose.py` (BodyChubby → 11 records) |
| §C.1/§C.3/§D runtime | `slider-lab/apply_sliders.js` (core + Babylon adapter + self-test) |
| §A.2 decoding | `character_assets/learned/tools/osdparse.py`, `himbo_full_decode.py` |
| §A.3 differencing | `character_assets/learned/tools/learn_poc.py`, `nifparse.py` |
| §A.4 transfer | `character_assets/learned/tools/fit_foreign.py` (+ `learned/FIT_REPORT.md`) |
| Record format | `MAKEHUMAN_OMNIVERSAL.md` §6.1, `APP_BLUEPRINT.md` §3.3 |
| Production store | `character_assets/learned/omniversal/` (lab output graduates here per §B.8) |

*Lab outputs from this pass live in `slider-lab/output/` — they are
worked examples with full QA attached, not yet the production store.*
