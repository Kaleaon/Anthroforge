# A4 — Stylised Fur Clumps

**Fur-craft wave, agent A4 · Nov 12, 2026.**
**Question:** how do stylised/toony artists (the stylised base packs,
kemono bases, furry character art) do fur — and can that language be a
*parts library* under `PARTS_STANDARD.md`, the way strands/cards are
for the realistic end?

**Answer in one line:** stylised fur is not strands and not texture —
it is a small set of **solid, sculpted clumps**: flattened teardrop
spikes with bent centrelines, layered big-to-small, placed only where
fur breaks the silhouette. Four prototype parts below prove the
construction, the costing, and the seating.

Companion files: `parts/` (GLB + STL + `.part.json` per part,
`fur_clumps_demo.blend`), `renders/`, `work/build_clumps.py`,
`work/render_clumps.py`.

---

## 1. What the study found (sources)

1. **Fur zones are few and named.** A fursona-modelling guide's
   Blender pass works "in four zones and leave the rest painted: the
   **neck ruff and chest floof**, the **cheek fur**, the **tail**, and
   the **forearm and hock tufts** account for nearly all the visible
   fur silhouette on an anthro character" — geometry anywhere else
   "reads as a shag carpet." (threedium.io fursona guide)
2. **Clump topology doctrine** (Tripo's stylised-hair-clump guide):
   "major forms over minor details; edge loops follow flow lines;
   density is strategic — more geometry where the silhouette curves
   sharply." Block in the big masses at low subdivision first; 3–4
   supporting loops along any length that must bend, tightest at the
   root and at the point of greatest bend.
3. **The extrude-and-sharpen tuft method** used by working stylised
   artists (Vully/@usbfig, Instagram tutorial, Sep 2026; Abe Leal's
   low-poly hair tip): extrude small polygon groups out of the body
   surface, sculpt them into spikes, **mark the tuft edges sharp** so
   the point survives shading. Silhouette is the whole game: "adding
   extra geometry, even on low-poly elements, enhances visual
   interest" precisely at the outline.
4. **2D fur language transfers directly** (digital fur-painting
   guides, furry character art): fur groups into **short clumps and
   tufts**, never individual strands; flow arrows run back from the
   nose, down the neck, down the legs, swirling at chest and joints;
   the silhouette is *broken all around* by tufts pulled past the
   edge; each clump is a lit top over a darker gap beneath — in 3D
   terms: one flat tone per clump face family, gaps read as the
   spaces between clumps.
5. **Coat length changes the clump dialect:** dense/fluffy coats
   (husky) = small, rounded, blended clumps; medium coats (fox, cat)
   = visible separated clumps at cheeks/chest/tail; wiry coats =
   irregular spiky silhouettes. One clump *profile family* per dialect
   (see rule C3), not one universal spike.

## 2. Construction rules (the deliverable doctrine)

- **C1 — Silhouette-first.** A clump earns its polygons only if it
  changes the outline from some common view. Interior fur is paint/
  texture territory. Place clumps at silhouette zones (cheeks, jaw
  line, neck/chest, ear rims and bowls, tail, hocks/forearms) and
  nowhere else by default.
- **C2 — One clump = one lathe-profile spike.** Profile: plump base
  (≈62% of max radius at the root so it seats), full at ~18% of
  length, then a long taper — 86% → 55% → 24% → a true point at
  100%. Never a cone (too even) and never a blob (no point = no fur
  read). The prototype profile is the table in `build_clumps.py`.
- **C3 — Flatten across the flow.** Cross-sections are ellipses,
  minor axis ≈ 0.6 × major, thin axis in the bend plane. A round
  spike reads as a thorn; a blade reads as fur. Dialects vary the
  numbers: fluffy 0.75, medium 0.6, wiry 0.45 + irregular lengths.
- **C4 — Bend the centreline, don't kink the mesh.** Droop grows
  quadratically toward the tip (gravity + growth direction), ≈ 0.4 ×
  length of total drop for hanging cheek/ruff clumps, less (0.2) for
  ear tufts that stand. 5–6 rings carry the bend; ring twist ≈ 14°
  over the length keeps faces from lining up into a prism.
- **C5 — Big-to-small, always in threes.** A fur feature is a fan:
  one hero clump, flanked by smaller ones at descending lengths
  (≈ 1.0 / 0.8 / 0.65), roots stepping along the flow line. A single
  spike is a horn; a fan is fur. (Cheek set: 0.195 hero, 0.150,
  0.160 descending the jaw.)
- **C6 — Layer shells, short under long.** Volume fur (tails, ruffs
  on a body) is two layers: short clumps rooted on the surface,
  hugging it; long clumps rooted the same way, standing off. The
  tail set ships 8 inner + 6 outer. One layer reads as spikes on a
  stick; two read as a coat.
- **C7 — Root below the surface, tip past it.** Roots bury 8–15 mm
  (at head scale) into the base so no gap can open under animation;
  the base fan is recessed so the root seats as a shallow cone.
  Burial at the root is correct seating, not a fit defect — the fit
  metric agrees (excess stays 0.0% when roots seat and bodies don't
  swallow).
- **C8 — Flat shading is the finish.** Graphic clumps shade flat
  (one tone per face); smooth shading melts the spike read into
  blobs. If a smooth pipeline must be used, mark silhouette edges
  sharp instead (the extrude-method artists' rule).
- **C9 — Fur inherits, never rigs itself.** Clumps are class A with
  `skin.mode: inherit` — weights transfer from the base at equip
  (blueprint §8.4). A cheek tuft split across Head/Jaw weights
  follows the jaw; ear tufts inherit the ear chain so they cannot
  lag ear carriage (ears carry ~half the expression vocabulary).
  No clump part ships its own bones; cost stays at the floor.
- **C10 — Cost discipline.** One clump ≈ 32 verts / 60 tris; a whole
  head set (cheeks + ears + ruff) = 480 verts and **3 points** of
  the 128-point character pool. If a fur feature costs more than a
  detail-class 4 points, it is being built wrong — decimate the
  profile, not the count of clumps (the count is the look).

## 3. The prototype parts

All authored procedurally in-house (no external asset), seated on
`neutral_base_head_v3` in its own frame (metres, L = 1.0). Records:
`parts/*.part.json` (PARTS_STANDARD §3.4 + [PS] fields).

| Part | Socket | Construction | Verts / tris | Points | Fit (§5) |
|---|---|---|---|---|---|
| `fur_cheek_tufts` | `hair` | 3-clump fan × 2 sides, descending the jaw side, tips past the jawline | 192 / 360 | 1 | **0.716 partial** |
| `fur_ear_tufts` | `ear.L/R` | 2 clumps × 2 ears, rooted in the bowl, standing up-in | 128 / 240 | 1 | **0.936 fitted** |
| `fur_chest_ruff` | `neck.ruff` | 5-clump throat fan under the chin, hanging down-back | 160 / 300 | 1 | **0.549 partial** |
| `fur_tail_clumps` | `tail.base` | 8 inner + 6 outer clumps on a tapered core (local tail frame) | 448 / 840 | 1 | **0.362 — below gate** |

Demo assembly: `parts/fur_clumps_demo.blend` (head + the three head
parts; tail set at its own origin). Renders: `renders/`.

## 4. Seating notes (per part)

- **Cheek tufts** root along the jaw side at x ≈ ±0.24 (head
  half-width 0.273), stepping down-back; directions fan from
  down-back to mostly-down so the fan's tips break the jawline
  silhouette in front, side, and three-quarter views.
- **Ear tufts** root at the ear bowl's base (x ≈ ±0.27–0.29) and
  stand up-inward — inside the ear's own silhouette, so they read in
  front view as inner-ear fur, the standard kemono tell.
- **Chest ruff** took three placements, and the render — not the
  score — caught the first two: (1) roots up inside the skull
  volume, hanging straight down: score 0.002, invisible in render.
  (2) roots on the neck-stub rim at the back of the jaw: score
  0.351, but the side render showed nape spikes under the occiput,
  not a ruff. (3) **final:** a throat fan — roots under the chin
  along the throat underside (y +0.06…−0.10, z ≈ −0.28…−0.30),
  hanging down with a slight back sweep: score **0.549**, and the
  side render reads as a ruff under the jaw. Lesson recorded for
  the standard: on a head-only base, `neck.ruff` demos seat on the
  throat, and a plausible fit score cannot substitute for looking
  at the render. On a full body the fan extends onto the chest,
  which this base doesn't have.
- **Tail clumps** ship in a documented local frame (origin at
  `tail.base`, −Y posterior, +Z up) around a tapered proxy core
  (radius 0.046 → 0.020 over 0.52 m, `parts/tail_core_proxy.stl`) —
  the frame the tail fitter consumes.

## 5. Fit scoring — results and an honest metric finding

Scored with `parts-lab/fit_score.py` against per-socket base
assemblies (PARTS_STANDARD §5.1's union rule — scoring ear tufts
against a base *without* ears returned 0.55 for correctly seated
parts; with ears in the assembly, 0.936).

- **Ear tufts 0.936, cheek tufts 0.716, chest ruff 0.549** — fitted /
  partial-with-note, all in shippable bands. Burial is root seating;
  excess 0.0% (ruff 2.89% at the centre root cone).
- **Tail 0.362 falls below the 0.40 intake line and is recorded as a
  prototype that does not ship.** Attempts to raise it by geometry
  (shorter, tighter inner layer; deeper roots; more inner clumps)
  moved the score by ≤ 0.02 while improving the actual seating
  little — for a layered shell on a thin core, the score is not
  measuring bad seating:
  - The metric rewards verts near a base *surface*. A hanging ruff
    and a clump shell are mostly **stand-off by design** — the
    stand-off is the fur volume. Excess is 0.0% and roots bury
    correctly on both; what fails is engagement, because most of
    the part is legitimately in free space.
  - The engagement band is 3 voxels, so it scales with the union
    bbox: 3.2 cm against the head, only 1.34 cm against the thin
    tail assembly — thin bases are graded harder for the same
    geometry.
  - (The ruff showed the complementary case: its sub-gate scores
    *were* placement bugs, and fixing placement — guided by the
    render — moved it 0.002 → 0.351 → 0.549. The metric is a good
    smoke alarm; it is not the fire's location.)
- **Proposal back to the parts standard:** fur shells need a
  root-engagement variant — engagement measured over root rings
  (must be ≥ 90% buried-or-banded) **plus** a stand-off allowance:
  a vert is "accounted" if its distance to the base ≤ its clump's
  designed stand-off at that ring. Until that variant exists, the
  tail set stays prototype-flagged with its standard score on
  record. Do not tune clump geometry to the current metric — that
  path ends with fur glued flat to the skin, which is the one thing
  stylised fur must never do.

## 6. Limits / next steps

- Prototype profiles are one dialect (medium coat). Fluffy and wiry
  variants are parameter changes (C3), not new parts — worth one
  follow-up set each before this library grows.
- All parts are `inherit` weight mode; the jaw-split behaviour of
  cheek tufts (C9) is asserted by the weight-transfer design, not
  yet demonstrated on the skinned v2 rig.
- Leg feathering (forearm/hock tufts — the fourth fur zone) is the
  obvious fifth part; it needs a body base, not this head.
- The tail score must be re-run under the proposed root-engagement
  metric before the set ships; the ruff should be re-scored against
  a headed body base when one exists.
- The tail set's clump distribution is underside-weighted by design
  (a hanging fringe + top/side fillers); the render reads as fringe
  on a core rather than full tail volume. A full-coverage variant
  is an azimuth-distribution parameter change, and in production
  the grey proxy core is replaced by the character's own tail mesh
  plus painted undercoat — the clumps are the silhouette layer, not
  the whole tail.
