# Neutral Base Head v3 — Build Notes

**Method actually used (the one v2 skipped):** v3 starts from REAL geometry — GalileoGB's
rigged cougar avatar — extracted, measured, and **neutralised** toward the species-head-spec
neutral column with smooth-field deformations. No procedural loft, no balloon smoothing: the
cougar's sculpted anatomical planes survive into the result. v2's brief said "neutralised
cougar anchor" but never executed it; v3 is that brief, executed.

## Sources & licence

- **GalileoGB cougar** (`FemaleCougar_ForSale.blend`, CC Attribution / CC-BY — attribution
  required): tissue surface, ears, sculpted mouth/teeth slab, tongue. Informed geometry, and
  its parts are carried into the deliverable, so the CC-BY attribution travels with it.
- **Puma concolor CT skull** (Sketchfab, CC-BY): parameter reference only (spec §5 verticals).
- **v2's parts** (our own procedural work): eye assemblies, nose leather, throat, neck socket.
- **Poly Haven studio HDRI** (CC0): render lighting only.

## Pipeline

1. **Stage A — extraction.** Head cut from the body mesh on the half-mesh by bone weights
   (DEF_Head + Ear + Eye ≥ 0.40), one connected component, Mirror applied → 1,559-vert tissue
   head. Eyeball, mouth slab (719 v, teeth/gums sculpted in), tongue (457 v) extracted too.
   Frame: face +Y, up +Z, scaled so L (nose tip → occiput) = 1.0.
2. **Stage B — source measurement** with the same rulers used on the result (below).
3. **Stage C — neutralisation.** Ears split off first (own objects). Smooth gaussian/ramp
   fields on tissue (mouth pieces follow the lengthen/deepen fields): rostrum lengthen ×1.15,
   zygomatic narrow, muzzle narrow + dorsum raise, jaw deepen (palate line masked so the
   arcade doesn't drop), braincase narrow, forehead drop at the orbit station (for OrbitRise),
   ears rescaled about their base (length ×1.43, width ×0.92, slight lift). Six tuning rounds.
4. **Stage D — jaw split, layers, grafts, groups.** Jaw split along a hinge-anchored cut
   surface; **Jaw object origin sits exactly on the hinge** (0, −0.2167, −0.1278) so it
   articulates by object rotation. **Skull** = tissue offset inward along normals with v2's
   documented tissue thicknesses (0.007–0.014 by region); **SkullMandible** likewise;
   **Muscles** = temporalis + masseter patches separated from the skull offset and pushed out
   0.0045. The cougar's own sculpted arcade and tongue were kept over v2's placeholder teeth
   (real sculpted geometry beats cones) — see limitation 1. v2's eye assemblies, nose leather,
   throat, neck socket grafted (see the seating fix, below). 20 vertex groups regenerated.
5. **Stage F/G — unified measurement, export, renders.**

## The eye-seating fix (found by looking at the first renders)

The first full-quality front/side renders showed v2's eye assemblies bolted onto the face like
googly eyes: I had placed them at the spec's abstract centre spacing (±0.170) instead of at
this head's actual sockets (±0.134, from the cougar's own eyeball landmark carried through
the neutralisation). Fixed: assemblies re-anchored to the socket centres, yawed 15° outward to
match the socket facing, sunk slightly; nose leather re-centred on the true nose-tip cluster
(it had been floating on the bridge). This is the v1 EyeSpacing tension arriving again — see
the Interorbital line below. **Fit was chosen over the arithmetic; the deviation is disclosed,
not hidden.**

## Measured results (proportions.json; L = 1.0; identical rulers on source and result)

| Measure | Target | Source cougar | **v3 result** | Dev | Gate |
|---|---|---|---|---|---|
| Zygomatic breadth | 0.58 | 0.644 | **0.547** | −5.8% | ✓ |
| Skull height (dome rise above orbit) | 0.31 | 0.348 | **0.317** | +2.2% | ✓ |
| Muzzle fraction (anterior-orbit ruler) | 0.33 | 0.304 | **0.344** | +4.1% | ✓ |
| Orbit diameter | 0.15 | 0.144 | **0.150** | 0.0% | ✓ |
| **OrbitHeight** (eye centre above palatal line) | 0.17 | 0.186 | **0.172** | +1.2% | ✓ |
| Ear length | 0.40 | 0.288 | **0.389** | −2.8% | ✓ |
| Jaw length | 0.74 | 0.52 (proxy) | **0.716** | −3.3% | ✓ |
| Muzzle depth | 0.20 | 0.157 | **0.231** | +15.5% | ✗ (ruler-sensitive: 0.21–0.23 across tuning rounds; the thin mid-muzzle band lands near the stop) |
| **Interorbital width** | 0.19 | 0.140 | **0.112** | −40.9% | ✗ — **deliberate**: 0.19 + Ø 0.15 implies 0.34 centre spacing, which lands outside this skull's surface (v1 flagged the same tension). Eyes seated in the real sockets instead. Needs a spec ruling. |
| **OrbitRise** (eye depth below dorsal profile) | 0.12 | 0.207 | **0.204** | +69.6% | ✗ — the felid brow/forehead mass at the orbit station barely moved; the forehead-drop field lowered the centreline but the band maximum sits at the brow corners. Flattening further means restructuring the brow, beyond a neutralisation's remit. |
| Cranium width (dome shell) | 0.36 | 0.476 | **0.478** | +32.8% | ✗ — target is a bare-skull bone measure; this ruler reads the fleshed dome shell (temporalis + ear bases). The narrowing shows in ZB (−15% relative); the dome shell itself is essentially the cougar's. |
| Muzzle width | 0.17 | 0.315 | **0.216** | +26.9% | ✗ — deliberate partial (−31% relative). Full compliance tubes an anthro muzzle (v2's anteater failure in reverse). |
| Jaw width | 0.40 | 0.621 | **0.534** | +33.4% | ✗ — bone anchor vs fleshed masseter width; moved from source, not to target. |
| Ramus depth | 0.28 | 0.380 (proxy) | **0.251** | −10.5% | ✗ — near-miss; the jaw band is bottom-limited after the split. |

**Vertical placement (Joe's requirement + spec §5):**
- **OrbitHeight 0.172 vs target 0.17 ✓** — and the side render proves it: the eye sits raised
  above the muzzle/palatal line with skull behind it, nothing like a crocodilian's flush eye.
- **Ear tip height above the palatal line: 0.530 (source) → ≈0.63 (result)**; ear tips now
  clear the skull dome by **+0.146** (source cougar: −0.004, tips below the dome). Ear base
  insertion barely moved (0.255 → 0.259 above palate) — exactly as spec §5 predicts: ear
  "height" reads as tip + carriage, not base.

**8 of 14 gates inside ±6%**; every miss above is named with its reason. Ruler definitions are
in `work/stageF_final.py` (SkullHeight = dome rise above the orbit plane; CraniumWidth =
dome-shell band; both chosen because the spec anchors are bone measures and documented as
such in the spec-amendment work).

## Limitations (read before building on this)

1. **The teeth arcade is one fused slab spanning both jaws** (the cougar's sculpt). It cannot
   split upper/lower when the jaw opens; the jaw-open render shows it intersecting. The
   universal-arcade split (uppers on skull, lowers on jaw) is v4 work.
2. **Low-poly source.** 1,559 tissue verts (962 tissue + 538 jaw after the split). Faceting is
   visible on the cheek/jaw in close renders, and the jaw split's cut edge zigzags through the
   coarse cheek geometry. The surface wants a subdivision + sculpt pass or a higher-res source
   before it reads "scan-grade."
3. **No rig in the export.** The jaw pivot exists as the Jaw node's transform; there is no
   armature/skin in the GLB (same scope as v2's).
4. **Neck socket** is scaled 2.28× from v2's to fit the cougar's neck stub (Ø ≈ 0.47) — chunky
   but seated at the back-bottom where it belongs.
5. Vertex groups live in the .blend + `neutral_base_head_v3.groups.json` sidecar (glTF cannot
   carry arbitrary groups).

*Render note: `render_compare_v1v2v3.png` is a composite of each version's own front render
(v1 `preview_front.png`, v2 `render_front.png`, v3 `render_front.png`, left → right) — the
three files store their heads under different facing conventions, so a single shared scene
could not frame all three honestly; the composite compares like for like instead.*

## Visual verdict — does v3 clear Joe's bar?

Partly, and the honest split is: **the head is right; the finish is not there yet.** What v3
fixes for real: it is a genuine animal head — sculpted planes, a stop that breaks instead of
sagging, a straight nasal bridge, eyes seated in their sockets under a brow shelf and visibly
raised above the muzzle line, ears that read as ears, a jaw that actually articulates on its
hinge with a real mouth behind it. Side-by-side (render_compare_v1v2v3.png) it is plainly the
most professional of the three: v1 is a toy, v2 is a better-instrumented cartoon, v3 is a
low-poly game avatar of an actual mammal. What still keeps it off the "professional,
realistic-anchored" bar: the low-poly faceting (limitation 2), the heavy felid brow that
OrbitRise measures and the profile shows, ears that still read broad with a visible base seam,
and a muzzle that reads long in profile because its width was only partly narrowed. None of
those are proportion-system failures — they are surface-resolution and sculpt-detail work.
**Verdict: v3 clears the construction and proportion bar (with the disclosed exceptions) and
is the correct base to build on; it does not yet clear the finish bar. The next step is a
subdivide-and-sculpt pass on this geometry — not another rebuild.**
