# B2 — Retopology Workflow: study + prototype

**Agent B2, AnthroForge model-craft wave (Nov 12, 2026).** Question: how do we turn
sculpt-grade library meshes (100k–2.5M tris, no usable flow) into clean,
animation-ready quad meshes — and what does it cost? Method: study the practical
Blender workflow (manual quad retopo, shrinkwrap discipline, RetopoFlow-style
assisted workflow *conceptually* — RetopoFlow is Joe's paid add-on; nothing was
downloaded), then run one real head through the pipeline end-to-end and measure
what comes out.

**Subject:** "orc head" by demidevil13 (Sketchfab, CC BY) —
`character_assets/orc/…-10-orc_head.zip`. Chosen because it's a true sculpt-grade
case: **855,696 tris**, humanoid head where eye/mouth loop flow actually matters,
and representative of the library's Sketchfab hauls.

---

## 1. The workflow, as studied

Retopology = building a *new* low-poly mesh over the sculpt, following its forms;
the sculpt stays as the detail/bake source. The production sequence, consistent
across every source consulted:

1. **Prep the source.** Duplicate the sculpt into a reference collection; never
   model on it directly. Check Face Orientation + Statistics (tri count, n-gons,
   non-manifold). Symmetrize or note asymmetry before you start.
2. **Set the density budget first.** Hero head ≈ 5–8k quads; full characters
   5–25k polys depending on class. Cage offset (bake distance) 0.5–2% of
   character height. Density goes where it bends — eyelids, lips, nose — not
   uniformly.
3. **Plan loops deformation-first.** Face: 3–4 concentric rings around the mouth
   (orbicularis oris), ~3 around each eye (orbicularis oculi), nasolabial flow
   nose-wing → chin, brow → temple → cheek → jaw highways. Work outward from
   anchor loops (mouth → nose → eyes → brow → ears → jaw → neck); never patch
   isolated islands and stitch later.
4. **Build with surface discipline** (the settings that make it work):
   - New mesh object over the sculpt; **Retopology overlay** on (draws the edit
     mesh toward camera, offset raised when verts sink into the sculpt).
   - **Snapping: Face** as Snap Target for placing single verts; **Face Project**
     as Snap Target *for Individual Elements* when moving whole loops (each vert
     projects along the view ray); **Face Nearest** for hidden areas (between
     fingers, inside mouth). Target Selection: *Include Non-Edited* ON (snap to
     the sculpt), *Include Active* OFF.
   - **Shrinkwrap modifier** on the cage, target = sculpt, Mode: **Project**,
     offset **0.001–0.003** (in metres at human scale; scale-relative: sit the
     cage 0.1–0.5% of head height *proud* on convex detail, never sunken). Keep
     it **unapplied, last in the stack**, during construction; toggle it to check
     the cage-only silhouette still reads.
   - **Poly Build** tool for strip-by-strip construction; F2 for fast face fill;
     LoopTools Relax only on rigid spans. **Mirror** modifier for symmetric
     subjects — retopo half, mirror, done.
   - Display: bright semi-transparent material + *In Front* so the cage reads
     over the sculpt.
5. **Topology rules that survive every method:**
   - 100% quads in deform zones; tris only on flat rigid panels (<2%, never
     adjacent, never at lips/eyelids/joints).
   - Poles: only 3- and 5-poles, placed on flat/hidden/low-stretch areas (back
     of head, under jaw); never across a stretch direction; no edge fans, no
     spirals — the flow must survive Subdivision level 2 without pinching.
   - Density transitions spread over 3–5 quads, never abrupt.
   - Manifold/watertight cage; no doubles, no interior or zero-area faces.
6. **Validate, then hand off.** Quad %, pole census, non-manifold check,
   silhouette vs sculpt, *then* UV unwrap and bake (retopo destroys UVs — the
   sculpt is the bake source for diffuse/normal/roughness).

### RetopoFlow-style assisted workflow (concepts only)

RetopoFlow 4 (Superhive; Joe owns a copy — not downloaded here) is a sketch-based
layer over exactly the discipline above: entering a tool auto-configures
snapping, auto-merge, selection and the retopology overlay. The tools that
matter, and what each replaces in the manual flow:

- **Contours** — sketch a stroke, get a loop wrapped around a cylindrical form
  (neck, limbs, muzzle). Replaces hand-placing anchor loops.
- **PolyStrips** — draw a ribbon of quads along a flow line (the brow→temple→
  cheek highways). Replaces extrude-and-fill strip building.
- **PolyPen** — place/move individual verts/quads for detail areas.
- **Patches** — auto-fill the region bounded by finished strips.
- **Relax** — smooths flow *along* the surface (vs LoopTools Relax in 3D).
- Symmetry mode mirrors strokes live.

Reported effect: loops land where a human would put them, ~2–3× faster than
Poly Build alone; the judgment (loop plan, pole placement) is unchanged — the
tool accelerates placement, not decisions.

### Time cost (literature)

| Method | Character head | Source basis |
|---|---|---|
| Manual Poly Build + Shrinkwrap | **2–6 h** (competent artist) | practitioner guides |
| RetopoFlow assisted | **1–2 h**, hero head "a few hours" incl. learning curve | guides + user reports |
| Automatic (QuadriFlow/ZRemesher class) | **2–10 min** + cleanup; quality = base mesh, not final | guides |
| Full hero character incl. UV + bake | **1–3 days** | practitioner guides |

Rule of thumb the sources converge on: **if it animates, lean manual (or
auto + manual fix-up of deformation zones); if it's static or a bake base,
automatic is enough.** Our prototype below is the hybrid: automatic base +
shrinkwrap pin + measured validation, with the deformation-zone caveat stated
plainly.

---

## 2. Prototype — what was actually run

Pipeline (Blender 5.2.3 headless, scripts in `work/`): the hybrid chain from §1 —
**join → voxel remesh proxy → QuadriFlow → Shrinkwrap pin → measured validation**.
No hand-placed loops: this tests the *automatic base* tier honestly, with the
manual/RetopoFlow pass as the known follow-up for deformation zones.

**Source prep finding:** the Sketchfab GLB is not one mesh — it's **9 chunk
objects of ≤65,532 verts each** (an exporter vertex cap), all sharing one
material and one coordinate space, seams duplicated (573,148 verts unwelded;
427,850 after a weld). Object-mode join concatenates them; the weld turned out
to be *unnecessary* — the voxel stage is volumetric and deviation treats the
union surface identically — and skipping it removed the single biggest memory
spike of the run. Worth remembering for every Sketchfab haul in the library.

| Stage | Setting | Time |
|---|---|---|
| glTF import (33 MB .bin) | — | 52 s |
| Join 9 chunks | object mode, no weld | ~5 s |
| Voxel remesh proxy | voxel size = height/180 = 0.551 u | 96 s |
| QuadriFlow | target 6,000 faces, smooth normals | 169–202 s |
| Shrinkwrap pin | NEAREST_SURFACEPOINT → sculpt, applied | 2 s |
| Deviation measurement | 17,435 surface samples, BVH | 52 s |
| Renders | Cycles, 512², ~8 samples | ~1 min/view |

Machine total ≈ **15–20 min** end-to-end on this shared VM, unattended.

### Result mesh

| | Sculpt (joined) | Retopo |
|---|---|---|
| Faces | 855,696 tris | **5,811 quads (100%)**, 0 tris, 0 n-gons |
| Verts | 427,850 (welded count) | 5,813 |
| Manifold | watertight | **watertight, 0 non-manifold, 0 boundary edges** |
| Poles | — (tri soup) | 80 × 3-pole, 72 × 5-pole, **0 poles ≥6** |
| File | 31 MB GLB | **210 KB GLB** |

Face reduction **147×** (98.6%). Pole count (152 total) is in the normal band
for a closed quad head of this size; QuadriFlow scattered them by curvature
rather than by anatomy — see limits below.

### Deviation from the sculpt (the honesty numbers)

Measured against the **full 855,696-tri sculpt**, 17,435 samples (every cage
vertex + every face centre + one random in-face point per face), closest-point
BVH distance. Head height = 99.15 u (≈24 cm at human scale, so 1 u ≈ 2.4 mm):

| | mean | median | p95 | p99 | max |
|---|---|---|---|---|---|
| distance (units) | 0.057 | 0.022 | 0.235 | 0.432 | 1.642 |
| % of head height | **0.058%** | 0.022% | 0.237% | 0.435% | 1.656% |
| ≈ mm at human scale | 0.14 | 0.05 | 0.57 | 1.04 | 3.97 |

Vertex deviation is exactly 0.000 — by construction (the Shrinkwrap pin puts
every cage vertex *on* the sculpt), so the sampled-surface row above is the
real measure: the quad surface spanning between pinned verts bows off the
sculpt by ~0.06 u on average. The max (1.64 u) sits at the sharpest extremity
(tusk/ear-tip class geometry), where one quad spans what the sculpt does in
hundreds of tris.

**Silhouette deviation** (ortho renders, alpha-mask comparison, 512²; "before"
rendered from a 150k-tri render-decimation of the sculpt — see process notes):

| View | IoU | boundary offset mean | p95 | max |
|---|---|---|---|---|
| back (−Y) | 0.978 | 1.33 px (0.26%) | 6.4 px | 18.4 px |
| profile (+X) | **0.992** | 0.58 px (0.11%) | 2.0 px | 21.9 px |
| top (+Z) | 0.988 | 0.76 px (0.15%) | 2.9 px | 11.3 px |

Mean silhouette error is ~1 px at 512² everywhere; the double-digit maxima are
single thin extremities (tusk/ear tips again) where the cage legitimately
rounds what the sculpt spikes.

### What it looks like

Clay renders (`renders/before_*` vs `renders/after_*`) read as the same bust:
topknot, brow mass, ear, tusk and shoulder flare all land. What the cage drops
is *surface* detail — hair strands, skin cracks, pore-level sculpt — which is
exactly the split §1 predicts: that detail belongs in baked normal/diffuse maps
from the sculpt, not in the cage. The wireframe plot
(`renders/retopo_wireframe.png`) shows QuadriFlow's even, curvature-following
grid with a visible flow concentration around the ear.

### Limits — stated plainly

1. **This is a bake-ready cage, not a finished animation head.** QuadriFlow
   does not place anatomical loops: there are no deliberate concentric rings
   around the eyes/mouth, and poles sit where curvature put them, not where
   §1's rules want them (flat/hidden areas). For a *hero* head, the follow-up
   is the manual discipline from §1 — or Joe's RetopoFlow: Contours for the
   eye/mouth rings, PolyStrips to re-route the brow→cheek highways, Relax,
   ~1–2 h by the literature's clock. For background heads, body parts, and
   bake bases, this output is shippable as-is.
2. **No UVs, no bake** were produced (retopo destroys the source UV layout by
   design; unwrap + bake is the next pipeline stage, not part of this test).
3. **Symmetry was not enforced** (QuadriFlow symmetry off): the sculpt is
   near-symmetric (X bounds −32.63/+32.69) but the cage is free-running, so
   mirrored-UV workflows would need a symmetrize pass first.

### Process notes (for whoever reruns this)

- **Run long Blender jobs as systemd services, not shell background jobs** —
  worker-scoped processes get SIGKILLed on session teardown (happened twice),
  and a combined render pass over the 856k sculpt OOM-killed at Cycles BVH
  build. The staged design (one object per render process; sculpt rendered
  via a 150k-tri render decimation) exists because of that kill.
- **BVHTree.FromObject measures in LOCAL space.** The sculpt hangs under a
  rotated `Geode` parent (glTF Y-up→Z-up); world-space sample points returned
  a plausible-looking but entirely bogus mean deviation of 6.9 u before the
  frame error was caught by a self-distance control (a mesh's distance to its
  own surface must be 0 — in local space it is exactly 0.0). *Always* run the
  self-distance control before trusting a deviation number.
- Blender 5.2's glTF exporter takes `use_selection`, not `export_selected`;
  and **save the .blend before exporting anything** — an exporter exception
  otherwise takes the finished geometry with it (happened once).
- Direct QuadriFlow on the raw 856k sculpt never completed; the voxel proxy
  (105,460 watertight quads) is what makes QuadriFlow tractable, and because
  the shrinkwrap pin + all measurements run against the *original* sculpt,
  the proxy costs no honesty.

### Deliverables

- `orc_head_before.glb` — the joined sculpt (855,696 tris, 31 MB)
- `orc_head_retopo.glb` — the cage (5,811 quads, 210 KB)
- `orc_head_retopo.blend` — both meshes in one scene
- `renders/` — before/after clay (back, profile, top) + retopo wireframe plot
- `work/stats.json` — every number quoted above, machine-readable
- `work/stage*.py` — the full pipeline, rerunnable

---

## Sources

- Blender Manual via geturna.com guide (menu names checked against Blender 5.2):
  https://geturna.com/en/guides/retopology-blender
- blenderdeluxe.com, "Blender Retopology: Build a Mesh Ready to Animate" (5.2):
  https://blenderdeluxe.com/en/3d-design/retopology-in-blender-52-from-dense-sculpt-to-animation-ready-mesh-1113
- Saved Pixel, "Blender Retopology in 2026: Methods, Addons, Faster Workflows":
  https://savedpixel.com/blog/blender-retopology-complete-guide/
- Neural4D, "Blender Retopology: How to Fix Bad Topology in AI 3D Models"
  (time-cost table): https://blog.neural4d.com/user-guide/blender-retopology-ai-3d-models/
- RetopoFlow 4 product page (tool concepts):
  https://superhivemarket.com/products/retopoflow?ref=discover-the-rookies
- StraySpark, "Best Blender Retopology Addons in 2026":
  https://www.strayspark.studio/blog/best-blender-retopology-addons-2026
