# B8 — Map Baking: pipeline rebuilt and run end-to-end (finisher pass)

**Finisher for the AnthroForge model-craft wave (Nov 12–13, 2026).** The original
B8 agent landed nothing: `b8-baking/` held four empty directories — no scripts,
no maps, no renders. This pass rebuilt the stage from the B2 handoff contract
(B2's RETOPO.md §1 step 6 and §"Limits" item 2 name UV-unwrap + bake as the
explicit next stage) and ran it end-to-end on B2's own pair.

**Subject:** demidevil13's orc head (CC BY) — the B2 prototype pair:
sculpt `orc_head_before.glb` (855,696 tris, vertex colours, no textures) →
retopo cage `orc_head_retopo.glb` (5,811 quads, watertight). Head height
99.15 u (≈24 cm at human scale, 1 u ≈ 2.4 mm).

---

## 1. The pipeline as run

Blender 5.2.3 headless, CPU, `--threads 2`, flat studio world for renders.
Scripts: `work/bake_stage1.py` (import → unwrap → cage → bake),
`work/render_stage2.py` (apply → export → render), `work/analyze.py` (metrics).
One Blender process per stage; total machine time ≈ **5 minutes** (bake 137 s,
renders 125 s) — baking a 5.8k-quad cage is cheap next to B2's retopo (~15–20 min).

| # | Stage | What was done | Settings that mattered |
|---|---|---|---|
| 0 | Inspect | GLB headers parsed directly: the cage ships **POSITION+NORMAL only — no UVs**; the sculpt carries `COLOR_0` vertex colours. Two consequences: unwrap is stage 1, and a colour bake is possible from vertex colours. | — |
| 1 | UV unwrap (cage) | Smart UV Project over all faces. The automatic tier, matching B2's hybrid positioning — a hero head would get hand-placed seams instead. | angle limit **66°**, island margin **0.003**, correct aspect on. Result: **77.3% of the 2048² tile is covered** by islands (measured from the diffuse bake's alpha — see §3 note). |
| 2 | Bake cage | Cage = cage copy displaced along per-vertex averaged face normals (area-weighted). | extrusion **2.0 u = 2.0% of head height** — just above B2's measured max surface deviation (1.64 u, at tusk/ear tips) and inside the production 0.5–2% band's top end. Deliberate trade: a tighter cage risks missing the extremities; the cost shows up as one local artifact (§4). |
| 3 | Bake, selected→active | Cycles bake, sculpt selected / cage active, `use_cage` on, max ray distance unlimited, image margin (dilation) **16 px**, clear on. | **Normal** tangent-space, 2048², 1 spp · **Diffuse colour** from the sculpt's vertex colours (Principled + Vertex Color node on the source; pass filter COLOR only), 2048², sRGB · **AO** 1024², **32 spp** (AO is low-frequency; half resolution is the honest cost/quality point) · **Curvature** via the sculpt's Cycles *Pointiness* → 0.35–0.65 contrast ramp → Emission bake, 2048². |
| 4 | Apply + export | Cage material: colour × AO (multiply) → Base Color, normal map (strength 1.0), curvature → roughness via ramp (concave 1.0 → convex 0.72). Exported as a self-contained GLB. | see §4 for what glTF could and couldn't carry. |
| 5 | Validate | Map statistics masked to true UV coverage + a same-camera lit render of sculpt vs baked cage (ortho, 768², 32 spp, one sun + flat grey world, face three-quarter). | Metrics in §3; image in `renders/comparison.png` (sculpt left, baked cage right). |

## 2. Deliverables

- `maps/orc_head_normal.png` — tangent-space normal, 2048²
- `maps/orc_head_color.png` — vertex-colour diffuse, 2048²
- `maps/orc_head_ao.png` — ambient occlusion, 1024²
- `maps/orc_head_curvature.png` — pointiness curvature, 2048²
- `orc_head_baked.glb` — the cage with UVs + embedded maps (8.9 MB)
- `renders/render_high.png`, `renders/render_low_baked.png`, `renders/comparison.png`
- `work/` — the three scripts, `bake_stats.json`, `analysis.json`, logs, `bake_scene.blend`

## 3. Measured results

Bake times: normal 20.7 s · colour 11.8 s · AO 43.9 s · curvature 43.5 s.

**Map statistics, computed inside UV islands only** (the mask is the diffuse
bake's alpha channel, the one honest coverage signal — see the note below):

| Map | Mean (RGB) | Std | Reading |
|---|---|---|---|
| Normal | (0.501, 0.505, 0.983) | (0.088, 0.082, 0.070) | Textbook tangent-space average with real deviation — sculpt detail transferred. |
| Colour | (0.537, 0.529, 0.456) | (0.120, 0.142, 0.130) | Warm green-grey skin tones with strong variation (war paint, mottling). |
| AO | 0.877 | 0.194 | Mostly open surface, real occlusion in creases/eye sockets/mouth. |
| Curvature | 0.502 | **0.041** | Correctly centred (flat ≈ 0.5) but low contrast — pointiness energy concentrates at features (min 0.0 / max 0.92), it does not wash the whole surface. Fine as a roughness modulator; weak as a standalone "curvature map." |

**Normal-map validity (error check 1):** decoded vectors have mean length
**0.998**, with **99.4%** of island texels within 0.9–1.1 — the map is a clean
unit-normal field, no broken quadrants or inverted channels.

**Render check (error check 2):** same camera/light/world for both —
**silhouette IoU 0.987** between sculpt and baked cage (in line with B2's
geometry-only IoUs of 0.978–0.992), **foreground mean absolute pixel difference
15.3 / 255 (≈6%)**. That 6% is the honest price of the whole retopo+bake split
at these settings: it includes intended normal-map shading correction over the
coarse cage plus genuine losses (§4). Visually (`renders/comparison.png`) the
baked cage preserves skin mottling, the red war-paint, topknot and band, brow
horns, tusks, dentition and expression folds.

**Coverage note (a Blender 5.2 behaviour worth recording):** NORMAL, AO and
EMIT bakes write **opaque alpha across the whole canvas**, so their "fill"
reads 1.0 and means nothing. Only the DIFFUSE bake preserves true per-texel
coverage alpha — island coverage (77.3%) and all in-island stats above are
masked by it. Whole-canvas stats for the other passes are background-contaminated
and should never be quoted.

## 4. Honest limits

1. **Local bake artifact at the ear plug.** The baked render shows a small
   dark, scrambled patch at the earlobe gauge/plug where the sculpt reads
   clean. Likely ray confusion at the 2.0 u cage offset: the plug is a shallow
   inset disc, and rays starting 2 u out can land on the lobe behind it.
   Known fixes (not applied): explode-the-parts bake, a locally tighter cage,
   or masking the plug to its own bake. It is the only visible map defect in
   the comparison view.
2. **Automatic UVs.** Smart UV Project seams are machine-placed; at 2048² over
   a whole head, fine sculpt detail (hair strands, pores) renders softer than
   the sculpt, and seam-adjacent stretching exists by construction. A hero
   pass = hand seams + 4096² + a separate teeth/eye material split.
3. **The GLB does not carry the AO.** The colour×AO multiply is a Blender node
   construct glTF can't express; the exporter embedded normal + colour +
   curvature (as the roughness texture) and **no occlusion texture**. In the
   comparison render the AO *is* applied. Standard fix: multiply AO into the
   diffuse as a texture post-process, or ship it in the glTF occlusion slot —
   neither done here.
4. **Colour source is vertex colours.** The sculpt has no painted textures;
   the diffuse bake can only be as rich as its `COLOR_0` layer (which, to its
   credit, includes the war paint). A textured sculpt would bake identically
   through the same stage.
5. **One view, 32 samples.** The render check is a single three-quarter view
   at moderate sampling; silhouette/MAE numbers are for that view. B2's
   three-view silhouette study remains the geometric reference.
6. **The cage is still not an animation head** (B2's caveat stands): no
   anatomical eye/mouth loops were added at any point in this stage. Baking
   makes the automatic cage *presentable*, not *rig-ready*.

## 5. Two process gotchas (for whoever reruns this)

- **Zero-user image datablocks are purged when a .blend is saved.** Stage 1's
  blend kept only the last-baked image (the one still wired into the bake
  material); the other three vanished from `bpy.data.images` on reopen.
  Stage 2 therefore loads maps **from the PNGs on disk** — treat the files,
  not the blend, as the source of truth. (Set `use_fake_user` if a blend must
  carry them.)
- **Baking is fast; rendering the sculpt is the slow part** (70 s vs 55 s for
  the cage at 768²/32 spp) — and B2's warning stands: keep sculpt renders in
  their own process on this VM.
