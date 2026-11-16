# MakeHuman × Omniversal Sliders — Research + Architecture

*Nov 12, 2026. Joe's ask: "look into MakeHuman, and how to expand it with
omniversal sliders." **Omniversal slider** (working definition): one slider
vocabulary — a slider defined once, semantically ("belly protrusion",
"muzzle length", "jaw width") — that can be instantiated on any base mesh
(MakeHuman hm08, the AnthroForge neutral base, Skyrim HIMBO/Fat Males),
instead of every system shipping an incompatible, base-locked slider set.*

*Tagging discipline as elsewhere in this project: **[S]** sourced fact,
**[L]** verified locally on this machine, **[D]** derived, **[E]** estimate.*

---

## 1. What we already have locally [L]

MakeHuman is **already in the building** — two separate footholds:

| Asset | Where | State |
|---|---|---|
| **MPFB2 v2.0.18** (Blender extension zip, 43 MB) | `~/workspace/stick-figure-avatar/photoreal/tools/mpfb2.zip` | Installed into Blender 5.2 (`~/.config/blender/5.2/mpfb` config present); **proven working headless Nov 10, 2026** — built the photoreal human (`photoreal/photoreal_avatar.blend` + `.glb`, 53-bone rig). Manifest in the zip: GPL-3.0-or-later code, Blender ≥4.2. |
| **MH system assets** (downloaded packs) | `~/workspace/stick-figure-avatar/photoreal/assets/` | `clothes/ eyebrows/ eyelashes/ eyes/ hair/ skins/ teeth/ tongue/` — the CC0 system-asset content is on disk. |
| **Converted hm08 asset set** | `~/workspace/charmorh-expansion/assets/makehuman-hm08{,-age,-body,-face}/` | MakeHuman base already converted once for the CharMorph pipeline: `mesh.bin/json`, `rig.bin/json`, `targets.bin/json`, `spec.json` per set. A precedent conversion exists — reuse its tooling (`~/workspace/charmorh-expansion/tools/convert-makehuman`). |
| **Learned deltas** (omniversal raw material) | `~/workspace/character_assets/learned/` | Fat Males exact-topology morph (npz, 2,024-vert delta field, max displacement 10.93 Skyrim units ≈ 15.6 cm), HIMBO full decode (126 sliders, 22 presets), **and the finished foreign-topology fit** (see §4.2). |
| **Tools** | `~/workspace/character_assets/learned/tools/` | `nifparse.py`, `osdparse.py`, `learn_poc.py`, `fit_foreign.py` — the fit tool is the retargeting engine of §4. |

Disk check at time of writing: 64 GB free (floor is 55 GB) — nothing in this
plan needs a big download; MPFB2's full target library is inside the zip
already on disk.

---

## 2. How MakeHuman actually works [S]

### 2.1 One base mesh, nothing but deltas

- Everything is built on a single base mesh, **hm08**: ~19,158 vertices
  **including helper geometry** (clothes-fitting cages etc.), ≈13,380 body
  vertices once helpers are stripped [S — third-party MPFB2 evaluations;
  treat the exact split as ±1%]. Pure-quad, deformation-grade topology.
- A **`.target` file** is the atomic morph: plain ASCII, header
  `# basemesh hm08`, then one line per moved vertex:
  `vertex_index  dx  dy  dz`. A target stores *only* offsets — applying it is
  `base + Σ wᵢ·deltaᵢ`. (In MPFB2's data the same files ship gzipped as
  `.target.gz`; ~1,258 target files in the bundled library [S].)
- **Hard rule:** a target may never add/delete a vertex, face or edge.
  Topology *and vertex order* are the contract. This is the single most
  important fact for §5 — a `.target` is meaningless on any other mesh.

### 2.2 Modifiers: how sliders map to targets

- A **modifier** is a named slider that controls one or more targets via a
  **token system**: folder + filename tokens define a target *group*
  (e.g. `data/targets/cartoon/eyes-large.target` → group
  `(cartoon, eyes, large)`). A bipolar slider is two targets
  (`…-small` / `…-large`) blended by slider sign; weights normally run
  0…1, bipolar −1…1.
- **Macro modifiers** (gender, age, race/ethnicity, weight, muscle, height,
  proportions) don't map 1:1 to files. They resolve through the
  **macrodetails grid**: for each macro combination there is a target
  (e.g. `macrodetails/african-female-old.target`), and the engine
  interpolates the grid from the current macro values. Moving "age" quietly
  re-derives dozens of target weights.
- **Detail modifiers** (~100 modifiers total across the system) address
  regional target groups directly — nose, ears, cheeks, chin, arms, legs…
- **Custom targets** are a first-class citizen: drop a `.target` into the
  custom/user target folder and it appears as a slider («Custom» panel), or
  load it programmatically. In MPFB2:
  `TargetService.load_target(obj, path, weight=…)` applies any target file to
  a created human; `TargetService.bake_targets()` commits the stack;
  `TargetService.reapply_macro_details()` recomputes the macro layer.
  **This is the injection port for §4.3 — we do not need to fork MakeHuman.**

### 2.3 Pipelines into Blender: MHX2 and MPFB2

- **MHX2** is MakeHuman's own exchange format (mesh + rig + materials +
  proxy info) with a Blender importer. It is the legacy route; the community
  centre of gravity has moved to MPFB2.
- **MPFB2** (MakeHuman Plugin For Blender, v2.x) re-implements the system
  natively in Blender: `HumanService.create_human()` builds the base,
  HumanObjectProperties carry the macro values, targets load/bake as above,
  `HumanService.add_builtin_rig()` attaches a rig, and MHCLO assets
  (clothes/hair/eyes/teeth as separate fitted meshes) attach with weights
  interpolated from the body. MPFB2 is what our Nov 10 build used [L].

### 2.4 Rigs

MPFB2 ships several rigs as JSON definitions over the same base:

| Rig | Bones | Notes |
|---|---|---|
| `game_engine` | **53** | UE-style naming (`pelvis`, `spine_01…03`, `clavicle/upperarm/lowerarm/hand_[lr]`, full fingers, `thigh/calf/foot/ball_[lr]`, `neck_01`, `head`). The game-export choice [S]. |
| `default` | **163** | Full MakeHuman rig incl. facial bones, fingers, toes. Face is **bone-driven** — MH has no ARKit-style face morph set [S]. |
| others | — | `mixamo`, `rigify` variants, `game_engine_with_breast`, CMU mocap, etc. |

Rig joint positions are derived from the (morphed) mesh, so shape targets
do move the skeleton's joints to a degree — but bone *count/topology* is
fixed per rig definition.

### 2.5 Asset ecosystem

- **System assets** (bundled/asset-pack): skins, clothes (MHCLO), hair,
  eyes, teeth, tongue, poses, expressions — CC0 (§3).
- **Community asset packs** at static.makehumancommunity.org: curated zips,
  each asset individually licensed (CC0 or CC-BY packs; §3 caveat).
  Relevant packs: deformation packs (Arms 01, Cheek 01, Ears 01, Hands 01,
  Nose 01, 2023) and the **Animal 01–04** packs (2024) — §3.5/§4.5.
- **MakeTarget** (Blender add-on, AGPL): the official way to author a
  target — sculpt the hm08 base in Blender, export the delta. Our writer in
  §4.3 produces the same file format without the GUI.

---

## 3. Licences — the bottom line [S]

| Component | Licence | Consequence for us |
|---|---|---|
| MakeHuman application code | **AGPL-3.0-or-later** | Use the app/tooling freely; if we ever *ship modified MH code as a network service*, AGPL bites. Our plan doesn't — we generate data files. |
| MPFB2 code | **GPL-3.0-or-later** (zip manifest, [L]) | Same posture: tool, not payload. We call its API in our own Blender scripts; we don't redistribute its code inside AnthroForge. |
| **Bundled assets** — base mesh, proxies, **targets/modifiers**, textures, MHCLO clothes/hair, **rigs, poses, expressions** | **CC0 1.0** (explicit enumerated scope, LICENSE.md §C / LICENSE.ASSETS.md) | **Mine freely.** MH targets are a lawful slider *source* for AnthroForge, no attribution required. |
| **Output** (exports, .mhm, renders, scripted generation) | **No claim whatsoever** — "we regard these things as your data" (LICENSE.md §D) | Anything we bake out of MH/MPFB is ours. |
| Community assets (asset packs / user repo) | **Per-asset**: packs are labelled CC0 *or* CC-BY; individual files occasionally contradict their pack label (documented cases of AGPL/none inside "CC0" packs) | Verify **per file**, not per pack. CC-BY is fine with attribution kept in the slider provenance (§4.1). |
| Targets **we** author (incl. generated from our learned deltas) | Ours by default | The Fat Males/HIMBO learned data stays under the project's existing study-only rule — deltas learned from Skyrim mods are **internal study material**, and any `.target` generated from them inherits that status until Joe rules otherwise. Legal ≠ licence-clean for redistribution: keep provenance flags honest (§4.1). |

**Bottom line:** MakeHuman is the cleanest possible partner system — its
entire bundled slider library is CC0 and its output is disclaimed. The only
licence care needed is per-file checks on community assets.

---

## 4. The gap — what MakeHuman can't do today

1. **Real species heads.** The hm08 head is a human head. A muzzle must be
   *pulled out of* nose/mouth/cheek vertices — there is no muzzle material,
   no ear geometry beyond the human ear (animal ears in the packs are
   targets that reshape the ear region / separate small meshes), no
   digitigrade anything in the head's case, and no layered
   skull→muscle→tissue construction (Joe's rule) — MH heads are one surface
   of blended deltas.
2. **Non-human body plans.** No digitigrade leg targets of consequence, no
   tail (tails exist only as clothing/proxy hacks), no quadruped. The macro
   grid spans *human* variation only: weight/muscle targets top out far
   below bara/orc extremes, and nothing in the grid does prognathic jaws,
   brow-ridge hypertrophy, or trap/neck mass at orc scale (our
   `preset-orc-bara.md` lives at those extremes).
3. **Swappable parts system.** MHCLO attaches *fitted separate meshes*
   (clothes/hair/eyes/teeth) — close in spirit, but parts are fitted
   *clothing*, not rigged anatomical part swaps (no "replace forearm with
   paw", no per-part own-skin-weight modules like AnthroForge's ruling).
4. **Teeth as a system.** MH ships a teeth mesh as a fitted proxy asset.
   There is no arcade concept, no diet morph axis, no jaw-riding lower set
   as a *parameterised* system. Our universal-arcade design (Joe, Nov 12)
   has no MH counterpart to interoperate with — MH would receive teeth as
   exported part variants, not sliders.
5. **Expressions.** Facial rig is bone-based (163-bone default rig); no
   blendshape expression vocabulary to map omniversal face sliders onto.

### 4.5 Do community furry targets exist? Yes — thin but real [S]

The **Animal packs** (released 2024-05-10, mostly one author, JALdMIC):

| Pack | Licence | Contents (targets unless noted) |
|---|---|---|
| Animal 01 | CC0 | faun face, piggy nose, donkey head, equinus (horse) head v2, catgirl ears |
| Animal 02 | CC-BY | canine/feline/bunny/dropped ears v2, furry mouths (canine v4, feline v4, reptile), shark mouth |
| Animal 03 | CC-BY | **full head deforms**: bear (+cartoon), cat, fox (cartoon), lion, tiger, wolf head v3, dog, rabbit/hare, cow, squirrel, + cartoon heads |
| Animal 04 | CC-BY | full-body furry transforms |

**Honest quality read [E, from pack scope/thumbnails]:** these are earnest
hobbyist single-author deforms of the human head — ear reshapes, snout-ish
pulls, mouth reshapes. They are *not* layered-anatomy species heads, there's
no digitigrade/tail/teeth system behind them, and coverage is whatever one
author fancied. Their real value to us is threefold: (a) **proof** the
`.target` format + custom-target route happily carries non-human shapes;
(b) **mining stock** — CC0/CC-BY delta fields we can legally convert to
omniversal sliders and then *improve*; (c) a **correspondence test set** —
wolf head v3 gives us an MH-native furry delta to retarget onto the
AnthroForge base as a second proof (§6).

---

## 5. What breaks (read before designing)

1. **Vertex-order lock.** `.target`, `.osd`, and our npz deltas are all
   *index-keyed*. The same slider is a different file on every base; there
   is no shortcut around per-base instances. (This is *why* omniversal
   sliders need a canonical definition + generated instances, §6.1.)
2. **Helper vertices.** MH targets index into the full 19,158-vert basemesh
   including helpers; strip or keep helpers inconsistently and every index
   shifts. Any MH instance generator must work against the exact `base.obj`
   from the MPFB2 zip [L] and state its helper policy.
3. **Macro interference.** In MH, applying a custom target and then touching
   a macro slider triggers `reapply_macro_details`, which recomputes the
   macro stack — custom targets survive (they're a separate layer), but a
   naive integration that bakes macros into our target will double-apply.
   Keep omniversal instances *pure* (delta vs the macro-neutral base).
4. **Extreme deltas fold.** Fat Males' belly delta peaks at ~15.6 cm on a
   Skyrim-proportioned base. Transferred naively to MH proportions, expect
   self-intersection at the waist/flank crease and navel inversion at
   weight 1.0. Mitigations: region masks with smooth falloff, per-slider
   `safe_range` < full range, and fold detection (negative-volume triangle
   test) as a QA gate per instance.
5. **Correspondence has known dead zones.** The fit POC (§6.2) failed to
   find clean correspondence in the **flank** band and the **genital
   patch**, and 196 HIMBO verts lack decoded triangles. Delta transfer must
   carry a **residual mask** and zero-out (or hand-fix) deltas in dead
   zones — silently transferring them manufactures artifacts.
6. **Skeletons don't transfer with sliders.** A slider is bind-pose shape
   only. MH `game_engine` = 53 bones, AnthroForge v2 = 36 bones, Skyrim =
   XPMSSE (~115+ bones) [E for XPMSSE count]. Each base must re-derive its
   joint positions from the morphed shape (AnthroForge v2 already re-derives
   bind pose on rebuild [L]; MPFB derives rig joints from the mesh [S]).
   Omniversal sliders must therefore never encode joint data — shape only.
7. **Asymmetry & mirroring conventions differ** (axis handedness: MH/Blender
   Z-up right-handed vs Skyrim NIF frame vs Babylon left-handed). Every
   instance generator owns an explicit frame-conversion step; the learned
   npz files record their source frame [L].

---

## 6. The omniversal slider architecture

### 6.1 Canonical slider definition (base-independent)

A slider is a **semantic object**, not a vertex list. The vertex lists are
*instances*, generated per base and cached. Canonical record (JSON):

```json
{
  "id": "body.belly.protrusion",
  "label": "Belly",
  "group": "body/torso",
  "semantics": "At +1, the abdominal surface at the navel landmark sits the
                full endpoint displacement forward of neutral; 0 = neutral
                base; -1 = the hollow/taut endpoint.",
  "region": {
    "landmarks": ["navel", "sternum_bottom", "pelvis_top"],
    "mask_rule": "geodesic falloff from navel landmark, r = 0.35 x torso_len"
  },
  "range": { "min": -1.0, "max": 1.0, "default": 0.0,
             "safe_max": 0.85, "units": "normalised",
             "endpoint_anchor": "max |delta| = 0.156 m at navel (Fat Males)" },
  "symmetry": "bilateral_x",
  "provenance": { "source": "Fat Males body morph (learned, exact-topology)",
                  "licence": "study-only (internal)",
                  "method": "exact delta / foreign-fit transfer" },
  "instances": {
    "makehuman_hm08":  { "file": "instances/mh08/body.belly.protrusion.target",
                         "qa": { "residual_p95_cm": 0.28, "folds": 0 } },
    "anthroforge_v2":  { "file": "instances/af2/body.belly.protrusion.npz",
                         "qa": { "residual_p95_cm": null } },
    "skyrim_himbo":    { "file": "instances/himbo/body.belly.protrusion.npz",
                         "qa": { "residual_p95_cm": 0.28 } }
  }
}
```

Design rules:

- **Identity = semantics + region + endpoint anchor**, never a file. Two
  instances are "the same slider" if they produce the same landmark-relative
  shape change, verified by QA numbers, not by construction.
- **Region masks are landmark/geodesic**, defined per base by an annotator
  step (landmark vertex picks per base, stored once per base) — this is
  what makes masks portable where vertex indices are not.
- **Units are metres** everywhere in canonical space; source-unit
  conversions (Skyrim unit = 0.01428 m [L]) happen at import.
- **`safe_range` and QA residuals are part of the definition.** A slider
  that folds at 1.0 ships with `safe_max` 0.85 and says so.
- **Provenance/licence travels with the slider** — CC0-mined,
  CC-BY-mined (attribution string), and study-only sliders are
  distinguishable at a glance in any UI built on this.

Storage layout: `~/workspace/character_assets/learned/omniversal/` with
`sliders/<id>.json` + `instances/<base>/<id>.<ext>` — alongside, not
instead of, the existing learned artifacts.

### 6.2 Retargeting: moving a delta between bases

Engine: the existing fit pipeline (`fit_foreign.py`), whose POC
**has now landed** [L, FIT_REPORT.md]:

- Pair: HIMBO base (9,346 verts, foreign topology) fit to the Fat Males
  shape (2,024 verts). Method: trimmed ICP rigid alignment → non-rigid
  registration → delta transfer with normal gating.
- Result over the well-corresponded surface: **median residual 0.05 cm,
  p95 0.28 cm** — transferred deltas land within ~3 mm of the studied shape
  across most of the body. Height-band medians ≤ 0.039 Skyrim units
  everywhere except the named dead zones (flank, genital patch, the
  196-vert triangle-coverage hole).
- Production rules the report itself mandates: report residuals in **both**
  directions (base→target alone flattered the fit ~30×); carry the
  residual mask into the transferred field; mask dead zones rather than
  transferring noise.

So the retarget step of the omniversal pipeline is not speculative:
**register source base → target base once, cache the correspondence, then
every slider on the source base transfers through it.** Correspondence is
per *base pair*, sliders are per *slider* — cost scales with pairs, not
sliders. Base pairs needed first: `himbo ↔ mh08`, `mh08 ↔ anthroforge_v2`,
(head) `mh08 ↔ anthroforge_head`.

### 6.3 MakeHuman-ward: generating `.target` files from our learned deltas

Pipeline (all pieces exist):

1. Import a learned delta (npz) → canonical slider (importer tags
   provenance, converts units).
2. Transfer through the `source ↔ mh08` correspondence (§6.2) → delta field
   on hm08 vertex order, dead zones masked.
3. **Emit `.target`**: ASCII writer — header `# basemesh hm08`, one
   `index dx dy dz` line per moved vertex (threshold |delta| > 0.1 mm to
   keep files lean). ~30 lines of Python [E, format is fully documented §2.1].
4. Deliver two ways: (a) **file drop** into MH's custom-target folder →
   slider appears in MakeHuman itself; (b) **MPFB2 runtime** —
   `TargetService.load_target(human, path, weight=w)` in our Blender
   scripts, no MH install needed. Route (b) is the one our Nov 10 pipeline
   already proves end-to-end [L].
5. QA gate: apply at −1 / 0 / +1 in MPFB2 headless, render, run fold test +
   landmark displacement check vs the canonical endpoint anchor.

First slider families this unlocks inside MakeHuman: **Fat Males belly/
weight** (body), **HIMBO muscle sliders** (the 126 decoded — transferred
as a set), and the **species head sliders**: the 25-slider head spec
(`species-head-spec.md`) instantiated on hm08 gives MakeHuman wolf/fox/
lion/panther heads as *sliders*, exactly what the Animal packs gesture at
but as a coherent parametric system. Head caveat: hm08's head has far fewer
vertices than our base head and no muzzle material — expect the MH instance
of e.g. `head.muzzle.length` to be the *weakest* instance (residual QA will
show it); the canonical definition stays honest about that per-instance.

### 6.4 Reverse: mining MakeHuman as a slider source

- Parse `.target.gz` directly (gzip ASCII — trivially readable) → canonical
  sliders with provenance `CC0 (MakeHuman bundled)` or per-file community
  licence. The ~1,258 bundled targets include the full macro grid and ~100
  detail modifiers' worth of regional shape vocabulary AnthroForge doesn't
  have yet (cheek, nose, ear, hand detail…) — all CC0.
- The Animal packs (§4.5) convert the same way: instant furry starter
  sliders on the MH base, then transferred to the AnthroForge base through
  the `mh08 ↔ anthroforge` correspondence for comparison against our
  species-spec sliders.
- MH's measurement/modifier *names* are also worth mining as vocabulary:
  the canonical ID namespace should adopt MH group tokens where they exist
  (`nose`, `cheek`, `arms`…) so MH-mined and learned sliders sort into one
  tree.

### 6.5 Teeth and parts — deliberately *not* sliders

Per Joe's rulings (Nov 12): teeth = one universal arcade with a diet morph
axis; parts = swappable rigged modules. In omniversal terms these are
**part variants with slider-driven placement** (the arcade scales/places by
jaw sliders; it is not itself a delta field). The canonical format above
gets a sibling record type (`"kind": "part"`) referencing meshes + the
sliders that place them — same provenance/QA discipline, different payload.

---

## 7. Build order

1. **First proof (§8)** — one slider, MH-ward. *Days, not weeks [E].*
2. **Canonical store + importers** — npz (learned) and `.target.gz` (MH)
   importers writing §6.1 records; landmark sets annotated for mh08 and
   the AnthroForge base.
3. **Base-pair correspondences** — `himbo ↔ mh08` (body), then
   `mh08 ↔ anthroforge_v2` (body), then head pair. Reuse `fit_foreign.py`;
   budget the flank/dead-zone hand-fixes per pair.
4. **Batch transfer** — HIMBO 126 + Fat Males set → mh08 instances;
   MH detail-target library → anthroforge instances. QA gates on.
5. **Species head sliders on both bases** + Animal-pack comparison run.
6. **UI surfacing** — AnthroForge reads canonical records and shows
   per-instance QA honestly (a slider with a weak MH instance says so).

## 8. The first proof — Fat Males belly, MH-ward

**One slider:** `body.belly.protrusion`, sourced from the *exact-topology*
Fat Males delta (our cleanest learned field — no fit error at the source).

**Path:** belly-region mask (landmark rule, §6.1) applied to the Fat Males
delta → transfer through a fresh `fatmales/himbo ↔ mh08` correspondence →
emit `body.belly.protrusion.target` → apply in MPFB2 headless at
−1 / 0 / +0.5 / +1 → renders + measurements.

**Why this slider:** biggest, cleanest delta we own (mean 2.59, max 10.93
Skyrim units; concentrated in torso bands z 60–100 [L]); belly is the
best-corresponded region in the fit POC (belly band residuals were in the
≤0.039-unit-median group [L]); and a belly is unmistakable in a render —
pass/fail is visible, not arguable.

**Success criteria:**
- Navel-landmark forward displacement at +1 matches the canonical endpoint
  anchor (0.156 m, scaled by MH-vs-Skyrim torso proportion) within **5 mm**.
- **Zero fold-overs** in the belly region at +1 (negative-volume test);
  if folds appear only above some weight, ship with that `safe_max` and
  the proof still passes *if* safe_max ≥ 0.7.
- Residual p95 ≤ **0.3 cm** over the belly mask (matching the POC's
  demonstrated transfer quality).
- The `.target` loads in stock MakeHuman/MPFB2 with no code changes —
  proving the injection route, not just our viewer.

**What it proves if it passes:** the full loop — learned delta → canonical
slider → foreign base instance → a *third-party application* gaining a
slider it never had. Every other slider after that is batch work.

## 9. Risks / open questions

- **Head transfers will be the weak link** — hm08 head vertex density vs
  our layered base head; expect muzzle sliders to need hand-authored
  correction on the MH instance. Budget for it; don't let it block the body
  proof.
- **Macro-grid entanglement** when *mining*: MH macro targets are grid
  corners, not independent sliders — mining them as canonical sliders needs
  a de-gridding step (sample the grid at axis extremes). Detail targets
  mine cleanly; macros mine with care.
- **Licence hygiene on generated files**: a `.target` generated from
  study-only learned data must carry its provenance into any folder it
  lands in (filename suffix or sidecar) so it can never be mistaken for a
  CC0 MH asset later.
- **Anny precedent** [S]: NAVER's Anny already rebuilt MH assets as a
  differentiable parametric model with phenotype blending — evidence the
  MH target library tolerates re-packaging into other parametric systems,
  and a design reference (not code) for phenotype-layer-over-targets.

---

### Sources (accessed Nov 12, 2026)

- MakeHuman community docs — Modifiers System (DeepWiki mirror of
  `makehuman/apps/humanmodifier.py`); MHBlenderTools: MakeTarget;
  Technical notes on MakeHuman (targets & modifiers) —
  static.makehumancommunity.org.
- MakeHuman licensing — LICENSE.md / LICENSE.ASSETS.md summaries via
  DeepWiki `makehumancommunity/makehuman` (Licensing page); MPFB2
  LICENSE.md §C–D as quoted in third-party licence audits (GitHub).
- MPFB2 usage — HumanService/TargetService API from MPFB2 script samples
  and third-party build docs (GitHub: tkleisas/MiVic MAKEHUMAN.md;
  happydave/asset-harness MPFB2 findings — base vert counts, rig table).
- Asset packs index + Animal 01/02/03 pack pages —
  static.makehumancommunity.org/assets/assetpacks/.
- Local: MPFB2 2.0.18 zip manifest [L]; Nov 10 photoreal build scripts [L];
  `character_assets/learned/` artifacts + FIT_REPORT.md [L].
