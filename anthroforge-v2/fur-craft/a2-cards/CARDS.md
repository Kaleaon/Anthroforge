# Fur Card Geometry Craft — CARDS.md (A2)

**Agent A2, fur-craft wave (Nov 12, 2026).** How fur *cards* — the geometry,
not the texture — should be shaped: profiles, bend, segmentation, crossed
planes, width/length ratios per zone, and what happens to the silhouette at
grazing angles. Companion studies: A8 (the textures these cards carry,
`a8-cardtextures/CARD_TEXTURES.md`), A5 (budgets, `a5-budgets/FUR_BUDGETS.md`),
A13 (atlas/UV contract, `a13-atlas/FUR_ATLAS.md`).

**Labels:** **[M]** measured this pass · **[S]** sourced (citation in §7) ·
**[E]** estimate/derived by arithmetic.

**Deliverables in this folder:** `cards/*.glb` — six card families at a
normalised size (L = 100 mm, W = 30 mm, root at origin, growth +Z, UVs set);
`cards_patch_demo.glb` + `a2_cards_demo.blend` — the six test patches with
A8 textures applied; `renders/patch_<family>_{front,grazing}.png`;
`work/` — builders (`card_geo.py`, `build_cards.py`, `build_patch.py`) and
measurement scripts + JSON.

---

## 1. The card is a system: geometry × alpha

The single most consistent rule in the production literature: **the mesh and
the alpha texture are one unit, designed together** [S]. The mesh silhouette
should track the texture's opaque core, not its bounding box — a rectangular
card under a tapered alpha wastes overdraw on texels that will be discarded,
and an outline that cuts through the alpha's clump teeth pixelates them [S].
Our A8 bakes make this concrete: coverage at alpha > 0.5 is 0.74–0.82 [M, A8]
with a tip envelope that narrows as t^1.4 and clump teeth carved by strands
converging to shared tips. The geometry rules below are written against that
alpha: card width taper follows the alpha envelope, fork prongs land on the
clumped texture's strand bundles, and nothing in the geometry may contradict
the texture's root→tip direction.

**Root burial.** Cards root 3–5 mm *under* the skin surface and the texture's
root edge fades over its bottom 4 % (A8) — together these hide the card/skin
junction at any angle the coat itself is visible from [S: cards "intersect
the scalp slightly", plus a textured under-layer beneath].

## 2. Profiles — the six families

| Family | Shape | Tris | Texture | Intended zone |
|---|---|---:|---|---|
| `ribbon_flat` | single plane, width taper 1→0.58 | 8 | straight | coat, back — the A5 baseline card |
| `ribbon_bent` | single plane, 42° arc baked in | 12 | wavy | neck, chest, anywhere fur lies over a curve |
| `ribbon_fork` | shared base → 2 prongs at s = 0.58 | 12 | clumped | ruff edges, cheeks, between-clump gaps |
| `cross_pair` | two flat ribbons at 90° | 16 | guard_ruff | ruff/mane core (A5's cross-plane standard) |
| `tri_fan` | three bent ribbons at 60° yaw | 24 | clumped | hero silhouette tufts, tail base, ear tufts |
| `quad_shingle` | wide card, 3 across, centre V-fold | 12 | straight | short-coat zones: shoulders, hips, forearm feathering |

**Straight vs tapered.** A fur card is widest at the root and narrows toward
the tip, tracking the alpha envelope (A8 narrows lateral spread as t^1.4, so
geometry at 1→0.55–0.6 of root width keeps nearly all quad area inside the
alpha > 0.5 core while the texture supplies the fine taper) [E from A8 §1].
Never taper to a point in geometry: a triangle tip rasterises badly,
aliases at mips, and the alpha already ends the card.

**Forked.** The clumped bake's silhouette is *teeth* — strands converge to
~15 shared tips with real gaps between [M, A8]. A rectangular card forces
those teeth to live entirely in alpha; a forked card puts geometry into two
of the teeth so the gaps survive as true silhouette at grazing angles and
close range. The fork split (s ≈ 0.55–0.6) matters: earlier and the prongs
read as two cards (and the shared root's skinning breaks); later and the
gap is too short to register. Each prong samples its own u sub-range of the
texture (here [0.06–0.46] / [0.54–0.94]) so prongs carry different strand
bundles, not a stretched copy of the whole curtain.

**Multi-plane clusters.** Crossed pairs and tri-fans buy view-independence:
a single plane's projected area falls as |cos θ| and is gone by ~80°
(§5 measures this); a second plane at 90° guarantees one plane is never
more than 45° from face-on. The price is exact: ×2 or ×3 the triangles,
and intersecting planes show a hard crease line where they cross if the
alpha there is dense — clusters therefore take the *coarsest* textures
(guard_ruff, clumped) whose broken alpha hides the intersection [E].

## 3. Bend: geometry vs shader

Fur lies *over* a body: roots point along the skin normal, tips fall along
flow. That arc must exist in the silhouette, and the silhouette is geometry.

- **Bake the macro bend into the geometry.** A 30–45° arc over the card
  length is the difference between a coat and a mohawk of flat stickers.
  Cost: segments to carry the arc (below). Benefit: it works in every
  renderer we ship to — Babylon, SL (no custom vertex shaders), offline —
  and it is *true* in the depth buffer, so silhouette, shadow and occlusion
  all agree.
- **Shader bend is for motion, not shape.** A vertex-shader offset ∝ s² is
  the right place for wind sway and breathing (A17's states), layered on top
  of the baked arc. It must never be the only bend: it vanishes in any
  pipeline stage that doesn't run the shader (shadow maps in some engines,
  SL entirely, QA renders), and it cannot fix a silhouette the geometry
  doesn't have.
- **Bend placement along the card.** Real guard hairs leave the skin
  nearly straight, then arc. Our arc is circular (constant curvature) —
  measured acceptable in the patch renders, but a root-stiff profile
  (curvature ramping in after s ≈ 0.3) is the v2 refinement; Hair Tool's
  Bend Shape parameter (0 = bend at roots, 1 = at tips) exists precisely
  because artists reach for this control [S].

**Segments.** A5's baseline card is 4 segments / 8 tris. That is the floor
for a *straight* card (segments also carry skinning weight gradient — a
2-segment card folds like a hinge under animation [S: edge loops placed for
deformation control matter more than raw count]). A bent card needs 5–6
segments before its silhouette stops reading as facets at close range;
beyond 6 the returns vanish because the alpha's own teeth dominate the
silhouette. Rule: **4 segments straight, 6 bent, fork prongs get 2 each
past the split; LOD steps cut placements, not segments** (A5 §5 already
halves placements per tier — cutting segments instead would change the
silhouette's *character*, not just its density).

## 4. Width : length by zone

From A13 §4's measured card widths and A5 §4's zone lengths [M]:

| Zone | Length | Width | W : L | Family guidance |
|---|---:|---:|---:|---|
| Ruff / mane | 170 mm | 30 mm | 1 : 5.7 | cross_pair core + fork edges |
| Back / dorsal | 95 mm | 24 mm | 1 : 4.0 | bent ribbons |
| Coat | 66 mm | 22 mm | 1 : 3.0 | flat/bent ribbons |
| Tail plume | 120–200 mm | 30–40 mm | 1 : 4–5 | bent + tri_fan at base |
| Ear tufts / chin | 25–45 mm | 12–18 mm | 1 : 2–2.5 | quad_shingle, fork |
| Belly | 42 mm | 16 mm | 1 : 2.6 | shells/texture (A5) — not cards |

The ratio tightens as fur shortens: below ~1 : 2 a card reads as a leaf or
feather, not a fur clump (the alpha can't hold an opaque core across that
aspect at card texel densities, A13 §4); beyond ~1 : 7 the card is
strand-starved — mostly transparent texels and overdraw with no core [E].
Layering beats widening: production hair practice stacks ≥ 3 density
layers (dense cards low, sparse cards high) instead of growing individual
cards [S] — the same conclusion A5 reached from the budget side.

**Texel check.** A13's hero-tier targets (≥ 16 px/mm across, ≥ 6 px/mm
along shaft) are met by every row above at the 2048 tier; the ruff sits
exactly at the floor on both axes — if any zone earns wider geometry for
the same texture, it is the ruff, not narrower textures.

## 5. Grazing angles — where cards go to die

<!-- RESULTS: projected-area table + patch render stats appended by the
     build; see work/projected_area.json and work/render_stats.json -->

A coat is mostly *seen* at grazing angles: looking along a flank, a
shoulder, a tail. Three defences, in order of cost:

1. **Baked bend** turns part of every card toward a grazing viewer — a bent
   card's tip section presents its face when the root section is edge-on.
2. **Crossed/tri planes** cap the worst case: some plane is always within
   ~45–60° of face-on. This is the only defence that survives a viewer
   orbiting to the card's own plane.
3. **The V-fold (quad_shingle)** is the cheap middle: one extra vertex
   column buys a centre ridge whose two half-planes tilt ±~16° off the
   card plane, so the card never goes fully edge-on — at 12 tris it costs
   what a bent ribbon costs, and for short coats it is the better buy.

What does *not* work: relying on the under-layer. At grazing angles the
eye integrates along the surface; a textured skin under disappearing cards
reads as *painted* fur — acceptable as LOD2+ fallback (A5 rung 3), a
failure at hero distance.

## 6. Placement rules that belong to geometry

- **Layer order:** dense/CORE-type cards against the skin, sparse and
  forked cards outside — silhouette is authored by the outer layer, mass
  by the inner [S].
- **Yaw discipline:** single planes yaw within ±20° of flow; random-yaw
  singles produce the "straw" look. Clusters (cross/tri) may yaw freely —
  they have no wrong angle.
- **One card, one job:** a card that tries to be a whole tuft (too wide,
  too long, forked twice) deforms and reads badly; split it [S].
- **UV borders on straight edges:** keep the card's UV rectangle exact
  (A13: card UVs span the usable rect exactly); shape comes from the
  vertex outline and alpha, never from distorting UVs, which would smear
  the root→tip gradient the markings system depends on.

## 7. Sources

- Reallusion, *CC 3.4 Hair Mesh Production* — cross-shaped advanced cards,
  layering, cards close to scalp, avoid wasteful longitudinal divisions.
  https://wiki.reallusion.com/Content_Dev:CC_3.4_Hair_Mesh_Production
- Tripo3D, *Smart Mesh Topology for Hair Cards* — mesh planned around the
  alpha silhouette; edge loops follow flow; UV borders on straight edges.
  https://www.tripo3d.ai/blog/explore/smart-mesh-topology-for-hair-cards-assets
- Hair Tool 2 docs (Jose Conseco) — fur via instanced cards; Bend Factor /
  Bend Shape semantics (bend needs segments > 1; shape = root-vs-tip bias).
  https://joseconseco.github.io/HairToolDocs_28/main_workflows/short_hair/
- Mari Zatorska, *Real-time Hair Workflows* — density layering, wider
  cards near scalp, per-group constant widths.
  https://marizatorska.artstation.com/blog/9BDv/real-time-hair-workflows
- Internal: A5 FUR_BUDGETS (tri costs, zone table, LOD rules), A8
  CARD_TEXTURES (alpha envelopes, coverage), A13 FUR_ATLAS (UV rect,
  cutoff 0.5, texel targets).

## 8. Honest limits

- The prototype patches are *domes*, not anatomy: no concave regions
  (armpit, ear canal), no fur-over-fur layering against a second coat
  direction, and placement is a jittered grid, not a groom-derived flow
  field (A3/A7 own flow). Grazing numbers are therefore best-case for
  singles — real flow misalignment makes singles worse, clusters barely
  change.
- Projected-area measurement samples the alpha at tri centroids/barycentric
  grids — it is a geometry×alpha integral, not a render; the renders are
  the cross-check, at 32 Cycles samples with cutout (no hashed blending),
  so render coverage reads slightly harsher than a blended production
  material would.
- A8 standalone textures carry the root at **v = 0** (image bottom —
  verified by row statistics [M]); A13 atlas slots carry it at the v = 1
  side. These GLBs follow A8. Whoever packs A8 bakes into A13 slots must
  flip V at pack time or every card ships upside-down — pale roots,
  black tips.
- Cross/tri clusters were measured unskinned. Under animation their
  intersection crease can pump; the mitigation is root-weight discipline
  (cluster verts weighted to the same bone gradient as singles), not
  geometry — flagged for the rigging pass, not solved here.
- One dome curvature (R = 0.5 m) at one card scale per family. Shoulder-
  radius curvature (R ≈ 0.08 m) will splay card roots noticeably more;
  not measured.
