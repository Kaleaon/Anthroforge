# GLB QA Gauntlet v2 — Extended Model-Craft Checks

**Agent:** B3, model-craft wave (Nov 12, 2026) · **Deliverables:** this report,
[`validate_glb2.py`](validate_glb2.py), [`results/`](results/) (68 × `.qa2.json`
+ merged `_summary2.json` + the exact `_filelist.txt` swept).
**Relation to v1:** v1 ([`../../qa-gauntlet/validate_glb.py`](../../qa-gauntlet/validate_glb.py))
checks parse / skin presence / 36-bone contract / morphs / scale / degenerate
tris / NaN and remains the export gate, untouched. v2 reuses v1's GLB parser
and adds the checks a modelling pro runs before calling an asset *good*.
Same library as the v1 sweep: the identical 68 GLBs (56 bodies-3d +
10 stick-figure-avatar + 2 anthroforge-v2; the 3 fur-card GLBs added to the
results folder later are not part of the 68).

**Re-run:** `python3 validate_glb2.py results/_filelist.txt --list --out results`
(resume-safe: existing per-file results are skipped).

---

## What v2 checks

| Class | Checks |
|---|---|
| **Topology** | Non-manifold edges (shared by >2 faces), boundary/open edges, duplicate faces, unused vertices, split-vertex ratio (same position, distinct index — the hard-split/UV-island footprint) |
| **Winding / normals** | Directed-edge conflicts (adjacent faces traversing a shared edge in the *same* direction), vertex-normal vs face-normal agreement (inverted-face fraction), signed-volume sign on closed meshes |
| **UV** | Textured primitive with no TEXCOORD_0, UV out-of-range fraction (tiling), UV-overlap estimate (area-conservation: summed tri UV area vs covered UV area), UV disagreement on shared edges |
| **Texel density** | Texels/metre per textured primitive (from embedded PNG/JPEG header dims × UV area ÷ world area); consistency = coefficient of variation across a file's primitives |
| **Materials** | Defined-but-unused materials, primitives with no material, duplicate material names |
| **Skin weights** | Influence-count distribution, zero-total-weight vertices on skinned primitives, unnormalised sums (\|Σ−1\|>0.01), joint indices outside the skin's joint list, skin joints no vertex uses (orphan groups), WEIGHTS_1 without JOINTS_1 |
| **Animation** | Channel targets exist, sampler time keys monotonic, NaN/Inf in outputs, zero-duration samplers, duplicate (node, path) channels |

### Calibration honesty (three metric designs failed before one worked)

The UV-overlap number is the third design, and the failures are recorded in
the script so nobody re-tries them: (1) fixed samples-per-triangle occupancy
under-fills large triangles and read **0.7 fake "overlap" on clean atlases**
(Poisson 1−e^−λ, λ≈0.5); (2) exact per-triangle cell-centre rasterisation is
correct but its Python loop took >5 min on a 1.2M-vert sculpt. The shipped
method (midpoint-subdivide to ≤4 grid cells per sub-triangle, then one
vectorised 9-point lattice, λ≥6) reads **0.00–0.10 on the known-clean
procedural base head** — treat ≤0.10 as the noise floor. Two more real bugs
were caught by calibration, both instructive: face normals must be compared
in *local* space (world face normals vs local vertex normals garbage-dots
any rotated mesh), and `np.unique(axis=0)` is a trap at 1M+ verts (replaced
by a quantised hash count for split vertices).

---

## Results by class (68 files)

| Check class | OK | Warn | Fail | n/a | Headline |
|---|---|---|---|---|---|
| Topology | 8 | 54 | 6 | — | 2,599 non-manifold edges in 6 files; boundary edges everywhere (58 files) — normal for part/shell models |
| Winding / normals | 43 | 9 | 16 | — | **7 models are systematically inside-out** (below) |
| UV | 30 | 38 | 0 | — | Zero textured-but-UV-less primitives; overlap is mostly deliberate mirroring |
| Texel density | 12 | 21 | — | 35 | Measurable on 33 files; 21 have CV > 0.5 |
| Materials | 68 | 0 | 0 | — | **Clean sweep**: 398 materials defined, 0 unused, 0 unmaterialed primitives, 1 duplicate name |
| Skin weights | 8 | 26 | 0 | 34 | Zero unnormalised sums and zero out-of-range joints library-wide; orphan joints and one zero-weight disaster (below) |
| Animation | 20 | 4 | 0 | 44 | 24 files, 6,449 channels: **no bad targets, no NaN, no non-monotonic samplers anywhere** |

Zero unused vertices in the entire library, too — exporters are not leaving
orphan position data behind.

## The findings that matter

### 1. Whole models wound inside-out, masked by double-sided materials
Vertex normals and triangle winding systematically disagree in:
`cat_base.glb` / `anthro_female_cat_base.glb` (**86%** of faces inverted —
the same AKM cat in two copies), the AKM border collie in all three of its
library copies (**69%**; probed directly: its largest primitive has 100% of
face normals pointing inward, and every one of its materials is
`doubleSided: true`, which is why it renders fine), `toriel_head_rig.glb`
(63%), `otter-chan.glb` (60%), `persipia.glb` (23%). These files break
backface culling, normal-from-winding tooling, and any engine that trusts
winding over the NORMAL attribute. **Fix is one click in Blender (recalculate
outside / flip winding), but only v2 sees it — v1 passes all of them.**

Separately, closed meshes with negative signed volume: our own
**`neutral_base_head.glb` v1** (one mesh wound consistently inward — normals
and winding agree with each other, both point in), the Kaleaon v3 family
(5 sub-meshes each — eyes/teeth-class shells authored independently), and
`pyn_realism.glb` (2).

### 2. The BVH rig file is the library's worst citizen
`bvh_rig_models_update_fox_rabbit_and_cat.glb` fails or warns on nearly
every axis: **80,934 of 152,886 skinned vertices (53%) carry zero total
weight**, 2,438 non-manifold edges, **2,024 duplicate faces**, 6,072 winding
conflicts, UVs 100% out of range, 4 zero-duration samplers. Whatever pipeline
converted it (BVH→GLB) bound only half the geometry. Do not build on it
without a rebind.

### 3. Orphan joints: rigs carrying skeletons nobody uses
948 skin joints across the library are weighted by no vertex.
`panda_girl_-_stylizedfree_blender_rig.glb` carries **572 unused of 742**
(the full Rigify metarig exported wholesale); styloo's `cat.glb` carries
**237 unused of 283** — a static cat wearing an 84%-dead skeleton;
`toriel_head_rig.glb` 24 of 46. Harmless at runtime, pure bloat and a
contract-matching hazard. The gold files are nearly clean by contrast
(collie/persipia/photoreal: 1 orphan each).

### 4. Texel density is inconsistent almost everywhere it exists
21 of 33 measurable files have texel-density CV > 0.5 across their
primitives — i.e. face textures resolve several times finer or coarser than
body textures on the same model. Worst: `persipia.glb` CV 1.65,
`otter-chan.glb` 1.21, `Pyn_v3.glb` 1.04. The Kaleaon family averages
~12–16k texels/m per primitive (4K textures on small parts) against the
collie's 650 — two orders of magnitude of house style difference, worth
knowing before mixing parts across models. (Per-primitive means are
unweighted; CV is the comparable number.)

### 5. UV overlap is real, large, and mostly *intended*
39 files double-claim >20% of their UV area (area-weighted);
`kaleaon_body.glb`/`kaleaon_erect.glb` 0.98, the Pyn line 0.87–0.97,
`stick_figure_avatar.glb` 0.95. This is the mirrored-halves atlas strategy
plus stacked sculpt shells: legitimate, but it means effective texture
resolution is shared, and it will silently halve the detail of any
asymmetric marking painted in texture space — the markings system already
assumes mirror-symmetric base UVs, so this confirms that assumption is
load-bearing. The check to actually fear — a textured primitive with **no
UVs at all — occurs zero times**.

### 6. Small print
- **Duplicate faces** also in `kaleaon_realism.glb` (73) and `pyn_realism.glb`
  (62) — our own realism passes, worth a weld/clean before further work.
- **Non-manifold edges** also in `kaleaon_realism.glb` (77), `pyn_realism.glb`
  (66), `fox_fem._full_rig.glb` (16), and 1 each in two julianemilioqwe
  `model.glb` files.
- **Zero-duration animation samplers**: `mesh_9_furry.glb` 329,
  `generic_productfemale_dog_furry.glb` 104 — these are single-key static
  poses shipped as "animations", not corruption; they inflate channel
  counts (mesh_9 alone is a third of the library's) without moving anything.
- **Split-vertex ratios** peak at 0.83 (Kaleaon v3) vs ~0.0–0.2 for
  hand-authored game models — the sculpt-lineage fingerprint. In-place UV
  tears (UV disagreement across a *shared* index edge) occur **zero times**
  library-wide: in indexed geometry, seams live at splits, and this library's
  splits are honest.
- **Boundary edges** total 7.15M, but 6.4M of them are the Kaleaon sculpt
  family's open shells; the median part-model has a few thousand (open
  mouths, eye sockets, shell garments). Read per-file, not in aggregate.

## Recommended gate changes (for AnthroForge's *own* exports)

Graduate to **fail** in the export gate: non-manifold edges > 0 ·
inverted-face fraction > 5% or negative-volume closed mesh ·
zero-weight vertices on a rigged export · unnormalised weight sums ·
joint index out of range · textured primitive without UVs · NaN/non-monotonic
animation data. (The library proves all are achievable: files exist that pass
every one.) Keep **advisory**: boundary edges, UV overlap (intent-dependent),
texel CV, orphan joints, split ratio, zero-duration samplers.

## Method / run notes

- 64 files ran the full check set. **4 files ran `--lite`** (UV-overlap and
  seam passes skipped): `kaleaon_sacdrape`, `kaleaon_sculpt`,
  `kaleaon_v3_r2`, `kaleaon_v3_r3` — the 75–105 MB sculpts were OOM-killed
  repeatedly in full mode because the sweep ran while the VM was saturated
  by the ~40-agent craft wave (load avg >30, ~1 GB RAM free). Their per-file
  JSONs carry `"lite": true`. Everything else in those files' reports
  (topology, winding, weights, texel) is full-strength — and their sibling
  `kaleaon_rigged3.glb` completed the full set, so the family's UV behaviour
  is not unmeasured.
- Wall clock was dominated by machine contention, not the checks: small
  files validate in 1–4 s on an idle core; the v1 sweep of the same library
  took 45 s total. Budget v2 at ~2–4× v1 on an idle machine.
- Duplicate *content* exists under multiple paths (the AKM collie ×3,
  persipia ×2, several Pyn bodies) — v2 reports per path, matching v1;
  identical twins produce identical numbers, which doubled as a determinism
  check on the harness.
