# HYPER RANGES — the hyper regime for AnthroForge sliders

*Nov 12, 2026. Joe's direction: "make sure the models can handle hyper."
Third run of this pass (two prior runs died on infrastructure timeouts;
this one builds on their landed scaffolding — `scripts/hyper_common.py`,
`scripts/fix_coupling_defects.py`, preserved originals in `work/originals/`).
Measured input: B16's hyper audit, `model-craft/b16-morphs/MORPH_CRAFT.md`
§8 + `audit_hyper_results.json`. House rules H1–H8 (MORPH_CRAFT §8) are
adopted wholesale; this document turns them into per-family design,
app-library schema changes, two shipped-defect repairs, and one gated
hyper proof build.*

---

## 1. The regime in one paragraph

Hyper is not a bigger clamp. Every slider family gets a **measured fold
onset**; the shipped range ends at or below it (H1). Past onset, the
slider becomes **piecewise**: a separately authored **hyper segment** —
sculpted/repaired at its own design point and crossfaded in — takes over
(H2). **Length and overall size leave the morph stack entirely** and ride
bone scale, which cannot fold (H3). Combos are re-solved per segment
(H4); correctives carry **validity envelopes** and are re-extracted per
segment when contact geometry changes (H5); where masses meet, the
**contact solve sets the ceiling**, not the fold solve (H6); definition
relief is **re-authored per segment** at the segment's amplitude (H7).
No family exposes a hyper range until its record carries the three QA
numbers: fold onset, penetration count at range max, relief-to-mass
ratio at range max (H8).

## 2. Failure map (measured, B16 audit + this pass)

Flipped faces of 13,378 body faces, fields scaled from their shipped
`.target` deltas (B16, `audit_hyper_results.json`):

| family / stack | 1× | 1.5× | 2× | 3× | 4× | onset | regime (§3) |
|---|---|---|---|---|---|---|---|
| belly protrusion (v1 core) | 0 | 47 | 104 | 151 | 164 | ~1.0–1.5× | segmented |
| belly stack v5.1 | 0 | 26 | 75 | 173 | 243 | ~1.0–1.5× | segmented — **proof §5** |
| belly stack + contact v5.2 | 0 | 26 | 75 | 179 | 264 | corrective inverts ≥3× | envelope [0, ~2] |
| muscle | 0 | 4 | 13 | 52 | 93 | ~1.0–1.5× | segmented (unauthored) |
| tissue.strongman | 0 | 0 | 0 | 2 | 18 | **3×** | **linear to 2×** |
| strongman combo | 0 | 27 | 49 | 104 | 166 | ~1.0–1.5× | re-solve per segment |
| combo pear | 0 | 6 | 27 | 67 | 116 | ~1.0–1.5× | re-solve per segment |
| combo bigchest | **1** | 47 | 79 | 145 | 200 | **at 1× (defect)** | **repaired §4** |
| combo gachidebu | **3** | 111 | 211 | 385 | 500 | **at 1× (defect)** | **repaired §4** |
| belly + strongman (all) | 0 | 67 | 144 | 266 | 427 | ~1.0–1.5× | per-segment solves |

Interpenetration (inner-thigh band, verts across midline), measured by
B16 on the **belly stack + contact corrective scaled together**:
**0 at 1× → 19 at 1.5× → 34 at 2× → 58 at 3× → 69 at 4×** (reproduced
this pass: 0 / 23 / 34 / 56 / 72 — the 2× anchor matches exactly; small
off-anchor diffs are band-definition dust). The attribution matters:
the v5.1 belly field *alone* never crosses on hm08 (43.5 mm min gap
even at naive 2×) — **the extrapolated contact corrective is the
penetration source**. Penetration onsets *before* folds do, and it
arrives through the corrective channel — at hyper the contact solve,
not the fold solve, is the binding constraint (H6), and correctives
are guilty until envelope-proven (H5).

Relief submersion (flat_abs relief RMS 1.74 mm against tissue mass at
the abs verts): ratio **0.066 at tissue 0.6× → 0.040 at 1× → 0.020 at
2× → 0.013 at 3× → 0.010 at 4×** — halves per doubling. The 1× relief
cannot be re-weighted back into visibility at hyper (H7).

Smoothness buys headroom: tissue.strongman (max displacement 95.7 mm,
second-largest field we own) is the only family clean at 2×, because it
is broad and smooth. Fold onset tracks field *curvature*, not size.

## 3. Per-family regime design

### 3.1 Adiposity — `body.belly.protrusion` (v5.1 system)
- **Channel split:** girth/volume stays morph; overall body size is NOT
  this slider's job (bone scale / character scale).
- **Segments:** base 0→1 = shipped v5.1 stack (fold-gated, 0 flips).
  **Hyper segment 1→2 = authored this pass (§5):** the 2× state solved
  directly — contact-capped, attenuation-repaired at the 2× design
  point in quantised space — shipped as the *incremental* delta over
  the 1× state, so the slider is piecewise-linear in vertex space and
  the crossfade is exact by construction.
- **Ceiling 2×.** A 2→3 segment is future work and must be authored the
  same way (solve at 3×, repair at 3×); extrapolating segment 2 is
  forbidden by H2 — the uncapped stack is at 173 flips by 3×.
- **Negative pole:** unchanged known debit — the source morph is
  one-sided, −1 folds (~140 faces inherited since v1). Hyper work does
  not touch it; the fix remains a separately authored decrease target.
- **Contact:** the v5.2 contact corrective's envelope is **[0, 1]**; the
  hyper segment carries its **own re-solved contact keys** (§5), per
  H5. B16 measured the v5.2 corrective *adding* flips from 3× — outside
  its envelope the evaluator must not extrapolate it. The proof found
  the sharper version: even *clamped at its envelope edge* and composed
  with the solved 2× belly, v52 leaves 7 crossings at 0.34 mm gap —
  envelopes bound a corrective's own weight, but composition still
  re-solves at each segment design point.

### 3.2 Tissue — `body.tissue.strongman` and the tissue vector
- **Linear extension to 2×, no segment needed** (measured 0 flips at
  2×, onset 3×). Ship `range.max = 2.0` with the H8 numbers recorded;
  hold a 0.5 safety margin under onset as house policy.
- A 2→3 segment, if ever wanted, is authored at 3× (2 flips to repair —
  cheap), but tissue at 3× on top of a 1× belly is a *combo* question
  (§3.5), not a tissue question.
- The tissue **wrap factor** (muscle_tissue.tissue_wrap coupling) is
  range-independent — it is a ratio, evaluated from front tissue — but
  its anchors were fitted at ≤1× front tissue; at tissue 2× the factor
  saturates at 1.00 (ring closed), which is the correct asymptote.

### 3.3 Muscle — `body.muscle`, neck/forearm fields
- **1× family today** (onset ~1.0–1.5×; 4 flips already at 1.5×).
  Hyper muscle is an **authoring** task, not a range change: a hyper
  segment sculpted from the bara study's artist bands (which already
  sit above athlete bands) with the yoke-first construction, repaired
  at its design point. Not built in this pass — logged, §7.
- **Frame widths hand off to bone scale at hyper (H3):**
  `body.chest.broadness` past +1 continues as clavicle/delt bone scale
  (recorded as a `bone_scale` channel, §6) rather than stretching the
  ShoulderInc morph field, whose fold behaviour at 2× is unmeasured
  and whose job is *shape*, not span.

### 3.4 Definition — relief family (`flat_abs`, `traps_valleys`, `pecs_crease`, `back`)
- **Per-segment re-authoring (H7).** Each segment's record carries its
  own `relief_amplitude_mm`, set so relief-to-mass at the segment's
  design point matches the 1× design intent (~0.04 at abs). At the 2×
  belly segment that means roughly **double** the 1× amplitude
  (≈3.5 mm RMS) *if* definition is wanted there at all — under the
  composition model, high tissue submerges definition anyway
  (definition_attenuation coupling), so the honest default at hyper
  tissue is: relief authored, evaluator attenuates, nothing faked.
- Relief fields themselves are small-amplitude normal-direction fields;
  they do not fold onset-limit the stack (their failure mode is
  invisibility, Door 3, not folds).

### 3.5 Combos — pear / bigchest / gachidebu / strongman stacks
- **Re-solved per segment (H4).** The τ = 0.60 tissue gain was solved
  at the 1× design point; any hyper combo re-solves its gains at the
  segment design point and fold-gates the *composed* state, not the
  parts. Composing individually-gated segments does **not** inherit
  their gates (the everything-stack onsets at ~1.0–1.5× even though
  tissue alone reaches 3×).
- The 1× defects in bigchest/gachidebu are repaired in §4 — a combo
  with flips at its own design point may not parent a hyper segment.

### 3.6 Genital / per-part channels (from the HIMBO + Atomic Muscle decodes)
- **Length → bone scale (H3), always.** AM's own Penis Length morph
  (to 1.5) is the small-range exception that proves the rule: at hyper
  multiples a length morph pays ~600 mm of displacement for what a
  scale does free, and pays it in folds. Our records: length channels
  are `bone_scale` records over the part's bone chain (per-shaft for
  multi-shaft parts — the Kaleaon quad-shaft set takes four
  independent length scales + a shared girth morph, per the
  two-channel rule).
- **Girth stays morph**, segmented like adiposity: base segment to
  measured onset, hyper segment authored past it. AM's two-sided
  Shaft Width (−1..1) and >100% headroom are UI precedents, not range
  evidence — ranges still come from onset measurement (H1).

### 3.7 Ears / tails / appendage parts
- Length-class appendages (ear length, tail length) follow §3.6:
  bone scale for length, morphs for shape/girth. Ear *size* presets
  like fennec +100 are shape morphs and stay in the morph stack with
  their own onset measurement owed before any hyper exposure.

## 4. Shipped-defect repair — bigchest (1 face) + gachidebu (3 faces) at 1.0×

**Status: REPAIRED Nov 12, 2026** (`scripts/fix_coupling_defects.py`,
results in `work/defect_fix.json`; repaired files written back to
`bara-proof/body.coupling.{bigchest,gachidebu}.target` with provenance
notes in their headers). Method: the coupling-validation build gated
its *in-memory float* deltas at 0 flips on both bases (gachidebu raw
min_dot 0.00061, bigchest 0.00177) — the builds sat ON the fold
boundary and the `.target` format's 0.1 mm quantisation pushed them
over. Repair = attenuation **in quantised space** (the exact numbers
that ship), gated on both bases to 0 flips **and** a margin floor
(min normalised dot ≥ 0.01), so the fix has headroom instead of landing
back on the boundary. Originals preserved in `work/originals/`
(md5-verified identical to the shipped files before repair).

| combo | as-shipped flips (raw / macro) | flipped faces (centroid, height frac) | repair | after: flips, min_dot (raw / macro) | deviation vs original |
|---|---|---|---|---|---|
| bigchest | 1 / 0 (min_dot −0.0239) | F4952 (−0.005, +0.057, +0.670 m, h 0.892) | 2 rounds | **0**, 0.0764 / 0.0542 | max 1.64 mm, RMS 0.038 mm, 34 verts |
| gachidebu | 3 / 3 (min_dot −0.0239 / −0.916) | F489 (−0.018, +0.055, +0.661, h 0.887), F4952 (as above), F7215 (+0.031, −0.021, +0.675, h 0.895) | 13 rounds | **0**, 0.0233 / 0.0189 | max 3.06 mm, RMS 0.085 mm, 87 verts |

Both defects live in one cluster — the upper-chest/shoulder field at
~89% body height; face 4952 flips in both combos. The repair cost is
invisible (≤3.06 mm worst-vertex, sub-0.1 mm RMS). Reload-from-disk
verification passes on both bases. Note the repaired combos still fold
at 1.5× (45 / 111 faces) — expected: they are 1× families until a
per-segment re-solve exists (H4, §3.5); the repair buys a clean design
point, not a range extension.

## 5. Hyper proof build — belly stack at 2× (segment-authored)

**Design point: slider 2.0 on `body.belly.protrusion`, hm08, both
bases, all gates run on the shipped quantised files recomposed under
the §6 evaluator semantics.** Scripts: `scripts/build_hyper_proof.py`,
`scripts/verify_proof_contact.py`, `scripts/solve_midpoint.py`,
`scripts/final_gate.py`, `scripts/render_proof.py`. Numbers:
`work/proof_qa.json`, `work/proof_contact.json`,
`work/proof_midpoint.json`, `work/final_gate.json`.

**Method (H2, literally):** the 2× state was *solved*, not scaled.
Naive 2× (2 × the v5.1 delta) measures **75 flipped faces on both
bases**. Quantised attenuation repair at the 2× design point (30
rounds) brings it to 0 flips with margin (min_dot 0.0215 raw / 0.0214
macro). The solve is honest about its cost: deviation vs naive 2× is
max 279.8 mm at the single hottest drape/groin vert, RMS 17.6 mm over
the support, 616 verts touched — the repair concentrates exactly where
the extrapolated field was violent. At the canonical navel vert
(4075): 1× = 111.4 mm forward / 69.9 mm down; solved 2× = **162.0 mm
forward / 101.8 mm down** (naive would claim 222.8 / 139.8). The
segment is a valid sculpt at its design point, not a doubled one —
and the torso ring still grows all the way around: navel-height slice
perimeter **0.68 m base → 1.06 m at 1.0 → 1.37 m at 2.0**, flanks and
back moving with the front (the tissue wrap survives hyper).

**Contact (H5/H6) — the instructive half.** The belly field alone
never binds the cap on this base (43.5 mm gap at naive 2×; cap engaged
0 verts). The *policy composition* — solved belly 2× + v52 contact
clamped at its envelope edge 1.0 — still crossed **7 verts at 0.34 mm
gap**: the corrective was solved against the 1× thigh gap, and the 2×
belly narrows the world it lands in. Re-solving the cap at the 2×
composition (13 verts capped, no fold repair needed) gives
`contact_hyper2`: **0 crossings, 5.9 mm min gap**. A first mid-segment
composition that double-applied the v52 field measured 5 folds /
23 crossings — the bookkeeping failure mode H5 exists to prevent —
so the segment ships **total-field contact keys** {1.0: v52,
1.5: hyper15 (solved directly at the midpoint: 8 verts capped),
2.0: hyper2} and the evaluator piecewise-interpolates *between solved
keys*. Quarter points then gate clean from the shipped files:

| slider | folds raw / macro | crossings | min thigh gap |
|---|---|---|---|
| 1.0 | 0 / 0 | 0 | 7.32 mm |
| 1.25 | 0 / 0 | 0 | 6.62 mm |
| 1.5 | 0 / 0 | 0 | 5.91 mm |
| 1.75 | 0 / 0 | 0 | 5.93 mm |
| 2.0 | 0 / 0 | **0** | **5.90 mm** |

The gap narrows smoothly and monotonically as the contact patch
engages — progressive onset working as designed (the v5.2 pattern,
re-solved per segment). **0 unresolved interpenetration at the stated
multiple: met**, with the cap floor (4 mm) cleared at every sampled
state.

**Shipped artifacts** (in `hyper/`): `body.belly.protrusion.hyper2.target`
(segment increment; `body.belly.hyper2_full.target` = the composed
design point, for QA), `body.belly.protrusion_contact_hyper15.target`,
`body.belly.protrusion_contact_hyper2.target`,
`body.belly.protrusion.hyper_record.json` (the §6 schema, populated),
renders `renders/hyper2_states.png` (front/profile at 0 / 1.0 / 2.0),
`renders/hyper2_slice.png` (navel-height ring), `renders/hyper2_thigh_contact.png`.

**H8 triple for this family:** fold onset (base segment) ~1.5× ·
penetrations at range max **0** · relief-to-mass at range max 0.020
(B16, tissue 2×) — definition at hyper rides the attenuation coupling
as designed; a hyper relief re-authoring (§3.4) remains optional work,
not a gate failure.

## 6. Schema changes for the app library format

Current records carry a flat `range {min, max, default, safe_max?,
endpoint_anchor}`. Hyper needs five additions (all backwards-compatible:
a record without them is a 1× record, which is exactly today's truth).

```jsonc
"range": {
  "min": -1, "max": 2.0, "default": 0,
  "max_basis": "fold_onset_measured",        // H1: max derives from onset
  "segments": [                              // H2: piecewise, not extrapolated
    {"from": 0.0, "to": 1.0, "target": "body.belly.protrusion_v5.1.target",
     "authored_at": 1.0, "fold_onset": 1.5},
    {"from": 1.0, "to": 2.0, "target": "body.belly.protrusion.hyper2.target",
     "authored_at": 2.0, "fold_onset": null,   // segment endpoint IS the design point
     "incremental_over": "body.belly.protrusion_v5.1.target"}
  ]
},
"channels": {                                // H3: what the slider drives
  "girth": "morph", "length": "bone_scale"
},
"bone_scale": {                              // present when a channel is bone_scale
  "bones": ["clavicle.L", "clavicle.R"], "axis": "span",
  "max_scale": 1.35, "engages_above": 1.0    // morph to 1, scale past it
},
"correctives": [                             // H5: envelopes, not vibes
  {"id": "contact_v52", "target": "body.belly.protrusion_contact_v52.target",
   "envelope": {"slider": "body.belly.protrusion", "min": 0.0, "max": 1.0},
   "outside_envelope": "clamp",             // clamp | reengage | disable
   "superseded_in_segment": {"from": 1.0, "by": "contact_hyper2"}}
],
"contact": {                                 // H6: the ceiling's source
  "policy": "capped", "zones": ["inner_thigh"],
  "min_gap_m": 0.004, "ceiling_set_by": "contact_solve"
},
"hyper_qa": {                                // H8: all three, or no hyper range in UI
  "fold_onset": 1.5,
  "penetrations_at_max": 0,
  "relief_to_mass_at_max": 0.02
}
```

Evaluator consequences (for the app core):
- Segment evaluation is `Σ segment_deltas` with each segment's weight
  clamped to its own span — extrapolation past the last segment is a
  hard clamp, never a scaled delta.
- A corrective outside its envelope is clamped to the envelope edge
  (or re-engaged, if the record says a per-segment replacement exists);
  the evaluator reports the clamp as a warning, same style as existing
  safe-band warnings.
- `hyper_qa` missing ⇒ UI caps the slider at the last gated segment.
- **Corrective keys are TOTAL fields** (proof §5): a segment contact
  key states the whole contact field at its slider value and *replaces*
  the base corrective's contribution there; the evaluator interpolates
  between keys, never stacks them. The first composition drafted for
  the proof stacked them and manufactured 5 folds / 23 crossings out
  of bookkeeping alone — the schema now makes that state
  unrepresentable.

A worked example record ships with this pass:
`hyper/body.belly.protrusion.hyper_record.json`.

## 7. Open items / not built here

- Hyper muscle segment (§3.3) — authoring task, needs the bara artist
  bands sculpted at a 2× design point; neck field vocabulary ceiling
  (BARA_PROOF M2/M3 misses) binds here too.
- Belly segment 2→3 (§3.1) — same method as §5 when wanted.
- Ear/tail hyper onsets unmeasured (§3.7) — no hyper exposure until
  measured (H8).
- Belly negative-pole decrease target — pre-existing debit, unchanged.
- Pose-space correctives for the 36-bone rig at hyper — unscoped;
  first posed QA sizes it (MORPH_CRAFT §7 carries the 1× version).

## 8. Provenance & method notes

- All fold gates run on **both** bases (raw base.obj frame + MPFB macro
  frame, range-aligned) in the **quantised** `.target` space — the
  §4 defects exist precisely because a float-space gate was trusted.
  New house rule, worth promoting: **ship gates run on the shipped
  numbers.**
- Frames/loaders follow B16's `audit_hyper.py` exactly (`hyper_common.py`)
  so every number here compares with MORPH_CRAFT §8.
- Study-tier provenance throughout: composed displacement fields only,
  never source assets.
