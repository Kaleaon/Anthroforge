# Body Plans — Bento Research and the 4 → 2 → 0 Leg Spectrum

**Status:** Design specification for AnthroForge, Nov 12, 2026.
**Inputs:** Linden Lab's Project Bento skeleton documentation and creator practice; `APP_BLUEPRINT.md` §3.4 (part record), §3.5 (sockets), §8.1 (rig contract), and §11.3 (DAE / Second Life profile).
**Joe's framing:** body plans run **4 legs → 2 legs → 0 legs**, and **wings are a flexibility axis**, not another point on the leg-count axis.

---

## 0. Decisions in one page

1. **A body plan is a rig configuration, not a mesh, species, preset, or slider.** It declares the axial chain, limb sets, tail role, root/pelvis behaviour, ground-contact model, socket instances, slider instances, and locomotion set.
2. **Leg count is selected by changing plan.** There is no `legs` slider and no morph that “grows” or “removes” legs. A plan switch is a re-rigging and re-solving operation.
3. **The shared character survives the plan switch.** Identity, species preset structure, the head slider vector, expressions, teeth, materials, markings semantics, and — where the anatomy exists — upper-body sliders stay in one canonical character record.
4. **Plan-local shape is stored per plan.** The same canonical slider can have a different delta field, mask, and region map on each plan. Switching back to a plan restores that plan's stored instance values instead of overwriting them.
5. **Wings are a cross-plan part family.** Any plan can be ± wings. A wing part brings its own bone-chain template, mounts at plan-specific instances of the `wing.L` / `wing.R` sockets, and carries its own folded / relaxed / spread / flap / glide / display animation states.
6. **Bento is an export profile, never the internal rig.** AnthroForge keeps its own canonical names and plan-specific chains. The SL DAE profile maps them to Bento names, emits partial skeletons deliberately, and reports every merged, baked, or dropped chain.

---

# Part I — What Project Bento actually provides

Primary source: Linden Lab, *Project Bento Skeleton Guide*, https://wiki.secondlife.com/wiki/BentoSkeletonGuide

Bento added **106 new bones** to the Second Life avatar skeleton. The largest groups are facial-expression and finger joints. Bone numbers are ordered from the root outward: the joint closest to the root has the lowest number.

Two Bento properties matter throughout this design:

- **Partial skeletons are allowed.** A rigged DAE no longer has to specify every bone; unused bones can simply be omitted from the skinning data. This is what makes tail-only, wing-only, and lower-body add-on exports practical.
- **Many Bento bone positions are driven by avatar shape sliders.** Wing, tail, hind-limb, face, hip, collar, eye, and foot bones are all position-affected. An animation that contains translations can partially or completely override the position the shape sliders produced. Bento joint placement is therefore a negotiation between the mesh's uploaded joint positions, the wearer's shape, and whatever animation is playing — not a fixed bind pose the creator fully controls.

## 1.1 Wing bones

The final Bento wing set is **11 joints**:

| Structure | Bones |
|---|---|
| Shared root | `mWingsRoot` — lies at the base of the wings; exists so the pair can be moved or repurposed together |
| Left main chain | `mWing1Left` → `mWing2Left` → `mWing3Left` → `mWing4Left` |
| Right main chain | `mWing1Right` → `mWing2Right` → `mWing3Right` → `mWing4Right` |
| Left fan branch | `mWing4FanLeft` — branches off the main chain, intended to help with applications like bat wings |
| Right fan branch | `mWing4FanRight` |

Early Bento drafts used names such as `mWingsRoot1` / `mWingsRoot2`. The shipping name is the singular **`mWingsRoot`**; exporters must use the final names, not names found in old draft material.

Bento also added wing attachment points — **Left Wing (45)** and **Right Wing (46)**. An object attached there follows the attachment transform rigidly. That is not the same thing as being rigged to the wing bones.

## 1.2 Hind-limb bones

The hind-limb set is **9 joints**:

| Structure | Bones |
|---|---|
| Shared root | `mHindLimbsRoot` — parent of both hind chains, effectively a second pelvis |
| Left chain | `mHindLimb1Left` → `mHindLimb2Left` → `mHindLimb3Left` → `mHindLimb4Left` |
| Right chain | `mHindLimb1Right` → `mHindLimb2Right` → `mHindLimb3Right` → `mHindLimb4Right` |

Linden's guide states the default position is **behind the original legs**, as an additional pair of legs, and explicitly notes the chains can be repositioned and used for a second pair of arms or wings instead. Bento also added **Left Hind Foot (54)** and **Right Hind Foot (55)** attachment points, linked to `mHindLimb4Left` / `mHindLimb4Right`.

Linden coupled the hind limbs to the main body on purpose: sliders that scale `mPelvis` also alter `mHindLimbsRoot` “to better keep the front and hind legs synced up,” and hind-limb sliders were added to match the corresponding leg joints. That coupling is convenient for ordinary avatars and a real constraint for centaurs — see §2.1.

## 1.3 Tail bones

One six-joint chain:

`mTail1` (base) → `mTail2` → `mTail3` → `mTail4` → `mTail5` → `mTail6` (tip)

Attachment points: **Tail Base (43)**, linked to `mTail1`, and **Tail Tip (44)**, linked to `mTail6`.

Six segments is generous for an appendage tail. It is coarse for a serpent body that is tens of segments long in any anatomically serious rig — the central naga problem in §2.3.

## 1.4 Spine additions

Bento inserted four joints into the existing spine:

| Bone | Position |
|---|---|
| `mSpine1`, `mSpine2` | Between `mPelvis` and `mTorso` |
| `mSpine3`, `mSpine4` | Between `mTorso` and `mChest` |

By default these are folded up inside the original spine and do nothing; a model that wants a longer or more flexible trunk must reposition them. They are the only sanctioned way to lengthen the avatar's axial chain in Bento, which is why quadruped and centaur builders lean on them.

## 1.5 Head and face bones, briefly

Bento's head additions are a full facial rig, not a single jaw bone. In outline:

- Face root and shaping: `mFaceRoot`, `mFaceJawShaper`.
- Forehead and brows: `mFaceForeheadLeft/Center/Right`, `mFaceEyebrowOuter/Center/Inner` per side.
- Eyes and lids: upper/lower lid bones per side, eye-corner bones, and `mFaceEyeAltLeft/Right` for additional or independently oriented eyes (the viewer's own eye control uses the original eye bones).
- Ears: `mFaceEar1Left`, `mFaceEar2Left`, `mFaceEar1Right`, `mFaceEar2Right` — also usable for antennae and other head appendages.
- Nose: `mFaceNoseLeft/Center/Right`, `mFaceNoseBase`, `mFaceNoseBridge`.
- Cheeks: upper/lower cheek bones per side.
- Mouth: `mFaceJaw` for open/close, upper/lower lip bones (left/center/right and corners), `mFaceChin`.
- Tongue and teeth: `mFaceTongueBase`, `mFaceTongueTip` (parented under the jaw, as are the lower-lip bones), `mFaceTeethUpper`, `mFaceTeethLower`.

Bento also added 30 finger joints (three per finger). Fingers are outside this document's scope, but they count in the export comparison in §6: Bento's skeleton is far richer than AnthroForge's core in the face and hands, and far poorer in the places body plans actually need freedom (axial length, serpent resolution, wing fingers).

## 1.6 Rigged, rigid, or animesh — the three ways a thing attaches

| Route | What moves it | Follows wearer shape? | Needs its own animations? | Failure mode |
|---|---|---|---|---|
| **Rigged to Bento bones** | Skin weights to the avatar skeleton | Yes — bones are shape-slider positioned | Yes, for any bone Bento has no default motion for (wings, tail, hind limbs, most face bones) | Conflicts with every other item using the same bones; translation animations can override shape-driven joint positions |
| **Rigid attachment** | The attachment point's transform only | Only as much as the point itself moves | No — but it can never bend internally | A “wing” that cannot fold or flap; correct choice only for ornaments, folded-wing shells, and props |
| **Animesh** | Its own independent skeleton inside a separate object | No — animesh does not respond to avatar shape sliders or deformers | Yes — script/AO-driven, entirely self-contained | Consumes scarce animesh attachment slots (1 Basic/Plus, 2 Premium, 3 Premium Plus per Linden's guide); it is a companion object, not part of the wearer's body |

**AnthroForge rule drawn from this:** animesh is an *export target option* for independent creatures, rideables, and constructs whose custom fold/slither solve must not fight the avatar's bones. It is never the internal model of a body plan, because a body plan must live on the character's own skeleton and slider space.

## 1.7 Animation conventions creators have to live with

- **Bento bones ship with no default animations.** An unanimated wing, tail, or hind limb does not idle, sway, or walk. Whatever moves it is an animation the creator ships.
- **Poses stick.** After a Bento animation ends, bones can remain in their last pose instead of returning to neutral. Creators ship a low-priority neutral/background animation or explicit reset keyframes.
- **Partial-skeleton hygiene is a correctness issue, not tidiness.** A tail-only export should be weighted only to the tail bones. If the export's armature contains other bones whose positions were moved during authoring, the uploader can save those as joint-position overrides and deform the *wearer's* body — the classic accident is a tail or ear file that silently shifts the wearer's pelvis or face. Unused bones must be removed, and ancestors included only deliberately.
- **Joint positions are uploaded per mesh and can fight each other.** Two worn rigged items that both reposition the same bones do not compose; the wearer gets whichever override wins.

---

# Part II — How SL actually builds each plan (solved vs hacked)

## 2.1 Centaurs and quadrupeds

Bento did **not** add a quadruped avatar type. Second Life still has one avatar, one root, and one recognised skeleton. Every centaur and feral quadruped in SL is that skeleton repositioned, re-weighted, hidden in places, and driven by a custom animation override (AO). What Bento genuinely added was the *second leg pair* and extra spine joints to build with.

**Centaur construction.** The humanoid upper body — pelvis, spine, chest, neck, head, arms — stays upright at the front. The equine barrel extends backward from the human pelvis. In creator tests reported during Bento development, the front of the body around the pelvis and the front leg pair (built on the repositioned standard leg chains) formed correctly. The rear barrel and rear leg pair are weighted to the `mHindLimb` chains.

**Known pain points — these are design requirements for us:**

1. **Hind-limb joint positions were unreliable.** In Bento-era creator testing, hind legs weighted to the hind chains collapsed to a point behind the pelvis when their positions were supplied through the uploader's joint-position mechanism; the same legs held their shape when a **deform animation** supplied the positions instead. Deform animations remained the working backup. *Lesson: an SL centaur export needs a joint-position path and a deform-animation fallback, and must be honest about which one a given package uses.*
2. **Partial joint positions fight the wearer.** A centaur lower-body add-on wants to reposition only the lower body, but joint-position overrides are not neatly scoped — a centaur attachment can override positions belonging to the wearer's mesh body and head. Commercial centaurs are therefore body-specific add-ons with their own AO and fitting shapes, not universal skeletons. *Lesson: “works with most bodies” is a fitting programme, not a property of the rig.*
3. **Front/hind length coupling breaks ground contact.** A Bento feedback-thread example: a wearer with a short human shape bought a centaur add-on; the front legs came out short because they followed the wearer's shape, and the hind legs ended up under the ground. The creator's requested fix was to decouple hind-leg scaling from avatar-leg scaling and give the hind chains their own directional adjustments. Linden instead kept the `mPelvis`-scale coupling so front and hind legs “sync up.” *Lesson, adopted as a hard rule in §3.4: a plan stores independent foreleg and hindleg lengths and its own ground-clearance calibration. The second leg pair is never a slave of the first.*
4. **Locomotion is a separate discipline.** Four-beat walk, trot, canter/gallop, turning, and lie/sit equivalents are their own animation set. The humanoid torso's gestures layer *over* a quadruped base. Retargeting a biped walk onto a centaur moves the wrong limbs and breaks foot contact; nothing about Bento changes that.

**Feral quadrupeds** differ from centaurs in construction: the whole skeleton is re-aimed horizontal — humanoid arms commonly serve as the front legs and humanoid legs as the rear legs in a full-avatar build, with a custom AO replacing every default humanoid state, and alpha layers / invisiprims historically used to hide whatever of the base avatar should not show.

## 2.2 Biped and digitigrade — the baseline Bento was designed around

The standard SL skeleton *is* the biped plan. Bento's contribution is additive detail: face, fingers, tail, wings, extra spine flexibility.

Digitigrade is **not a separate Bento plan**. Creators achieve it by repositioning the leg joints (lengthening the foot segment so the avatar walks on its toes with a raised hock), re-weighting the leg mesh, and shipping gait animations whose contact timing matches the new geometry. Leg geometry, joint placement, and animation change; the skeleton's identity does not. AnthroForge adopts the same treatment: digitigrade is a leg-style module inside the 2-leg plan (§3.3).

## 2.3 Naga and serpent avatars

Commercial SL nagas are, almost without exception, **tail attachments, not avatar types**:

- The serpent body is a mesh rigged to the six `mTail` bones, worn at the tail base, and shipped with a dedicated Snake AO (idle sway, slither, coil/sit, swim, turns).
- The avatar's legs are **hidden with alpha**, not removed — the leg bones still exist in the skeleton. Products instruct users to apply auto-alpha or an alpha layer; “removes your legs” in a listing means hides them.
- The **pelvis → tail junction is a fitted part of its own.** User reports on naga products describe waist seams, hip clipping, and back/side bumps; a concave pelvis add-on or girdle/collar piece is the standard fix. A raw tube butt-jointed to the waist does not work.
- **Six segments is the hard ceiling**, and it shows: reviewers of naga animation sets report the tail folding on itself near the tip and locomotion that reads as hovering forward rather than ground-hugging undulation. Segment-length distribution and ground contact matter more than chain existence.
- **Nonstandard hierarchy hacks are fragile.** One naga creator's slither animation, correct in Blender, broke in-world; the suspected cause was a modified hierarchy in which the tail base was connected to a hind-limb bone, together with location/rotation key use. Reparenting Bento chains into exotic arrangements is not a stable foundation.
- If the Snake AO omits upper-body states, the avatar falls back to humanoid animations in ways users notice. A naga AO must cover the whole avatar, not just the tail.

**What Bento solved for naga:** a standard tail chain on the avatar, shape-positioned tail bones, partial rigged attachments, tail base/tip attachment points.
**What it hacked:** hidden-not-removed legs, a six-segment ceiling on a body that wants many more, humanoid root locomotion under a body that should move by lateral undulation, and coil/sit states that exist only as individual poses.

## 2.4 Wings in practice

- A rigged Bento wing **must be weighted to the wing bones and shipped with animations**. Wearing a mesh at the Left/Right Wing attachment point produces a rigid ornament, not a wing.
- The four-segment straight chain flaps and flops adequately. It does **not** truly fold:
  - *Bat/membrane wings:* folding needs finger branches radiating from a wrist point. The known workaround repositions the fourth wing bone by translation so it effectively branches from the second, approximating one folded finger — at the cost of location keyframes on every wing keyframe.
  - *Feathered wings:* primaries, secondaries, and scapulars need to fan and slide over each other like a Chinese fan. One `mWing4Fan` branch cannot represent per-feather fanning. Creators accept stylised folding, repurpose other bone systems, or leave Bento for animesh / independent rigs.
- **Design conclusion:** Bento's wing is a *minimum viable wing*. AnthroForge's internal wing template (§3.5) must be richer, and the Bento export must honestly report what it merged away.

---

# Part III — AnthroForge body-plan architecture

## 3.1 The plan record

A plan is a versioned configuration record. It references the canonical rig definition (APP_BLUEPRINT §8.1) and the canonical slider registry; it contains no mesh and no slider deltas of its own.

```json
{
  "format": "anthroforge.body-plan", "version": 1,
  "id": "plan.quadruped_taur",
  "label": "Centaur (quadruped, taur)",
  "leg_count": 4,
  "posture": "taur",

  "root": {
    "bone": "Pelvis",
    "pelvis_role": "locomotor-root | torso-junction | barrel-junction",
    "root_height_policy": "solve-from-leg-pairs",
    "ground_contact": "four-contact"
  },

  "axial": {
    "upright_chain": ["Pelvis", "Spine1", "Chest", "Neck", "Head"],
    "barrel_chain":  ["BarrelRoot", "Barrel1", "Barrel2", "RearPelvis"],
    "serpent_chain": null
  },

  "limb_sets": [
    { "role": "foreleg", "side": "L/R", "chain": "foreleg",
      "length_scale_key": "plan.foreleg.length", "contact": "hoof" },
    { "role": "hindleg", "side": "L/R", "chain": "hindleg",
      "length_scale_key": "plan.hindleg.length", "contact": "hoof" }
  ],

  "tail": { "role": "appendage", "chain": "tail", "segments": "5-8" },

  "locomotion": {
    "set": "quadruped",
    "required": ["stand", "walk", "trot", "gallop", "turn", "lie"],
    "layered": ["upper-body-gesture", "head-face", "wing"]
  },

  "sockets": "plan instance table, §3.6",
  "slider_policy": "shared | per-plan-instance | unsupported, per §4",
  "export": { "bento": "mapping profile, §5" }
}
```

Required fields for every plan, whatever its shape:

| Field group | Declares |
|---|---|
| `root` | Root bone, what the pelvis *means* in this plan, how root height is derived, and the ground-contact model |
| `axial` | The spine configuration: upright chain, horizontal barrel chain, serpent chain — a plan uses the subset its posture needs |
| `limb_sets` | Each leg/arm set: role, chain template, its own length-scale key, and its contact type |
| `tail` | The tail chain **and its role**: `appendage` or `body` (§4.2 — this distinction drives the slider rules) |
| `locomotion` | The required gait set and which animation layers may be imported from other plans |
| `sockets` | This plan's instance of every socket it supports: bone, position rule, accepted part kinds |
| `slider_policy` | Per canonical slider: shared value, per-plan instance, or unsupported on this plan |
| `export` | How the plan maps to each export profile, and what the profile must report losing |

## 3.2 The plan table

| Plan | Legs | Rig in brief | Pelvis / spine | Locomotion | ± Wings |
|---|---|---|---|---|---|
| `plan.quadruped_taur` — **centaur** | 4 | Upright humanoid torso on a horizontal equine barrel; foreleg pair at the barrel's front, hindleg pair at its rear; tail chain at the rear | `Pelvis` is simultaneously locomotor root, torso base, and barrel junction; upright spine chain rises from it; a plan-specific barrel chain runs backward to a `RearPelvis` | Quadruped gait set (walk / trot / gallop / turn / lie) with humanoid upper-body gestures layered on top | Wing sockets instance on the humanoid upper back |
| `plan.quadruped_feral` — **true quadruped** | 4 | Horizontal spine; forequarters and head/neck at the front; **no upright humanoid torso**; forelimbs are legs, not arms | The pelvis is the *rear* pelvis; the axial chain re-aims horizontal and the chest becomes forequarters | Quadruped gait set; no arm-gesture layer exists to import | Wing sockets instance at the withers, between the forequarters |
| `plan.biped` — **biped / digitigrade** | 2 | The AnthroForge core rig: pelvis → spine → chest → neck/head, arms, legs; optional tail chain; plantigrade or digitigrade leg module (§3.3) | `Pelvis` is root and leg junction; spine vertical | Biped set (stand / walk / run / sit / …); digitigrade changes contact geometry and gait timing, not plan identity | Wing sockets instance on the upper back — the reference placement all other plans' instances are described against |
| `plan.naga` — **serpent** | 0 | Upright torso above the pelvis; below it, a long segmented serpent column **is** the lower body; leg chains carry no body geometry | `Pelvis` is root and serpent junction, expressed in the mesh as a fitted girdle/collar; upright spine above it is the shared chain; the serpent chain continues the axis downward/backward | Serpent set: idle sway, slither, turn, coil, swim; root translation is *coupled to* lateral undulation and ground contact so the body does not hover | Wing sockets instance on the upper back, behind the shoulders; wing clearance must be solved against the raised serpent column in coil poses |

Wings appear in every row because they are not a row: they are the modifier defined in §3.5, applicable to all four plans.

## 3.3 The biped plan and the digitigrade module

`plan.biped` is the plan the existing 36-bone v2 core already implements: pelvis/spine/chest/neck/head, clavicle–arm–hand chains, leg/foot chains, plus module extensions (tail, wings, ear chains, jaw) when parts are equipped.

Leg style is a **module inside the plan**, not a plan of its own:

- `leg_style: plantigrade` — hip → knee → ankle → foot, foot flat on the ground.
- `leg_style: digitigrade` — the module inserts the hock segment (per APP_BLUEPRINT §8.1's digitigrade hock extension), re-seats the joint positions derived from the morphed mesh, and shifts ground contact to the toes. Ankle/hock geometry, the leg's region masks, and gait contact timing change; the character's plan, upper body, and slider space do not.

## 3.4 Root height and ground contact — per plan, on purpose

The centaur ground-contact failure in §2.1 is the reason this is a plan field and not an implementation detail.

- **Biped:** two-contact model; root height from the active leg module (plantigrade and digitigrade solve differently).
- **Quadruped (both subtypes):** four-contact model. Foreleg length and hindleg length are **independent plan values with independent calibration offsets**. Root height and barrel pitch are solved from both pairs. A short fore pair pitches the barrel; it never silently shortens the hind pair.
- **Naga:** a distributed-contact model. Contact is a set of intervals along the ventral serpent chain, not points. Root height, undulation phase, and forward root translation are solved together; in the coil state the contact patch is the coil's underside and the “root height” is the coil stack height.
- **Export honesty:** no target engine in our profile set runs this solver. It is baked into exported joint positions and animation clips, and the export report says so.

## 3.5 Wings — the cross-plan modifier

A wing is a **part family** in the APP_BLUEPRINT §3.4 sense, with three additions: a bone-chain template, a state set, and a plan-socket contract.

**Sockets.** The canonical sockets already exist: `wing.L` and `wing.R` (§3.5 of the blueprint). Each plan provides its own *instance* of them — same socket name, plan-specific bone and placement rule (upper back on biped/taur/naga; withers on feral). A part is compatible only if socket, plan, and fit region all match (§4.3).

**Chain template (reference).** Part families may declare fewer or more bones, but the reference template is deliberately richer than Bento's:

```
WingRoot  (shared, parented to the plan's chest/withers node)
 ├─ Wing1.L → Wing2.L → Wing3.L → Wing4.L → Wing5.L      (main chain)
 │     ├─ WingFan1.L  (branch at the Wing3 “wrist” — membrane fingers / primary group)
 │     └─ WingFan2.L  (branch at Wing4 — secondary group)
 └─ (mirrored for R)
```

- **Membrane wings** use the fan branches as finger rays and may declare more of them in their own part record.
- **Feathered wings** use the fan branches as feather-*group* bones (primaries / secondaries / coverts); per-feather bones are not required for the group bones to fan and overlap convincingly.
- **Skin mode is `own-weights`** (blueprint preference): the wing carries skinning to the shared skeleton. `rigid` is reserved for folded-wing shells and ornaments that genuinely never bend.

**States, owned by the part family, not by locomotion:** `folded`, `relaxed`, `spread`, `flap`, `glide`, `display`. Locomotion sets may *request* a wing state (a galloping centaur folds; a gliding biped spreads) but never define one. No state is assumed to exist by default — the Bento lesson of §1.7 applies internally too: an unanimated wing does nothing.

**Wing sliders** (span, root offset, fold angle bias, feather/finger spread) are canonical sliders whose *values* are shared across plans; their instances are re-derived per plan because the socket moved.

## 3.6 Plan switching — the migration algorithm

Switching plan is a defined operation on the character record, in this order:

1. **Select the plan template** and instantiate its rig configuration from the canonical rig definition.
2. **Carry the shared slider vector unchanged** (head, expressions, species structure, materials — §4.1).
3. **Load this plan's stored slider instances** (§4.2), or derive first-time instances from the canonical anchors. Plan-local values are written back under the plan's own key; one plan's belly never overwrites another's.
4. **Re-derive joint positions** from the morphed mesh under the new plan's axial/limb configuration (blueprint rule: sliders never encode joints; joints are derived at build/export).
5. **Validate parts** against the new plan (§4.3). Incompatible parts are *unequipped to the character's inventory, never deleted*, and listed in the switch report.
6. **Attach the plan's locomotion set** and discard the old plan's locomotion bindings (§4.4). Portable layers (head/face, gestures where arms exist, wing states) are re-validated for root height and clearance.
7. **Run the ground-contact solve** (§3.4) and the plan's pose-suite validation.
8. **Report**: parts unequipped, sliders instanced for the first time, sliders unsupported on this plan, and any export-profile consequences.

## 3.7 What the pelvis means — the quiet centre of the design

Every plan keeps a `Pelvis` root, because the character's identity, root motion, and the `pelvis.genital` socket all hang off it. But the pelvis's *job* changes, and the plan record says which job:

- **Biped:** root + leg junction. The familiar case.
- **Taur:** root + torso junction + barrel junction. In the mesh it needs a fitted barrel collar at the junction — the centaur equivalent of the naga's girdle problem.
- **Feral:** rear pelvis only. The “junction” role moves to the forequarters.
- **Naga:** root + serpent junction, expressed as a fitted girdle/collar part region. The pelvis carries no leg geometry at all.

---

# Part IV — Compatibility rules

## 4.1 Carries across all plans unchanged

These live in the shared character record and are never re-authored per plan:

- Character identity and share-code structure.
- Species preset *structure* (a preset is a slider vector + part choices; its plan-specific instances are resolved at apply time).
- **The full head slider vector** — the 31-slider head system including the seven brow sliders — and the layered skull → muscle → tissue construction, on every plan that carries the shared head (all four; on feral the head sits at the front of a horizontal neck, which changes its *placement*, not its shape space).
- **Expression masters and fine sliders**, as vectors with species gain tables. Plan gains may be applied to head *orientation* on feral; the expression vectors themselves do not fork.
- **The universal teeth arcade** and jaw mechanics.
- Eye, ear, nose, muzzle, and crest parts, wherever the plan's socket table provides the socket.
- Materials, palettes, and markings *semantics* (which layers exist and what they mean — their region maps are per-plan, §4.2).
- Wing part identity and wing slider values (§3.5).

## 4.2 Needs a per-plan instance

A canonical slider record is semantic (MAKEHUMAN_OMNIVERSAL: ID + region mask + endpoint anchors + range + provenance). Its *instance* — the actual delta field on a particular body — is per base. Body plans add a second instancing axis: **per plan**. The rules:

| Canonical slider / system | Biped | Taur | Feral | Naga |
|---|---|---|---|---|
| `body.belly.protrusion` and torso mass | Abdominal instance | **Splits in two**: human-torso belly instance *and* equine-barrel belly instance, driven from one canonical value by plan-declared weights | Barrel/ribcage instance | No abdomen exists; maps to a **ventral serpent-girth** instance or is marked unsupported and superseded by `serpent.girth` |
| Pelvis / hip sliders | Root + leg junction instance | Root + barrel-junction instance; width drives the collar fit | Rear-pelvis instance | Root + serpent-junction instance; width drives the girdle fit |
| Torso length | Vertical spine instance | Vertical torso instance **plus** barrel-length instance | Horizontal axial-length instance | Torso instance **plus** serpent-column length — a separate canonical slider (`serpent.length`), not a stretched torso |
| Leg length / muscle / foot sliders | Leg-module instances (plantigrade/digitigrade variants) | **Separate foreleg and hindleg instances** — never coupled (§3.4) | Separate foreleg/hindleg instances | **Unsupported.** No instance exists; the values are stored, inert, and restored on switching back |
| Tail length / girth / taper | Appendage instance | Appendage instance | Appendage instance | **Body instance.** On naga the tail chain is the body: these become primary body sliders (length, girth, taper, coil bias, undulation amplitude) with their own delta fields — never a silent reuse of the appendage deltas |
| Fur | Region maps for the biped body | New region maps: torso regions shared, barrel regions new | New region maps throughout | Same fur *profile* semantics; ventral/dorsal serpent regions are new maps |
| Markings layers | Biped maps | Barrel maps added | Full re-map | Serpent banding/ventral maps added |

**Storage rule:** instances are keyed `instances/<plan-id>/<slider-id>`, beside the existing per-base instancing. A slider with no instance for the active plan and no derivation rule is *unsupported on this plan* — greyed in the UI, named in the switch report, never silently zeroed.

## 4.3 Parts: socket match is necessary, not sufficient

The APP_BLUEPRINT part record gains one backward-compatible block:

```json
"plan_fit": {
  "plans": ["plan.biped", "plan.quadruped_taur", "plan.naga"],
  "socket_by_plan": { "plan.naga": "wing.L", "plan.quadruped_feral": "wing.wither.L" },
  "variant_by_plan": { "plan.naga": "wing_membrane_naga.glb" },
  "excluded_plans": ["plan.quadruped_feral"]
}
```

Compatibility rule — a part may equip only if **all** hold:

1. The plan's socket table provides the socket the part needs.
2. The plan is listed in `plan_fit.plans` (or the part declares plan-agnostic fit *and* passes the fit-score check for this plan).
3. The part's fit regions exist in the plan's region map.
4. No `conflicts` entry fires under this plan's geometry (conflict checks are re-run per plan — a mane that clears a biped's wings may not clear a naga's coil).

Consequences worth stating plainly:

- **Leg clothing and leg parts are excluded on naga** — there is no leg to fit, and “hide the item” is not compatibility.
- **Barrel parts** (tack, barrel armour, saddle-region wear) are excluded on biped and naga even though a generic `back` socket exists on all plans. Socket-name equality is not fit.
- **`pelvis.genital` is bound per plan.** The socket name is canonical; its position rule follows the pelvis's job in that plan (§3.7). A genital part needs a plan instance or a plan-locked declaration; the biped position is never assumed.
- **Tail-tip parts on naga are body-tip parts**, with body-part cost and safety treatment, not accessory treatment.
- A part may ship **plan-specific mesh/weight variants** under one part ID (`variant_by_plan`); the character record stores which variant is equipped.

## 4.4 Animation compatibility

- **Locomotion never carries across plans.** Not “retargets poorly” — is not carried. Each plan binds its own set (§3.1 `locomotion.required`).
- **Portable layers:** head/face animation on all plans; arm gestures on biped, taur, and naga (feral has no arms to gesture with); wing states on any winged plan, subject to clearance validation against that plan's geometry (horns, tail, raised serpent coil).
- **Appendage tail animation is not portable to naga.** A biped's tail-sway cycle and a naga's slither cycle are different categories of motion that happen to share a chain template.
- Every imported layer is re-validated for root height and ground contact under the active plan before it is accepted.

---

# Part V — The Bento export profile

## 5.1 Recommendation

**Ship an opt-in SL DAE “Bento names” profile (`dae-sl-bento`) that maps AnthroForge's canonical core and module bones to the final Bento names, emits partial skeletons containing only the bones each export actually uses plus deliberate ancestors, includes joint positions only for plan/part bones that need them, and reports every baked, merged, or dropped chain — and never make Bento naming the internal rig.**

## 5.2 Name mapping (core and modules)

| AnthroForge | Bento export | Notes |
|---|---|---|
| `Pelvis` | `mPelvis` | Root of every export |
| Spine chain | `mSpine1`–`mSpine4`, `mTorso`, `mChest` | Extra internal spine resolution is distributed across the four Bento insertions; the profile reports any segment it had to collapse |
| `Neck` / `Head` | `mNeck` / `mHead` | — |
| `Jaw` | `mFaceJaw` | Tongue/lower-lip dependents follow Bento's parenting |
| Ear chains | `mFaceEar1*`, `mFaceEar2*` per side | Internal chains longer than two segments merge distal segments; reported |
| Eyes | Standard eye bones; additional/alternate eyes → `mFaceEyeAlt*` | Per the guide's distinction between viewer-controlled and alt eyes |
| Face detail modules (brow, lids, cheeks, lips, nose, tongue, teeth) | The corresponding `mFace*` bones | Only when the character actually carries those modules; otherwise facial motion is morph-baked and the report says so |
| Arms / hands | Standard SL arm chain; finger bones only if a hand module is equipped | The 36-bone core has no fingers; nothing is invented at export |
| Biped legs | Standard SL leg chain | Digitigrade hock segment merges into the ankle/foot span; the *shape* survives via joint positions |
| Taur/feral forelegs | Standard SL leg chain (repositioned) | Matches how SL centaurs are actually built (§2.1) |
| Taur/feral hindlegs | `mHindLimbsRoot`, `mHindLimb1–4` per side | The hind root is always emitted with its chains — a partial export that omits it reproduces the historical hind-limb collapse |
| Tail (appendage role) | `mTail1`–`mTail6` | Internal chains of 5–8 segments compress or pad to six |
| Serpent column (naga) | `mTail1`–`mTail6` | Internal 12–20 segments aggregate to six — the single largest fidelity loss in the profile; reported with the aggregation ratio |
| Wings | `mWingsRoot`, `mWing1–4` per side, `mWing4Fan` per side | Internal `Wing5` merges into `Wing4`; extra fan/finger branches merge into the single `mWing4Fan` or bake; every merge is a report line |
| Genital chain | `mGroin` where a compatible module exists, else rigid/baked | Reported per part |

## 5.3 Profile rules

1. **Partial by construction.** A full-body export emits the plan's skeleton. A *part* export (tail only, wings only, a taur lower-body add-on) emits only the bones that part uses, plus ancestors included deliberately and listed in the report. Stray moved ancestors are a validation failure — §1.7's wearer-deformation accident is designed out here.
2. **Joint positions are opt-in per bone.** They are emitted for plan-defining bones (hind chains, serpent/tail chains, wing roots, repositioned forelegs) whose Bento defaults are wrong for the plan, and withheld elsewhere. The report lists every bone carrying a position override.
3. **Joint-position fallback for centaurs.** Because hind-limb joint positions have a documented history of collapsing in the SL uploader (§2.1), the taur profile offers a companion **deform/reset animation package**: a neutral background animation plus the deform clip that establishes hind positions. The export report states which mechanism a given package relies on.
4. **Hard SL limits enforced:** ≤110 recognised joints, ≤4 influences per vertex, weights normalised, ≤8 material slots per mesh (per APP_BLUEPRINT §11.3). Counts are computed *after* mapping, not before.
5. **Morphs bake.** As with generic DAE, slider shape is baked into the exported mesh; the report states this. Bento bone *positions* derived from the morphed mesh are emitted as joint positions where rule 2 allows.
6. **The DAE is not the whole avatar.** SL mesh upload carries no usable locomotion. Every plan export ships a companion **animation manifest** naming the required AO set (plan locomotion, wing states, neutral reset) so a package is never silently missing the animations Bento does not provide by default.
7. **Naga packages include the alpha requirement.** SL cannot delete the wearer's legs; the export bundles or references the leg-hiding alpha asset and states the girdle/collar junction part as required, per §2.3.
8. **Bind-rotation warning.** Quadruped practice in SL is to reposition joints, not rotate bones in the armature, because rotated bind joints produce upload/animation weirdness. The profile warns when a plan's SL-bound chains carry non-identity bind rotations.

## 5.4 Per-plan export consequences

| Plan | What survives | What is lost or hacked — stated in the report |
|---|---|---|
| Biped | Near-lossless core mapping; tail/wings/face modules where equipped | Finger detail exists only with a hand module; face detail only with face modules |
| Biped + digitigrade | Leg shape via joint positions | Hock segment merged; SL shape sliders may move the repositioned joints and break the digitigrade stance |
| Taur | Hind chains map onto real Bento bones — the best-supported non-biped plan | Fore/hind independence cannot survive SL's slider coupling: lengths are baked as joint positions, and wearer shape changes can break ground contact exactly as in §2.1; deform-animation fallback offered |
| Feral | Front pair → standard legs, rear pair → hind chains, spine insertions carry the horizontal trunk | Arm chains unused and omitted; humanoid upper-body content has no target; custom AO is mandatory, not optional |
| Naga | Torso and head map cleanly; serpent column maps onto the tail chain | **Column resolution collapses** (internal segments → 6); legs hidden by alpha, never removed; root locomotion remains the avatar's — slither quality is bounded by the AO, not the mesh |
| Any plan + wings | Main chain and one fan branch map directly | Extra main segment and extra fingers/feather groups merge or bake; true fold fidelity is the known casualty (§2.4); wing AO clips are required — an exported wing with no animations is a rigid-looking wing |

## 5.5 When to choose animesh instead

Only when the construct is **not the character's body**: a companion creature, a rideable, an independent winged construct, or a wing/serpent mechanism whose custom skeleton must not fight other Bento items on the same bones. The costs are structural — no wearer-shape response, scarce attachment slots — so animesh never substitutes for a body-plan export.

---

# Part VI — Our 36 bones vs Bento's skeleton: the honest trade

AnthroForge's v2 core is 36 bones (pelvis/spine, neck/head, arms, legs, plus the prototype's short wing and tail chains and genital chain), extended by modules only when parts are equipped — jaw, ear chains, tongue, tail 5–8, wing chains per part spec, digitigrade hock. Bento is a fixed, maximal skeleton: the legacy avatar bones plus 106 additions, present whether or not a given avatar uses them.

**What the small canonical rig gains:**

- **Authoring and runtime economy.** Fewer bones to weight, pose, validate, and animate; module chains exist only when a part needs them.
- **The right resolution where plans need it.** A naga column of 12–20 segments, wing fingers beyond a single fan branch, a dedicated barrel chain — none of these exist in Bento at any price, and all of them are ordinary module extensions here.
- **Derived joints.** Joint positions are derived from the morphed mesh at build/export. The rig follows the character's actual shape instead of a fixed bind pose negotiated with shape sliders.
- **Name and schema sovereignty.** Canonical slider records, part records, and plan records are ours; no SL shape-system behaviour leaks into the character model.
- **Natural partial exports.** Modules map to Bento's partial-skeleton allowance cleanly — a part exports its own chain and nothing else.

**What it loses, all of it at the SL boundary:**

- **Ecosystem compatibility.** Bento face, finger, wing, tail, and hind bones are understood by every SL viewer, AO, and animation already in the world. AnthroForge characters get that compatibility only through the §5 mapping, only for chains that have Bento equivalents.
- **Facial and hand richness by default.** Bento's face rig exists in every export target; ours exists only when the character carries the modules.
- **Resolution at mapping time.** Serpent segments, wing fingers, ear-chain segments, and spine segments beyond Bento's insertions are merged or baked on export. The internal rig is richer than anything Bento can receive.
- **Shape-system interplay.** SL shape sliders reposition Bento bones for free, including on other creators' content worn with ours. Our derived-joint guarantee does not survive a system where animations with translations can override slider positions.
- **The one-skeleton ceiling.** SL still has one avatar skeleton. Our plan cleanliness — separate fore/hind solves, distributed naga contact, per-plan socket instances — is baked into meshes, joint positions, alphas, and AO packages on export. It does not transfer as *behaviour*.

**Net position:** internally, plans are configurations of a small rig with exactly-placed extensions. For SL, Bento is a *target vocabulary* we translate into — fluently for bipeds, well for centaurs, and with named, reported losses for nagas and elaborate wings.

---

# Part VII — Validation gates for plans

A plan or plan export is not done until these pass (extending APP_BLUEPRINT §8.5):

1. **Plan-switch round trip.** Biped → taur → naga → biped restores each plan's stored instances exactly; shared vector untouched; unequipped parts listed and recoverable.
2. **Ground contact.** Per plan: biped two-contact, quadruped four-contact with fore/hind lengths varied *independently* (the §2.1 regression test), naga distributed contact in slither and coil with no visible hover.
3. **Pose suite per plan.** Taur: rear, paw, lie with torso gestures layered. Naga: full coil, raised-coil with wings spread (clearance), swim. Feral: lie, turn. Wing fold clearance against horns, ears, tail, and serpent column on every plan.
4. **Junction fit.** Taur barrel collar and naga girdle checked across the pelvis-slider range for seam gaps and clipping.
5. **Export audit (Bento profile).** Joint count after mapping ≤110; every emitted joint position listed; partial exports contain no unintended ancestors; merged chains enumerated; naga package includes alpha + animation manifest; taur package states its hind-position mechanism (joint positions vs deform animation).

---

## Appendix — Terminology

- **Plan**: a rig configuration record (§3.1). Selected, never slid.
- **Plan instance (of a slider)**: the per-plan delta field/mask realising a canonical slider on that plan's body (§4.2).
- **Socket instance**: a plan's concrete placement of a canonical socket name (§3.5, §4.3).
- **Appendage role / body role (tail)**: whether the tail chain is an accessory or the lower body itself. The role flag in the plan record drives slider instancing (§4.2), part treatment (§4.3), and animation portability (§4.4).
- **Bento profile (`dae-sl-bento`)**: the opt-in SL DAE export profile of §5. A translation, never the internal rig.
