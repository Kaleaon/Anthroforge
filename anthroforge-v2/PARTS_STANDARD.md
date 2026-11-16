# Parts Standard — Sockets, Part Records, Fit Scoring

**Status:** Normative for AnthroForge parts, Nov 12, 2026.
**Agrees with:** `APP_BLUEPRINT.md` §3.4 (part record) / §3.5 (sockets) / §8.1 (rig contract) / §11.0 (export gauntlet) · `BODY_PLANS.md` (plan record, wing sockets, plan-fit rules) · `SPORE_AND_PARTS.md` rules SP1–SP10.
**Companion code:** `parts-lab/fit_score.py` (§5).

Where this document extends the blueprint, the extension is marked
**[PS]** and is backward-compatible: a part record that ignores every
[PS] field is still a valid §3.4 record.

---

## 1. Part classes — three attachment tiers

Joe's modularity ruling (rigged preferred, rigid fallback) plus SP6's
free-attach partition give three classes. The class is a property of
the part record (`skin.mode` + `class`), never of the mesh alone.

| Class | `skin.mode` | Contract | Use for | Never for |
|---|---|---|---|---|
| **A — Rigged socketed** (preferred) | `own-weights` (authored) or `inherit` (transferred at equip, blueprint §8.4) | Named socket + fit region + weights to the shared skeleton; may carry morphs, chains (ear/wing/tail modules), and a `function` block | Ears, tails, jaws, wings, digitigrade legs, teeth arcades — anything that bends, animates, or means something | — |
| **B — Rigid bone-attached** (fallback) | `rigid` | Named socket *or* named bone + local transform; single-bone full weight | Horns, crest plates, nose rings, folded-wing shells, props that genuinely never bend internally (the Bento lesson: a rigid "wing" is an ornament, not a wing) | Anything the expression/animation system must move |
| **C — Free-attach detail** (SP6) | `rigid` or `inherit` | **Parent bone + surface offset only.** No socket, no fit region, no weights of its own, no morphs, no semantics | Ornaments, piercings, crest feathers, scars-as-geometry, decals-with-relief — placed anywhere on a named body region via `free.1..4` | **Graduation rule (SP6):** the moment a part needs its own weights, morphs, animation, or a `function` block, it leaves class C and takes a socket. Free-attach is safe exactly where the system can procedurally guarantee the consequences; class C's guarantee is "it rides the bone and cannot break the surface it sits on" — nothing more |

Symmetry (SP8): placement symmetry is an **editor mode**, not part
data. A class-C placement or a mirrored socket pair can be flagged
asymmetric **per part instance** in the character record, and the flag
is reversible — un-flagging restores the mirror. (Spore's one-way
asymmetry is the documented counterexample.)

Size classes (KSP lesson, SPORE §5.3): sockets declare a size class
and parts declare theirs. Class mismatch is **data, not a solver
surprise**: the fit re-solve (blueprint §6.5) is the adapter, and a
part whose class differs from the socket's by more than one step is
rejected at equip, not forced.

---

## 2. Socket catalogue

Anchor bones are the v2 36-bone rig's canonical names (blueprint
§8.1). Module chains (ear 4-segment, wing template, tail 5–8) exist
only when a part brings them, per §8.1's module-extension rule and
BODY_PLANS §3.5. Fit volumes are for a ~1.8 m biped at neutral
sliders; volumes scale with the socket's `rescale_by` sliders.
Plans: **B**iped · **T**aur · **F**eral · **N**aga (BODY_PLANS §3.2).

| # | Socket | Anchor bone | Fit volume | Plans | Accepts (kind / class) | Size classes | Socket-level exclusions & conflicts |
|---|---|---|---|---|---|---|---|
| 1 | `ear.L` / `ear.R` | `Ear_L` / `Ear_R` (module chain EarBase→EarTip follows) | Cone, base Ø ≈ 0.09 m, depth 0.05 m, at skull side | B T F N | anatomy / A | S M L | vs `head.top` crest: clip-check above EarHeight +60 (blueprint §3.4 example); vs `hair` mane shells |
| 2 | `eye.L` / `eye.R` | `Head` (eye look-at bones are head extensions) | Sphere r ≈ 0.055 × orbit scale, seated in socket | B T F N | anatomy / A (pupil/iris are variants *on* the part, not parts) | S M L | Extra/alt eyes are class C on `Head`, never a socket variant |
| 3 | `brow` | `Head` | Strip ≈ 0.16 × 0.03 m above each orbit | B T F N | anatomy / A or B | — | Species-gated: torus strips are humanoid/orc equipment; animal bases take brow *sliders*, not brow parts |
| 4 | `muzzle` | `Head` | Rostrum box ≈ 0.14 × 0.12 × 0.18 m | B T F N | anatomy / A | S M L | Mutually exclusive with beak/proboscis variants on the same socket (one muzzle per head) |
| 5 | `nose` | `Head` (muzzle tip) | Box ≈ 0.05 m cube at rostrum tip | B T F N | anatomy / A or B | S M | Requires a `muzzle` occupant or base rostrum; nose-leather material zone rides the part |
| 6 | `jaw` | `Jaw` | Mandible volume, hinge at `Jaw` origin | B T F N | anatomy / A | S M L | Carries the `function.hinge` block (§4); jaw variants and `teeth.lower` must be co-validated (gape vs arcade) |
| 7 | `teeth.upper` | `Head` (skull) | Arcade shell inside muzzle, ≈ 0.11 m wide | B T F N | teeth / A | S M L | One universal arcade (Joe's ruling): diet is morph axes on the part, never a second part on this socket |
| 8 | `teeth.lower` | `Jaw` | Arcade shell inside mandible | B T F N | teeth / A | S M L | Tusk emergence is a morph extreme of this part; splay = f(JawWidth) coupling (SP9 hint surface) |
| 9 | `head.top` | `Head` | Cap patch ≈ 0.12 m Ø on skull crown | B T F N | anatomy / A or B | S M L | Horn pairs vs crest vs ears: pairwise clip-checks; antlers are class A (they sway), horn cores may be B |
| 10 | `hair` | `Head` | Scalp shell, offset ≤ 0.03 m from skull surface | B T F N | hair / A or C-inherit | — | Mane shells conflict with `ear.*` and `head.top` occupants — declared per part, checked per plan (BODY_PLANS §4.3 rule 4) |
| 11 | `neck.ruff` | `Neck` | Collar torus ≈ Ø 0.24 m, length 0.15 m | B T F N | anatomy, hair / A | S M L | Ruff volume vs wing roots on B/T/N: clearance check in spread/fold poses |
| 12 | `back` | `Spine1` (patch follows `Chest`) | Dorsal patch ≈ 0.30 × 0.40 m | B T F N | anatomy, clothing / A or B | — | **Socket presence ≠ fit (BODY_PLANS §4.3):** barrel tack/armour fits only the T/F instances of this socket; biped back-wear does not transfer to the barrel |
| 13 | `wing.L` / `wing.R` | `Chest` (core `Wing_L1/L2` are the minimum instance; full template = WingRoot + Wing1–5 + fan branches, BODY_PLANS §3.5) | Root patch ≈ 0.10 × 0.14 m on upper back | B T N (instance: upper back) | anatomy / A only | M L | Rigid wings forbidden (class B shells must use `back` and declare themselves ornaments); wing state set is owned by the part family (BODY_PLANS §3.5) |
| 14 | `wing.wither.L` / `wing.wither.R` | `Chest` (feral instance of the wing sockets) | Root patch at the withers, between forequarters | F | anatomy / A only | M L | Same part family as #13, plan-specific socket instance — a wing part lists both sockets in `socket_by_plan` |
| 15 | `arm.L` / `arm.R` | `Shoulder_L` / `Shoulder_R` | Upper-arm cylinder ≈ Ø 0.11 m | B T N | anatomy, clothing / A | S M L | **Absent on F** — feral forelimbs are legs; arm parts are excluded, not hidden (§4.3) |
| 16 | `leg.digi.L` / `leg.digi.R` | `Ankle_L` / `Ankle_R` + digitigrade hock module | Lower-leg/paw volume ≈ 0.28 m long | B (module inside plan.biped, BODY_PLANS §3.3) | anatomy / A | S M L | Plantigrade↔digitigrade is a leg-style module swap, not a plan switch |
| 17 | `leg.fore.L/R`, `leg.hind.L/R` | Fore: `Hip_L/R` chains repositioned · Hind: plan hindleg chain at RearPelvis | Lower-leg/paw volume, per pair | T F | anatomy / A | S M L | Fore and hind instances are **independent** — lengths, fits and conflicts are never coupled (BODY_PLANS §3.4 hard rule) |
| 18 | `tail.base` | `Pelvis` (core `Tail_1`; module chain 5–8) | Rump cone, base Ø ≈ 0.08 m | B T F (appendage role) | anatomy / A | S M L | **On N this socket does not exist:** the tail chain's role is `body`, and tail-tip items there are body parts with body-part cost/safety treatment (BODY_PLANS §4.3) |
| 19 | `pelvis.genital` | `Pelvis` (GenBase chain) | Ventral pelvis volume ≈ 0.12 × 0.10 m | B T F N | anatomy / A | S M L | Position rule follows the pelvis's *job* per plan (BODY_PLANS §3.7); a genital part needs a per-plan instance or a plan-locked declaration — the biped position is never assumed |
| 20 | `free.1` … `free.4` | **Any bone** (instance stores bone + local transform) | None — offset contract only (SP6) | B T F N | detail / C only | — | Four concurrent free-attach instances per character; a fifth placement replaces or graduates. Class C only — see §1 graduation rule |

**Count: 28 named sockets + 4 free-attach slots = 32 socket entries.**
(Blueprint §3.5's 19 named sockets, plus the plan instances BODY_PLANS
requires: `wing.wither.*`, the split quadruped leg sockets, and the
`tail.base` naga carve-out made explicit.)

### 2.1 Conflict / exclusion fields (normative)

Every part record carries `conflicts` from its first shipped version
(blueprint §3.4, the SCVI lesson). [PS] extends the entry shape:

```json
"conflicts": [
  { "with": "hair_mane_v1", "kind": "clip | exclude | clearance",
    "plans": ["plan.biped"], "above": {"head.ear.height": 60},
    "note": "mane shell intersects ear base above EarHeight +60" }
]
```

- `kind: exclude` — the two parts may never co-equip.
- `kind: clip` — co-equip allowed; the fit re-solve runs and the
  pair is flagged in the export report if intersection remains.
- `kind: clearance` [PS] — no static intersection, but a *pose*
  (wing fold, jaw gape, coil) can collide; checked in the plan pose
  suite (BODY_PLANS Part VII), not at equip.
- `plans` [PS] — conflicts are **re-evaluated per plan**; an entry
  with no `plans` field applies on all plans.
- Socket-level exclusions (table above) are defaults the *socket*
  enforces even when a part forgets to declare them.

### 2.2 Complexity cost — the budget fields

Per the WWE rule (CREATOR_LESSONS R5) and Spore's two-budget split
(SP3): **capability tier and technical cost are separate fields,
always.**

```json
"tier": 3,
"cost": { "verts": 1450, "tris": 2600, "bones": 4, "morphs": 0, "points": 6 }
```

- `points` [PS formula, published here]: `ceil(verts / 1000) + bones + 2 × morphs`.
  Calibrated so the blueprint §3.4 worked example (pointed ear,
  1,450 verts / 4 bones / 0 morphs) prices at exactly **6**.
- `tier` (SP3): 1 = basic … 5 = most capable/expressive. The parts
  browser sorts by tier within category; tier never enters `points`.
- **Per-part caps by budget class:** detail ≤ 4 pts · standard
  anatomy ≤ 12 pts · major (wings, tails, full leg modules) ≤ 25 pts.
  A part over its class cap does not ship; it is decimated or split.
- **Character pool: 128 points** (WWE's pool), summed over equipped
  parts, shown in the UI meter, **enforced at export** (blueprint
  §11.0) — an over-pool character edits fine and exports with a
  `broken` conformance flag until the pool is respected. Spore's
  complexity-gates-sharing rule, at export instead of upload.

---

## 3. The part record, v1.1 [PS deltas only]

Everything in blueprint §3.4 stands. Additions:

```json
{
  "class": "A | B | C",
  "tier": 1,
  "size_class": "S | M | L",
  "function": { },
  "plan_fit": {
    "plans": ["plan.biped", "plan.quadruped_taur", "plan.naga"],
    "socket_by_plan": { "plan.quadruped_feral": "wing.wither.L" },
    "variant_by_plan": { "plan.naga": "wing_membrane_naga.glb" },
    "excluded_plans": []
  },
  "lineage": { "from": ["partA", "partB"], "blend": 0.5 },
  "fit_qa": { "score": 0.99, "base": "openfur_canine_5.0",
              "tool": "parts-lab/fit_score.py", "date": "2026-11-12" }
}
```

- `plan_fit` is BODY_PLANS §4.3's block, adopted verbatim. Equip
  requires **all four** §4.3 conditions (socket provided, plan listed
  or plan-agnostic + fit-score pass, fit regions exist in the plan's
  region map, no conflict fires under this plan).
- `lineage` is SP10: a variant may declare two parents and a blend;
  animation-relevant parameters (tail sway, ear carriage) blend with
  the geometry (Impossible Creatures' combiner principle).
- `fit_qa` [PS]: the part's intake fit score (§5) against its
  reference base. No score, no ship — for class A and B parts.
  Class C is exempt (its contract has no fit region to score) and
  carries `"fit_qa": {"exempt": "class-C"}` instead.

---

## 4. The `function` block (SP1 / SP3)

Parts carry **semantic tags, not game numbers**. Consumers —
animation, expression, materials, export validation, the derived
character sheet — read the block; they never infer function from
names or categories (SP1). The block is **optional**: ornament parts
declare none, and authors must not be forced to fake values.

```json
"function": {
  "jaw":    { "diet_archetype": "carnivore",
              "hinge": {"axis": "x", "gape_deg": [0, 42],
                        "translation_mm": 4} },
  "teeth":  { "arcade_ref": "teeth/universal_arcade",
              "diet_axes": ["TeethCanine", "TeethMolar", "TeethIncisor"] },
  "gait":   { "profile": "digitigrade", "contact": "toes",
              "stance_width": 0.62, "ik_hint": "hock-back" },
  "ear":    { "carriage_deg": [-30, 45], "expression_role": "primary" },
  "eye":    { "vision": ["slit-pupil", "nocturnal"] },
  "wing":   { "flight": "glide", "states": ["folded", "relaxed",
              "spread", "flap", "glide", "display"] },
  "tail":   { "sway": {"amp_deg": 12, "freq_hz": 0.6} }
}
```

Rules:

1. **Character-level values are computed views (SP2).** Diet comes
   from the equipped jaw/teeth parts; gait family from the leg
   parts; flight from the wing part. The character record stores
   none of these. `character_load`'s resolved summary recomputes
   them on every equip/unequip.
2. **Aggregation is documented per field**, never improvised:
   `diet_archetype` = the jaw part's value (single occupant);
   hearing/expression range under asymmetric ears = **per-side**;
   total complexity = **sum** of `cost.points`; capability display =
   **max** tier per category (Spore's best-part-wins, as a *display*
   rule only).
3. **Diet lives on the teeth/jaw parts, not the character** —
   Spore's mouth-is-the-diet-field, and the same architecture as
   Joe's universal-arcade ruling: one arcade part, diet as its
   morph axes, character diet as the derived view.
4. **Gait profiles feed procedural locomotion (SP5):** stance +
   leg-part `gait` blocks are the input to the stepping layer; a
   leg part without a `gait` block cannot be locomotion-validated
   and is flagged at intake.
5. **Ear carriage is expression data:** on furry heads ears carry
   roughly half the emotional vocabulary (expression-system.md);
   `carriage_deg` bounds what the expression masters may ask of
   the part.

---

## 5. Fit scoring — the intake gate

**Tool:** `parts-lab/fit_score.py` (numpy + scipy, no trimesh).
**Method:** the Khajiit Hair Unlock study's buried-vertex score,
generalised. Voxelise the base volume (3-axis scanline majority
fill — real bases are open shells and flood fills leak), then test
every part vertex:

- `buried_pct` — % of part verts inside the base volume. Some burial
  is *correct* (ear bases, teeth roots seat in). Burial alone is
  never the score: a part floating in space buries 0% and fits
  nothing.
- `engaged_pct` — % of part verts within the contact band (default
  3 voxels) of the base surface, either side. The coverage term.
- `excess_pct` — % buried deeper than 15% of the part's own bbox
  diagonal. Deep burial = swallowed / mis-scaled / wrong frame.
- **`fit_score = engaged × (1 − excess)`** ∈ [0, 1].
  **≥ 0.75 fitted · 0.40–0.75 partial · < 0.40 poor.**

**Gates:** class A/B parts ship at ≥ 0.75 against their reference
base; 0.40–0.75 ships only with the deficiency written into
`fit_qa.note`; < 0.40 is rejected at intake. Scores are recorded in
`fit_qa` (§3) with base identity and date — a score without a named
base is meaningless, because **the score is frame-relative**: parts
must be scored in the frame they ship in. (Intake corollary, proven
by run 4 below: check the frame *before* scoring — a part file in a
local origin frame is a fitter input, not an equippable part.)

**Cavity caveat:** the score measures surface-seating fit. A part
that belongs inside a hollow (tongue in a mouth cavity) reads as
deep-buried against a *solid* base; score cavity parts against the
hollowed base or read `buried_pct` as seating depth for them.

### 5.1 Measured runs (Nov 12, 2026, resolution 128)

Base/part: OpenFur Canine 5.0 (Luccus, CC BY-SA 4.0) — head, jaw,
gums, tongue STLs share one assembled frame as shipped.

| # | Part vs base | buried | engaged | excess | **fit_score** | Verdict |
|---|---|---|---|---|---|---|
| 1 | Gums vs Head+Jaw | 30.9% | 79.4% | 0.0% | **0.794** | fitted |
| 2 | Tongue vs Head+Jaw | 73.7% | 99.5% | 0.5% | **0.990** | fitted |
| 3 | **Control:** OpenFur Teeth vs Cults HoneyBear head (deliberate mismatch) | 0.0% | 0.0% | 0.0% | **0.000** | poor |

Run notes:

- **Run 1** is the honest middle case: the gumline wraps the mouth
  line across both skull and jaw pieces — against Head *alone* it
  scores 0.0 (its seat is mostly jaw territory), which is why bases
  are unioned per socket assembly, not per file.
- **Run 2:** the tongue's high burial is *correct seating* inside
  the jaw assembly — engaged 99.5% with near-zero excess is what a
  well-seated cavity part looks like under this metric.
- **Run 3 (control):** total separation, as required — the teeth
  fall 100% outside the bear head's grid (different author, scale,
  and origin conventions). Fitted pairs score 0.79 / 0.99; the
  control scores 0.000.
- **Frame diagnostic (not a scored pair):** OpenFur's own Teeth STL
  ships in a *local* frame (bbox z 0–15.7, centred on its own
  origin) while its Head/Gums/Tongue/Jaw share the assembled frame
  (z 0–178.9). As shipped it cannot score against its own head —
  placing it is the teeth fitter's job (blueprint §6.4). The score
  caught, on first contact, exactly the failure class it exists to
  catch.

Reproduce:
```
cd parts-lab
python3 fit_score.py --base <Head.stl> --base <Jaw.stl> --part <Gums.stl> --json
python3 fit_score.py --base <Head.stl> --base <Jaw.stl> --part <Tongue.stl> --json
python3 fit_score.py --base <HoneyBear.stl> --part <Teeth.stl> --json
```

---

## 6. First-10-parts pack

The first pack proves every socket class and every licence tier.
Sources are **owned library assets only**. Several entries are
*donor-region extractions* from full meshes (the pack spec names the
source file and the region; extraction + re-weighting per blueprint
§8.4 is the authoring step, not a claim the part file already
exists standalone).

| # | Part | Source (owned) | Licence tier | Socket | Plans | Class / notes |
|---|---|---|---|---|---|---|
| 1 | `ear_point_canine` — pointed canine ear | CVRxEarth "Big Bad Wolf" glTF — `bodies-3d/parts-library/existing-haul/wolf-rigged-ccby/` (also `furry-lineup/…/models/wolf_cvrx/scene.gltf`), ear region extraction | **build** — CC BY-4.0 | `ear.L/R` | B T F N | A · the reference ear; carries `function.ear` carriage |
| 2 | `ear_fennec` — oversize fennec ear | Codaj "Anthro Fennec Rigged" GLB — `bodies-3d/parts-library/sketchfab/anthro-fennec-rigged-codaj/` (41k verts, named ear chains) | **build** — CC BY-4.0 | `ear.L/R` | B T F N | A · size class L; EarHeight anchor donor for the fennec preset |
| 3 | `ear_round_bear` — rounded bear ear | KilliansCorner Honey Bear head STL — `character_assets/cults3d/HoneyBear.stl`, ear region extraction | **study** — Cults freebie terms: personal making/altering; commercial needs separate licence (cults MANIFEST) | `ear.L/R` | B T F N | A · fills the bear gap (Sen); graduates to build only on licence check or re-authoring |
| 4 | `tail_canine_bushy` — bushy canine tail | CVRxEarth wolf glTF, tail region extraction | **build** — CC BY-4.0 | `tail.base` | B T F | A · `function.tail` sway donor |
| 5 | `tail_fennec` — fennec tail | Codaj fennec GLB, tail (12-bone chain in source; instanced to the 5–8 module chain) | **build** — CC BY-4.0 | `tail.base` | B T F | A · longest-chain donor; chain-compression test case |
| 6 | `tail_collie_plume` — plumed dog tail | AKM Border Collie GLB — `furry-lineup/…/models/border_collie.glb`, tail extraction | **study** — licence **UNKNOWN** in library records; verify before any build use (cleared fallback donor: styloo dog, CC0) | `tail.base` | B T F | A · QA-gauntlet gold-reference mesh, licence paperwork lags the geometry |
| 7 | `horns_dragon` — dragon horn pair | KilliansCorner Big Snoot Dragon headbase — `character_assets/cults3d/` (foam-model-big-snoot-dragon…), horn region extraction | **study** — same Cults freebie terms as #3 | `head.top` | B T F N | B (rigid cores) · first `head.top` occupant; antler-class A variant is future work |
| 8 | `paws_digitigrade_feline` — digitigrade paw set | Vr-cvantorium rigged cat glTF — `bodies-3d/parts-library/existing-haul/cat-rigged-ccby/` (also `character_assets/cat-rigged-CCBY.zip`), hind paw extraction | **build** — CC BY-4.0 | `leg.digi.L/R` (+ T/F leg instances) | B (T/F instances) | A · carries `function.gait: digitigrade`; the Khajiit digitigrade architecture (separate paw mesh, foot collapsed in place) is the fitting model |
| 9 | `wings_membrane` — membrane wing pair | styloo Animals Pack, butterfly GLB — `character_assets/styloo-animals-CC0.zip` (`glb/butterfly.glb`), wing extraction, re-proportioned | **build** — CC0 | `wing.L/R`, `wing.wither.L/R` | B T F N | A · low-poly donor — proves the wing socket + state set; **named gap:** no build-tier feathered/bat wing donor on disk yet (SL GoldPearl wing template awaits the wear-scan) |
| 10 | `mane_lion` — lion mane / neck ruff | Poly Haven Lion Head glTF — `bodies-3d/parts-library/polyhaven/lion-head/` (photoscanned sculpture), mane region extraction | **build** — CC0 | `neck.ruff` (+ `hair`) | B T F N | A · first ruff occupant; its `hair` conflicts with `ear.*` occupants are the pack's worked conflict example |

**Pack coverage check:** sockets exercised — ear ×3 styles, tail ×3,
head.top, leg.digi, wing (+wither instance), neck.ruff. Tiers —
7 build (5 CC BY, 2 CC0) / 3 study, each study entry naming *why*
and what graduates it. Classes — 9 × A, 1 × B; class C is exercised
by the free-attach *slots*, which ship empty by design (their first
occupants are user-placed ornaments, not pack content).

---

## 7. Intake checklist for a new part (summary)

1. Record complete per §3.4 + §3 [PS] — class, tier, size class,
   `plan_fit`, conflicts (present even if empty), cost counted.
2. Frame check: the part file sits in its shipping frame
   (bbox sanity vs its reference base). Local-frame files go to the
   fitter, not the library.
3. Fit score (§5) ≥ gate against the named reference base;
   recorded in `fit_qa`.
4. Licence tier verified from the source manifest — **UNKNOWN is a
   tier, and it means study** until resolved (pack #6 is the standing
   example).
5. `function` block present where the category has semantics
   (§4); gait block mandatory on leg parts.
6. Pose-suite clearance conflicts (`kind: clearance`) checked on
   every plan in `plan_fit.plans`.
7. Mandatory anatomy (SP7): a character with no resolved head or no
   teeth-arcade resolution path **cannot export** — parts are how
   that gate gets satisfied, so a base with no compatible jaw/teeth
   parts in the library is a library bug, reported as one.
