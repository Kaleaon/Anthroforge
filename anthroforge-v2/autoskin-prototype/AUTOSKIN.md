# AUTOSKIN — Auto-Skinning Prototype: Results & Recommendation

**Subject:** Orc Head Bust *Free* — Jesterz86, Sketchfab, CC BY. Eyes, teeth,
tongue and hair are separate meshes — a deliberately hard first subject:
six meshes, 38,046 verts, non-manifold in places, open at the bottom (bust).
**Rig:** the AnthroForge 36-bone contract (`BONE_HIERARCHY` in
`anthroforge_3d_pro_v2.html`); only the head/neck/jaw bones carry real weight
on a bust, but the full 36-bone armature is built and exported.
**Deliverable:** [`orc_bust_skinned.glb`](sandbox://workspace/anthroforge-v2/autoskin-prototype/orc_bust_skinned.glb)
— geodesic weights + anatomical guards, full 36-joint skin.

## Verdict in one paragraph

**Geodesic-falloff weighting with anatomical guards (method B+) wins, and it
isn't close.** Bone heat (method A) covers every vertex and tracks the chin
slightly better, but it is semantically blind: it drags the *upper* teeth
0.33 units when the jaw opens (they must not move at all), moves the eyes
0.24 units in a jaw pose, and leaks jaw weight into the torso through the
open bottom of the bust (isolated edges strained up to 84×). Method B+ keeps
upper teeth at exactly 0.0000 displacement, eyes perfectly rigid, and its
only real weakness is neck stretching on a hard 35° head turn — a blend
width problem, fixable with tuning, not a correctness failure.

## Methods

### A — Blender automatic weights (bone heat)
Armature built from the fitted 36-bone layout; each mesh parented with
`ARMATURE_AUTO`. Bone heat **succeeded on all 6 meshes (100% vertex
coverage)** — notable on a non-manifold bust. Weights extracted to the same
top-4 npz format as method B for a fair fight. Script:
`work/blender_auto.py`, log: `work/auto_log.txt`.

### B — Geodesic falloff (custom)
Per bone: seed verts = verts whose nearest bone segment is that bone, by a
clear margin. Weight field = `exp(-(geodesic distance to seeds / σ)²)` via
multi-source Dijkstra on the mesh edge graph, σ = 0.38 × bone length
(min 0.16). Disconnected components without seeds fall back to Euclidean
segment distance. Top-4 influences, normalised. ~10 s for the whole bust.

> **Bug found in the inherited code:** the super-source Dijkstra in
> `geo_weights.py` wired the virtual source node to vertex 0 and read
> distances from an isolated node — it would have returned all-inf
> distances and zero weights everywhere. Fixed (proper 0-length edges from
> source node *n* to every seed) before first run.

### B+ — B plus anatomical guards (`work/apply_guards.py`)
Raw geodesic fields leak across semantic boundaries on connected meshes.
The guards are the production part of the method:

| Guard | Rule | Why |
|---|---|---|
| Eyes | rigid to Head | eyeballs must never smear |
| Teeth | **per connected component** (72 components: individual teeth + arcade slabs): centroid above occlusal plane z = −0.97 → rigid Head, below → rigid Jaw | the teeth are one mesh object but two arcades; the raw field gave *all* 11,407 teeth verts jaw weight > 0.5 |
| Tusks | tall front components (span ≥ 0.30, front of mouth) that **taper toward the top** → Jaw, overriding the plane | orc lower tusks erupt *up past* the occlusal plane; the plane rule alone misfiled all 3 tusk components (1,281 verts) as upper teeth — caught on the first jaw render, fixed, re-verified |
| Rings | rigid to Ear_L / Ear_R by x sign | earrings; raw field gave them to the shoulders on a near-tie Euclidean fallback |
| Tongue | influences restricted to {Head, Jaw}, renormalised | tongue root is jaw/hyoid, not shoulders |
| Jaw hinge fade | on the bust mesh, Jaw weight × smoothstep(z): full below z = −0.45, zero above z = −0.15 | raw field put jaw weight > 0.5 on 10,712 bust verts incl. brow/cheeks; guarded: 6,651, concentrated in chin/jaw/neck-front where it belongs |

## Pose tests

Numpy LBS harness (`work/pose_test.py`): each posed bone rotates about its
own rest head point around a world axis, transforms compose down the
hierarchy. Poses: **jaw open** (Jaw +25° X), **head turn** (Head +35° Z),
**head tilt** (Neck +6°, Head +14° roll). Metrics: per-mesh displacement,
teeth discipline vs a geometric upper/lower reference split (same rules as
the guards), edge-length strain on the bust (collapse / candy-wrapper
detector), chin tracking. Renders: `pose_<method>_<pose>_{front,side}.png`.

### Jaw open 25° — the discriminating test

| Metric | B+ geodesic | A bone heat |
|---|---|---|
| Upper teeth displacement (want 0) | **0.0000** | 0.3277 ✗ |
| Lower teeth displacement (want ≈0.45 rigid) | **0.423** | 0.362 |
| Eyes displacement (want 0) | **0.0000** | 0.237 ✗ |
| Chin displacement | 0.377 | **0.409** |
| Bust edge strain p99 / max | 0.955 / 3.9 | 0.000 / **54.2** ✗ |
| Tongue mean displacement | 0.397 | 0.103 |

Visually: B+ opens the mouth cleanly, tusks ride the jaw, upper arcade and
eyes stay put ([pose_geo_jaw_side.png](sandbox://workspace/anthroforge-v2/autoskin-prototype/pose_geo_jaw_side.png)).
A opens the mouth but the whole dental arcade translates as one blob and
the mouth interior smears ([pose_auto_jaw_side.png](sandbox://workspace/anthroforge-v2/autoskin-prototype/pose_auto_jaw_side.png));
its p99 strain of 0 with a 54× max is the signature of a few torso verts
carrying jaw weight through the open bust bottom and getting ripped.

### Head turn 35°

Both methods swing the whole head assembly coherently (hair/eyes/teeth/
rings mean displacements all ≈0.53–0.60 under B+). **B+'s weak spot:**
bust edge strain p50 0.055 / p99 1.58 / max 6.5 — the neck blend is wide
and a hard 35° yaw stretches the neck-to-chest transition. A's bulk strain
is lower (p99 0.000) but it still hides an 84× max-strain outlier. Neither
is shippable at 35° without neck work; B+'s failure is diffuse and tunable
(σ per bone, a Neck counter-rotation split), A's is spiky and structural.

### Head tilt (Neck 6° + Head 14°)

B+ is clean and gentle (strain p99 0.344, max 0.862; all parts track).
A comparable on bulk strain (p99 0.617) with another 41× outlier.

## Failure modes (both methods, honestly)

1. **Semantic blindness (A, and raw B):** any purely geometric method will
   skin upper teeth to the jaw if the arcades share a mesh. Guards or
   per-part rules are not optional polish — they are the difference
   between working and broken.
2. **Open / non-manifold geometry (A):** bone heat diffuses through the
   interior and out the open bottom of the bust, planting stray weights in
   the torso (the 54–84× strain outliers). It also has no answer for
   which side of a boundary a vertex belongs to.
3. **Tusk-class ambiguity (B+):** geometry-only classification of tall
   front teeth needed a shape cue (taper direction), not just position.
   Expect a small residue of genuinely ambiguous parts on real imports —
   this is where a human click ("this part rides the jaw") must exist.
4. **Neck stretch at extreme yaw (B+):** single-σ geodesic falloff
   over-blends the neck. Mitigations: per-bone σ, pose-space corrective,
   or splitting the turn between Neck and Head (the tilt pose, which does
   split, strains ~4× less at p99).
5. **Renderer caveat:** the pose renders use a painter's-algorithm
   matplotlib renderer (per-face depth sort, no per-fragment occlusion) —
   far-side teeth can show through the cheek in stills. Numeric metrics,
   not the stills, are the ground truth; the exported GLB was verified
   numerically inside Blender (below).

## Export & verification

`work/blender_export.py` rebuilt the armature, imported the original glTF
(materials/UVs preserved), assigned B+ weights as vertex groups, and
exported the bind-pose GLB. (No Workbench render check: this VM lacks
libEGL and Blender *aborts* rather than errors — verification is numeric,
via `work/blender_verify.py`.)

**QA gauntlet** (`qa-gauntlet/validate_glb.py`, full JSON in `work/qa/`):

> 6 meshes · 38,046 v / 70,004 t · **skin 36 joints, contract 36/36** ·
> 6 textures embedded / 0 external · **0 degenerate triangles · 0 NaN** ·
> extent 6.92 m, no scale flag

**End-to-end in Blender:** re-imported the GLB, posed the Jaw bone 25°,
evaluated the deformed meshes — eyes displace 0.0000, chin 0.526, lower
teeth follow, upper band ~static. Magnitudes run ~1.3–1.4× the numpy
figures (the glTF round-trip re-fits the armature frame/pivot on import);
direction, ordering, and all zero/non-zero verdicts agree. In the app's
own rig space the numpy numbers are the ground truth.

**Size note:** the GLB is 47.7 MB, of which ~43 MB is the source's own
embedded textures. Geometry + skin is ~5 MB. Texture downscaling is an
export-profile decision, not a skinning problem.

## Recommendation for the app

**Default: geodesic falloff + the guard pack (B+).** It is fast (~10 s),
fully scriptable/headless, deterministic, and — with guards — semantically
correct on the hard cases (teeth, eyes, earrings, tongue). Ship these
guards as named, inspectable rules, and add per-bone σ overrides.

**Bone heat: keep as an optional second opinion** for closed, manifold,
full-body meshes (where its diffusion is well-behaved and its chin/joint
tracking is slightly ahead) — never as the default for parts-based or
open geometry, and never without the same guard pack applied afterwards.

**A human must intervene when:**
- a part is geometrically ambiguous (tusk-class: position says one bone,
  anatomy says another) — one click per part, offered by the UI with the
  classifier's best guess pre-selected;
- the mesh is a single connected blob mixing two arcades/organs with no
  component structure to split on;
- extreme-pose QA (turn ≥ ~30°) shows neck/joint strain above threshold —
  the fix is blend tuning or a corrective, which is artist work.

**Pipeline shape this implies:** import → component split → geodesic
weights → guard pack → pose-test harness (jaw/turn/tilt + strain metrics)
as an automated gate → human review only for flagged parts. Every stage
of that pipeline now exists in `work/` as a working script.

## Files

| File | What |
|---|---|
| `orc_bust_skinned.glb` | deliverable: B+ skinned bust, 36/36 contract |
| `pose_geo_jaw_side.png` / `pose_geo_jaw_front.png` | winning method, jaw pose |
| `pose_geo_turn_front.png` / `pose_geo_tilt_front.png` | turn / tilt |
| `pose_auto_jaw_side.png` | bone-heat jaw pose (the smear) |
| `work/geo_weights.py` | geodesic weighting (bug-fixed) |
| `work/apply_guards.py` | anatomical guard pack |
| `work/blender_auto.py` + `auto_log.txt` | method A + coverage log |
| `work/pose_test.py` + `pose_metrics.txt` | pose harness + all metrics |
| `work/blender_export.py` / `blender_verify.py` | GLB export / in-Blender verification |
| `work/qa/orc_bust_skinned.qa.json` | gauntlet report |
| `work/rest_*.png`, `work/bust/` | rest renders, source glTF (CC BY, Jesterz86) |
