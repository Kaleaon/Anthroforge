# AnthroForge

**A parametric avatar creator for anthropomorphic and fantasy characters** — a real
installable app (Windows first), not a web page. A character is *created*, not
loaded: a base body/head + a vector of sliders + a manifest of swappable rigged
parts + a material stack, serialised into a small portable **character record**
(`.afchar.json`) that doubles as a share code (`AF1-…`).

This repository is the project's full working tree as of **Nov 16, 2026**:
the design/build lab (`anthroforge-v2/`) and the application core
(`anthroforge-app/`). The one-page map of everything is
[`anthroforge-v2/HANDBOOK.md`](anthroforge-v2/HANDBOOK.md); the master build
spec is [`anthroforge-v2/APP_BLUEPRINT.md`](anthroforge-v2/APP_BLUEPRINT.md).

## Four load-bearing ideas

1. **Learn, don't guess.** Slider deformations are *measured* from real models
   by a learn-then-delete pipeline — fit a base over a target, extract the
   per-vertex deformation, delete the target, keep the data. Exact
   same-topology pairs give exact deltas; foreign topology ships with a
   measured residual (median 0.05 cm), never a fake "100%".
2. **Omniversal sliders.** One slider vocabulary across every base. A slider
   is a *semantic record* (name, region mask, endpoint anchor in metres,
   range, provenance); each base mesh holds a generated **instance** of it
   with its own QA numbers. Composition order is fixed: base → muscle →
   tissue (sampled over the muscled surface) → gravity, with definition
   attenuation curves and a fold gate run on the shipped, quantised numbers.
3. **Layered anatomy.** Heads (and later bodies) are built skull → muscles →
   tissue. A brow ridge is bone, a scowl is muscle, padding is tissue — a
   surface merely wrapped over the form reads too skeletal.
4. **Swappable parts.** Body parts attach/detach at named sockets on a shared
   skeleton (Spore / Second Life model). Rigged parts are preferred; rigid
   bone-attached is the fallback tier. Parts carry conflict metadata and a
   visible complexity cost from a shared pool.

Supporting stances: stylisation (realistic ↔ toony) is its own axis over the
species presets; agents are first-class users — the creator surface is exposed
over an **MCP connector**; everything is offline-first, files-are-the-truth,
and every library asset carries a licence tier (build / study / reference)
that the pipeline enforces.

## Repository map

| Path | What it is |
|---|---|
| `anthroforge-app/` | The application: Python core service (character records, share codes, slider registry, geometry/build service, fold gate, GLB writer), the canonical library (slider records, per-base instance packs, presets), the MCP server package, a Telegram Mini App front end, and the pytest suite (**114 tests passing**). |
| `anthroforge-v2/` | The design & build lab: handbook and design docs, the standalone `anthroforge_3d_pro_v2.html` prototype (36-bone rigged builder with validated GLB export), base/body/head construction, character builds, and the study waves (fur-craft A1–A20, model-craft B1–B20) whose findings the app encodes. |
| `NOT_INCLUDED.md` | Redistribution audit: third-party study material deliberately **not** shipped in this repo, and why. |

## The slider engine (anthroforge-app)

- **110 slider records** in `anthroforge-app/library/sliders/` — 73 body +
  **37 head records** (the full species-head vocabulary: muzzle, cranium,
  brow, ears, eyes, jaw), each with anchors, ranges and provenance.
- **2 bases**: hm08 and its masculine variant, with canonical float64
  instance packs (the fold gate runs on 0.1 mm-quantised targets — rounding
  flips near-boundary faces, so packs ship unrounded).
- **15+ character presets** as `.afchar.json` + `AF1-` share codes,
  round-tripping bit-exact: orc strongman/bodybuilder, Pyn, Sen (+ muscle
  bear), Jorge, Brand, and the batch-2 Titans (Alpha, Beta, Gamma, Delta,
  Sage ×2, Thatch, Hollis).
- **MCP**: `validate_character` and `export_run` are live; the remaining
  specced tools are loud stubs, never silent no-ops.

## Bases and character builds (anthroforge-v2)

- **Bodies** — composed, fold-gate-passing, QA-gauntlet-clean GLBs:
  Pyn (fennec, 45.7 L lean build), Jorge (St. Bernard, 94.9 L at base scale),
  Brand (badger, 143.4 L at 183 cm), Sen (bear, stages 1+2 with baked fur
  cards) — `anthroforge-v2/characters/<name>/`, each with a build doc whose
  numbers are measured, not asserted.
- **Base head v5** — `anthroforge-v2/base-head-v5/`: layered skull → muscle →
  tissue head with a real **lip-line loop cage** (the v4 lip crease became an
  actual mouth opening with margin rows), split upper/lower teeth arcades on
  the jaw pivot, **zero teeth/margin overlaps at −10°/−20°/−30°**, and the
  surface-true MuzzleWidth measure (0.2412, identical to v4).
- **Species heads** — Pyn, Jorge and Brand heads built on the v4 base from
  craniometry-derived species vectors, ruler-verified station by station;
  Sen's head rebuilt after the batch caught a left/right mirroring bug in
  the original build machinery (his EyeSpacing had converged his eyes
  instead of spreading them — fixed, quantified, documented in
  `characters/sen/SEN_BUILD.md` §10).
- **Hyper ranges** — `anthroforge-v2/hyper/`: belly/tissue sliders authored
  past 1.0 into a measured hyper segment (to 2×) with per-segment contact
  re-solves and zero folds at the shipped ceilings.
- **Kaleaon anatomy** — `anthroforge-v2/parts-lab/kaleaon-anatomy/`:
  swappable part set built to the parts standard (28 sockets, 128-point
  complexity pool), gauntlet-clean.

## Craft findings worth knowing

- **Fur**: Geometry Nodes is the groom-authoring route; the coat is a
  two-layer system whose split is *per-species data* (lion undercoat 0,
  wolf/bear/St. Bernard 0.85–1.0); Marschner hair shading can't ship on
  cards — production cards use anisotropic GGX + Charlie sheen.
- **Models**: deformation-aware decimation with prune-to-4/renormalise is
  mandatory; posed integrity is set by LOD0 skeleton/topology, not density.
- **Soft dynamics**: stiffness must be angular; settle time is the honest
  softness readout (1.60 s soft vs 0.43 s firm).

## Third-party material & credits

Everything in this repo is our own work **except** the following, which ship
under their own terms and are credited here and in `NOT_INCLUDED.md`:

- The base-head lineage (v3 onward) carries parts derived from the
  **GalileoGB cougar** (CC-BY) — tissue surface, ears, mouth/teeth slab,
  tongue — neutralised and rebuilt into our layered head. Attribution and
  the full source list live in `anthroforge-v2/base-head-v3/BUILD_NOTES.md`.
- `model-craft/b19-scans/lion_head_clean.glb` is a cleaned **Poly Haven**
  lion-head scan (CC0).
- `anthroforge-v2/lib/` vendors **Babylon.js** (Apache-2.0) and the
  **Tailwind** browser build (MIT) so the standalone HTML prototype runs
  offline.
- Base bodies derive from **MakeHuman / MPFB** (CC0) targets; slider fields
  were *learned* from study models (HIMBO vocabulary, Fat Males) by the
  learn-then-delete pipeline — the study models themselves are **not**
  included anywhere in this repo. See `NOT_INCLUDED.md` for the full audit.

## Status

Active development. Open decisions and known debits are tracked in the
HANDBOOK (§5) and in each build doc — nothing in this tree is presented as
more finished than its doc says it is.
