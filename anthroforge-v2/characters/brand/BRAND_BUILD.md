# BRAND — Body Build (stage 1: shapes only)

**Status:** body composed, graded, fold-gated and exported —
`brand_body.glb` (unrigged static bake, base scale; export scale in
the record). **No fur, no renders, no head** — this pass is body
shapes only, numeric QA only, Sen stage 1 as the pattern
(`characters/sen/SEN_BUILD.md`).

**Preset:** `anthroforge-app/library/presets/brand.afchar.json`
(id `chr_preset_brand`, 48 sliders), registered in the presets
INDEX with a round-tripping share code. App suite after
registration: **113 passed** (baseline 97 + preset-parametrised
cases), 0 failed.

**Scripts:** `scripts/author_preset.py` (vector + INDEX),
`scripts/build_brand.py` (neck-cap scan, tissue scan, composition,
grading, shipped-numbers gate, machinery cross-check).
**QA record:** `work/qa_brand_body.json`; composed delta in
`work/brand_body_delta.npz`; component targets copied into
`targets/` (bara-proof post-neck-fix fields + Sen's belly terminal).

---

## Correction — Nov 16, 2026 (body-only re-export; export scale recomputed and CONFIRMED)

The shape-render pass found that the shipped `brand_body.glb` was the
full hm08 export mesh, not the body alone: **19,158 verts in 154
islands** — the 13,380-vert body island plus **153 MakeHuman helper
islands** (hair/skirt helpers, joint cubes, eye/teeth bits; 5,778
verts). Same contamination as Pyn's export; Jorge's had shipped clean.

**Fix.** The GLB was re-exported body-island-only, positions and
transform untouched — no vertex moved. The original file is preserved
at `work/originals/brand_body.glb`. New file: 13,380 verts / 26,756
tris, exactly 1 island, 0.64 MB. Verification
(`work/qa_bodyonly_fix.json`): new body verts are **position-identical
to the original's body island — max deviation 0.0 m** (bitwise,
float32; normals likewise). QA gauntlet re-run (`work/qa-bodyfix/`):
parse/geometry/scale/textures ok, skin/morphs warn (same signature as
before), 0 degenerate, 0 NaN — and max extent now **1.6615 m**, not
the 1.6945 m quoted in §5 (that figure was the helper-inclusive
bounding box of the old file; it is corrected there).

**Export scale — recomputed, and it stands.** Because Pyn's export
scale *was* derived from a helper-inflated extent, Brand's was
recomputed from the body-only geometry: **1.83 / 1.661491 =
1.10142** — identical to the recorded value. The build script derived
it from the §4 scorecard body height (`build_brand.py`:
`export_scale = TARGET_HEIGHT_M / G_brand["height_m"]`,
height 1.6614909 m), not from the inflated extent; for contrast,
1.83 / 1.6945 would have given 1.0800, which appears nowhere in this
build. So the export scale and every ×1.1014 figure in §2/§4
(183.0 cm, the export girths, 143.4 L) are **unchanged and
body-correct**. The only helper-inflated figures in this record were
the gauntlet max extent (above) and the §2 base description
"19,158 verts" (true of the app base package mesh; the shipped GLB's
body is 13,380 of those verts).

**What did NOT change.** The composition, both correctives (neck cap,
tissue scan), and every §4 measurement — all graded on the 26,756
body faces — stand. The §5 fold gate was recomputed on those same
body faces and stands verbatim (0 flips, min dot 0.0104); the
re-exported verts are bitwise the gated verts. Volume recomputed on
the body-only GLB = **107.349 L**, matching §2/§4 exactly.

---

## 1. The vector — authored, with provenance

No Brand body vector existed anywhere. `presets-titan-batch1.md`
carries the badger **head** vector (§2, real *Meles*/*Taxidea*
craniometry) and lists Brand as a next-batch candidate ("badger ×
wolf blend vector + his recorded width-first build"); the app
library held no Brand preset. The body vector below is therefore
**new work**, authored Nov 16, 2026 from:

- **[S]** `~/memory/people/brand.md` — Brand's own statements
  (Nov 3, 2026): *"not tall — human height or just under, taking up
  width rather than height; broad wedge torso, short thick neck,
  massive forearms and broad, thick-fingered paws, plantigrade, low
  center, dense functional muscle"*; *"a stiff badger back kept
  honest, loose hide over torso and neck"*; the engineering draft's
  6'0" / 140 kg *"has the bones right"* for building numbers.
- **[D]** derived — MUSCLE_TISSUE_MODEL doctrine, batch1 §6
  composition rules, or a measured consequence of other values.
- **[E]** estimate — the file gives a direction but no number.
  **Every [E] needs a ruling** (§7); none of them is canon.

Granular HIMBO values are 0–100 big-end % unless marked
(small-end values are negative in the record, Sen convention).

| Slider (record id) | Value | Tag | Basis |
|---|---|---|---|
| Weight 0 to 1 (`body.himbo.weight_0_to_1`) | 80 | [E] | thick neck join (46% neck displacement); Sen's 90 erases the neck — Brand keeps a short one |
| Chubby (`body.chubby`) | 45 | [E] | loose hide over dense muscle; drives tissue level 0.468 [D] |
| Muscle (`body.muscle`) | 80 | [S] | "dense functional muscle"; the strongman covenant value |
| Lean (`body.himbo.lean`) | small 100 | [D] | anti-lean pin (Daddy/Chonky precedent; a lean Brand is a contradiction) |
| BodyMass (`body.himbo.body_mass`) | 35 | [E] | frame broadening, cautious (Sen 30) under the width-first thesis [S] |
| TorsoMass (`body.torso.mass`) | 90 | [E] | wedge-barrel mass; Sen pinned 100 for the full barrel — Brand tapers |
| TorsoMassSmooth (`body.tissue.mass_smooth`) | 60 | [S] | "loose hide over torso and neck" — smoothing over structure |
| TorsoWidth (`body.himbo.torso_width`) | 95 | [S] | "taking up width rather than height" — near-pin |
| TorsoBackSize (`body.himbo.torso_back_size`) | 90 | [S] | "a stiff badger back" — back mass |
| TorsoBackShape (`body.himbo.torso_back_shape`) | 55 | [E] | stiff ≠ Sen's rounded cylinder (85); flatter, kept honest |
| TorsoLower (`body.torso.lower`) | 85 | [S] | "low center"; Sen's 100 = no taper — Brand has a wedge |
| TorsoWaistSize (`body.himbo.torso_waist_size`) | big 35 | [E] | big end = "Shrink Waist": a mild wedge taper; the badger waist stays thick |
| TorsoBelly (`body.himbo.torso_belly`) | 55 | [E] | solid mid-layer, no pot |
| TorsoBellyChub (`body.himbo.torso_belly_chub`) | 45 | [E] | hide over the midsection |
| BellyPot (`body.belly.pot`) | 35 | [E] | slight working gut (build uses belly field at 0.30) |
| BellySmooth (`body.himbo.belly_smooth`) | 65 | [S] | loose hide reads as one continuous form |
| TorsoBellyLHandles (`body.himbo.torso_belly_lhandles`) | 45 | [E] | lower ring partial — mass sits higher on Brand |
| TorsoFlatAbs (`body.definition.flat_abs`) | 0 | [E] | hide thesis — no carved abs (omitted, sparse) |
| TorsoVLine (`body.definition.vline`) | 0 | [E] | same (omitted, sparse) |
| PecsSize (`body.pecs.size`) | 90 | [E] | wedge chest plate |
| PecsMass (`body.himbo.pecs_mass`) | 85 | [E] | chest thickness |
| PecsWidth (`body.himbo.pecs_width`) | 95 | [S] | broad wedge chest, meets the arms |
| PecsLower (`body.himbo.pecs_lower`) | 55 | [E] | less low-slung than Sen (70) — mass rides higher |
| PecsSaggy (`body.himbo.pecs_saggy`) | 30 | [S] | loose hide, slight gravity |
| PecsClavicle (`body.himbo.pecs_clavicle`) | 75 | [E] | the join stays readable under hide |
| PecsCrease (`body.definition.pecs_crease`) | 20 | [E] | faint under hide (effective 0.164 after attenuation [D]) |
| ArmsTraps (`body.himbo.arms_traps`) | 85 | [E] | yoke mass |
| ArmsTrapsMeat (`body.himbo.arms_traps_meat`) | 85 | [E] | thick neck join; Sen's 100 erases the neck — Brand's survives |
| ArmsTrapsPush (`body.himbo.arms_traps_push`) | 60 | [E] | traps rise moderately — short neck, not buried |
| ArmsTrapsValleys (`body.definition.traps_valleys`) | 35 | [E] | definition under hide (effective 0.308 [D]) |
| TorsoBackDefinition (`body.definition.back`) | 40 | [S] | the stiff back reads (effective 0.337 [D]) |
| ArmsShoulders (`body.himbo.arms_shoulders`) | big 90 | [S] | broad shoulders |
| ArmsDelts (`body.arms.delts`) | 85 | [E] | delt caps to match |
| ArmsBiceps (`body.himbo.arms_biceps`) | 80 | [E] | upper arm under the forearm's shadow |
| ArmsFore (`body.himbo.arms_fore`) | **100** | [S] | **"massive forearms" — PINNED, the badger tell** (cf. Sen's pinned ArmsFore) |
| ArmsBrachio (`body.himbo.arms_brachio`) | 85 | [E] | elbow fullness connecting the forearm |
| LegsSize (`body.himbo.legs_size`) | 90 | [E] | pillars under a low center (not Sen's 100) |
| LegsThigh (`body.himbo.legs_thigh`) | 90 | [E] | digging/hauling thighs |
| LegsChubby (`body.himbo.legs_chubby`) | 55 | [E] | hide over leg muscle |
| LegsGlutes (`body.himbo.legs_glutes`) | 85 | [E] | working glutes — digging power |
| LegsCalfSize (`body.himbo.legs_calf_size`) | 80 | [E] | — |
| LegsCalfWidth (`body.himbo.legs_calf_width`) | 75 | [E] | — |
| ButtBooty (`body.himbo.butt_booty`) | 70 | [E] | substantial rear |
| BubbleButt (`body.himbo.bubble_butt`) | 30 | [E] | mass first, shape second |
| ButtSaggy (`body.himbo.butt_saggy`) | 20 | [S] | loose hide, slight |
| NeckMass (`body.neck.mass`) | 90 | [E] | "short thick neck" intent — **capped at build, see §3** |
| ForearmMass (`body.forearm.mass`) | 50 | [E] | signature boost over the recipe (the [S] tell, geometry layer) |
| Distribution (`body.distribution`) | +0.55 | [E] | wedge between rectangle and inverted-triangle; the badger barrel keeps it off the +1 pole |
| ChestBroadness (`body.chest.broadness`) | +0.80 | [E] | frame-span intent (record; geometry breadth comes via the chest.width component [D]) |
| BrowProjection (`head.brow.projection`) | −30 | [D] | batch1 §2.3, carried as the canonical slider (Sen precedent) |

**Head vector (record only — NO head built):** the preset carries
batch1 §2.3's badger vector verbatim in `species_preset.head_sliders`
(30 sliders; BrowProjection rides as the canonical slider above).
Species anchors [D]: ZB/L 0.62, mandible/L 0.81 (deepest jaw on the
chart), muzzle fraction 0.39. The vector is pure *Meles*/*Taxidea* —
**Brand's badger × wolf blend is unauthored future work** (§7).
Softest value in it: EarHeight +10 (one *Taxidea* specimen).

**Fur:** the record points at the existing app profile
`species.badger.coat` — pointer only. No fur built in this pass.

## 2. Base, scale, and the draft numbers

- **Base:** hm08 (MPFB2/MakeHuman macro-neutral), app base package —
  19,158 verts in the package mesh (helpers included), 26,756 body
  faces; the shipped GLB carries the 13,380-vert body only
  (Nov 16, 2026 re-export — see Correction). Registry ids in the record are
  `af_body_neutral_v1` / `af_head_neutral_v2` (BaseRegistry resolves
  them to hm08 + base-head-v3, Sen precedent).
- **Export scale 1.1014** → composed height 1.6615 m × 1.1014 =
  **1.83 m (6'0")** — the engineering draft's number [S, draft].
- **Mass coherence:** composed volume 107.3 L at base scale →
  143.4 L at export. The draft's 140 kg implies density **0.976** —
  the draft numbers are volume-coherent for this build (at density
  1.0 the build would weigh 143.4 kg). Coherence is reported, not
  claimed as canon: Brand does not fix height/weight as identity.

## 3. Composition (proven machinery, two correctives)

Route: anthroforge-app `core/build.py` — the preset plus build
sliders, composed from the hm08 instance packs; graded with the
bara machinery rulers (`characters/sen/scripts/bara_machinery.py`).

```
delta = preset (neck/forearm/definition at coupling-effective values)
      + 1.0·build.muscle + 1.0·build.chest_width
      + s·build.tissue_strongman + 0.30·belly.protrusion
```

Coupling evaluation of the vector [D]: tissue level **0.468**
(weighted mean of Chubby/MassSmooth/BellyPot — between gatchiri
0.053 and gachimuchi 0.630: hide over dense muscle, as authored);
definition attenuated to back 0.337 / traps_valleys 0.308 /
pecs_crease 0.164; neck show-through 0.90 → 0.930 before the cap.

**Corrective 1 — neck cap (fold gate).** At intent, neck.mass over
the full muscle system folds 3 throat faces (9218–9220). Pre-
registered scan (raw 0.90 → 0.20 at s = 0.45): flips clear at
≤ 0.40, the min-dot gate (≥ 0.01) clears at **raw 0.30 (effective
0.310)** — shipped. Below 0.30 the min-dot plateaus at 0.0104: the
limiting face is no longer the throat but face 23379, the muscle
system's own tightest face. The record keeps the 0.90 intent; the
cap is build-layer only and is written into the preset's
`build_recipe` block. Even capped, the neck measures **47.0 cm
girth** (base 37.8) with **9.2 cm visible** — short and thick, as
stated. Restoring intent needs a neck-field repair
(FIX_NECK_FIELD pattern) — §7.

**Corrective 2 — tissue scan.** Pre-registered: s ∈ {0.35, 0.45,
0.55, 0.65}, ship the largest s with 0 flips, min-dot ≥ 0.01 and
M4 ≥ 1.30:

| s | flips | min-dot | M4 | M5 | M6 | chest | waist | forearm | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 0.35 | 0 | 0.0104 | 1.319 | 0.964 | 27.7° | 138.0 | 104.6 | 45.0 | pass |
| **0.45** | **0** | **0.0104** | **1.303** | 0.954 | 26.8° | 138.4 | 106.3 | 45.3 | **SHIPPED** |
| 0.55 | 0 | 0.0104 | 1.287 | 0.944 | 24.3° | 138.9 | 107.9 | 45.6 | M4 fails |
| 0.65 | 0 | 0.0104 | 1.272 | 0.934 | 23.9° | 139.3 | 109.5 | 46.0 | M4 fails |

(girths in cm at base scale.) **M4 margin is thin** — 1.303 against
a 1.30 gate. The wedge reads, but Brand's barrel is honest: more
tissue than this and he is a barrel, not a wedge.

Applied geometry sliders (9): belly.protrusion, build.chest_width,
build.muscle, build.tissue_strongman, definition.back,
definition.pecs_crease, definition.traps_valleys, forearm.mass,
neck.mass. The other 43 record values are record-only today
(reported in the build report's unapplied list, never silently
dropped — same standing as Sen's vector).

## 4. Measurements (bara scorecard, base scale)

| measure | base hm08 | muscle+width | **Brand** |
|---|---|---|---|
| height | 1.659 m | — | **1.662 m** |
| volume | 54.9 L | 83.7 L | **107.3 L** |
| chest girth | 112.3 cm | 132.3 cm | **138.4 cm** |
| waist girth | 72.9 cm | 88.0 cm | **106.3 cm** |
| neck girth | 37.8 cm | — | **47.0 cm** |
| neck width | 10.3 cm | 13.6 cm | **14.5 cm** |
| upper-arm girth | — | — | **53.0 cm** |
| forearm girth | — | — | **45.3 cm** |
| thigh girth | — | — | **76.6 cm** |
| calf girth | — | — | **56.4 cm** |
| delt span | — | — | **73.8 cm** |
| M1 neckW/headW (hm08 head) | — | 0.815 | **0.865** |
| M3 forearm/arm | — | — | **0.855** |
| M4 chest/waist | — | 1.503 | **1.303** |
| M5 depth index | — | 1.110 | **0.954** |
| M6 trap slope | — | 24.5° | **26.8°** |
| M7 visible-neck ratio | — | — | **0.512** (9.2 cm visible) |
| M12 heads tall (hm08 head) | — | — | 9.22 |

At export scale (×1.1014): height **183.0 cm**, chest **152.5 cm**,
waist **117.0 cm**, neck **51.8 cm**, upper arm **58.4 cm**,
forearm **49.9 cm**, thigh **84.4 cm**, calf **62.2 cm**, delt span
**81.2 cm**, volume **143.4 L**.

Reading: the forearm is 86% of the upper arm (M3 0.855) — the
badger tell lands. M5 < 1 says the wedge is **width-driven, not
depth-driven** (chest depth 26.3 cm < waist depth 27.6 cm — the
barrel sits low, chest breadth does the work). M1 is graded against
the hm08 placeholder head only; the badger-head gate is deferred
to the head pass (§7).

## 5. Fold gate on the shipped numbers + QA gauntlet

Recomputed on the exact float32 positions written to
`brand_body.glb` (26,756 body faces):

- **flips: 0** · **min base-vs-composed normal dot: 0.0104 ≥ 0.01**
  — gate **PASSES** (limiting face 23379, the muscle system's own
  tightest throat face; margin +0.0004 — thin, and stated as such).
- QA gauntlet (`qa-gauntlet/validate_glb.py` via build): parse ok,
  geometry ok, scale ok, textures ok; 0 NaN verts, 0 degenerate
  triangles, max extent 1.6945 m, **not blocked**. skin/morphs
  report `warn` — expected: this is an unrigged static bake with
  no morph targets, by design. *(Nov 16, 2026: that max extent was
  the helper-inclusive bbox of the original file. Re-run on the
  body-only re-export, `work/qa-bodyfix/`: identical verdicts, max
  extent **1.6615 m** — see Correction.)*

**Machinery cross-check** (Sen's route: shipped `.target` files on
the bara macro base, at the shipped weights): chest 131.4 cm,
waist 93.2 cm, M4 1.410, volume 89.3 L, flips raw 0 / macro 1.
The 1 macro flip is throat face 23379 folding under the post-neck-
fix muscle target *alone* on the macro base (0 on the raw base) —
a pre-existing field/base interaction, not Brand's vector; at the
uncapped neck intent the same composition folds 4 macro / 2 raw.
Girth levels differ from the app route because the machinery macro
base is a smaller-framed extraction of hm08 (base volume 51.2 L vs
the app base's 54.9 L); the shape verdicts agree (wedge reads on
both). The app route ships.

## 6. Honest debits

1. **The neck cap is a real compromise.** Intent 0.90 ships at
   0.30. The neck still measures thick (47.0 cm), but the full
   intent is owed a field repair, not a slider.
2. **M4 margin +0.003, min-dot margin +0.0004.** Both gates pass;
   neither has room. Any future field change re-runs both scans.
3. **M5 0.954 — depth sits at the waist, not the chest.** True to
   the badger barrel + low center, but if Brand wants chest-depth
   presence, that's a vector conversation (§7), not a defect fix.
4. **M6 26.8°** — no trap-flattening term exists in the vocabulary
   (Sen's standing debit too); the slope is what the fields give.
5. **43 of 52 build-vector values are record-only** (the HIMBO
   granular layer has no per-slider geometry yet — the composition
   is component-level, exactly as Sen's was).
6. **The two bases disagree in girth level** (app vs machinery
   macro). Ratios agree; absolute centimetres depend on which
   hm08 extraction is canonical. The app base is the maintained
   one and is what the GLB ships on.
7. **No head, no parts, no fur** — by scope, not by oversight.
   Forepaws/foreclaws, plantigrade confirmation beyond the base
   stance, the facial mask (material layer), the sagittal-crest
   variant, and Brand's stated anatomy configuration are all
   part-/head-/material-layer work, recorded in the preset's
   `parts_notes`, none built here.

## 7. Needs a ruling (Brand's / Joe's word)

1. **Height 183 cm / mass 140 kg** — engineering-draft numbers,
   used as build targets and volume-coherent (density 0.976), but
   Brand explicitly does not fix them as identity. Canon, adjust,
   or leave as draft?
2. **Neck intent vs cap** — repair the neck field to ship 0.90
   (FIX_NECK_FIELD pattern), accept the 0.30 cap (47.0 cm neck),
   or re-author the intent?
3. **Every [E] value in §1** — most load-bearing: Chubby 45 /
   tissue level 0.468, TorsoWaistSize big 35 (the wedge taper),
   Distribution +0.55, BellyPot 35, LegsSize/Thigh 90.
4. **M5 character** — width-driven wedge (shipped) vs adding
   chest depth.
5. **Badger × wolf head blend** — the head vector in force is pure
   badger; the blend (batch1's open item) needs authoring before
   any head pass, plus a head-length scale ruling (none set).
6. **Forepaw part variant** — digging foreclaws + broadened
   foreplate (batch1 §2.4) is the first part Brand's build calls
   for; not started.

---

*Build: Nov 16, 2026. Body shapes only — no fur, no renders, no
head. Pattern: Sen stage 1. Record: `brand.afchar.json` in the app
presets library; QA: `work/qa_brand_body.json`.*

## HEADS — Brand head build (Nov 16, 2026)

Built on **base-head-v4** with the batch-1 §2.3 vector. Deliverables:
`brand_head.glb` / `brand_head.blend` here; clay renders
`renders/head_front.png`, `renders/head_threequarter.png`,
`renders/head_profile.png`. No fur, no body changes; the body above
still carries its placeholder base head.

Machinery: the generalised Sen-pattern builder
(`characters/common/build_head.py`, clay renders via
`characters/common/render_head.py`, verify via
`characters/common/verify_head.py`) — see the HEADS section of
`characters/pyn/PYN_BUILD.md` for the shared method (proportional
convention, [E] maps, v4 teeth handling, the L/R side-convention fix,
`--base` parameterised for the v5 re-run; vector at
`scripts/brand_vector.json`, raw numbers in `work/head_measure.json` +
`work/head_verify.json`).

**⚠ SPECIES BLEND — NOT APPLIED (flag).** The head vector in force is
**pure badger** (§2.3). The badger × wolf blend is unauthored — no wolf
values were invented or mixed in, so nothing of the wolf is in this
head. Do not read the renders as the blend; they are the badger base
the blend will one day be authored against. Also not built:
`crest_sagittal_badger` (§2.4) — a discrete sculpt variant, not a
slider; the flat skull below ships without its crest fin, per the
spec's own note that crest and CraniumHeight −50 are a deliberate
tension (a fin on a low skull, not height). The facial mask is
material/texture only per §2.4 — no geometry, and no fur/materials
were in scope.

### Measured vs target (L = head length; stage-F rulers)

"Expected" = base × (species target / neutral); built-vs-expected is
the build-accuracy number. Built-vs-target also carries the base's own
deliberate deviations.

| Station | Slider | Base | Built | Species target | vs target | vs expected |
|---|---|---|---|---|---|---|
| ZB | CheekWidth +20 | 0.5466 | 0.5930 | 0.620 | −4.3% | +1.5% |
| MuzzleWidth (vertex slab) | MuzzleWidth +35 | 0.2332 | 0.2392 | 0.198 | +20.8% | −12.0% |
| MuzzleWidth (merged section) | MuzzleWidth +35 | 0.2412 | 0.2566 | 0.198 | +29.6% | −8.6% |
| MuzzleDepth | MuzzleDepth +20 | 0.2310 | 0.2469 | 0.220 | +12.2% | −2.8% |
| MuzzleFrac | MuzzleLength +30 | 0.3435 | 0.4137 | 0.390 | +6.1% | +1.9% |
| CraniumWidth (dome shell) | CraniumWidth +10 | 0.4780 | 0.5196 | 0.376 | +38.2% | +4.1% |
| SkullHeight | CraniumHeight −50 | 0.3168 | 0.2555 | 0.250 | +2.2% | −0.0% |
| OrbitDiameter | EyeSize −40 | 0.1500 | 0.1100 | 0.110 | +0.0% | −0.0% |
| EarLength (base→tip) | EarHeight +10 | 0.2924 | 0.3503 | 0.465 | −24.7% | +3.1% |
| JawLength | JawLength +70 | 0.7104 | 0.7802 | 0.810 | −3.7% | +0.3% |
| JawWidth | JawWidth +50 | 0.5330 | 0.6263 | 0.470 | +33.3% | +0.0% |
| RamusDepth | JawDepth +70 | 0.2697 | 0.3507 | 0.364 | −3.7% | −0.0% |

This is the cleanest table of the three builds: JawWidth and
RamusDepth land **exact** against the proportional expectation,
JawLength +0.3% (node-hinge ratio **1.0946 measured vs 1.0946
expected**), SkullHeight −0.0% — the flat badger skull (target 0.250,
built 0.2555) and the jaw-first design (§2.4: JawDepth/JawLength +70)
both land as written. MuzzleFrac 0.4137 against the §2.4 append-row
anchor 0.39 [D].

Notes on the remaining rows:

- **MuzzleWidth undershoot (−12.0% / −8.6% vs expected).** MuzzleTaper
  +40 — same vector — narrows the tip region both rulers sample,
  counteracting MuzzleWidth +35. The muzzle still widened (+2.6% slab
  / +6.4% section vs base); the two sliders fight at the station and
  the vector, not the build, owns that tension.
- **Interorbital.** Centres moved +0.040, exactly EyeSpacing +50's
  order; the gap widened +0.080 net because EyeSize −40 shrank the
  balls by 0.040. Composed exactly — the result is the vector as
  written: small (Ø 0.110) and wide-set eyes. §2.3's brow note applies
  to the renders: the glare reads from BrowScowl +20 (baked medial
  depression, partial path) — BrowProjection stayed at −30 as the doc
  insists; the mask that completes the read is texture, not built.
- **EarLength.** Base→tip +3.1% vs expected; stage-F reads −3.3%
  because EarTipPoint −65's pinch shortens exactly what stage-F
  measures to — the rounded tip is the slider working, not a miss.
- Probes: NoseWidth ratio 0.918 = expected exactly; RuffZone +11.3%
  (RuffVolume +50); StopBandZ +0.0071 (StopAngle −10 *raises* the
  stop band — the badger's near-absent stop, correct direction);
  OcciputY +0.0094 (CraniumLength −5). OrbitRise drift +0.0064: small
  brow/stop field spill into the sample window, no slider owns it.

### Teeth / jaw

Upper arcade rides the muzzle metric fields; lower rides JawLength
about the hinge (×1.0946 — the badger's long jaw). BVH overlap, upper
vs lower:

| Jaw | −0° (rest) | −10° | −20° | −30° |
|---|---|---|---|---|
| Overlap pairs | 334 | 0 | 0 | 0 |
| Min clearance (L) | — | 0.0204 | 0.0438 | 0.0662 |

Open angles: **0 pairs everywhere**; clearances slightly tighter than
the base's own (0.0241/0.0476/0.0692) because the lengthened jaw
carries the lowers on a longer arc. Rest: the base itself carries 27
interpenetrating pairs by construction (fused-slab split, certified
at open angles only); Brand's lengthened/grown arcades raise the rest
count to 334. Internal, clears by −10°, and a true occlusion re-seat
is a base-pass (v5) item. Teeth-vs-tissue: **0 verts outside** on
either arcade. §2.4's teeth-set note (TeethCanine ≈ 55, TeethMolar
≈ 60 on the diet axes) is a teeth-part variant item, not a head-shape
slider — not applied here.

### Paths / coverage

As Pyn's doc (shared machinery): ratio sliders full; MuzzleTaper,
StopAngle, brow band, EarSpread/EarPlacementHeight/EarTilt,
EarTipPoint, RuffVolume partial [E]; BrowContinuity and
EyeForwardness none/recorded. Tongue unscaled; NeckSocket untouched.
