# MUSCLE × TISSUE MODEL — the fat+muscle composition layer

*Design + implementation doc, Nov 12, 2026. Joe's directive: "some folks
are both fat and muscular like you noticed, so keep coming up with ways
to model that properly" — plus his same-day addition: "also, the
pear-shape to big chest variables."*

*Companion to `BARA_LESSONS.md` (the two-vector doctrine and the §6 E
backlog this implements), `first-proof/FAT_REFERENCE.md` +
`GRAVITY_V4.md` (the fat system), `preset-orc-bara.md`,
`presets-titan-batch1.md`. Implemented in the app core:
`anthroforge-app/core/sliders.py` (coupling evaluation),
`anthroforge-app/library/couplings/` (8 declarative records),
`anthroforge-app/library/sliders/` (20 canonical records),
`anthroforge-app/tests/test_couplings.py` (26 tests; suite 53 green).*

*Tag discipline as elsewhere: **[S]** sourced, **[D]** derived,
**[E]** estimate/calibration. Everything derived from HIMBO/Atomic
Muscle material is **study-only / internal** under Joe's Nov 12, 2026
licence ruling; the coupling machinery and curves are ours.*

---

## 1. The problem this solves

Fat and muscle are not two independent slider stacks. Naively adding a
fat field and a muscle field produces the failures the studies already
named: the Fat Males read (belly with no core under it), definition
sliders that stay carved under any amount of tissue, a "cut" preset
whose only difference from the strongman is a smaller Muscle number.
Real combined bodies behave differently:

- Fat **drapes over whatever is under it** — the same fat layer makes
  a different silhouette over a built core than over a lean one.
- **Definition is a tissue dial, not a muscle dial** (BARA_LESSONS
  R16): the same muscle reads bodybuilder or strongman purely by the
  fat layer over it.
- Tissue is **regional**: a lifter's forearms stay lean while the
  abdomen loads; the largest forms (traps, pecs) still displace the
  surface at tissue levels that completely submerge the abs.
- **Where** the mass sits is its own variable — pear to big-chest —
  and it steers fat placement and muscle deposition differently.

The model below is the interaction layer: five mechanisms (§2–§6),
one distribution axis (§3), all expressed as declarative coupling
records evaluated over the character's raw slider vector. The stored
character record keeps the RAW vector; couplings are an evaluation,
never an edit.

---

## Amendment — Nov 12, 2026 (later same day): chest broadness + the wrap

*Joe, same session: "also need to be able to edit broadness of chest,
remember, fat goes from front to sides as well, the sides dont stay
stiff." Two additions, both now implemented and tested:*

1. **Chest broadness is a slider** — `body.chest.broadness`, a
   two-pole **frame** variable (lateral span of the chest/ribcage),
   grounded in the HIMBO decode's width fields and specified in full
   in the record (carriers, composition, acceptance gates). It is
   distinct from chest *depth*, from TorsoMass (volume fill) and from
   PecsSize (plate volume); §3 gains a closing note on how it relates
   to the distribution axis.
2. **The wrap is a named mechanism** — tissue distributes
   *circumferentially*, so the tissue field's angular profile is now
   specified, factored and QA-checked (§4, "Circumferential wrap"):
   a per-band wrap factor couples flank gain to frontal gain, and
   **stiff sides** is a defined failure with a floor ratio. The
   evaluator ships it as the `muscle_tissue.tissue_wrap` coupling
   (the 8th record); the geometry consequence for the proofs is
   stated in §4 and §9 item 7 — calibration target, not a rebuild.

## 2. Composition order — engine doctrine

```
geometry:  base -> muscle field -> tissue field -> gravity/drape
vector:    authoring -> distribution -> muscle -> tissue
```

**Fields compose in this order, always.** Muscle is applied to the
base first; the tissue field is then sampled over the *muscled*
surface; gravity/drape (the v4 system's mobility fields and sag
terms) acts last, on the tissue over the muscled shape. The reasoning
is physical, not stylistic: subcutaneous fat lies over muscle, so its
rest shape is the muscled shape; and what hangs, hangs from what is
underneath — a power belly hangs from a built core (BARA_LESSONS
R17), which is why v4's drape machinery takes the muscled surface as
its input rather than the base.

The vector-layer evaluation (`evaluate_effective_vector`) mirrors the
order in four stages, recorded declaratively in
`muscle_tissue.composition.json` and enforced against the code
pipeline by test:

1. **authoring** — the TissueDefinition dial fills unset sliders
   (§6.1); explicit values always win.
2. **distribution** — the mass-distribution axis resolves to
   per-region factors for both vectors (§3).
3. **muscle** — muscle values pass through *untouched*. This is a
   tested invariant, not a hope: poles are tissue moves (R16), so no
   tissue-stage mechanism may rewrite the Muscle vector itself. The
   one exception is named and bounded: show-through (§6.3) scales the
   top *form* sliders at the tissue stage, because that is the tissue
   sampling over them, expressed in vector terms.
4. **tissue** — regional tissue resolves (§4), then definition
   attenuation (§5), show-through (§6.3), and the PowerBelly terms
   (§6.2) are computed. Gravity's *parameters* (core share, tilt) are
   derived here; gravity itself remains geometry-stage.

## 3. The mass-distribution axis — pear to big-chest

One control, `body.distribution` ∈ [−1, +1], first-class alongside
the two vectors. Five archetypes are **presets on the axis**, not
separate systems:

| Point | Archetype | Chest:waist:hip character | Ratio anchors |
|---|---|---|---|
| −1.00 | **pear** (gynoid) | hips/glutes/thighs dominant, chest small | waist:hip ≈ 0.65–0.75 [E]; hip girth > chest girth [S pattern] |
| −0.35 | **hourglass** | chest ≈ hips, waist pinched | waist:hip ≈ 0.70 [E]; chest:hip ≈ 1.0 [E] |
| 0.00 | **rectangle** | even deposition | waist:hip ≈ 0.85–0.90 lean male [S, FAT_REFERENCE] |
| +0.45 | **apple** (android) | midsection dominant | waist:hip ≥ 0.95, converging 0.98–1.02 at class II–III [S, FAT_REFERENCE] |
| +1.00 | **inverted triangle / big-chest** | chest/shoulders dominant, hips narrow | shoulder:hip width ≈ 1.3–1.5 [E]; chest:waist toward the BB band 1.55–1.75 at low tissue (BARA_LESSONS M4) |

The axis carries **weight multipliers over four macro regions**
(chest / waist / hips-glutes / thighs), piecewise-linear between the
archetype anchors (full table in `muscle_tissue.distribution.json`;
pear: chest 0.55, waist 0.85, hips 1.45, thighs 1.40 — inverted
triangle: chest 1.45, waist 0.85, hips 0.60, thighs 0.70). The
multipliers are **[E] calibrations** chosen to drive builds into the
ratio bands above; they are tuning values for the first geometry
builds to tighten, not measurements.

**It steers both vectors, at different strengths** — this is the
crux of Joe's "pear-shape to big chest variables":

- **Tissue at full strength (×1.0).** Fat placement is strongly
  pattern-driven: gynoid vs android deposition is the sourced
  physiology (FAT_REFERENCE R2 and the patterning note — patterning
  is a property of the *person*). The distribution factors multiply
  the regional tissue weights (§4).
- **Muscle at reduced strength (×0.6).** Muscle distribution is
  partly frame and training history, less plastic than fat placement.
  A muscle-driven pear exists (glute/thigh-dominant lower-body
  lifter: speed-skaters, lower-body specialists) and a muscle-driven
  inverted triangle is the classic gym build; both are the *muscle*
  factor set (emitted as `distribution.muscle.*` derived values for
  the geometry layer) with tissue comparatively even.

So "a pear build" is underdetermined until both vectors speak: the
worked examples in §7 show a tissue-driven and a muscle-driven pear
at the same axis point producing measurably different bodies.

**Patterning notes.** The android/gynoid pattern is a person-level
property (clinical, and the fat tutorials agree), which is why it is
one axis on the character, not per-part settings. Sex/species
patterning enters as *default axis positions and profile choices for
presets* (male-default presets sit android-leaning; the bear species
thesis is barrel-even), never as a hard constraint — the axis stays
user-drivable across its whole range for any character.

**Chest broadness — the frame the chest factor lands on** *(added
by the Nov 12 amendment)*. The axis's chest multiplier is a
*deposition* factor; it presupposes a frame to deposit on, and that
frame is its own variable: `body.chest.broadness` ∈ [−1, +1], the
lateral span of the ribcage/shoulder girdle. The decode carries it
as HIMBO's largest width fields — the TorsoShoulderInc/Dec pair
(4,968 / 5,000 diff verts; max 0.0597 m / 0.0334 m — the poles are
asymmetric because the source pair is) — blended with TorsoWidth
(ribcage band, max 0.0217 m, 99.5% torso-region) and PecsWidth
(plate *extent*, max 0.0150 m, 99.9% chest), plus the lat component
that makes frontal width taper (BARA_LESSONS R11). Three
distinctions keep it honest: broadness is **span, not depth** (the
sagittal axis is TorsoSterDepth/PecsFlatten territory), **not
TorsoMass** (barrel volume — a narrow frame can be thick, a broad
frame lean), and **not PecsSize** (front plate volume; the plates
sit on the frame broadness sets). In the pipeline it behaves like
the Muscle vector: authored, and never rewritten by the tissue
stage (test-asserted) — it is deliberately *not* a show-through
target, because the lateral silhouette gain at tissue is the wrap
mechanism's output (§4), not a boost to the frame. Full grounding,
build spec and acceptance gates (BARA_LESSONS M8 band,
width-vs-depth orthogonality) live in the record itself.

## 4. Regional tissue

```
tissue(region) = clamp01( level x profile_weight(region)
                          x distribution_tissue_factor(macro(region)) )
```

- **level** — the TissueVector summary: the character's explicit
  `body.tissue.level` if set, else a weighted mean of the tissue
  sliders present (Chubby 0.55 / MassSmooth 0.25 / BellyPot 0.20).
- **profile** — the `lifter` profile **[E] weights on the [S]
  ordering** of FAT_REFERENCE R2 (fat follows muscle mass; abdomen
  first, then thighs, upper arms, chest, flanks, back; the
  water-balloon rule pools low): abdomen 1.00, thigh 0.80, upper
  arm 0.70, flanks 0.65, chest 0.60, glutes 0.60, back 0.55,
  neck 0.45, calf 0.30, forearm 0.25, **foot 0.15, hand 0.12**.
  The hand/foot entries were absent in the first authoring — the
  same zero-endpoint assumption the belly v5 geometry made, and
  Joe corrected both (Nov 12, 2026: "wrists and hands also need
  fat, not massive amounts but that is realistic"). Terminal
  tissue is small but real: the v5.1 geometry (GRAVITY_V5.md
  addendum) measures it from the Fat Males hand/feet deltas —
  wrist girth +2.98 cm total at full tissue, proximal fingers
  +13.5–15.4% radial thickness — so the profile weights are
  small **nonzero** by design: hand/foot definition attenuates
  slowest of all, but it attenuates, and the regions exist.
- Regional tissue is emitted as `tissue.<region>` derived values —
  it is the quantity every other coupling consumes, and the quantity
  the geometry layer will use to modulate the tissue field per
  region.

**Circumferential wrap — the angular dimension** *(added by the
Nov 12 amendment; Joe: "fat goes from front to sides as well, the
sides dont stay stiff")*. Regional tissue says *how much* sits at a
height band; the wrap says *how it is spread around the ring* at
that band. A tissue field that grows only forward — belly deeper,
chest deeper, flanks still at the base surface — is the angular
sibling of the failures already named (v3's mask-boundary step,
FAT_REFERENCE R1's local add-on): the silhouette reads stiff-sided
because the mass never went around. The reference pattern is
sourced: deposition loads the abdomen first and the flanks late
(FAT_REFERENCE R2's ordering), the clinical pannus definition
explicitly includes "flanks and back" (R6), and at heavy classes
the whole ring fills — waist:hip converges to 0.98–1.02 [S]. The
sides are a deposition site in their own right, not spillover:
HIMBO ships a dedicated LoveHandles block (1,071 diff verts, max
|delta| 0.0224 m), and v4's flank roll (peak at h 0.28, 10.3 cm
pinch contrast, GRAVITY_V4 M7b) was delivered precisely because the
learned fields carried flank mass.

The mechanism, per height band (waist, chest):

```
wrap_factor(band) = interp(anchors, tissue(front of band))     [E]
required:  side radial gain >= wrap_factor x front radial gain
anchors:   front 0.00 -> 0.35 · 0.15 -> 0.45 · 0.50 -> 0.75 ·
           0.85 -> 1.00 · 1.00 -> 1.00
```

The factor *rises* with front tissue: at lean levels the flanks
legitimately lag (the ordering is real), and by the heavy classes
the ring must close. **Stiff sides, defined as a QA check:** in a
band whose front tissue is ≥ 0.30, a measured side/front radial-gain
ratio below the **floor 0.40 [E]** fails. At the vector layer the
`muscle_tissue.tissue_wrap` coupling emits `wrap.factor.<band>`
(both bands) and `wrap.ratio.waist` (flanks ÷ abdomen from the
resolved profile — the waist band is the one with a true side
region) and raises the stiff-sides advisory if the *profile* ever
violates the floor; the chest band emits its factor only, its ratio
being a mesh measurement. On a mesh the same check is a build
failure, not an advisory.

**Geometry consequence (stated, not rebuilt).** The v5/bara tissue
transfer kernel already runs full-circle in φ (GRAVITY_V5), so the
wrap factor lands there as a **calibration target**: after transfer,
audit each band's angular gains — flank-sector mean radial gain ÷
front-sector mean radial gain, in the band's height window — and if
the ratio falls below the `wrap.factor` the character's tissue
emits, scale the side sectors up to meet it *before* fold repair
(a front-heavy source field is exactly the case this catches). A
ratio below the 0.40 floor at front tissue ≥ 0.30 fails the build.
For the bara-proof this extends FAT_REFERENCE M6 (chest gain) from
a front-band measurement to a ring measurement. The v4/v5 fields
came from full-circle transfers of flank-carrying sources and are
expected to pass; the audit is owed at the next build, not a reason
to rebuild them now.

## 5. Definition attenuation

```
effective_definition = raw x A(region tissue) x G(muscle)
```

- **A** — per-region-class piecewise-linear curves (full anchors in
  `muscle_tissue.definition_attenuation.json`), fitted **[E]** to
  the **[S]** body-fat bands of BARA_LESSONS §1/§5-M10 mapped
  through the regional profile: at regional tissue ≈ 0.15 (the
  <10% body-fat band) A ≈ 0.98–1.00 everywhere — full definition.
  At strongman tissue (regional ≈ 0.5–0.65), abdomen A ≈ 0.5–0.65:
  valleys soften, mass reads. At gachidebu tissue (≈ 0.85+), the
  abdomen is mostly submerged (A ≈ 0.28) while the yoke still
  reads (A ≈ 0.57).
- **Region classes submerge at different rates** — the ordering is
  the reference pattern, not a guess: abdomen fastest, then chest,
  back, yoke (traps — the largest forms), and **limb_distal
  (forearms/calves) slowest of all**: grip-built forearms keep their
  separation at tissue levels that erase the V line. (No current
  canonical slider targets limb_distal; the curve ships now so
  forearm/calf definition sliders land on a fitted curve, not a
  new invention.)
- **G, the muscle gate** — `0.5 + 0.5 x muscle` **[E]**: definition
  over no muscle reads at half strength, not zero (lean untrained
  bodies do show separation) and not full (one V-line slider must
  not hand a non-lifter bodybuilder abs — see the femboy contrast
  in §7).
- Targets: TrapsValleys → yoke, BackDefinition → back, PecsCrease →
  chest, VLine + FlatAbs → abdomen.

**Interaction: distribution × attenuation.** Because A reads
*regional* tissue, the distribution axis moves definition without
touching any definition slider: a pear at level 0.6 keeps its pec
crease (chest tissue 0.21) while a big-chest build at the same level
and same raw crease submerges it (chest tissue 0.36 — §7, and
`test_distribution_moves_definition_via_tissue`). This is the
mechanism that makes the axis a modeling variable rather than a
preset label.

## 6. The preset-layer couplings

### 6.1 TissueDefinition dial (BARA_LESSONS A5)

One dial, `body.definition.dial` ∈ [0, 1], linearly interpolating
the two orc sub-presets' authored tissue vectors — dial 0 *is*
`orc_bara_strongman` tissue (Chubby 0.65, MassSmooth 0.65,
Valleys 0.40), dial 1 *is* `orc_bara_bodybuilder` tissue (Chubby
0.05, MassSmooth 0.10, Valleys 0.85, BackDef 0.95, PecsCrease 0.75,
VLine 0.85, FlatAbs 0.90). It **fills only unset sliders**; anything
the character sets explicitly wins. The orc sub-presets are its
first two stored points, exactly as A5 specified.

### 6.2 PowerBelly (BARA_LESSONS §6 E item 2)

One Belly control whose character changes with the Muscle vector,
expressed as coupling terms — never a mode switch:

```
belly_composite = weighted mean of the belly sliders present
core_share      = muscle x belly_composite      (built-core share)
drape_share     = 1 - core_share                (v4-system share)
tilt_deg        = 3.0 deg x core_share          (posture-shear scale)
```

The geometry layer routes `core_share` of the belly field through
the built-core variant (low-sitting, tilt-coupled, continuous with
TorsoLower's muscle+fat waist stack, R18) and `drape_share` through
the v4 fat system. The tilt anchor is v4's own −3.0° pelvic lobe
**[S, GRAVITY_V4]**, scaled by how much of the belly is core. At
muscle ≈ 0 the terms degenerate cleanly to pure v4 (core_share 0,
drape 1.0) — the low-muscle belly is the v4 system, by construction,
not by branching.

**Distribution interaction:** apple *is* the belly-dominant cell —
at distribution +0.45 the waist tissue factor (1.45) saturates
abdomen tissue and crushes abdominal definition while the belly
terms run (§7). **Advisories** (warnings, never blocks): belly
composite out-sliding the chest slider by > 0.25 at lifter muscle
levels → verify M4 chest:waist ≥ 1.28 on the mesh (R17 — the chest
ring stays dominant); belly > 0.6 with muscle < 0.3 → the tissue-only
warning (the Fat Males failure, R18).

### 6.3 Show-through

The largest forms displace the tissue surface above them (R17's
chest, the yoke at gachidebu). Vector-layer expression, evaluated
at the tissue stage over the muscled values:

```
effective = raw x (1 + 0.15 x tissue(region))     [E factor]
```

Targets only: NeckMass (neck), PecsSize (chest), ArmsDelts (upper
arm), TorsoMass (chest). The registry clamp still applies — a pinned
form stays pinned and the excess surfaces as a range warning, which
is the honest outcome: show-through cannot manufacture slider range
the record doesn't have.

## 7. Worked examples — evaluator output, Nov 12, 2026

All numbers below are the shipped evaluator's actual output on the
stated raw vectors (reproducible via `tests/test_couplings.py` and
the records). Definition values are EFFECTIVE (post-coupling).

### 7.1 The bara grid (shared Muscle 0.80; poles are tissue moves)

| | gatchiri (BB tissue) | gachimuchi (SM tissue) | gachidebu (max tissue) |
|---|---|---|---|
| tissue level | 0.053 | 0.630 | 0.945 |
| tissue abdomen / neck / forearm | .05 / .02 / .01 | .63 / .28 / .16 | .95 / .43 / .24 |
| TrapsValleys raw → eff | 0.85 → **0.765** | 0.40 → **0.346** | 0.40 → **0.322** |
| VLine raw → eff | 0.85 → **0.760** | 0.10 → **0.045** | 0.85 → **0.195** |
| PowerBelly core / drape / tilt | 0 / 1.0 / 0° | .44 / .56 / 1.32° | .68 / .32 / 2.04° |
| NeckMass show-through | — | 0.90 → 0.938 | 0.90 → 0.957 |

Read: at gachidebu the V line is authored at full 0.85 and *still*
submerges to 0.195, while trap valleys at less than half the raw
value keep reading at 0.322 — the attenuation ordering, not slider
discipline, produces the genre's look. The belly's core share
climbs with tissue *because muscle is held* — more belly over the
same core is more power belly, not more drape.

### 7.2 Gachimuchi variant — Sen vs `sen_muscle_bear`

The §4.5 variant, numerically (test-asserted): Muscle effective
identical (0.65 = 0.65); tissue level 0.758 → 0.515; effective
TrapsValleys 0.233 → 0.436 (raw 0.30 → 0.55 **and** attenuation
relief — both halves of the variant's intent, separated); core
share 0.42 → 0.33. The variant is a tissue move, and the evaluator
proves no muscle moved.

### 7.3 Lean contrast — the femboy/otter cell

Low muscle (0.20), low tissue (level 0.131): VLine raw 0.60 →
**0.354**. The muscle gate (G = 0.6) is what does this — tissue
attenuation is nearly 1.0 at this level. A lean build keeps a
soft definition read (separation exists on lean bodies) without
the slider handing it a lifter's carved midsection. Pyn's preset
remains a documented non-application of the bara gates
(BARA_LESSONS §6 D); this cell is about the *mechanism* behaving
at the lean corner, not about re-grading him.

### 7.4 Distribution worked examples (Joe's addition)

**Pear, tissue-driven** (axis −1, muscle 0.45, level 0.637):
thigh tissue **0.714** vs chest tissue **0.210**; PecsCrease raw
0.80 → 0.555 (kept — there is little chest tissue to submerge it);
VLine → 0.257 (waist factor 0.85 still loads the abdomen).

**Pear, muscle-driven** (axis −1, muscle 0.85, level 0.284): same
axis point, different body — thigh tissue 0.319, chest 0.094;
PecsCrease → 0.735; muscle deposition factors (derived):
hips-glutes 1.27, thighs 1.24 vs chest 0.73. The axis steered the
muscle; the tissue stayed comparatively even. **Same distribution
value, two different pears — the vectors decide which kind.**

**Big-chest / inverted triangle** (axis +1, muscle 0.85, level
0.419): chest tissue **0.364** vs thigh tissue **0.234** (chest
factor 1.45 over a *lower* level than the pear's); PecsCrease
0.80 → 0.641; NeckMass 0.90 → 0.937 show-through.

**Apple** (axis +0.45, muscle 0.50, level 0.723): abdomen tissue
saturates at **1.00** (0.723 x 1.00 profile x 1.45 waist factor,
clamped); VLine 0.70 → **0.115**; PowerBelly core share 0.40 — the
belly-dominant cell with a real core under it, distinct from both
the strongman barrel (distribution-neutral, chest keeps tissue
0.41 here vs strongman's 0.38 at similar level) and from a
tissue-only belly, which the advisory would flag.

## 8. Implementation map

| Piece | Where |
|---|---|
| Coupling records (8) | `anthroforge-app/library/couplings/muscle_tissue.*.json` |
| Canonical slider records (20) | `anthroforge-app/library/sliders/` |
| Evaluation | `core/sliders.py`: `CouplingRecord`, `CouplingRegistry`, `evaluate_effective_vector`, `EffectiveVector` |
| Character API | `Character.effective_sliders(registry, couplings)` — raw record untouched |
| Tests | `tests/test_couplings.py` (26): monotonicity, anchors, invariants, dial poles, advisories, distribution, gachimuchi example, wrap audit, broadness invariant |

Derived values the geometry layer consumes: `tissue.level`,
`tissue.<region>`, `distribution.{weight,tissue,muscle}.<macro>`,
`attenuation.<slider>`, `power_belly.{composite, core_share,
drape_share, tilt_deg, index}`, `wrap.factor.{waist, chest}`,
`wrap.ratio.waist`.

## 9. Open problems / honest limits

1. **Geometry-side validation is the next step, deliberately not
   duplicated here.** Whether attenuation-corrected vectors
   actually *read* correctly on hm08 — and whether the curves'
   [E] anchors are right — can only be settled by composing the
   fields on a mesh and grading against the BARA_LESSONS scorecard
   (M4/M5/M10 especially). That build follows the running
   bara-proof; this doc's numbers are vector-layer truths, not
   mesh truths.
2. **Curve anchors are fits, not measurements.** The attenuation
   curves and distribution multipliers are [E] calibrations over
   [S] bands. The first geometry builds should tighten them; the
   records are the single place to edit when they do.
3. **MassSmooth auto-rise is not modelled.** Tissue smoothing
   currently moves only via the dial or explicit values; a
   tissue-driven floor for MassSmooth (analogous to show-through
   in reverse) is plausible but was not fitted to anything — left
   out rather than invented.
4. **Tissue level derivation is a weighted mean of three sliders.**
   A character heavy in Chubby but with no BellyPot reads level
   from what is present (weights renormalise). Explicit
   `body.tissue.level` is the escape hatch presets should use when
   the mean misreads.
5. **Regional muscle modulation is derived-only.** The muscle
   factor set is emitted for the geometry layer; at the vector
   layer `body.muscle` stays one global field, because the HIMBO
   Muscle field's own region split (chest 35 / legs 29 / arms 20)
   is baked into the source field. True regional muscle sliders
   await the decomposition work (SLIDER_ENGINEERING).
6. **Species profiles beyond `lifter` are not authored.** The
   regional-tissue record supports multiple profiles; bear
   (barrel-even) and digitigrade variants are future records, not
   new code.
7. **The amendment's geometry debts (Nov 12).** Two, both stated
   rather than discharged: (a) `body.chest.broadness` ships as
   record + build spec — its component fields are decoded, but the
   composite field and the M8/orthogonality acceptance measurements
   are owed at its first geometry build, the same status NeckMass
   shipped with; (b) the wrap factor's anchors are [E] fits and the
   ring audit (§4) has not yet run on any mesh — the first
   bara-proof/v6 build that audits its angular gains either
   confirms them or tightens them in the coupling record, which is
   the single place they live.

**Licence:** the coupling records, curves and this model are ours
(build tier). The slider records they reference carry their own
provenance — the HIMBO-derived set is study-only / internal.
