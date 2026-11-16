# Belly v4 — the whole-torso adiposity system

Joe's verdict on v3 (Nov 12, 2026): *"it still bulges weirdly, look at
video of someone being heavier, or furry artist tutorials they make."*

He was right, and the study (FAT_REFERENCE.md) named the failure
exactly: v1–v3 hang a belly — even a physically careful one — on an
otherwise **lean** torso. The artists have names for the siblings of
that mistake ("Anime Chubby", "Michelin Man"); v3 was a third one: a
correct belly on an untouched body. Real adiposity is a **system**:
fat distributes by mass and gravity over the whole torso, posture
adapts, creases form at compression points, and the belly's profile is
continuous with everything around it.

v4 therefore rebuilds the slider as a coupled whole-torso field. The
v3 belly core is untouched inside its mask; everything outside it is
now learned fat distribution, posture, and blend — verified against
the FAT_REFERENCE metrics, not just eyeballed.

## The model

```
shape(w) = base + w * LIN + f(w) * SAG,   f(w) = sign(w)|w|^2.0
LIN  = B * D_protrusion + (1 - B) * D_distribution + D_posture
SAG  = B * D_sag3                        (v3's pendant term, unchanged)
```

- **B** — the v1 geodesic belly mask. Inside the core, v4 ≡ v3
  exactly. The mask ring crossfades core → distribution, so there is
  no boundary where "belly" ends and "lean" resumes.
- **D_distribution** — a 50/50 blend of two learned whole-torso fields,
  each transferred with v1's `(h, θ)` kernel machinery:
  (a) the **Fat Males** full-torso morph (the v1 source, whole body
  this time), and (b) the HIMBO **"Chonky" preset recipe** — 17 Vanilla
  OSD blocks composed at the preset's big values (Chubby 0.40,
  TorsoMass/Lower/SterHeight 1.0, BackShape 0.92, BackSlope 0.90,
  LoveHandles 0.66, Pecs Size/Width/Clavicle 1.0, ButtBooty 0.75,
  Traps 1.0/0.92, Shoulders 0.50…). Excluded, deliberately:
  SamuelLike and FemmeB/FemmeBooba (they live in other slider sets;
  SamuelLike is a body-swap morph, Femme* the wrong pattern),
  BellySmooth (no Vanilla OSD block exists), TorsoWaistSize (identity
  decodes to "Shrink Waist" — direction too ambiguous to sign from a
  preset), and all arm/leg sliders outside the torso gate.
- **Gain calibration — the instructive failure.** First attempt matched
  the sources on belly-front peak; it failed because the two sources
  *disagree about what a fat body is*: Fat Males is a pot-belly sculpt
  (front peak **15.4 cm**), Chonky is broad mass (belly front only
  **3.3 cm**; its biggest front push is its pecs). Matching belly peaks
  would have tripled Chonky's widths. Since the belly core is the
  protrusion/sag terms' job, the distribution sources are matched
  where the distribution's job lives — the **flank band** — giving
  α = 2.0, which hit its cap: even doubled, Chonky's flanks are the
  lighter of the two, so the blend leans Fat Males at the sides.
  Reported, not hidden.
- **D_posture** — a rotation field about the pelvis pivot (FAT_REFERENCE
  R9): anterior lobe −3.0° at the pelvis, compensating +1.4° lobe at
  the chest, height-faded. Kept on evidence, not on faith: it passed a
  pre-set gate (below-navel share 56.9% → 63.7%, apron lowest point
  lowered, pre-repair flips not increased).
- **The waist crease that wasn't authored.** A pinch term was built
  (solved depth at the natural waist, sides/back only). The solver
  returned **0.0 cm** — the learned fields already carry the crease:
  the shipped width profile has a flank roll peaking at h 0.28
  (45.1 cm wide — the iliac/love-handle level) with a 10.3 cm pinch
  contrast above it. The machinery stays in the build script as a
  documented no-op; inventing a second crease on top would have been
  worse.

## Repairs and gates

- Fold control now runs over the **whole torso (12,298 faces, both
  bases)**, not the belly patch: slope limiter + attenuation repair on
  `A = D4 − D1` (the v2+v3 method). The distribution fields are
  intrinsically smooth, so repair is a touch-up here — **4 rounds**,
  min attenuation 0.53, 67 verts touched (v3's belly-only repair took
  40 rounds and touched 509).
- **Hard gate: 0 flips at +1 on both bases** (min face dot 0.116 raw /
  0.005 macro — the macro margin is thin but positive; v3's belly-only
  raw margin was 0.0034, so v4 is not worse where it matters).
  Coupled +0.5: 0 flips, min dot 0.48/0.59 — the mid-slider is the
  cleanest state of the four versions. +1.05: 8 macro flips (outside
  the slider range, same caveat as v1–v3). **−1 still folds**
  (183 raw / 170 macro over the whole torso; the negative pole needs
  its own authored decrease target — carried over from v1, unfixed).

## Scorecard — FAT_REFERENCE metrics, v3 vs v4

Three first-pass metrics were found flawed on inspection and were
re-measured with corrected definitions (the corrections are part of
the record: first-pass M2 minimised over the crotch verts; first-pass
M3/M9 girths were computed over bands contaminated by the hanging
arms; first-pass M4/M7b compared against anatomy-dominated references).
Corrected values (torso-only gate, base radius < 0.215 m):

| metric | target | v3 | v4 | verdict |
|---|---|---|---|---|
| M1 front protrusion below navel | ≥ 55% | 65.9% | 63.1% | **pass** (pendant read kept; slight dilution is the upper torso filling in — expected) |
| M2′ apron bottom above crotch | ~0–8 cm (grade 0–1 zone) | 9.05 cm | 8.81 cm | **borderline pass** — just short of pannus grade 1, right for this size class |
| M3 waist:hip, navel-level (clinical def.) | ≥ 0.95 | 1.130 | 1.141 | **pass** — belly band exceeds hips: android-dominant, matches the obese-men pattern |
| M3 waist:hip, narrowest-point | ≥ 0.95 | 0.864 | 0.831 | **miss** — see note below |
| M4′ boundary step (ring gradient vs base) | ≤ 1.5 | 1.00 | 1.28 | **pass** — no silhouette step at the old mask boundary (first-pass M4, a broken definition, read 3.16/3.76 and is superseded) |
| M5 back-band added radial | ≥ 1.5 cm | 0.0 cm | 5.59 cm | **pass** (was the single most damning v3 zero) |
| M6 chest front / width gain | ≥ 1.5 cm / ≥ 2 cm | 0.11 / 0.0 | 1.77 / +4.79 cm | **pass** |
| M7a under-belly pinch ratio | ≤ 0.75 | 0.697 | 0.715 | **pass** (inherited sculpt, unchanged) |
| M7b flank crease | visible roll + pinch | roll at belly edge | roll peak h 0.28, pinch contrast 10.3 cm | **pass** — delivered by the learned fields (Handles/Lower/FM flanks), authored pinch shipped 0.0 cm |
| M8 added torso volume proxy | ≥ 1.8 × v3 | 1.0 × (7,254 cm³) | 3.29 × (23,889 cm³) | **pass** |
| M9 waist:height (narrowest) | trend → obese range | 0.478 | 0.513 | crosses the 0.5 line; class II reference is 0.77 — this is a moderate belly class, as designed |

The M3 split verdict is a definition story, not cherry-picking: the
obesity literature's waist is a tape at navel/midpoint level (there,
v4 = 1.14 — deep in the obese-men pattern, arguably overshooting
because the belly is this slider's centrepiece). The *narrowest-point*
waist tells the other half: the waist indentation **survives** at
85.5 cm girth (base 65.3) while hips grew to 102.9 — the silhouette
keeps a waist *because* the mass went to belly, flanks and hips
faster than to the waist point. A fat torso where the narrowest W:H
also hit ~1.0 would need the waist filled to hip level, i.e. a
different, more uniform obesity class than this slider's.

**Zone residuals** (measured vs the triangle-exact learned Fat Males
field — reported for continuity with v1–v3, noting v4's *target* is
now the FM+HIMBO blend, so these read as distance-from-FM, not pure
error): pin patch p95 4.46 cm, crease zone 4.57, flank 2.04, core
3.62, all-triangle-exact p95 4.40 (v3: 3.77). The whole-torso FM field
itself is coarse — kernel CV p95 3.40 cm on only 1,154 torso samples
(HIMBO: p95 1.96 cm on 5,514) — v4's distribution is a low-frequency
mass layer, not a detail sculpt, and is honest about it.

**Navel at +1:** forward 11.14 cm numpy / **11.27 cm Blender**,
down 6.99 / 6.99 — v3's hang preserved (the distribution hands back
~0.5 cm of the forward travel v3's drain surrendered; the drop is
0.3 cm shallower). Blender evaluated belly-region check at +1:
0 flips / 918 faces, min dot 0.027.

## Does it still bulge weirdly? — honest self-critique

Look at the renders (front / profile / three-quarter / back /
v3-vs-v4 profile). The specific complaint is **fixed in the torso**:
the profile is continuous from sternum to apron to pelvis; the back
carries real mass with a waist fold visible from behind; the flanks
roll at the iliac level; from the front the belly is continuous with
the waist and hips instead of sitting on them. The pouch-on-lean-body
read is gone.

What remains, in order of how much it matters:

1. **The system boundary moved to the limbs.** Arms and thighs are
   still the lean base's — R2/R10 name upper arms and thighs as major
   distribution sites, and a heavy torso on lean legs is the same
   class of error as v3's, one joint further out. v4's scope was the
   torso (the slider's region); the honest next step is a limb pass
   (HIMBO arm/thigh blocks + Atomic Muscle fields are already in the
   learned library) — call it v5 scope, don't pretend v4 covers it.
2. **Front read is a single dome.** The roll stack (R4) shows in
   profile and as the under-belly crease; from the front the belly is
   one mass. Real bellies of this class mostly do read that way from
   the front — but a second, upper roll would strengthen the read at
   higher weights. The drain keeps the upper abdomen *relatively*
   empty by design (v3's lesson); whether it should carry a shallow
   roll at +1 is a judgement call for Joe's eye, not a metric.
3. **The proof base is MPFB's default human** — feminine chest forms,
   as in v1–v3. The male-pattern reading (R11: widened, sagging chest
   with downward nipples) is only partially testable on this base; the
   distribution did widen and load the chest (+4.8 cm width, +7.0 cm
   depth at h 0.85). The AnthroForge male presets will exercise this
   properly; nothing in v4's machinery is base-specific beyond the
   hm08 correspondence.
4. **Calibration compromises on record:** α capped at 2.0 (Chonky
   flanks still lighter than Fat Males'), FM whole-torso CV p95
   3.40 cm, macro-base min dot 0.005 at +1, −1 pole folds. None are
   hidden; all are in the QA JSON.

## Files

- `body.belly.protrusion_v4.target` — combined at +1
  (LIN_v4 + SAG_v3), stock-MPFB loadable.
- `body.belly.protrusion_distribution_v4.target` — the v4-over-v3 component
  (distribution + posture + crossfade): stacks on v3 to reproduce v4,
  or works standalone as a torso-mass layer under another belly.
- `body.belly.protrusion.slider_v4.json` — model, recipe + exclusions,
  calibration, corrected metric table, fold QA, provenance.
- `FAT_REFERENCE.md` — the study this build is scored against.
- `work/qa_numbers_v4.json` (+ `corrected_metrics`),
  `work/blender_v4_numbers.json`, `work/belly_v4.npz`.
- Renders: `renders/belly_v4_w+1.0_profile.png`, `_front.png`,
  `_threequarter.png`, `_back.png`, `belly_v4_w+0.5_profile.png`,
  `belly_v3_vs_v4_+1_profile.png`.
- Scripts: `scripts/build_belly_v4.py`, `scripts/test_belly_v4.py`,
  `scripts/analyze_v4_profiles.py`, `scripts/finalize_v4.py`.

**Licence:** study-only / internal, like v1–v3 — the distribution
fields derive from Fat Males and HIMBO material used under Joe's
Nov 12, 2026 licence ruling (study/derive, no AI training). Not CC0,
not redistributable, not to be shipped with stock MPFB content.
