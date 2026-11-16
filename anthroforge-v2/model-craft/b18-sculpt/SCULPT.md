# SCULPT.md — Sculpting Tools & Workflow for AnthroForge

**Agent B18, model-craft wave, Nov 12–13, 2026.** Question: how does sculpting
work in this pipeline — which brushes do what, which topology strategy
(dyntopo / remesh / multires) belongs at which stage, and — the constraint
that decides everything here — **what can a scripted, headless Blender
actually do on this VM, where no interactive Blender session exists?**

Method: workflow study (§1–§5), then **two probe runs against the real
binary** (Blender 5.2.3 LTS, `blender -b`) that executed the actual
operators and logged what happened (§6 — this section is measured, not
researched), then one scripted sculpt prototype on the B10 wolf torso
blockout (§7). Scripts, probe logs and results: `work/`. Prototype:
`prototype_sculpt.blend`, renders in `renders/`.

Evidence labels: **[P]** = proven by a probe/prototype in this run ·
**[D]** = documented Blender behaviour, not re-proven here ·
**[E]** = estimate / practitioner consensus.

---

## 1. Where sculpting sits in the AnthroForge pipeline

Sculpting is the **form-authoring stage between blockout and retopo**, and
— the rule B2 already established — the sculpt is a *source*, never the
shipping mesh:

```
B10 blockout (primitives, proportions proven)
  → SCULPT (primary → secondary → detail form; symmetry measured)
  → B2 retopo (clean quad cage shrink-wrapped to the sculpt; sculpt = bake source)
  → UV / bake / rig (B17 gates) → B20 critique (§3.3 Anatomy judges this stage's output)
```

Two side-doors feed the same stage:

- **Scans / library sculpts enter through B19 cleanup first** (weld → cull →
  fill → guarded denoise), and B19's denoise step *is* a sculpt-adjacent
  operation (Taubin smoothing with a measured acceptance gate). A scan that
  needs form repair (a crushed muzzle, a missing ear tip) gets it here, in
  sculpt, after cleanup — never before the weld/audit.
- **Slider/parts work does not sculpt.** Morph fields and parts are built by
  the slider/parts machinery; sculpting is for one-off hero form and for
  authoring the *reference* a field is derived from.

The B20 rubric is this stage's acceptance review: §3.3 Anatomy scores
"primary forms present and placed over the skeleton they imply; secondary
form where the style promises it" — a sculpt pass is done when the
silhouette (§3.1) and anatomy (§3.3) evidence says so, not when it feels
finished.

## 2. Brush roles — what each one actually does

A brush is a falloff field + a deformation rule + a stroke. Naming the rule
matters here because §6 shows the *rule* is what survives headless, even
when the operator doesn't.

| Brush | Deformation rule | Stage / anthro use | Scripted equivalent |
|---|---|---|---|
| **Draw / Draw Sharp** | Displace along averaged normal inside radius; Sharp uses a pinched falloff for crests | Secondary form: muscle bellies, brow ridges, lip line | Normal displacement, Gaussian/smoothstep falloff **[P]** |
| **Clay / Clay Strips** | Displace along a *plane* (not the normal) up to a height cap — builds flat-topped mass without inflating; Strips = rectangular footprint laid in overlapping stamps | **Primary-form workhorse.** Pectorals, deltoids, thigh mass, muzzle planes. Strips read as faceted "clay" until smoothed | Plane-clamped displacement along an elongated stroke footprint, layered passes **[P]** (prototype S1 approximates with normal displacement — see limits) |
| **Inflate** | Displace along each vertex's own normal — volume gain, rounds everything | Belly, cheeks, paw pads, fat tissue over muscle (the Tissue layer of skull→muscle→tissue) | Per-vertex normal displacement, radial falloff **[P]** (prototype S2) |
| **Blob / Crease** | Blob: spherical push in/out. Crease: pinch + push-in combined → sharp valleys | Crease: nasolabial fold, mouth line, between toes, ear fold | Pinch field + negative displacement (below) |
| **Pinch** | Pull verts toward the stroke centreline — sharpens an edge without adding/removing height | Ridge definition: spine line, jaw edge, claw bases | Pull toward a curve/plane by falloff × factor **[P]** (prototype S4) |
| **Scrape / Fill** | Pull verts toward the brush plane — levels an area to a flat (Scrape) or fills valleys to the plane (Fill) | Planar anatomy: forehead plane, back topline, plantar surfaces, muzzle top | Project toward a plane by falloff inside a band **[P]** (prototype S3) |
| **Smooth** | Laplacian relaxation toward neighbour average; preserves volume better than mesh smooth at low strength | Everywhere, constantly: kill faceting between clay strips, soften transitions — *not* a finishing-only step | Masked Laplacian iterations **[P]** (prototype S5) |
| **Grab / Elastic Grab** | Move a region rigidly-ish with a soft falloff (Elastic adds rubber-band lag) | Proportion correction *inside* sculpt: drag an ear base, pull a belly down, reposition a mass before committing | Translation field with smooth falloff (trivially scriptable) |
| **Move / Pose** | Move: free displacement along the stroke. Pose: bend/twist a limb-like region around pivots with falloff chains | Pose = quick pose studies, tail curve checks. Move = large clay relocation | Translation/rotation fields about a pivot |
| **Snake Hook / Thumb** | Pull surface out along stroke direction with pinch (Hook) / push mass sideways (Thumb) | Horns, tails, ear tips, tongue; Thumb for nudging a mass sideways into place | Directional displacement along a path |
| **Flatten / Contrast** | Flatten = scrape toward local average plane; Contrast = push verts away from local average (sharpens *and* flattens) | Final planar cleanup; Contrast for stylised reads | Plane projection (local fit) |
| **Mask / Draw Face Sets** | Not deformation — *selection as data*. Mask protects areas from every brush; face sets partition the mesh for per-part operations | Mask the eyes/teeth while sculpting the head around them; face sets per muscle group for isolated passes | **Data-level, fully scriptable** — `.sculpt_mask` (per-vertex float) and `.sculpt_face_set` (per-face int) attributes **[P]** |
| **Trim / Line Project** | Boolean-cut the sculpt against a drawn shape/plane | Rare for organics; hard cuts for props, horn bases | Boolean modifier (object mode) **[D]** |

Pass order that production converges on, and that the prototype follows:
**build up (clay) → add volume (inflate) → level (scrape) → define
(pinch/crease) → soften transitions (smooth, masked)** — big-to-small,
same discipline as B10 blocking, one scale down.

## 3. Topology strategy — dyntopo vs voxel remesh vs multires

All three answer "where does sculpt resolution come from?" They are not
interchangeable; the decision is per-stage:

| | Dyntopo | Voxel remesh | Multires |
|---|---|---|---|
| Mechanism | Retriangulates locally under the brush, detail size per stroke | Rebuilds the whole mesh as a uniform voxel surface (openVDB) | Subdivides a base cage (Catmull-Clark levels); displacement stored per level |
| Topology | Triangles, adaptive, messy | Uniform quads-ish grid, watertight, **destroys flow/UVs/groups** | The base cage's own flow — survives to export |
| Symmetry | Mirror option per axis | Grid-symmetric if the source is **[P]** (§7) | As symmetric as the cage |
| Best stage | **Concept / primary form** on a human's machine: start from a blob, density follows the work | **Stage transitions**: fuse blockout primitives (§7), repair scans (B19's re-shell option), make a sculptable substrate from anything | **Detail stage on a near-final cage**: pores, fine wrinkles — and the *only* strategy whose detail bakes cleanly to the low cage |
| Failure mode | Runaway density, lumpy mids, unusable for export directly | Uniform density = wasteful at detail scale; erases thin features below voxel size (ear tips!) | Can't change proportions or fuse parts; stretching the cage past its flow tears detail |
| Headless on this VM | Toggle operator executes **[P]** — but there is no stroke to feed it (§6), so **unusable here** | **Operator works headless** **[P]** — the scripted pipeline's substrate tool | Subdivide operator works headless **[P]**; sculpting *on* the levels needs strokes, so here it's a container, not a tool |

**Decision rules (house):**

1. Blockout → sculpt: **voxel remesh** to fuse (0.5–1% of body length;
   §7 used 18 mm ≈ 1.9% of torso length — coarse end, primary forms only).
   Check thin features against voxel size first; if ears/horns would melt,
   sculpt them as separate shells and fuse later (the B14 pattern).
2. Form exploration with a human at a real Blender: dyntopo, detail size
   relative, constant passes of voxel remesh to reset lumpiness.
3. Once retopo exists and proportions are locked: **multires on the cage**
   for detail; sculpt never again touches raw topology.
4. Never dyntopo/remesh an asset that already has UVs, weights, or morphs
   you intend to keep — all three strategies either destroy or invalidate
   them (remesh explicitly; dyntopo by retriangulation; multires is the
   exception *because* it keeps the cage).

## 4. Sculpt layers, face sets, masks — the honest Blender position

- **Blender has no sculpt layers.** ZBrush-style per-layer displacement
  (sculpt a "fat" layer and a "scar" layer, blend their strengths) does
  not exist natively in Blender 5.2 **[D]**. The house substitutes, in
  order of preference:
  1. **Versioned snapshots** — one `.blend` (or object copy) per pass/stage,
     which is what our wave workflow already does everywhere (B19's
     trial-on-a-copy rule is the same instinct). Crude, auditable, works
     headless. **[P]** (prototype keeps fused + sculpted objects side by side)
  2. **Shape keys as pseudo-layers** — sculpt on a key, slide its value to
     blend. Works on a fixed topology (post-retopo cage); conflicts with
     Multires (a known, long-standing limitation — keys and multires
     displacement do not compose freely) **[D]**. Use for expression/morph
     authoring (B16's territory), not for the multires detail stage.
  3. **Face-set partitioning** — isolate regions per pass; the closest
     thing to layers for *organisation* (not blending).
- **Face sets are data**: a per-face integer attribute (`.sculpt_face_set`),
  creatable and writable from a script with a verified round-trip **[P]**.
  Scripted passes should *write* face sets as they go (one set per stroke
  region) so a later interactive session — on Joe's machine, or a future
  one — inherits the organisation. The sculpt-mode *operators* that manage
  face sets are a different story: §6.
- **Masks are data** the same way: per-vertex float (`.sculpt_mask`) **[P]**.
  A scripted field pass should honour and emit masks exactly like a brush
  does (prototype S5's touch-mask is the same idea, kept as a Python list —
  next iteration should write it into `.sculpt_mask` proper).

## 5. Symmetry workflow

- **Measure before enforcing** — B19's policy, adopted whole: mirror-sample
  the asset; symmetrize anatomy (skulls, body bases) where asymmetry is
  damage, leave authored asymmetry (a carving's mane, an expression) alone.
  Real bone carries ~0.5 mm regional asymmetry; ironing a healthy asset
  flat is a defect, not a fix.
- Interactive: brush Mirror (X/Y/Z, plus radial) and Topology Mirror for
  dyntopo; Edit-mode **Symmetrize** and the Mirror modifier for cages.
  Symmetrize runs headless in Edit mode **[P]** — it's an object/edit tool,
  not a viewport tool.
- **Scripted passes get symmetry by construction**: build every falloff
  field as a function of |x| (resp. the symmetry axis) and both sides
  receive the identical delta; §7 measured the residual at < 0.005 mm on
  sampled points (the voxel substrate was itself grid-symmetric). This is
  *stronger* than brush mirror, which only mirrors stroke placement over
  an independently-triangulated dyntopo surface.
- Retopo keeps its own symmetry discipline (B2: retopo half, Mirror
  modifier) — the sculpt being symmetric does not excuse an asymmetric cage.


## 6. Headless reality — the probe matrix (measured, this VM, Blender 5.2.3)

Two probe scripts (`work/probe_headless.py`, `work/probe2_one.py`), run
with `blender -b --factory-startup`. Risky operators were re-run **one per
process under a shell timeout** after the combined run segfaulted — which
turned out to be the most important result in the table:

| Operation | Headless result | Evidence |
|---|---|---|
| `object.mode_set(mode='SCULPT')` | ✅ **works** — sculpt mode can be entered | probe 1 |
| `sculpt.brush_stroke` | ❌ **refused**: `RuntimeError: Operator bpy.ops.sculpt.brush_stroke.poll() failed, context is incorrect` | probe 2 (isolated) |
| `sculpt.mesh_filter` (SMOOTH) | 💥 **SEGFAULT** (exit 139, crash dump, no Python exception) | probe 2 (isolated) |
| `sculpt.face_sets_init` | 💥 **SEGFAULT** (exit 139) | probe 2 (isolated) |
| `sculpt.dynamic_topology_toggle` | ⚠️ executes without exception — but useless: nothing can feed it strokes | probe 1 |
| `object.voxel_remesh` | ✅ **works** (cube 8 → 152 verts; prototype torso 1,446 → 3,924) | probes 1–2, §7 |
| `object.quadriflow_remesh` | ✅ **works** (386 → 225 verts) — the B2 automatic-retopo route is scriptable too | probe 2 |
| `object.multires_subdivide` | ✅ **works** (`total_levels=1` after one call) | probe 1 |
| `.sculpt_face_set` / `.sculpt_mask` attributes | ✅ **work** — create + write + read-back round-trip | probe 1 |
| `mesh.symmetrize` (Edit mode) | ✅ **works** | probe 1 |
| Context facts | `bpy.context.window` **exists** in `-b` but has **zero areas** (`areas=[]`) — there is no VIEW_3D region for a stroke to land in. That absence is the root cause of the refusals above | probe 1 |

**Reading the matrix — three tiers, and the middle one is dangerous:**

1. **Object/Edit-mode machinery works.** Remesh, QuadriFlow, multires
   levels, symmetrize, joins, modifiers, rendering — the whole
   substrate-and-finish toolbox is scriptable.
2. **Viewport operators refuse or crash.** Anything whose poll needs a 3D
   Viewport (brush strokes) fails cleanly — but some sculpt-mode operators
   that *don't* check properly (mesh filter, face-sets init) **segfault
   the whole process**. A naive headless pipeline that calls them dies
   silently mid-run with no exception to catch. House rule, learned here
   and consistent with what B2's run hit: **any unproven sculpt-mode
   operator runs one-per-process, under a timeout, behind a saved
   checkpoint** — or doesn't run.
3. **Data-level sculpting works and is the actual answer.** Brushes are
   falloff fields with deformation rules (§2); every rule in the table
   there has a direct mesh-data implementation, and §7 proves the chain
   end-to-end. What this route cannot reproduce, stated plainly:
   - **Stroke dynamics** — pressure/tilt curves, build-up *during* a
     stroke, anchored/space stroke spacing, the artist's mid-stroke
     corrections. Scripted passes are **batch**: define fields → run →
     render → critique (B20 panels) → adjust numbers → re-run. Slower per
     iteration than a hand, perfectly repeatable, and every number is in
     the script — which suits this workspace's evidence-first workflow.
   - **Surface-dragging brushes** — real clay/snake-hook strokes drag
     material *along* the surface. Data fields displace mostly along
     normals; elongated masses read slightly "inflated" next to
     hand-dragged ones (visible in §7's prototype if you look for it).
   - **Dyntopo's adaptivity** — sculpt density following the work. The
     scripted substitute is staged remeshing (remesh finer → re-apply /
     continue), which is global, not local.
   - **Interactive-only tools** — Trim/Line, lasso face sets, pose brush
     gizmos, stencil/alpha painting mid-stroke: no headless path, don't
     fake one.

## 7. Prototype — one scripted sculpt pass on the B10 wolf torso

`work/proto_sculpt.py`, 32 s wall clock end-to-end, `--threads 2`.
Subject: B10's `Chest` + `Belly` + `Pelvis` primitives (the torso masses;
the blockout's axes: X = body length, Y = lateral, Z = up).

**Stage B — substrate.** Join (1,446 verts) → transforms applied →
`voxel_remesh` at 18 mm → **3,924 verts / 3,922 faces**, one watertight
shell, volume 0.05091 m³. Renders: `renders/before_blockout_side.png`
(primitives), `before_sculpt_side.png` / `before_sculpt_34.png` (fused:
three ellipsoid lumps, stepped topline, visible fusion seams).

**Stage C — the pass** (order = §2's production order; all fields
|y|-symmetric by construction):

| Stroke | Brush analogue | Field | Measured result |
|---|---|---|---|
| S1 | Clay strips | 3 layered passes along two chest-side bands (r = 75 mm) | ≈1,210 verts/pass; ≤4.5 mm per pass, 7.65 mm mean cumulative on touched verts — shoulder/pec mass |
| S2 | Inflate / gravity sag | Ellipsoid falloff at the belly, direction = 0.55·normal + 0.75·down | 440 verts, max 20.0 mm — belly drops and rounds |
| S3 | Scrape | Dorsal band pulled 55% toward plane z = 0.795 | 756 verts, max 18.5 mm — the stepped topline becomes one level line |
| S4 | Pinch / Crease | Flank tuck at x = −0.20: pull toward groove plane + 6 mm inward | 250 verts, max 10.5 mm — a readable tuck crease behind the ribs |
| S5 | Smooth | Masked Laplacian, 3 iterations, λ = 0.35 × touch-weight | 2,312 verts blended — fusion seams and strip faceting soften, forms kept |

**Outcome, measured:** volume 0.05091 → **0.05377 m³ (+5.62%)**; bbox
0.936 × 0.258 × 0.397 → 0.936 × **0.273** × **0.378** m (wider from the
clay mass; lower because the scrape's levelling outweighs the sag);
**symmetry residual < 0.005 mm** (median and p90, 250 KD-tree mirror
samples — at float rounding; substrate and fields were both symmetric).
Renders `after_sculpt_side.png` / `after_sculpt_34.png` show it: level
topline, hanging belly line, tuck crease, one continuous barrel instead of
three lumps. Both objects (fused, sculpted) are kept in
`prototype_sculpt.blend`; numbers in `work/proto_results.json`.

## 8. Per-stage tool table — AnthroForge standard

| Pipeline stage | Interactive tool (human machine) | Scripted route (this VM) | Verdict |
|---|---|---|---|
| Fuse blockout / scan → substrate | Voxel remesh, dyntopo | `object.voxel_remesh` **[P]** | Scripted — solved |
| Primary forms | Clay Strips, Grab, Scrape | Stroke fields along station lines (B10 stations give the coordinates) **[P]** | Scripted — proven §7 |
| Secondary forms | Draw, Inflate, Pinch, Crease | Falloff fields per muscle group; face sets written per region **[P]** (fields) | Scripted — same math, finer fields |
| Tertiary detail (pores, fine wrinkles) | Multires + Draw Sharp / alpha brushes | **No honest route** — needs strokes on multires levels | **Interactive only.** Park detail for a human session; do not simulate |
| Pose/expression studies | Pose brush, Elastic Grab | Bone posing (rig exists) or rotation fields for a look-dev still | Scripted approximation acceptable for studies, never for shipped form |
| Scan form repair | Clay/Scrape over B19-cleaned mesh | Field repair for *measured* defects (dent depth known from audit); artistic repair = interactive | Split verdict by defect type |
| Organisation | Face sets, masks | Attribute writes **[P]** | Scripted — solved |
| Symmetry enforcement | Brush mirror, Symmetrize | Symmetrize op **[P]** / symmetric fields **[P]** | Scripted — solved |

## 9. Honest limits

- **The prototype is primary-form only, by construction.** 3,924 verts at
  18 mm voxels cannot hold secondary form; the after-renders are visibly
  faceted. A production scripted pass would remesh at 6–10 mm (≈25–60k
  verts on this torso — the field math is unchanged, the run is still
  seconds) or accept dyntopo's absence and stage two remesh resolutions.
- **S1 approximates Clay Strips with normal displacement**; true clay
  displaces along a plane with a height cap and *does not* round the
  strip. The difference reads at close range (our strips are softer). A
  plane-clamped variant is a small change to the field function — noted,
  not done.
- **S3's scrape plane is world-Z.** A real scrape follows the brush's
  local plane; on a curved topline the scripted version needs a fitted
  plane per band (least-squares over the band's verts) — same caveat.
- **No stroke was ever executed.** §6 is unambiguous: every claim about
  "scripted sculpting" in this document means data-level field
  deformation, proven in §7 — not Blender's brush engine driven remotely.
  Any future agent claiming to "run the brushes headless" should be
  asked for its probe log.
- **The segfaults are Blender 5.2.3-specific observations** on this VM's
  build; another build may refuse politely instead. The one-per-process
  rule is cheap insurance either way.
- Renders are Workbench clay at 640×480 — B20-style evidence (silhouette /
  anatomy read), not beauty shots; judged as such.

## 10. House rules distilled

1. Sculpt is a **source stage**: blockout → sculpt → retopo (B2); the
   shipping mesh is never the sculpt.
2. On this VM, sculpting is **batch field work**: numbers in a script,
   renders as evidence, B20 rubric as the gate. Tertiary detail is
   interactive-only and gets scheduled as such, not faked.
3. **Unproven sculpt-mode operators run one-per-process under a timeout,
   behind a checkpoint** — two of them segfault headless (§6).
4. Every scripted pass **writes its organisation** (face sets / mask
   attributes) so a later interactive session inherits it.
5. Symmetry is **measured, then enforced by construction** (symmetric
   fields) or by op (Symmetrize) — per B19's anatomy-only policy.
6. Topology strategy is chosen per stage (§3): remesh to fuse, dyntopo
   to explore (human machines), multires to detail a locked cage.
