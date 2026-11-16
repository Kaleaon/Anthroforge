# GLB QA Gauntlet — Library Sweep Report

**Harness:** [`validate_glb.py`](validate_glb.py) (stdlib + numpy, zero-install —
parses the GLB container, JSON chunk and accessors directly; trimesh/pygltflib
are not installed on this VM and were not needed).
**Run:** Nov 12, 2026 · **Per-file JSON:** [`results/`](results/) (one `.qa.json`
per GLB + merged `_summary.json`).
**Re-run:** `python3 validate_glb.py <dir> --out results`

## Coverage

| Source tree | GLBs |
|---|---|
| `~/workspace/bodies-3d/` | 56 |
| `~/workspace/stick-figure-avatar/` | 10 |
| `~/workspace/anthroforge-v2/` | 2 |
| **Total found / run** | **68 / 68** |

(The brief capped the sweep at ~60; all 68 found were run — total wall time
~45 s, so the harness is cheap enough to gate every export.)

## Results by check class

| Check | OK | Warn | Fail | n/a | Notes |
|---|---|---|---|---|---|
| Parses cleanly | 68 | — | 0 | — | Every GLB in the library is structurally sound. |
| Skin present & weighted | 34 | 32 | 2 | — | 36 files declare a skin; 32 files are legitimately static (scans, sculpts, parts). |
| 36-bone contract | 0 | 0 | 36 | 32 | **No library file matches our rig** — see below. |
| Morph targets | 28 | 40 | — | — | 28 files carry ≥1 morph target; best: 13 (Kaleaon v3 family). |
| Textures self-contained | 68 | — | 0 | — | 35 files have textures; **all embedded, zero external URIs** anywhere. |
| Geometry (degenerate tris / NaN) | 66 | — | 2 | — | Only 13 degenerate triangles in the whole library; **zero NaN vertices in 68 files**. |
| Scale sanity (0.1–10 m) | 56 | 12 | — | — | 12 files are unit-suspect (cm/mm exports) or tiny parts. |

### The contract result is expected — and it defines the gate

Every skinned library asset is a *foreign rig* (Blender/Rigify-style or
game rigs of 21–742 joints). The best partial match to our 36 names is
3/36 (`stick_figure_avatar.glb`, `realistic_avatar.glb` — generic names
like Root/Head coincide). **The 36-bone contract can only bind
AnthroForge's own exports** — which is exactly what v2's exporter already
validates in-browser. For library imports, contract mismatch must stay
informational, or we'd reject 100% of the library.

## Gold references (best-formed files)

| File | Why it's gold |
|---|---|
| `stick-figure-avatar/furry-lineup/threejs-lineup/models/border_collie.glb` | The complete package at sane weight: 66 joints, all primitives weighted, IBM present, **12 morph targets**, 7 embedded textures, 1 animation, 0 degenerate, 8.8k verts. The shape our exports should have. |
| `stick-figure-avatar/furry-lineup/threejs-lineup/models/persipia.glb` | Same profile (65 joints, 9 morphs, 7 embedded textures, animation, 0 degenerate). Caveat: 8.57 m extent — an outlier node/prop inflates the bbox; worth a look before citing its scale. |
| `bodies-3d/kaleaon-rigged3/kaleaon_rigged3.glb` (+ `kaleaon-sculpt`) | Richest rigs we own: 89 joints, 13 morph targets, 6 embedded textures, plausible 2.33 m extent, 0 degenerate. Heavy (1.17 M verts) — a quality reference, not a size reference. |
| `stick-figure-avatar/photoreal/photoreal_avatar.glb` | Only fully-textured file at true human scale (1.75 m): 53 joints (MPFB rig), 11 embedded textures, 3 animations, clean geometry. No morphs. |

## Worst offenders

| File | Problem |
|---|---|
| `bodies-3d/parts-library/sketchfab/bunny-azuliezeiro/bunny.glb` and `…/fox-fem-full-rig-azuliezeiro/fox_fem._full_rig.glb` | **Vestigial skins**: a skin block with a single joint (`metarig_rootJoint`) and *zero* weighted primitives — the geometry is unskinned despite the "full rig" billing. The only skin-class failures in the library. |
| `bodies-3d/…/toriel_head_rig.glb` | Extent **30,571 m** — exported in millimetres. Unusable without a unit fix. |
| `kitty_base.glb`, `kitty_base_v1.0.glb` | Extent 254.6 m — centimetre exports; also unskinned. |
| `cat_base.glb` / `anthro_female_cat_base.glb` (28.7 m), `leopard_animation_run.glb` (81.3 m), `round-rim_glasses.glb` (185.3 m), `MascularMale.glb` (22.0 m), `lowpoly_base_male_protogen.glb` (22.2 m), `otter-chan.glb` (13.5 m), `panda_girl…glb` (11.7 m) | Same unit disease, lesser degree. |
| `bodies-3d/pyn-formgraft/pyn_formgraft.glb` (9) and `bodies-3d/pyn-realism/pyn_realism.glb` (4) | The library's only degenerate triangles. Trivial counts — a cleanup pass, not a rejection. |
| Four files literally named `model.glb` (Sketchfab exports) | Up to **1.26 M triangles**, unskinned, no morphs, anonymous names — the least reusable assets we hold. |
| `eyeball.glb` (0.021 m) | Flagged "too small" — correctly: it's a *part*, not a body. The scale check needs the asset's role as context, which is why scale is a warn, not a block. |

## Block vs warn — recommendation for the app's export gate

**BLOCK export (hard fail):**
1. **Parse failure / accessor overrun** — the file is corrupt, full stop.
2. **NaN or Inf vertices** — poison for every downstream consumer.
3. **Skin declared but no inverse bind matrices** — a rig that cannot pose.
4. **Skin declared but zero weighted primitives** — the bunny/fox failure mode: advertises a rig that isn't there. (Block when the character is exported *as rigged*; n/a for a deliberately static export.)
5. **External texture URIs** — breaks the self-contained file (and SL upload). Textures must embed. (Library currently: 0 violations.)
6. **Contract mismatch on AnthroForge's OWN exports** — must be exactly 36/36 named joints. Never apply this block to imports.
7. **Degenerate triangles above 0.1% of total tris** — indicates a broken bake. (Nothing in the library comes close.)

**WARN (export proceeds, user sees it):**
1. **No skin** — legitimate for scans, sculpts, static parts.
2. **No morph targets** — most of the library; only warn when the character record actually uses sliders.
3. **Scale outside 0.1–10 m** — almost always a unit export (cm ×100, mm ×1000); offer the one-click rescale instead of blocking. Parts (an eyeball at 2 cm) must be able to waive this.
4. **Degenerate triangles > 0 but ≤ 0.1%** — log the count (today's worst: 9).
5. **Joint count ≠ 36 on imported/reference assets** — informational only.
6. **Size budget** — verts/tris or file MB over the target platform's budget (e.g. the 1.17 M-vert Kaleaon rigs) warns; the platform profile decides the number.

## Harness limits (stated honestly)

- Bounding box applies node world transforms, using the first node that
  references each mesh; a mesh instanced at two scales reports the first.
- Sparse accessors are reported as accessor errors (none exist in this
  library); Draco-compressed GLBs would need a decoder (none exist here —
  `extensionsUsed` was checked on all 68).
- JOINTS_0/WEIGHTS_0 presence is checked per primitive; weight *quality*
  (sums ≈ 1, ≤4 influences) is a v2-harness check, not this one.
