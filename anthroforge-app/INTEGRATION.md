# Integration — today's proven work, applied to the app

*Nov 12, 2026. Joe asked: "can all our work and refinements be applied
to the modelling app?" — this pass does it, and this document is the
map of what landed, what is record-only, and what is still in flight.
Suite: **87 tests, all passing** (was 54 before this pass).*

## 1. Inventory — every deliverable, by state

### Wired (geometry in the app, fold-gate verified)

| Deliverable | Where it lives now | Verification |
|---|---|---|
| Belly lineage v5.1 + terminal tissue | `body.belly.protrusion` record refreshed; canonical lin/sag fields in `library/instances/body.belly.protrusion__makehuman_hm08.npz` | navel +11.14 cm fwd / −6.99 cm down at +1 (the lineage's own QA numbers); 0 flips |
| Belly v5.2 thigh-contact variant | same record, `arrays.variants.contact` | 0 flips at +1 on the app base |
| Bara proof components | new records `body.build.muscle`, `body.build.chest_width`, `body.build.tissue_strongman`, `body.build.bara_strongman` (combined) + instance packs | components sum to the combined field; 0 flips each and combined |
| Definition reliefs (flat_abs, traps_valleys, pecs_crease, back) | hm08 packs added to the existing records | 0 flips at +1 each |
| Neck + forearm authored fields | `body.neck.mass` gained its instance; new record `body.forearm.mass` + packs | 0 flips at +1 each |
| Masculine base | `library/bases/makehuman_hm08_masculine.npz` + base record; belly re-derived instance on the refreshed record | frame alignment reproduced (offset [0, +0.40 cm, +81.68 cm] method); belly instance folds 0 |
| Default base package | `library/bases/makehuman_hm08.npz` + record | alignment residual p50 3.22 / max 6.17 cm vs the documented cross-check 3.2 / 6.2 cm |
| End-to-end build | `core/build.py` (`build_character`, `evaluate_character`, `Library`) | belly / bara / masculine / Sen builds in tests, all gate-clean |
| MCP `export_run` (#20) + `validate_character` (#27) | live handlers in `mcp/server.py`, delegating to `core.build` | tests call both through `call_tool` |

### Record-only (canonical data in the app, no hm08 geometry yet)

| Deliverable | State |
|---|---|
| HIMBO vocabulary (62 sliders: 13 curated + 49 generated `body.himbo.*`) | Records carry decode stats + the Skyrim instance pointer. They exist so the spec'd presets validate end-to-end; geometry transfer to hm08 is future work per slider. |
| Presets: orc_bara_strongman, orc_bara_bodybuilder, Pyn, Sen, sen_muscle_bear, Jorge | `library/presets/*.afchar.json` + `INDEX.json` with share codes. Body vectors are canonical slider values; head vectors ride in `species_preset.head_sliders` (see limits). All six validate clean and round-trip through their share codes (test-asserted). |
| Species fur profiles (8) | `library/fur/species_profiles.json`, extracted verbatim from SPECIES_FUR.md §9; validated by `core/fur.py` (region vocabulary, density/length ranges, patterns) |
| Fur budgets | `library/fur/budgets.json` (platforms, zone budgets, LOD switching) from FUR_BUDGETS.md §3–5 |
| Coupling-validation builds (gachidebu / pear / big-chest) | Validation artefacts in `bara-proof/`; their measurements already live in the definition records' QA (`attenuation_measured_vs_predicted`). Not sliders — correctly not registered. |
| Head v4 (base-head-v4) | Landed in anthroforge-v2 (blend/GLB/groups/proportions). **Not** registered as an app base: the canonical `head.*` slider records now exist (Nov 16, 2026), but they carry no instance geometry against this base yet (see limits). |
| Head slider records (37) | All specced head sliders (species-head-spec.md §3.1 + §5.4, brow-study.md §5) are canonical `library/sliders/head.*.json` records on the spec index scale; vocabulary-only (`instances` empty) until a head base + per-base fields land. |
| Soft-tissue dynamics (dynamics/) | Landed in anthroforge-v2 (`dynamics_spec.json`, prototype). Runtime data format; a `core/dynamics.py` consumer is future work, not part of this pass. |

### Not yet landed (in flight elsewhere — nothing here depends on them)

- `characters/sen/SEN_BUILD.md` — landed Nov 12, 2026 (evening), stages 1+2 complete: Sen's composed GLB + targets + QA JSONs in `anthroforge-v2/characters/sen/`, LOD fur cards + renders in §9. Sen's app preset comes from the spec doc (§4), which is what that build implemented; preset vectors cross-checked exact against the build (SEN_BUILD.md).
- `bara-proof/COUPLING_VALIDATION.md` — the validation geometry and numbers landed; the consolidated doc has not.
- The hyper-range / Kaleaon-anatomy deliverables (Thread 58) — in flight; nothing in the app references them yet.

## 2. What the app can now do

```
character (.afchar.json / share code / preset)
  → validate against the 74-record slider registry
  → couplings: raw vector → effective vector (+ derived: regional
    tissue, power-belly shares, wrap factors, advisories)
  → geometry: each effective slider with an instance on the
    character's base applies its field (gravity-coupled sliders
    evaluate their authored shape function, not a linear scale)
  → fold gate over body faces (flips + thinnest margin reported)
  → GLB export → QA gauntlet verdicts on the report
```

- **74 slider records**: 20 seed + 4 composed builds + forearm +
  49 generated HIMBO vocabulary records.
- **11 sliders carry hm08 geometry** (canonical-precision packs in
  `library/instances/`): belly (with contact variant), the 4 bara
  builds, 4 definition reliefs, neck, forearm. A twelfth instance —
  the belly on the masculine base — is a per-base re-derivation.
- **2 bases**: `makehuman_hm08` (the blueprint's `af_body_neutral_v1`
  default resolves to it) and `makehuman_hm08_masculine`.
- **6 presets** with share codes (`library/presets/INDEX.json`).
  Codes run ~1.3–1.7 k chars — larger than the scaffold's ~286-char
  sparse examples because these are full 25–54-slider vectors; the
  codec round-trips them bit-exact (test-asserted).
- **MCP**: `export_run` and `validate_character` are live; the other
  30 callable names remain stubs that raise loudly.

### Why instance packs, not the .target files

The proofs ship `.target` files (MPFB interchange; deltas rounded to
0.1 mm). That rounding moves the belly lineage's thinnest fold-gate
face across zero: canonical field → min normal dot **+0.0018** at +1
(their published margin, reproduced bit-exact on the app base);
rounded .target → **−0.0003** on that one face. Not a fold — a
rounding graze on a face that is nearly edge-on by design. The app
therefore builds from float64 packs extracted from the proofs' own
canonical work arrays (`scripts/build_instance_packs.py`, which
re-verifies 0 flips for every pack), and records keep the `.target`
paths as the interchange form. Base packages are float64 for the
same reason.

### Regeneration scripts (all in `scripts/`, all idempotent)

`build_base_packages.py` (base npz + records, with the documented
alignment cross-check as an assertion) · `wire_proof_records.py`
(belly refresh, bara records, neck/forearm) · `build_instance_packs.py`
(precision packs + record patching + gate verification) ·
`build_presets.py` (HIMBO records + presets + share codes; fails on
any spec'd slider name the decode cannot resolve) · `build_fur_data.py`
(fur profiles extracted from the Markdown's JSON blocks; budgets).

## 3. Frontend follow-up — precisely what the Babylon page still needs

The v2 page (`anthroforge-v2/anthroforge_3d_pro_v2.html`) and the
Telegram Mini App page still drive **procedural** sliders; nothing in
them reads the app library yet. To close that gap, in order:

1. **A library bundle endpoint/file.** The Core emits one JSON
   bundle: slider registry (id, label, group, range, safe range),
   preset list (name, file, share code), fur profile ids. Static
   file is enough for the Mini App; the Tauri shell can read the
   library folder directly.
2. **Field delivery to the page.** Instance packs are float64 npz —
   not web-loadable. The build service should emit, per base, a
   compact web pack: for each instanced slider, its field as a
   Babylon **morph target** in a GLB (positions-only targets,
   float32 is fine *for display* — the fold gate stays a Core-side
   check at export). Sliders with a sag component (belly) need
   **two** morph targets (LIN and SAG) and the page must evaluate
   `w·LIN + sign(w)|w|^γ·SAG` by setting the two target influences —
   Babylon supports multiple targets per mesh, so this is influence
   bookkeeping, not new tech.
3. **Preset + share-code loading in the page.** `sharecode.js`
   (telegram-miniapp) is already codec-compatible with the Core
   (verified Nov 12). The page needs: paste-a-code → decode → set
   slider UI from the vector → apply couplings. **Couplings are the
   gap**: the evaluator is Python. Either (a) the page calls the
   Core (Mini App: via the bot backend; Tauri: via the local Core
   service), or (b) port `evaluate_effective_vector` to JS — it is
   ~200 lines of pure functions over the coupling JSONs, which are
   already data. (b) is the better long-term answer and the coupling
   records were designed for it.
4. **Unapplied-slider honesty in the UI.** Most preset sliders are
   vocabulary records without hm08 geometry today. The page must
   show them as *recorded but not yet geometric* (the build report's
   `unapplied` list is exactly this), never silently pretend.
5. **Head vectors.** `species_preset.head_sliders` should render as
   a read-only spec panel; the canonical `head.*` records now exist
   (Nov 16, 2026) but carry no instance geometry yet, so head
   controls map to the records without deforming anything — and the
   page must not invent a second vocabulary.

## 4. Honest limits

- **Per-base instancing is real cost.** A slider's field exists per
  base or not at all. The masculine base has exactly one instance
  (belly v1 re-derived); every other slider is unapplied there and
  the build report says so. Nothing transfers implicitly.
- **Study-tier by default.** All HIMBO/Fat-Males-derived records are
  `study-only (internal)` and ship in the library under the
  blueprint's D6 default (internal-only until a slider graduates by
  re-authoring from build-tier sources). Joe's D6 ruling is still
  pending; the records' licence fields carry the tier either way.
- **The HIMBO vocabulary is vocabulary.** 62 body records validate
  presets and drive the coupling layer; 11 sliders have geometry.
  A preset character built today deforms by its instanced sliders
  only (for Sen: his definition values at their coupling-attenuated
  effective values). The full Sen geometry composition lives in
  `anthroforge-v2/characters/sen/sen_composed.glb`, built by the
  proof pipeline, not yet by this Core.
- **Head sliders: 37 specced, 37 records (Nov 16, 2026).** The full
  species-head-spec.md set (§3.1 + the §5.4 vertical extension) plus
  the brow-study.md brow vector are now canonical `head.*` records,
  on the spec's −100…+100 index scale. They are vocabulary records:
  `instances` are empty — no head base instance geometry exists yet —
  so preset head vectors are still stored verbatim in
  `species_preset` (under spec names, incl. the pre-rename
  `EarHeight`/`EarPlacementHeight`) and do not evaluate
  geometrically. The §5.4 renames (`EarHeight` → `EarLength`,
  `EarPlacementHeight` → `EarBaseHeight`, values for the latter do
  not carry over) are recorded in the records themselves. The
  `EarTipHeight` composition with `EarLength`/`EarTilt` is a
  placement solve no coupling kind expresses; it is documented in
  the `head.ear.tip_height` record, not in `library/couplings/`.
  The orc's `JawProtrusion` extension is flagged in the orc presets,
  not yet a record (it traces to the orc spec, not the head spec).
- **Core GLB export is a geometry proof, not the product export.**
  It writes positions/normals/indices — no skin, morphs, materials
  or animation. The skinned export path lives in the v2 Babylon app
  and the export prototype (with its DAE/FBX findings); unifying
  them behind `export_run` is blueprint Phase work, not done here.
- **Belly negative pole.** The −1 direction folds (~184 faces,
  linear evaluation) in every lineage version; a separately authored
  decrease target is still owed. The record documents it; values at
  the negative pole should be treated as unproven.
- **Fur is data, not geometry.** Profiles and budgets are validated
  app data; no groom/card builder consumes them in the Core yet.
- **QA gauntlet contract gate.** Our Core exports are unskinned, so
  the gauntlet's 36-bone contract check reports n/a — the contract
  binds once the skinned export path is unified (above).
