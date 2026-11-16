# Print Fur — the fur plan (A18)

*Fur-craft wave, Nov 12, 2026. Extends [MARKINGS.md](../../MARKINGS.md) §7's print/fursuit
profile — which exports marking masks as stencil PNGs — from **colour** to **fur itself**:
direction, pile length, and fabric pieces. Worked example built on the library's neutral
base head v3. Machine-readable companion: [`furplan.json`](furplan.json).*

---

## 1. How digital fur becomes physical fur (the study)

A digital groom is a direction field + a length field + a colour field on a surface.
A fursuit is **cut pieces of one-way fabric, shaved to length, sewn at colour boundaries**.
The fur plan is the translation layer between those two descriptions. Four facts of the
physical craft drive the whole format:

### 1.1 Nap is a hard constraint, not a style choice

Faux fur is a warp-knit backing with a dominant pile direction (the *nap*). Pile reflects
light anisotropically: two panels of the *same* fur sewn with opposite nap read as
different colours/densities, and the error is unfixable after sewing. Craft practice is
unanimous:

- Mark **nap arrows on the backing of every piece** (chalk/marker) before cutting; lay all
  pieces on the roll with arrows aligned — fur is cut **single-ply**, never folded.
- Cut from the **backing side with a blade** (razor/X-Acto), slicing only the knit so the
  pile strands survive the cut edge.
- The pattern itself must carry the arrow: sewing-pattern convention puts a nap/grain
  arrow on every paper piece, and DTD templates get arrows drawn on the tape (§1.4).

So a fur plan's direction map is not decoration — it is the per-piece arrow set, and it
must be *right on the animal*, because the maker transfers it verbatim.

### 1.2 The direction rule on a head

Our own library states it plainly — the OpenFur canine base (PrusaPrinters) instructs:
*"do not forget to add arrows for the fur's direction, flowing from the nose down to the
body and up the ears. If in doubt: use reference images of actual canines."* Generalised
across mammal heads:

- Fur lies **away from the face mask** (nose/eyes), sweeping **back over the skull** and
  **down the cheeks, jaw and neck** — the direction water and a stroking hand travel.
- **Ears reverse**: fur runs **base → tip, up the ear**, on both surfaces.
- The **midline is a part line**: flow diverges from the muzzle/skull centreline; pattern
  pieces are mirrored halves, so the plan only needs one side's field verified.

Our build (§3) generates exactly this field: geodesic distance from face seed sets
(nose tip/muzzle front on the head, chin front on the jaw, ear bases on the ears), fur
direction = uphill of that distance, tangent-projected and smoothed. Measured piece-mean
naps on the example confirm the rule numerically (head pieces ≈ (∓0.27, −0.95, +0.18) —
back and slightly up over the dome; ears ≈ (·, ·, +0.95) — straight up).

### 1.3 Pile zoning is a shaving problem first, a sewing problem second

Digital fur changes length continuously. Physically, sewing different pile lengths
together puts a bulky, visible step at the seam — so makers mostly **don't**. Standard
practice (e.g. Atomic Fursuits' DTD workflow: templates are "transferred to fur and
**pre-shaved**"):

1. Cut the colour piece from **one fur** whose pile is the zone *maximum*.
2. **Shave zones down** with clippers — bulk removed with vacuum clippers, boundaries
   refined with finishing clippers and different guard lengths. Shave *before* sewing
   wherever the piece allows.
3. Zone boundaries that are **not** seams are **blend-shaved gradients**, not steps.

Consequences for the format:

- The pile map is a **shave map**: each zone states a *finished* length, and its edges
  are gradient instructions (the example renders vertex-colour blends at zone edges on
  purpose — that gradient *is* the instruction).
- Where a pile boundary **coincides with a colour seam**, a second fabric is free (the
  seam exists anyway) — the plan flags these as `seam_coincident` candidates for a
  future revision; v1 keeps one fabric per piece + shave map.
- Commercial piles are nominal (~25 / 50 / 75 mm shags); the short zones (6 / 13 mm) are
  **shave targets, not SKUs**. The plan's pile table therefore records target mm, and
  the piece list records the *starting* fabric pile as the piece's max zone.

### 1.4 Colour zones are the pieces; seams live on colour boundaries

A pattern piece = one fabric = one colour region (connected). No-fur zones are
*materials*, not pieces of fur: nose leather (vinyl/silicone/latex), inner-ear
minky/felt, eye/claw parts. Markings *within* a colour that aren't worth a separate
fabric fall back to MARKINGS §7: airbrush through the stencil PNGs — which this plan
also ships (§2), now generated per fur piece as well as per marking layer.

### 1.5 From a 3D model to paper: DTD and its digital equivalents

The maker's canonical route from a shaped base to a sewing pattern is the **duct-tape
dummy (DTD)**: cover the base (over cling film on foam) with duct tape, draw seam lines,
markings **and nap arrows** on the tape, cut along the lines, flatten the tape pieces
onto paper, add margins. Symmetric base ⇒ pattern one half, mirror it. Studios like
Atomic Fursuits run DTD on *every* part, including over 3D-printed bases designed in
Blender — the digital model does not remove the tape step, it makes the base under it
exact.

Digital equivalents, in order of fidelity:

1. **The base's UV space** — a UV island *is* a flattened pattern piece with known
   distortion. Our head panel uses the v3 head's UV directly. Valid when UVs are
   production-grade; distortion becomes seam stress, so high-stretch islands get darts.
2. **Paper-model unfolding** (Blender's Export Paper Model, Pepakura-style): flattens
   a mesh along chosen seams into print-tiled pieces. The right route for parts with
   **no production UV** — on head v3, the jaw and ears (this plan's panels for them are
   labelled *drafting previews*, not cut patterns).
3. **DTD on a printed base** — still the ground truth; the plan's job is to make the
   tape step *transcription*, not design: seams, zones and arrows are already decided.

Print scaling: the plan declares a scale (`L = 300 mm` here); pattern PNGs print at
100 % = plan scale, tiled by the print tool. A 100 mm calibration square belongs on
every pattern sheet (v1.1 fix — the example sheet predates the rule; see §5).

---

## 2. The fur plan format (`anthroforge.furplan v1`, draft)

One folder per character part (head/body/part), emitted by the print/fursuit export
profile next to the colour bake and MARKINGS stencils:

| File | Content |
|---|---|
| `furplan.json` | The record: scale, pile table, fabric table, nap convention, **piece list** (below). Source of truth; PNGs are views of it. |
| `furplan_direction_{front,side,back,top}.png` | Neutral render + nap arrows per view. The maker's wall chart. |
| `furplan_pile_{front,side,back}.png` | Pile-zone (shave) map with mm legend. |
| `furplan_colour_{front,side,back}.png` | Colour-zone map with fabric legend. |
| `furplan_pieces.png` | Cut layout: pieces in UV/flatten space, labels + per-piece nap arrow, piece table. |
| `stencil_<piece-or-layer>.png` | Binary masks in the same flatten space (airbrush guides + piece isolation checks). Extends MARKINGS §7. |

**Piece record** (in `furplan.json`): `id`, `name`, `part`, `fabric` (colour/fabric
table ref), `pile_mm` (dominant zone) + `pile_range_mm` (the shave gradient the piece
contains), `area_cm2` at plan scale (fabric estimating: total example head ≈ 1,789 cm²
of fur), `nap_mean_xyz` (the piece's arrow, in part space), `verts` (provenance).
Example totals: 9 pieces, ≈ 1,789 cm² of fur at L = 300 mm.

**Conventions**

- **Nap arrow = direction the pile LIES** (root → tip fall), in the same sense as the
  arrows makers draw on fabric backing.
- **Pile codes**: 0 NO-FUR (material) · 1 MICRO 6 mm · 2 SHORT 13 mm · 3 MEDIUM 25 mm ·
  4 LONG 50 mm. Codes are *finished lengths at plan scale*, shave targets per §1.3.
- **Regions** use the MARKINGS §3 fur-region vocabulary (`muzzle`, `cheeks`, `ruff`,
  `ears.inner`, `ears.back`, …) — a zone means the same patch of animal in the groom,
  the markings stack, and the fur plan.
- **Seam allowance**: plan default **10 mm** added around every piece at cut time
  (fur seams need more than dressmaking's 6 mm; some makers draft to 12 mm cutting
  margin beyond the sewing line).
- Mirrored pieces are listed once per side (pattern once, cut 2× mirrored) — asymmetry
  in a character's markings produces genuinely different L/R pieces, same rule as
  MARKINGS §3 `mirror`.

---

## 3. The worked example — neutral base head v3

**Method.** Geometry extracted in world frame from `neutral_base_head_v3.blend`
(TissueHead 962 v, Jaw 538 v, ears 76 v each, NoseLeather). Anatomical groups from the
v3 build's own group map (Muzzle/Cranium/Cheek/Brow/EyeSocket/EarBase/EarTip/Chin).
Direction field per §1.2 (geodesic-uphill, bias-blended, smoothed). Zone rules are
thresholds on those groups + world coordinates (palate line from the v3 measurement
set: eye centre z − OrbitHeight 0.172 L). Pieces = connected colour components ≥ 6
verts, head-main split at the midline into mirrored halves. Scripts in `work/`.

**Pile rules (summary)** — muzzle tip/bridge core MICRO; muzzle, brow, eye surrounds,
jaw front SHORT; cranium/cheek fronts MEDIUM; cheek ruff (lower + posterior cheek),
occiput, jaw underside LONG; inner ear MICRO; ear outer MEDIUM; nose NO-FUR.
Resulting distribution (head): 91 / 374 / 399 / 98 verts across MICRO/SHORT/MED/LONG.

**Colour rules (example scheme — agouti wolf-type)** — MAIN over cranium/cheeks and
muzzle sides; PALE kept low and front: chin/mouth zone + nose-front (cougar-style —
a flat z-cut paints the whole deep muzzle block, which reads as a bib, not a muzzle)
plus a small jaw-line blush, and the whole jaw (cream jaw/throat); DARK ear backs;
INNER minky inner ears; nose leather bare.

**Pieces (9)**: head-main L/R (483 cm² each, pile range 6–50 mm — the shave gradient
is the work), head-pale muzzle front (64 cm²), jaw-pale (580 cm²), ear-dark L/R,
ear-inner L/R, nose-leather (14 cm², material). Total fur ≈ 1,789 cm² ≈ 0.18 m² —
one ¼-hide-equivalent of each main fabric covers a head with cutting waste; PALE is
the yardage driver because the jaw is one big piece.

**QA** — nap means match the §1.2 rule (above); mirrored pieces' naps mirror (x flips,
y/z equal) exactly; zone maps are seam-clean (majority-smoothed, no single-vertex
islands above the 6-vert piece floor; sub-floor speckles are documented blend edges).

---

## 4. Maker notes the plan assumes

- Shave order: bulk-pass the LONG→MEDIUM transitions first, sew, then refine blends on
  the head (clipper-over-comb) — plan gradients are drawn wide enough for comb work.
- Knit faux-fur backing stretches across the nap more than along it; pieces whose
  `nap_mean` runs across a high-curvature zone (cheek ruff) get a dart note in v1.1.
- Markings that live *inside* a long-pile colour zone need higher-contrast stencils
  (long fur mutes pattern — MARKINGS §9); stencil PNGs here are full-contrast already.

## 5. Honest limits / next fixes

- **No calibration square on the pieces sheet yet** (v1.1) — print scaling relies on
  the declared scale + printer dialog. Add the 100 mm square before anyone cuts from it.
- **Ears/jaw panels are drafting previews** (PCA/profile projections, front+back faces
  overlap in projection) — production patterns for UV-less parts go through §1.5 route 2.
- Head only. A body fur plan needs the body base + the head/body **cowl overlap** (DTD
  practice tapes over the shoulders for exactly this) — the format's `part` field is
  ready; the body example is not built.
- Pile/fabric tables name *classes*, not vendor SKUs; a SKU mapping is a sourcing
  pass, deliberately out of scope here.
- Zone thresholds are tuned to this head's measured anchors; a species preset (long
  ruff on a lion, ear tufts on a lynx) should re-drive them from the species record,
  the same way markings presets re-drive masks.
