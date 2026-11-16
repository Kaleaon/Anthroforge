# Neutral Base Head v2 — Build Notes

*Completed + QA'd Nov 12, 2026 (finish/QA pass after the original build agent
errored out mid-run; exports produced by re-running the final script with
`--final`, see "Reproduction" below). Verdict up front, because Joe will judge
the renders himself: **v2 is a real engineering step past v1 and its headline
widths measure near spec, but visually it still reads as a smooth cartoon
animal — longer-muzzled and flatter than v1, with paddle ears — not the
realistic-anchored professional base the brief asked for.** Details and
measurements below; nothing in this file oversells it.*

## Deliverables

| File | Contents |
|---|---|
| `neutral_base_head_v2.blend` | Full scene: tissue deliverable set + Skull / SkullMandible / Muscles reference layers + camera. 25 objects. |
| `neutral_base_head_v2.glb` | Export of the deliverable set only: 21 nodes / 21 meshes / 8 materials, 21,260 verts (post-export split). No skin, no animations. |
| `neutral_base_head_v2.groups.json` | Slider vertex groups sidecar (glTF can't carry them): 20 groups across TissueHead (12), Ear_L/R (3 each), Jaw (2). |
| `proportions.json` | Script-measured ratios vs the species spec's neutral column (see table below). |
| `render_front/side/threequarter.png` | Tissue set, studio HDRI, Cycles 40 samples. Three-quarter poses the jaw open −21° about the hinge. |
| `render_layers.png` | Skull + muscle layers (tissue hidden). |
| `build_base_head_v2.py` | The whole build, rerunnable headless. |

GLB node set (actual): `TissueHead, Jaw, Ear_L, Ear_R, Eyeball_L/R, Iris_L/R,
Pupil_L/R, Eyelid_L/R, LidMargin_L/R, NoseLeather, TeethUpper, TeethLower,
Tongue, Throat, NeckSocket, NeckSocketDisc`. (There is no node literally named
"Head" or "MouthInterior" — `TissueHead` is the head, `Throat` + mouth-dark
material serve as the interior.)

## Method — as actually built (read this before repeating the brief)

The v2 brief described "neutralise the rigged cougar (GalileoGB) toward
neutral, then layer." **The delivered script does not do that.** No cougar
geometry was imported, retopologised, or deformed. What was actually built is
a second-generation **procedural loft with layered derivative construction**:

- A tissue surface lofted from an 18-station superellipse table (60 × 80
  stations/rings → 4,802 verts), the station widths set from the spec's
  neutral ratios. Puma influence is parametric only (e.g. the zygomatic-arch
  peak placement, noted in a code comment as "~t=0.48 (puma)").
- A **skull layer** derived from the same table by subtracting documented
  per-region soft-tissue thickness (hw −0.016 muzzle / −0.011 cranium,
  top −0.009, bottom +0.010, arch × 0.82), plus separate zygomatic-arch
  tubes, a nasal bone plate, a supraorbital shelf + glabella, and a bone
  mandible (the jaw loft at 0.94 width, +0.012 z).
- A **muscle layer** of named primitives: temporalis, masseter, buccinator,
  zygomaticus straps, orbicularis oculi/oris tori, frontalis sheet, and a
  corrugator slip modelled at its brow-study dimensions (29.2 × 12.6 ×
  1.62 mm — expression, not mass).
- **Tissue displacement passes** over the loft: eye-socket bowls (−0.020),
  orbital rims, brow pad (+0.006), temporalis pads (+0.011), broad cheek fat
  pads (+0.011), and a mouth-crease pinch.

So the layer stack genuinely exists as objects in the .blend and the tissue
surface is numerically skull + offsets — Joe's construction rule is honoured
in structure. But every layer is still formula geometry (lofts, ellipsoids,
gaussian bumps), not modelled anatomy, and the layers render shows the
muscle primitives intersecting and poking through the skull rather than
sitting fitted inside an envelope. The stack is a scaffold, not a sculpt.

**Brow:** built to the brow-study animal values — canids/felids have no
supraorbital torus (species BrowProjection −20…−45 vs modern human 0,
Neanderthal +56…+100), so the bone brow here is only a modest shelf ledging
a few mm proud of the frontal, and the visible brow read is shelf-shadow +
a +0.006 tissue pad. Correct per the study; the torus range belongs to
humanoid bases, not this neutral.

## Anatomy parts (new vs v1)

- **Eyes:** eyeballs (r = 0.050) seated *inside* socket bowls, with separate
  iris + pupil caps on the orbit axis and a lid shell (sphere with the front
  52° cap removed) + lid-margin torus per eye. In the final renders the
  brown iris reads properly at front and 3/4 — this is v2's clearest win
  over v1's proud bead.
- **Jaw:** true U-trough loft (outer wall, rim step, inner walls, floor) —
  not v1's solid bar — with a masseter bulge at the angle. Origin is the
  world origin; posing is done by matrix about the hinge point
  (0, −0.245, −0.026) at render time. Teeth (upper/lower canines, cheek
  rows, incisors), tongue slab, and a dark throat ellipsoid ride with it.
- **Nose leather:** separate ellipsoid with philtrum groove + nostril-wing
  swells, glossy dark material.
- **Ears:** lens-cross-section lofts (inner-ear dish carved on the front
  face), merged as separate objects interpenetrating the skull (not welded —
  same known v1 limitation).
- **Neck:** socket torus + dark termination disc at the occiput.

## Proportions vs the species spec's neutral column

Measured by the script on the final mesh (ratios to L; L itself measures
1.036 vs the 1.000 frame, +3.6%):

| Measure | Measured | Spec neutral | Dev |
|---|---|---|---|
| Cheek width (ZB/L) | 0.559 | 0.58 | −3.6% |
| Cranium width | 0.410 | 0.36 | **+13.9%** |
| Muzzle width (rostrum) | 0.163 | 0.17 | −4.0% |
| Muzzle depth | 0.176 | 0.20 | **−12.2%** |
| Skull height (head+jaw) | 0.283 | 0.31 | −8.8% |
| Jaw length | 0.723 | 0.74 | −2.3% |
| Jaw width | 0.371 | 0.40 | −7.3% |
| Jaw depth (ramus) | 0.249 | 0.28 | **−11.2%** |
| Ear height | 0.393 | 0.40 | −1.8% |
| Ear width/length | 0.573 | 0.55 | +4.3% |
| Orbit opening (est.) | 0.189 | 0.15 (orbit Ø) | **+26.1%** |
| Eye centre spacing | 0.205 | 0.34 * | −39.8% * |
| Nose width / muzzle width | 0.497 | 0.55 | −9.7% |

\* The 0.34 "target" is the builder's own centre-spacing figure, not a spec
anchor — the spec's EyeSpacing anchor is *interorbital width* 0.19 L
(slider 23). On that basis: centre spacing 0.205 − eyeball Ø 0.097 ⇒
interorbital ≈ 0.108, still ~43% under the spec anchor. Either way the
eyes sit too close together; the socket opening is meanwhile ~26%
oversized for the eyeball inside it. Both are visible in the renders
(eyes read small and close-set on a wide head).

Pattern in the misses: the head is **too wide and too low** — cranium
+13.9% wide while skull height −8.8%, muzzle depth −12.2% and ramus depth
−11.2% are all short. The widths the loft table controls directly are
fine; the vertical/depth dimensions, which emerge from the superellipse
top/bottom channels, all sag. That is exactly the flat, long read in the
renders.

## Visual QA (finish agent's own read of all four renders + v1 previews)

What improved over v1: studio HDRI + subsurface clay kills v1's flat grey
look; the eyes are seated anatomy now (socket, lid shell, iris that reads)
instead of a bead on a bump; there are teeth, a tongue, a throat, a real
jaw trough, a defined nose, and a neck termination. The 3/4 open-jaw shot
is the best of the set.

What did not improve enough: **the silhouette and surfaces still read
cartoon.** The muzzle is a long smooth tube — with the low cranium the
profile leans anteater/aardvark more than neutral mammal, arguably a
stronger species lean than v1's fox. The front view is dominated by the
zygomatic-arch gaussian, which spikes the cheeks into a wide flat diamond
(manta-like), and by the ears: at spec length but broad and thin, they sit
on the skull as two pale paddles with a visible base seam and read
rabbit/fennec, not neutral. Surfaces are balloon-smooth throughout — the
"flat" dorsal-flattening parameter never produces actual anatomical
planes, and the stop is a gentle sag, not a break. The nose leather reads
as a plush-toy blob from the front, the upper canines hang outside the
closed mouth line like fancy-dress fangs, and the open jaw reads as a
long scoop. The layers render proves the stack exists but also exposes
it: muscle ellipsoids bulge through the bone instead of living inside it.

**Verdict: better instrumented, better lit, better accessorised — same
underlying failure as v1.** A loft + bumps cannot produce the planes of a
real head; it can only be tuned. If this base is used, use it as a
deformation/engineering base (groups, jaw, proportions scaffold), not as
evidence the form problem is solved. A v3 needs a sculpted or
scan-derived surface (e.g. actually neutralising the cougar/lion geometry
this time) with the v2 layer stack and parts transplanted onto it.

## Remaining gaps

1. **Form** (above): no anatomical planes; muzzle too long/flat; cranium
   too wide/low; eyes close-set in oversized sockets; ear bases seamed,
   ears oversized in read despite on-spec length.
2. **Muscle layer is schematic** — primitives intersecting the skull, not
   fitted masses; temporalis/masseter volumes don't drive the tissue
   surface (tissue pads are independent gaussians).
3. **No symmetry verification** — v2's proportions script never measures
   X-asymmetry (v1 reported 0.000). Group counts are near-mirror
   (BrowL 820 / BrowR 819, EyeSocketL 892 / R 898) but vertex-exact
   symmetry is unproven.
4. **Ear group naming** — the sidecar's ear groups are `Ear_L / EarBase_L
   / EarTip_L` (underscores) while the other 14 groups keep v1's
   `CheekL` style. Harmless, but an importer should read names from the
   sidecar, not assume v1 spelling.
5. **No rig** — GLB/blend carry no skeleton; jaw posing is by matrix in
   the render function only. Teeth/tongue are separate objects, not
   parented to the jaw object.
6. **Eyelids** are shells without concentric loop topology; they'll
   deform poorly under blink morphs. Teeth are cones/boxes, tongue is a
   rounded slab — placeholders, as specced for v2, but placeholders.
7. The jaw hinge is a render-time constant in the script, not stored as
   an empty/pivot object in the .blend.

## Reproduction

```
~/workspace/tools/blender/current/blender -b --python build_base_head_v2.py -- --final
```
(Full run ≈ 20 min, most of it the four Cycles renders. Without `--final`
it builds and renders but skips the GLB export and .blend save. The
exports in this folder were produced by exactly this command on
Blender 5.2.3 LTS after the original build agent died post-render;
groups/proportions/renders were regenerated by the same run, superseding
the mid-edit copies the dead agent left — one visible difference: eye
centres moved 0.118 → 0.106 in the final script revision.)

## Sources & licences

- **Geometry: 100% procedural** (this script). No third-party mesh data
  is incorporated, so no attribution obligations attach to the asset.
- Proportion targets: `species-head-spec.md` neutral column (internal
  doc; its values trace to the published skull literature cited there).
- Brow treatment: `brow-study.md` (internal; Smith & Ranyard / Ahern,
  Lee & Hawks 2002 chords as tabulated there).
- Puma CT skull (Puma concolor MSB:Mamm:214485, Biodiversity / Sketchfab,
  CC BY) was supplied as the skull-layer reference for this build; per
  the as-built method above it informed parameters only — no scan
  geometry is in the file.
- Render lighting only (not in the asset): Poly Haven
  `photo_studio_01` HDRI, CC0.
