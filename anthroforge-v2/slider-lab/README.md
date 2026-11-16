# slider-lab — working code for SLIDER_ENGINEERING.md

Every method in `../SLIDER_ENGINEERING.md` has a runnable implementation
here. Python needs only numpy + scipy (both on this VM); the JS runtime
is dependency-free Node. All commands below were actually run on
Nov 12, 2026, and the outputs quoted are the real outputs.

## Files

| File | Manual sections | What it does |
|---|---|---|
| `mask_tools.py` | §B.2, §B.6, §C.5 | Mesh IO (learned-npz + pure-python GLB reader), geodesic distances (multi-source Dijkstra), falloff masks, partition-of-unity splits (L/R, bands), Laplacian mask smoothing, fold/volume QA |
| `author_slider.py` | §A.6, §B, §E.1 | Spec-driven procedural authoring → canonical record + npz/JSON instances + QA report. Ships `head.brow.projection` |
| `decompose.py` | §A.7, §E.2 | Splits one decoded .osd slider (HIMBO BodyChubby) into 11 sub-sliders with exactness proof |
| `apply_sliders.js` | §C.1, §C.3, §D | Runtime: bind-pose-aware combined-delta application, area-weighted normal recompute, record-range + fold-guard clamping with warnings; Babylon adapter (`applyToBabylonMesh`) + Node self-test |
| `output/` | §E | Everything the runs produced: canonical records, instances, QA JSON, the JS fixture |

## Run it

```bash
cd ~/workspace/anthroforge-v2/slider-lab

python3 mask_tools.py demo
python3 author_slider.py brow-projection
python3 decompose.py            # optional arg: another .osd slider name, e.g. 'Belly'
node apply_sliders.js --selftest output/fixture_head.json
```

## Actual outputs (Nov 12, 2026)

**mask_tools demo** (brow mask on the neutral base head + partition checks):

```
head verts: 6100  brow seeds: 368
brow mask: {'verts_full': 516, 'verts_partial': 900, 'verts_any': 1416, 'weight_sum': 904.99}
lr partition max |sum-1|: 0.0
band partition max |sum-1|: 0.0
```

**author_slider — BrowProjection** (new slider, brow-study §5.1 anchors):

```
authored: head.brow.projection on anthroforge_head_v1
  L = 1.0  mask: {'verts_full': 516, 'verts_partial': 900, 'verts_any': 1416}
  anchors: [1295, 1309] mask weights: [1.0, 1.0]  displacement at +1 (L): [0.06, 0.06]
  v=-0.50 folds(region/total)=0/0 max|d|=0.0300 L dV=-0.00148
  v=+0.50 folds(region/total)=0/0 max|d|=0.0300 L dV=+0.00148
  v=+1.00 folds(region/total)=0/0 max|d|=0.0600 L dV=+0.00297
  v=+1.25 folds(region/total)=0/0 max|d|=0.0750 L dV=+0.00371
  v=+1.50 folds(region/total)=110/110 max|d|=0.0900 L dV=+0.00445
  safe_max = 1.25
```

Fold-free through +1.25; 110 folds at the +1.5 gorilla anchor → the
record ships range max 1.5 with `safe_max: 1.25`, and the runtime
enforces it (below).

**decompose — HIMBO BodyChubby → 11 sliders** (parent: 9,229 diff verts,
max 3.998 Skyrim units — matches the original decode exactly):

```
piece body.chubby.left         verts= 4929  mean=0.863 u  max=3.998 u (0.057 m)
piece body.chubby.torso        verts= 3325  mean=1.038 u  max=3.998 u (0.057 m)
... (9 more pieces)
exactness: max |sum(6 crosses) - parent| = 4.441e-16
exactness: max |L+R - parent|           = 4.441e-16
parent at +1: folds total=14 in-region=14      <- shipped slider, own base; recorded as base QA
```

**apply_sliders.js self-test** (cross-checks the Python QA in the
viewport runtime):

```
value +1.0: anchor displacement = 0.0600 (expected 0.0600)
value +1.0: warnings = []
value +1.0: anchor normal length = 1.0000
value +2.0: anchor displacement = 0.0750 (safe_max 1.25 -> expect 0.0750)
value +2.0: warnings = [{"slider":"head.brow.projection","requested":2,"applied":1.5,"note":"hard clamp to record range"},
                        {"slider":"head.brow.projection","requested":1.5,"applied":1.25,"note":"fold guard: clamped to QA safe_max"}]
bind pose untouched: true
```

## Notes / honest limits

- Geodesics are the graph (Dijkstra) approximation — fine at these mesh
  densities; the heat method is the upgrade path (manual §B.2).
- The lab writes to `output/`, **not** the production store
  (`character_assets/learned/omniversal/`). Graduation is a deliberate
  step (manual §B.8): the BrowProjection record is build-tier by
  construction (procedural, published anchors); the Chubby pieces stay
  study-tier (provenance inherited from the HIMBO mod).
- `decompose.py`'s base is the HIMBO vertex order from
  `learned/himbo-to-fatmales_fit.npz` (the same base the fit validated);
  the 14 parent folds concentrate where that base's triangle coverage
  is known-thin.
- `apply_sliders.js`'s Babylon adapter is exercised only through the
  dependency-free core in Node here — the v2 app loads Babylon from CDN,
  so the adapter path is code-reviewed, not run, in this lab. The core
  math it calls *is* the tested part.
