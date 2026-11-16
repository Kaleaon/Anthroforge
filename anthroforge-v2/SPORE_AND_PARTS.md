# Spore and Parts-Driven Creators — Teardown of the Parts-First Canon, and Rules for AnthroForge

*Design research, Nov 12, 2026. Commissioned by Joe: "work on individual parts, or grab info and design stuff from Spore or other games." Companion to CREATOR_LESSONS.md (the slider/preset canon) and HEROFORGE.md (the commercial parts library). This doc covers the system AnthroForge's swappable-parts design most resembles and had never been torn down: **Spore's Creature Creator** (Maxis, 2008), plus quick passes at Impossible Creatures, Monster Hunter Stories' gene system, and Kerbal Space Program's attach nodes. Method: web research — SporeWiki documentation, the SIGGRAPH literature, GDC-era interviews and postmortems. Every factual claim is sourced; URLs at the end.*

---

## 1. Spore Creature Creator (Maxis, 2008) — the parts-first canon

### 1.1 The body is a vertebra chain wearing a metaball skin

There is no base mesh in Spore. A creature starts as a blob organised around a **spine of vertebrae** floating over a pedestal, and the body you sculpt *is* that chain:

- **Vertebrae are the primitive.** Each vertebra can be selected and fattened or thinned individually; the chain can be lengthened (stretch the body and segments are added), curved, and extended at either end to form necks and tails. Chaim Gingold (lead designer of the editor) arrived at this by watching artists start characters from "bean shapes" — he gave the bean pull-points, "and they looked like vertebrae, which also helped the animation system… You see that spine and you go, 'oh, it's a creature.'" The spine is what Gingold called the creature's **deep structure**: it is simultaneously the sculpting handle, the skeleton the animation system reads, and the thing that makes any arrangement of parts read as an animal.
- **The surface is implicit.** Body and limbs are **metaballs** — an implicit surface that re-triangulates as you edit (Hecker's team used ear-clipping triangulation because the Marching Cubes patent was still in force). Stretch a limb or spine and more metaballs are inserted to keep the surface smooth; shrink or grow individual balls to taper or bulk a section. There is no topology to break, no UV seam to tear, no weight map to repaint — because none of those exist yet. They are all *derived later, procedurally* (§1.6).
- **Consequence.** The body plan space is enormous in silhouette (worms to nine-legged horrors) and narrow in kind: every Spore creature is, structurally, a tube with parts on it. There is no independently articulated head, no layered anatomy, no hands unless a grasper part provides them. That narrowness is the price of the freedom in §1.2 — remember it when we price free-attach in §2.

### 1.2 Rigblocks: parts attach anywhere, and bring their own deformation grammar

Detailed anatomy — mouths, eyes, hands, spikes — is not metaball work. Those are **rigblocks**: hand-authored part meshes that snap onto the body surface **anywhere the player drops them**. Each rigblock carries predefined degrees of freedom exposed as morph handles (arrows and rings around the selected part): scale it, stretch it, rotate it, elongate it — within limits the part's author defined. A part is therefore not a fixed mesh; it is a small parametric family, closer to one of our slider records wearing a mesh than to a static prop.

- **Limbs are the special case.** A limb attaches to the body as a chain: you can add or remove joint nodes along it (Ctrl-drag detaches/attaches a node), bend it, and terminate it with a grasper or a foot. The limb's *placement* is free; its *structure* is a joint chain the animation system can reason about.
- **Symmetry is the default physics of placement.** Parts dropped off-centre are mirrored bilaterally; centreline parts stay single. This is not a per-part property — it is the editor's placement mode (see §1.4 for what happened when they relaxed it).
- **Palette organisation.** Seven categories — **Mouths, Sensory Organs (eyes/ears/noses), Limbs, Hands (graspers), Feet, Weapons, Details** (feathers, wings, leaves…) — holding **228 functional parts** at launch in the full game; Will Wright's pre-release count of "about 400 creature parts" includes the wider pool, and the *Creepy & Cute* pack and the Dr Pepper *Bot Parts* pack added more. Within a category, parts sit in **columns of increasing capability**: leftmost is basic, rightmost is the strongest version — and the most expensive (§1.3, §1.5).

### 1.3 Parts are function: the stat system

Every part carries gameplay statistics, and the creature's character sheet is **computed from its parts**, live, in the editor:

| Stat group | Stats (levels 1–5 unless noted) | Granted by |
|---|---|---|
| Abilities | Sight (binary), Sneak, Jump, Glide, Graspers (binary), Mating Call (binary), Sprint | eyes; detail parts; feet; wings; hands; all mouths; feet |
| Attack (max 20) | Bite, Charge, Strike, Spit | all mouths (Bite); hooves & horn-like weapons (Charge); hands & spikes (Strike); spit weapons (Spit) |
| Social (max 20) | Sing, Dance, Charm, Pose | mouths (Sing); feet (Dance); fur/feather/accessory details (Charm); hands (Pose) |
| Speed (max 5) | — | feet primarily |
| Health (max 5) | — | various parts; also scales with brain size |
| Diet | carnivore / herbivore / omnivore | **determined entirely by which mouth you attach** |

Mechanics that matter for us:

- **Cost tracks capability.** Every part has a DNA-point price that "reflects their efficiency and effect on the creature's rating" — the rightmost column's Level-5 mouth costs 250 DNA where a Level-1 mouth costs 15–25 (SporeWiki's per-part tables). Capability, price and palette position are one and the same signal.
- **Levels don't stack; the best part speaks for the creature.** Each ability shows one level — the level of the strongest part granting it. Bolting on a second, weaker mouth doesn't raise Bite. (Community-documented behaviour; the editor's stat bars are per-ability levels, and per-part levels are fixed per part.)
- **Form does not feed stats.** Lengthening a leg does not make the creature faster; Speed lives in the *foot part chosen*, not in the geometry. A mouse-sized creature with a Level-5 mouth out-bites a five-ton elephant-thing with a Level-1 mouth. Maxis deliberately severed the stat system from the sculpting system: geometry is expression, parts are function.
- **One hard validation gate.** Every creature must have a mouth; **a creature without a mouth cannot be saved.** Not a warning — a refusal. It is the only content rule the editor enforces absolutely, and it is enforced because the mouth is load-bearing for the game (diet, bite, sing, mating call all hang off it).

### 1.4 Symmetry, then asymmetry — shipped late, one-way

At launch, bilateral symmetry was unconditional. **Patch 5 (v1.05, July 2009)** added asymmetry as a modifier-key behaviour: hold **A** while dragging a part and it separates from its mirror partner and moves independently; A+drag from the palette creates a new asymmetric part; Ctrl+F flips a part's handedness. Two details worth stealing attention:

- **Once a part is asymmetric, it cannot be converted back to symmetric.** Asymmetry in Spore is a one-way edit, not a state — a data-model decision (the mirrored pair is dissolved) that players had to live with.
- It shipped **a year post-launch**, into every editor (creatures, vehicles), and immediately generated its own glitch ecology (parts flipping in test drive, asymmetric cell-state corruption). Freedom retrofitted onto a symmetry-assuming system is visibly more expensive than freedom designed in. (Compare Saints Row in CREATOR_LESSONS: asymmetry as a launch feature, but with uneven slider coverage — the two failure modes bracket the right answer.)

### 1.5 Two budgets, not one

Spore runs **two independent economies** on the same build, and separating them is one of its most transferable ideas:

1. **DNA points — the capability budget.** Parts cost DNA (the standalone Creature Creator gave a 2,000-DNA budget; in the Creature Stage you earn DNA and spend it in the editor). This budget prices *power*: it stops a starting creature from wearing all Level-5 parts.
2. **The complexity meter — the technical budget.** Every part adds complexity points; the meter caps at **138 points** for a creature (148 for an outfitted one — community-documented figures), and at the cap, further parts turn red and cannot be added. This budget prices *geometry/system load*, and it doubles as a **sharing gate**: over-complexity creations can't be uploaded to the Sporepedia.

WWE's parts-points pool (CREATOR_LESSONS R5) is the complexity meter's descendant. Spore's extra lesson is the split: *what a part does* and *what a part costs to render/simulate* are different currencies, and conflating them produces either pay-to-win looks or ugly-but-cheap power.

### 1.6 Animation: the morphology problem, solved by semantics

Spore's hardest problem is the one our retargeting work keeps hitting: **how do you animate a skeleton that did not exist when the animation was authored?** Maxis's answer, published as a SIGGRAPH 2008 paper (Hecker, Raabe, Enslow, DeWeese, Maynard, van Prooijen, "Real-time Motion Retargeting to Highly Varied User-Created Morphologies", *ACM Transactions on Graphics* 27(3)), has three layers:

- **Authored motion is stored morphology-independently.** Animators pose and keyframe in a familiar tool, but they also **annotate the semantics** of the motion — which element is the actor, what it contacts, what the stylistic relationships are. The system records the animation in a generalised form: structural relationships + style, not joint curves for a specific rig.
- **At runtime, the generalised motion is specialised onto the actual creature.** Semantic goals become pose goals fed to a robust IK solver, which finds the pose *this* body — with its leg count, neck length, and mouth placement — needs to perform "pick fruit from a tree" or "dance a jig". Skin weights for the generated mesh are likewise derived automatically: each vertex's weights come from which implicit function (which body part) describes it. Nothing is hand-weighted because nothing *can* be.
- **Locomotion is generated, not authored.** Gait derives from the legs the player placed — count, position, length. Dan Moskowitz (lead gameplay engineer): the system could produce "a fully animated nine-[legged] creature, all of whose legs touch the ground and it moves naturally." Feet planting on the ground is a *solver output*, not an animator's hope.
- **The editor performs the creature back at you.** In Test Drive the creature idles, walks, looks at its own hand, smiles, vocalises through its mouth part. Animation is not a preview feature bolted on; it is the editor's primary feedback that your assemblage is *alive* — and it works on every legal build, because the animation system accepts morphology as input rather than as a constraint.

### 1.7 Paint: even the texture is procedural

Paint Mode applies colour and pattern procedurally — a base, a coat and a detail layer, generated onto an auto-built texture atlas. The player picks palettes and pattern styles; the system does the UVs. Like the mesh, the skin is *derived from parameters*, which is why a creature's full description stays tiny (§1.8) and why no Spore creature has ever had a broken UV seam.

### 1.8 Sharing: the creature is a PNG

Spore's sharing format is the most elegant in this entire research series:

- **The data is minuscule because the creature is a recipe.** Gingold: "The picture is 20k. The creature is 4k — it's incredible." A creature is a few kilobytes of parameters — spine definition, part IDs, placements, transforms, paint choices — because everything else is regenerated by the receiver's copy of the procedural systems.
- **The recipe is embedded invisibly in the thumbnail PNG.** The creature's save/share artefact is an ordinary-looking PNG image of the creature with the creature data encoded inside it. Sharing is: post the picture anywhere. Importing is: **drag the PNG into the editor or the Sporepedia** and the creature resurrects, fully editable. No codes to transcribe (contrast Elden Ring in CREATOR_LESSONS), no file-format literacy, no separate download — the preview *is* the payload.
- **Sporepedia + pollination.** Uploaded creations went to the Sporepedia, and the game itself downloaded other players' creatures in the background to populate your world — the library came to the player. (Patch 5.1 also added a cheat to export creatures in **Collada** format for Maya — even Spore eventually grew a DAE door, as an escape hatch, not the front door.)

---

## 2. What "attach anywhere" actually costs

Spore is routinely misread as "free placement works, just do that." It works *because Maxis paid for it in four currencies* — and the bill is the lesson:

| Currency | What Maxis paid | What it bought |
|---|---|---|
| **Substrate** | The body is a metaball tube on a vertebra chain — no arbitrary base meshes, no separate head, no layered anatomy, one body plan family | A surface that is always attachable, always skin-able, always re-meshable |
| **Procedural everything** | Auto-triangulation, auto-UV/atlas, auto-skin-weights, semantic retargeting + IK, generated gait, procedural paint — years of R&D (a SIGGRAPH paper's worth on animation alone) | Zero per-part fitting labour; every legal build animates, textures and saves |
| **Budgets as governance** | DNA (capability) + complexity (technical) caps enforced in-editor; complexity also gates sharing | No moderation pass, no broken imports; the format polices itself |
| **Style absorption** | A soft, cartoony art direction where floating intersections and squashy joins read as charm | Intersection/clip sins that would be defects in a realistic creator are invisible |

**Against our socket model** (APP_BLUEPRINT §3.5, PARTS_STANDARD): sockets give anatomical guarantees Spore never attempts — an ear socket knows the skull's layered construction underneath, a jaw socket knows the teeth arcade and the hinge axis, a digitigrade leg socket knows the gait family. Spore cannot express "this part must align to a hinge" because it has no hinges; we cannot express "put a horn literally anywhere" because our parts carry fit regions and weights. The honest verdict is **both, partitioned by part class** — which is what the blueprint already does with its `free.1..4` slots (CREATOR_LESSONS R9, from Soulcalibur VI). Spore sharpens the partition rule:

> **Free-attach is safe exactly where the system can procedurally guarantee the consequences** (skinning, fit, animation). Spore guarantees them for *everything* by owning the whole substrate. We guarantee them for *socketed anatomy* by construction — so our free-attach tier must be restricted to part classes whose consequences we can guarantee by a weaker contract: a parent bone + a surface offset + rigid or inherit skinning (ornaments, horns, piercings, crest feathers). The moment a free-attached part needs its own weights, morphs or animation semantics, it must graduate to a socket.

The failure mode to avoid is SCVI's (free-attach with no substrate guarantees at all → reactive conflict patches). The failure mode at the other pole is a socket list so rigid that users can't put an earring where they want it. Spore + SCVI bracket the design space; our free-attach slots sit between them, and Spore tells us the price of moving the line: every part class we free-attach creates a procedural guarantee we must build.

---

## 3. Stats on parts: the verdict for AnthroForge

**Yes — parts should carry functional metadata. But our "stats" are descriptors, not game numbers.** Spore's stats exist because a game consumes them. AnthroForge's consumers are its own systems — animation, materials, export validation, the resolved character summary — and they are hungry for exactly the same kind of per-part semantics:

- **Jaw/mouth parts → diet + arcade parameters.** Spore's mouth *is* the diet field; our universal teeth arcade already works this way (Joe's ruling: one arcade, diet as morph axis — the character record's `teeth.arcade` params: canine/molar/incisor/wear/tusk). Spore validates the architecture: the functional data lives **on the part record**, and the character's diet is a *derived view* of the equipped jaw, not an independent character field that can disagree with the geometry. Extend the same pattern: jaw parts declare their hinge geometry and gape range — the animation/expression system consumes those, the way Spore's system consumes "this mouth bites at level N".
- **Leg/foot parts → locomotion profile.** A digitigrade leg part should declare `gait: digitigrade`, stance width, and IK hints; a plantigrade foot declares its own. This is the input our retargeting actually needs (§4) and Spore's gait generator runs on.
- **Sense parts → capability tags.** Eye parts already carry pupil variants in our design; add semantic tags (vision: slit-pupil/nocturnal…) that materials and expression systems can read. Ear parts: carriage range for the expression system (ears are half the emotional vocabulary on a furry head — see expression-system.md).
- **Detail/ornament parts → nothing.** Spore's Details category is mostly cosmetic (Charm aside) — a part is allowed to declare *no* function. The `function` block must be optional, or authors will fake values to satisfy the schema.

Three supporting mechanics to adopt with the metadata:

1. **Tier the library like Spore's columns.** Parts have capability tiers; DNA price, palette position and tier were one signal. Our `cost.points` already prices geometry — add an authoring-side **tier** (1 = basic, higher = more capable/expressive) so the parts browser can sort and users can read a part's ambition at a glance.
2. **The character sheet is a computed view.** Spore's stat bars update live as you attach. Our `character_load` already returns a "resolved summary"; make it include the **derived functional profile** (diet, gait family, complexity total, capability tiers) computed from equipped parts — never stored, never editable, always current. Impossible Creatures' "army analyzer" (§5.1) is the same idea as a dedicated readout.
3. **Best-part-wins is a display rule, not a data rule.** Spore collapses duplicates to a single level for gameplay clarity. For us, derived values that aggregate (e.g. total hearing range from two different ear parts under asymmetry) should aggregate by a *documented rule per field* — max, sum, or per-side — stated in the part schema, not improvised per consumer.

---

## 4. Procedural animation from morphology vs. our retarget problem

Our current approach (retarget-prototype work; Eldritch Foundry's stance lesson in CREATOR_LESSONS): author clips on one rig, retarget to other proportions, measure foot drift, correct. Spore's approach differs **in kind**, and it reframes what we should store:

- **We store animations as joint curves for a known skeleton; Spore stored them as semantic descriptions for an unknown one.** Hecker's system is the existence proof that the semantic layer is buildable: annotate at authoring time (actor, contact, gaze, style relations), specialise at runtime through IK. Our morphology varies far less than Spore's — one 36-bone rig family, parts and sliders on top — so full Spore-grade semantics is overkill. But the *direction* is right and cheap at our scale: **every clip in our library should carry a semantic sidecar** (end-effectors, contact phases, gaze targets, which bones are style vs. structure), recorded when the clip is authored or retargeted, so a solver — not hope — handles foot planting and reach on extreme proportions (bara orc stride vs. fennec stride).
- **Gait is the extreme case and should be generated.** Spore never authored a walk cycle for a nine-legged creature; it generated stepping from leg placement. Our version: stance presets own the leg configuration (the EF lesson), and the walk/run layer should be **procedural stepping over the stance** — stride length, phase offsets and footfall targets computed from the leg parts' locomotion profiles (§3) with IK planting — with authored clips reserved for upper-body/action performance where style lives. This inverts the usual budget: locomotion is the *least* authorable, most generatable layer, and it's the one our retarget measurements show drifting.
- **Acceptance criterion, stolen directly:** Moskowitz's nine-leg test becomes our bara test — *a build at any legal slider/part extreme idles and walks with feet planted and no manual fix-up*, or the animation system, not the build, is at fault. Test Drive is the UX form of the same rule: the editor must perform the character live (idle, walk, emote) as first-class feedback, because a creator whose output only animates after export is hiding its failures until the most expensive moment.

---

## 5. Quick passes: three more parts-driven systems

### 5.1 Impossible Creatures (Relic, 2003) — parts as two-donor inheritance

Five years before Spore, Relic built creature combination as **region-locked part inheritance from exactly two donors**: pick any two of 51 stock animals (76 with downloads), then choose, per body region (head, forelegs, hindlegs, body, tail, wings…), which donor's part the hybrid gets — or in some regions, whether it has that part at all. The marketing combinatorics: 40,000+ distinct creatures.

- **The Combiner Engine is the transferable artefact.** Relic documented it publicly: separate **skeleton combiner, geometry combiner, texture combiner and animation combiner** pipelines. The animation combiner is the remarkable one for 2003 — animations are broken down **per limb** and re-joined to match the hybrid's limb assignment, with a custom IK solution compensating for differing leg lengths so the creature walks on even ground. A chimp's arms bring the chimp's upright idle with them. *Animation dialect travels with the part.*
- **Abilities ride parts, stats are computed per region.** Keep the owl's wings or lose flight; take the rhino's head to get the ramming attack. Each stock animal publishes a full stat block (health, defence, speed, melee damage, size, sight radius), and the hybrid's numbers derive from which parts came from whom. The included **army analyzer** renders the derived stats back as a readout — design feedback as a feature.
- **The limits are the lesson.** Exactly two donors, fixed regions, no free placement, no sculpting. IC traded Spore's placement freedom for *combinatorial* freedom plus guaranteed-coherent results — every hybrid is assembled from parts that were authored as a working animal, blended by an engine whose whole job is coherence. For AnthroForge: this is our species-pole blending (CREATOR_LESSONS R3) at part granularity, and a direct ancestor of Eldritch Foundry's Lineage idea — a part can declare **two parent sources and a blend**, and the fit solver's job is IC's combiner job. It also legitimises per-part animation dialects: a tail part bringing its own sway parameters is IC's chimp-arms principle, domesticated.

### 5.2 Monster Hunter Stories — parts as genes (Monster Hunter Stories 1–3, Capcom, 2016–2026)

The monstie gene system is a parts system with **no geometry at all** — and that's why it's instructive. Every monstie has a **3×3 gene grid**. Genes are trait tokens (an active skill, a passive buff, a resistance), each tagged with an attack type (Power/Speed/Technical) and an element. Genes determine *everything* the monstie can do.

- **Transfer is free and (by Stories 3) non-destructive.** The Rite of Channeling moves genes between monsties; in Stories 1–2 the donor was consumed, in Stories 3 it is not — Capcom removed the sacrifice because it punished experimentation. Genes are never used up.
- **Position is meaning: bingo.** Three same-type or same-element genes in a row/column/diagonal grant a bingo bonus (+5% damage for that type/element per line, per guide documentation), lines stack, and threshold bonuses unlock at 2/3/5 completed lines. A wildcard "rainbow" gene completes lines it sits in. The grid makes **couplings visible and playable** — players optimise adjacency, not just inventory.
- **Transferable pieces.** (a) Our couplings (APP_BLUEPRINT §3.3 — tusk angle = f(JawWidth)) are currently invisible functions; bingo argues for surfacing *synergy hints* in the editor when a part/slider combination triggers a coupling ("this jaw + these tusks → tusk splay recalculated"). (b) Our preset/lineage inheritance can borrow the token model: a Titan-family variant inheriting slider-blocks from two parents is a gene transfer, and the UX should feel like channeling — drag a block, source keeps its copy. (c) Non-destructive transfer as a stated rule: moving anything between characters never consumes the source. (Our records already behave this way; MHS shows it's worth *promising* in the UI, because the consumed-donor version measurably discouraged play.)

### 5.3 Kerbal Space Program (Squad, 2013) — attach nodes as typed contracts

KSP builds spacecraft from parts, and its attachment system is the most *engineered* of the four — parts connect through **nodes**, and a node is a typed interface, not a point:

- **Node = position + direction + size class.** A stack node is defined as coordinates, an orientation vector, and a size (the stock classes run 0.625 m / 1.25 m / 2.5 m / 3.75 m). Nodes preferentially mate with their own size class; parts also carry an **attach-rules contract** (the five flags: stack, surface-attach, allow-stack, allow-surface, allow-collision) that declares *how* the part may be joined at all.
- **Adapters are first-class parts.** When size classes mismatch, you don't force it — you insert an adapter part whose whole job is bridging class 3 to class 2. Mismatch is a catalogue problem with a catalogue solution.
- **Symmetry is a placement mode.** The editor's symmetry tool is modal: mirror vs. radial, ×1–×8, applied at placement time (R cycles method, X cycles count); symmetrically placed parts form groups that move together until the user breaks the group. The part file knows nothing about symmetry.
- **Transferable pieces.** (a) **Sockets should carry size classes** (`ear` socket in S/M/L) and parts declare theirs; our fit re-solve (blueprint §6) is the "adapter" — naming it as one lets PARTS_STANDARD express class mismatch as data instead of as a solver surprise. (b) **Attach-rules flags** are the machine-checkable form of our socket contract: for each socket and part, `accepts: [stack|surface]`, `allowIntersect`, etc. — five booleans did for KSP what our prose socket descriptions must do for the fit pipeline. (c) KSP's root-part tree (a vessel is a tree; the root can be re-chosen) mirrors our character tree — and its lesson that *re-rooting is an editor operation, not a file migration* applies to our base-swap flow.

---

## 6. Rules for AnthroForge

Numbered SP-rules, continuing the CREATOR_LESSONS (R) and HEROFORGE (HF) series. Each: the do/avoid, the proof, the system it lands on (against APP_BLUEPRINT §3.4/§3.5 part record + sockets, and the in-progress PARTS_STANDARD).

**SP1 — Every part record carries a `function` block of semantic tags; geometry-only parts declare none.**
DO: jaw parts declare diet archetype + hinge/gait-relevant data; leg parts declare locomotion profile; eye/ear parts declare sense/expression tags. Consumers (animation, materials, export validation) read tags, never infer from names.
AVOID: function implied by category or filename — Spore's animation system worked because semantics were *specified at authoring* (Hecker et al.); inference is how you get a jaw that can't open.
*Proven by:* Spore (mouth = diet/bite/sing; Hecker semantics). *Lands on:* part record (§3.4 — add `function`), teeth arcade, expression system.

**SP2 — The character sheet is a computed view over equipped parts, shown live.**
DO: `character_load`'s resolved summary includes the derived functional profile — diet, gait family, total complexity, capability tiers — recomputed on every equip/unequip, with the aggregation rule per field documented in the schema.
AVOID: storing derived values in the character record, where they can disagree with the parts list.
*Proven by:* Spore's live stat bars; Impossible Creatures' army analyzer. *Lands on:* character record (§3.1), editor UI, MCP `character_load`.

**SP3 — Tier the parts library; price and position follow tier.**
DO: every part gets a capability tier; the parts browser sorts by tier within category; `cost.points` (technical) and tier (capability) stay separate fields — Spore's two budgets.
AVOID: one conflated "cost" that makes a heavy-but-basic part look equivalent to a light-but-expressive one.
*Proven by:* Spore's columns + DNA pricing vs. complexity meter (§1.3, §1.5). *Lands on:* part record, parts browser, export budget (extends CREATOR_LESSONS R5).

**SP4 — The share artefact is the picture: embed the share code in the preview render.**
DO: every character render/share image carries the `AF1-` payload embedded in the PNG (ancillary chunk), so the image *is* the import file — drag it into the app and the character resurrects, part-missing report and all (blueprint §3.2 degradation rules apply). Keep the text code for chat contexts.
AVOID: code-only sharing as the primary path — Spore proved in 2008 that the preview-as-payload has zero transcription friction, and Elden Ring proved the cost of making users move data by hand.
*Proven by:* Spore PNG creatures (4 KB recipe in a 20 KB picture). *Lands on:* share flow (§3.2), render/export pipeline.

**SP5 — Locomotion is generated from leg configuration; authored clips carry semantic sidecars.**
DO: stance + leg-part locomotion profiles feed a procedural stepping layer with IK foot planting; authored clips ship with semantic annotations (end-effectors, contacts, gaze) for the retarget solver. Acceptance test = the Moskowitz test: any legal build walks with feet planted, no manual fix-up.
AVOID: per-species authored walk cycles as the primary locomotion strategy, and retarget acceptance based on eyeballing instead of foot-plant/drift metrics.
*Proven by:* Spore (Hecker et al., SIGGRAPH 2008; generated gait). *Lands on:* animation library format, retarget pipeline, leg-part `function` block (SP1).

**SP6 — Free-attach is a part class with a substrate contract, not a placement free-for-all.**
DO: surface-attach (drop anywhere on a named body region) is allowed only for detail-class parts whose contract is parent bone + surface offset + rigid/inherit skinning; anything needing own weights, morphs or semantics graduates to a socket (extending the blueprint's `free.1..4`).
AVOID: SCVI's unsubstrated free-attach (conflict rules patched in after the scandal) — and the opposite failure, sockets so rigid that an earring needs a socket proposal.
*Proven by:* Spore (freedom bought with a procedural substrate, §2); SCVI (negative). *Lands on:* PARTS_STANDARD socket taxonomy, part record `skin.mode`.

**SP7 — Mandatory anatomy gates export, like Spore's mouth gates saving.**
DO: export validation refuses a build with no resolved head or no teeth-arcade resolution path, and warns (doesn't refuse) on cosmetic gaps — the gate list lives in the validation gauntlet alongside the GLB checks.
AVOID: silent export of structurally incomplete characters, and hard gates on anything aesthetic.
*Proven by:* Spore (no mouth → no save). *Lands on:* export validation (§11), QA gauntlet.

**SP8 — Symmetry is an editor placement mode; asymmetry is per-part data, and it is reversible.**
DO: mirror/radial placement modes at edit time (KSP's modal symmetry, incl. radial counts for back-ridge/detail rows); a part instance can be flagged asymmetric in the character record (`parts[].transform` + per-side entries), and un-flagging restores the mirror — asymmetry as *data*, fixing Spore's one-way edit.
AVOID: Spore's irreversible asymmetry (a 2009 patch's data-model debt) and Saints Row's partial asymmetry coverage (CREATOR_LESSONS R6).
*Proven by:* Spore Patch 5 (asymmetry, one-way — the caution); KSP (modal symmetry). *Lands on:* editor UX, character record part entries.

**SP9 — Make couplings visible: synergy hints in the editor.**
DO: when a part/slider combination activates a coupling (§3.3) or a known synergy (jaw width → tusk splay; ear part → expression range), the editor surfaces it as a hint on the affected control, MHS-bingo style — couplings the user can *see* get used; invisible ones get reported as bugs ("my tusks moved").
AVOID: silent cross-effects between controls.
*Proven by:* Monster Hunter Stories gene bingo (adjacency bonuses as a visible, playable system). *Lands on:* couplings (§3.3), editor UX, expression system.

**SP10 — Part variants may declare two parents and a blend.**
DO: a part record may carry `lineage: { from: [partA, partB], blend }` and let the fit solver/homology warp produce the intermediate — the part-level form of species pole-blending; animation-relevant parameters (tail sway, ear carriage) blend with the geometry, IC-style.
AVOID: treating every intermediate as a brand-new authored part (library growth becomes multiplicative instead of additive).
*Proven by:* Impossible Creatures' Combiner Engine (per-region two-donor inheritance, per-limb animation blending). *Lands on:* part record, homology warp (§6), Titan-family variant generation.

---

## 7. Sources

- SporeWiki — Creature Creator (categories, 228 parts, stat tables, DNA costs, keyboard controls incl. Patch 1.05 asymmetry, mouth-required rule): https://spore.fandom.com/wiki/Creature_Creator
- SporeWiki — Bite (per-part ability levels and DNA prices by tier): https://spore.fandom.com/wiki/Bite
- SporeWiki — Downloading content (PNG drag-and-drop import into editor/Sporepedia): https://spore.fandom.com/wiki/SporeWiki:Downloading_content
- Rempton Games — "How The Spore Creature Creator Works" (metaballs + rigblocks, part degrees of freedom): https://remptongames.medium.com/how-the-spore-creature-creator-works-44abc76283bb
- CheatCC — Spore Creature Creator review (vertebra sculpting, part categories, $2,000 DNA budget, complexity meter, Test Drive sharing): https://www.cheatcc.com/articles/spore-creature-creator-review-for-pc-pc/
- Game Developer — "Gingold Talks Spore's 'Magic Crayon' Approach" (bean→vertebrae origin, 4 KB creature / 20 KB picture, compression rationale): https://www.gamedeveloper.com/game-platforms/gingold-talks-i-spore-i-s-magic-crayon-approach
- Lai, Leymarie, Latham, Arita, Suzuki — "Virtual Creature Morphology: A Review", *Computer Graphics Forum* 40(2), 2021 (§11 Spore: implicit surfaces, ear-clipping triangulation, weights from implicit-function identity, semantic animation tags): http://onlinelibrary.wiley.com/doi/10.1111/cgf.142661
- Hecker, Raabe, Enslow, DeWeese, Maynard, van Prooijen — "Real-time Motion Retargeting to Highly Varied User-Created Morphologies", *ACM Trans. Graph.* 27(3), SIGGRAPH 2008: https://dl.acm.org/doi/10.1145/1399504.1360626
- Developer interviews compilation (Moskowitz on the procedural animation system and the nine-legged creature; Bradshaw on algorithms interpreting form): https://sudonull.com/post/222-How-Spore-was-created-interviews-with-developers
- Worthplaying — Spore v1.05 patch notes (asymmetry feature, controls, one-way conversion): https://www.worthplaying.com/article/2009/7/23/news/63631-spore-v105-patch-available-now/
- Spore official patch page (Patch 5 / 5.1 notes, incl. Collada export cheat): http://static.spore.com/patch
- Spore Unlimited Complexity Mod documentation (complexity caps: 138 creature / 148 outfitted; over-cap creations barred from Sporepedia): https://adarenmer.weebly.com/uploads/1/4/8/6/148691813/spore-unlimited_complexity_mod.pdf
- GameFAQs — "How can a 25Kb PNG file contain all that is needed?" (PNG-embedded creature data discussion): https://gamefaqs.gamespot.com/boards/954516-spore-creepy-and-cute-parts-pack/43665107
- Impossible Creatures engine overview (Combiner Engine: skeleton/geometry/texture/animation combiners, per-limb animation blending, IK for leg-length differences) — GameSpy archive of Relic's IC site: https://gamespy-archives.quaddicted.com/sites/www.strategyplanet.com/sigma/ic/icengine.shtml.html
- Wikipedia — Impossible Creatures (two-animal combination, 51 stock animals / 76 with downloads, ability inheritance): https://en.wikipedia.org/wiki/Impossible_Creatures
- Worthplaying — Impossible Creatures review (part-selection interface, per-part attributes, owl-wings/rhino-head ability examples): https://worthplaying.com/article/2003/2/6/reviews/8130-pc-review-impossible-creatures/
- G2A News — Monster Hunter Stories 3 gene guide (3×3 grid, bingo bonuses, Rite of Channeling transfer/rearrange): https://www.g2a.com/news/features/monster-hunter-stories-3-gene-guide-to-creating-perfect-monsties/
- TheGamer — Monster Hunter Stories 3 gene/channeling guide (genes shared, never consumed; Stories 3's non-destructive donor change): https://www.Thegamer.Com/monster-hunter-stories-3-twisted-reflection-build-monstie-strongest-genes-rite-of-channeling-excursions-guide/
- KSP Forum — "Node Definitions — explained" (node position/direction/size, attachRules flags, NODE{} transform-based definitions): https://forum.kerbalspaceprogram.com/topic/155189-reopen-ksp-node-definitions-explained/?tab=comments
- Pinter Computing — KSP spacecraft construction (symmetry modes: mirror/radial cycling, placement modes, subassemblies): https://pinter.org/archives/12581

*Verification note: Spore part counts are given as 228 functional parts (SporeWiki, launch full game) against Will Wright's ~400 figure (SporeWiki's Wright quote), which counts the wider part pool; complexity caps (138/148) are community-documented via the Unlimited Complexity Mod notes rather than an official Maxis publication. The "best part wins" behaviour of Spore ability levels is community-documented and consistent with SporeWiki's per-part level tables. Monster Hunter Stories 3 details come from guide coverage of the 2026 release; the gene-grid/bingo/channeling mechanics originate in Stories 1 (2016) and are described here in their current form.*
