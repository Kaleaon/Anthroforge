# SEN_BUILD — Sen, end-to-end character build

**Status: stage 1 complete and verified; stage 2 (fur cards + renders) executed 2026-11-13 — see §9.**
Built 2026-11-12 (Blender 5.2.3, MPFB2). This document was reconstructed and
verified after the fact (the original build agent died silently before
reporting): every number below is either read from the build's own work
files (`work/qa_sen_body.json`, `work/head_measure.json`, `work/fur_stats.json`,
the stage logs) or measured fresh with the QA gauntlet
(`qa-gauntlet/validate_glb.py`) on the shipped GLBs. Gaps are listed as gaps,
not smoothed over.

Sen: Titan #10, grizzly × moon bear blend (Asiatic black bear in the blend per
the character record), bipedal. Canon mass 2500 lb / 1134 kg and export height
3.05 m are density/scale facts carried in the record — not slider outputs.

---

## 1. What exists on disk

| Artifact | State |
|---|---|
| `sen_build.blend` (2.87 MB) | Stage-1 final: composed body + bear head + strand groom. Saved 23:02, log-confirmed ("BUILD SAVED (stage 1: body+head+groom)"). |
| `sen_composed.glb` (1.08 MB) | QA-gauntlet verified, §5. |
| `sen_head.blend` (408 KB) | Head layer stack (skull/muscle/tissue). The GLB below carries tissue only; the stack lives here. |
| `sen_head.glb` (633 KB) | QA-gauntlet verified, §5. Authored in head-local units (head length L = 1.0). |
| `targets/` | The four shipped component targets the body was composed from (muscle, chest.width, tissue.strongman, belly terminal v5.1). |
| `work/sen_body_delta.npz` | `delta_sen_canonical_m` (19158×3, float64), the muscle-system delta, and the shipped `tissue_scale`. |
| `work/sen_assembly.blend` (+ `.blend1`) | Pre-groom assembly save from the stage-1 run. |
| `scripts/` | `bara_machinery.py`, `grade_sen.py`, `build_head.py`, `verify_head.py`, `build_body_fur.py` (stage 1), `build_cards_renders.py` (stage 2), `build_record.py` (records, see §7). Stage-2 execution added `build_cards_renders_run.py`, `build_renders_only.py`, `fix_curtain_bake.py`, `rebuild_cards.py` — see §9. |
| `renders/` | Four stage-2 beauty renders landed 2026-11-13: `sen_front.png`, `sen_profile.png`, `sen_threequarter.png`, `sen_head_closeup.png` (640×800). See §9. |
| `fur_card_texture_sen.png` | Curtain bake for card alpha (512×1024). First bake was empty (two defects, §9); repaired bake: alpha mean 0.354. |
| `fur_cards_sen_lod0/1/2.glb` | LOD card sets: 1,700 / 680 / 255 cards, QA-gauntlet clean. See §9. |
| `work/sen_build_stage1.blend` | Byte copy of the pristine stage-1 `sen_build.blend`, taken before stage 2 ran. |
| `work/cards_proof.png` | Verification render of the LOD0 cards alone (scripted front camera, 6 spp). See §9. |
| `work/fur_card_texture_sen_emptybake.png` | The first, empty curtain bake, preserved as defect evidence. |

## 2. Body — composition

Base: **hm08** (MPFB2 / MakeHuman base, macro-neutral), 19,158 verts.
The composition was parsed back from the shipped `.target` files — the
ground truth of what ships, not the pre-repair fields:

```
delta_sen = muscle + chest.width + s · tissue.strongman + belly.protrusion_terminal_v51
```

- **Tissue corrective scan (pre-registered rule):** s ∈ {1.0, 0.925, 0.85,
  0.775, 0.70}; ship the largest s with M5 in [1.05, 1.20] while M4 ≥ 1.25.
  No s qualified (M5 *falls* as s rises toward band from below while M4
  drops), so **s = 1.0 shipped** and the M5 miss is reported, per the rule.
- **Fold gate: 0 flipped faces** (raw and macro) over 26,756 body faces —
  same clean result as the muscle system alone.
- Composed body: volume **98.9 L** (base 51.2 L; muscle system alone 78.5 L),
  height 1.668 m at base scale, chest girth 1.336 m, waist girth 1.026 m.
- For assembly the body was cut at the neck: min-width slice at z = 1.460
  (w = 11.4 cm), cut at z = 1.448 → 9,249-vert headless body, head seated on
  the cut. Landmarks: crotch 0.52, chest 1.15, cut 1.45.

### Body scorecard (bara machinery, from `qa_sen_body.json`)

| Metric | Sen | Reference / gate | Verdict |
|---|---|---|---|
| M4 chest/waist | **1.301** | muscle system 1.522 | in family (matches the bara-proof strongman PASS) |
| M1 neck W / head W (hm08 head) | 0.711 | muscle system 0.703 | — |
| M2 neck/arm, neck/calf | 0.689 / 0.633 | | — |
| M3 forearm/arm | 0.691 | | — |
| M7 visible-neck ratio | 0.169 | | — |
| M8 span / head W | 4.508 | | — |
| M11 thigh/waist | 0.740 | | — |
| M12 heads tall | 7.36 | | — |

### Sen's own §4.2 gates — two honest misses and one structural miss

| Gate | Target | Measured | Verdict |
|---|---|---|---|
| M1 neck W / bear head W | ≥ 1.10 | **0.774** predicted from spec ZB; **0.832** corrected against the built head's tissue width (0.112 m neck / 0.1346 m) | **MISS** |
| M5 torso depth index | 1.05–1.20 | **0.938** | **MISS** (low; no tissue scale in the scan fixes it without breaking M4) |
| M6 trap slope | 20–26° | **32.9°** | **MISS** (high) |

These are the same HIMBO-vocabulary ceiling the bara proof hit (its honest
M2/M3/M5 misses): the composed fields have no neck-broadening term and no
trap-flattening term, so the neck stays narrow against a correctly wide bear
head. The character record carries a `body.neck.mass` 0.90 *intent* slider,
but the composed geometry's formula has no neck field — the slider is a
record of intent, not an applied deformation. Recorded here rather than
hidden, same as the build scripts record it.

## 3. Head — bear vector on base-head-v3

Base: **base-head-v3** (GalileoGB cougar, CC-BY, neutralised), deformed by a
31-slider bear species vector (spec units −100…+100) applied as smooth-field
deformations over the skull → muscle → tissue stack. The full applied vector
and per-slider path audit are in `work/head_measure.json`. Headline values:
MuzzleWidth +40, MuzzleDepth +40, MuzzleTaper −40, StopAngle +40,
EarWidth +55, EarTipPoint −80, JawWidth +55, JawLength −50, RuffVolume +70,
EyeSize −40, EyeSpacing +30, NoseSize +35.

Application paths, honestly graded in the build's own audit:

- **Full:** muzzle (length/width/depth), cranium (W/H/L), forehead, cheeks,
  jaw (depth/width/length), ears (length/width), eyes (size/spacing), nose.
- **Partial:** MuzzleTaper, StopAngle, EarSpread, EarTilt (index sliders with
  estimated field maps); EarTipPoint (tip pinch only — the round-ear
  silhouette variant is a discrete part choice, spec §1.4); EarBaseHeight
  (re-anchored, applied as a 0.02 L drop); the brow family — BrowProjection
  (tissue-band recession), BrowThickness, BrowShelf, BrowPosition,
  BrowPadding, BrowScowl (baked medial depression; the expression system
  owns the live slider); RuffVolume (tissue swell only — **the ruff proper
  is a head fur groom, which was not built**).
- **None:** BrowContinuity (no torus components exist on a non-hominin head
  to split/merge); EyeForwardness (assemblies keep v3's 15° socket yaw;
  convergence is a socket-rig parameter, not a surface field).

Measured rulers, before → after (head-local units, L = 1.0):
muzzle band width 0.234 → 0.304 (**+30.0%**), jaw width 0.538 → 0.642
(**+19.2%**), nose width 0.088 → 0.105 (+19.1%), tongue extent 0.440 → 0.572
(+30.0%), orbit diameter 0.150 → 0.110 (−26.7%), ear base–tip 0.290 → 0.208
(−28.2%), jaw length 0.913 → 0.852 (−6.8%), ZB band 0.527 → 0.522 (−0.8%),
tissue max width 0.547 → 0.557 (+2.0%).

**Tongue:** scaled ×1.3 (Sen canon: huge tongue). Clearance vs the jaw is
**bbox-level only** — the fused teeth-arcade slab (base-head-v3 limitation 1:
one slab that follows both fields and cannot split) prevents a true
occlusion check. Tongue max-forward sits 0.0249 L behind the jaw front.

**Scale:** head length at base scale 0.2414 m; **export scale 1.74** → head
length 0.42 m (large grizzly head) and whole-character height 3.05 m at
export. The scale is a record directive — the GLBs on disk are at base
scale / head-local units, not pre-scaled.

**Eyes:** amber, round (ursid) pupil, per the character record. The head
assembly in the composed GLB carries 20 objects: ears, eyeballs, eyelids,
irises, pupils, lid margins, jaw, nose leather, teeth arcade, throat,
tongue, neck socket + disc, tissue head.

## 4. Fur — strand groom (stage 1 only)

Strand groom built directly on the composed body in `sen_build.blend`
(fur-prototype method: groom → cards was the plan; only the groom exists).
Five regions, from `work/fur_stats.json`:

| Region | Parents | Length | Rendered strands | Colour (authored, linear) |
|---|---|---|---|---|
| ruff | 2,200 | 0.150 m | 8,800 | (0.115, 0.070, 0.038) |
| back | 3,000 | 0.100 m | 12,000 | (0.150, 0.092, 0.048) |
| belly | 2,400 | 0.045 m | 9,600 | (0.165, 0.103, 0.055) |
| coat | 5,200 | 0.068 m | 20,800 | (0.155, 0.097, 0.052) |
| crescent | 700 | 0.055 m | 2,800 | **(0.620, 0.545, 0.400)** pale cream |
| **Total** | **13,500** | | **54,000** | |

Region masks measured on the cut body (verts with weight > 0.5): coat 6,052,
belly 1,225, back 1,094, ruff 1,082, crescent **72** — the chest-crescent
mask is a small, faint patch (mean weight 0.009). The crescent is Sen's
moon-bear chest marking as a **natural pale-fur zone** (fur-colour function,
MARKINGS.md §1.1 target 2) — not a tattoo, not a decal (Joe's correction,
Nov 4 2026). A second recorded zone, the pale forehead mark, exists in the
record only: its exact shape is not described in the person file, so no
geometry or texture was authored for it. That is an open item, not an
oversight.

Coat colour: dark tan/brown; skin palette base `#6B4A2E` in the record.

## 5. GLB verification (QA gauntlet, run for this document)

| | sen_composed.glb | sen_head.glb |
|---|---|---|
| Parses | ok | ok |
| Meshes / primitives | 21 / 21 | 20 / 20 |
| Vertices / triangles | 26,575 / 29,714 | 16,374 / 11,280 |
| Degenerate triangles | 0 | 0 |
| NaN vertices | 0 | 0 |
| Materials | 9 | 8 |
| BBox | 1.091 × 1.536 × 0.464 m | 0.861 × 0.808 × 1.111 (head units) |
| Skin | **none** | **none** |
| Morph targets | **0** | **0** |
| Textures | 0 | 0 |
| Gauntlet status | parse/geometry/scale ok; skin + morphs "warn" | same |

What the warnings mean, plainly: **the composed GLB is a static, unrigged
bake.** The slider composition is baked into the body mesh (that's why the
fold gate could be run on it), the head is placed as rigid objects, there is
no skeleton, no skinning, and no morph targets — the live slider vectors
live in the character records and the `.target` files, not in this GLB.
It is a proof-of-composition assembly, not a deployable character. Rigging
to the 36-bone contract rig and a morph-carrying export are future work,
not hidden defects of the geometry itself (0 degenerate, 0 NaN, clean
parse on both files).

## 6. Pipeline history (from the logs, for honesty)

- The first single-process run (`work/build_body_fur.log`, 22:46) was
  **OOM-killed at stage D** on this 6 GB VM ("Killed" is the last line).
- The pipeline was split; the stage-1 rerun (23:00, `work/build_stage1.log`)
  completed: body bake → head import/seat → GLB export → groom →
  `sen_build.blend` saved.
- **Stage 2 (`build_cards_renders.py`) never ran** in the Nov 12
  pipeline: no log, no card textures, `renders/` empty. LOD fur cards,
  the curtain bake for card alpha, and all beauty renders were absent
  until the 2026-11-13 execution — see §9.

## 7. Records & preset cross-check

`scripts/build_record.py` builds two `.afchar.json` records (sen_titan +
sen_muscle_bear) with share codes via the app core. **Its outputs do not
exist in this folder** — no `characters/sen/*.afchar.json`, no
`work/record_report.json`. Either the script never ran here or its outputs
were superseded; the surviving records are the app-library copies,
`~/workspace/anthroforge-app/library/presets/sen.afchar.json` and
`sen_muscle_bear.afchar.json`, cross-checked against the build here:

- **Body vector: exact match.** All 41 HIMBO values in the app preset equal
  `build_record.py`'s HIMBO dict value-for-value (weight 0.90, chubby 0.80,
  muscle 0.65, lean −1.00, torso_mass 1.00, torso_waist_size −0.60,
  pecs_size 1.00, arms_fore 1.00, legs_thigh 1.00, …). Ids were renamed to
  canonical registry ids by the integration pass (`himbo.*` →
  `body.himbo.*` / canonical singles like `body.torso.mass`,
  `body.definition.traps_valleys`).
- **Muscle-bear variant: exact match, doctrine holds.** The variant preset
  differs from Sen only in tissue values — chubby 0.55, mass_smooth 0.45,
  belly_pot 0.50, pecs_saggy 0.30, traps_valleys 0.55, plus
  `body.definition.back` 0.50 — identical to the script's §4.5 deltas.
  MuscleVector is held exactly; only the TissueVector moves. (The script's
  duplicate namespaced copy `himbo.torso_back_definition` 0.50 was folded
  into the single canonical slider in the app copy.)
- **Head vector: exact match.** The app preset's 30 `head_sliders` equal
  `head_measure.json`'s applied vector value-for-value. BrowProjection −20
  is carried as the canonical `head.brow.projection` slider in both.
  EarLength / EarBaseHeight appear in the app preset under their older spec
  names (EarHeight / EarPlacementHeight) — the preset's own `head_note`
  documents the rename.
- **Discrepancies (recorded, not hidden):**
  - App presets label the bases `af_body_neutral_v1` / `af_head_neutral_v2`;
    the geometry was actually built on **hm08 (MPFB)** and **base-head-v3**.
    The labels are the app registry's base ids, not the build's sources.
  - App presets carry empty `parts[]` and `identity{}`; the build script's
    record has the fuller data (3 parts incl. tongue ×1.3; titan index 10;
    canon mass 1134 kg). Export scale 1.74 and height 305 cm do survive in
    the app copy, under `species_preset`.
  - The script's record-only sliders `body.neck.mass` 0.90,
    `body.chest.broadness` 1.0, `body.distribution` 0.0 do not appear in the
    app preset. Chest broadness corresponds to the chest.width target that
    *was* composed; neck mass has no composed geometry (§2).
- **sen_muscle_bear has no geometry.** By design and documented in the
  script itself: the shipped strongman tissue target is recipe-baked, so
  the variant is record + coupling evaluation only until a tissue field is
  rebuilt at the variant recipe. `sen_build.blend` / `sen_composed.glb`
  are the sen_titan (strongman) build only.

## 8. Open items

1. ~~**Stage 2 never ran**~~ — **done 2026-11-13**, see §9. (The script
   was not in fact ready to run: it referenced five names owned by
   stage 1's process, resolved `SEN` via `Path.home()`, and its
   curtain bake had two independent defects that emptied it. All
   found, fixed, and documented in §9.)
2. **No rig / no morphs in the GLB** — 36-bone contract skinning and a
   morph-carrying export are owed before this is a usable character.
3. **§4.2 gates M1 / M5 / M6 miss** — need a neck-broadening field and a
   trap-flattening term in the tissue vocabulary; not fixable by rescaling
   the existing components (the scan proved it for M5).
4. **Head ruff groom not built** — RuffVolume is tissue swell only.
5. **Forehead mark** — zone recorded; shape undescribed in the person file;
   needs a canon decision before authoring.
6. **Local record outputs missing** — re-running `build_record.py` would
   regenerate `characters/sen/*.afchar.json` + `work/record_report.json`
   and close the provenance gap with the app-library copies.
7. **Tongue/jaw occlusion** — only bbox-checked; a true check waits on the
   split teeth arcade (base-head-v4 work).

*Verification performed 2026-11-12 (finisher pass): GLBs re-validated with
the QA gauntlet; all work JSONs and both stage logs read; app presets
diffed value-by-value against `build_record.py` and `head_measure.json`.
No geometry was rebuilt or modified.*

## 9. Stage 2 — executed 2026-11-13

`build_cards_renders.py` was run by Tinker's finisher pass. It took
three passes and four repairs; every planned output now exists and is
verified. The original script was left byte-untouched; repairs live in
sibling runners (`build_cards_renders_run.py`,
`build_renders_only.py`, `fix_curtain_bake.py`, `rebuild_cards.py`).

### 9.1 Execution history

1. **Full runner** (`build_cards_renders_run.py`): stage D and the
   card build completed (13,500 groom parents extracted; LOD0/1/2 =
   1,700/680/255 cards; GLBs + `work/card_counts.json` written). A
   VM/runtime restart then killed the process ~15 min into stage E's
   first render — no frame landed, no error in the log.
2. **Renders-only pass** (`build_renders_only.py`): stage E executed
   alone; all four beauty renders landed, exit 0, ~25 min.
3. **Curtain-bake repair + card rebuild** (`fix_curtain_bake.py`,
   `rebuild_cards.py`): a texture census exposed the first bake as
   empty (below); both defects were diagnosed with
   `world_to_camera_view`, fixed, the bake re-run, and the cards
   rebuilt against the real texture. A proof render
   (`work/cards_proof.png`, LOD0 cards alone at the scripted front
   camera, 6 spp) confirms the cards now shade — beforehand they
   would have rendered invisible (the card material keys alpha from
   the baked texture, DITHERED).

### 9.2 Blockers found in the never-run script

- **Undefined names.** The script uses `HAIR`, `WORK`, `REND`,
  `neck_axis`, `fdir` — all owned by `build_body_fur.py`'s process.
  Supplied in the runner: colour/work constants copied verbatim from
  stage 1; `neck_axis` recomputed with stage 1's exact formula on the
  saved body ((-0.0001, -0.0845, 1.4439)); `fdir` taken from the stage-1
  log ((0.067, -0.998, 0)).
- **`SEN` via `Path.home()`.** Stage 1 was invoked with
  `HOME=/tmp/af_home`; under the same invocation the script would
  have looked for the blend in a home that has none. Patched to
  resolve from `__file__`.
- **The leftover `Human` object is render-visible** in the saved blend
  (uncut, unfurred, all four slider targets at 1.0). Stage D's
  blanket `hide_render` reset would have left it standing inside Sen
  in every beauty render. The runners hide it after open and after
  the reset. (Stage 1's own renders never saw it — it hid everything
  but the body before rendering.)
- **The curtain bake was doubly broken.** (a) The scripted camera
  rotation (π/2, 0, π) faces the camera **−Y** (forward measured
  (0, −1, 0)); the curtain sits at +Y. (b) The 75° tilt pivots on the
  world origin (verts authored at y=5.0 in mesh space), throwing the
  plane to ≈(0, 0, 5.2), NDC y ≈ 3.0. Either defect alone empties the
  bake. First bake census: alpha mean 0.000, RGB mean 0.000 — preserved
  as `work/fur_card_texture_sen_emptybake.png`. Repairs: camera
  rotation → (π/2, 0, 0) (forward (0, +1, 0), up +Z); verts centred
  on the plane centre (0, 5.0, 1.35) with the object located there,
  so the tilt pivots in place. Everything else — plane size, 800
  parents × 5 children, hair length 0.42, `Hair_coat` slot, 512×1024
  @ 24 spp, transparent film — exactly as scripted.

### 9.3 Outputs

| Artifact | Result |
| --- | --- |
| `fur_card_texture_sen.png` | 512×1024 repaired curtain bake: alpha mean **0.354**, 35.5% of texels > 0.5, per-column means 0.000–0.549 (strand streaks); opaque-texel RGB (0.321, 0.266, 0.210). |
| `fur_cards_sen_lod0.glb` | 1,700 cards — 27,194 verts / 13,600 tris, 1 embedded texture, QA gauntlet clean (0 degenerate, 0 NaN). |
| `fur_cards_sen_lod1.glb` | 680 cards — 10,876 v / 5,440 t, clean. |
| `fur_cards_sen_lod2.glb` | 255 cards — 4,074 v / 2,040 t, clean. |
| `work/card_counts.json` | `{"lod0": 1700, "lod1": 680, "lod2": 255}`. |
| `renders/sen_front.png`, `sen_profile.png`, `sen_threequarter.png`, `sen_head_closeup.png` | 640×800, scripted cameras/lighting/resolution. Debits below. |
| `work/cards_proof.png` | LOD0 cards alone, scripted front camera — cards visible, alpha cutout working, region tints reading (dark ruff mass, tan coat). |

Against the landed stacks: LOD0's 13,600 tris sit inside A5's desktop
LOD0 fur budget (≤48k tris), but the scripted 1,700 placements across
all zones are ~⅓ of A5's placement budget (~4,700) — the proof render
shows the consequence: the cards read as a sparse tuft/silhouette
layer, not a continuous coat. The bake is Sen's own curtain, as
scripted; the A8 card bakes and A13 atlas were not consumed (the
script never referenced them), and the texture is one undifferentiated
streak field for all regions — region identity comes from the
vertex-colour tints only.

### 9.4 Divergences from the script as written

- **Split execution** (the pipeline's own §6 precedent) after the
  restart kill; stage E ran as its own process.
- **Samples 32 → 12 in stage E.** Measured throughput: 39.4 s per
  sample-frame (probes: 2 spp @ 320×400 = 23.7 s, 2 spp @ 640×800 =
  82.8 s; fixed overhead ≈4 s), so 32 spp ≈ 21 min/frame, ≈85 min for
  the set. Resolution, cameras, lighting and groom are unchanged.
- **The final `save_as_mainfile` was not executed.** `sen_build.blend`
  remains the pristine stage-1 file (byte copy kept at
  `work/sen_build_stage1.blend`); the scripted save would have
  persisted stage-2 scene state (cameras, world, render settings,
  display-time `child_percent = 0`) into the verified stage-1
  artifact.
- Stage D's Sun (energy 3.0, rotation (0.9, 0.2, 0.6)) was recreated
  identically in the renders-only pass — in the single-process design
  it is what lights stage E.
- Groom `child_percent` left at the saved 50 in the renders pass
  (render children are governed by `rendered_child_count = 3` either
  way; no visual effect).

### 9.5 Honest debits (stage-2 outputs)

- **Strands render ribbon-thick.** Stage 1 never set the groom's hair
  diameter (the same unset default A3 measured at 5–9 mm in the
  GeoNodes groom), so the beauty renders show straw-like ribbons, not
  hair. A stage-1 groom property, faithfully rendered.
- **Coat reads pale tan** under the scripted 3.0-energy sun; the
  authored dark browns and the pale chest crescent do not separate
  visually in any of the four views.
- **Profile view does not sell the head** — at the scripted 2.5 m the
  near arm and ruff mass fill the frame. Head close-up: ruff strands
  cross the face; eye, muzzle and nose visible but occluded.
- 12-sample renders carry moderate noise (no denoiser was scripted).
- Card counts are the scripted ones; per §9.3 they under-place
  against A5. Raising LOD0 density is a numbers change in
  `build_cards`, not a pipeline change, if wanted.

## 10. Head rebuild — L/R mirror fix (2026-11-16)

`sen_head.glb` / `sen_head.blend` were rebuilt on **base-head-v4** with
Sen's unchanged 31-slider vector. §3 above is the historical record of
the v3-based build and is **not** edited; where its numbers differ from
this section's, this section's were re-measured on identical rulers
across both files (`scripts/measure_mirror.py`,
`characters/common/verify_head.py`).

### 10.1 The bug

The original builder (`scripts/build_head.py`, 2026-11-12, preserved
untouched) keyed left/right off object names, in both the ear block
and the eye block:

```python
side = 1.0 if sname == "R" else -1.0
```

In this head frame `Eyeball_L` / `Ear_L` sit at **+x** (both bases:
Eyeball_L centre x = +0.1311), so every name-keyed lateral shift ran
mirrored:

- **EyeSpacing +30** — the +0.012 L/side spread was applied as −0.012
  to the +x eye and +0.012 to the −x eye: the eyes **converged**
  0.012 L/side instead of spreading.
- **EarSpread +40** — the +0.016 L/side base shift was applied inward
  on both ears, and the 6° cant was likewise name-keyed (inward).

Found 2026-11-16 during the Pyn/Jorge/Brand head builds. Their
corrected builder (`characters/common/build_head.py`) takes
side from each part's own position: `side = 1.0 if centre_x >= 0`.

### 10.2 The rebuild

Driver: `scripts/build_sen_head.py` — runs the corrected builder on
`base-head-v4/neutral_base_head_v4.glb` with `scripts/sen_vector.json`
(the batch-1 bear vector; `EarLength` → `EarHeight` and
`EarBaseHeight` → `EarPlacementHeight` renamed to the spec names the
corrected builder reads, **values identical** to the original build's
vector), then applies Sen's tongue ×1.3 — a character direction of
the original build (its §4.3; §3 above), not a slider — exactly as
the original did (uniform scale about the tongue's posterior base).

Preserved before overwriting, in `work/originals/`:
`sen_head_v3base.glb`, `sen_head_v3base.blend`,
`head_measure_v3.json`. New work files: `work/head_measure.json`
(builder report + tongue), `work/head_verify.json`,
`work/mirror_measure_baseline.json`, `work/mirror_measure_new.json`,
`work/build_rebuild.log`, `work/render_rebuild.log`. New head files:
`sen_head.glb` 1,254,308 B, `sen_head.blend` 748,684 B (the blend is
now the builder's v4 scene; the v3 skull/muscle/tissue stack blend is
the preserved original).

### 10.3 Mirror stations — before / after

Eyes are material points (the eyeball assembly translates rigidly),
so centre deltas are the applied shift itself. Raw head-local units:

| Station | Base | Old build (v3) | New build (v4) |
|---|---|---|---|
| Eye centre \|x\|, per side | 0.1311 (both bases) | 0.1191 → **Δ −0.0120 (converged — bug)** | 0.1430 → **Δ +0.0119 (spread — fixed)** |
| Inter-centre distance | 0.2622 | 0.2382 | 0.2862 |
| Interorbital gap | 0.1122 | 0.1283 (Δ +0.016) | 0.1762 (Δ +0.064) |

The gap decomposition closes exactly on both builds: gap Δ =
EyeSpacing term + EyeSize term (EyeSize −40 shrinks the globes
0.150 → 0.110, widening the gap by +0.040 either way). Old:
−0.024 + 0.040 = +0.016 — the spacing term is negative, the bug's
signature. New: +0.024 + 0.040 = +0.064, matching `verify_head.py`'s
measured station delta. The swing between builds is 0.024/side,
exactly twice the slider's 0.012 term — a flipped sign, nothing else.

Ears: the shift **term** is exact from the code (old −0.016 L/side
inward + inward cant; new +0.016 L/side outward + 6° outward cant;
term swing 0.032/side). The measured base point is a
nearest-quartile centroid, which also migrates with tilt, tip pinch
and seating, so measured deltas are reported with that caveat:

| Station (quartile-centroid ruler) | v3 base | Old build | v4 base | New build |
|---|---|---|---|---|
| Ear base \|x\| | 0.3195 | 0.2530 | 0.3276 | 0.3065 |
| Ear tip \|x\| | — | 0.3324 | — | 0.4428 |
| Ear base–tip length | 0.2895 | 0.2079 (−28.2%) | 0.2924 | 0.1947 (−33.4%) |

The new ears sit +0.0535/side further out than the old shipped ears
on the identical ruler — the term swing plus the corrected builder's
material-point re-seating (seat delta x −0.0119/side: the ears now
follow the deformed skull surface, the builder's second documented
divergence from Sen's script). The tips tell the visible story:
+0.110/side further out — the outward cant now throws them wide
instead of tucking them in (see `renders/head_front.png`).

### 10.4 Full station check (verify_head.py, v4 base → new build)

Built vs the proportional expectation (the build-accuracy column;
species-target deltas include the base's own deliberate deviations):

ZB −1.4% · MuzzleWidth merged-section **+1.7%** (legacy vertex-slab
+5.5% — the ruler-artefact family of BUILD_V4's appendix; the
section ruler is the standard) · MuzzleDepth −3.3% · MuzzleFrac
+0.5% · CraniumWidth +0.0% · SkullHeight +0.0% · OrbitDiameter −0.0%
(0.110, the species target exactly) · JawLength +1.4% (node-hinge
ratio 0.9324 = expected exactly) · JawWidth −0.0% · RamusDepth
+0.0% · NoseWidth ratio 1.191 = expected · EarLength stage-F ruler
−1.2%. EarLength on the orientation-agnostic base→tip ruler reads
−20.5% vs expectation — that ruler prices in the EarTipPoint −80
pinch/shorten and the tilt; the stage-F ruler is the comparable one.
Drift checks: OrbitHeight Δ 0.0; OrbitRise +0.008 L (brow fields act
above the orbit; no slider owns the station).

Like-for-like headline rulers, §3's build vs this one (raw units;
ruler differences noted): muzzle width 0.304 (band ruler) → 0.292
(merged section) — a base+ruler change, not a regression (build
accuracy on the section ruler is +1.7%, above) · jaw width 0.642 →
0.636 · nose width 0.105 → 0.105 · tongue extent 0.572 → 0.572
(the ×1.3 step reproduced to 1e-4) · tongue max-forward vs jaw front
−0.0249 → −0.0253 · orbit diameter 0.110 → 0.110 · jaw y-extent
0.852 → 0.851 · tissue max width 0.557 → 0.558. The §2 M1 gate's
head-side input is unchanged: 0.112 m neck / (0.5578 × 0.24138 m) =
**0.832**, as corrected in §2. Export scale 1.74 remains a record
directive; the GLB is in head-local units, as before.

### 10.5 Teeth (BVH, builder's verify on the shipped head)

| Jaw angle | Overlap pairs | Min clearance |
|---|---|---|
| −10° | **0** | 0.027 L |
| −20° | **0** | 0.049 L |
| −30° | **0** | 0.068 L |
| 0° (rest) | **71** | 0.00025 L |

The open-angle criterion passes clean — now a true BVH check against
split arcades, replacing §3's bbox-only tongue/jaw note. The rest
count is reported, not hidden: the undeformed v4 base itself carries
**27** rest pairs (re-measured this pass with the same BVH code);
Sen's vector adds 44 (JawLength −50 reseats the lower arcade's rest
fit; MuzzleLength +15 grows the upper's block). Rest-occlusion
re-seating is base-head-v5's job and was explicitly out of scope
here.

### 10.6 Verification & renders

QA gauntlet on the new `sen_head.glb`: 21 meshes, 41,700 v /
20,792 t, **0 degenerate, 0 NaN**, no skin / 0 morphs (static bake —
same status as §5; the vert growth over the old head's 16,374 v is
the v4 base's denser split-arcade construction). Clay renders,
head-only, in `renders/`: `head_front.png`, `head_threequarter.png`,
`head_profile.png` (640×800, the batch's render script).

### 10.7 Scope note — the composed character still carries the old head

`sen_composed.glb` and `sen_build.blend` are **unchanged**: the
composed character still embeds the v3-based head, mirrored
eyes/ears included, and the §9 stage-2 full-body renders still show
it. This rebuild replaced the standalone head file only, per the
job's scope. Re-composing the character on the corrected head is a
separate step — it also wants v5's rest-occlusion re-seat (§10.5).
The stage-2 fur cards are body fur and are unaffected; §8's open
items stand as written, except item 7 (tongue/jaw occlusion), which
the split arcade + this BVH pass now covers for the head file.
