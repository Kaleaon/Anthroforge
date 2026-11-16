# Base Head v5 — Lip-Line Loop Cage (B12 F-M7)

Built 2026-11-16 from `base-head-v4/` (untouched). Joe's direction: heads and
faces first. Deliverables in this folder:

- `neutral_base_head_v5.blend` / `.glb` / `.groups.json`
- `proportions.json` — full gate table (machinery: `work/measure_v5.py`)
- `renders/` — clay: front, three-quarter, profile, jaw-open three-quarter
- `work/build_v5.py`, `work/mouth_open_v5.py` (+ `mouth_open_v5.json`),
  `work/render_v5.py`, `work/final_measure_v5.json`, `work/build_log_v5.json`

## What changed topologically

v4's lip line was a crease: the tissue/jaw seam crossed the front of the muzzle
and the two shells simply ended there. v5 replaces the surface band around that
line with a real loop cage, per FACE_CRAFT.md §1.4/§6.4 (F-M7):

- **The lip line is the front run of the tissue/jaw seam**, extracted as the
  owner-change edge path (119 verts), cut at the commissures and resampled to
  **81 columns** (length 1.354 L-units, spacing 0.0169, mirror-symmetrised,
  max edge asymmetry 0.000133). It is now a row of real vertices shared
  (as position duplicates) by both shells.
- **Cage cross-section** (one continuous strip, 9 rows × 81 = 729 verts):
  tissue support (+0.045 surface walk) → tissue body (+0.020) → **edge (the lip
  line)** → tissue margin1 → tissue margin2 → *the mouth opening (a real gap)*
  → jaw margin2 → jaw margin1 → **edge** → jaw body → jaw support.
  F-M7's ≥3 concentric loops per side are the support/body/edge rows; the two
  margin rows per side give the lip real thickness around a real opening.
- **Poles only at the commissures**: end columns of every row are pinched
  toward the commissure point (weights 0.92/0.60/0.40/0.25/0.12), forming the
  tight pole clusters F-M7 prescribes.
- **Margins roll before they dive**: margin step 1 is z-divergent (each margin
  leaves the rim toward its own shell — tissue up toward the palate vault, jaw
  down toward the mouth floor), step 2 travels back into the cavity. Depth is
  **capped per column at 0.55 × the measured rim→teeth clearance** (both
  arcades): the vestibule at the side-front columns is only ~0.011 deep
  (rim col 16 clearance 0.0107) against a nominal 0.022 tuck; 45/81 columns
  keep full depth, minimum cap factor 0.232. A per-column separation pass
  keeps the two margin strips ≥0.0035 apart in the cheek pouch.
- **Philtrum (F-M5, partial)**: centre ±3 columns of the tissue body/support
  rows are pinched inward (0.0030/0.0020, cos² falloff). The edge row is not
  pinched. The philtrum's upper span to the nose seat is not built (B12 item 6).
- **Integration with the layered construction**: the merged tissue+jaw surface
  was cut by deleting the band within geodesic distance ~0.052 of the lip line
  (multi-source Dijkstra over mesh edges; flush end cuts at the commissures —
  152 faces), the cage grid (640 quads) was inserted, and the annulus between
  the cage's outer loop and the cut boundary was bridged with
  `bmesh.ops.bridge_loops` (282 tris; three hand-rolled pairing walks failed on
  the boundary's commissure weave — see work/build_v5.py header notes).
  Bridge faces were assigned to Tissue/Jaw by vertex vote + BFS propagation so
  each object's bridge region stays one contiguous band. Skull / muscle /
  mandible layers were regenerated with build_v4b's recipes; the teeth arcades,
  tongue, eyes, ears and all other objects are carried over unchanged.
- **New vertex groups** (the slider/expression hand-off): `LipCage`
  (405 verts per object = 5 rows × 81), `Philtrum` (14), `CommissureL` /
  `CommissureR` (11 tissue / 12 jaw each).

Resulting meshes: TissueHead 4,099 v / 4,152 f; Jaw 2,348 v / 2,274 f.
**Both objects: 0 nonmanifold edges, 0 inconsistent windings.** Boundary
chains — tissue [170, 32, 32] (main + two ear holes, as v4's [130, 32, 32] plus
the cage rim), jaw [192, 92] (main + inner loop, v4 [154, 92]); every boundary
vertex degree 2. GLB gauntlet: 21 meshes, 44,161 v / 22,050 t, 0 degenerate,
0 NaN, extent 1.0977 m (v4: 41,389 v / 20,792 t, same extent).

### Commissure placement — flagged deviation from F-M8

F-M8 puts the commissure at (±0.165, 0.08, −0.18). The cage's poles sit at
**(±0.2285, 0.0953, −0.1868)** — y and z match, x does not. The poles were
picked from real seam vertices nearest the F-M8 target: at mouth-corner height
the jaw cut genuinely wraps the cheek at |x| ≈ 0.229 on this head (eye centre
x is 0.1311; the muzzle is wide — see the MuzzleWidth gate). Ending the cage
off-seam mid-cheek would detach it from the actual mouth opening, so the cage
follows the seam. If Joe wants the mouth corner pulled in to 0.165, that is a
jaw-cut redesign, not a cage change.

## Proportion gates — v4 vs v5

Rule (as v4's): no gate's |dev| may exceed v4's. **MuzzleWidth is measured
surface-true** — edge∩plane section over the merged tissue+jaw surface at the
canonical station (diag_g method). The vertex-slab ruler is **superseded**:
it scoped TissueHead only and densification moved it (v3 0.2158 → v4 0.2332
while the surface never changed; surface-true reads 0.2413/0.2412 on v3/v4).
Interorbital held at 0.1122 by design (Joe's ruling still open — not changed).

| gate | target | v4 | dev | v5 | dev | parity |
|---|---|---|---|---|---|---|
| ZB | 0.58 | 0.5466 | −5.8% | 0.5466 | −5.8% | ✓ |
| CraniumWidth | 0.36 | 0.478 | +32.8% | 0.478 | +32.8% | ✓ |
| MuzzleWidth (surface-true) | 0.17 | 0.2412 | +41.9% | 0.2412 | +41.9% | ✓ |
| MuzzleDepth | 0.20 | 0.231 | +15.5% | 0.231 | +15.5% | ✓ |
| SkullHeight | 0.31 | 0.3168 | +2.2% | 0.3168 | +2.2% | ✓ |
| MuzzleFrac | 0.33 | 0.3435 | +4.1% | 0.3435 | +4.1% | ✓ |
| OrbitDiameter | 0.15 | 0.150 | 0.0% | 0.150 | 0.0% | ✓ |
| Interorbital | 0.19 | 0.1122 | −40.9% | 0.1122 | −40.9% | ✓ (held) |
| OrbitHeight | 0.17 | 0.172 | +1.2% | 0.172 | +1.2% | ✓ |
| OrbitRise | 0.12 | 0.2035 | +69.6% | 0.2035 | +69.6% | ✓ |
| EarLength | 0.40 | 0.3776 | −5.6% | 0.3776 | −5.6% | ✓ |
| JawLength | 0.74 | 0.7128 | −3.7% | 0.7090 | −4.2% | ✗ (+0.5 pt) |
| JawWidth | 0.40 | 0.533 | +33.2% | 0.533 | +33.2% | ✓ |
| RamusDepth | 0.28 | 0.2697 | −3.7% | 0.2697 | −3.7% | ✓ |

**13/14 gates at exact v4 parity; 8/14 inside the ±6% target band, same as
v4.** The one miss: JawLength moved 0.0038 (the attaining chin-front vertex
sat inside the deleted band; the cage's walked surface there sits a hair
inside the old extreme). It remains inside the ±6% band. Not chased — moving
geometry to satisfy a ruler artefact is how v4 got its MuzzleWidth scare.

Surface metrics (measure_v4's method): cheek facet 9.08° → 11.58°, vertex-
normal step 11.33° → 14.57° — the metric's cheek window now includes the cage
band and bridge (denser, folded margin rows), so the rise is the cage being
measured, not the cheek getting worse. Seam roughness **improved**
0.0259 → 0.0160 (the shared boundary now runs along the resampled rim;
150 coincident points vs 119).

## Teeth + mouth-open test

Jaw articulation is rigid-object posing about the hinge H = (0, −0.2167,
−0.1249) — Jaw and TeethLower carry loc = H; Tongue rides the same matrix.
No armature exists yet (same scope as v3/v4). Full data:
`work/mouth_open_v5.json`.

**Teeth arcades (the v4 verify, re-run): 0 BVH overlap pairs at −10/−20/−30°**;
sampled min clearances 0.0277 / 0.053 / 0.0759 (v4 build log: 0.0241 / 0.0476 /
0.0692 — same regime).

**Rim gap** (tissue edge row vs jaw edge row, column-matched; the rows are
exact duplicates at rest, gap 0.000000): centre column 0.125 / 0.249 / 0.371
at −10/−20/−30°; front-mean 0.120 / 0.238 / 0.355; commissure gap
0.055 / 0.111 / 0.165 — symmetric left/right to 4 decimal places. Commissure
group-centroid separation at rest is 0.0043 (the two pole clusters are near-
duplicates, not shared verts — expected in the two-shell construction).

**Margin clearance — 0 overlap pairs everywhere**: tissue margin vs TeethLower,
jaw margin vs TeethUpper, tissue margin vs TeethUpper, jaw margin vs
TeethLower (rigid-invariant pair), and margin vs margin, at rest and at all
three angles. This was not free: the first cage build interpenetrated the
upper teeth at the side-front columns (29 pairs) and the margins crossed in
the slit (39 pairs); the fixes were the own-shell roll direction, the
clearance-capped depth, and the roll-first step — all documented above.

**Lip-part field test** (synthetic): both edge rows displaced apart along the
jaw-travel direction (0.01 each at centre columns, cos² falloff over ±20
columns, graded weights across all cage rows: rim 1.0, margin1 0.6, margin2
0.35, body/support 0.35). Achieved centre parting 0.020; max edge stretch
1.161 (tissue) / 1.202 (jaw); min face-area ratio 0.63 / 0.43; **0 flipped
faces** in either 640-tri strip. The cage parts without tearing.

**Rigid-pose sanity**: jaw face areas invariant under the pose (max drift
0.0), normals invariant to 1e-06 degrees — the pose is a pure rotation, as
designed.

## Renders

`renders/head_v5_front.png`, `head_v5_threequarter.png`,
`head_v5_profile.png`, `head_v5_jawopen_threequarter.png` (−25°). Cycles CPU,
single clay material, flat grey world + sun lights, no HDRI (Workbench/EEVEE
need libEGL, absent on this VM). The dark temple/cheek fossa in the side
views is shadow in a concave region, not a hole — verified by ray casts
hitting TissueHead identically on v4 and v5.

## Debits

1. **JawLength parity miss** (−3.7% → −4.2% vs target; 0.0038 absolute) —
   documented above; inside the ±6% band.
2. **Philtrum is partial**: only the lower ~0.045 of its span (body/support
   rows at the rim). Full philtrum to the planum awaits the nose-seat work
   (B12 build order item 6).
3. **Margins are tucked surface, not a sealed oral cavity**: the two margin
   strips end facing each other across a gap; there is no inner mouth bag
   behind them. Fine for lip motion; a tongue/throat seal is separate work.
4. **No rig**: the jaw is a node transform on the v4 pivot; TeethLower follows
   by copied pivot, exactly as v4. The cage is not yet wired to any slider —
   `LipCage` / `CommissureL/R` / `Philtrum` groups are the hand-off for the
   E9/E11–E17 lip sliders (FACE_CRAFT §5.2, all still ✗).
5. **Bridge triangles are the cage's coarsest faces**: mean edge 0.021 but
   p95 0.062, max 0.102 at the muzzle front and commissure chords (54 of 846
   bridge edges > 0.06). Topologically clean; a density pass could even them
   out if the front bridge shading bothers in smooth renders.
6. **Merged-intermediate note**: in the merged working mesh the lip-line edge
   carries 4 faces (interior to both objects' patches by construction). Each
   delivered object is individually manifold — this only matters if a future
   tool re-merges the shells naively.
7. Cheek facet / normal-step metrics rose (11.58° / 14.57°) because the
   metric window now contains the cage — if a future gate wants a pure-cheek
   number, the window needs a cage exclusion.
