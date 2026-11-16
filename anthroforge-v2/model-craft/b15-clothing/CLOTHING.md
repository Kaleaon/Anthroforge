# B15 — Clothing Fit Across Slider Extremes

*AnthroForge model-craft wave, study B15. Provenance: the original B15 agent
died on a transport timeout after completing the builds and all measurement
passes but before writing this document. This doc was reconstructed by a
finisher agent from the surviving scripts, `metrics.json`, run logs and
renders; the `.blend` was re-opened and verified, and one extension pass
(belly at hyper 2.0, §6) was run by the finisher using the study's own
machinery. Every number below is from `metrics.json` unless noted.*

## 1. Question

When a character's sliders move to extremes — muscle, fat, coupled tissue —
what happens to a garment that was fitted at neutral? Three standard conform
strategies are compared on the same garment, same body, same states:

- **Method A — delta transfer with a static offset** (BodySlide-style
  conform): the garment is built at neutral as the body surface offset
  outward, then each garment vertex receives *the same morph delta* as the
  body vertex it was derived from. The neutral offset is baked, never
  re-solved.
- **Method B — delta transfer + per-state offset maintenance**
  (shrinkwrap-equivalent): in each state, the garment vertex is placed at
  the *deformed* body vertex plus the design clearance along the *deformed*
  vertex normal. Vertex clearance is re-solved per state; connectivity and
  correspondence are unchanged.
- **Method C — A + iterative collision push-out** (Outfit-Studio-style
  resolve): starting from A, any garment vertex whose signed clearance is
  below a 6 mm target is pushed out along its source body vertex's deformed
  normal, with a graph-Laplacian relax (0.5 blend) between rounds to avoid
  spikes; 4 rounds.

## 2. Setup

- **Body:** MPFB hm08 base, 13,380 body verts (helpers excluded), in the
  first-proof canonical frame (x right, y front, z up, metres).
- **Garment:** a tank top cut from the body mesh itself — torso patch
  (normalised torso height h from −0.06 to 0.985, radius < 0.215 m) with a
  front neck scoop, back neckline and lateral armhole cuts: **1,538 verts,
  168 boundary verts**. Design clearance **8 mm** along neutral vertex
  normals. Because the garment *is* a body patch, garment vertex *i* and
  body vertex `g_idx[i]` correspond exactly — this is the best case for
  delta transfer, and the doc's limits (§8) say so.
- **States** (all at slider +1 unless noted):
  - `neutral` — base.
  - `strongman` — muscle + chest.width + tissue.strongman targets summed
    (bara-proof).
  - `fat_v51` — belly protrusion v5.1 target (first-proof; navel delta
    sanity-checked in-script: ≈ +0.11 m front, −0.07 m down).
  - `gachidebu` — the tissue_wrap coupling composition target (bara-proof).
  - `hyper2` — belly slider **2.0**, finisher extension (§6).

## 3. Measurement — three passes, one authority

The study measured in three generations; they do not all agree, and the
disagreement is itself a result:

1. **Pass 1 — garment-in, nearest-vertex** (`build_garment.py`): signed
   clearance of each garment vertex against the nearest deformed body
   vertex's normal.
2. **Pass 2 — body-through-garment, nearest-vertex**
   (`measure_pokethrough.py`, `method_c.py`): 2,986 body-surface samples
   (covered-region verts + face centroids) tested against the garment.
   This pass also produced the regional diagnosis (worst poke location).
3. **Pass 3 — point-to-triangle signed distance** (`measure_final.py`,
   `measure_masked.py`): exact closest-point-on-triangle both directions.
   **This is the authoritative pass**; passes 1–2 are kept as the diagnosis
   trail. Pass 2's nearest-vertex sign test overcounts poke-through where
   garment faces are large (fat_v51 method A: 1.07% in pass 2 vs 0.10% in
   pass 3), because a body centroid can sit outside the *nearest vertex's*
   tangent plane while still being inside the cloth surface.
   `measure_masked.py` additionally excludes body samples within 20 mm of a
   garment boundary vertex (armholes, scoop, hem — exposed skin by design),
   leaving ~2,490–2,642 samples per state/method.

## 4. Results at +1 (pass 3, authoritative)

### 4.1 Garment vertices penetrating the body

| state | A: % in / max mm / mean clearance | B: % in / max mm / mean clearance | C: % in / max mm / mean clearance |
|---|---|---|---|
| neutral | 0.07% / 6.88 / 7.89 mm | 0.07% / 6.88 / 7.89 mm | 0% / 0 / 10.14 mm |
| strongman | 0% / 0 / 7.68 mm | 0% / 0 / 7.90 mm | 0% / 0 / 10.73 mm |
| fat_v51 | 0% / 0 / 7.25 mm | 0% / 0 / 7.82 mm | 0.13% / 8.0 / 10.35 mm |
| gachidebu | 0% / 0 / 7.63 mm | 0% / 0 / 7.90 mm | 0% / 0 / 10.73 mm |

Garment-side penetration is essentially a non-problem for delta transfer at
+1: pass 1 agrees (worst case across all states is a single vertex 0.76 mm
in at neutral). Vertex clearance does sag under A where the surface grows
(pass-1 min clearance: 1.83 mm at fat_v51, 2.07 mm gachidebu, 3.37 mm
strongman); B restores the vertex-level minimums (3.43 / 5.85 / 6.34
...[truncated 7892 chars] mm) and the
p5 clearance to the full 8.0 mm — but §4.2 shows why that does not save it.

### 4.2 Body poking through the garment (the failure that matters)

Body samples poking outside the garment, openings excluded (masked pass;
unmasked figures differ by <0.1 pt except where noted):

| state | A: % / max mm / mean when out | B: % / max mm / mean when out | C: % / max mm / mean when out |
|---|---|---|---|
| neutral | 0.62% / 8.0 / 7.47 mm | 0.62% / 8.0 / 7.47 mm | 0.32% / 28.92 / 18.01 mm |
| strongman | 0% / 0 / 0 | 0.27% / 7.99 / 7.91 mm | 0.47% / 35.8 / 21.86 mm |
| fat_v51 | 0.11% / 7.69 / 3.33 mm | 2.15% / 8.29 / 7.37 mm | 0.28% / 32.33 / 22.7 mm |
| gachidebu | 0% / 0 / 0 | 0.49% / 8.01 / 7.94 mm | 0.43% / 36.48 / 23.16 mm |

Diagnosis (pass 2): at fat_v51 the worst poke for both A and B sits at
**h ≈ 0.38** — the mid-belly band, where the v5.1 field's growth is steepest
and the garment's faces are stretched widest. The failure is *between*
garment faces, not at garment vertices: body face centroids escape through
cloth faces whose corner verts all test clear.

## 5. Findings

1. **Plain delta transfer (A) is the best of the three at +1.** It is
   exactly clean at strongman and gachidebu (0% poke, both directions),
   near-clean at neutral, and at fat_v51 only 0.11% of covered body samples
   escape, shallowly (mean 3.33 mm when out). The residual at neutral
   (0.62%, max exactly the 8.0 mm design offset) is consistent with
   opening-adjacent samples the 20 mm mask doesn't fully catch, not deep
   through-cloth failure.
2. **Re-solving the offset per state (B) makes fit *worse*, not better.**
   B does exactly what it promises at the vertices (§4.1), but pushing
   every vertex out along the *deformed* normal on high-curvature growth
   opens the faces between them: fat_v51 poke jumps 0.11% → 2.15%,
   gachidebu 0% → 0.49%, strongman 0% → 0.27%. Vertex clearance and cloth
   coverage are different properties; B optimises the wrong one. A
   shrinkwrap-style conform should not be the app's default.
3. **Push-out + relax (C) buys clearance with ballooning and spikes.** C
   holds the highest mean clearance everywhere (10.1–10.7 mm vs the 8 mm
   design) and zero garment penetration except fat_v51 (0.13%), but its
   relax step leaves the worst single-point body pokes in the study
   (28.9–36.5 mm max, mean-when-out 18–23 mm) — a few body samples end up
   far outside a locally over-relaxed cloth, concentrated near openings.
   As implemented (4 rounds, 6 mm target, 0.5 relax) it is not a clean win
   over A on any state.
4. **The binding constraint is garment tessellation over growth zones.**
   All three methods share the body-patch mesh; the mid-belly escapes
   happen where slider growth stretches cloth faces largest. A production
   garment needs its own, denser tessellation over high-growth regions
   (or adaptive subdivision driven by the same fields that drive the
   sliders) before any conform method's ceiling rises.

## 6. Extension: belly at hyper 2.0 (finisher-run)

The study originally stopped at +1. The hyper pass has since shipped a
belly segment to 2.0 (see `hyper/HYPER_RANGES.md`), so the finisher ran the
same garment, methods and pass-3 machinery at slider 2.0
(`scripts/measure_hyper2.py`, results under `hyper2_extension` in
`metrics.json`; C garment saved as `scripts/garmentC_hyper2.npy`).
Composition per the hyper record: v5.1 field + hyper segment delta, contact
corrective excluded exactly as in the original fat_v51 state. Cross-check:
the composition matches the pre-summed `body.belly.hyper2_full.target` to
0.17 mm max anywhere and **0.00 mm on garment source verts**.

| method | garment % in / max pen | mean clearance | body poke % / max | poke, openings excl. % / max / mean-out |
|---|---|---|---|---|
| A | 0.91% / 7.74 mm | 6.33 mm | 1.11% / 15.14 mm | 1.17% / 10.04 / 2.47 mm |
| B | 1.89% / 8.0 mm | 7.29 mm | 4.59% / 17.57 mm | 4.73% / 8.54 / 4.86 mm |
| C | 1.24% / 23.26 mm | 10.54 mm | 1.94% / 37.64 mm | 1.93% / 37.64 / 8.67 mm |

At 2.0 every method degrades and none is production-clean:

- **A stays least-bad** — ~1.1–1.2% of body samples out, shallow on average
  (mean 2.47 mm when out) — but garment-side penetration appears for the
  first time (0.91% of verts, max 7.74 mm).
- **B degrades fastest**, as at +1 only more so (4.59–4.73% poke).
- **C breaks locally**: its own iteration test (nearest-vertex) reported
  the 6 mm target met, but the point-to-triangle pass finds a 23.26 mm
  garment penetration — in the 2.0 fold concavities the approximate sign
  test its loop trusts is wrong. C's max body poke (37.64 mm) is again the
  worst single point.

Conclusion, consistent with the hyper doctrine for the sliders themselves:
**clothing needs re-solving at each segment design point, not
extrapolation of a neutral fit** — a garment authored/re-fitted at the 2.0
state (its own tessellation + a point-to-triangle-grade collision resolve)
is future work; none of the three cheap conforms ships at hyper as-is.

## 7. Deliverables

- **`clothing_fit.blend`** — verified by the finisher to open clean in
  Blender 5.2.3: `Body_hm08` (13,380 verts), `TankTop_A_delta_transfer` and
  `TankTop_C_plus_pushout` (1,538 verts each), every object carrying shape
  keys `Basis / strongman / fat_v51 / gachidebu`. Method B exists only as
  data (`scripts/garment_data.npz`), not as a blend object.
- **Renders** (`renders/`): front Cycles stills — neutral A, strongman A,
  fat_v51 A, fat_v51 C. They verify gross silhouette/fit only: the
  materials' Principled base colour was never set (only viewport diffuse),
  so the stills are clay-shaded and the A vs C garments are *not*
  colour-distinguishable in them. No gachidebu render was produced.
- **Scripts** (run order): `build_garment.py` (garment + states + pass 1,
  writes `garment_data.npz`) → `measure_pokethrough.py` (pass 2) →
  `method_c.py` (C garments + diagnosis) → `measure_final.py` (pass 3) →
  `measure_masked.py` (openings-excluded) → `build_blend.py` (blend +
  renders). Finisher add-on: `measure_hyper2.py` (§6).

## 8. Honest limits

- **One garment, best-case construction.** A sleeveless torso patch derived
  from the body itself, with exact vertex correspondence. Real garments
  (own pattern, own mesh, sleeves, trousers, skirts) break the
  correspondence assumption and will do worse under every method.
- **Bind pose only.** No posing, no walking, no dynamics — all three
  methods are static geometric conforms. Nothing here measures cloth
  behaviour in motion; that belongs to the soft-dynamics work.
- **Single-slider states.** Extremes were tested one slider family at a
  time (strongman is itself a 3-target sum; gachidebu a coupling
  composition). Belly × muscle combos, the masculine base, and the
  negative belly pole are untested.
- **Tessellation confound.** Because garment and body share a mesh, part
  of the measured poke-through is a sampling artifact of that shared
  tessellation (§5.4) — the rates compare methods fairly, but their
  absolute values would move with a production garment mesh.
- **Method C was measured against a stronger test than it optimises**
  (§6) — a C variant whose loop uses point-to-triangle distance might do
  better; that variant does not exist yet.
- **Renders are weak evidence** (§7) — read the numbers, not the stills,
  for A-vs-C differences.

## 9. Recommendation for the app

Default garment conform = **Method A (delta transfer, static neutral
offset)**, with per-garment tessellation density over growth zones treated
as part of the garment record. Do **not** ship shrinkwrap-style offset
maintenance (B) as a "better fit" toggle — measured, it is worse. Reserve
collision resolve (C) for a future implementation whose solver and grader
use the same point-to-triangle metric, and treat hyper-range clothing as a
per-segment re-fit problem (§6), mirroring the slider regime design.
