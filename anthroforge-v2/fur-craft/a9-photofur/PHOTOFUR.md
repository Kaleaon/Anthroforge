# A9 — Photo-Sourced Fur Textures (PHOTOFUR)

*AnthroForge fur-craft wave, brief A9. Original agent died silently after the
pipeline run (Nov 12, 2026, ~22:47 CST); this doc was reconstructed by the
finisher (Nov 13) from the shipped scripts, JSON sidecars, and the textures
themselves, with independent re-measurement of every claim that could be
re-measured, plus the proof renders the original run never produced.*

## 0. Verdict up front

A9 built a real, working **photo → tileable fur swatch** pipeline and three
species tiles (wolf, bear, fox), each a 1024² diffuse + a per-pixel flow map
with an honest self-measurement sidecar. The flow maps verify as faithful.
The diffuse tiles carry genuine photographic strand detail and colour that
neither A11's synthesis nor A15's painting can fake.

The seamlessness goal, however, **was not met by the pipeline's own metric**:
wrap-seam steps measure 3.4–5.5× the mean interior step (wolf, bear) and
~21–23× (fox), against a design target of ~1.0. The proof renders (§5)
confirm it: these tiles work as **single patches at their nominal physical
scale**, not as indefinitely tiled ground cover. Fox is the weakest tile —
its crop contains the pelt's dark parting groove, which tiling repeats as a
striped grid.

## 1. What was on disk (as found)

| Path | Contents |
|---|---|
| `scripts/photofur_pipeline.py` | The full pipeline (numpy/scipy/PIL), header docstring = design |
| `scripts/render_proofs.py` | Blender proof renderer — written, never successfully run (§5) |
| `sources/*.jpg` | 3 source photos: wolf taxidermy (3200×2168), black bear (1944×1855), fox skins (3000×1968) |
| `sources/crops/*_raw.png` | The exact pre-processing crops (620²/560²/360², matching the pipeline's crop table) + `contact_raw.png`, the stage-1 inspection contact sheet |
| `textures/fur_<sp>_diffuse.png` | 1024×1024 RGB tile |
| `textures/fur_<sp>_flow.png` | 1024×1024 RGB flow map (RG = strand direction, B = coherence) |
| `textures/fur_<sp>.json` | Sidecar: crop, physical scale, angles, coherence, seam metrics |
| `proofs/` | **Empty** as found; two finisher renders added (§5) |

Source provenance: the pipeline header asserts "CC/PD, Wikimedia Commons."
The finisher did not re-verify licences (no downloads permitted); treat
provenance as asserted by the original agent, not audited.

## 2. Method, as shipped in the code

1. **Crop.** A square of visually uniform fur is cut from the photo
   (chosen by eye against the contact sheet) and Lanczos-resized to 1024².
2. **Direction.** A structure tensor on luminance gives the dominant strand
   angle (energy-weighted orientation histogram). The crop is rotated in a
   measure-and-correct loop (≤3 passes, ±1.5° tolerance) until strands run
   down-tile (+V, 90°).
3. **De-light.** Homomorphic flattening: per channel, divide by a σ=90
   Gaussian estimate of the illumination field, renormalise to the field
   mean; then a global 0.5–99.5 percentile re-stretch and a mild unsharp
   (0.35) for strand pop.
4. **Seam treatment.** The 384-px strip straddling each wrap seam is blended
   with its own half-shift under a sin² weight, per axis — value-continuous
   at the wrap by construction.
5. **Flow.** Per-pixel structure tensor (σ=14): orientation encoded as a
   unit vector in RG, coherence in B.
6. **Metrics.** Wrap-seam step ÷ mean interior step, per axis, recorded in
   the JSON sidecar (pre- and post-seam-treatment).

**Design-vs-code gap (recorded, not hidden).** The header docstring designs
*three* seamlessness defences — (a) a quiet-join roll search, (b) a
frequency split with the low layer made exactly periodic, (c) seam-band
symmetrisation of the high layer. The shipped `run()` implements only a
single full-image seam-band symmetrisation (one operation standing in for
b+c); the quiet-join roll search (a) does not exist in the code. §4 and §5
should be read with that in mind: the weakest version of the design is what
actually ran.

## 3. Verification (finisher, independent re-measurement)

| Check | Result |
|---|---|
| File dimensions/format | All 6 textures 1024×1024 RGB ✓ |
| JSON seam ratios vs shipped PNGs | Recomputed ratios match sidecars to ≤0.15 (8-bit quantisation) for all 3 species — **the sidecars honestly describe the shipped files** ✓ |
| Diffuse dominant strand angle (pipeline estimator on shipped files) | wolf 89°, bear 92°, fox 89° vs 90° target ✓ |
| Flow direction encoding | Per-pixel agreement with an independently recomputed tensor field: mean axial error 0.22–0.27°, 100% of coherence>0.3 pixels within 5°. Reflected-sign variant is 19–40° off → encoding is correct, no sign flip ✓ |
| Flow unit vectors | \|(2R−1, 2G−1)\| mean 0.996–0.998, p5–p95 tight on 1.0 ✓ |
| Flow B (coherence) | Means 0.26 (bear) / 0.30 (fox) / 0.36 (wolf); same ordering as the sidecar coherence scalars (different estimator: per-pixel σ=14 vs energy-weighted σ=10 — not a discrepancy) ✓ |
| Raw crops vs pipeline table | Crop PNG sizes match `JOBS` exactly ✓ |

**Consumer warning — do not summarise a flow map by its mean direction.**
A coherence-weighted circular *mean* of the flow field reads 115° (wolf) /
66° (bear) / 93° (fox), which looks like a 25° misalignment. It is an
estimator artefact: these coats have broad, skewed axial orientation
distributions, and a mean over them is meaningless. The histogram *mode* of
the same fields is 88–92°, and the per-pixel check above is exact. Read flow
per-pixel (as a groom guide) or by mode — never by mean.

## 4. Per-species results

| | Wolf | Bear | Fox |
|---|---|---|---|
| Source | Grey wolf, taxidermy flank | American black bear, flank, summer coat | Red fox, dressed pelt torso |
| Crop | 620² @ (1000,495) | 560² @ (560,470) | 360² @ (1475,220) |
| Upscale to 1024² | 1.65× | 1.83× | **2.84×** |
| Raw strand angle → rotation → final | 105° → +17° → 90° | 2° → −88° → 90° | 89° → 0° → 89° |
| Coherence (sidecar) | 0.425 | 0.280 | 0.395 |
| Nominal tile size | 20 cm (51.2 px/cm) | 15 cm (68.3 px/cm) | 12 cm (85.3 px/cm) |
| Diffuse mean colour | `#AF6C45` warm agouti brown | `#495651` grey-green-brown | `#D96740` russet |
| Seam ratio x, pre → post | 2.97 → **3.63 (worse)** | 5.08 → 4.90 | 16.86 → **20.77 (worse)** |
| Seam ratio y, pre → post | 3.34 → 3.45 (worse) | 6.40 → 5.50 | 27.81 → 22.78 |

Notes per species:

- **Wolf — the success of the three.** The raw crop is a rich agouti flank:
  dark guard-hair blotches over pale undercoat, crisp strand detail. The
  tile preserves all of it. Its tiling failure (§5) is *motif repetition* —
  the crop's distinctive dark blotch is recognisable in every repeat — not
  seam steps. As a single patch it is genuinely good.
- **Bear — the colour caveat.** Coherence 0.28 is the lowest (a wavy,
  unkempt summer coat — the measurement is believable). The tile reads
  grey-green-brown, **not black**: de-lighting a dark photograph divides by
  the illumination field and percentile-stretches what's left, which
  amplifies whatever colour the shadowed coat held (here, a green-grey
  cast, plausibly foliage bounce in the source photo). Use the bear tile
  for strand structure/flow, not for black-bear colour.
- **Fox — crop-limited.** Two compounding problems, both visible in the raw
  crop: the dressed pelt's dark parting groove runs through the crop, and
  at 360² source pixels it is the softest tile after the 2.84× upscale.
  The groove repeats under tiling as a regular dark stripe (§5). The
  russet colour itself is right, and its flow map is the most faithful of
  the three by dominant direction (mode 88°, mean 93°).

On the seam ratios generally: two effects inflate them beyond "the seam is
a hard line." (1) The band blend makes the wrap step equal to the step
between rows one band-width (192 px) apart in the original — small for
smooth content, large for strand content. (2) The denominator (mean 1-px
interior step) is tiny along the strand direction for well-aligned fur, so
the y-ratio is harsh by construction. The ratios are therefore a
*pessimistic* seamlessness measure — but the renders show the pessimism is
warranted for fox and roughly fair for wolf.

And the seam treatment itself: symmetrisation **did not reliably help** —
it improved bear (both axes) and fox-y, but made wolf (both axes) and fox-x
measurably worse. It guarantees value continuity of the blended function,
not a small measured step, and for high-frequency strand content those are
different things.

## 5. Proof renders (the gap, closed for two species)

As found, `proofs/` was empty and `render_proofs.py` had never produced
output. It also **could not have run as shipped**: `clear_scene()` loads an
*empty* factory scene, after which `setup_world_and_lights()` indexes
`bpy.data.worlds["World"]` — a KeyError, since the empty scene has no World
datablock. (Whether the original agent hit this or simply died first is
not determinable from the files.)

The finisher ran the script's own plane proof — plane at 3× tile width,
texture repeated 3×3 so all wrap seams cross the frame, Cycles 48 samples,
Blender 5.2.3, `--threads 2` — via an external driver that adds the one
missing world guard and otherwise calls the shipped functions unchanged.
The shipped script was not modified. Two of three species were rendered
(wolf = best metric, fox = worst; bear is bracketed), plane only (the
sphere proof conflates tiling with the sphere's own UV seam):

- [proof_fox_plane3x3.png](proofs/proof_fox_plane3x3.png) — **tiling is
  obvious at a glance.** The crop's dark parting groove repeats as a grid
  of dark stripes; the surface reads as pleated plush, not fur. The
  ~21–23× seam ratio predicted a visible failure and the render agrees.
- [proof_wolf_plane3x3.png](proofs/proof_wolf_plane3x3.png) — strand detail
  and agouti mottling read beautifully *within* a tile; across tiles, the
  dark blotch motif repeats recognisably and the 3×3 grid is easy to see.
  Seam *steps* are not the problem here; repetition of a unique motif at a
  20 cm period is.

Working rule from both: **use these tiles as one patch per region** (or
under a card/strand layer that breaks the period), never as multi-repeat
ground cover, until a larger, motif-free tile exists.

## 6. Position against A11 and A15

The three texture briefs are complementary, not competing:

- **A9 (this) — capture.** The only route that records a real coat's actual
  colour statistics and strand lay, including the guard/undercoat mixture
  *as photographed*. Output is a flat diffuse + flow swatch: it cannot be
  re-patterned (a wolf tile cannot grow stripes), cannot separate guard
  from undercoat, and has no per-follicle banding — the agouti banding is
  in the picture, not in a model.
- **A11 (FUR_COLOUR) — synthesis by biology.** Shaft band profiles +
  melanism field *reprogram* the hairs: any pattern, any species recipe,
  distance colour by population integral. It generates; it does not
  measure. A9's tiles are its natural ground truth — e.g. A11's wolf guard
  integral `#76634a` vs A9's wolf tile mean `#AF6C45`: the photo tile is
  lighter and warmer, as expected (flank crop includes pale undercoat
  show-through, and de-lighting lifts mid-tones), so the pair brackets the
  plausible range rather than contradicting.
- **A15 (HANDPAINT) — synthesis by craft.** A painted stroke recipe
  (diffuse + roughness from the same stroke events) for stylised coats
  where an artist's hand, not an animal, is the reference.

A9's flow maps also feed the groom side directly: they are the photographic
counterpart of A7's painted `FURP_direction` fields, and verify to the same
per-pixel standard a groom consumes.

## 7. Honest limits

1. **Seamlessness not achieved** by the pipeline's own metric (3.4–22.8 vs
   ~1.0 target) nor visually under 3×3 tiling (§5). Single-patch use only.
2. **Seam treatment unreliable** — symmetrisation worsened 3 of 6 measured
   axes; the docstring's stronger defences (quiet-join roll, frequency
   split) were designed but never implemented (§2).
3. **Physical scale is eyeballed.** `tile_cm` (20/15/12 cm) was estimated
   by eye from photographs with no scale reference; px/cm in the sidecars
   is indicative, not measured. Do not use it as strand-length truth.
4. **Every tile is upscaled** (1.65×/1.83×/2.84×); no tile is
   native-resolution, and fox strand detail is substantially interpolated.
5. **Bear colour is not trustworthy** (de-light cast amplification, §4).
6. **One flat diffuse only.** No roughness, normal, or height maps were
   derived; the coat's 3D structure is a lit 2D projection — image-space
   lay, no groom geometry. (Contrast A15, whose roughness is registered to
   its diffuse by construction.)
7. **Specimen state is baked in**: taxidermy flank, summer coat, dressed
   pelt. These are dead-animal coats in arranged poses, not live pelage
   under natural light.
8. **Proof coverage is partial**: finisher rendered wolf + fox planes
   only; bear plane and all sphere proofs remain unrun, and
   `render_proofs.py` still contains the World KeyError (§5) — fix it
   before relying on it.

## 8. If this is picked up again

- Re-crop fox from a parting-free region (the source photo has other
  torso area) — the single highest-value fix; it is a stage-1 problem.
- Implement the docstring's quiet-join roll search before symmetrising;
  it is cheap and attacks the seam step directly.
- Prefer crops ≥1024 px native (wolf/bear sources allow larger squares
  than were taken) to kill the upscale softness.
- Treat A9 tiles as calibration swatches for A11 profiles and as photographic
  direction fields alongside A7's painted maps — the roles they verify well in.
