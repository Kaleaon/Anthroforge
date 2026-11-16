# WEIGHT CRAFT — weight-painting technique mining + robust weight transfer evaluation

Sources Joe supplied Nov 12, 2026, back-to-back with the paintable-weights /
realistic-gravity push:

- **A.** The Royal Skies, *“Blender 4.0 — Weight Paint Workflow (& Techniques!!)”*
  — https://www.youtube.com/watch?v=PLWv9yjVaoU
- **B.** `sentfromspacevr/robust-weight-transfer` (GitHub) — Blender add-on
  implementing *Robust Skin Weights Transfer via Weight Inpainting*
  (Abdrashitov et al., SIGGRAPH Asia 2023).
- **B2.** cvELD Edit Paint, via 80.lv — paid add-on adding advanced
  weight-painting tools to Blender.

Companion docs: `autoskin-prototype/AUTOSKIN.md` (our B+ geodesic+guards
baseline and its pose metrics), `first-proof/GRAVITY_WEIGHTS.md` (the
AF_mobility paintable field and its §3.2 brush semantics).

---

## Part A — The Royal Skies video: what we could and couldn't extract

**Access report (plainly): the transcript could not be obtained.** Every
sanctioned route was tried, in order:

1. **yt-dlp** (fresh venv install, subtitles only): YouTube answered
   *“Sign in to confirm you're not a bot”* after an HTTP 429 on the watch
   page. No cookies were used and none were fabricated.
2. **Timedtext endpoints** (`api/timedtext?type=list`, `kind=asr`,
   `video.google.com/timedtext`): empty responses — no caption track list
   is served to this network.
3. **Transcript mirror** (youtubetotranscript.com): HTTP 429.

So the list below is **not a transcript**. Each item is tagged:
`[desc]` = stated in the video's own description/title ·
`[author]` = corroborated from Royal Skies' own published micro-tutorials ·
`[manual]` = the stock Blender weight-paint operation the workflow is built
on (Blender Manual, retrieved verbatim) — included because it's the toolset
the video teaches, not because we heard him say it in this video.

The video's promise, from its description `[desc]`: *“Here are ALL the
tricks I use to weight-paint new character easily and FAST.”* The through-line
is speed: block weights in with fills and gradients, fix with blur/levels,
never hand-paint what an operator can do.

### Technique list

| # | Technique | When it's used | Gist |
|---|---|---|---|
| 1 | **Projected brush falloff** `[author]` | Painting thin/double-sided regions (legs, fingers, cloth) | Brush falloff → **Projected** so a stroke paints *through* the mesh and weights the back side in the same pass — his signature fix for “the backside never gets painted.” |
| 2 | **Auto Normalize on, always** `[manual]` | Entire session | Options → Auto Normalize keeps every vertex's deform weights summing to 1 *while* you paint, so no cleanup pass is owed later. |
| 3 | **Fill / Set Weight to block in** `[manual]` | Start of any bone's pass | Fill the active group with the current paint value over a selection instead of brushing large areas (Set Weight, `Ctrl`+`X` in the manual's shortcut table). Block first, blend second. |
| 4 | **Linear Gradient tool for joints** `[manual]` | Elbows, knees, fingers, jaw hinge — anywhere influence must ramp along a limb | Weights → Gradient (Linear), `Shift`+`A`: drag across the joint; the field ramps from the paint value to 0 along the drag instead of being feathered by hand. |
| 5 | **Radial Gradient for point influences** `[manual]` | Shoulder/hip balls, breast, belly button region | Gradient (Radial), `Shift`+`Alt`+`A`: click-drag outward from the influence centre. |
| 6 | **Blur brush as the default second pass** `[manual]` | After every block-in | Blur averages a vertex with its neighbours — the fast way to kill steps and spikes without repainting. (Our graph-Laplacian “Smooth” brush in GRAVITY_WEIGHTS §3.2 is the same op.) |
| 7 | **Smooth operator on a selection** `[manual]` | Local harsh transitions | Weights → Smooth blends selected verts toward adjacent unselected ones — a targeted blur that respects a selection boundary. |
| 8 | **Clean with a threshold** `[manual]` | End of every bone pass | Weights → Clean removes sub-threshold assignments (e.g. < 0.01–0.2), killing the stray 2% influences that cause mystery deformation. |
| 9 | **Levels (gain/offset)** `[manual]` | A bone's falloff is right in shape but wrong in reach | Weights → Levels scales/offsets the whole group: widen or tighten an influence without repainting its shape. |
| 10 | **Normalize / Normalize All** `[manual]` | After any non-normalized edit (fills, levels, transfers) | Per-vertex sum back to exactly 1, locked groups untouched. |
| 11 | **Mirror weights + Topology Mirror** `[manual]` | Symmetric characters — paint one side only | Mirror the group across X; Topology Mirror handles meshes that aren't perfectly symmetric. Companion trick: copy group → rename to the opposite bone → Mirror = “mirror to opposite bone.” |
| 12 | **Vertex-group locking** `[manual]` | Protecting finished bones while painting neighbours | Locked groups are skipped by Normalize/Clean and by painting spill — the guardrail that makes multi-bone sessions safe. |
| 13 | **Multi-Paint** `[manual]` | Adjusting a *blend* (e.g. spine chain) as one unit | Several bones selected are treated as one while preserving their internal ratio. |
| 14 | **Quantize (use sparingly)** `[manual]` | Stepped/mechanical influences, or matching a target engine's precision | Snaps weights to discrete steps; destroys smooth ramps, so it's a finishing op, not a painting op. |

**What this validates for us:** the discipline is *operators first, brush
second* — fills, gradients, blur, levels, clean, normalize, mirror, lock.
That is precisely the op set a paint mode needs; freehand brushwork is the
exception path, not the workflow.

---

## Part B — Robust Weight Transfer (`sentfromspacevr/robust-weight-transfer`)

### What it is

A Blender add-on (v1.1.9, `bl_info` minimum Blender 3.1.0) wrapping the
SIGGRAPH Asia 2023 paper *Robust Skin Weights Transfer via Weight
Inpainting*. One click: pick a skinned source object, run on target(s).

### The algorithm — why “robust” is earned

Blender's built-in Transfer Weights / Data Transfer is pure **closest-point
copy**: every target vertex takes the barycentric-interpolated weights of
the nearest source triangle. That is exactly what breaks between legs, in
armpits, and across the chest — the nearest surface is often the *wrong*
surface, and there is no recovery.

RWT keeps closest-point only where it is *trustworthy*, and solves for the
rest:

1. **Gated matching.** For each target vertex, find the closest point on the
   source surface (libigl `point_mesh_squared_distance`) and barycentrically
   interpolate weights *and* normals there. Accept the match only if
   **distance ≤ threshold** (default 0.05 scene units) **and** the
   interpolated source normal agrees with the target normal within an
   **angle threshold** (default 30°; a “flip normal” option also accepts
   ~180°, for solid meshes whose normals point inward).
2. **Biharmonic inpainting.** Unmatched vertices get their weights by
   solving a biharmonic system on the **target's own connectivity**
   (`igl.min_quad_with_fixed` on Q₂ = −L + L·M⁻¹·L, matched verts as fixed
   Dirichlet values). Weights therefore *flow along the target surface*
   from good matches instead of being copied across gaps — an inner-thigh
   vertex is filled from thigh matches, not from the other leg.
3. **Robust Laplacian.** The system is built with `robust_laplacian`
   (Sharp & Crane), which tolerates the non-manifold / messy geometry that
   makes the classic cotan Laplacian explode. Two modes: **SURFACE** (mesh
   Laplacian, flow stays inside each loose part) and **POINT** (point-cloud
   Laplacian on an internal remesh — weights can flow between disconnected
   parts; the add-on default).
4. **Post passes.** Optional adjacency smoothing localised to inpainted
   regions, and a 4-bone-limit pass whose removal mask is *dilated/smoothed
   over the mesh graph* so limiting doesn't tear holes in the field.

So: different topology is the entire point (no correspondence needed);
intersections and nearby-but-wrong surfaces are handled by the normal gate
+ inpainting rather than by proximity; the “geodesic” flavour is the
biharmonic solve over the target's own graph.

### Requirements & Blender 5.2 compatibility

- Deps (its `requirements.txt`, installed by its own pip operator,
  numpy-pinned to Blender's): `scipy`, `libigl==2.5.1`, `robust-laplacian`.
- `bl_info` declares Blender ≥ 3.1.0 with **no upper cap**; the operator
  code uses only long-stable `bpy` APIs. Nothing in the code contradicts
  running on our **Blender 5.2.3 LTS**; the pinned libigl 2.5.1 ships
  wheels for Blender 5.2's Python (3.13). We verified the *core* headless
  on Python 3.12 with the exact pinned deps (below); a full in-Blender
  install run was not performed — the `bpy` wrapper is a thin shell over
  `weighttransfer.py`, which is what we exercised.

### Licence — read and tiered

The repo ships the full **GPL v3** text as `LICENSE`. The add-on's own
file headers state (verbatim from `weighttransfer.py`):

> “This program is free software: you can redistribute it and/or modify it
> under the terms of the GNU General Public License as published by the
> Free Software Foundation, **either version 2 of the License, or (at your
> option) any later version**.”

— and, for the ported core:

> “The following portions of this file are based on work by Rinat
> Abdrashitov and are licensed under the **MIT License**” (the
> `RobustSkinWeightsTransferCode` reference implementation).

**Tier: build-tier as a *tool*, study-only as *code*.** Running a GPL
add-on inside Blender imposes no licence on its output (vertex weights are
data, not a derivative work of the add-on), so RWT can sit in our Blender
sidecar pipeline today. But its code is copyleft: none of
sentfromspacevr's GPL wrapper may be copied into the app. The clean
in-core route exists — the algorithm's reference implementation by the
paper's author is MIT (per the attribution above), so an in-core
implementation should be written from the paper + that MIT reference,
not from the GPL port.

### Headless test — orc bust testbed, autoskin pose metrics

Setup (`/tmp/rwt_test/test_rwt.py`, pure Python, pinned deps): source =
the bust mesh carrying our B+ (geodesic + guards) weights over the 36-bone
contract; targets = the bust's own teeth, eyes, and hair meshes — foreign
topology, and the teeth/eyes are *interior* parts, the case that destroyed
bone heat in AUTOSKIN.md. Scoring = the autoskin harness (jaw open 25°)
plus per-vertex L1 distance to the B+ field on the same mesh (B+ is the
guard-corrected reference). Blender's built-in transfer wasn't re-run:
bone-heat figures from AUTOSKIN.md are the Blender-native baseline, and
Data Transfer shares the closest-point DNA RWT's matching stage starts
from.

| Target / mode | Matched | Upper teeth disp (jaw) | Lower teeth disp | Eyes disp (jaw) | L1 vs B+ |
|---|---|---|---|---|---|
| B+ geodesic + guards (reference) | — | **0.0000** | 0.423 | **0.0000** | 0 |
| Blender bone heat (AUTOSKIN.md) | — | 0.3277 | 0.362 | 0.237 | — |
| RWT teeth, POINT (add-on default), d=0.05 / 0.25 | 15% / 24% | **FAILED** | — | — | — |
| RWT teeth, SURFACE, d=0.25 | 24% | 0.2263 | 0.270 | — | 1.369 |
| RWT eyes, d=0.05 / 0.25 | 45% | — | — | 0.0446 | 1.999 |
| RWT hair, SURFACE, d=0.25 | 74% | — | — | — | 0.742 |

Findings, honestly:

1. **Where it works, it's fast and complete.** Match + inpaint ≈ 0.2 s per
   part at these sizes, and every successful run produced **zero
   unweighted vertices** — the inpainting guarantee is real.
2. **It beats Blender-native on interior parts but loses to guards.**
   Eyes at 0.045 jaw displacement are 5× better than bone heat (0.237);
   upper teeth 0.226 vs bone heat's 0.328. Neither reaches B+'s exact 0 —
   biharmonic fill is *smooth*, and smooth is precisely what an arcade
   boundary must not be.
3. **POINT mode (the default) failed outright on the teeth** —
   `igl.min_quad_with_fixed` returned “Numerical issue” at both distances.
   The teeth are 72 disconnected components with few matched seeds each;
   the add-on's own README acknowledges this loose-parts failure family
   (it ships a “Select Rejected Loose Parts” helper). SURFACE mode
   succeeded on the same input. **Our pipeline default would be SURFACE.**
4. **Interior parts match poorly by design.** Teeth matched only 15–24%:
   they sit *inside* the head, far from and normal-opposed to the source
   surface. RWT is built for surface-hugging targets (clothing over a
   body) — hair, its home case, matched 74%.
5. **The sobering one: it faithfully transferred our own field's sins.**
   The B+ *bust surface* near the eye sockets itself carries Jaw ≈ 0.54 +
   Shoulders ≈ 0.46 (the guards fixed the separate eye/teeth *parts*; the
   bust's geodesic field still leaks there). RWT copied that local field
   and inpainted it smoothly across the eyeballs — hence L1 ≈ 2.0 vs the
   rigid-Head reference despite decent pose numbers. Transfer quality is
   capped by source-field quality; no transfer method fixes a contaminated
   source.

---

## Part B2 — cvELD Edit Paint (via 80.lv)

- **What:** *cvELD Edit Paint* (v2.2.5) by **cvELD** — weight painting
  **inside Edit Mode**, no Weight Paint mode round-trips.
- **Where it ships:** SuperHive Market (formerly Blender Market),
  https://superhivemarket.com/products/cveld-edit-paint/ — **$13.00 USD**,
  in stock. No GitHub release found.
- **Licence/tier:** paid commercial add-on → **study/design-tier under our
  no-purchases rule**. Evaluated from the 80.lv article + the author's
  demo coverage only; **not purchased, not installed**.
- **Compatibility:** explicitly supports **Blender 4.5 – 5.2** — our
  5.2.3 LTS is in range.
- **Feature set beyond stock Blender:**
  - **Paint in Edit Mode** with vertex selection as the mask — paint only
    what you selected, with ordinary edit-selection tools.
  - **Multi-bone painting** — adjust several bones' weights in one place
    instead of group-hopping.
  - **Standard brush + Half Brush** — the half brush paints only one side
    of the brush footprint for precise edge control.
  - **Smart Gradient** — gradient applies **only along the drag
    direction**, not radially everywhere.
  - **Five original gradient modes + Ribbon Gradient** (newest update);
    demo coverage names the sub-modes: **Bone Axis Gradient** (ramp along
    a bone's axis, with explicit start/end values, e.g. 0.29→0.79),
    **Radial Gradient**, **Blender Gradient** (stock behaviour), **Fan
    Gradient**, **Ribbon Gradient** (ramp across a band).
  - **Pose-mode painting** — paint and fine-tune weights *while the bone
    is posed/moved*, i.e. fix the deformation where you can see it.
  - **Strict normalization + protected locks** — normalization enforced
    during painting; locked bones are truly protected.
  - **Multi-Color display** and per-selection weight readout in the demo
    UI.

---

## Part C — Synthesis for AnthroForge

### C.1 One brush discipline, two fields

AnthroForge paints two kinds of per-vertex scalar fields with the same
hand: **skin weights** (per bone) and **AF_mobility** (per slider, the
gravity/sag field of GRAVITY_WEIGHTS.md). Royal Skies' operator-first
discipline, cvELD's Edit-Mode innovations, and GRAVITY_WEIGHTS §3.2
converge on a single paint-mode ops list. This is the requirement set for
the app's paint mode:

**Brushes**
1. Draw (add/subtract, strength-scaled) — with **Projected falloff**
   toggle (paint-through) [Royal Skies].
2. Half Brush — one-sided footprint for painting up to a boundary without
   crossing it [cvELD].
3. Blur — graph-Laplacian relaxation stroke [both; = GRAVITY §3.2 Smooth].
4. Mobility/Anchor pair for AF fields (raise/lower toward pinned)
   [GRAVITY §3.2].

**Gradient tools** (one drag, whole falloff — the single biggest speed win)
5. Linear Gradient (drag-defined ramp) [stock/Royal Skies].
6. **Smart Gradient** — ramp only along the drag direction [cvELD].
7. **Bone Axis Gradient** — ramp parameterised by a bone's axis with
   numeric start/end values [cvELD]. For AF_mobility this generalises to
   *field-axis gradient* (e.g. along the gravity/torso axis).
8. Radial Gradient [stock].
9. Fan Gradient and Ribbon Gradient — fanning ramps for ears/fingers and
   band ramps for crease lines [cvELD].

**Operators** (apply to selection / active group / all groups)
10. Fill / Set Weight (block-in) · 11. Normalize (+ Auto-Normalize toggle,
    strict mode) · 12. Clean (threshold) · 13. Levels (gain/offset) ·
    14. Smooth-selection · 15. Mirror (+ topology mirror, mirror-to-
    opposite-bone) · 16. Limit influences (top-N with graph-dilated mask,
    borrowed from RWT's `limit_mask`) · 17. Attenuate-at-flips auto-repair
    [GRAVITY §2.4] for AF fields.

**Session mechanics**
18. **Edit-mode painting with selection masks** — no mode round-trip;
    selection is the mask [cvELD].
19. **Multi-field painting** — several bones (or bone + mobility)
    adjustable in one panel with per-field locks [cvELD multi-bone +
    stock locking].
20. **Pose-and-paint** — pose the rig (jaw open, spine bent) and paint
    while posed, so hang-region weights are fixed where the deformation
    is visible [cvELD]. For AF fields: preview the slider at +1 *while*
    painting the mobility field (the paintable .blend already does this
    with shape keys — it becomes a first-class app behaviour).
21. **Matched/rejected visualisation** — a debug view showing which
    vertices a transfer matched vs inpainted [RWT's “Visualize Rejected
    Weights”], and the mobility heat-viz layer [GRAVITY §3.1].

### C.2 Where robust transfer fits the architecture

Foreign-topology transfer is our core registration problem twice over:
slider deltas (the learn pipeline) and skin weights (auto-skinning). RWT
addresses only the second, and the test says **complement, not replace**:

- **B+ (geodesic + anatomical guards) stays the default for anatomy.**
  It is the only method that scored exact 0 on upper teeth and eyes,
  because the guards encode semantics no geometric method has. RWT has
  no guard concept — its inpainting actively smooths across the
  boundaries guards exist to protect.
- **RWT becomes the transfer stage for surface-hugging parts** — clothing,
  hair shells, armour, accessories fitted over a skinned body — where it
  matched 74% outright, never leaves an unweighted vertex, and its
  normal-gate + inpaint design is strictly better than the closest-point
  copy it would replace. This is the VRChat-clothing problem it was built
  for, and it's a real hole in our current pipeline (B+ weights a part
  from the rig; it does not transfer a *body's* field onto a garment).
- **Adopt two of its mechanics into our own code regardless:**
  (a) **matched-% as a QA gate metric** — a transfer that matched <50%
  is flagged for review instead of silently shipping inpainted guesses;
  (b) the **graph-dilated top-N limiting mask**, which is better than
  naive top-4 truncation and slots into the export path.
- **Watch the failure mode:** multi-component targets + POINT mode =
  hard failure in the solver. If RWT runs in the sidecar, pin it to
  SURFACE mode, and treat per-component matched counts as part of the
  gate (a component with zero matches is a guard-class problem — route
  it to the human-click flow AUTOSKIN.md already specifies).

### C.3 Verdict

| Source | Verdict | Why |
|---|---|---|
| Royal Skies video | **Adopt the discipline** (ops list §C.1) | Operator-first painting is the fastest known workflow and maps 1:1 onto both our field types. (Transcript unverifiable — bot-walled; techniques tagged by provenance in Part A.) |
| Robust Weight Transfer | **Adopt as a tool** in the Blender sidecar for surface parts; **adopt algorithm ideas** (inpainting gate, matched-% QA, dilated limiting) for in-core work via the paper + MIT reference implementation; **do not copy the GPL code** | GPL v2+/v3 copyleft on the wrapper; output data is unencumbered. Beats Blender-native, loses to B+ guards on anatomy, best-in-class on garments. |
| cvELD Edit Paint | **Study-tier (paid, $13, not purchased); adopt its features as design requirements** | Edit-mode painting, Smart/Bone-Axis/Ribbon gradients, half brush, pose-and-paint are now requirements 2, 6, 7, 9, 18, 20 in §C.1 — whether or not the add-on itself is ever bought. Blender 4.5–5.2 support covers our 5.2.3. |

Test artefacts: `/tmp/rwt_test/test_rwt.py`, `/tmp/rwt_test/diag_rwt.py`
(pinned deps in a scratch venv; repo cloned at `/tmp/rwt`). Disk after
work: 56 GB free — floor respected, nothing heavy pulled.
