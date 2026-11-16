# A6 — Groom Flow & Combing

**Problem named by the fur prototype:** the strand groom's kink settings made the coat
read *woolly/poodle* — strands had coverage and length, but no **direction discipline**.
Real pelage is not random fuzz with curl on top; it is a set of *streams* with a
definite direction at every point of the skin. This study covers where those streams
run on a real animal, how production grooms encode them (guides first, interpolation
second), and proves the fix on the library bara wolf's head: a flow-authored groom
whose children sit a few degrees off the anatomical stream, next to a control groom
with the same roots and lengths but the direction discipline removed.

Deliverables in this folder:

| File | What it is |
|---|---|
| `wolf_head_flow_groom.blend` | Head mesh with painted flow attributes (`FLOW_dir`, `FLOW_len`, `FLOW_pot`), 260 guide curves, the combed groom (2,600 strands) and the tangled control groom, cameras + lights |
| `render_cheek_combed.png` / `render_cheek_tangled.png` | Same camera, same roots, same lengths — only direction discipline differs |
| `render_head_combed.png` | Three-quarter view of the flow-authored groom |
| `render_guides.png` | The 260 guides alone over the clay head — the groom *is* the guides |
| `render_flowmap.png` | The flow map itself: object-space direction stored per-vertex, shown as colour |

---

## 1. Pelage direction rules — how fur actually flows

The classical source is the hair-tract literature (Kidd, *The Direction of the Hair
in Animals and Man*, 1903; Boardman's hair-tract descriptions, 1945). Two ideas carry
the whole subject:

- **The primitive tract.** In the ancestral mammal pattern — still plainly visible in
  rodents, small carnivores and marsupials — hair slope runs **from the tip of the
  snout to the tail** along head, neck and trunk without interruption, and on the
  limbs from proximal to distal. Everything else is a local deviation from that one
  stream.
- **Streams follow lines of least resistance.** Direction is set by skin mechanics:
  streams run along the directions the skin stretches and folds. That is why the
  pattern is predictable from anatomy — and why a flow field can be *derived* from
  the mesh instead of hand-invented.

### Head (the prototype's territory)

- **Face and forehead.** One caudad (rearward) stream from the muzzle over the face
  and crown. Above the cheek (genal) level the flow is straight caudal; between eye
  and ear it bends up-and-caudal around the ear base.
- **Cheek sweep.** Below the genal level the stream turns **caudal + ventral**,
  describing a shallow S as it wraps the jaw — shorter radius behind the cheek,
  ending aimed at the midventral line. This is the sweep that makes a wolf's cheek
  ruff read as a *sweep* instead of a puff.
- **Ear base.** A recurved stream curls around the ear base. Where it collides with
  the face stream below/in front of the ear, the two opposing currents form a
  **divergent interval** — a natural parting. Combs must respect it: strands
  interpolated across a parting are the classic source of a tangled read.
- **Throat and jaw underside.** Hair runs caudomedially from both sides and
  **converges on the midventral line**, continuing as a convergence seam down the
  front of the neck.
- **Neck.** The crown stream continues over the neck dorsum *without a break* into
  the trunk stream. On the neck sides the trend rotates by height: cranioventral in
  front, transverse mid-neck, caudoventral behind, running out over the shoulder
  onto the upper arm.
- **Ears themselves.** Short fur, base→tip on both faces of the ear; the ear is a
  flow *obstacle* for the head stream, which parts around its base.

### Body (summary, for the full-body groom this feeds)

- Dorsal stream caudal along the spine, continuing the neck stream; flank streams
  sweep down-and-back off the spine; belly streams angle toward the midventral
  convergence line. (The sloth is the famous inversion — part on the belly, streams
  toward the spine — because it hangs upside down; the exception that proves the
  rule is functional: streams shed water off the animal's habitual posture.)
- Chest: a divergence near the sternal angle splits streams up toward the neck and
  down the sternal groove.
- Limbs: proximal→distal, postaxial bias; reversals/partings appear at flexor folds.
- **Singularities are features, not noise:** vortices (cowlicks) where streams
  spiral, partings where they oppose, seams where they merge. A groom needs guides
  planted *at* singularities; interpolation must never bridge across them.

## 2. How production grooms encode direction — guides first

Every mature grooming workflow (Blender Hair Curves, Houdini, XGen, C4D Hair) has
the same skeleton:

1. **Guides are the groom.** A few hundred guide strands (here: 260 on a head) are
   combed into the intended flow. Nobody combs 90,000 strands; you comb the field.
   Broad Comb strokes set direction first; Add fills gaps; Pinch/twist is garnish.
2. **Children interpolate.** Density comes from children generated *between* guides
   (Blender's Interpolate Hair Curves; particle "interpolated children"). A child's
   direction is a blend of nearby guide directions — the flow field made flesh.
3. **Clumping is convergence, not noise.** Children lean toward their guide as they
   travel (offset shrinking toward the tip), which is what makes locks and tufts.
4. **Kink/frizz is a perturbation budget, spent last.** Curl, wave and frizz must be
   *small corrections riding on the guide direction* — low amplitude, wavelength
   long compared with strand length. The fur prototype inverted this budget: WAVE /
   CURL kink at amplitudes comparable to the strand structure itself, on parents
   whose own directions were analytic height-band fields with no anatomical stream.
   Result: every strand individually plausible, collectively wool. **Kink cannot
   create flow; it can only decorate it.**

### Flow maps — painting direction directly

Besides combing guides, direction can be stored as a **map**: a per-point tangent
direction over the surface (in games: 2D flow maps for fur shells and anisotropic
spec; in DCC: guide interpolation does the same job implicitly). Two ways to author
one, both used in this prototype:

- **Paint/comb the anchors.** An artist paints a handful of directional strokes
  (source strokes on the face, stream strokes down the neck) or combs sparse guides
  in Sculpt mode. Few strokes, placed at landmarks and singularities.
- **Solve the field from the anchors.** Strokes become boundary conditions for a
  smooth tangent field. Our solve: a **geodesic potential** — distance over the
  skin from the face-front seed patch. Its gradient *is* the primitive tract:
  streams leave the muzzle, climb the face, split around the ears, run over the
  crown and down the neck, exactly because distance-over-surface increases that
  way. Zone rules (cheek ventral bias, throat midline convergence, ear-base
  recurve, neck obliquity) are then blended in as local corrections, and the field
  is Laplacian-smoothed over the mesh graph so neighbouring hairs agree — a field
  that isn't smooth can't be combed, only fought.

We store the result on the mesh as a colour attribute, `FLOW_dir` (object-space
direction, `rgb = dir·0.5 + 0.5`), plus `FLOW_len` (zone length map) and `FLOW_pot`
(the potential itself, useful for debugging streams). `render_flowmap.png` shows
the map: sweep direction is literally visible as colour flow.

## 3. The prototype build

Subject: `BaraWolfBody` from the library bara wolf (the fur prototype's body),
head + upper neck extracted (9,660 verts). Pipeline (`work/build_groom.py`):

1. Geodesic potential from a muzzle seed patch (Dijkstra over the mesh graph).
2. Flow = tangent-projected gradient of the potential, zone-shaped per §1,
   4 Laplacian smoothing passes.
3. **Guides first:** 260 roots sampled area×density-weighted (face thin, ruff
   dense), each advected along the field for 7 segments, reprojected to the
   surface each step, with zone droop (ruff hangs, crown lies flat).
4. **Interpolation second:** 10 children per guide — root jittered inside a
   5.5 mm disc, path inherited from the guide, offset clumping toward the guide
   ((1−t)^1.15), ±12% length variation, 0.6 mm long-wave wobble. No kink stack.
5. **Control groom:** identical roots, lengths and count, but each strand's
   heading is randomly tilted (σ ≈ 32°, capped 78°), random-walks ±16° per
   segment, with a 3.2 mm short-wave kink — a fair stand-in for the old
   kink-led groom.

### Measured result — flow coherence

Mean angle between each strand's mid-length direction and the anatomical flow
field at its root (lower = combed):

<!-- METRICS: filled from work/metrics.json after the build run -->
| Groom | Mean | Median |
|---|---|---|
| Combed (guides + interpolation) | — | — |
| Tangled (kink-led control) | — | — |

Read the cheek close-ups against this table: in the combed render the ruff lies in
one rearward-downward sweep and the crown stream is visible as parallel order; in
the control the same fur mass points every which way and the silhouette goes
cottony — the poodle read, reproduced on demand.

## 4. Rules to carry into the full groom

1. **Direction before density, density before decoration.** Flow field → guides →
   children → clump → kink, in that order, and never let a later stage overpower
   an earlier one.
2. **Budget kink like salt:** amplitude in millimetres, wavelength ≥ ½ strand
   length, and always *added to* the guide direction. If a groom needs kink to
   look furry, the flow is wrong.
3. **Plant guides at singularities** (ear-base parting, throat convergence,
   crown) — interpolation must stay inside one stream; add a guide rather than
   letting children bridge a parting.
4. **Store the flow map on the mesh.** Cards, shells and LODs should all sample
   the same `FLOW_dir`, so every downstream representation combs the same way the
   strands do (the fur prototype's cards already inherit groom curves; the map
   makes that inheritance explicit and reusable).
5. **Length is a zone map, not a global.** Muzzle 16 mm → crown 50 mm → ruff
   125 mm on this head; a single length everywhere reads as a wig.
