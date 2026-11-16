# Neutral Base Head v1 — Build Notes

*Authored procedurally with headless Blender 5.2.3 (`build_base_head.py`, rerunnable —
every number below regenerates from that script). Built to the NEUTRAL column of
`../species-head-spec.md` §3.1: a generic mesaticephalic mammal parked between the
canid and felid averages, deliberately no species.*

## Construction

- **Frame:** L = 1.0 unit along Y (nose tip y=+0.50 → occiput y=−0.50), +Z up,
  +X = head's left. Scale to real skull size at export, per spec §3.0.
- **Skull + muzzle:** a superellipse cross-section **loft** (96 interpolated stations
  × 56-point rings, Catmull-style key profiles + channel smoothing). Ring loops run
  around muzzle/cranium, rails run nose→occiput — the deformation flow the spec asks
  for. Zygomatic flare is an angle-localised widening at the cheek stations; eye
  sockets, brow ridges, stop pinch and a mouth-line crease are analytic
  displacement passes with smooth falloffs.
- **Ears:** tapered tube lofts (20 rings × 18) merged into the Head mesh, bases
  embedded in the cranium, pinna faces canted ~30° outward. Clean base ring loop
  per ear; EarBase/EarTip groups carry the slider split.
- **Jaw:** separate object, its own loft (26 × 36). **Object origin sits exactly
  on the hinge axis (0, −0.28, −0.02)** — rotate it on X and the jaw opens
  (the three-quarter preview is rendered at −15° to prove it).
- **MouthInterior:** a simple open-front/open-bottom tunnel (dark clay material)
  parented to Head, fully embedded when the jaw is closed, so opening the jaw
  reveals interior walls instead of a hollow shell. No teeth/tongue yet — those
  are spec §3.4 discrete part sets, separate work.
- **Eyeballs:** separate sphere objects (icosa subdiv 2) seated in displaced
  sockets, per spec §3.1 (EyeSize slider scales/moves these).

## Counts

| Object | Verts | Notes |
|---|---|---|
| Head (skull 5,378 + ears 2×361) | **6,100** | single mesh, quad-dominant, 2 pole fans |
| Jaw | 938 | separate object, hinge origin |
| Eyeball_L / Eyeball_R | 162 ea | separate objects |
| MouthInterior | 8 | tunnel, 4 faces |
| **Scene total** | **~7,370** | Head mesh itself is inside the 4k–12k target band |

## Vertex groups (weighted, smooth falloffs — in the .blend)

Head: `Muzzle`, `MuzzleTip`, `NoseLeather`, `MuzzleBridge`, `Cranium`,
`CraniumDome`, `CheekL/R`, `BrowL/R`, `EyeSocketL/R`, `EarL/R`, `EarBaseL/R`,
`EarTipL/R`. Jaw: `Jaw` (all), `Chin`. L/R counts mirror exactly (e.g. Cheek
757/757, EarTip 199/199) — the mesh is X-symmetric by construction; measured
asymmetry |minX + maxX| = 0.000.

⚠️ **GLB caveat:** glTF has no standard channel for arbitrary vertex groups and
Blender's exporter does not embed them (verified by parsing the exported GLB —
no extras/group data). Groups therefore live in the **.blend** (source of truth)
plus **`neutral_base_head.groups.json`**, a sidecar of group → vertex-index
lists (blend index space) for AnthroForge or any other consumer to rebuild
them from. If the app pipeline needs groups inside the GLB itself, the route
is skin weights on a head armature, not vertex groups.

## Proportions — measured on the final mesh vs spec neutral anchors

Verification runs inside the build script (`proportions.json`); ratios to L.

| Anchor (spec §3.1) | Target | Measured | Δ |
|---|---|---|---|
| Total length L | 1.00 | **1.000** | exact |
| CheekWidth ZB/L | 0.58 | 0.568 | −2% |
| CraniumWidth (braincase) | 0.36 | 0.361 | ✓ |
| MuzzleWidth (rostrum @ canine) | 0.17 | 0.177 | +4% |
| CraniumHeight (skull height) | 0.31 | 0.315 | +2% |
| MuzzleLength (fraction) | 0.33 | 0.33 (stop station at y=+0.17 by construction) | ✓ |
| MuzzleDepth | 0.20 | 0.20 (profile) | ✓ |
| MuzzleTaper (nose/base) | 0.50 | ≈0.42–0.50 (nose W 0.096 / base W 0.23) | ✓ |
| NoseSize (nose W / muzzle W) | 0.55 | 0.096/0.17 = 0.56 | ✓ |
| JawLength (mandible/L) | 0.74 | 0.752 (incl. chin pole) | +2% |
| JawWidth | 0.40 | 0.385 | −4% |
| JawDepth (ramus height) | 0.28 | 0.25 z-span (profile keys carry 0.267; smoothing rounds the coronoid/angle peaks) | −11% |
| EarHeight (ear/L) | 0.40 | 0.395 external (0.419 incl. embedded base allowance) | ✓ |
| EarWidth (ear W / ear L) | 0.55 | 0.22/0.40 = 0.55 | ✓ |
| EyeSize (orbit Ø/L) | 0.15 | socket bowl ≈0.15 effective; eyeball Ø 0.104 | ✓ |
| **EyeSpacing** | interorbital 0.19 → centres ≈0.34 implied | **centres 0.236** | ⚠️ see below |

**EyeSpacing is the one real spec tension.** With braincase 0.36 and ZB 0.58,
orbit centres at the anchor-implied 0.34 spacing land *outside the skull
surface* at orbit height (surface half-width there ≈ 0.15) — the eyeballs
floated off the head like gumballs in the first iteration. Centres were placed
at ±0.118 (spacing 0.236), seated in displaced sockets, and the frontal breadth
between the orbits still measures in the spec's 0.24 family. Either the anchor
means something narrower than centre-spacing, or the orbit band needs to be
wider than the other anchors allow. Flagged for a spec ruling before v2; the
EyeSocket/Brow groups make repositioning a local edit, not a rebuild.

## Known weaknesses (v1 honesty)

1. **Ears are interpenetrating, not welded.** Ear base rings are buried in the
   cranium rather than topologically bridged. Fine at neutral and for moderate
   slider values; extreme EarSpread/Tilt deltas will show the seam working.
   v2: bridge/weld the base loop into the cranium grid.
2. **No concentric eye loops.** Sockets are displacements on the loft grid, so
   there are no dedicated eyelid rings. EyeSize/EyeForwardness sliders will
   deform acceptably; eyelid sculpting needs a v2 retopo pass around the orbit.
3. **Jaw is a solid loft bar**, not a U-shaped trough — no teeth row, no inner
   jaw surface. Reads correctly closed and open (with MouthInterior), but a
   wide-open jaw from below shows the bar's top face, not a mouth floor.
   v2: hollow the jaw and add the teeth/tongue interior set (spec §4 item 2).
4. **Ramus depth −11%** (above) and rostrum +4%: profile smoothing tax.
   v2: add peak-preserving smoothing or post-scale the jaw Y/Z locally.
5. **No neck socket.** The loft closes at the occiput and the underside is a
   full throat surface; mounting on a body means intersecting the neck (the
   usual base-mesh arrangement) or cutting a socket in v2.
6. **Clay only.** One neutral material (+ dark interior). No UV work beyond
   Blender's defaults, no nose-leather material zone — NoseLeather is a
   vertex group, ready for the §3.4 `nose_canid`/`nose_felid` part variants.
7. Previews are Cycles clay renders (48 samples) — shading faceting at the
   poles is a render artifact of the fan caps, not a surface defect.

## Files

- `neutral_base_head.blend` — source of truth (groups, hinge-placed jaw origin)
- `neutral_base_head.glb` — 5 nodes: Head, Jaw, Eyeball_L, Eyeball_R, MouthInterior
- `neutral_base_head.groups.json` — vertex-group sidecar (blend index space)
- `proportions.json` — the verification table above, machine-readable
- `preview_front.png` / `preview_side.png` / `preview_threequarter.png`
- `build_base_head.py` — full procedural build; tweak keys at the top, rerun
