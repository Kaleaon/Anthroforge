# AnthroForge — Application Master Blueprint

*Nov 12, 2026. Joe's commission: "make complete, detailed instructions in
every single aspect, to make this into an app, not just a web page, with an
MCP connector, DAE, FBX, BLEND, etc. exports, as well as ways of doing fur,
body hair, skinning, etc."*

*This is the build specification for **AnthroForge the application**: an
installable, offline-first character creator whose viewport descends from
the single-file Babylon.js prototype
(`anthroforge_3d_pro_v2.html`), whose slider engine is the omniversal
learned-morph system, whose parts are swappable rigged modules, and whose
control surface is exposed to AI agents over MCP as a first-class citizen.*

*Companion documents (normative — this blueprint builds on them, it does
not re-decide them):*
- *`species-head-spec.md` — the 25-slider head framework + species presets.*
- *`preset-orc-bara.md` — first preset family (head/body/teeth/materials).*
- *`MAKEHUMAN_OMNIVERSAL.md` — canonical slider record, retargeting, licences.*
- *`CREATOR_LESSONS.md` — 12 design rules (cited below as R1–R12).*
- *`~/workspace/character_assets/teeth/TEETH.md` — universal teeth arcade.*
- *`~/workspace/specs/models/RIG_CONTRACT.md` — pose conventions + homology.*
- *`brow-study.md` — **pending** at time of writing; §7.4 reserves its slot.*

*Tagging: **[S]** sourced/existing fact, **[D]** decision taken in this
blueprint, **[DECISION]** genuinely Joe's call, with options + recommendation.*

---

## Table of contents

1. Product definition
2. Architecture
3. Data model
4. MCP connector — full design
5. Viewport & editing UX
6. Geometry core
7. Head construction (layered anatomy)
8. Skinning
9. Fur & body hair
10. Materials & textures
11. Export pipeline (per format)
12. Import & learning pipeline
13. Library, provenance & licence enforcement
14. Non-functional requirements
15. Roadmap
16. Risks, open questions & DECISION list

---

## 1. Product definition

### 1.1 What the app is

AnthroForge is a **parametric avatar creator for anthropomorphic and
fantasy characters**. A character is *created*, not loaded: a base body/head
plus a vector of **omniversal sliders** (learned deformations, not guessed
ones), a manifest of **swappable rigged parts** (ears, muzzles, jaws, tails,
teeth arcades, genitalia modules, hair/fur systems), and a **material
stack** (skin, coat, scars, warpaint). Every character serialises to a
small, portable **character record** — which is also the share-code payload
(CREATOR_LESSONS R2).

Differentiators, in order of importance:

1. **Sliders are learned.** Deformation fields are extracted from real
   models by the learn-then-delete pipeline (Fat Males exact deltas, HIMBO
   126-slider decode, foreign-topology fit at median residual 0.05 cm /
   p95 0.28 cm) — the app ships *measurements*, not artist guesses.
2. **One slider vocabulary across bases.** The omniversal canonical record
   (`MAKEHUMAN_OMNIVERSAL.md` §6.1) means "belly", "muzzle length",
   "masseter" mean the same thing on the AnthroForge base, on MakeHuman's
   hm08, and inside Skyrim BodySlide data — each base holds a generated
   *instance* of the slider with its own QA numbers.
3. **Layered anatomy.** Heads (and later bodies) are authored as
   skull → muscle → tissue; sliders deform the stack coherently, so a brow
   ridge is bone, a scowl is muscle, padding is tissue (Joe's rule;
   CREATOR_LESSONS R12).
4. **Parts are modules.** Rigged parts carry their own skin weights to the
   shared skeleton and attach at named sockets (Spore/SL modularity
   ruling). Parts carry conflict metadata and a visible complexity cost
   (R4, R5).
5. **Agents are users.** The full creator surface is exposed over MCP
   (§4), so Joe — or an AI family member — can build, adjust, render and
   export a character without touching the GUI. The GUI and the MCP tools
   call the *same* core service; there is no second-class API.

### 1.2 Target platforms

| Priority | Platform | Notes |
|---|---|---|
| **P0** | Windows 10/11 x64 (Joe's machine) | Primary dev + ship target. Installer + portable zip. |
| P1 | Linux x64 (this VM / Joe's infra) | Same codebase; needed for headless batch + CI renders. |
| P2 | macOS (Apple Silicon) | Tauri makes it cheap; sign/notarise only if Joe wants it distributed. |
| — | Mobile / web-only | **Out of scope.** The v2 HTML remains as a read-only viewer fallback, not the product. |

### 1.3 Operating stance

- **Offline-first, fully.** No account, no telemetry, no cloud dependency.
  The library, characters, and learned data live on the user's disk.
  Network is used only when the user explicitly runs an intake action
  (§12) — and even then the *library* is local files.
- **Local AI welcome.** MCP (§4) listens on loopback only by default.
- **Files are the truth.** Characters, sliders, parts and presets are
  plain files (JSON + NPZ + meshes) in a visible library folder — never
  locked inside an opaque database. SQLite is an *index* over the files,
  rebuildable at any time (§2.5).
- **Re-editing is free, forever** (R7). Nothing about a saved character is
  permanent; every export is re-derivable from its record.

### 1.4 Users

| User | How they drive it |
|---|---|
| Joe (primary) | GUI on Windows; also voice/agent delegation. |
| AI agents (Tinker, family bots, coding agents) | MCP over stdio or loopback HTTP. |
| Future community | Share codes + part/slider packs (files), imported locally. No server component in v1. |

---

## 2. Architecture

### 2.1 Shape of the system

```
┌────────────────────────────────────────────────────────────────┐
│  AnthroForge app (Tauri 2 shell)                               │
│  ┌──────────────────────────┐   IPC (Tauri commands/events)    │
│  │  Frontend (WebView)      │◄──────────────────────────────┐  │
│  │  Babylon.js viewport     │                               │  │
│  │  + editor UI (TS)        │                               │  │
│  └───────────┬──────────────┘                               │  │
└──────────────┼──────────────────────────────────────────────┼──┘
               │ localhost HTTP (JSON)                        │
               ▼                                              │
┌──────────────────────────────────────────────────────────┐  │
│  Core Service (Python, headless, single process)         │  │
│  • character state machine (the ONE implementation)      │  │
│  • slider engine (canonical records + per-base instances)│  │
│  • morph/parts/fur evaluation → geometry buffers         │──┘
│  • library index (SQLite) + provenance gate              │
│  • job queue (fits, exports, renders are jobs)           │
└──────┬───────────────────────┬──────────────────┬────────┘
       │ subprocess pool       │ subprocess        │ stdio / HTTP
       ▼                       ▼                   ▼
┌──────────────┐      ┌────────────────┐   ┌────────────────────┐
│ Blender 5.2  │      │ Python workers │   │ MCP server         │
│ sidecar      │      │ (fit, learn,   │   │ (same Core API,    │
│ (exports,    │      │  npz/osd I/O,  │   │  §4) — agents      │
│  fur bake,   │      │  teeth fit)    │   │                    │
│  skinning)   │      └────────────────┘   └────────────────────┘
└──────────────┘
       ▲
       │ files only (no linking)
┌──────┴───────────────────────────────────────────────────────┐
│  Library folder (user-visible)                               │
│  characters/  sliders/  instances/  parts/  presets/         │
│  bases/  teeth/  fur/  materials/  intake/  exports/         │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 The shell — Tauri vs Electron

| Criterion | **Tauri 2** | Electron |
|---|---|---|
| Installer size | ~5–10 MB shell (+ WebView2 runtime, preinstalled on Win11) | ~80–150 MB (bundles Chromium) |
| RAM at idle | Low (system WebView) | High (full Chromium per app) |
| Babylon.js rendering | WebView2 = Chromium — full WebGL2/WebGPU path the v2 app already uses | Chromium — identical |
| Native integration | Rust core; spawning/managing sidecars is natural | Node core; also fine |
| Joe's constraint | Flip-phone-era hardware budget matters; disk floor discipline (≥55 GB free on the VM) argues for the small shell | Works, but heavier |
| Risk | WebView2 version variance on old Win10 installs | Bundle bloat; slower cold start |

**[D] Recommendation: Tauri 2.** The viewport is already Babylon.js on
Chromium tech, so WebView2 costs us nothing; the Rust core is only a
launcher/supervisor (all real logic lives in the Core Service, §2.3), so
the Rust surface stays tiny. Electron is the documented fallback if a
WebView2-specific rendering bug ever blocks us — the frontend must
therefore avoid Tauri-only APIs outside one thin `host.ts` shim.

**[DECISION] D1 — Shell: Tauri 2 (recommended) vs Electron.** Cost of
switching later is low *if* the shim rule above is kept.

### 2.3 Core Service (Python)

One Python 3.12 process is the single implementation of everything that
isn't pixels:

- **Character state machine** — load/save/validate character records,
  apply slider vectors, equip/unequip parts, evaluate the *resolved
  character* (base + morphs + parts + fur parameters) into geometry
  buffers the viewport renders.
- **Slider engine** — canonical records + per-base instances
  (`MAKEHUMAN_OMNIVERSAL.md` §6.1); applies instances as vertex deltas;
  enforces `safe_range`; reports folds.
- **Job queue** — everything slow (foreign-topology fits, exports, fur
  bakes, renders, learn-pipeline runs) is a job with progress events, a
  log, and cancellation. The GUI never blocks; MCP calls can poll or wait.
- **Library index** — SQLite over the library folder (§2.5).
- **Provenance gate** — every read of a slider/part/material checks its
  licence tier (§13) before it can enter an export marked "clean".

Why Python: the entire existing toolchain already is Python —
`learned/tools/` (`nifparse.py`, `osdparse.py`, `fit_foreign.py`,
`himbo_full_decode.py`), the base-head builders, the teeth work. NumPy is
the native tongue of delta fields. Rewriting any of it in Rust/TS would
burn the project's scarcest resource (time) for zero user-visible gain.

### 2.4 Blender sidecar

Blender **5.2** (already installed and proven headless in this workspace:
base-head builds, MPFB2 photoreal build) runs as a managed subprocess
pool (1–2 workers), driven by generated Python scripts over a job
protocol (JSON in / JSON out + file paths):

Jobs owned by the sidecar:
- **Exports**: DAE, FBX, BLEND (§11) — Blender is the only sane free
  implementation of all three.
- **Fur**: strand generation + card baking (§9).
- **Skinning**: automatic weights (voxel/heat), weight cleanup, rig
  construction from the canonical rig definition (§8).
- **Base authoring**: base-head/body builders, layered-anatomy stack
  evaluation (§7).
- **Validation renders**: studio-HDRI QA renders (Poly Haven HDRI already
  in the library), pose-test renders (§8.5).

**Do not bundle Blender in the installer.** Detect a Blender ≥4.2 install
(user-pointed path setting) or offer a one-click download of the portable
build into the app-data folder. Rationale: Blender is GPL; bundling is
legal but heavy (~1 GB) and version-pinning our sidecar scripts to *our*
tested 5.2 matters more than zero-config. **[DECISION] D2 — bundle a
pinned portable Blender (zero-config, ~1 GB, version-locked) vs detect
external install (lean, user-managed). Recommendation: detect-first with
guided download fallback.**

MPFB2 is used the same way as today: invoked inside Blender scripts as a
tool, never linked or redistributed by the app (`MAKEHUMAN_OMNIVERSAL.md`
§3 — GPL tool, CC0 payload; our outputs are ours).

### 2.5 Storage

- **Library folder** (default `~/AnthroForge Library/`, user-movable):
  plain files, layout in §3.6. Human-browsable on purpose.
- **SQLite index** (`library.db` in app-data): tables for sliders,
  instances, parts, characters, presets, materials, fur profiles, jobs.
  It is a *cache*: `anthroforge reindex` rebuilds it from the files. If
  the DB and a file disagree, the file wins.
- **App-data**: settings, MCP token, Blender path, job logs, undo history
  (per character, file-backed journal — §5.7).

### 2.6 Process & failure rules

- Core Service is supervised by the Tauri shell (restart on crash, state
  recovered from files; in-flight jobs marked failed, never silently
  retried).
- The viewport is disposable: killing the WebView loses nothing but the
  camera angle. All edits flow *through* the Core Service (command
  pattern), so GUI and MCP edits interleave safely on one character.
- Coordinate frames: **canonical storage frame is metres, Y-up,
  Z-forward** (RIG_CONTRACT pose conventions; matches the soma rig work).
  Blender is Z-up: the sidecar owns the one conversion at its boundary.
  Babylon is left-handed: the frontend owns its conversion. Every file
  format writer states its frame in its section (§11). This is the
  `MAKEHUMAN_OMNIVERSAL.md` §5.7 rule made structural: conversions live
  at exactly one boundary each, never sprinkled through the code.

### 2.7 What is reused, as-is

| Existing asset | Reused as |
|---|---|
| `anthroforge_3d_pro_v2.html` (169 KB) | Split into the frontend: Babylon scene setup, the verified 36-bone `BABYLON.Skeleton` builder, bind-pose baking, `computeMeshSkinWeights` (→ §8 fallback), part equip/socket prototype (`equipPart`, socket rings/dropzones), heatmap view, GLB export validation. The single-file structure dies; the code survives. |
| `lib/babylon.js` + loaders/serializers | Vendored frontend dependencies (offline rule — no CDN). |
| `learned/tools/*.py` | Core Service modules: NIF/OSD parsing, fit engine, HIMBO decode. |
| `learned/*.npz/json` + FIT_REPORT | First slider instances + QA baselines. |
| Base head v1/v2 builders + groups JSON | §7 authoring pipeline + vertex-region definitions. |
| MPFB2 + MH system assets (local) | Human bases/targets via sidecar; CC0 mining source (§12.4). |
| CharMorphExpansion `convert-makehuman` tooling | Precedent hm08 conversion; reference for instance generators. |
| Linkpoint `core/sl-asset-decoder.cjs` | LLMesh → geometry decoding for SL intake (§12.5). |
| SL grabber (`sl-client/grabber/`) | Inventory catalogue source for wear-scan queue (§12.5). |
| Z-Anatomy (CC BY-SA) | Muscle-layer authoring reference for §7. |
| RIG_CONTRACT homology (`mammal_deform.py`, `species_space.py`) | Part retargeting + species pole-blend maths (§6.5, §5.3). |

---

## 3. Data model

### 3.1 The character record (`.afchar.json`)

The one file that *is* a character. Everything else is derived.

```json
{
  "format": "anthroforge.character",
  "version": 1,
  "id": "chr_01J…ULID",
  "name": "Unnamed",
  "base": { "body": "af_body_neutral_v1", "head": "af_head_neutral_v2" },
  "sliders": { "body.belly.protrusion": 0.62, "head.muzzle.length": -0.35 },
  "species_preset": { "id": "species.wolf", "weight": 1.0,
                      "residual_edits": { "head.ear.height": 0.1 } },
  "parts": [
    { "slot": "ear.L", "part": "ear_point_v1", "variant": null,
      "transform": { "offset": [0,0,0], "rotate_deg": [0,0,0], "scale": 1.0 } },
    { "slot": "teeth.arcade", "part": "teeth_arcade_universal",
      "params": { "canine": 80, "molar": 55, "incisor": 50, "wear": 10,
                  "tusk_lower": 80, "damage": { "side": null, "amount": 0 } } }
  ],
  "fur": { "profile": "species.wolf.coat", "overrides": { "torso.back.density": 0.9 } },
  "materials": { "skin": { "palette": "orc.classic_green", "base": "#6B8E3D" },
                 "layers": [ { "kind": "scar", "id": "scar_brow_L", "opacity": 0.8 } ] },
  "identity": { "notes": "", "family": null },
  "provenance": { "created_by": "gui|mcp", "app_version": "…" }
}
```

Rules:
- **Sliders are sparse**: absent = default (usually 0). A character file
  stays small and diff-able; presets are just named slider vectors (R1).
- **Parts reference library IDs + versions**, never embedded meshes. A
  character is portable iff the recipient's library has the parts — the
  share flow checks and reports missing parts by ID (§5.6).
- `identity` carries R10's non-geometry layer (name, family, notes).

### 3.2 Share code

The character record minus provenance, compressed (deflate) and
base64url-encoded, prefixed `AF1-`. Expected length: ~200–600 chars for a
typical build (SF6-recipe-class). Also exportable as a QR code and as the
`.afchar.json` file itself. Codes are **versioned by prefix**; a future
format change is `AF2-`, old codes keep decoding. Parts/sliders referenced
by ID resolve against the local library; unresolvable IDs degrade
gracefully (base + sliders still apply; missing parts listed).

### 3.3 Canonical slider record

Adopted verbatim from `MAKEHUMAN_OMNIVERSAL.md` §6.1 — semantic ID,
landmark/geodesic region mask, endpoint anchor in metres, range +
`safe_range`, symmetry, provenance/licence, per-base instances with QA
(residual p95, fold count). Two additions from the orc work:

- `"extensions"` namespace for sliders a preset family needs beyond the
  base set (e.g. `head.jaw.protrusion` from `preset-orc-bara.md` §2.2 —
  the forward jaw translation no existing slider expressed; `body.neck.mass`
  from §3.0 there). Extensions are ordinary records; the orc preset simply
  ships the first two.
- `"couplings"`: sliders whose effect depends on another slider's value
  (tusk emergence angle = f(JawWidth), orc spec §4.1). A coupling is a
  named function + its inputs; the engine evaluates couplings after the
  base vector, deterministically, so GUI/MCP/export all agree.

### 3.4 Part record (`part.json`, one per part, beside its meshes)

```json
{
  "format": "anthroforge.part", "version": 1,
  "id": "ear_point_v1", "label": "Pointed ear",
  "kind": "anatomy | teeth | hair | clothing | prop",
  "sockets": ["ear.L", "ear.R"],
  "meshes": { "lod0": "ear_point_lod0.glb", "lod1": "…", "print": "….stl" },
  "skin": { "mode": "own-weights | inherit | rigid",
            "bones": ["EarBase_L", "Ear1_L", "Ear2_L", "EarTip_L"] },
  "fit": { "regions": ["head.ear.base"], "rescale_by": ["head.ear.height"] },
  "conflicts": [ { "with": "hair_mane_v1", "kind": "clip|exclude",
                   "note": "mane shell intersects ear base above EarHeight +60" } ],
  "cost": { "verts": 1450, "bones": 4, "morphs": 0, "points": 6 },
  "fur": { "accepts": ["ear.inner"] },
  "licence": { "tier": "build", "spdx": "CC-BY-4.0", "attribution": "…" },
  "provenance": { "source": "authored | learned | mined", "detail": "…" }
}
```

- `skin.mode` implements the modularity ruling: **own-weights preferred**
  (part carries skinning to the shared skeleton), `inherit` = weights
  transferred from the base at equip time (§8.4), `rigid` = bone-attached
  fallback tier.
- `cost.points` is the WWE-style complexity price (R5): computed from
  verts/bones/morphs by a published formula, shown in the UI, enforced at
  export (§11.0).
- `conflicts` is R4's metadata, present from the first part ever shipped,
  not patched in later (SCVI lesson).

### 3.5 Sockets

Canonical socket list (extends the v2 prototype's socket system):
`ear.L/R`, `muzzle`, `jaw`, `nose`, `head.top` (crest/horns),
`hair`, `teeth.upper`, `teeth.lower`, `tail.base`, `wing.L/R`,
`arm.L/R`, `leg.digi.L/R`, `pelvis.genital`, `neck.ruff`, `eye.L/R`
(pupil/iris variants), `brow` (torus variant strips), `back`, plus
**free-attach slots** `free.1..4` (R9: position/rotation/scale on any
bone, for props/ornaments). Each socket names its bone, its fit region,
and which part kinds it accepts.

### 3.6 Library layout

```
<Library>/
  bases/            base body/head meshes + rig definitions + region maps
  sliders/          canonical records: sliders/<id>.json
  instances/        per-base deltas: instances/<base>/<id>.{npz,target}
  parts/            parts/<id>/part.json + meshes
  presets/          species, orc sub-presets, Titan family, user presets
  teeth/            arcade geometry + diet-morph data (from TEETH.md work)
  fur/              fur profiles + groom maps
  materials/        palettes, layer decals, PBR sets
  characters/       .afchar.json files (+ .afpkg bundles, §11.8)
  intake/           staging for §12 (learn-then-delete workspace)
  exports/          default export destination
```

### 3.7 Presets

A preset is a file of exactly the same shape as the character record's
variable sections — `{ sliders, parts, fur, materials }` — plus metadata
(name, family, author, thumbnail render). Applying a preset = merging its
sections into the current character (R1: a starting point, still fully
editable). Species presets (wolf/fox/fennec/lion/panther/cat/dog from the
head spec + body counterparts), the two orc sub-presets, and the style
axis (realistic ↔ toony interpolation between two anchor vectors,
species-head-spec addendum) are all just presets + one interpolation rule.

---

## 4. MCP connector — full design

AnthroForge ships an **MCP server** (`anthroforge-mcp`) that exposes the
Core Service's entire surface. Design rule: **the MCP server contains no
character logic.** Every tool is a thin, typed wrapper over the same Core
API the GUI calls — so an agent and a human can edit the same character
interleaved, and a feature that exists in one surface exists in both.

### 4.1 Transports

| Transport | For | Details |
|---|---|---|
| **stdio** (primary) | Local agent hosts (Muse/Desktop-style) | Server launched by the host: `anthroforge-mcp --stdio`. Core Service is spawned-or-attached automatically (single-instance lock). Zero network surface. |
| **Streamable HTTP** | Agents on the same machine / home network (family bots, the VM) | `http://127.0.0.1:8765/mcp` by default. **Loopback-only unless the user flips the LAN toggle** (§4.2). |

One server binary serves both. The app installer registers the stdio
config snippet for common hosts (a "Connect an agent" panel in Settings
shows copy-paste config for each host type + a live connection list).

### 4.2 Auth & safety model

- **stdio**: trusted by construction (the host process launched it). No
  token.
- **HTTP**: bearer token, generated on first run, stored in app-data
  (never in the library), shown/rotated in Settings. Requests without it
  get `401`. Token is per-install, not per-user (single-user app).
- **LAN exposure is OFF by default** and is a **[DECISION] D3**: options
  (a) loopback-only forever (agents must run on the same machine),
  (b) loopback default + explicit LAN toggle with token (recommended —
  the Titan family bots live on other hosts by design).
- **Destructive-action policy**: tools are split into *read*,
  *edit* (reversible via the character journal, §5.7), and *commit*
  (writes files: save, export, learn-pipeline delete step). Commit tools
  accept a `dry_run` flag; the learn pipeline's delete step **requires**
  `confirm_delete: true` with the learned artifact's checksum echoed
  back (§12.2) — an agent cannot delete a source model on a guess.
- Rate limits: renders/exports are job-queue bound (§4.5); the server
  never runs more jobs concurrently than the queue allows.

### 4.3 Tool surface (28 tools)

Conventions: all tools take/return JSON. `character` params accept a
character ID or `"current"` (the GUI's open character) or `"new"`.
Lengths in metres, angles in degrees, slider values in canonical units
(−1…+1 bipolar or 0…1 as the record declares; tools also accept the
−100…+100 display scale via `scale: "display"`).

**Character lifecycle**

| # | Tool | Parameters (sketch) | Returns |
|---|---|---|---|
| 1 | `character_create` | `name?, base_body?, base_head?, species_preset?` | character record + id |
| 2 | `character_load` | `character` (id/path/share-code `AF1-…`) | record + resolved summary (verts, parts, cost) |
| 3 | `character_save` | `character, path?` *(commit)* | path, checksum |
| 4 | `character_share_code` | `character` | `AF1-…` code + QR png path |
| 5 | `character_duplicate` / `character_delete` | `character, new_name?` | new id / deletion receipt |

**Shaping**

| # | Tool | Parameters | Returns |
|---|---|---|---|
| 6 | `sliders_list` | `group?, base?` | canonical records (id, label, range, safe_range, licence tier, per-base QA) |
| 7 | `sliders_get` | `character` | current sparse vector (dense on request) |
| 8 | `sliders_set` | `character, values: {id: value}, scale?` | applied vector, clamp/fold warnings per slider |
| 9 | `preset_apply` | `character, preset_id, weight 0..1?, sections?` | diff summary (what changed) |
| 10 | `blend_set` | `character, space: "body_composition"|"species_poles", point: [x,y] or weights` | resulting slider vector (triangle/pole maths, §5.3) |
| 11 | `anatomy_inspect` | `character, layer: skull|muscle|tissue|all` | layer meshes' stats + landmark measurements (head ratios vs spec) |

**Parts & teeth**

| # | Tool | Parameters | Returns |
|---|---|---|---|
| 12 | `parts_search` | `query?, kind?, socket?, tier?` | part records (cost, conflicts, licence) |
| 13 | `part_equip` | `character, slot, part_id, variant?, transform?` | equip result + conflict report + new cost total |
| 14 | `part_remove` | `character, slot` | removal receipt |
| 15 | `teeth_set` | `character, diet_preset? | {canine, molar, incisor, wear, tusk_lower, damage}` | arcade params + clearance check result (§7.5) |

**Fur & materials**

| # | Tool | Parameters | Returns |
|---|---|---|---|
| 16 | `fur_set` | `character, profile? | region params {region: {density, length, curl, clump, colour}}` | fur summary + perf estimate (§9.7) |
| 17 | `material_set` | `character, slot, palette? | hex, layers?: [{kind, id, opacity}]` | material stack |
| 18 | `library_search` | `query, kinds?: [slider|part|preset|material|fur]` | ranked records across the library |

**Render, export, jobs**

| # | Tool | Parameters | Returns |
|---|---|---|---|
| 19 | `render_preview` | `character, views: [front|side|threequarter|back], lighting: studio|inworld, pose?` | job → PNG paths (studio HDRI, honest light R11) |
| 20 | `export_run` | `character, format: glb|dae|fbx|blend|obj|stl|target|afpkg, profile?, path?` *(commit)* | job → file + validation report (§11.0) |
| 21 | `jobs_list` / `job_get` / `job_cancel` | `job_id?` | status, progress, log tail |

**Learning pipeline (§12)**

| # | Tool | Parameters | Returns |
|---|---|---|---|
| 22 | `intake_import` | `path, licence: {tier, spdx?, note}` *(commit)* | staged intake id + mesh stats |
| 23 | `intake_learn` | `intake_id, base, mode: exact|fit, sliders?: [ids]` | job → learned instances + residual report |
| 24 | `intake_finalize` | `intake_id, learned_checksum, confirm_delete: bool` *(commit)* | library filing receipt / source deleted |

**System**

| # | Tool | Parameters | Returns |
|---|---|---|---|
| 25 | `app_status` | — | version, library path, bases installed, Blender found?, queue depth |
| 26 | `rig_get` | `base` | canonical rig definition (bones, sockets, conventions) |
| 27 | `validate_character` | `character` | full gate report (§8.5 + §11.0 checks, without exporting) |
| 28 | `undo` / `redo` | `character, steps?` | journal position (agents share the GUI's undo history) |

### 4.4 Resources & prompts

- **Resources** (read-only, URI-addressed):
  `anthroforge://character/{id}` (record + resolved summary),
  `anthroforge://slider/{id}` (canonical record),
  `anthroforge://part/{id}`, `anthroforge://preset/{id}`,
  `anthroforge://library/manifest` (counts, tiers, bases),
  `anthroforge://job/{id}/log`.
- **Prompts** (server-provided workflows):
  `build_character` (guided: species → body triangle → parts → fur →
  render → export), `learn_from_model` (intake walkthrough with licence
  gate), `qa_character` (validate + render + summarise failures).
- Resource subscriptions: `character/{id}` notifies on change, so an
  agent watching the GUI user work sees edits live.

### 4.5 Async & the job model

Tools 19, 20, 23 return immediately with a `job_id` (plus `wait_ms`
option: block up to N ms for small jobs). All other tools are
synchronous and fast (< 200 ms budget; slider application on a 40k-vert
base is a NumPy delta sum, measured class: tens of ms).

### 4.6 Error model

Every error is structured; no stack traces cross the wire:

```json
{ "error": { "code": "PART_CONFLICT", "message": "hair_mane_v1 clips ear_point_v1 above EarHeight +60",
             "details": { "slot": "ear.R", "conflict": "clip" }, "retryable": false,
             "suggestion": "lower head.ear.height below 0.6 or choose ear_round_v1" } }
```

Code families: `NOT_FOUND`, `LICENCE_TIER` (study-only content in a
clean export), `PART_CONFLICT`, `SLIDER_RANGE` (value beyond safe_range —
returned as warning unless `strict: true`), `FIT_RESIDUAL` (learn job
exceeded threshold), `EXPORT_VALIDATION` (gate failures listed),
`JOB_FAILED` (with log resource URI), `AUTH`, `BAD_INPUT`.

### 4.7 Worked example session (abridged, real shapes)

```
→ tools/call character_create { "name": "Test Orc", "species_preset": "species.none" }
← { "id": "chr_01J9…", "base": {"body":"af_body_neutral_v1","head":"af_head_neutral_v2"} }

→ tools/call preset_apply { "character": "chr_01J9…", "preset_id": "orc_bara_strongman" }
← { "changed": 71, "warnings": [ { "slider": "body.torso.mass", "note": "at safe_max" } ] }

→ tools/call teeth_set { "character": "chr_01J9…", "diet_preset": "omnivore",
                         "tusk_lower": 80 }
← { "arcade": "teeth_arcade_universal", "clearance": { "diastema_ok": true, "lip_ok": true } }

→ tools/call fur_set { "character": "chr_01J9…", "profile": "none",
                       "regions": { "scalp": { "density": 0.4, "length": 0.06 } } }
← { "strands_est": 18400, "perf_class": "realtime-cards" }

→ tools/call render_preview { "character": "chr_01J9…", "views": ["front","threequarter"] }
← { "job_id": "job_4471" }   → job_get → { "done": true, "files": ["…/front.png", …] }

→ tools/call export_run { "character": "chr_01J9…", "format": "glb" }
← { "job_id": "job_4472" }   → { "done": true, "file": "…/Test Orc.glb",
    "validation": { "skin": true, "joints": 44, "morphs": 12, "folds": 0, "conformance": "clean" } }
```

### 4.8 Versioning

MCP tool schemas are versioned with the app (`app_status` reports
`mcp_schema: 1`). Additive changes only within a schema version; a
breaking change bumps it and the server keeps serving the previous
version's tools under a `/v1` namespace for one release.

---

## 5. Viewport & editing UX

The frontend is the v2 app, restructured: Babylon.js viewport centre,
editor panels around it, all state owned by the Core Service (the GUI is
a view + command emitter, §2.6). Rules R1–R12 are requirements here, not
aspirations.

### 5.1 Layout

- **Centre**: viewport (Babylon), neutral studio lighting by default +
  one "in-world" lighting preset toggle (R11). Ground grid off by
  default; turntable button; camera bookmarks (face / full / part
  close-ups).
- **Left**: character tree — base, parts by socket, fur regions, material
  layers; complexity budget meter pinned at its head (R5).
- **Right**: contextual editor (sliders / part browser / fur / materials
  / anatomy, per selection).
- **Bottom**: job strip (fits, exports, renders with progress), message
  log (warnings in plain language, e.g. "Belly slider is past its safe
  range on this base — folds may appear").
- **Top**: character name, share code button, export menu, undo/redo.

### 5.2 Slider panels

- Categories mirror the canonical groups: Body (composition / torso /
  arms / legs), Head (muzzle / cranium / ears / jaw-cheeks / eyes-brow),
  Face detail, Teeth, Fur. Search box across all (Elden Ring's laboratory
  is the depth model; its discoverability is the anti-model).
- Each slider row: name, numeric readout (canonical units, editable),
  range bar with the **safe range shaded** and per-base QA badge (a
  slider whose instance on this base has p95 > 0.3 cm shows a subtle
  "approximate" marker — honesty surfaced, per the omniversal design).
- **Link/unlink toggle per bilateral slider** (R6: complete asymmetry or
  none — Saints Row's partial coverage is the documented failure).
- Right-click a slider: "copy value", "reset", "show region" (highlights
  the mask on the mesh), "provenance" (source + licence of the delta).

### 5.3 Blend controls (R3)

- **Body composition triangle**: mass ↔ muscle ↔ lean (the Fat Males /
  HIMBO axes exactly), a 2D pad; every interior point is valid. Sliders
  driven by the triangle update live; grabbing a driven slider directly
  moves the triangle point.
- **Species pole blend**: head identity as a blend between species
  anchors (wolf ↔ fox ↔ cat ↔ lion…) — poles are the preset vectors;
  GTA's lesson applies: pole *diversity* creates the variety. Implemented
  as weighted vector interpolation in slider space.
- **2-axis pads** for position parameters (ear placement, eye spacing ×
  height) — DAI's one good idea, kept.

### 5.4 Direct manipulation (R6)

Drag on the mesh: pull a muzzle longer, push a belly out, drag ears up.
Pointer rays map to the nearest slider region; drag distance maps to
slider delta. Double-click a feature → detail mode (fine handles +
numeric). This drives the *same* sliders — the parameter vector
underneath is untouched conceptually, only the input method differs.

### 5.5 Part browser & sockets

- Grid browser (the v2 prototype's parts grid, grown up): filter by
  socket/kind/licence tier; each card shows thumbnail, cost points,
  conflict icons.
- Click a socket ring in the viewport (prototype already draws them) →
  compatible parts only. Drag-and-drop from browser to socket works too
  (prototype's dropzones).
- Free-attach mode (R9): pick a prop, click anywhere on the body, then
  position/rotate/scale gizmo; the attach stores bone + local transform.
- Conflicts surface *before* equip completes: modal lists clip/exclude
  conflicts with "equip anyway" (flagged on the character) or cancel.

### 5.6 Presets & share codes (R1, R2)

- Preset gallery: species, orc sub-presets, Titan family, user presets —
  each a thumbnail + name; applying one shows a **diff preview** (which
  sliders/parts change) before commit.
- Share panel: generates `AF1-` code + QR; import box accepts code, file,
  or drag-dropped `.afchar.json`. Import reports missing library items by
  ID with a "what's missing" list — never a silent partial character.

### 5.7 Undo, journal, autosave

Every mutation (GUI or MCP) appends to the character's journal (command
+ inverse). Undo/redo are journal walks; the journal persists with the
character, so yesterday's session is undoable today. Autosave writes the
record on every committed change (atomic rename); exports never modify
the record.

### 5.8 Anatomy inspector

Toggle layers (skull / muscle / tissue / surface) for heads (§7) and,
later, bodies: X-ray slider (layer opacity), isolate buttons,
measurement readout (the head-spec ratios, live). This is an *inspector*,
not an editor (R12) — users see the stack exists and what it does; they
edit sliders.

### 5.9 Weight-paint mode — see §8.4. Fur grooming view — see §9.6.

### 5.10 Posing for preview

A small pose library (stand, walk cycle sample, jaw open, head turns) for
QA previews — poses are *tests*, not an animation editor. Pose-test
renders double as the skinning validation gate (§8.5).

---

## 6. Geometry core

### 6.1 Bases

| Base | Status | Notes |
|---|---|---|
| Neutral body v1 | To author (Phase 2) | Humanoid-plantigrade/digitigrade-switchable via leg parts; quad-dominant, ~35–45k verts; region map parallel to the head's. Interim: MPFB2 hm08 human as the dev base (CC0) so the engine is testable end-to-end before our base lands. |
| Neutral head v2 | **In build** (`base-head-v2/`) | Layered construction (§7); 20 vertex groups already defined (groups JSON on disk); ~7.4k verts class. |
| hm08 (MakeHuman) | Local (CC0) | Foreign base #1: instance generation + mining target (§12.4). |
| Skyrim HIMBO / Fat Males | Local (study-only) | Source bases for learned deltas; never ship as bases. |

Every base ships with: mesh, region/landmark annotation file (the
portable masks of the omniversal design), rig definition (§8.1), and a
**base card** (vert count, frame, units, licence).

### 6.2 Morph engine

- Evaluation is `verts = base + Σ wᵢ·deltaᵢ(base)` in NumPy, deltas held
  as sparse NPZ (only moved verts stored; Fat Males body delta = 112 KB
  at 2,024 verts — the format is proven).
- **Real morph targets, not procedural scaling**: the v2 prototype's
  BodySlide/SoS were procedural sliders; the app replaces them with true
  delta stacks. Where a target format supports morphs (GLB, BLEND), the
  *unbaked* stack can be exported as named morph targets (§11); the
  viewport always shows the evaluated sum.
- Slider application is incremental (recompute only changed deltas'
  contributions) — full recompute budget < 100 ms at 45k verts × ~200
  active sliders.
- **Fold detection** runs on demand + at export: negative-volume triangle
  test over each slider's region at current weights; results feed the
  safe-range warnings (§5.2) and the conformance flag (§11.0).
- **Couplings** (§3.3) evaluate after the raw vector (tusk angle from
  JawWidth is the reference implementation).

### 6.3 Retargeting service

The fit pipeline (`fit_foreign.py`: trimmed ICP → non-rigid registration
→ delta transfer with normal gating; POC residuals median 0.05 cm /
p95 0.28 cm) becomes a Core Service job type:

- **Base-pair correspondence cache**: register base A → base B once,
  cache the correspondence + residual mask; every slider then transfers
  through it (cost scales with pairs, not sliders —
  `MAKEHUMAN_OMNIVERSAL.md` §6.2).
- Dead zones (flank, genital patch on the POC pair) are masked, never
  transferred as noise; the mask ships inside the instance's QA block.
- Both-direction residual reporting is mandatory (one direction flattered
  the POC fit ~30×).
- Priority pairs: `himbo ↔ mh08`, `mh08 ↔ af bases`, head pairs per
  species-head-spec §4 (Codaj fennec first, then AKM cat, AKM collie).

### 6.4 Teeth arcade fitter

Per TEETH.md's proven construction — no solver theatrics:

- The universal arcade is **two rigid plates**: upper rides the skull,
  lower rides the jaw object. Fitting = scale to jaw width/length
  (landmarks from the head region map) + parent. That's the whole fitter.
- Diet morph axes (`TeethCanine/Molar/Incisor/Wear`, orc spec §4.0)
  deform tooth shapes *in place* on the plates; AAhne's parametric tooth
  (hull-of-spheres curved cone, SCAD source on disk) is the procedural
  shape function for generating endpoint variants and tusk extremes.
- Clearance checks (hard gates, §7.5): jaw closes without interpenetration;
  lower canine enters the upper diastema gap at TeethCanine-lower ≥ 70;
  tusk tips clear the upper lip line at standard settings.

### 6.5 Part fitting & extremes re-solve (R4, R8)

- Equipping a part at non-neutral sliders triggers a **fit re-solve**:
  the part's fit region is re-deformed by the current slider stack
  (region deltas applied to the part's base verts, own-weights parts) or
  re-scaled/re-seated (rigid parts). Clothing-style parts always re-solve
  on slider change — appearance is a layer over the *current* body, never
  baked to one morph state.
- At extreme slider values (|v| beyond the instance's safe range),
  exports are still produced but carry the conformance flag (§11.0) —
  quarantine-by-flag, not refusal (SF6 lesson).
- Homology warp (`mammal_deform.py`): parts authored on one body plan can
  be warped onto homologous skeletons (digitigrade ↔ plantigrade legs)
  via the canonical-landmark deformer — with its documented limits
  (nearest-segment discontinuity at joints; check renders per plan).

---

## 7. Head construction (layered anatomy)

### 7.1 The stack

Joe's rule, structural: **skull → muscles → tissue → surface.** The base
head is authored as three registered layers over one topology plan:

| Layer | Contents | Authored from |
|---|---|---|
| Skull | Cranium, zygomatics, mandible (separate jaw object on its hinge), brow torus shelf, teeth sockets | CT references (puma skull scan in `head-hunt/skull-reference/`), species-head-spec §2 ratios, Z-Anatomy |
| Muscle | Temporalis fan, masseter slab, frontalis/corrugator, orbicularis (eye + mouth), buccinator, muzzle musculature | Z-Anatomy (CC BY-SA), orc spec §2.3 method (masseter is the worked example) |
| Tissue | Fat pads (cheek, brow, submental), skin thickness field, ruff soft tissue | Species tissue profiles; sub-preset switch on orc (tissue is the Strongman↔Bodybuilder dial) |

### 7.2 How sliders use the stack

Each head slider declares which layer(s) it deforms (the canonical record
gains a `layer` hint per head slider): BrowRidge = skull (torus) with
tissue following; CheekWidth = zygomatic (skull) + masseter (muscle) in a
documented ratio; RuffVolume = tissue only. The evaluated surface is
always skull + muscle offsets + tissue offsets composed onto the surface
topology — the user sees one head; the engine keeps the accounting.

### 7.3 Base head v2 status & the v1 lesson

v1 (analytic loft) measured on-spec but read cartoony — balloon muzzle,
bead eyes, no planes. v2 (in build at `base-head-v2/`) corrects by
construction: cougar-anchored neutralisation + layered stack, eyelid
shells, seated eyes, defined nose leather, ear thickness + inner ear,
U-trough jaw with teeth/tongue, neck termination, studio-HDRI QA renders.
The app treats *whichever* base head passes Joe's visual bar as
`af_head_neutral_v2`; the builder script + groups JSON are the authoring
pipeline either way (§2.4 sidecar job).

### 7.4 Brow

The species spec's BrowRidge slider + the orc `brow_torus` variant
(continuous bar above +70) are the interim design. The commissioned
**brow study** (`brow-study.md`, Neanderthal→gorilla supraorbital
spectrum, per-layer assignment: torus = bone, scowl = muscle, padding =
tissue) slots in as the authority for BrowProjection/BrowContinuity/
BrowShelf ranges when it lands; until then, brow sliders ship flagged
`provisional` in their canonical records.

### 7.5 Jaw, teeth, mouth interior

- Jaw is a separate object, origin on the hinge axis (v2 builder proves
  −15° opening cleanly); jaw sliders deform it; the lower arcade rides it
  (§6.4).
- Mouth interior: tunnel + tongue (part, own simple rig: one bone chain)
  ship with the base head; teeth/tongue clearance is measured at build
  time (v2 builder's method) and re-checked by `teeth_set` (§4.3 #15).
- Eyes: eyeball meshes L/R seated in sockets with eyelid shells;
  pupil variants (round/slit) are eye-socket parts (§3.5), iris is a
  material (§10).

---

## 8. Skinning

### 8.1 The rig contract (app edition)

One **canonical rig definition** (JSON, versioned) generates every
skeleton the app uses; Blender and Babylon skeletons are *projections* of
it, never hand-maintained separately.

- **Body core (36 bones)** — the v2 app's verified set: pelvis/spine
  chain, neck/head, clavicle/arm/hand chains, leg/foot chains. Names
  follow the MPFB `game_engine` convention where they overlap ( eases
  MH interop), else the v2 names.
- **Head extensions**: jaw, ear chains L/R (EarBase/Ear1/Ear2/EarTip,
  Codaj pattern), brow L/R (optional, for torus-adjacent expression),
  tongue chain (3), eye L/R (look-at).
- **Module extensions** (present only when the part is equipped): tail
  chain (5–8), wing L/R (armature per part spec), digitigrade hock
  segment, crest/horn = rigid (no bones).
- **Conventions**: metres, Y-up, Z-forward storage frame (RIG_CONTRACT);
  bind pose = neutral standing, arms in relaxed A; joint positions are
  **derived from the morphed mesh** at build/export (v2 already re-derives
  bind pose on rebuild; MPFB does the same) — sliders never encode joints
  (omniversal §5.6).
- Face: bone-driven (jaw/ears/eyes) + morph-driven detail. No ARKit
  clone in v1; expression set = jaw open, blink (lid morphs), ear poses.

### 8.2 Automatic weighting

Two engines, one interface (`weights_compute(mesh, rig, method)`):

1. **Blender sidecar (primary)**: Blender's armature auto-weights
   (bone-heat) for clean manifold meshes; **voxel/geodesic binding** as
   the robust path for fused/part-heavy meshes (voxelise → geodesic
   distance to bones → diffuse) — the method that survives bara extremes
   and part unions where bone-heat fails.
2. **In-app fallback**: the v2 prototype's `computeMeshSkinWeights`
   (distance-based, 4 influences) — kept for quick previews and as the
   no-Blender path; labelled approximate.

Post-process (always): normalise to sum 1.0, cap 4 influences/vertex,
prune < 0.01, mirror-symmetry enforcement on symmetric regions, smoothing
pass across region borders (2 iterations Laplacian on weight fields).

### 8.3 Base authoring flow

Base meshes are weighted **once**, by the sidecar, at authoring time —
not per character. Slider deformation never changes weights (deltas are
bind-pose shape). Joint re-derivation at extreme morphs re-seats bones
but keeps weight *assignments*; a "re-derive + smooth" job is available
when a base author ships a new revision.

### 8.4 Parts & weights

- `own-weights` parts: weights authored with the part (in Blender,
  against the canonical rig) and validated on intake (§12.3).
- `inherit` parts: weights transferred from the base surface at equip
  time (nearest-surface + normal-gated copy, then §8.2 post-process) —
  how clothing-tier and simple anatomy parts get skinned without
  authoring effort.
- `rigid` parts: single-bone, full weight — ears' tips ornaments,
  piercings, crest strips.
- Part removal never leaves weight residue on the base (parts are
  separate meshes end-to-end; nothing is ever merged into the base).

### 8.5 Validation gates (extend v2's export checks)

Run at base authoring, part intake, and export:

1. **Bind-pose identity**: skinned bind pose vs unskinned mesh — max
   deviation must be 0.000-class (v2's verified standard: 0.000 across
   2,450 sampled verts).
2. **Pose suite**: elbow/knee bend 90°, jaw open max, head turn, ear
   chain curl, tail sway — renders checked for candy-wrapper collapse
   and interpenetration (automated: self-intersection count per pose;
   human/agent eyeballs the renders).
3. **Weight sanity**: every vertex ≥1 influence, sums = 1 ± 1e-3, no
   vertex bound to a bone > its region's allowed set.
4. **Symmetry**: L/R weight sums mirror within tolerance on symmetric
   regions.
Failures block "clean" conformance (§11.0) but never block export
outright — the file ships flagged, per R4.

### 8.6 Weight painting (GUI)

Viewport brush over the selected mesh: paint/erase/smooth/blur on the
selected bone, heatmap overlay (the prototype's
`refreshSkinWeightHeatmapView` is the seed), mirror-paint toggle,
numeric readout per clicked vertex. Paint edits are journal commands
(undoable, MCP-visible via `validate_character` deltas — a dedicated
`weights_paint` MCP tool is a Phase-3 candidate, not MVP; agents today
request re-computation with parameters instead).

---

## 9. Fur & body hair

### 9.1 One system, three densities

Fur, body hair, and hairstyles are **one system at different parameter
values** — a region-parameterised coat, not three features:

| Read | Density | Length | Where |
|---|---|---|---|
| Body hair | Low, patchy (region masks do the patchiness) | 5–30 mm | Human-ish bodies, orc forearms/chest |
| Full fur | High, continuous | 20–120 mm | Species coats (fennec, wolf…) |
| Hair styles | Very high, groomed (guide-driven) | 50–600 mm | Scalp styles, manes, topknots, beards |

The species spec's RuffVolume slider is *tissue*, not fur — the coat sits
on top of it. Mane (lion) is a hair-style region set + the ruff region at
high length, not a special mesh (the species spec's "mane shell" becomes:
mane = fur profile; a low-LOD shell mesh remains as the distant-LOD
representation, §9.4).

### 9.2 Candidate systems, compared

| System | Look | Cost | Deforms with body? | Exports to | Verdict |
|---|---|---|---|---|---|
| **Texture-only** (anisotropic fur texture + normal) | Flat at silhouette | ~Free | Yes (it's the skin material) | Everything | Always-on base layer under all other systems |
| **Shell fur** (8–24 offset shells, alpha-noise texture) | Good mid-ground fuzz; silhouette breaks at grazing angles | Low–med GPU | Yes (shells are skinned copies) | GLB/FBX/DAE as geometry+alpha (heavy-ish) | **Viewport preview standard** + low-LOD export |
| **Hair cards** (baked ribbons w/ alpha, flow-textured) | Game-standard; excellent at LOD0–1 | Low GPU, moderate memory | Yes (skinned) | GLB/FBX/DAE/BLEND — the *only* fur game engines accept | **Primary real-time/export representation** |
| **Strand/curve hair** (Blender Hair Curves / Geometry Nodes) | Film-grade; true grooming | Heavy (100k+ strands) | Via surface-deform in Blender | BLEND natively; elsewhere only baked (to cards/shells/mesh tubes) | **Authoring + hero representation**; source of truth for grooms |

### 9.3 Decision

**[D] Primary: strand-authored, card-delivered, shell-previewed.**

- **Authoring truth** lives in Blender: curve hair on the morphed
  surface, groomed by guides (§9.6). Stored in the character's fur
  profile as *parameters + guide data* (§9.5), so a character file stays
  small and re-bakeable.
- **Viewport** shows shell fur (fast, follows sliders live) with a
  "hero preview" job that renders the true strands via the sidecar.
- **Exports** bake strands → cards (default) or shells (low), per format
  table (§9.8). BLEND export carries the real curves.
- Texture-only is the floor: every coat has a fur *texture* under
  everything, so density 0 still reads as skin-with-fur-grain, not
  plastic.

**[DECISION] D4 — confirm strand→cards as primary.** Alternative:
cards-authored directly (faster to ship, weaker grooms, no film-quality
renders). Recommendation stands with strand-authored: our pipeline is
Blender-native anyway, and cards can always be baked *down*.

### 9.4 LOD strategy

| LOD | Representation | Strand/card budget (whole character) | Use |
|---|---|---|---|
| Hero | Strands (renders, BLEND) | 150–400k strands | Stills, close-ups |
| LOD0 | Cards, full groom | 25–60k cards | Games, SL-class uploads, viewport "high" |
| LOD1 | Cards, reduced + merged | 8–15k cards | Games distance, app default export |
| LOD2 | Shells (12) or mane-shell mesh | — | Far distance, thumbnails |
| LOD3 | Texture only | — | Crowds/icons |

Budgets are defaults in the fur profile; the complexity meter (§5.1)
counts fur cost alongside parts (R5).

### 9.5 Fur in the character record

Per **region** (regions = the head/body region map: scalp, muzzle,
cheeks, ruff/neck, ears.inner, torso.front, torso.back, arms, legs, tail,
pelvis, hands/feet):

```json
"fur_region": {
  "density": 0.0-1.0,        // strands per cm², normalised
  "length_m": 0.045, "length_variation": 0.3,
  "curl": 0.0-1.0, "clump": 0.0-1.0, "frizz": 0.0-1.0,
  "colour": { "root": "#3a2c20", "tip": "#8a6f4d", "pattern": "agouti|solid|tipped|banded" },
  "groom": { "direction_map": "…png|null", "guide_set": "guides_id|null" }
}
```

Species defaults ship as fur profiles (`species.wolf.coat` etc.):
fennec = short, dense, pale, huge ear-inner coverage; lion = short body +
mane region long; orc = near-zero body, scalp styles only. Pattern
(agouti banding, tipping) is a shader-level colour function, not geometry.

### 9.6 Grooming UX

- **Region paint mode**: paint density/length/curl maps directly on the
  mesh (brush = texture paint into the region maps, 1k default, 2k scalp).
- **Guide grooming** (hero): comb/brush guides in the Blender sidecar
  session launched from the app ("Open groom in Blender" — the app is
  not going to out-groom Blender; it *manages* grooms as library data).
- Direction/flow is stored as a tangent-space flow map per region;
  cards bake follows it.
- Viewport shows shell approximation updating live while painting;
  strand preview is a render job (§4.3 #19 with `fur: "hero"`).

### 9.7 Performance budgets (defaults, user-tunable)

- Viewport shell fur: ≤ 24 shells × base verts; auto-degrades to
  texture-only below 30 fps sustained.
- Card bake default cap: 60k cards / 2M tris total character; the bake
  job reports its estimate *before* running (MCP `fur_set` returns
  `perf_class` for the same reason).
- Strand hero renders are jobs, never interactive.

### 9.8 Fur × format survival

Full matrix in §11.9. Headline: **strands survive only into BLEND**;
everything else gets cards/shells baked at export, chosen per format
profile. Fur is never silently dropped — the export report states what
was baked and at what LOD.

---

## 10. Materials & textures

### 10.1 Material model

One PBR stack per surface class (skin / fur-card / leather-nose / eye /
teeth / cloth), glTF-compatible core (baseColour, roughness, metalness=0
for organics, normal) + app extensions (SSS tint/thickness for skin &
ears, clearcoat for nose leather/wet look — the Fat Males Dry/Wet pairs
are the reference that wetness is a *material state*, not a new model).

### 10.2 Colour systems

- **Skin**: palette records (orc spec §5.1 is the template: named palette,
  hex range, per-character pick). Melanism (panther) is a palette, per
  the species spec — *coat colour is material, never geometry*.
- **Fur**: root/tip gradient + pattern function (§9.5).
- **Eyes**: iris palette + pupil part variant; heterochromia = per-eye
  material slots.
- **Teeth**: ivory gradient + gum material; `TeethDamage` exposes a
  darker dentine zone (material zone on the arcade, orc spec §4.1).

### 10.3 Layers (decals)

Scars, tattoos, warpaint, tan lines, grime: an ordered layer list per
character (§3.1), each a decal texture + placement (region + UV-space
transform) + opacity. Layers render in the viewport via multi-UV/decal
projection and **bake into the exported textures** at export (targets
don't carry our layer system). Face paint must respect anatomy lines
(brow torus line, orc spec §5.2) — placement is region-anchored, so
layers follow morphs instead of floating.

### 10.4 Painting

Texture paint mode in-viewport (diffuse/roughness/layer masks) at
1k/2k; sidecar Blender session for heavy painting. Painted textures are
library files referenced by the character record.

### 10.5 Resolution / UDIM policy

- App textures: single-UV per mesh, 2k body / 2k head / 1k parts default;
  4k skin optional per character ("texture budget" shown in the cost
  meter).
- **No UDIMs in exports** (SL and most game targets don't take them);
  UDIM allowed only inside BLEND project interchange.
- Texture atlasing: parts atlas together at export when the profile asks
  (SL profile does — §11.3).

---

## 11. Export pipeline

### 11.0 Common rules (all formats)

Every export is a **job** (§2.3) running the same gauntlet:

1. **Resolve** the character (evaluate sliders/parts/fur/materials).
2. **Validate**: §8.5 skinning gates + fold report + part-conflict
   report + licence gate (§13: study-only content in the manifest →
   export is stamped `provenance: study` and *cannot* be stamped clean).
3. **Convert** via the format's path (below).
4. **Verify the artefact**: re-import the produced file (headless) and
   check the contract for that format (skin present, joint count, morph
   count, bind-pose deviation) — the v2 GLB validation, generalised.
   An export that fails verification is reported failed, never silently
   delivered.
5. **Report**: file, size, what survived / what baked / what dropped,
   conformance flag (`clean | extreme | study | broken`), cost totals.

### 11.1 GLB / glTF 2.0 — the native format

- **Path**: in-app (Babylon serializer for viewport-identical output) or
  sidecar Blender — **[D]** sidecar is canonical (one geometry path for
  all formats); the v2 in-app exporter remains as the quick-share path
  and must pass the same verification.
- **Survives**: skin (4 influences), morph targets (the active slider
  stack exported *unbaked* as named targets, on request; default =
  baked shape + zero targets), parts as separate skinned meshes, cards/
  shell fur, PBR + extensions (SSS via `KHR_materials_*` where defined,
  else baked).
- **Validation**: the v2 checks, kept verbatim as the floor — skin
  present on all character meshes, joint count matches rig, inverse
  bind matrices present, JOINTS_0/WEIGHTS_0 complete, bind-pose max
  deviation ≈ 0.

### 11.2 BLEND — native project interchange

- **Path**: sidecar builds a real Blender scene: base + shape keys (one
  per active slider — Blender shape keys *are* our delta instances),
  armature from the canonical rig, parts as objects, **strand fur as
  Hair Curves + Geometry Nodes groom**, material node stacks, layers as
  texture files + decal empties.
- **Survives**: everything, including fur strands and the layered head
  stack (skull/muscle/tissue as separate objects) — BLEND is the only
  lossless round-trip format; "Open in Blender" from the app = this
  export + launch.
- This is also the **authoring interchange**: base/part authoring returns
  through BLEND (§12.3).

### 11.3 DAE (Collada 1.4.1) — incl. the Second Life profile

- **Path**: Blender sidecar (Blender's Collada exporter), post-processed
  by a Python profile step.
- **Generic DAE**: skinned mesh + skeleton + baked shape; morphs do NOT
  survive Collada in any interoperable way → baked, report says so.
  Fur → cards only.
- **SL profile** (the one that matters — Joe's upload route):
  - Rigged-mesh rules: joint names/count within SL's limits (≤110
    joints recognised; our 36-core + extensions fits), ≤4 influences,
    weights normalised; Bento-compatible extra bones (tail/ears/wings)
    mapped to SL's Bento names where equivalents exist, else dropped
    with a report line.
  - **LODs**: four levels generated by decimation profile (High = as-is,
    then ~50% / ~25% / lowest = 300-tri impostor floor per SL's uploader
    economics) or user-supplied; physics mesh = convex-decomposed low
    mesh (sidecar) or lowest-LOD reuse.
  - Materials: ≤8 faces/material slots per mesh (SL limit), textures
    atlased to ≤1024 (profile default) PNG/TGA.
  - Scale/orientation: metres → SL importer conventions handled by the
    profile (Z-up export, joint offsets in SL's expected frame).
  - The export report lists estimated upload cost drivers (tri counts
    per LOD) — the uploader's LI is Linden's maths, but our counts are
  the honest predictor we can give.

### 11.4 FBX

- **Licensing reality, stated plainly**: Autodesk's FBX SDK is
  proprietary; we neither need nor ship it. **Blender's native FBX
  exporter writes binary FBX 7.4** and is the path — proven by the
  library itself (Terris wolf FBX, Leopard Hybrid FBX on disk).
  **[DECISION] D5**: Blender-exporter FBX (recommended) vs licensing/
  integrating the Autodesk SDK (only if a future target rejects
  Blender-flavoured FBX — none known today).
- **Profiles**: `unity` (metre scale, −Z forward conversion at the
  boundary, Humanoid-friendly bone names option), `unreal` (scale,
  bone naming per UE mannequin option), `generic`.
- **Survives**: skin, **morph targets as blend shapes** (FBX carries
  them; export unbaked stack on request), cards fur; strands → baked
  or dropped per profile (report states which).
- Settings locked per profile (apply modifiers, armature-only deform,
  tangent space) — no user-facing FBX flag soup.

### 11.5 OBJ / STL — print & fursuit route

- Unposed, unskinned, watertight-checked meshes; STL in mm at *wearable
  scale* option (the fursuit bases in the library are the reference:
  head bases print at real size) or figurine scale presets.
- Head bases export with the jaw separated + hinge pin holes option
  (the Zaba kits' construction), teeth plates as separate STLs.
- Fur: not applicable (fabric step in the physical build) — export
  report notes the coat region map can be exported as a *pattern guide*
  PNG alongside.

### 11.6 MakeHuman `.target` export

Per `MAKEHUMAN_OMNIVERSAL.md` §6.3: any canonical slider with an hm08
instance exports as a stock `.target` file (ASCII writer, helper-vertex
policy stated in the file header comment + sidecar provenance note so a
generated target can never be mistaken for a CC0 MH asset). Also the
reverse-import (§12.4).

### 11.7 BodySlide `.osd` import/export

- Import: `osdparse.py` already decodes the format (HIMBO 126 sliders) —
  intake route (§12).
- Export: sliders with a Skyrim-base instance can be written back as
  `.osd` diffs + a BodySlide XML slider-set definition, so AnthroForge
  shapes can be *used* in Skyrim. Study-tier provenance rules apply
  (§13): exporting *our own authored/learned-here* sliders is fine;
  re-exporting a decoded HIMBO slider verbatim is redistribution of
  someone else's data and the gate refuses "clean" status for it.

### 11.8 `.afpkg` — character bundle

Zip: `.afchar.json` + every referenced part/slider-instance/material/fur
file + thumbnail renders + a `MANIFEST` with licences. The "send someone
the whole character" format; import = unpack into library with licence
gate report. Share codes (§3.2) stay the lightweight path.

### 11.9 Survival matrix

| Data | GLB | BLEND | DAE (generic) | DAE (SL) | FBX | OBJ/STL | .target |
|---|---|---|---|---|---|---|---|
| Baked shape | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | (is a delta) |
| Unbaked morph stack | ✓ (targets) | ✓ (shape keys) | ✗ baked | ✗ baked | ✓ (blend shapes) | ✗ | single slider |
| Skin + weights | ✓ | ✓ | ✓ | ✓ (≤4 infl) | ✓ | ✗ | ✗ |
| Parts (separate) | ✓ | ✓ | ✓ | ✓ (as links/attachments) | ✓ | merged/separate opt | ✗ |
| Fur strands | ✗ → cards | ✓ curves | ✗ → cards | ✗ → cards | ✗ → cards | ✗ | ✗ |
| Fur cards/shells | ✓ | ✓ | ✓ | ✓ (cost!) | ✓ | ✗ | ✗ |
| Material layers | baked | ✓ live | baked | baked | baked | basic | ✗ |
| Teeth arcade | ✓ (parts) | ✓ | ✓ | ✓ | ✓ | ✓ plates | ✗ |

---

## 12. Import & learning pipeline

The learn-then-delete pipeline (Joe's method) as an app subsystem. All
steps are jobs; all are exposed in the GUI (Intake panel) and over MCP
(§4.3 #22–24).

### 12.1 Intake

- **Formats in**: GLB/glTF, DAE, FBX, BLEND, OBJ, STL, NIF (Skyrim, via
  `nifparse.py`), LLMesh (SL raw, via `sl-asset-decoder`), `.osd` sets,
  `.target` files, MPFB2/MH `.mhm` (via sidecar).
- Every intake **requires a licence declaration** before processing:
  tier (`build` CC0/BY/SA · `study` · `reference`), SPDX where known,
  source note. No declaration → the file sits in `intake/` unprocessed.
  This is the library's existing discipline, enforced by the tool
  instead of by memory.
- Mesh stats + thumbnail render are generated on intake (verts, tris,
  rigged?, materials) — the intake card an agent or Joe approves from.

### 12.2 Learn

Two modes, per the pipeline's proven split:

- **Exact** (same topology as a base — `_0/_1` pairs, BodySlide sets,
  re-poses of our own base): per-vertex deltas directly; zero fit error
  by construction. Output = slider instances + canonical record draft.
- **Fit** (foreign topology): §6.3 retargeting job; output = instances +
  residual report; instances whose p95 exceeds the threshold (default
  0.3 cm body / 0.1 cm head) are filed as `qa_failed` — visible, usable
  only with the badge showing.
- **Delete step**: only after the learned artifacts are written and
  checksum-verified does `intake_finalize` offer source deletion —
  Joe's rule ("learn, then delete") with the safety order made
  mechanical: *learn → verify → file → then, and only then, delete.*
  Study-tier sources are deleted by default at finalize; build-tier
  sources may be kept as library parts instead (authored-part route,
  §12.3) — the finalize dialog states which happened.

### 12.3 Authored-part route

A build-tier model can skip learn/delete and become a **part**: sidecar
normalises it (frame, scale), rigs/inherits weights (§8.4), assigns
sockets + cost, runs §8.5 gates, writes `part.json` (§3.4). Humanoid
donor models (the CC-licensed library hauls) enter here.

### 12.4 MakeHuman mining

`.target`/`.target.gz` import per `MAKEHUMAN_OMNIVERSAL.md` §6.4: parse
→ canonical records with CC0 provenance (bundled) or per-file licence
(community packs — per-file check, the doc's documented caveat). Macro
targets need the de-gridding step (sample grid corners to axis sliders);
detail targets mine directly. Animal-pack targets mine as furry starter
sliders, flagged as the hobbyist-grade sources they are.

### 12.5 Second Life integration points

- **Catalogue**: the grabber's `catalogue.json` (65,503 items / 41,143
  full-perm) imports as a *virtual library shelf*: browsable in the app,
  items marked with their permission masks.
- **Wear-scan queue**: the prioritised full-perm object list
  (`sl-client/WEAR_SCAN_QUEUE.md`, in preparation) drives the Windows
  Firestorm loop (wear → export → detach); DAEs dropped into `intake/`
  are matched back to catalogue entries by name and inherit their
  permission record automatically.
- **Permission rule is structural**: only full-perm (or own-created)
  items may pass intake's licence gate as `build`/`study` sources for
  geometry learning; copy/mod-only items may be catalogued as
  `reference` (thumbnails/notes only, no geometry processing) — the
  no-copybot line, enforced by the gate rather than by vigilance.

### 12.6 Preset/character import

`.afchar.json`, `AF1-` codes (§3.2), `.afpkg` (§11.8), plus foreign
character-ish sources as *reference intakes* (a Skyrim RaceMenu preset
or BodySlide preset file imports as a slider vector mapped through the
canonical vocabulary where names align — partial mapping reported, never
silently dropped).

---

## 13. Library, provenance & licence enforcement

- **Tiers**: `build` (CC0 / CC BY / CC BY-SA / public domain — usable in
  exports stamped clean, attribution strings auto-collected into the
  export report and `.afpkg` MANIFEST), `study` (learned-from or
  permission-granted material — usable inside the app, exports stamped
  `study`), `reference` (view/measure only; geometry never enters a
  slider, part, or export).
- The gate is checked at: intake (§12.1), learn finalize (§12.2),
  part equip into an export-bound character (warning only), and export
  (§11.0 step 2 — the stamp).
- Attribution: every build-tier record carries its attribution string;
  the app generates a `CREDITS.txt` beside any export that used
  attributed content. CC BY-SA content flags share-alike in the report.
- This section implements Joe's standing rule — *learn/measure/derive =
  go; verbatim redistribution = no* — as code paths, not intentions.

---

## 14. Non-functional requirements

- **Startup**: cold start to interactive viewport ≤ 5 s on Joe's machine
  class; Core Service warm.
- **Interaction**: slider drag feedback at viewport frame rate (delta
  application is incremental, §6.2); no modal blocking on jobs.
- **Disk discipline**: the app respects the workspace rule (≥55 GB free
  on the dev VM); library growth is user-visible (Settings shows library
  size by section); caches (correspondences, bakes, thumbnails) are
  capped + purgeable, and are never the only copy of anything.
- **Undo/journal** (§5.7) covers every mutation; a crash loses at most
  the in-flight command.
- **Accessibility of data**: everything exportable/deletable by the user
  as files; uninstalling the app leaves the library intact.
- **Logging**: local job logs only; nothing leaves the machine.

---

## 15. Roadmap

Effort classes: **S** = weekend-scale, **M** = 2–4 weeks of focused
build, **L** = a quarter-scale programme. Classes assume agent-assisted
development at the pace this project has actually moved (Nov 12 alone
produced the v2 app fixes, the fit POC, three specs and two pipelines).

### Phase 0 — Proofs already on disk (done / in flight)

- v2 web app: real skinning + validated GLB export ✔
- Learn-then-delete POC + foreign-fit POC (0.05/0.28 cm) ✔
- Omniversal architecture + canonical record ✔ (this doc set)
- Species head spec, orc preset spec, teeth library ✔
- Base head v2 (layered) — in build; SL catalogue + grabber ✔

### Phase 1 — MVP (M)

**The smallest app that is an app.** Exactly this, nothing more:

1. Tauri shell + Core Service skeleton; the v2 frontend split into
   modules behind the `host.ts` shim; library folder + SQLite index.
2. Character record load/save + share code (encode/decode + import UI).
3. Slider engine on **one base pair**: hm08 (dev base) + the Fat Males
   belly first-proof slider, end-to-end per `MAKEHUMAN_OMNIVERSAL.md`
   §8 (its success criteria are the MVP's acceptance test), then the
   HIMBO/Fat Males body set as instances on hm08.
4. MCP server: stdio transport, tools #1–10, #18–21, #25, #27 (create/
   load/save/share, sliders, presets, library search, render, export
   GLB, jobs, status, validate) — agents can build a body day one.
5. GLB export with the §11.1 validation gauntlet.
6. Viewport: slider panels + preset gallery (species head presets
   applied to the head region of the dev base as far as density allows)
   + studio/in-world lighting toggle.

*Acceptance*: Joe (or an agent via MCP) creates a character, applies the
belly slider + a species preset, exports a GLB that passes verification,
and re-imports it by share code on a clean library.

### Phase 2 — The real bases + parts (L)

1. Neutral body base authored + weighted (§8.3); base head v2 integrated
   with the layered stack live (§7); head instances for the 25 sliders;
   species presets complete (head + body).
2. Parts system: sockets, part browser, equip/remove with conflicts +
   cost (R4/R5), teeth arcade (§6.4) with diet morphs + orc tusk
   coupling; orc preset family ships as the demo content.
3. Exports: BLEND + FBX + DAE generic (sidecar paths, §11).
4. Weight-paint mode; anatomy inspector.
5. Retargeting service productionised (base-pair cache; himbo↔mh08,
   mh08↔af pairs).

### Phase 3 — Fur, SL, polish (L)

1. Fur system complete (§9): profiles, region painting, shell viewport,
   card baking, hero strand renders; species coat defaults.
2. DAE SL profile + wear-scan intake loop (§11.3, §12.5).
3. `.osd` export, `.target` export, `.afpkg`.
4. Direct manipulation (§5.4), blend triangles fully wired (§5.3),
   free-attach props (R9).
5. HTTP MCP transport + LAN toggle; prompts/resources polish.

### Phase 4 — v1.0 and beyond

- Library packs: community slider/part packs as importable files;
  in-app gallery *of local files* (no server) — a server-backed public
  gallery is a separate product decision, not a feature.
- Expression set expansion; quadruped body plan (RIG_CONTRACT rigs are
  the reference); body layered anatomy (muscle layer for bodies,
  SF6-style per-muscle sliders — R12's echo).
- macOS build; installer signing.

---

## 16. Risks, open questions & DECISION list

### 16.1 Risks

| Risk | Severity | Mitigation in this blueprint |
|---|---|---|
| **hm08 head density** can't carry muzzle sliders (omniversal doc's named weak link) | Medium | MH head instances ship with honest QA badges; our own head is the primary — MH is a partner, not the foundation. |
| **Extreme-delta folding** at bara/orc ranges | Medium | Safe ranges, fold gates, conformance flags (R4) — never silent breakage. |
| **Blender version drift** breaks sidecar scripts | Medium | Pinned tested version (5.2); sidecar scripts version-checked at startup (§2.4, D2). |
| **Scope gravity** — the creator-forever trap (12 games' worth of features) | **High** | MVP is deliberately body-only-on-a-dev-base (§15); every later feature is phased and named. |
| **Study-tier data leaking into "clean" exports** | High (trust/legal) | Provenance is a data-model field + export gate (§13), not a convention. |
| **WebView2 variance** on older Windows | Low | Electron fallback preserved by the `host.ts` shim rule (§2.2). |
| **Fit dead zones** (flank/genital) silently corrupting transferred sliders | Medium | Residual masks are part of the instance format (§6.3); dead zones masked, never transferred. |
| **Fur scope explosion** (grooming is a discipline, not a feature) | Medium | App manages grooms; deep grooming delegates to Blender (§9.6). Card bake caps enforced (§9.7). |

### 16.2 DECISION list for Joe

| # | Decision | Options | Recommendation |
|---|---|---|---|
| D1 | App shell | Tauri 2 / Electron | **Tauri 2** (small, WebView2 = Chromium we already target) |
| D2 | Blender supply | Bundle pinned portable (~1 GB) / detect external | **Detect + guided download** |
| D3 | MCP HTTP exposure | Loopback-only / loopback + LAN toggle w/ token | **Loopback + toggle** (family bots are remote by design) |
| D4 | Fur primary | Strand-authored→cards / cards-authored | **Strand-authored** (Blender-native pipeline; cards bake down) |
| D5 | FBX path | Blender exporter / Autodesk SDK | **Blender exporter** (SDK unnecessary + proprietary) |
| D6 | Study-tier sliders in *shipped default library* | Include flagged / internal-only until re-derived clean | **Internal-only by default**; a slider graduates to the shipped library only when re-authored from build-tier sources. (Blueprint assumes this; flag if Joe wants flagged-inclusion instead.) |
| D7 | MVP base | hm08 dev base first (fast, CC0) / wait for our neutral body | **hm08 first** — the engine proves out in Phase 1 while base authoring runs parallel in Phase 2. |
| D8 | Public gallery/server someday | Never / local-only packs / hosted gallery | **Local packs only** for v1 scope; revisit after v1.0. |

### 16.3 Open questions (not blocking the MVP)

- Brow study results may add head sliders (BrowContinuity/BrowShelf) —
  canonical format absorbs them without schema change (§7.4).
- Body layered anatomy: how far does the muscle layer go for bodies in
  v1 — head-only at first (blueprint's assumption) or full-body from
  Phase 2? Cost driver; Joe's call when Phase 2 is scoped.
- Titan family presets: authored as presets (Phase 2 content) — each
  family member's preset needs their slider vector signed off, same as
  the orc spec's honesty-box process.
- Print route: fursuit-scale STL (§11.5) assumes the Zaba-kit
  construction (separate jaw, hinge) — confirm against Joe's printer/
  maker plans when Phase 3 scopes it.

---

*End of blueprint. Build order is §15; the first concrete task is the
Phase-1 MVP item 3 — the Fat Males belly proof — whose acceptance
criteria already exist in `MAKEHUMAN_OMNIVERSAL.md` §8.*
