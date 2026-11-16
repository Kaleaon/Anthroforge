# B11 — Hands & Feet: Anthro Paw-Hand + Digitigrade Paw-Foot

**Status:** Two class-A parts built and QA'd, Nov 12, 2026 (model-craft
wave B11). This document was completed in a finisher pass — the build
agent died on a transport timeout after producing parts, records,
renders and QA, but before writing the doc its own part records cite
(§6, §7). Everything below is grounded in `work/build_hands_feet.py`,
the two `.part.json` records, the build/render logs, and an independent
qa-gauntlet re-run.

**Provenance:** fully procedural, original geometry authored for
AnthroForge — no donor mesh, no library geometry copied. Anatomy per
WikiVet canine phalanges (digit counts, dewclaw as digit I, carpal
"stopper" pad) adapted to an anthro hand.

**Files:**

| | |
|---|---|
| Build script | `work/build_hands_feet.py` (Blender 5.2.3, `blender -b --python build_hands_feet.py`) |
| Render script | `work/render_parts.py` |
| Source blend | `parts/b11_hands_feet.blend` (both parts + both fit stubs) |
| Parts | `parts/paw_hand_r.glb` + `.part.json` · `parts/paw_foot_digi_r.glb` + `.part.json` |
| QA | `work/qa/` (gauntlet JSON per part + `_summary.json`) |
| Renders | `renders/` — 6 views, §8 |

---

## 1. Parts at a glance

| | `paw_hand_r` | `paw_foot_digi_r` |
|---|---|---|
| Name | Anthro paw-hand (right) | Digitigrade paw-foot (right) |
| Socket | `arm.R` (distal sub-part — see §7) | `leg.digi.R` (PARTS_STANDARD #16) |
| Anchor bone | `Wrist_R` | `Ankle_R` |
| Class / tier / size | A / 3 / M | A / 3 / M |
| Meshes | `paw_hand_main`, `paw_hand_pads`, `paw_hand_claws` | `paw_foot_main`, `paw_foot_pads`, `paw_foot_claws` |
| Verts (GLB) | 1,270 | 1,092 |
| Tris (GLB, triangulated) | 2,456 | 2,108 |
| Joints | 16 (1 core + 15 module) | 11 (1 core + 10 module) |
| Morphs | 0 | 0 |
| **Cost points** | **18** | **13** |
| Extent | 0.205 m | 0.266 m |
| Fit verdict | partial (0.721, ships with note) | fitted (0.790) |
| Plans | biped, taur, naga (excl. feral) | biped (+ feral/taur hind-leg instances) |

Count note: `build_stats.json` records Blender *polygon* counts
(hand 1,440 / foot 1,243); the part records and this doc carry the
GLB *triangle* counts after triangulation. Both are correct in their
own terms.

---

## 2. Construction method

Everything is built from three procedural primitives in
`work/build_hands_feet.py`:

- **Loft** — ring sections (centre, x/z radii, tangent) swept along a
  path, 8–14 verts per ring, capped at both ends. Palm, fingers,
  thumb, metatarsus, toes, dewclaw and both fit stubs are lofts.
- **Ellipsoid with true pole vertices** — pads, thenar mound, hock
  knob. The pole construction is deliberate: a naive lathe puts `seg`
  coincident verts at each pole and produces a fan of degenerate
  triangles; QA pass 1 caught 150–200 per part from exactly this, and
  the shipped parts have **0 degenerate tris** (§8).
- **Cone** — claws: base ring + mid ring + tip point, with the mid
  ring offset and the tip dropped to fake the claw's downward bend.

A `MeshBuilder` accumulates sub-forms into one mesh while carrying a
per-vertex **weight function** and a per-vertex **fit flag** (internal
overlap blobs — thenar mound, calcaneal knob — are flagged out of the
fit-score surface, §6). Skinning is authored (`own-weights`), max
**2 influences** per vertex; across a joint the blend is 0.85 / 0.15
toward the distal bone.

Three flat Principled materials (Coat / Pad / Claw). No textures.

The script comments preserve a genuine two-pass iteration history;
pass-1 findings fixed in the shipped build:

- wrist ring made near-oval — a flat wrist section cannot seat into
  a forearm (§6);
- pads sunk ~1.2 mm deeper — pass 1 read as stuck-on discs (see §9,
  debit 2: improved, not solved);
- thumb pad moved off the fingertip to the distal segment's
  underside — tip placement read as a dark cap over the claw;
- carpal pad moved outward — pass 1 had it fully buried in the wrist;
- toe radii ×1.15 — pass 1 toes read spindly against the metatarsus.

---

## 3. `paw_hand_r` — the paw hand

**Frame:** right hand, medial = −X; fingers +Y, palm −Z; wrist at
y = 0. Total length 0.205 m.

**Palm.** A 7-ring loft: wrist section 0.030 × 0.0165 m (near-oval,
≈ 60 × 33 mm — a real wrist proportion, and the shape a forearm
sleeve can receive), swelling to 0.043 m wide at mid-palm, then
narrowing to a final **knuckle-brow** ring that seats the finger
bases deeper into the palm mass. The **thenar mound** (thumb muscle)
is a separate ellipsoid merged into the palmar-lateral palm; most of
it is internal overlap, so it is excluded from the fit surface.

**Digits — five, canine-pattern.** Fingers II–V are 3-segment lofts
(proximal / middle / distal phalanges), each segment slightly
flattened (rz = 0.92 r) and tapered (0.88× per joint, 0.55× at the
tip). Segment lengths (proximal + middle + distal):

| Digit | Lengths (mm) | Total | Fan |
|---|---|---|---|
| Index | 42 + 28 + 21 | 91 mm | +4° |
| Middle | 46 + 31 + 22 | 99 mm | 0° |
| Ring | 43 + 29 + 21 | 93 mm | −3° |
| Pinky | 34 + 23 + 18 | 75 mm | −7° |

Bind pose carries a relaxed curl of 7° / 11° / 14° added at the
three joints, flexing toward the palm. **Thumb:** metacarpal + two
phalanges (bones `Thumb1–3_R`), based at (−0.036, 0.032, −0.002)
with direction (−0.45, 0.78, −0.30) — out, forward and palmar, i.e.
genuinely **opposed**. Function block: power + precision grip.

**Pads.** Canine arrangement, all flattened ellipsoids (crown
3.0–4.1 mm) sunk into the palmar surface:

- **Metacarpal ("heart") pad** — two lobes + a distal apex across
  the palm at the MCP line;
- **Digital pads ×4 + thumb pad** — underside of each distal
  segment (not on the tip — see §2);
- **Carpal ("stopper") pad** — proximal palmar wrist, offset
  laterally, as in the dog.

**Claws.** Non-retractile, blunt (canine pattern): 14–16 mm cones,
base embedded at the dorsal-distal fingertip, angled forward-down.

---

## 4. `paw_foot_digi_r` — the digitigrade foot

**Plantigrade vs digitigrade — scope.** PARTS_STANDARD #16 rules
that plantigrade↔digitigrade is a *leg-style module swap* inside
plan.biped, not a plan switch: the base leg carries the plantigrade
foot, and `leg.digi` is the module that replaces it. B11's brief was
the module — **no plantigrade foot part was built, because under the
standard the plantigrade foot is base geometry, not a socket part.**
A standalone plantigrade paw (e.g. for a bear-style plantigrade
module) is unbuilt future work, not an omission in this part.

**Frame:** right foot; origin at the ground under the hock, toes +Y,
plantar −Z. Part length 0.267 m against the socket's ≈ 0.28 m fit
volume.

**Path.** `Ankle_R` (the hock) sits at z = 0.256 m. The **metatarsus**
is a 6-ring loft descending and pitching forward from the hock to
the MTP joint at z ≈ 0.032 — the long "second ankle" segment that
defines the digitigrade stance — with a **calcaneal knob** ellipsoid
at the back of the hock (internal overlap; fit-excluded). Weights
blend `Ankle_R` → `Metatarsus_R` down the shaft.

**Toes — digits II–V bear the weight.** 3-phalanx lofts pitched down
38° / 22° / 5° across the segments to bring the tips to the ground
plane. III/IV are the central, longest pair (60 mm each), II 55 mm,
V 51 mm — the canine primary-pair pattern, recorded in the
`function.gait` block (`contact: toes`, `ik_hint: hock-back`).
Cost measure: each toe gets **two** bones — proximal, and mid+distal
combined — which matters in §7.

**Dewclaw (digit I).** A small 2-phalanx loft on the medial-proximal
metatarsus (−0.0205, 0.026, 0.118), pointing down-forward, with its
own `Dewclaw_R` bone and a 9 mm claw; visible in `foot_front.png`.
Declared variant **`dewclaw_off`**: hide the `Dewclaw_R`-weighted
geometry — the hind dewclaw is absent or rudimentary in many canids,
so this is a per-character toggle, not a second part.

**Pads.** **Metatarsal heart pad** (two lobes + distal apex) on the
plantar MTP — per the gait block, a *secondary* contact under load;
the toes are primary. Digital pads under each distal toe segment.

**Claws.** 15 mm cones at the toe tips, forward-down, bases embedded.

---

## 5. Rig & skinning summary

| | Hand | Foot |
|---|---|---|
| Core joints | `Wrist_R` | `Ankle_R` |
| Module joints | 15: 3 per digit × 5 | 10: `Metatarsus_R`, 2 per toe × 4, `Dewclaw_R` |
| Mode | own-weights (authored) | own-weights (authored) |
| Max influences | 2 | 2 |

Articulation check: `renders/hand_grip_pose.png` poses all finger
chains at −0.45 / −0.65 / −0.55 rad with the thumb at −0.35 — the
chains curl into a credible grip with no visible collapse. That
single pose is the only articulation evidence; no pose suite was run
(§9, debit 6).

---

## 6. Fit QA

**Method:** PARTS_STANDARD §5 — `parts-lab/fit_score.py` at
resolution 128; `fit_score = engaged × (1 − excess)`; gates:
≥ 0.75 fitted · 0.40–0.75 partial (ships only with the deficiency in
the record) · < 0.40 rejected.

**Bases.** No full character base was used. Each part was scored
against a purpose-built **sleeve stub** shipped in the blend —
`stub_forearm` (forearm-end sleeve) and `stub_shin` (shin-end
sleeve following the metatarsus path) — lofted ≈ 2.5 mm proud of the
cuff they receive.

**Why cuff-region scoring.** A whole-part score is 0.0 *by
construction*: fingers and toes have no base surface to engage, so
the standard's metric would grade a hand on its fingertips. The
socket's seating surface is the cuff, so the scored region is the
cuff, exported as its own STL by the build script (faces touching a
fit-excluded vertex are skipped, so the internal thenar/calcaneal
blobs never enter the sample):

- hand — wrist cuff: palm loft rings y ≤ 0.032;
- foot — hock/metatarsus cuff: main-mesh faces with all verts
  z ≥ 0.200.

| Part | buried | engaged | excess | **score** | Verdict |
|---|---|---|---|---|---|
| `paw_hand_r` cuff vs `stub_forearm` | 93.75% | 79.86% | 9.72% | **0.721** | partial |
| `paw_foot_digi_r` cuff vs `stub_shin` | 100.0% | 88.89% | 11.11% | **0.790** | fitted |

Reading the numbers honestly:

- High burial is the **correct signature of a sleeve seat**, not a
  defect — cf. PARTS_STANDARD §5.1 run 2, where the tongue's 73.7%
  burial is what correct cavity seating looks like. A cuff that
  buried 0% would be floating.
- The hand's residual 9.72% excess is the loft start-cap pole vertex
  and axis-adjacent cuff verts reading as deep-buried **inside a
  solid-scored sleeve** — an artefact of scoring a sleeved cuff
  against a solid volume, not a surface misfit. Cuff-wall engagement
  is 79.9% at a designed gap of ≈ 1.5 mm. The hand ships at 0.721
  under the standard's partial rule, with this note — that is the
  rule working as intended, not a waiver.
- The foot's excess is likewise cuff verts seated deep along the
  sleeve axis.
- Sample-size caveat (finisher finding): the hand cuff STL exported
  by the build is **29 verts** (the first two loft rings + start-cap
  pole — build log: `CUFF VERTS 29 29`). The 0.721 rests on a thin
  sample; see §9, debit 5.

---

## 7. Budget accounting & catalogue findings

**Formula check** (PARTS_STANDARD §2.2):
`points = ceil(verts / 1000) + bones + 2 × morphs`, re-verified
against the shipped GLBs in the finisher pass:

- hand: ceil(1270/1000) + 16 + 0 = 2 + 16 = **18** ✓ (record: 18)
- foot: ceil(1092/1000) + 11 + 0 = 2 + 11 = **13** ✓ (record: 13)

**Caps** (§2.2): detail ≤ 4 · **standard anatomy ≤ 12** · major ≤ 25.
Both parts price **over the standard-anatomy cap and inside the
major cap** — the hand by 6 points, the foot by 1.

**The accounting finding.** The entire overage is digit-chain bones.
Geometry contributes 2 of the hand's 18 points; the skeleton
contributes 16. A hand is not a "major" part by any intuitive
measure — 0.21 m long, 1.3k verts — but *any* articulated hand prices
as one under the flat per-bone rule: 3 bones × 5 digits is what a
hand is. The foot already applies the obvious economisation
(2 bones per toe instead of 3) and still lands at 13. The standard
prices bones flat because bones are what animation costs — but as
written it structurally cannot admit a standard-cap hand. Options,
for the standard's owner to rule (not decided here):

1. class articulated extremities (hands, paw-feet) as **major**;
2. discount module digit bones (e.g. 0.5 pt) past the first chain;
3. keep the caps and record extremity parts as standing exceptions.

Until ruled, both records carry the overage openly in `budget_note`
and ship inside the major cap and the 128-pt character pool.
Pool-pressure data point for the same ruling: hands + digi feet on
both sides = 2 × (18 + 13) = **62 of 128 points** before ears, tail
or head parts are equipped.

**Catalogue gap — no distal hand socket.** The catalogue's arm
socket (#15, `arm.L/R`) is shoulder-anchored: its fit volume is the
*upper-arm cylinder*, i.e. whole-arm parts. `paw_hand_r` anchors at
`Wrist_R` and seats a cuff into the forearm, so its record declares
socket `arm.R` with a note that it is a **distal sub-part of the
arm.R family**. The foot side already has the precedent — `leg.digi`
(#16) is exactly a distal module socket. Recommendation: add a
distal-extremity hand socket mirroring #16, so hands stop borrowing
the whole-arm socket.

---

## 8. QA gauntlet

Independent re-run in the finisher pass
(`qa-gauntlet/validate_glb.py`, both GLBs):

| Check | `paw_hand_r.glb` | `paw_foot_digi_r.glb` |
|---|---|---|
| Parses | ok | ok |
| Meshes / primitives | 3 / 3 | 3 / 3 |
| Verts / tris | 1,270 / 2,456 | 1,092 / 2,108 |
| Degenerate tris | 0 | 0 |
| NaN verts | 0 | 0 |
| Skin | present, inverse bind matrices, all 3 prims weighted | same |
| Joints | 16 | 11 |
| Max extent | 0.205 m | 0.266 m |
| Morphs | 0 (warn: none present) | 0 (warn: none present) |
| Rig contract | 1/36 — "fail" | 1/36 — "fail" |

The contract line needs its context: the gauntlet's contract gate
grades against the full 36-bone *character* rig. A module part
carries its one core anchor (`Wrist_R` / `Ankle_R`) plus its module
chain by design, and the records declare exactly that — module parts
are exempt from the full-character contract gate. "1/36 + module
chain, 0 degenerate, 0 NaN" is the pass condition for this part
class, and both parts meet it.

---

## 9. Renders & honest debits

**Renders** (512², Cycles 24 samples, stubs hidden):

- `hand_dorsal.png` — back of hand: clean fan, opposed thumb, claw
  tips at each fingertip.
- `hand_palmar.png` — pad layout reads in correct anatomical
  positions (heart pad, digitals, carpal).
- `hand_grip_pose.png` — §5's articulation check.
- `foot_side.png` — the digitigrade profile: hock, long metatarsus,
  toes and metatarsal pad at the ground line.
- `foot_front.png` — four toes abreast, claws down, **dewclaw
  visible** on the medial metatarsus.
- `foot_plantar.png` — toe pads + metatarsal heart from below.

**Debits:**

1. **Right side only.** No `_l` parts exist. PARTS_STANDARD §1/SP8
   makes placement symmetry an *editor mode*, so left instances are
   mirrors at equip rather than separate part files — but no
   mirrored equip has been verified, and the build script is
   `_R`-hardcoded (thumb at −X, fan signs, medial dewclaw). If left
   part *files* are ever wanted, mirroring is a real script task
   (bone renames, X-flip, winding), not a checkbox. It was not
   attempted in the finisher pass for exactly that reason.
2. **Pads read as appliqué in flat shading.** Placement and
   proportions are anatomically right, but each pad is a sunken
   ellipsoid with a hard intersection silhouette in a near-black
   flat material: in `hand_palmar.png` / `foot_plantar.png` the
   digital pads read as dark discs with a centre dome, and the
   metacarpal/metatarsal hearts read as separate beans rather than
   one heart-shaped pad. Pass 2's deeper sink improved this; a
   union/blend pass or material-level blending is the actual fix.
3. **Digits are smooth tapered tubes.** Knuckle and joint definition
   is loft taper only — no knuckle creases or swellings; from the
   front the toes read slightly blocky (10-gon rings, rz = 0.90 r).
4. **Proportions sit at the lean extreme.** The foot's metatarsus is
   long and slender (greyhound-like) with relatively small toes;
   the palm reads broad and paddle-like from dorsal. Both are within
   canine variation, but a stockier variant is a parameter pass that
   has not been built.
5. **Fit evidence is stub-based and, for the hand, thin-sampled.**
   Both scores are against purpose-built sleeve stubs, not a real
   base arm/leg; no full-character equip test exists. The hand's
   0.721 additionally rests on a 29-vert cuff sample (§6).
6. **No morphs, no pose suite.** 0 morph targets (correctly no claw
   retract — canine claws are non-retractile — but also no toe
   splay or pad squash), and articulation evidence is one grip pose
   for the hand and bind pose only for the foot.
7. **Blend hygiene.** `parts/` carries the stale `b11_hands_feet.blend1`
   backup alongside the blend. The two stub objects inside the blend
   are intentional fit bases (§6), not stray geometry — don't clean
   them out as clutter.
