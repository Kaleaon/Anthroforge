# Fur Atlas & UV Strategy — FUR_ATLAS.md

**Status:** spec v1 + working prototype. Atlas packed from the fur-prototype's
production card bakes, LOD0 cards remapped onto it and QA-validated.
**Deliverables in this folder:** `fur_atlas_2048.png` (the atlas),
`fur_atlas_layout.json` (machine-readable slot rects, both UV spaces),
`fur_cards_lod0_atlas.glb` (prototype cards on the atlas, one material),
`uv_layout_diagram.png` (annotated layout), `scripts/` (packer + remapper).

---

## 1. Why an atlas, and what was wrong before

The fur prototype shipped its cards with **two separate 512×1024 textures,
both embedded in every LOD file**, picked per-card by material index
(`FurCardA` / `FurCardB`). That costs two texture binds and two materials per
card mesh, duplicates the same ~2.3 MB of PNG in all three LOD GLBs, and gives
the baker no shared discipline: no padding standard, no variant system, no
place for utility data (gradients, IDs) to live. The atlas replaces all of it
with **one texture, one material, eight named slots** whose meaning is fixed
across resolutions and across companion maps (normal / ID / flow).

Inspection for this study also surfaced three defects in the current assets.
They are recorded here because the atlas pipeline is where they get fixed:

1. **`fur_cards_lod0.glb` embeds the wrong bake.** Its two embedded images
   (sha256 `c640b9bb40e3…`, `48a83f527db3…`) are the *v1* card bake — the one
   whose framing caught the tilted emitter plane diagonally in shot (see
   `work/embedded_0.png`). LOD1/LOD2, exported later from the recovered
   scene, embed the correct v2 bakes byte-identically (LOD1 image 0 hashes
   to `4b1074f90300…`, the standalone `fur_card_texture_a.png` exactly).
   So the hero LOD — the file anyone loads first — is the broken one, and
   would render dark diagonal slabs instead of hair curtains in any glTF
   viewer. (The Blender renders in FUR_PROTOTYPE.md are unaffected: in
   scene, the materials read the fixed files from disk; only the packed
   GLB copies went stale.) The remapped GLB in this folder is the first
   LOD0 whose texture is the real v2 curtain, via the atlas.
2. **Raw bake alpha cannot survive an alpha test.** The standalone bakes
   carry raw Cycles coverage alpha: max 0.584 (A) / 0.459 (B), and coverage
   at a standard 0.5 cutoff is **0.01 % (A) and 0.00 % (B)** — the strands
   are ~1 texel wide, so almost no texel is half-covered. The prototype
   material masked this with hashed dithered blending (effective opacity ≈
   alpha ≈ 6 % mean), which is part of why the card coat read as sparse
   clay-with-tufts. §5 defines the renormalisation curve that is now a
   mandatory pack-time step.
3. **Bake density is top-loaded.** Alpha mass by row decile of texture A
   (top→bottom): 0.026, 0.138, 0.126, 0.108, 0.088, 0.069, 0.048, 0.028,
   0.008, 0.000 — the bottom ~10 % of the frame is empty and the strand
   field effectively ends around 85 % of the height. §4's framing rule
   reclaims that texel budget.

## 2. The layout standard

One canonical grid, three resolutions. Slot semantics are identical at every
tier, so a character's UVs never change meaning when the tier does — only
the rect coordinates scale.

| Tier | Atlas | Cell | Usable | Pad | Audience |
|---|---|---|---|---|---|
| AF-FUR-2048 | 2048×2048 | 512×1024 | 480×992 | 16 px | hero / desktop |
| AF-FUR-1024 | 1024×1024 | 256×512 | 240×496 | 8 px | mobile, Telegram Mini App (WebGL) |
| AF-FUR-512 | 512×512 | 128×256 | 120×248 | 4 px | far LOD, low-end |

Grid: **4 columns × 2 rows**, portrait cells (1:2) — the aspect of a hanging
strand curtain, and the orientation long-hair card workflows standardise on
(planning textures are laid out wide and cut into cards; here the curtain is
baked per-slot instead). Eight slots:

| # | Slot | Content | Role |
|---|---|---|---|
| 0 | `DENSE_A` | full-density curtain (proto texture A) | LOD0/LOD1 workhorse |
| 1 | `SPARSE_B` | low-density curtain (proto texture B) | layering, cheap fill, see-through depth |
| 2 | `DENSE_A_MIR` | slot 0 mirrored in U | second silhouette, zero extra geometry cost |
| 3 | `SPARSE_B_MIR` | slot 1 mirrored in U | second sparse silhouette |
| 4 | `CORE_A` | A with alpha^(1.5)×1.35 | high-coverage under-layer; the "you cannot see through the coat" card |
| 5 | `CLUMP_A` | centre crop of A, rescaled | fewer, thicker clumps per card; ruff/mane cards |
| 6 | `THIN_FAR` | A, alpha eroded 3×3 then ×0.8 | LOD2 / distance cards — pre-thinned so distance thinning is art-directed, not mip-accidental |
| 7 | `UTILITY` | four vertical strips, see below | shader data, not cards |

`UTILITY` strips (usable-local x ranges, 480-wide usable): **gradient LUT**
0–96 (value 1.0 at root → 0.0 at tip; a shader samples it at the card's own
`s` to recover normalised shaft position for root/tip colour, root AO, and
tip fade, independent of slot), **underfur puff** 96–240 (heavily blurred
alpha blob in the species' mean coat colour — the shell/undercoat card),
**wisp** 240–336 (a 64-px centre column of B stretched — 1–2 strand flyaway
cards), **reserved** 336–480 (flat root colour, alpha 0; earmarked for a
flow/ID strip when the fur shader lands).

Prototype slot contents are all derived from the two real bakes by named
operations (mirror, crop, alpha curve, erosion, blur) — no painted filler —
so the pack is honest about how much variety two bakes buy: four silhouettes,
two densities, one clump read. More bakes widen variety *within the same
grid*; the grid does not change.

**Companion maps.** Normal, ID, and flow maps reuse this exact grid — slot *n*
is the same card in every map of the set. (A8's card-texture work already
bakes a tangent-space normal beside its RGBA with the same root-at-top
discipline; see the integration note in §9.)

## 3. UV rules

- **Root at the top.** In image space, row 0 of every cell is the ROOT edge;
  strands read downward, root → tip. Cell-local shaft coordinate
  `s ∈ [0,1]`, `s = 0` at root, `s = 1` at tip, measured inside the
  **usable rect** (never the cell — the pad ring is not UV domain).
- **Card UVs span the usable rect exactly.** A card's across coordinate maps
  `u ∈ [0,1]` → usable width; its length maps `s` → usable height. No card
  UV may enter the pad ring; the ring exists only to be sampled *by
  filtering*, never by address.
- **glTF form.** glTF measures `v` from the image's top row as
  `v = 1 − row/H` in the convention our exporter chain produces (the
  prototype's card roots carry `v = 1.0` and sample image row 0). A usable
  rect at pixel `(x, y, w, h)` in a `W×H` atlas therefore has
  `uv_gltf = [x/W, 1−(y+h)/H, (x+w)/W, 1−y/H]`, and the rect's **root edge
  is its v1 side**. `fur_atlas_layout.json` records every slot in both
  image space and glTF space; the remapper consumes the glTF form.
- **Remapping is a pure rect transform.** `u' = u0 + u·(u1−u0)`,
  `v' = v0 + v·(v1−v0)` — orientation-preserving, so a card that was
  correct against its standalone texture is correct against its slot.
  Verified on the prototype: both remapped primitives' UV ranges land
  exactly on their slots' usable rects.
- **Mirroring is a slot choice, not a UV trick.** Cards never use negative
  or wrapped UVs to fake variety; they point at the `_MIR` slot. This keeps
  tangent-space normals and any future flow map consistent per slot.
- **Clump islands.** Wide cards (slot 5) are whole-cell citizens, not
  sub-rects: if a future bake produces several clump islands per cell, each
  island keeps its own root edge on the cell's root side and islands never
  share a row band — a card must be able to take any single island as its
  full UV without crossing a neighbour.
- **No tiling inside a card.** A card samples its slot once, root to tip.
  (A8's bake tiles in U for *strand-field* authoring; that is a bake-time
  property of the field, not a licence for card UVs to wrap.)

## 4. Texel density

Measured on the prototype at the 2048 tier (usable 480 px across, 992 px
along shaft; card widths and groom lengths from FUR_PROTOTYPE.md):

| Region | Card width | Across | Strand length | Along shaft |
|---|---|---|---|---|
| ruff | 30 mm | 16.0 px/mm | 170 mm | 5.8 px/mm |
| back | 24 mm | 20.0 px/mm | 95 mm | 10.4 px/mm |
| coat | 22 mm | 21.8 px/mm | 66 mm | 15.0 px/mm |
| belly | 16 mm | 30.0 px/mm | 42 mm | 23.6 px/mm |

Targets: **≥ 16 px/mm across-strand and ≥ 6 px/mm along-shaft at the hero
tier** (halve per tier down). Across-strand density is the one that carries
silhouette and strand separation; along-shaft can run lower because strands
are near-parallel and detail along a strand is mostly the root→tip gradient.
The ruff sits at the floor on both axes — it is the longest, widest card and
the most visible; if any region earns a dedicated high-density slot in a
future pack, it is this one.

**Framing rule (bake-time).** The strand field must fill ≥ 95 % of the
cell height: roots within the top 2 % of the frame, tips reaching the
bottom 5 %. The current bakes end at ~85 % (§1.3) — reframing the curtain
bake to fill the cell is a ~1.15× along-shaft density gain for free, and it
makes `s` mean the same thing in every slot.

## 5. Alpha, cutoff, and mips

**Contract:** materials alpha-test (or alpha-to-coverage) at **cutoff 0.5**;
all coverage numbers below are stated at that cutoff so bake, atlas, and
material agree on one number (a coverage figure is meaningless without its
threshold).

**ATLAS-ALPHA-1 (mandatory at bake/pack time).** Raw rendered coverage
alpha is renormalised per atlas:

```
a' = clamp( (a − 0.02) / (t1 − 0.02) )
```

with `t1` solved per source set so the DENSE slot lands at **0.15 coverage**
at mip 0. For the prototype's bakes, `t1 = 0.231`. Resulting coverage:

| Source | raw mip0 | renorm mip0 | mip1 | mip2 | mip3 | mip4 |
|---|---|---|---|---|---|---|
| A (DENSE) | 0.0001 | 0.143 | 0.154 | 0.142 | 0.127 | 0.107 |
| B (SPARSE) | 0.0000 | 0.034 | 0.018 | 0.005 | 0.0001 | 0.000 |

Two lessons ride on this table. (a) After renormalisation the DENSE slot is
unusually mip-stable — neighbouring strand texels average *above* threshold
— losing only ~25 % of coverage by mip 4. (b) SPARSE collapses with
distance no matter the curve: thin isolated strands cannot survive
downsampling. **Rule:** SPARSE slots are near/mid-range cards only; distance
mass comes from DENSE and THIN_FAR, whose erosion is authored, not
accidental. Where the renderer supports it, prefer **coverage-preserving
custom mips** (rescale each mip's alpha so its coverage at 0.5 matches the
mip-0 target) and generate mips with premultiplied-alpha weighting.
Alpha-to-coverage (MSAA) is an acceptable substitute at LOD0; hashed
dithering — the prototype's crutch — is not a shipping mode.

**Cutoff discipline.** If a material ever ships a different cutoff, the
atlas's coverage targets must be re-solved at that cutoff; do not reuse
0.5-solved curves under a 0.33 material.

## 6. Bleed: padding and dilation

- **Padding scales with atlas size** (the standard edge-padding rule):
  512 → 4 px, 1024 → 8 px, 2048 → 16 px. The pad lives *inside* the cell,
  so the gutter between two usable rects is always 2× the pad (32 px at
  hero) — the ratio that keeps neighbouring slots from donating colour to
  each other until deep mips.
- **Dilate RGB, not alpha.** Every non-usable texel's RGB is filled by
  push-pull diffusion from the nearest usable edge (the packer in
  `scripts/build_atlas.py` does a weighted pyramid fill); gutter alpha
  stays 0. RGB dilation is what filtering actually samples across an edge;
  dilated *alpha* would grow silhouettes at distance.
- **Mips are generated premultiplied.** Colour from a zero-alpha gutter
  texel then contributes nothing, and the dilation only has to serve the
  non-premultiplied paths (some WebGL pipelines, hashed modes) and the
  first mip levels.
- Cards at **cell borders of the whole atlas** get the same pad — the atlas
  edge is a gutter like any other; texture wrap is CLAMP, never REPEAT,
  across the atlas as a whole.

## 7. Memory budgets

Per character, one atlas (albedo+alpha), all LODs sharing it:

| Tier | RGBA8 | + mips | BC7 / ASTC 4×4 | + mips | ASTC 6×6 | + mips |
|---|---|---|---|---|---|---|
| 2048 | 16.8 MB | 22.4 MB | 4.2 MB | 5.6 MB | 1.9 MB | 2.5 MB |
| 1024 | 4.2 MB | 5.6 MB | 1.05 MB | 1.4 MB | 0.47 MB | 0.62 MB |
| 512 | 1.05 MB | 1.4 MB | 0.26 MB | 0.35 MB | 0.12 MB | 0.16 MB |

Budget rule: **hero characters ≤ 5.6 MB of fur texture on desktop
(2048 BC7 + mips), ≤ 1.4 MB in the Mini App (1024 BC7 + mips)**; a second
atlas page (§8) doubles the line item and needs a reason. Companion maps
(normal at half resolution, ID/flow packed into channels) budget separately
at ≤ 50 % of the albedo line.

Against the status quo: the prototype embeds ~2.3 MB of PNG *per LOD file*
(and unquantised RGBA+mips would be ~5.3 MB resident), with two binds and
no variants. The atlas at 1024 BC7 carries eight slots for 1.4 MB resident
— and the LOD files stop carrying textures at all.

**Shipping format is KTX2/BC7 (desktop) or ASTC (mobile), never PNG-in-GLB.**
The prototype GLB here embeds the PNG atlas and is 9.6 MB for that reason
alone; it is a correctness proof, not a size proof.

## 8. Per-species plan

**One layout for every species; species do not get private atlases by
default.** What differs between a wolf, a fox, and a lion is coat *colour,
length, and groom* — colour is supplied by the markings system's fur-colour
function as a material tint over a neutral-brown bake, length and density
live in the groom/region maps, and the slots are structure, not species.
Concretely:

- **Page 1 (the standard page)** — the layout of §2, baked in a neutral
  mid-brown. Serves all straight/medium coats: wolf, fox, fennec, dog,
  cat, lion (mane cards draw on `CLUMP_A` + a longer groom, not new
  texture), bear, and the Titan presets. Sen's chest crescent, fennec ear
  backs, tiger striping — all are markings-layer colour over this page.
- **Page 2 (structure variants)** — same grid, different bakes, opened
  only when strand *structure* changes: curly/wire coats, the orc's coarse
  bristle, wet-look clumping. A character references page 1, page 2, or
  per-region pages (page 2 slots for the ruff only, say) — the slot
  semantics make mixing safe.
- **Never** per-species tint atlases: tint in the material, always. A new
  species added to the library costs zero texture memory until it needs a
  new strand structure.

## 9. Packing pipeline (normative)

1. **Bake** strand curtains per slot family (framing rule §4; strands
   ≥ 2 texels wide at bake resolution — draw/render them fat and let the
   curve in step 2 set final coverage; the prototype's ~1-texel strands
   are why its raw coverage was unrecoverable).
2. **Renormalise** alpha (ATLAS-ALPHA-1, §5); record the solved `t1` and
   the coverage table in the pack's layout JSON.
3. **Derive** the slot set (mirror / core / clump / thin / utility) by the
   named operations — derivations are code, not hand edits.
4. **Pack** into the grid; **dilate** gutter RGB (push-pull); alpha outside
   usable rects = 0.
5. **Compress** to KTX2 (BC7/ASTC) with premultiplied, coverage-checked
   custom mips where the tooling allows.
6. **Remap** card UVs by the rect transform (§3) and **regenerate any
   shipped GLB from the packed atlas** — the LOD0 defect in §1.1 is what
   happens when packed files and their sources drift apart; the packer,
   not the artist, owns the final bytes. `scripts/remap_glb.py` is the
   reference implementation.

**Validation of the prototype pack:** remapped LOD0 passes the QA gauntlet
— 17,832 verts / 13,600 tris (identical to source), 1 embedded texture /
0 external, 0 degenerate, 0 NaN, extent 2.129 m; both primitives' UVs
verified inside their slots' usable rects; materials collapsed 2 → 1.

**Integration note (A8).** A8's in-progress card bakes are 512×512 RGBA +
normal with per-variant seeds and their own (compatible) root→tip and
edge-bleed discipline. If A8 textures are adopted as slot sources, either
their bake moves to the 1:2 cell aspect or the grid gains a 1:1 row —
one decision, to be taken when A8 lands; the slot semantics, UV rules,
alpha contract, and bleed rules in this spec apply unchanged either way.

## 10. Open items

- Bake reframing + ≥ 2-texel strands (step 1) — the single largest quality
  lever; belongs to the card-texture line (A8), this spec only sets the
  targets it must hit.
- KTX2 tooling in the export pipeline (BC7/ASTC + custom mip coverage).
- LOD1/LOD2 remaps onto the atlas (same transform; their embedded textures
  are the correct v2 bakes, so this is deduplication, not repair — LOD0
  was the repair).
- The UTILITY reserved strip's flow/ID encoding, when the fur shader is
  specified.
- A ruff-dedicated high-density slot if hero close-ups demand it (§4).
