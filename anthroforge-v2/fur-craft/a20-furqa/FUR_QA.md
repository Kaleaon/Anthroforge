# Fur QA Harness — FUR_QA.md

**Agent A20, fur-craft wave (Nov 12, 2026).** A measurement harness for fur-card
assets: `fur_qa.py` scores a card LOD chain (GLBs, best LOD first) against a set
of PASS / WARN / FAIL gates covering density, silhouette coverage, grazing
behaviour, overdraw, LOD pop-in, direction coherence, and card-texture quality.

**Provenance:** the A20 agent built the tool and completed one recorded run,
then died before writing this doc. This file was reconstructed by a finisher
pass from `fur_qa.py`, `results/fur_qa_results.json`, and `results/run2.log`,
cross-read against A5's budgets (`../a5-budgets/FUR_BUDGETS.md`) and A13's
atlas spec (`../a13-atlas/FUR_ATLAS.md`). The finisher re-ran the tool on the
original subjects and on A13's atlas-remapped LOD0 (§3); every number below is
either from the recorded run or from that verified re-run.

**Running it:**

```
python3 fur_qa.py LOD0.glb [LOD1.glb ...] \
    [--render-strands S.png --render-cards C.png] [--out results.json] [--res 256]
```

Pure numpy + stdlib (PIL only for PNG decode); ~18 s for the prototype's
three LODs at the default 256² raster. **Exit code is 0 unless a file fails to
parse** — scores, not crashes, are the product, so any shipping gate built on
this tool must read the JSON, not the exit status (same convention as the
model-craft gauntlet, B3).

---

## 1. The checks

Cards are recovered from the GLB as **connected components of the triangle
graph**; card direction/length come from UV band centroids under the
fur-prototype convention **v = 1 at root, v = 0 at tip**. Views are the six
axis orthographic projections, rasterised per-triangle.

| Check | What it measures | Gate (PASS / WARN) |
|---|---|---|
| `density_cards_per_m2` | cards ÷ body surface, surface = Knud–Thomsen ellipsoid fitted to the *fur mesh's own* bounding box | ≥ 4000 / ≥ 1500 |
| `silhouette_coverage` | mean over 6 views of (rasterised card silhouette area ÷ convex-hull area of the projected card points). Geometry only — **alpha is not sampled** | ≥ 0.55 / ≥ 0.35 |
| `grazing_retention` | smallest view silhouette area ÷ largest (worst-view projected-area retention; a skin-show-through proxy) | ≥ 0.55 / ≥ 0.35 |
| `overdraw` | per view: alpha-weighted summed triangle area ÷ silhouette area, averaged. Alpha weight = the material texture's `strand_fill_alpha` (0.8 fallback if no texture) | ≤ 4.0 / ≤ 8.0 |
| `popin_delta[LOD]` | \|coverage − previous LOD coverage\| ÷ previous LOD coverage, per step down the chain | ≤ 0.10 / ≤ 0.25 |
| `direction_coherence_neighbour` | mean resultant length of card direction vectors within 0.15 m root-position bins (≥ 3 cards per bin) — do neighbouring cards agree on flow? | ≥ 0.75 / ≥ 0.55 |
| `direction_straightness` | per-card chord ÷ polyline path through v-band centroids, averaged | ≥ 0.85 / ≥ 0.70 |
| `texture_alpha_coverage[tex]` | fraction of embedded baseColor texels with alpha > 0.5 (the cutout precondition, cf. A5 §6: ≥ 15% opaque core) | ≥ 0.25 / ≥ 0.12 |
| `strand_fill_alpha` (reported, ungated) | mean alpha over texels with alpha > 0.03; also the overdraw weight | — |
| `colour_band_gradient[tex]` | (max − min) ÷ mean of the alpha-weighted luminance profile over 10 root→tip row bands | ≥ 0.25 / ≥ 0.10 |
| `dead_uv_fraction[tex]` | fraction of the 10 root→tip bands with < 1% occupied texels — is the texture's length actually used? | ≤ 0.05 / ≤ 0.20 |
| `lod_texture_alpha_ratio[tex vs LOD0]` | same-named texture's mean alpha at LODn ÷ at LOD0 — encodes A5 §5's rule *textures are not per-LOD; the chain must not fade as it steps down* | 0.7–1.4 / 0.4–2.0 |
| `render_silhouette_ratio` (optional) | foreground pixels of the card render ÷ the strand-groom render (corner-pixel background, fixed threshold). The only check scored against the groom master; runs only when both renders are supplied | ≥ 0.85 / ≥ 0.65 |

Also reported per LOD, ungated: card count, tris, mean card length/width,
per-view coverage, full band profiles, and `band_trend_corr` (root→tip
luminance trend correlation — computed but never gated; see §4).

---

## 2. Measured results — fur-prototype card chain

The only chain the tool has been run on in anger: `fur-prototype/fur_cards_lod{0,1,2}.glb`
plus the prototype's strand/card renders. This is the known-deficient prototype
(A5 §7 scored it FAIL on coverage, alpha, and packaging), so the run is best
read as the harness's calibration exercise: does it catch what A5 and A13
already proved by hand? **Largely, yes** — with the caveats in §5.

### 2a. Per-LOD metrics

| Metric | LOD0 | LOD1 | LOD2 |
|---|---|---|---|
| Cards (connected components) | 2,116 | 886 | 327 |
| Tris | 13,600 | 5,440 | 2,040 |
| Body-surface estimate (m², fur-bbox ellipsoid) | 8.959 | 10.045 | 9.423 |
| Cards / m² | 236.2 | 88.2 | 34.7 |
| Mean card length (m) | 0.0737 | 0.0706 | 0.0720 |
| Coverage (mean of 6 views) | 0.346 | 0.196 | 0.104 |
| Coverage by view (LOD0) | ±x 0.184/0.185 · ±z 0.311/0.304 · ±y 0.548/0.545 | | |
| Grazing retention | 0.633 | 0.497 | 0.464 |
| Overdraw | 1.348 | 0.126 | 0.100 |
| Straightness | 1.000 | 1.000 | 1.000 |
| Neighbour coherence | 0.852 | 0.858 | 0.864 |
| Pop-in delta vs previous LOD | — | 0.434 | 0.469 |

### 2b. Texture metrics (embedded baseColor images)

| Texture | alpha > 0.5 | strand fill | mean alpha | dead UV | band gradient | band trend |
|---|---|---|---|---|---|---|
| LOD0 `FurCardA` | 0.363 | 0.660 | 0.386 | **0.30** | 0.790 | +0.08 |
| LOD0 `FurCardB` | 0.363 | 0.719 | 0.375 | **0.30** | 1.014 | +0.24 |
| LOD1/2 `FurCardA` | 0.00009 | 0.107 | 0.064 | 0.10 | 0.648 | −0.82 |
| LOD1/2 `FurCardB` | 0.000 | 0.076 | 0.032 | 0.10 | 0.866 | −0.88 |

LOD0's band profiles end in three **NaN bands** — the bottom 30% of the
texture carries no alpha weight at all (the dead-UV FAIL). LOD1/LOD2 embed
byte-identical texture stats to each other, with a clean root→tip falloff.

### 2c. Gates — 17 unique: 9 PASS, 8 FAIL

| Gate | Value | Verdict |
|---|---|---|
| grazing_retention | 0.633 | PASS |
| overdraw | 1.348 | PASS |
| direction_coherence_neighbour | 0.852 | PASS |
| direction_straightness | 1.000 | PASS |
| texture_alpha_coverage [A / B] | 0.363 / 0.363 | PASS |
| colour_band_gradient [A / B] | 0.790 / 1.014 | PASS |
| render_silhouette_ratio | 0.926 | PASS |
| density_cards_per_m2 | 236.2 | **FAIL** |
| silhouette_coverage | 0.346 | **FAIL** (below even the 0.35 WARN line) |
| dead_uv_fraction [A / B] | 0.30 / 0.30 | **FAIL** |
| lod_texture_alpha_ratio [A / B] | 0.165 / 0.085 | **FAIL** |
| popin_delta [LOD1 / LOD2] | 0.434 / 0.469 | **FAIL** |

(The results JSON lists 19 rows: the two alpha-ratio gates appear twice
because LOD1 and LOD2 share textures, and the gate name doesn't carry the
LOD index — a tool wart, noted in §5.)

### 2d. Reading the run against A5 and A13

- **The FAILs corroborate the hand audits.** Coverage FAIL matches A5 §7c/§7d
  (LOD0 quad area = 0.47× body surface; effective alpha-aware coverage ≈ 14%).
  The dead-UV FAIL is A13 §1.3 measured from the other side (bake alpha mass
  dies by ~85% of texture height; A13 §4's framing rule — strand field fills
  ≥ 95% of cell height — is the fix). The pop-in FAILs quantify A5 §7c's
  "silhouette collapse down the chain": each step down loses 43–47% of the
  previous LOD's coverage.
- **The alpha-ratio FAIL's direction of blame is LOD0, not the lowers.** A13
  §1.1 proved by sha256 that `fur_cards_lod0.glb` embeds the *wrong* (v1)
  bake, while LOD1/LOD2 embed the correct v2 bakes. The v1 images are far
  denser (mean alpha 0.386/0.375 vs 0.064/0.032), so the ratio collapses.
  The gate did its job — it detected a real cross-LOD inconsistency — but a
  reader who assumes the lowers faded would fix the wrong file.
- **Consequence for the texture PASSes:** `texture_alpha_coverage` PASSing at
  0.363 describes the *v1 images embedded in the shipped GLB*, not the
  standalone v2 textures A5 §7d measured at **0.0% of texels > 0.5** (mean
  alpha 0.064/0.032 — exactly the stats this tool reads from LOD1/LOD2).
  Both are true; they are measurements of different images. `fur_qa` measures
  assets *as shipped*, which is what a shipping gate should do — but any
  citation of these numbers must say which images were in the file.
- **Overdraw PASS needs an asterisk.** A5's O budget (≤ 2.0, WebGL high tier)
  is referenced to *visible body* area; this tool's overdraw is referenced to
  the fur silhouette and weighted by strand fill — a related but different
  quantity. LOD1/LOD2 reading 0.13/0.10 is an artefact of their faint
  textures' low fill weights, not evidence of efficiency.
- **Density FAIL is real but the gate is uncalibrated** (see §4): A5's
  production plan is ≈ 4,700 placements over the wolf's measured 4.93 m² body
  ≈ 950 cards/m² true-body — and the tool's PASS line is 4,000/m² against an
  ellipsoid denominator that itself reads ~9 m² for this body. A
  budget-conforming production coat would FAIL this gate by 4–8× under
  either denominator.

### 2e. Re-run verification (finisher)

The finisher re-ran `fur_qa.py` on the same three GLBs + both renders:
**every gate value reproduced exactly** (the tool is deterministic — no
randomness, no timestamps in the scoring path), ~18 s wall for the chain.

---

## 3. Second subject — A13's atlas-remapped LOD0

`a13-atlas/fur_cards_lod0_atlas.glb` (same cards, UVs remapped onto the
2048 atlas, materials collapsed 2 → 1, textures no longer per-card files):

- Geometry scores are **identical** to §2a LOD0 (2,116 cards, 13,600 tris,
  coverage 0.346, grazing 0.633, coherence 0.853) — the remap preserved the
  geometry, and the harness sees it.
- Texture scores now read the **single `FurCardAtlas` image**: alpha
  coverage 0.138 (WARN), band gradient 1.168 (PASS), dead UV **0.0** (PASS),
  overdraw 0.708 (geometry unchanged — the delta from 1.348 is purely the
  texture's strand-fill weight).
- **Threshold conflict, measured:** A13's ATLAS-ALPHA-1 contract *designs*
  the DENSE slot to land at 0.15 coverage at the 0.5 cutoff (renormalised
  mip-0 measured 0.143 in FUR_ATLAS §5). A whole-page read of a conforming
  atlas gives 0.138 — yet this harness's alpha gate calls anything < 0.25 a
  WARN and < 0.12 a FAIL. **A texture built exactly to the atlas spec scores
  WARN here.** The gate predates the atlas; §4 reconciles them.
- **Dead-UV and banding change meaning under an atlas.** The metric reads 10
  horizontal bands across the whole 2048² page (4 × 2 cells); every band has
  some slot's texels in it, so dead UV reads 0.0 *vacuously* — it no longer
  measures any card's root→tip framing. Slot-aware sampling (the rect data
  already exists in `fur_atlas_layout.json`) is required before these two
  checks can gate atlas-based assets.

---

## 4. Gate graduation — what should ship-block, what stays advisory

Following B3's QA2 precedent (model-craft/b3-qa/QA2.md): graduate to
**fail-status** the checks that are (a) fully in the exporter's control and
(b) proven achievable; keep **advisory** the ones that are intent-dependent
or not yet calibrated against a passing production asset. Nothing in this
harness has yet seen a production asset pass, so quality thresholds graduate
conservatively.

### Graduate to FAIL for AnthroForge's own fur exports

1. **Cross-LOD texture consistency** (`lod_texture_alpha_ratio`, 0.7–1.4).
   Deterministic, exporter-controlled, and it already caught a real defect
   (the LOD0 wrong-bake embed). **Successor check:** once the A13 pipeline
   is the exporter, replace it with the stronger parse-level rule *LOD GLBs
   embed no textures at all* (FUR_ATLAS §9 step 6) — consistency by
   construction.
2. **Dead UV ≤ 0.05** — for standalone card textures. Bake framing is a
   pack-time discipline (A13 §4), not an artistic judgement, and the
   prototype's 0.30 shows the failure mode is real. For atlas assets this
   graduates only after the slot-aware re-implementation in §3.
3. **Pop-in delta: FAIL above 0.25** (today's WARN line becomes the hard
   line; ≤ 0.10 stays the PASS quality bar). A > 25% silhouette loss per
   LOD step is a visible pop under any art direction; the tighter line
   awaits calibration against a production chain built to A5 §5's switch
   spec.
4. **`render_silhouette_ratio` ≥ 0.85**, conditional on reference renders
   being supplied. The prototype itself proves 0.926 is achievable (B3's
   achievability test), and this is the only gate that compares cards
   against the groom master they were baked from.

### Keep advisory (WARN-tier) until calibrated

- **Density** — threshold is not derived from A5's budgets (§2d). Before it
  can gate: take the surface denominator from the *body mesh*, not the fur
  bbox, and recalibrate to A5 §4 (≈ 950 placements/m² of body, quad-area
  ratio ≥ 1.28×).
- **Silhouette coverage** — alpha-blind and self-referential (the
  denominator is the fur cloud's own hull, not the body's silhouette).
  Advisory until paired with an alpha-weighted variant measured against
  the body mesh.
- **Grazing retention** — a bbox-extent proxy, not a grazing-angle test.
- **Overdraw** — keep as a same-tool relative/regression measure. A5's
  O ≤ 2.0 is the real contract and needs a body-referenced implementation
  before it can ship-block.
- **Neighbour coherence** — the one geometry-quality signal that reads
  sensibly across all three LODs (0.85–0.86); graduate after one production
  asset passes it.
- **Colour band gradient** — measures gradient *strength*, not root→tip
  correctness: LOD0's scrambled v1 profile PASSes at 0.79/1.01 while
  LOD1/2's clean falloff also passes. If banding direction matters, gate
  the (already computed) `band_trend_corr` instead.

### Fix or retire before any gating use

- **`texture_alpha_coverage` thresholds conflict with ATLAS-ALPHA-1**
  (gate PASS ≥ 0.25 vs the atlas DENSE design point of 0.15; §3). Reconcile
  per slot class: DENSE-class PASS at the A13 contract (≈ ≥ 0.12–0.15),
  SPARSE-class exempt by design (it renormalises to 0.034 and is a
  near/mid-range layering slot, FUR_ATLAS §5).
- **`mean_card_width_m` is broken** — reports 0.9 mm for cards A13 measured
  at 16–30 mm wide. The implementation takes a single perpendicular spread
  against a fixed [0,0,1] axis. Fix or drop the field; do not cite it.
- **`direction_straightness` saturates** — 1.000 at every LOD because the
  prototype's cards are planar ribbons (band centroids are colinear by
  construction). No signal for the current card style; keep only if curved
  multi-segment cards arrive.
- **Duplicate gate rows** when LODs share textures (§2c) — name ratio/pop-in
  gates with their LOD index.

---

## 5. Honest limits

- **One real subject.** The full gate set has only ever been exercised on
  the known-deficient prototype chain (plus the finisher's single-LOD atlas
  run, §3). Thresholds for density, coverage, grazing, and overdraw are
  uncalibrated against any production asset; treat every PASS line except
  §4's graduated four as provisional.
- **Coverage is alpha-blind.** A card counts as full silhouette even if its
  texture is 94% transparent. The tool's 0.346 and A5's ≈ 14% effective
  coverage describe the same coat; neither number is interchangeable with
  the other.
- **The density denominator is the fur, not the body.** The ellipsoid is
  fitted to the card cloud's bbox, so the "same" body reads 8.96 / 10.05 /
  9.42 m² across its own LODs — density comparisons across LODs inherit
  that wobble. (A5's measured wolf body surface: 4.93 m².)
- **Card counting ≠ placement counting.** Connected components give 2,116
  LOD0 "cards" where A5 counted 1,700 placements at identical tri counts —
  cross-plane pairs and split fragments inflate the count ~24%, and the
  density gate inherits the inflation.
- **UV convention is assumed, not checked.** Card direction, straightness,
  and the texture banding all hard-assume v = 1 at root. A card set built
  with the opposite convention would score inverted directions and banding
  *silently* — no gate would complain.
- **Texture checks assume the embedded image *is* a card texture.** Under
  the A13 atlas they read a whole page of slots (§3); under a KTX2 export
  (FUR_ATLAS §7's shipping format) the PIL decode path won't read the image
  at all and texture gates will silently not fire — a missing-texture asset
  and a KTX2 asset are indistinguishable to this harness today.
- **Nothing here runs in an engine.** No Babylon/WebGL behaviour, no sorting
  or mip behaviour in a real renderer, no skinning. A13 §5's mip-stability
  table came from image analysis, not this tool.
- **Scale ceiling.** The rasteriser is a per-triangle Python loop at 256²:
  fine for card GLBs (~6 s/LOD), not viable for strand geometry, and thin
  cards quantise at this resolution (LOD0's ±x coverage of 0.184 is partly
  raster grain).
- **Grazing retention is a proxy of a proxy** — bbox-extent retention across
  axis views. It cannot see the actual grazing failure mode (card edges
  going transparent edge-on); that needs a renderer or an edge-on card
  incidence metric this tool doesn't have.

---

## 6. Handoffs

- **To the export pipeline:** §4's four graduated gates are the fur export
  contract; the JSON output is the interface (exit code is always 0).
- **To the atlas line (A13):** slot-aware texture sampling (dead UV, banding,
  per-slot alpha at the ATLAS-ALPHA-1 targets) is the missing piece before
  this harness can gate atlas-based fur.
- **To the card-bake line (A8/A2):** the framing rule (≥ 95% of cell height)
  and the cross-LOD consistency gate are the two checks your output will be
  scored against first.
- Disk discipline: analysis + two tool re-runs only; nothing downloaded,
  scratch output written to /tmp; free space unchanged (~56 GB).
