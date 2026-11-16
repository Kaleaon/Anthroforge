# B13 — Digitigrade Legs

*Model-craft wave B13, Nov 12, 2026. Finisher doc written Nov 12, 2026 after the
original agent died on a transport timeout post-export; every number below is
either quoted from the build script / work logs or re-measured from the shipped
GLBs by the finisher (marked ✓). The build script's header cites this file in
several places — it did not exist until now.*

**Socket:** `leg.digi.L` / `leg.digi.R` (PARTS_STANDARD #16) · **Class:** A ·
**Kind:** anatomy · **Plan:** `plan.biped` only (leg style is a module inside
the biped plan, BODY_PLANS §3.3 — not a plan switch) · **Cost:** 6 pts per leg,
12 the pair (major-class cap 25; character pool 128)

| File | Contents |
|---|---|
| `parts/legs_digitigrade.R.glb` | right leg, own 5-bone skin |
| `parts/legs_digitigrade.L.glb` | left leg — mirror defect **fixed**, see §9 |
| `parts/legs_digitigrade_pair.glb` | both legs, 2 skins |
| `parts/legs_digitigrade.blend` | source scene (both legs + armatures) |
| `parts/legs_digitigrade.R.part.json` / `.L.part.json` | part records (added by finisher) |
| `renders/standing_side.png` | the only render that exists (§7 debit 3) |
| `scripts/build_digitigrade.py` | full procedural build |
| `scripts/render_one.py` | single-view re-render from the saved .blend |
| `work/` | hm08 scan + landmarks, `fit_qa.json`, `leg_R.obj`, gauntlet results (`*.qa.json`, finisher) |

---

## 1. Design basis — measured from hm08

The leg was proportioned against the hm08 reference base, not eyeballed:

- `work/hm08_scan.json`: body height **1.66589 m**.
- `work/hm08_landmarks.json` (MakeHuman frame): floor z −0.81676, crotch
  z −0.04474 → **crotch 0.772 m above floor**, neck z 0.58247.

The part's own frame is canonical AnthroForge: metres, x = character right,
y = front, z = up, floor z = 0. The hip joint is placed at z **0.802 m** —
30 mm above the hm08 crotch line, inside the pelvis volume, where the skirt
(§4) seats. Total part extent is 0.898 m ✓ (gauntlet), i.e. the leg module
spans 54% of the reference body's height, hip seat to toe.

## 2. Joint design — a true digitigrade chain

Joint positions (canonical, right leg; left mirrored in x):

| Joint | (x, y, z) m | Role |
|---|---|---|
| Hip H | (0.098, 0.000, 0.802) | chain root, inside pelvis |
| Stifle K | (0.100, 0.070, 0.497) | true knee, forward |
| Hock A | (0.102, −0.032, 0.268) | **anatomical ankle (tarsus), backward** |
| MTP M | (0.102, 0.030, 0.052) | metatarsophalangeal joint |
| Toe tip T | (0.102, 0.118, 0.014) | digit end |

Segment lengths ✓ (recomputed from the shipped coordinates):

| Segment | Length | Share of 3-bone chain |
|---|---|---|
| Femur H→K | 0.313 m | 39.7% |
| Tibia K→A | 0.251 m | 31.8% |
| Metatarsus A→M | 0.225 m | 28.5% |
| Toes M→T | 0.096 m | (past the chain) |

Three-bone chain total 0.788 m. The split sits close to the canine structure
the build script cites (~41/30/29, Schmieder 2000 + breed data): slightly less
femur, slightly more tibia, metatarsus on the mark.

Standing interior angles ✓ (recomputed): **stifle 143.1°, hock 140.0°,
MTP 129.4°**. Against the dog bands the script quotes (stifle 135–140°,
hock 140–150°), the hock is in-band and the stifle is opened ~3–8° — the
script's stated reasoning is that an upright anthro stance opens the stifle
slightly; the number was a design choice, and it is recorded here as one.

**Hock placement.** The hock sits at z 0.268 m — one third of hip height —
and 32 mm *behind* the hip's sagittal plane (y −0.032 vs hip y 0), while the
stifle excursions 70 mm in front of it. The metatarsus leaves the hock
running forward-down at ~16° from vertical to the MTP at z 0.052 m, so the
load path is: femur forward, tibia back, metatarsus near-vertical, digits
flat. In the side render (§6) that zigzag is the whole silhouette.

### 2.1 Why this is digitigrade and not the reversed-ankle illusion

The cheap version of "digitigrade" is an illusion: take a plantigrade leg,
shape the calf so the *ankle* reads as a backward joint, and stretch the foot
so it reads as toes. It has one segment below the fake hock, no joint where
the metatarsus meets the digits, and it collapses the moment it animates,
because the deformation skeleton still thinks the long segment is a foot.

This part is the anatomical thing, in bone space:

- There is a **real joint at the anatomical ankle** (the hock), bending
  backward, at one-third leg height — not at foot level.
- The **metatarsus is its own load-bearing segment** (0.225 m, 28.5% of the
  chain) between hock and MTP. It never touches the ground.
- **Ground contact is digits only**: four toes past the MTP joint, pads under
  the MTP and toe tips (§4). `function.gait` in the part records declares
  `profile: digitigrade, contact: toes`.

BODY_PLANS §3.3 describes the SL/Bento practice — reposition the joints,
lengthen the foot segment, walk on toes with a raised hock, skeleton identity
unchanged — and adopts the same philosophy. B13 follows it one step further:
the core bone names `Hip/Knee/Ankle/Foot` are kept, and the extra
articulation the metatarsus needs is bought with **one module bone**.

### 2.2 The hock module — and a naming caveat

Per-leg bone chain (lengths ✓ from the shipped node translations):

```
Hip_* (femur 0.313) → Knee_* (tibia 0.251) → Ankle_* (prox. metatarsus 0.101)
    → Hock_* (dist. metatarsus 0.124) → Foot_* (toes 0.124)
```

`Ankle_*` heads **at the hock joint** and drives the proximal metatarsus;
`Hock_*` heads at mid-metatarsus (45% along A→M) and drives the distal
metatarsus. Four of the five names are core-rig names — the gauntlet matches
4/36 contract joints — and `Hock_*` is the +1 module bone, exactly the
"digitigrade hock module" PARTS_STANDARD socket 16 names as the anchor
companion to `Ankle_L/R`. Read the bone names as contract names, not anatomy
claims: the bone *called* Ankle is not at the anatomical ankle's plantigrade
position, it is at the hock, which is where a digitigrade module's ankle
joint has to live.

## 3. Does the part carry its own chain? Yes.

Each leg ships with its own 5-bone armature (`DigitigradeLeg_L` /
`DigitigradeLeg_R`); the pair GLB carries 2 skins ✓. This is deliberate and
matches the pattern B14 hit from the other side: the library wolf (Mixamo
humanoid rig) has no tail bones, so the tail part carries its chain with it
(APPENDAGES.md §6). A plantigrade core rig likewise has no hock-module bone
to lend, so the leg module brings the whole chain. At equip, the `Hip_*`
roots parent under the plan's `Pelvis`; `Hip/Knee/Ankle/Foot` bind to the
core names and `Hock_*` rides as the module extra (the gauntlet reports it
under `contract_extra`, which for a module part is the expected shape — cf.
the B11 hand's module exemption).

Weighting is authored (`own-weights`), analytic rather than painted: each
vertex is placed by arc length along the loft's station chain and blended
across interior joints with a smoothstep over ±35 mm of arc. Verified on the
shipped GLBs ✓: **weight rows sum to exactly 1.0000, max 2 influences, all
5 joints used.** Appendage geometry is weighted by rule: toes ramp
Hock→Foot along their length (Foot 0.45 at the base → 1.0 at the tip), main
pad 0.35 Hock / 0.65 Foot, toe pads 0.1 / 0.9, claws pure Foot.

## 4. Construction

Everything is procedural lofting (`scripts/build_digitigrade.py`); no donor
geometry. The leg tube is a 19-station elliptical loft, 16 points per ring,
with a `front_bias` term that shifts cross-section mass forward (quadriceps)
or backward (calf):

- **Skirt (2 stations above the hip):** rises +0.075 m above the hip joint,
  flaring to 0.205 × 0.215 m — this is the seat that disappears into the
  pelvis volume. The top cap is a flat ngon: a truncation, hidden inside the
  body in use, visible in the standalone render.
- **Thigh (7 stations):** 0.205 m wide at the skirt → 0.106 m at the stifle,
  front bias peaking +0.08 at the quad bulge (52% down).
- **Shin (5 stations):** gastrocnemius high and back-biased (−0.16 at 28%),
  tapering 0.102 → 0.052 m at the hock.
- **Metatarsus (4 stations):** lean tendinous shaft (0.050 → 0.044 m) with a
  flare to 0.060 m at the MTP knuckle.
- **Paw (3 stations):** spreads and flattens forward of the MTP, depth
  0.057 → 0.030 m.
- **Toes (×4):** separate 10-sided mini-lofts, canine count (no dewclaw),
  fanned −7° / −2.5° / +2.5° / +7° at ±9.2 / ±27.5 mm from paw centre.
- **Pads:** main pad a flattened ellipsoid (62 × 54 × 22 mm) under the MTP;
  four toe pads (23 × 27 × 12 mm). **Claws:** 20 mm cones at the toe tips.

Vertex budget per leg (897 total ✓): loft 305 (19 × 16 + cap centre),
toes 168 (4 × 42), main pad 108, toe pads 280 (4 × 70), claws 36 (4 × 9).
1,616 tris.

## 5. Socket scope divergence — read before equipping

PARTS_STANDARD socket 16 scopes `leg.digi` as a **lower-leg/paw module**:
fit region ≈ 0.28 m long, anchored at `Ankle_L/R` + hock module — i.e. it
imagines swapping below a kept plantigrade thigh. **B13 did not build that.**
It built a full leg from the hip: 0.898 m extent, own `Hip_*` root, pelvis
skirt, thigh included. The reasoning is defensible — a digitigrade femur and
stifle are not a plantigrade thigh, and §2's angles need the whole chain —
but it is a divergence from the socket as written, and it is recorded here
and in both part records rather than silently shipped. Either the socket
grows a full-leg variant, or this part's thigh section becomes reference
geometry for a future lower-leg-only cut. That is a standards call, not a
build call.

Plan fit follows from the socket: `plan.biped` only. Taur, feral and naga
plans instance their legs through `leg.fore` / `leg.hind` (socket 17), whose
fits are never coupled to the biped instances (BODY_PLANS §3.4 hard rule).

## 6. QA

### 6.1 Gauntlet (finisher-run, `qa-gauntlet/validate_glb.py`; full JSON in `work/`)

| Check | R | L | Pair |
|---|---|---|---|
| parse | ok | ok | ok |
| meshes / verts / tris | 1 / 897 / 1,616 | same | 2 / 1,794 / 3,232 |
| skin | ok — 5 joints, IBMs present | ok | ok — 2 skins |
| contract | 4/36 core + `Hock_R` extra | 4/36 + `Hock_L` | (first skin reported) |
| morphs | 0 (warn) | 0 | 0 |
| NaN verts | 0 | 0 | 0 |
| degenerate tris | **104** | **104** | 208 |
| extent | 0.898 m, scale ok | same | same |

The contract line is the module-part shape, not a failure of fit — the
gauntlet's full-character gate does not apply to socket modules (B11
precedent). The geometry gate genuinely fails, on the degenerates:

**Degenerate localisation ✓** (finisher, from the shipped index buffer):
all 104 degenerate triangles in each leg are **UV-sphere pole fans in the
pads** — 24 in the main pad (12 per pole) and 80 across the four toe pads
(20 each). The loft, toes and claws contribute zero. They are zero-area
triangles at the pad poles: invisible in renders, harmless to skinning, but
they fail the gate and would waste a slice of any downstream retopo/bake.
Fix is mechanical: collapse each sphere pole ring to a single vertex.

### 6.2 Fit QA (original agent's `work/fit_qa.json`, right leg vs hm08)

| Metric | Value |
|---|---|
| part verts | 897 |
| buried % | 0.0 |
| excess % | 0.0 |
| engaged % | 1.56 |
| out-of-grid % | 25.08 |
| band (world) | 0.0465 m |
| max depth (world) | 0.143 m |
| fit_score / verdict | 0.016 / "poor" |

The "poor" verdict does not survive contact with what this part is — the
same finding B14 recorded for proud appendages. `fit_score` grades how a
patch engages a base surface inside the base's grid. A whole-leg replacement
engages the base almost nowhere (only the skirt seat), and a quarter of its
verts sit outside the plantigrade base's grid *because the digitigrade chain
leaves the plantigrade envelope* — that departure is the product. The
applicable gates are buried 0.0% and excess 0.0%: nothing sinks into the
base, nothing spills. What was **not** measured: the skirt seat itself (how
the flare meets the hm08 pelvis surface). The seat is asserted by
construction, not verified — §7 debit 8.

### 6.3 The render

`renders/standing_side.png` (recovered post-hoc via `render_one.py`;
§7 debit 3). Read: the digitigrade silhouette is unambiguous in profile —
forward stifle, backward hock, long near-vertical metatarsus, contact on the
paw. Visible debits in-frame: a dark pinched notch at the front of the
stifle; the skirt's flat truncation edge reading against the small pelvis
stub; the toes merging into a single paw mass (the fan is a top-view
feature and no top/three-quarter view exists); the shin and metatarsus
reading as one smooth uniform tube with no tendon or hock-callosity break.

## 7. Honest debits

1. **THE LEFT LEG'S GEOMETRY IS NOT MIRRORED — the pair is not a pair.**
   **FIXED Nov 12, 2026 — see §9.** (Kept below as the defect record.)
   Verified three ways ✓: the L mesh's raw positions span
   x ∈ [−0.0045, +0.2005] m, the *right*-side envelope, identical in extent
   to the R mesh; the `.blend` shows the same for `leg_digitigrade_L`
   local coords; only the skeletons are mirrored (`Hip_L` head at
   x = −0.098 vs `Hip_R` at +0.098). In the pair GLB both meshes occupy the
   same right-side volume. At bind pose an engine renders the L mesh on the
   right; posed, it would swing around the left hip axis from across the
   body. **Root cause** (in `scripts/build_digitigrade.py`): the geometry
   path mirrors *twice* — `build_leg_geometry()` negates the joints for
   side < 0 and toe/pad placement is side-aware, and then `cb()` multiplies
   x by side again during the canonical→Blender conversion, cancelling the
   mirror. The armature path mirrors once (raw `JOINTS` through `cb()`) and
   is correct. **Fix:** mirror exactly once in the geometry path (drop the
   `side < 0` block in `build_leg_geometry` and make toe/pad x-placement
   side-naive, letting `cb()` do the work), rebuild, re-export, re-run the
   gauntlet. Small fix, **not applied** — this pass was document-and-records
   only. Consequence for the render: `standing_side.png` shows the R leg
   with the L leg exactly behind it; a three-quarter or stride view would
   have exposed the defect immediately, which is part of why debit 3
   matters.
2. **104 degenerate triangles per leg** (pad pole fans) — §6.1.
3. **Three of four planned renders were never produced, and
   `work/build_info.json` was never written.** The main build exported the
   GLBs at 22:36 and died during the render stage; `standing_side.png` was
   recovered at 22:47 via `render_one.py`. Missing:
   `standing_threequarter.png`, `stride_side.png`, `stride_threequarter.png`.
   The stride pose exists in both scripts and has never been evidenced —
   and per debit 1, a stride render of the pair could not have passed
   visual QA anyway.
4. **Socket scope divergence** — full leg vs the socket's 0.28 m lower-leg
   module (§5). Needs a standards decision.
5. **Pads hover ~5 mm.** In bind pose the toe-pad bottoms sit at
   z ≈ 0.0045 m and the main pad at z ≈ 0.006 m above the floor plane ✓
   (pad centres/radii from the build script). The render's contact shadow
   hides it; a gait cycle would show the float.
6. **No UVs, no materials, no morphs, no STL.** The GLBs ship bare geometry
   + skin (materials count 0 in the gauntlet run). B14's parts shipped STL
   print files; B13 has none. Fur/skin texturing and any print path are
   downstream work, unstarted.
7. **Surface detail is first-pass.** One smooth loft, uniform 16-point
   rings: no hock callosity, no Achilles read, no toe separation in
   profile, a pinched notch at the stifle front (§6.3). The proportions
   and chain are the deliverable; the surface wants a sculpt pass.
8. **The skirt seat is unverified** (§6.2): no metric was run on the
   pelvis interface itself, and fit QA ran on the right leg only.

## 8. Provenance

Original procedural geometry authored for AnthroForge (CC-BY-4.0, tier
`build`); no donor mesh. Anatomy per the canine structure data cited in the
build script (Schmieder 2000 + breed structure data) and the hm08 reference
measurements in `work/`. Rebuild/fix path: edit
`scripts/build_digitigrade.py`, re-run under Blender 5.2 headless (header of
the script carries the exact invocation), re-export, re-run
`qa-gauntlet/validate_glb.py` and update §6–§7 of this file.

## 9. Fix applied — left-leg mirror rebuild (Nov 12, 2026)

§7 debit 1 is **fixed**. The buggy originals (L / R / pair GLBs, the
`.blend`, the original `standing_side.png`, and the pre-fix gauntlet JSONs)
are preserved in `work/originals/`; the rebuild log is
`work/rebuild_fix.log`; `work/build_info.json` now exists.

**What changed** — `scripts/build_digitigrade.py`, mirror exactly once in
the geometry path, per the §7 recipe:

- `build_leg_geometry()`: the `side < 0` joint-negation block is deleted.
  Geometry is now always built in right-leg canonical space.
- `make_mesh()`: the matching `side < 0` joint negation (used for
  `joint_arcs`) is deleted for the same reason; L and R now report
  identical joint arcs, as congruent geometry should.
- Toe / pad / claw placement is side-naive (`build_toe()` cx, main pad
  centre, toe-pad centres, claw tips): the `side *` factors are gone.
- The single remaining mirror is `cb()` at Blender conversion — the same
  conversion the (always correct) armature path uses.
- One addition beyond the §7 recipe: for `side < 0`, face order is flipped
  in `make_mesh()`. A baked mirror reverses triangle orientation, and the
  measurement below shows why it matters — the buggy L shipped with
  *inward* normals. The flip restores the R leg's outward convention.

**Verification** (measured from the shipped GLBs, before → after):

| Check | L before | L after | R (reference) |
|---|---|---|---|
| mesh x envelope | [−0.0045, +0.2005] (right side) | **[−0.2005, +0.0045]** | [−0.0045, +0.2005] |
| normals, mean dot(n, dir from centroid) | −0.0858 (inward) | **+0.0859** | +0.0859 |
| weight row sums | exactly 1.000000 | exactly 1.000000 | exactly 1.000000 |
| max influences | 2 | 2 | 2 |
| verts / tris | 897 / 1,616 | 897 / 1,616 | 897 / 1,616 |
| gauntlet degenerate tris | 104 | 104 (unchanged — separate job) | 104 |
| gauntlet NaN verts | 0 | 0 | 0 |
| gauntlet extent | 0.8976 m | 0.8976 m | 0.8976 m |

Pair GLB after the fix: 2 skins, 1,794 v / 3,232 t, combined x envelope
[−0.2005, +0.2005] — a symmetric pair for the first time. The L mesh is the
exact mirror of R (envelope mirrored to the 0.1 mm the format carries;
normals stat identical to R's). Gauntlet status profile is otherwise
unchanged (contract fail = module-part shape, geometry fail = the 104
known pad degenerates), and refreshed gauntlet JSONs are in `work/`.

**Renders.** The full rebuild also produced all four planned views —
`standing_threequarter.png`, `standing_side.png`, `stride_side.png`,
`stride_threequarter.png` — closing §7 debit 3 as a side effect. The
three-quarter standing view now shows two distinct legs under the pelvis
stub, the stride views show the pair mid-gait; debit 1's "L exactly behind
R" is gone. `parts/legs_digitigrade.L.part.json` was updated in place:
`provenance.detail` and `qa_gauntlet.known_issue` now record the fix
instead of the defect; fit numbers were not affected (fit QA is R-only,
§6.2) beyond the mirror-instance note, which is now true.

**Not done in this pass, deliberately:** the 104 degenerate pad triangles
(§6.1) — collapsing the pole rings is a separate job, queued apart from
the mirror fix so each change verifies on its own.

