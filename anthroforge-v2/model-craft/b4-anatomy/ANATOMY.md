# B4 — ANATOMY-DRIVEN CONSTRUCTION: the torso pass study

*Model-craft wave, Nov 12, 2026. The original B4 agent built the passes,
exported the OBJs and produced `work/pass_stats.json`, then died before
the write-up. This doc is the finisher's reconstruction: scripts read,
stats independently recomputed from the shipped OBJs, renders
regenerated (the originals were unusable — see §5). Nothing in the
geometry was changed.*

**One-line result:** a sculptor's pass sequence — blockout → primary
form → muscle masses → tertiary detail → asymmetry — executed as
cumulative analytic displacement fields on one parametric torso region,
behaves the way the doctrine says it should: each pass moves the surface
by an order of magnitude less than the one before, the muscle pass does
the anatomical work, and the terminal asymmetry pass is measurable in
the geometry (+2.9 mm right-pec bias, −6.4 mm left-shoulder drop).

---

## 1. What the study is

A headless stand-in for brush work. There is no interactive sculpting on
this VM, so `scripts/build_passes.py` models a sculpt pass the way a
sculptor's passes actually accumulate: as smooth displacement fields
added cumulatively to a single mesh. The region is one torso — pelvis to
neck base, 1.35 m — parameterised as rings × angle (160 × 130 = 20,800
verts for passes 1–4), front = +Y, character right = +X, Z up, metres.

Because every pass is an explicit field with an amplitude, the study is
fully auditable: what a pass "adds" is not an impression from a render,
it is a term in the script and a number in the stats.

## 2. Method per pass

**Pass 0 — blockout.** The crude starting lump: 24 angles × 5 height
stations (every second control point of the profile), 120 verts, raw
piecewise profile, flat facets. Its only job is proportion: pelvis mass,
waist pinch, ribcage and neck taper in the right places at the right
heights.

**Pass 1 — primary form.** The same 9-station control profile
(z, rx, ry: pelvis 0.18 m → waist pinch 0.56 m → ribcage 0.95 m →
shoulder slope 1.24 m → neck base 1.35 m) interpolated and smoothed onto
the full 20,800-vert grid, plus one plane decision: the chest front is
flattened 10% across the z ≈ 0.98 band, because a chest is a plane with
masses on it, not a barrel. (The script docstring also claims "back
slightly fuller" — that term was never implemented; the flattening
factor is ≈0 at the back. Recorded here so nobody cites it.)

**Pass 2 — muscle masses (secondary form).** The anatomy pass, all
radial gaussian fields:

| Mass | Amplitude | Placement |
|---|---|---|
| Pectorals (pair, sternum-split) | +16 mm | θ ±0.58 rad, z 0.99, front-clipped |
| Sternum groove | −6 mm | centre front, z 0.99 |
| Deltoid caps | +13 mm | θ ±π/2, z 1.19 |
| Serratus fingers (3/side) | +4.2 mm | front-lateral, z 0.78 / 0.845 / 0.91 |
| Abdominal columns | +5 mm | θ ±0.30, z 0.48 |
| Transverse ab grooves (2) | −2.8 mm | z 0.435 / 0.525 |
| Obliques | +4 mm | θ ±1.25, z 0.55 |

**Pass 3 — tertiary detail.** Clavicle grooves (−2.6 mm along a shallow
V line), sternum centre line (−1.8 mm), a waist fold crease (−2.2 mm at
z 0.615), and two sinusoid octaves of sub-millimetre surface noise
(0.55 + 0.35 mm max). Everything in this pass is at or below the
millimetre scale — correctly so; tertiary detail that moves centimetres
is a pass-2 error.

**Pass 4 — asymmetry.** The life pass: right pec +3.2 mm fuller than the
left, left shoulder dropped (graded field, −9 mm at full weight), and a
gentle axial twist growing 0 → 0.022 rad over the height. A perfectly
symmetric torso reads as a mannequin; this pass is the difference
between a specimen and a person.

## 3. Measurements

From `work/pass_stats.json`, **independently recomputed by the finisher
from the shipped OBJs — chest/waist widths and radial std reproduce
exactly** (chest read at z ≈ 0.995, waist at z ≈ 0.564):

| Pass | Chest width (m) | Waist width (m) | Radial std (mm) | Move vs prev pass (mm) |
|---|---|---|---|---|
| 1 primary | 0.3364 | 0.2583 | 22.449 | — |
| 2 muscle | 0.3402 | 0.2639 | 22.894 | 3.706 RMS / 2.077 mean |
| 3 tertiary | 0.3407 | 0.2643 | 22.919 | 0.428 RMS / 0.327 mean |
| 4 asymmetry | 0.3406 | 0.2642 | 22.927 | 2.382 RMS / 1.732 mean |

One correction to the stats file: its `mean_move_vs_prev_pass_mm` is
**RMS displacement, not the mean** (the script takes sqrt of the mean
square). Both values are given above; the ordering is unaffected.

Reading the table: pass 2 does the anatomical work (largest surface
move; chest +3.8 mm, waist +5.6 mm wider as masses land). Pass 3 moves
the surface a third of a millimetre on average — a detail pass behaving
as designed. Pass 4's larger move is not surface detail; it is dominated
by the whole-form terms (twist + shoulder drop), which is what an
asymmetry pass is.

Finisher spot-checks on pass 4, measured directly off `pass4.obj`:
front chest rings (z 0.96–1.03) read **+2.84 to +2.88 mm** more radial
reach on the +X (right) half than the −X half — the fuller right pec,
as scripted. The −X half's maximum height drops from 1.350 m (pass 3,
symmetric) to **1.3436 m** in pass 4 — the left shoulder drop, realised
at 6.4 mm of its 9 mm field maximum by the grading.

## 4. Where it stopped

**The pass sequence is complete.** Pass 4 (asymmetry) is the terminal
pass of the design in `build_passes.py`'s own structure — there is no
pass 5 stub, no half-written field, nothing cut off mid-term. What the
dead agent never produced was (a) this write-up and (b) usable renders.
No further pass was run by the finisher, because the design has no
further pass to run; the genuine next step (a tissue pass — §6) is a
new study, not a completion of this one.

## 5. The renders — original set unusable, regenerated

The original `renders/pass*.png` cannot be used as evidence of anything
except a pipeline bug. `build_passes.py` writes **Z-up** OBJs; Blender's
OBJ importer copies the vertex data verbatim *and* stamps the imported
object with a +90°-about-X rotation (its Y-up assumption), tipping the
torso onto its side. All five original frames show a horizontal tube in
the corner of the frame, lit to flat white besides (900 W key ≈ 2.5 m
away blows the clay out completely). The originals are kept untouched
for provenance.

`scripts/render_views.py` (finisher) re-renders the unchanged OBJs with
exactly two fixes — importer rotation cleared so the mesh stands as
authored, and light energy brought down (150/45 W, clay albedo 0.55) so
the surface isn't clipped to white — into `renders/passN_view.png`:
flat grey studio world, same camera, same 460×580 / 48-sample Cycles
setup. In the corrected frames the stage progression reads as it
should: faceted blockout column → smooth primary silhouette → the
tertiary banding faintly visible at pass 3–4. The millimetre relief
itself is below this camera's readability; the numbers in §3 are the
evidence for it, the renders are evidence for the stages.

## 6. Relation to the house doctrine

**Head builds (skull → muscle → tissue).** Head v3's stage D builds the
layers as separate geometry: a Skull derived by offsetting the tissue
surface inward along normals by documented regional thicknesses, Muscle
patches (temporalis, masseter) separated from that offset and pushed
back out, tissue surface over the top. B4 is the same doctrine in a
different representation: instead of stacked meshes, the layers are
**cumulative fields on one surface** — profile (the bony landmark
stations: pelvis, waist, ribcage, neck) → muscle-mass fields → surface
detail. The correspondence is real but partial: B4's "skeleton" exists
only implicitly, as the control profile's stations. There is no bone
geometry, and no layer ever exists as its own mesh.

**MUSCLE_TISSUE_MODEL.** The engine's composition order is
`base → muscle field → tissue field → gravity/drape`, with tissue
*sampled over the muscled surface* because fat lies over muscle. B4
demonstrates the first half of that order in sculpt space — base form,
then muscle fields over it, each pass's input literally the previous
pass's surface. It does **not** demonstrate the second half: there is
no tissue pass and no gravity/drape term anywhere in the study. In the
shipping system that half lives in the slider/coupling layer, not in
sculpt space, so B4 is best read as the sculpt-side proof of the
muscle-field stage and its pass discipline — not as a model of the full
composition. A tissue-over-muscle pass study (submersion of pass-2
relief under a rising tissue field, per the definition-attenuation
curves) is the natural B4 follow-on and has not been done.

## 7. Honest limits

- **One region, tube topology.** The torso is an open ring grid: no
  arms, no head, no openings, no end caps. Nothing here tests how pass
  fields behave across a limb junction or a socket.
- **Radial-only displacement** (passes 1–3). Real sculpt masses slide
  tangentially as well as push out; only pass 4 breaks the radial rule
  (shoulder drop in Z, axial twist). Fields also cannot undercut —
  no overhangs, no fold geometry, the waist "fold" is a groove, not a
  fold.
- **Amplitudes are by-eye, not referenced.** The pass-2 masses are
  plausible sculptor's numbers, not measured from a reference body or
  the HIMBO/Fat Males field data the slider work is grounded in.
- **No tissue, no gravity** — see §6. The study's torso is a lean,
  defined torso at every pass; nothing in it speaks to fat bodies.
- **Script cruft, left as found:** pass 3 computes an unused `zz_line`
  variable and its fold-crease weight contains a no-op term
  (`|sin θ|**0` ≡ 1). Harmless, but the script is a demo, not a library.
- **Renders are stage evidence only** (§5); all quantitative claims
  rest on the OBJ recomputation in §3.

## Files

- `scripts/build_passes.py` — the study (original agent)
- `scripts/render_passes.py` — original renderer (kept; see §5)
- `scripts/render_views.py` — corrected re-render (finisher)
- `work/pass0_blockout.obj … pass4.obj` — per-pass geometry
- `work/pass_stats.json` — original stats (read RMS where it says mean)
- `renders/pass*.png` — original renders (broken framing; provenance)
- `renders/pass*_view.png` — corrected renders
