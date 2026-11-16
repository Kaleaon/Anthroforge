# SCAN_CLEANUP.md — House checklist for scan / reference-model cleanup

**Agent B19, model-craft wave, Nov 12, 2026.** How AnthroForge takes a raw scan-like
asset (photogrammetry, structured light, CT-derived) to a presentable, measurable
state — and how we *prove* each step with numbers instead of eyeballing it.

Prototype asset: **Poly Haven lion head** (photogrammetry scan of a carved lion-head
plaque, CC0, 1k texture set) — `bodies-3d/parts-library/polyhaven/lion-head/`.
Cleaned result: [`lion_head_clean.glb`](sandbox://workspace/anthroforge-v2/model-craft/b19-scans/lion_head_clean.glb);
before/after clay renders in [`renders/`](sandbox://workspace/anthroforge-v2/model-craft/b19-scans/renders/);
pipeline scripts + stage audit in `work/` (`audit.py`, `clean2.py`, `holefill_test.py`, `lion_audit.json`).

---

## 1. The audit comes first — and it must be run on the *welded* mesh

Every cleanup starts and ends with a measured audit, never a visual once-over.
Our audit (`work/audit.py`, Blender headless, bmesh) reports: verts / edges / faces,
boundary edges and boundary **loop count + loop sizes**, non-manifold edges
(>2 faces), wire edges, degenerate faces, loose verts, duplicate verts,
connected-component sizes, signed volume, surface area, bbox, a surface-roughness
metric (mean distance of each vertex from its neighbours' centroid), and a
mirror-asymmetry sample.

**Methodology rule (learned the hard way on this very asset):** glTF stores
split vertices at UV seams. A naive audit of the as-stored file reports those
seam splits as "holes" and "fragments". The lion arrived showing **3,468 boundary
edges in 49 loops and 44 components** — and *all of it* was split-vertex storage:
one weld pass (merge by distance, 1e-5 m) removed 1,769 duplicate verts and
closed every boundary edge **without adding or deleting a single face**.
So: audit the working (welded) mesh for truth; treat as-stored counts as a
storage-format artifact. The shipped GLB re-splits on export for the same
reason (25,147 stored verts vs 23,442 working verts) — re-import + weld
reproduces the watertight numbers exactly. This is normal for glTF, not damage.

## 2. The house pipeline (in order — order is load-bearing)

| # | Step | What it fixes | House tool / setting | Gate to proceed |
|---|------|---------------|----------------------|-----------------|
| 0 | **Audit + copy** | — (work on a copy, keep the original pristine) | `audit.py` | baseline numbers recorded |
| 1 | **Weld** (merge by distance) | split-vertex seams masquerading as holes/fragments; seam "noise" | Blender `remove_doubles`, dist 1e-5 m (0.1× the smallest feature you care about) | boundary edges collapse or reduce to *true* holes only |
| 2 | **Cull non-subject components** | capture environment & debris (ground discs, table slices, stray islands) | component census + distance rule (§3) | 1 component, or every extra component justified in writing |
| 3 | **Degenerate / loose cull** | zero-area faces, orphan verts from the scanner's meshing | area < 1e-10 m² | 0 degenerate, 0 loose |
| 4 | **Fill true holes** | occlusion gaps (under chin, concavities, underside) | Blender `holes_fill`; MeshLab *Close Holes* (its size limit counts **boundary edges**, not mm) | boundary edges = 0 |
| 5 | **Normals** | inverted / inconsistent facing from stitched scan passes | recalc outside; verify signed volume > 0 | volume positive, no see-through backfaces |
| 6 | **Denoise — guarded, optional** | scanner surface noise (photogrammetry ~sub-mm–mm; LiDAR 1–2 mm) | Taubin smooth (λ 0.30 / μ −0.34), trial on a copy first | apply **only** if roughness gain > 10% **and** bbox drift < 0.5% |
| 7 | **Symmetry — measured, enforced only for anatomy** | one-sided damage / scan warp on bilaterally symmetric subjects | mirror-difference sample; symmetrize/mirror-half for skulls & anatomy | decision + numbers recorded either way (§4) |
| 8 | **Scale calibration + grounding** | unit drift, environment padding inflating dims, floating origin | verify against a named reference dimension; seat subject at z = 0 | reference dimension recorded; no silent rescale |
| 9 | **Re-audit + export** | regressions from any step | `audit.py` on the result | all gates in §6 green |

Notes per step, from craft sources and this run:

- **Weld before you judge anything.** Half of all "broken scan" panic is
  unwelded storage. MeshLab equivalent: *Cleaning → Merge Close Vertices* /
  *Remove Duplicate Vertices*.
- **Hole fill size discipline.** Fill small holes automatically; a hole the
  size of a face filled flat looks wrong — large gaps want a bridged/curved
  patch or manual work. Blender's `holes_fill` with `sides=0` closes a loop
  with a **single flat n-gon**: correct for backs, plugs and plaque bottoms;
  on curved surface use a triangulated fill (sides limit + triangulate) or
  Edit-Mode Grid Fill, then relax the patch so it inherits local curvature.
- **Non-manifold repair** (none present on this asset): MeshLab *Repair
  Non-Manifold Edges* is surgical; Blender's 3D-Print Toolbox flags them.
  Self-intersections are the stubborn case — a boolean union-with-self or a
  Poisson re-shell (MeshLab *Surface Reconstruction: Poisson*, depth 8–10)
  is the heavy hammer, at the cost of fine detail.
- **Decimation is a downstream decision, not a cleanup step.** Cleanup keeps
  full resolution; reduction for a target (print / real-time / retopo base)
  happens after, quadric edge collapse (MeshLab) preserving boundary +
  normals + UVs, then **re-audit** — aggressive decimation can create new
  non-manifold edges.
- **CT / volumetric sources branch here** (our puma CT skull is the local
  example — a 172 MB threshold-surface export): expect internal structures,
  threshold noise and extreme counts. Weld/cull/fill still apply, but budget
  a decimation or Poisson pass and verify no internal shell survives inside
  the anatomical surface; scale comes from the DICOM voxel spacing, not the
  mesh — record it at import.

## 3. Component-cull rule (debris vs subject)

Cull a component only when **both** hold: (a) it is < 1% of the largest
component's vertex count, **and** (b) every one of its vertices sits > 2 mm
from the main shell (KD-tree min distance). Log every culled component's
size, bbox and distance — never cull silently.

Prototype evidence: after welding, the lion had one extra 169-vert component
(0.72% of main, min distance 3.5 mm, median 44.5 mm): the ornament's **square
display plinth, 206.6 × 206.6 × 39.4 mm** (visible in `renders/before_back.png`).
Presentation hardware, not the head subject → culled; it survives untouched
in the pristine original. Had it been touching or large, it would have stayed
and been documented instead.

## 4. Symmetry policy

Measure first: mirrored nearest-vertex distance over a sample of one side.
The lion measures **median 2.9 mm, p90 8.1 mm** of asymmetry — and we
deliberately did **not** symmetrize it: it is a hand-worked carving, the mane
asymmetry is the art. Enforcement is reserved for anatomical assets (skulls,
bones, body scans) where bilateral symmetry is biology, not style — and even
real bone carries ~0.5 mm regional asymmetry (contralateral-template studies
in the medical literature), so the house method is: mirror the *better* side
over a *damaged/missing* region, don't iron a healthy asset flat. For heads
this ties into the layered-construction rule: symmetrize the skull layer if
needed; tissue and mane keep their asymmetry.

## 5. Scale calibration

- Verify, don't assume. Poly Haven ships real-world metres; the as-stored
  bbox (436.4 mm tall) *looked* plausible — but 33 mm of that was the display
  plinth and float. True subject height after cleanup: **403.5 mm**, seated at
  z = 0 after a −32.9 mm grounding shift. **Environment geometry inflates
  dimensions; calibrate after the cull, not before.**
- Record one named reference dimension per asset ("overall height 403.5 mm")
  in the asset's notes. If a rescale is ever required, it is computed from
  that dimension and written down — never eyeballed, never silent.
- Orientation: face direction and up-axis recorded (this asset: front = −Y
  in Blender space after glTF import).

## 6. Acceptance gates (presentable state)

boundary edges **0** · boundary loops **0** · non-manifold edges **0** ·
degenerate faces **0** · loose verts **0** · components **1** (or justified) ·
signed volume **> 0** · normals outward · reference dimension recorded ·
before/after audit table in the asset's notes · clay renders front/back/¾.

## 7. Prototype results — Poly Haven lion head

All numbers from the welded working mesh (see §1); stages from `clean2.py`.

| Metric | As delivered | After weld | **Cleaned (final)** |
|---|---|---|---|
| Vertices | 25,380 | 23,611 | **23,442** |
| Faces | 47,214 | 47,214 | **46,880** |
| Boundary edges ("holes") | 3,468 | 0 | **0** |
| Boundary loops | 49 | 0 | **0** |
| Non-manifold edges | 0 | 0 | **0** |
| Degenerate faces | 0 | 0 | **0** |
| Duplicate verts | 1,769 | 0 | **0** |
| Components | 44 | 2 | **1** |
| Signed volume | +0.007221 m³ (incl. disc) | +0.007221 m³ | **+0.005596 m³** |
| Roughness (mean) | 1.103 mm | 0.802 mm | **0.608 mm** |
| BBox (W×D×H) | 320.8 × 206.6 × 436.4 mm | same | **320.8 × 198.1 × 403.5 mm** |

What each stage actually did here:

1. **Weld** did the heavy lifting: −1,769 verts, all 49 "holes" and 42 of 44
   "components" were split-vertex seams. Roughness fell 27% — the visible
   surface noise on this asset *was* seam stepping.
2. **Cull** removed the 169-vert display plinth (§3) — also the reason the
   height "shrank" 33 mm at calibration time.
3. **Hole fill:** no true boundary survived the weld on this asset, so the
   step is validated separately: on a copy of the cleaned mesh we cut a
   985-face (≈50 mm) cheek patch → 53 boundary edges → `holes_fill` →
   **boundary 0, non-manifold 0** (`work/holefill_test.py`). The fill is a
   single flat n-gon (sides=0 behaviour) — fine for a plug, documented in
   §2 as the thing to triangulate + relax on curved areas.
4. **Normals** recalculated outward; signed volume positive throughout.
5. **Denoise:** the guarded Taubin trial returned **8.6% roughness gain at
   0.018% bbox drift — below the 10% gain gate, so it was rejected and NOT
   applied.** The guard working as designed is the result: this carving
   didn't need smoothing once its seams were welded, and forcing it would
   have spent real carved detail for single-digit noise return.
6. **Symmetry:** measured (median 2.9 mm / p90 8.1 mm), not enforced — §4.
7. **Calibration/grounding:** subject seated at z = 0; reference dimension
   recorded (height 403.5 mm). No rescale — source scale verified honest.

### Environment findings worth keeping

- **Blender 5.2's `bmesh.ops.smooth_vert` silently no-ops headless** on this
  build (zero displacement, no error). Our denoise is a numpy Taubin over the
  edge graph instead — deterministic and measurable either way.
- Blender's bundled Python has **no scipy and no PIL**; anything beyond
  numpy must be implemented on numpy or run outside Blender.
- Cycles is the only headless renderer available here (no libEGL), same as
  the rest of the AnthroForge pipeline.

## 8. Sources consulted

- ModelRover, *3D Scan to Printable Model: A Repair-First Pipeline* —
  five-step repair pipeline; hole/manifold/decimation pitfalls.
  https://www.modelrover.com/g/3d-scan-to-printable-model
- Hi3DP, *Best Practices for 3D Scanning and Mesh Repair* — inspect →
  remove islands/spikes → fill holes flow. https://hi3dp.com/blog/best-practices-for-3d-scanning-and-mesh-repair
- MeshLab *Close Holes* guides (copyprogramming.com) — Close Holes size
  parameter counts boundary edges; iterative small-then-large closing;
  *Repair Non-Manifold Edges* for cracks.
  https://copyprogramming.com/howto/closing-hole-in-mesh ·
  https://copyprogramming.com/howto/meshlab-fill-cracks-in-mesh
- Polyvia3D, *Clean Up a 3D Scan* — the five canonical scan defects
  (debris, holes, noise, excess density, degenerate geometry).
  https://www.polyvia3d.com/guides/clean-up-photogrammetry-scan
- Foundry Modo docs, *Symmetrize* — mirror-half enforcement mechanics.
  https://learn.foundry.com/modo/17.1/content/help/pages/modeling/symmetrize_meshop.html
- Hong et al. 2021, *Morphological symmetry of the radius and ulna*
  (PLoS ONE) — real-bone bilateral asymmetry ≈0.5 mm regionally; basis for
  the §4 "mirror damage, don't iron healthy anatomy" rule.
  https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0258232
