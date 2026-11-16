# Morph Craft — Correctives, Combos, In-Pose Sculpting, Orthogonality

*B16 learning deliverable, Nov 12, 2026. Study of professional blendshape practice plus a
measured audit of every morph set we own: the hm08 belly stack (first-proof), the hm08
bara components + definition set (bara-proof), and the shape keys of a shipped BOOTH base
(LESSER MOKURI, MOKURI project — 18 keys on a 3,792-vert body). Audit tooling:
`audit_morphs.py` in this folder; raw numbers in `audit_results.json`. All deltas in
metres on the canonical hm08 frame unless noted.*

---

## 1. What the pros do (study digest)

**Four kinds of morph, four different contracts.** Production practice separates shapes
into: **primitives** (one isolated action — a FACS action unit, one slider's sculpt),
**correctives** (shapes that exist only to fix what other deformations break),
**combos** (pre-composed sums shipped as one target), and **alternative sets**
(visemes/expressions that are *chosen between*, not added). Most morph-set failures come
from treating one kind under another kind's rules.

**Corrective / pose-space deformation (PSD).** The standard film/game answer to skinning
failure (shoulder volume collapse, elbow pinch, mouth-corner tearing): pose the joint,
extract the deformed mesh, sculpt the *correct* anatomy, then compute the corrective as a
pure delta —

> **Delta = Beautiful Mesh − Deformed Mesh** (Blender Studio's Pose Shape Keys write-up
> states it in exactly this algebra; CrazySpace in the Python API is what makes sculpting
> on an already-deformed mesh sound in Blender).

The corrective is driven by the joint pose (a 1-D angle driver for simple joints, an RBF
interpolator over pose space for production rigs — Maya Pose Interpolator, Unreal Pose
Driver), and — the part everyone gets wrong once — a corrective is **only valid against
the exact deformation stack it was extracted from**. Change the weights, the bones, or an
upstream shape and the stored delta no longer lands on the sculpt (Blender Studio calls
this out explicitly; their add-on exists to keep the beautiful mesh re-derivable).

**Combo (combination) shapes.** When two primitives are individually correct but their
*sum* is wrong (jaw-open + lip-pucker pushes lips through each other; smile + cheek-raise
flattens), studios author a combination shape that fires only when both parents are
active, pushing the sum back to believable. A combo is a corrective whose driver is a
product of shape weights instead of a joint angle — same algebra, same extraction rule:
sculpt the *combined* result, subtract the uncorrected sum.

**Sculpting in pose.** Correctives and combos are never sculpted on the neutral base.
You sculpt the posed/combined mesh you actually ship, and the delta extraction removes
everything the existing stack already does. Sculpting a "corrective" against neutral
double-counts whatever the stack already contributes on those verts.

**Keeping sets orthogonal.** The facial-rig literature's rules (Mimic, DebuggerLabs,
MCO): every shape moves *only the area it describes*; shapes must mix predictably;
left/right actions are split into mirror pairs; volume is preserved at full weight. The
mathematical form of "moves only its area" is what §2 measures: small support overlap
*and* small directional correlation on the verts that are shared. Two refinements the
literature states qualitatively and our audit makes quantitative:

- Viseme sets are **not** orthogonal and are not supposed to be — あ/え/お share a jaw
  primitive because they are alternatives, blended with normalised weights, never summed
  raw (see Mokuri audit, §5).
- Linear blending travels in straight lines; anything that should arc (an eyelid over a
  spherical eyeball) gets **in-between shapes** at partial weights. Not a slider problem —
  a path problem, fixed with more targets, not better ones.

**House context.** This doc extends SLIDER_ENGINEERING.md (how we *get* sliders and
decompose fields) with how morphs are *authored and combined* once they exist, and it
gives MUSCLE_TISSUE_MODEL.md's couplings an audit instrument: a coupling is a claim about
how two fields interact, and §2 is how we check the claim on the mesh.

## 2. How the audit measures (reproduce: `python3 audit_morphs.py`)

Per morph, over its full vertex field (support threshold |Δ| > 0.1 mm):

| metric | meaning |
|---|---|
| support | # verts the morph actually moves |
| RMS / max | displacement magnitude over support / peak |
| energy E | Σ|Δ|² — the morph's total "amount of shape" |

Per pair (A, B):

| metric | meaning |
|---|---|
| field cosine ⟨A,B⟩/(‖A‖‖B‖) | the orthogonality number: 0 = independent, ±1 = same/opposite shape |
| support Jaccard / overlap coeff. | how much territory they share (overlap = \|A∩B\| / min(\|A\|,\|B\|)) |
| shared-vertex mean cosine | on verts both move: do they push together (+) or fight (−)? |
| cross-energy ratio 2⟨A,B⟩/(E_A+E_B) | stacking gain: +0.5 means the pair at (1,1) carries ~50% more displacement energy than independent parts would |
| fold test | flipped faces at +1 alone vs (+1,+1): does the combination create folds neither parent has? |

Stack integrity: combined targets are re-summed from their components and the residual
reported — a combo that isn't the sum of its parts is an undocumented edit.

## 3. Audit A — hm08 belly stack (the shipped v5.2 component set)

| morph | class | support | RMS | max |
|---|---|---|---|---|
| protrusion (v1) | primitive | 535 | 64.6 mm | 149.3 mm |
| sag_v3 | coupled term of protrusion | 515 | 27.3 mm | 83.7 mm |
| distribution_v4 | primitive (whole-torso) | 6,104 | 62.1 mm | 86.8 mm |
| limb_v5 | **replacement delta** | 5,755 | 61.9 mm | 87.8 mm |
| terminal_v51 | primitive (micro) | 5,578 | 1.1 mm | 3.2 mm |
| contact_v52 | **corrective** | 1,153 | 5.2 mm | 33.8 mm |

Key pairs:

| pair | cos | overlap | shared-cos | cross | reading |
|---|---|---|---|---|---|
| protrusion × sag_v3 | −0.107 | 1.00 | **−0.43** | −0.08 | sag pulls down where protrusion pushes out — deliberate opposition inside one coupled slider (f(w) term). Fine *because* they are never driven independently. |
| distribution_v4 × limb_v5 | **−0.952** | 0.86 | **−0.89** | **−0.95** | the strongest coupling we own, and it is structural: limb_v5 is a crossfade delta (field − D4 on limb verts), so it *contains the negation* of distribution's limb-region values. It is a replacement, not a layer. |
| distribution_v4 × contact_v52 | −0.009 | 0.39 | **−0.76** | −0.00 | contact pushes against distribution on the inner-thigh verts it shares — textbook corrective behaviour. |
| limb_v5 × contact_v52 | −0.010 | 1.00 | −0.01 | −0.00 | contact lives entirely inside limb territory yet is directionally independent there (midline-local vs radial) — a corrective can share 100% of a support and still not interfere. |
| distribution_v4 × terminal_v51 | +0.124 | 0.61 | +0.06 | +0.00 | broad but energetically negligible (terminal RMS is 1 mm) — overlap without energy is harmless. |

Fold behaviour (13,378 body faces): **no audited pair produced more flips combined than
the sum of its singles**, and every shipped composition is at 0 flips — including the
abuse case (full v5.1 stack + full strongman combo stacked: 0). But the singles are not
all clean: **sag_v3 alone flips 5 faces, distribution_v4 alone flips 2** — both were
repaired *in composition* during their builds, so the stack is safe and the components,
taken alone at +1, are not. Composition-repaired ≠ component-safe; see Rule 6.

## 4. Audit B — hm08 bara components + definition set

| morph | class | support | RMS | max |
|---|---|---|---|---|
| muscle | primitive (mass) | 10,482 | 14.3 mm | 47.8 mm |
| chest.width | primitive (frame) | 5,816 | 5.8 mm | 16.5 mm |
| tissue.strongman | primitive (mass) | 8,296 | 16.6 mm | 95.7 mm |
| neck.mass | primitive (regional) | 1,010 | 26.9 mm | 67.2 mm |
| forearm.mass | primitive (regional) | 3,704 | 4.1 mm | 18.2 mm |
| def.flat_abs / pecs_crease / traps_valleys / back | relief | 194–600 | 1.5–2.9 mm | 3.8–10.0 mm |

Findings:

1. **The three strongman mass components are strongly positively coupled** —
   muscle × chest.width cos **+0.573** (cross +0.32), muscle × tissue **+0.552**
   (cross +0.55), chest.width × tissue **+0.528** (cross +0.29), shared-vertex cosines
   0.71–0.93. All three were derived from overlapping HIMBO recipe territory, so at
   (+1,+1,+1) they deliver up to ~50% more displacement energy than independent parts
   would. This is *why* the strongman build had to solve tissue τ = 0.60 against the
   chest:waist gate instead of shipping tissue at 1.0 — the audit turns that one-off
   solve into a standing rule (Rule 3).
2. **neck.mass is embedded in muscle's field**: field cos only +0.067, but overlap 0.78
   with shared-cos +0.79 — where muscle already grows the yoke, neck.mass grows it the
   same way. Stacking both at full double-counts the yoke; BARA_PROOF's modest neck
   gains at full pin are partly this overlap being spent twice.
3. **The definition set is the most orthogonal thing we own** — |cos| ≤ 0.27 against
   every mass field, supports of a few hundred verts. Its shared-vertex cosines against
   muscle/tissue are strongly *negative* (flat_abs −0.87/−0.67, pecs_crease −0.82/−0.77):
   a crease is carved *against* the surface the mass field pushed out. Definition morphs
   are therefore relief correctives relative to the composed surface — they only mean
   anything evaluated after the mass stack, which is the composition order
   MUSCLE_TISSUE_MODEL.md already mandates. Corollary debt: re-author or re-audit them
   whenever the mass fields change (Rule 9).
4. **Watch pair: neck.mass × def.traps_valleys, cos +0.322** — the highest coupling in
   the definition family. Anatomically sensible (the valley is the gap the yoke mass
   creates), but it is over the watch threshold: any future change to either gets a
   pair re-audit.

**Combos.** The coupling targets (pear / bigchest / gachidebu) measure as what they are:
single targets living entirely inside muscle's footprint (support 10,482 = muscle's),
cos 0.57–0.92 against their parents. Correct as export artefacts; they must never be
decomposed back into sliders (Rule 7). **Stack integrity holds**: v5 = v4 + limb,
v5.1 = v5 + terminal, strongman = muscle + chest + tissue — all with max residual
≤ 0.20 mm, i.e. the .target format's 3-decimal-dm quantisation. No hidden edits anywhere
in the shipped sets.

## 5. Audit C — BOOTH base: LESSER MOKURI shape keys (Body, 3,792 verts, 18 keys)

A shipped, well-regarded VRChat base — useful precisely because its patterns differ from
ours. Keys: 5 visemes （あ い う え お） + ん, `sil`, blink/eye set （目閉じ， 笑顔目右/左，
びっくり, 眠い, 泣きそう, ニコッ), fangs （キバ）, あ2, Dummy00, Dummy01.

1. **あ2 is an exact duplicate of あ** — cos **+1.000**, cross +1.000, identical support
   (286 verts). Pure redundancy in a shipped set: at equal weights it silently doubles
   the "a" viseme. (Probably a spare-slot accident the author never cleaned.)
2. **Visemes share a jaw primitive, by design**: あ×え cos +0.980, え×お +0.906,
   あ×お +0.870, い×う +0.713. A viseme set is an alternative set — driven one-at-a-time
   or with normalised blending — so this is correct craft *under that driver contract*.
   Summed raw at full weight, あ+え would double-count the jaw drop. The contract, not
   the cosine, is what makes it safe.
3. **Expression keys are pre-composed combos**: 眠い × 泣きそう cos +0.841; both embed
   the blink — shared-vertex cosine vs 目閉じ is +0.92…+0.95. The author ships
   expressions as finished combinations rather than primitives-plus-combos. It works
   because VRChat expression menus drive them exclusively; it would fail our additive
   slider contract.
4. **Mirror-split eye keys are perfectly disjoint**: 笑顔目右 (94 verts) × 笑顔目左
   (95) show no measurable coupling — the FACS split pattern our expression system
   already follows with per-side offsets.
5. **Placeholder keys are not empty**: `sil` is an exact zero (the correct silence).
   Dummy00/Dummy01 sit *below* the 0.1 mm audit threshold (support 0) yet are near-exact
   duplicates of *each other* (cos +0.998) and correlate +0.98 with ん's sub-threshold
   field. Epsilon keys are worse than zero keys: invisible to support audits, visible to
   field audits, and they couple to real keys where nobody looks.

## 6. House rules — authoring morphs for AnthroForge

**Classification first.**
1. Every morph is classified in its slider record at authoring time: `primitive`,
   `coupled-term`, `replacement`, `corrective`, `combo`, or `alternative`. The class
   sets the contract below; an unclassified morph does not ship. (Our census today:
   belly stack = 3 primitives + 1 coupled-term + 1 replacement + 1 corrective; bara =
   5 primitives + 4 relief + 3 combos; Mokuri = 6 alternatives + ~9 pre-composed combos
   + 2 epsilon placeholders + 1 duplicate.)

**Orthogonality budgets (independent additive primitives).**
2. Field cosine |cos| ≤ 0.10 target, **0.20 hard cap**; support overlap ≤ 0.50 unless
   shared-vertex cosine ≈ 0 (territory may be shared if directions don't interact —
   limb × contact is the proof). The definition set (≤ 0.27 worst, most ≤ 0.1) is the
   standard; the strongman mass trio (0.53–0.57) is grandfathered under Rule 3, not a
   precedent.
3. Positively coupled components (cos > +0.20) ship with a **solved normalisation
   gain**, the way tissue τ = 0.60 was solved against the chest:waist gate. Raw (+1,+1)
   stacking of coupled fields is a bug, not a default.

**Replacement deltas are not sliders.**
4. A crossfade/replacement component (limb_v5 pattern: new field − current field on its
   territory, cos −0.95 against what it replaces) is applied in fixed stack order at
   coupled weights only. Never expose one as an independent control, never reuse one
   against a different base field than it was extracted from.

**When a corrective is owed.** Author one — do not ship the pair — when any of:
5a. the pair fold test at extreme weights creates flips beyond the sum of the singles;
5b. two *independently driven* morphs share ≥ 100 verts with shared-vertex cosine
    < −0.30 (they fight) or > +0.85 with cross-energy > +0.25 (they double) and no
    solved gain covers it;
5c. surfaces interpenetrate or must touch-and-flatten (contact_v52 is the template:
    parameterised by the tissue level that causes the contact, engaging progressively);
5d. in pose space: skinning error at any joint pose exceeds what weight-painting can
    fix — the shoulder/elbow class. Our 36-bone rig currently ships **zero** pose
    correctives; the first posed-character QA that shows volume collapse opens this
    debt explicitly rather than discovering it per-character.
   Inside a class where opposition is the design (coupled terms like sag, correctives
   like contact), 5b does not apply — the class tag is what distinguishes "fights by
   design" from "fights by accident."

**Sculpt in the deformed state.**
6. Correctives and combos are extracted as **sculpt − evaluated stack**, never sculpted
   on neutral. A corrective records its driver (joint pose, or parent weights for a
   combo) and the stack version it was extracted against; if any upstream field changes,
   the corrective is stale until re-extracted or re-audited. Components repaired in
   composition (sag_v3's 5 solo flips, distribution_v4's 2) carry the standing warning:
   *safe in stack ≠ safe alone* — a component may not be reused solo at +1 until it
   passes a solo fold test.

**Combos are exports, not sources.**
7. A shipped combo must equal the sum of its components within format quantisation
   (≤ 0.25 mm max residual — our three stacks measure ≤ 0.20 mm). Combos are never
   decomposed back into sliders, and never edited directly; fix the components and
   re-sum.

**Alternative sets play by different rules.**
8. Viseme/expression alternatives are exempt from Rule 2 and bound by the driver
   contract instead: exclusive or normalised blending, documented in the set's record.
   Nothing from an alternative set may be summed raw with a sibling. Pre-composed
   expression combos (the Mokuri pattern) are acceptable *only* inside such a set.

**Hygiene.**
9. Relief/definition morphs are authored against the composed surface and re-audited
   when mass fields change (their negative shared-cos is the signature of a carve; a
   carve registered to a surface that moved is a defect).
10. Duplicates are defects: cos ≥ 0.999 against an existing key (あ2 ≡ あ） blocks
    shipping. Placeholder keys are exactly zero or carry a documented purpose;
    epsilon deltas (Dummy00/01 pattern) are banned — they evade support audits and
    couple invisibly.
11. Mirror-split any control a user can drive asymmetrically (expression system's
    per-side offsets already comply); a combined L+R key plus separate L/R keys may
    not coexist without a driver rule saying which wins.
12. Motion that arcs gets in-betweens, not stronger endpoints (eyelid-over-eyeball
    class): if the linear path visibly cuts the corner, author the mid target.

**The gate.**
13. A new or changed morph lands with, in its record: class tag, support/energy stats,
    its three largest pair couplings from this audit, solo fold count, and in-stack
    fold count. `audit_morphs.py` is the measuring tool; extend its sets when new
    morph families land.

## 7. Open debts this audit leaves on the books

- sag_v3 (5) and distribution_v4 (2) flip faces solo at +1 — safe only inside their
  stacks (Rule 6 warning applies to any reuse).
- Strongman mass trio needs its solved gains recorded *in the slider records*
  (τ = 0.60 currently lives in BARA_PROOF.md, not in the records).
- neck.mass × muscle yoke double-count (§4.2) — a gain or a support trim is owed
  before NeckMass ships as a user slider.
- Zero pose-space correctives exist for the 36-bone rig (Rule 5d) — first posed QA
  will size this debt.
- The coupling combos were never fold-gated at their own design point: bigchest flips
  1 face and gachidebu 3 faces at 1.0× (§8, Door 1) — repair owed before either is
  used as a hyper parent (Rule H4).
- If any BOOTH/VRChat set is ever imported as a source: strip duplicate keys (あ2
  pattern), zero or document placeholders, and re-tag pre-composed expressions as
  combos before they meet our additive contract.

## 8. Hyper — behaviour at 2–4× and the rules that keep it usable

*Added Nov 12, 2026 at Joe's direction ("make sure the models can handle hyper").
Measured by `audit_hyper.py`; numbers in `audit_hyper_results.json`. Background pattern
from the body-diversity hunt (Thread 40): production hyper work splits into two channels
— **girth/shape as blendshapes, length/overall size as bone (transform) scale** — and
past the hyper threshold artists stop extrapolating and swap in different geometry
(Mal-0's Hyper body is a different mesh; Nexa'vali ships anatomy as separate add-on
objects). The measurements below show why both habits exist.*

**What does *not* change with scale:** field cosine. For linear morphs every term —
self-energy and cross-energy alike — grows with the product of the weights, so the
orthogonality picture in §§3–4 is identical at 0.5× and at 4×. Hyper interference is
not a correlation problem. It is a **geometry-validity problem**, and it arrives through
three doors:

**Door 1 — fold onset.** Our fields were attenuation-repaired *at +1*, which puts the
authored endpoint close to the fold boundary by construction. Measured flipped faces
(of 13,378 body faces):

| field | 1× | 1.5× | 2× | 3× | 4× | onset |
|---|---|---|---|---|---|---|
| protrusion | 0 | 47 | 104 | 151 | 164 | ~1.0–1.5× |
| belly stack v5.1 | 0 | 26 | 75 | 173 | 243 | ~1.0–1.5× |
| belly stack + contact | 0 | 26 | 75 | 179 | 264 | ~1.0–1.5× |
| muscle | 0 | 4 | 13 | 52 | 93 | ~1.0–1.5× |
| tissue.strongman | 0 | 0 | 0 | 2 | 18 | **3×** |
| strongman combo | 0 | 27 | 49 | 104 | 166 | ~1.0–1.5× |
| combo pear | 0 | 6 | 27 | 67 | 116 | ~1.0–1.5× |
| combo bigchest | **1** | 47 | 79 | 145 | 200 | **at 1×** |
| combo gachidebu | **3** | 111 | 211 | 385 | 500 | **at 1×** |
| belly + strongman (everything) | 0 | 67 | 144 | 266 | 427 | ~1.0–1.5× |

Two catches inside the table. First, **bigchest and gachidebu already flip faces at
their authored 1.0** (1 and 3 faces) — the coupling combos were composed numerically
but never fold-gated at their own design point; they ship with small defects before
hyper even starts, and gachidebu then grows fastest of anything audited (500 faces,
3.7% of the body, at 4×). Second, tissue.strongman is the outlier: a broad smooth field
stays clean to 2× and onsets at 3× — smoothness, not smallness, is what buys hyper
headroom (its max displacement, 95.7 mm, is the second-largest we own).

**Door 2 — interpenetration.** The belly stack holds the inner thighs apart at 1×
(the v5 gap, closed by the contact corrective). Past 1× the fields push through each
other: verts across the midline number 0 at 1×, 19 at 1.5×, 34 at 2×, 58 at 3×, 69 at
4×. And the contact corrective itself becomes a defect source outside its solved
range — from 3× up, stack+contact flips *more* faces than the stack alone (179 vs 173;
264 vs 243). **A corrective has a validity envelope**, exactly like the PSD rule in §1:
solved against one configuration, wrong outside it.

**Door 3 — relief submersion.** Definition relief is fixed-amplitude (flat_abs RMS
1.74 mm) while mass scales linearly, so the relief-to-mass ratio at the abs verts is
0.066 at tissue 0.6×, 0.040 at 1×, and halves with every doubling — 0.010 at 4×.
The evaluator's attenuation curve (§4, finding 3) is this same arithmetic at the vector
layer. At hyper values, authored definition does not fade gracefully; it is simply
*under* the surface, and no weight on the existing relief target brings it back.

**Hyper house rules.**

H1. **Fold onset is the range.** Every family's slider maximum is set from its
    measured onset, not from convention: tissue-class smooth fields may run to ~2×;
    the belly stack and mass components are 1× families today. The onset measurement
    is part of the Rule 13 gate for any morph claiming a range > 1.
H2. **Hyper is segmented, never extrapolated.** Past a family's onset, a separate
    hyper-segment morph — authored at its own design point, fold-repaired at that
    point, crossfaded like limb_v5's replacement — takes over. The slider becomes
    piecewise (0–1 base segment, 1–2 hyper segment, …). This is the morph-space form
    of the artists' mesh-swap: the 2–4× range gets *sculpted* geometry, not the 1×
    field stretched. Atomic Muscle's Penis Length shipping to 1.5 with state-variant
    morphs is the same instinct at smaller range.
H3. **Length goes to bone scale; girth stays in morphs.** Per-part length and overall
    size are transform (bone-scale) records, which cannot fold and do not fight the
    morph stack; morphs own cross-section and surface. A hyper *length* request routed
    into a morph target is a category error — it buys displacement the mesh must pay
    for in folds (protrusion's 149 mm max is ~600 mm at 4×) for something a scale does
    for free.
H4. **Combos are re-solved per segment.** A solved gain (τ = 0.60) is local to the
    segment it was solved in. Hyper combos are separate solves with their own fold
    gate — and the gate applies at 1× too: bigchest (1 flip) and gachidebu (3 flips)
    are defects to repair, recorded in §7's spirit, before either is used as a hyper
    parent.
H5. **Correctives carry envelopes.** A corrective record states the weight range it
    was solved over; the evaluator clamps or re-engages it outside that range rather
    than extrapolating it (contact ≥ 3× is the measured failure). Hyper segments that
    change contact geometry owe a re-extracted contact corrective per segment
    (Rule 6 algebra, applied per segment).
H6. **Adjacent-mass hyper is contact-capped.** Where masses meet (inner thighs,
    arm-to-torso, belly-to-thigh), the segment ceiling is set by the contact solve,
    not the fold solve — interpenetration (Door 2) onsets before folds do.
H7. **Definition is re-authored per segment.** Relief amplitude belongs to the
    segment's surface; a hyper segment that wants visible definition ships its own
    relief at its own amplitude. Expecting the 1× relief to survive is expecting a
    1.7 mm carve to read through 175 mm of tissue.
H8. **Hyper QA is three numbers**: fold onset, midline/penetration count at range
    max, relief-to-mass ratio at range max. No family exposes a hyper range in the
    UI until all three are in its record.

*Sources for §1: Blender Studio, "Pose Shape Keys Add-on" (studio.blender.org);
"Pose Space Deformation for Muscle Bulging in Games" (salivity.github.io); Autodesk
Maya Pose Interpolator docs; "Blend Shapes Explained" (mimicproductions.com); "Facial
Animation Explained" (debuggerlabs.com); MCO blend-shapes guide. Measurements: this
folder's `audit_results.json`, produced by `audit_morphs.py` from the shipped
first-proof/bara-proof targets and a Blender dump of Lesser_Mokuri.blend.*
