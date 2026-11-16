# Eldritch Foundry — Teardown of the Slider-Forward Miniature Creator, and Rules for AnthroForge

*Design research, Nov 12, 2026. Companion to [HEROFORGE.md](sandbox://workspace/anthroforge-v2/HEROFORGE.md) and [CREATOR_LESSONS.md](sandbox://workspace/anthroforge-v2/CREATOR_LESSONS.md). Commissioned by Joe: "I have no funds for that, but we need some way to use ideas — check out https://creator.eldritch-foundry.com/". So this teardown is written under a hard constraint: **zero spend**. Its organising question is not "what can we buy from Eldritch Foundry" (answer: nothing, see §6) but "what design knowledge is observable for free." Method: web teardown — Eldritch Foundry's own site, pricing page, press kit and social posts, their 2019 Kickstarter record, independent reviews and comparisons. Prices checked against pages crawled Nov 2026 and dated; EF's own site carries stale copy in places (one page still promises a colour beta "opening Q1 2025" while another announces it open), so every price below is attributed to its page and crawl date.*

---

## 0. What Eldritch Foundry is, in one paragraph

Eldritch Foundry (founded 2018, Petah Tikva, Israel; launched via a May–June 2019 Kickstarter that raised **$513,089 against a $30,000 goal**) is Hero Forge's closest competitor: a browser WebGL character creator whose output is a tabletop miniature — bought as a high-resolution physical print (32-micron heritage, wax supports, originally produced with 3DSystems) or as an STL/3MF download. Where Hero Forge is parts-first with sliders underneath, Eldritch Foundry is the mirror image: **a parts library with an unusually deep slider layer on top** — body build/height sliders, and a facial-expression slider system reviewers consistently rate above Hero Forge's. Its art direction is realistic where HF is stylised, its prices undercut HF at every point, and its subscription (Eldritch Unlimited) sells *unlimited* downloads where HF sells credits. For AnthroForge it is the second data point on every question HEROFORGE.md raised — and on taxonomy and expression, the more instructive one.

---

## 1. The parts model

The current creator (per EF's own published UI captures, Aug 2025) is a left-sidebar menu stack over one shared library:

| Menu | Contents |
|---|---|
| Body | **Ancestry** (species preset panel: Goblin, Orc, Half Elf, Half Orc, Halfling…), sex toggle, Upper Body, build/height controls, **Wings**, tails, lineage options |
| Head | Head/hair/ears/horns choices within the ancestry's family |
| Facial Controls | Expression + facial-feature sliders (§3) |
| Clothing | Outfit and armour parts |
| Pose | Stance presets + per-part pose adjustment (§5) |
| Base | Base shape/texture, conditional-marker bases |
| Color | Colour selection — in **open beta** as of the Nov 2026 homepage (§4) |

Structural facts:

- **Ancestry is a first-class object with a sub-level: Lineage.** An ancestry (species) carries multiple *lineages* — variant feature sets within the species (for humans, lineages approximating different real-world ethnic feature families; EF shipped a "Monstrous Lineages" expansion and "multiple new lineages" as headline 2023 features). Two-level taxonomy — ancestry → lineage — is EF's core organisational idea and its cheapest variety multiplier (Rule EF1).
- **Parts are authored per ancestry family, extras are universal.** Clothing, weapons, accessories and familiars dress any ancestry; wings/tails/horns attach as Body-tab sections (§2). Backpacks and carried clutter are a noted strength (storytelling props: burglar's pack with grappling hook, explorer's pack with potions — narrative density as a part category).
- **Familiars/companions are parts, detachable by design** (a Kickstarter stretch goal made familiars detachable; a 2024 Familiars Pack added frogs, owls, crows, parrots, chickens, foxes). Mounts are a product tier ("Mounted" physical mini, $39; "Epic Poses and Mounts" launched 2023) rather than a creator mode.
- **The library grows by themed drops, not just weekly singles.** "Eldritch Foundry Core" is a monthly themed STL pack line (e.g. *The Bronze Age* — a complete Greek hoplite set), free to Unlimited subscribers; ancestry drops (Mermaid, Naga, Alien, Monstrous Lineages) land as events. The catalogue is materially smaller than Hero Forge's — reviewers converge on "broader range of clothing/hair" for HF — and EF compensates with cadence and theming (Rule EF7).
- **No kitbash.** There is no free-attach mode and no bone-level posing. EF's escape valves are its sliders and its pose fine-tuning (§5), not rule-breaking placement. The governance problem HF solved with a paywalled quiz-gated kitbash simply does not arise — because the freedom was never offered.

## 2. Ancestries — and the mixing rule that matters

**EF's rule, stated plainly: ancestry is a commitment, not a bundle.** You pick one ancestry, and its body/head family comes with it — there is no cross-ancestry head grafting, no "lion head on human body" slot combination of the kind Hero Forge allows. Mixing exists, but only in two sanctioned channels:

1. **Universal additive extras.** Wings, tails, horns, fangs are Body-tab sections offered across ancestries — the 2019 pitch was literally "want wings and a tail and fangs and swords?" The extras attach to the ancestry's body; they don't replace its identity.
2. **Curated "Half-" ancestries.** Half Elf, Half Orc (and their kin) ship as *their own ancestries* — blends authored by EF, not user-assembled. Where HF lets species identity emerge from part combinations, EF pre-composes the popular mixtures and sells them as first-class entries.

**The animal-folk catalogue is broad — broader in species count than in depth per species.** The 2019 launch list used in-world names (Somon = Human, Deoth = Dwarf, Aeth = Elf, Vantar = Goliath, Nathlings = Tiefling, Avatars = Dragonborn, plus Orcs, Gnomes, Halflings, Pixies, Imps, Goblins, Kobolds, Firbolgs). EF's own Oct 2023 press kit then records Mermaid and Naga ancestries launched, a first Alien ancestry, and a coming-year ancestry slate that reads like a furry convention: **lions, centaurs, minotaurs, werewolves, pigs, sharks, wolves, mice, turtles** (plus "featureless heads"). The Nov 2026 homepage's staff picks confirm live animal folk in the current creator: **Leonine** (lion), **Tortugan** (turtle), **Lizard** folk, **Naga**. Treat the press-kit-only names (shark, mouse, pig, wolf, werewolf) as *announced 2023–24*, not individually re-verified live in Nov 2026 — EF does not publish a canonical ancestry list, the same verification caveat as HF's species count.

- **Body plans ride inside ancestry, like HF.** Naga and Mermaid replace the leg plan with a tail; Centaur (announced) replaces it with a taur plan. The partition-by-body-plan pattern (HF2) appears again, implemented as ancestry choice rather than part choice.
- **Faces are slider country even for beasts.** EF's facial controls apply across ancestries — a Leonine's expression is tuned with the same brow/jaw/cheek sliders as a human's (§3), which is precisely AnthroForge's layered-head bet: one expression system over every species head.

## 3. Sliders vs parts: EF inverts Hero Forge

EF is the more slider-forward of the two miniature creators:

- **Body sliders** set build and height within the ancestry; proportions stay realistic — EF's marketed identity is "highest-resolution, realistic-looking" against HF's deliberate cartoon chunk. All3DP's buying guide routes readers to EF explicitly "if you're looking for more realistic proportions."
- **Facial Controls are the differentiator.** The expression panel opens with just two master sliders — **Happy** and **Angry** — and the depth is one layer down: eyebrows, cheekbones, jaw position, chin size, nose height are all individually tunable, and reviewers demonstrate compound expressions (confused-disgusted-surprised blends) built from those fine sliders. Modular Realms' verdict, echoed across comparisons: EF "excels in facial expression control"; HF offers more mouth shapes, EF finer expression. Note the asymmetry — EF spent its face budget on *affect* (brow/jaw/cheek motion) rather than *inventory* (mouth part variants).
- **Everything else is parts.** Clothing, gear, hair — chosen, not sculpted. EF has no equivalent of HF's Face Customizer morph-head programme beyond its facial sliders, and no freeform sculpting anywhere (one SEO comparison's claim of "full sculpting control" is simply wrong — disregard that genre of source).

**The balance lesson:** HF proved catalogue breadth reads as depth; EF proves a *small set of well-chosen continuous sliders on the face* reads as depth too — because the face is where a viewer lingers. The two systems spent the same budget on different organs. AnthroForge, which owns learned-morph tech neither has, can spend on both — but EF's prioritisation (expression first, mouths last) is the right default order (Rule EF3).

## 4. Colour: late, beta, and catching up

- **EF designed in greyscale for most of its life.** Colour selection was a closed beta promised for "Q1 2025" (stale copy still on the site) and is announced **"now in open beta"** on the Nov 2026 homepage. Downloads include **multicolour 3MF** (independently catalogued by SkipTheCAD, Oct 2026), and physical minis are now also sold pre-painted (2025–26 sponsor copy). Compare HF: full zone/material/decal colour since 2020 — EF is ~5 years behind here and still labelling it beta.
- What can be observed for free is the *shape* of the catch-up: colour arrives as a creator menu of its own (last in the stack), applied over the existing part structure — consistent with per-part colour assignment rather than HF's mature zone/decal two-layer system. EF publishes no colour support documentation comparable to HF's, so zone granularity is **not verifiable from public pages**; flagged, not guessed.
- Lesson embedded in the timeline: colour was the feature EF's community asked for while EF shipped ancestries and poses instead. A creator can survive years without colour if its geometry pipeline is strong — but the beta's prominence on the 2026 homepage says the debt came due (Rule EF6 covers the other half of this: EF monetised the wait via new *forms* of the same design).

## 5. Posing: stance owns the legs, sliders own the arms

- **Pose = stance preset + per-part fine-tune.** You choose a stance for its *leg* positioning — the one thing that cannot be altered afterwards — then adjust arm, wrist, head, hair, body, cloak and accessory positions individually (Modular Realms' walkthrough; the 2020 World Anvil review already noted an "advanced pose editor" for per-element tweaks). Flying stances exist, with wings or effects as the visual support.
- **This is a genuinely different posing architecture from both** HF (preset + joint adjustment + paywalled kitbash skeleton) and game creators (animation rigs). EF's insight is anatomical: in a static statue, legs are structural and arms/head are expressive — so legs are a preset choice and everything expressive is a slider/offset. Cheap to build, hard to break, impossible to make interpenetrate as badly as free posing (Rule EF4).
- **Bust Mode (2025)** reframes the same design as a bust on a pedestal — a display product, not a new creator. Together with the VTT Exporter (2023, tokens for virtual tabletops) and colour 3MF, EF now sells one design in at least four forms (full mini STL, bust, VTT token, painted print) — the design-vector-outlives-format property, achieved with crop-and-frame profiles (Rule EF6).

## 6. Business model — and the free-routes audit (the section Joe asked for)

| Tier / item | Price (source, date) | What it buys |
|---|---|---|
| Designing | **Free** | Full creator, all ancestries/parts/poses, screenshots, community Guild browsing/remixing |
| STL / 3MF download, à la carte | **$5 per design** (EF homepage, crawled Nov 2026; $4.99 in May 2025 secondary sources — same price, rounded) | The geometry of your design |
| Physical mini | Standard $25 · Base Effects $29 · Epic $39 · **Mounted $39** · Double Size $55 (EF homepage, Nov 2026; "starting prices") | Printed mini, ~34 mm scale |
| Eldritch Unlimited — monthly billing | **$15/mo** (EF pricing page, crawled Oct 2026) | Unlimited STL+3MF downloads of your designs + Core monthly packs included |
| Eldritch Unlimited — quarterly | $13/mo ($39/quarter) | Same |
| Eldritch Unlimited — annual | **$10/mo ($120/yr)** | Same |
| Eldritch Unlimited — Lifetime | **$499 once** ("limited slots", recurring promo; EF pricing page + Jan–Mar 2026 social posts) | Same, forever |
| Merchant License | **$550/year** (SkipTheCAD licence audit, checked Oct 2026) | Sell *prints* of your designs commercially; files may never be sold. (An earlier beta merchant tier reportedly capped sales at 50 units/design — technicalustad, May 2025; treat as superseded/uncertain.) |

**The free-routes audit, honestly:**

- **Designing is free; geometry is never free.** No free STL, no sample file, no trial download, no free tier appears anywhere in EF's current public material, and independent generator catalogues classify EF flatly as **"Paid"** in every table (SkipTheCAD, checked Sep–Oct 2026) — unlike genuinely freemium rivals. Hero Forge at least gives away two sample STLs; EF gives away none that we could find.
- **Discounts are not a free route.** 15%-off affiliate codes are ubiquitous (multiple creator codes are live in EF's own partner content), which makes the cheapest *legal* single file ≈ $4.25 — still not $0, and Joe's constraint is no funds, so: **the cheapest legal way to obtain one EF geometry file is the $5 à-la-carte STL, and there is no legal $0 route to EF geometry. Full stop.**
- **What IS free is everything observable**: the full creator (ancestry list, lineage structure, slider inventory and ranges, pose list, part taxonomy — all browsable in the designer), the Community & Guild (published designs are viewable and *remixable in the creator* — "view designs, change them up, publish your own"), staff picks and marketing renders (a running showreel of what the ancestry/part combinations look like assembled), and EF's press/social material (ancestry announcements with renders). That is a complete design education at $0 — which is the actual deliverable of this study. As with Hero Forge: **reference yes, geometry no** — EF's STL terms are personal-use, and its parts are no more extractable or licensable than HF's (§9 of HEROFORGE.md applies mutatis mutandis).
- **Account note:** sources differ on the account question — SkipTheCAD's current tables list an account as *not needed* (the creator opens and designs in the browser), while tutorials advise registering early because saving progress and checking out need the account (and unsaved work is fragile — Modular Realms' loudest practical tip is "save your progress" against refresh-loss). Design free and accountless; save/download is where identity begins.

**Model contrast with HF:** EF's wall is also on export (HF4 holds), but the *shape* differs — EF sells **abundance** (unlimited downloads, one low $5 point) where HF sells **scarcity** (per-design $7.99, credit bundles). EF is ~38% cheaper per STL and its heaviest users pay a flat $120/yr. The unlimited tier only makes sense if downloads are cheap to serve and users print armies — a wargamer/party-of-six economy, not a one-hero economy.

## 7. Tech and platform notes

- **Browser WebGL creator**, same architecture class as HF: parts stream into a client session; designs live server-side in your account; exports (STL / multicolour 3MF) are generated from the design on purchase/subscription. The custody caveat from HF8 applies unchanged.
- **Community & Guild** is EF's discovery layer: browse community designs and collections, open them in the creator, remix, publish yours. It is HF's config-sharing plus a gallery front-end — the remix economy again, surfaced as a *destination* rather than a link format.
- **VTT Exporter (2023)** and Bust Mode (2025) are export-profile features — evidence EF's design data is internally a retargetable vector, exploited commercially one profile at a time.
- **Scale/resolution identity:** ~34 mm figures, "highest-resolution custom miniatures on the market" as the standing marketing claim, with the 32-micron/wax-support print heritage behind it. Independent print reviews (Strange Assembly, 2021) found fine detail mostly surviving, with facial micro-detail softer in print than in render — the EF version of HF's §8 honesty: render fidelity > print fidelity at the face, and expressions are exactly where EF spends — an unresolved tension worth noting.

## 8. Eldritch Foundry vs Hero Forge, head to head

| Axis | Eldritch Foundry | Hero Forge | Edge |
|---|---|---|---|
| House style | Realistic proportions, high-resolution marketing claim | Deliberately stylised, chunky at 30 mm | Taste; All3DP routes realism-seekers to EF |
| Species model | **Ancestry commitment** + lineage sub-variants; mixing via universal extras + curated Half- ancestries | **Species as preset bundle**; free slot-level mixing inside a body plan | HF for mixers; EF for authored coherence |
| Animal folk | Leonine, Tortugan, Lizard, Naga live; wolf/werewolf/minotaur/centaur/mouse/pig/shark announced 2023–24 | 42 species by 2020 and growing weekly since; deep birdfolk etc. | HF on count; EF respectable and furry-forward |
| Sliders | **Deep**: body build/height + the best facial-expression slider set in the category | Body sliders + Face Customizer morph heads, newer and generation-split | **EF on faces**, clearly |
| Parts catalogue | Smaller; clothing/hair breadth is the known gap; strong props/backpacks | Thousands, weekly cadence for a decade | HF |
| Posing | Stance presets (legs locked) + per-part arm/head/cloak tuning; flying stances | Presets + joint adjustment free; skeleton kitbash paywalled | HF ceiling; EF elegance-per-effort |
| Colour | Open beta (2026), multicolour 3MF; ~5 years late | Mature zones/materials/decals since 2020 | HF, decisively |
| STL price | **$5** à la carte | $7.99 à la carte | EF |
| Subscription | **Unlimited** downloads $10/mo annual-equivalent; $499 lifetime; Core packs included | Credits (5/mo) at $14.99–19.99/mo; packs extra | EF for volume users |
| Extra forms | Bust Mode, VTT exporter, pre-painted prints | 3D Digital (VTT colour file), Token/Scene Maker (Pro) | Even |
| Free geometry | **None** — no sample STL | Two sample STLs | HF (barely) |
| Commercial use | Merchant License $550/yr (prints only) | Prints may not be sold at all | EF — the only one with a door |

Net: EF is stronger exactly where AnthroForge is also aiming — **facial expression depth, slider-forward anatomy control, realistic anchoring, ancestry taxonomy** — and weaker where AnthroForge's blueprint already plans strength (parts breadth, colour systems, free-attach extremes). Study EF for the face and the taxonomy; study HF for the library and the colour.

## 9. Limits people actually hit

1. **Catalogue breadth.** The recurring review note, including from EF's sponsored reviewer: clothing/hair options run out sooner than HF's; layering wishes (undershirt + armour mix-and-match) unmet as of that walkthrough. A smaller library is EF's structural tax for being second and younger.
2. **Mouth shapes.** EF traded mouth inventory for expression sliders (§3) — users who need a specific mouth (fangs-bared, particular grin) have fewer part-level options; the expression must be *dialled*, and at print scale the dialled detail partially softens (§7).
3. **Colour immaturity.** A headline 2026 feature is still labelled beta, with no public colour documentation comparable to HF's — early-adopter risk is visible in the product itself.
4. **Save fragility.** The community's standard advice is save-early-save-often against refresh loss — the accountless-design convenience (§6) has a sharp edge.
5. **No extremes regime.** No kitbash, no free attach, no user pose-from-scratch: EF's ceiling for grotesque/bara/monster builds is its slider ranges, full stop. For AnthroForge's orc-bara ambitions EF is a floor model, not a ceiling model — HF's governed kitbash (HF10) remains the extremes reference.

## 10. Rules for AnthroForge

Each rule: do/avoid, the Eldritch Foundry evidence, and the AnthroForge system it lands on. All ten are adoptable at **zero cost** — they are taxonomy, slider design and product-shape decisions, not assets.

**EF1 — Two-level species taxonomy: Ancestry → Lineage.**
DO: organise species as ancestries, each carrying named *lineages* — variant feature sets within the species (wolf → timber/dire/arctic lineages; fox → red/fennec/arctic) — so perceived species variety multiplies without multiplying base geometry. EF built headline releases out of lineage drops alone (Monstrous Lineages, "multiple new lineages," 2023).
AVOID: a flat species list where every variant costs a full new species entry.
*Lands on:* species presets + style axis (a lineage is a preset point + slider vector, per R1 — EF's lineages are exactly that, named).

**EF2 — Offer two mixing regimes, and say which is which.**
DO: EF proves a *restricted* mixing regime can satisfy users: ancestry commitment + universal additive extras (wings/tails/horns/fangs as cross-species sections) + curated Half- blends. If AnthroForge's free slot-mixing (HF1/HF2) accrues too much fit debt for a part family, demote that family to EF-style sanctioned mixing instead of abandoning mixing altogether.
AVOID: silent inconsistency — some parts mixable, some not, with the rule discoverable only by failure.
*Lands on:* swappable-parts governance; part records carry a `mixing: free | additive | locked` field.

**EF3 — Spend the face budget on expression sliders before mouth parts.**
DO: ship two master emotion sliders (EF's Happy/Angry pattern) over a fine layer of brow/cheek/jaw/chin/nose sliders, driven by our layered head construction — brow and jaw are muscle/tissue-layer morphs in our anatomy, which is *why* they blend believably. EF beat the much larger HF on the face with this allocation alone.
AVOID: a mouth-part catalogue as the expression strategy; parts don't blend, expressions must.
*Lands on:* layered head + expression layer over species presets.

**EF4 — Pose architecture: stance owns the legs, adjustments own the rest.**
DO: for static/export posing, adopt EF's split — stance presets carry leg structure; per-part offsets (arms, wrists, head, cloak, held items) carry expression. It is the cheapest posing system that cannot produce broken statues, and it maps directly onto our skeleton as stance keyframes + joint offsets.
AVOID: free posing as the default (interpenetration support burden) — keep free control in the workshop/extremes regime instead (HF10).
*Lands on:* pose system; STL/print export profile.

**EF5 — Study competitors at $0 by treating their designer as the documentation.**
DO: generalise this teardown's method — a free creator *is* a published spec: taxonomy, slider inventory and ranges, pose lists, ancestry cadence, pricing psychology are all observable without buying geometry. Budget competitor geometry purchases last (HF §9.3's narrow case) and only after the free observation is exhausted.
AVOID: buying files to learn what the menus already disclose.
*Lands on:* research practice for the whole creator survey; the learn-then-delete pipeline's targeting.

**EF6 — One design, many forms: busts and tokens are export profiles, not features.**
DO: EF's Bust Mode and VTT Exporter are framing decisions on the same design vector — add *bust* (crop + pedestal) and *token* (top-down/flat render) profiles to AnthroForge's export list at near-zero marginal cost, alongside the print profile (HF7).
AVOID: building separate tools per output form.
*Lands on:* export profiles (app blueprint §10); Titan family busts are an obvious first use.

**EF7 — Theme the library drops.**
DO: organise part releases as named themed packs (EF Core's *Bronze Age* pattern) — a theme gives a month of parts a story, a test set ("does the hoplite set assemble?"), and a marketing beat, for free. AnthroForge's library growth (species waves, the orc pack) should ship themed, not dribbled.
AVOID: unthemed part sprawl that users can't browse by intent (EF's own Core packs were a response to users "doom-scrolling the part library" — their words, and a UI lesson by itself: *browse by curated set before browse by category*).
*Lands on:* parts library organisation + library browser UX.

**EF8 — If monetising downloads: abundance pricing beats credit scarcity for volume users.**
DO: note EF's proof that unlimited-at-$10/mo-annual undercuts credit bundles and still sustains a business — relevant if AnthroForge ever sells exports, and a genuine user-goodwill advantage (no credit anxiety, HF4's wall placement with EF's shape).
AVOID: assuming HF's credit model is the only shape; and note the precondition — unlimited only works when marginal export cost ≈ 0, true for server-generated STLs and for our local app exports alike.
*Lands on:* product policy (companion to HF4).

**EF9 — Merchant licensing is a door HF doesn't have; design the licence ladder early.**
DO: EF sells a Merchant License ($550/yr, prints only, files never) — a rung between "personal use" and "redistribution" that captures commercial-print value without leaking geometry. AnthroForge's licence tiers for parts/exports should include an equivalent rung from day one; retrofitting licence rungs is how communities get angry (HF's Daggerheart episode).
AVOID: binary personal/commercial terms that force print-sellers into violation or silence.
*Lands on:* licence tiers in the data model + export profiles.

**EF10 — Realism is a positioning choice with a slider budget attached.**
DO: EF's realistic anchoring is consistently what reviewers praise and route buyers on — it validates Joe's realistic-anchor end of the style axis as commercially legible, not just aesthetically preferred. The cost, visible in EF, is that realistic proportions make fit/clipping *less* forgiving than HF's chunk — budget fit-solving accordingly at the realistic end.
AVOID: treating stylisation as a free dial at export time; the fit regime must follow the style axis (R4's conformance flag).
*Lands on:* style axis + extremes/fit regime.

---

## 11. Sources

- Eldritch Foundry — homepage (pricing summary: Standard $25 / Base Effects $29 / Epic $39 / Mounted $39 / Double Size $55 / STL $5; Unlimited "from $10 a month"; Unlimited Lifetime promo; Bust Mode; Colour open beta; Community & Guild; staff picks incl. Tortugan, Naga, Leonine, Lizard): https://eldritch-foundry.com/
- Eldritch Foundry — Pricing page (Unlimited tiers $15/mo monthly · $13/mo quarterly ($39) · $10/mo annual ($120) · $499 lifetime): https://eldritch-foundry.com/pricing/
- Eldritch Foundry — creator (menus/architecture; WebGL-gated to text crawlers): https://creator.eldritch-foundry.com/
- Eldritch Foundry — Press Kit, Oct 2023 (Epic Poses and Mounts; Monstrous Lineages; Mermaid, Naga and Alien ancestries launched; 2024 ancestry plans: lions, centaurs, minotaurs, werewolves, pigs, sharks, wolves, mice, turtles; Familiars Pack; VTT Exporter): press kit PDF hosted on EF's download domain (exemple-stls-download.s3.amazonaws.com/PressKit_102423 copy.pdf)
- Eldritch Foundry — Instagram (creator UI capture, Aug 2025: Body/Head/Facial Controls/Clothing/Pose/Base/Color menus; Ancestry panel — Goblin, Orc, Half Elf, Half Orc, Halfling; Bust Mode early access; Core "Bronze Age" pack free with Unlimited, Jan 2026; Lifetime $499 promos): https://www.instagram.com/p/DND12P1xVLM/ · https://www.instagram.com/p/DTA6U_HkrLl/
- BackerKit — Eldritch Foundry FAQ (2019 launch races with in-world names: Somon, Deoth, Aeth, Vantar, Homon, Nathlings, Avatars; Pixies, Imps, Goblins, Kobolds, Firbolgs): https://eldritch-foundry.backerkit.com/faq
- Kicktraq — Eldritch Foundry Kickstarter record ($513,089 raised of $30,000 goal, May 9–Jun 8 2019): https://www.kicktraq.com/projects/242766563/eldritch-foundry/
- Modular Realms — EF walkthrough & vs-HF comparison (Body-tab contents: race, lineage, build, height, tails, wings; expression sliders — Happy/Angry + brow/cheek/jaw/chin fine controls; pose fine-tuning with legs fixed by stance; flying poses; HF broader clothing/hair; EF expression + resolution + $5-vs-$7.99 price; *sponsored by EF — flagged in the article itself*): https://www.modularrealms.com/blogs/news/how-to-make-epic-custom-minis-for-your-ttrpg-games
- Strange Assembly — EF print review, Part 2 (physical print fidelity; wings without extra charge; expression in print): https://www.strangeassembly.com/2021/review-eldritch-foundry-part-2
- World Anvil blog — EF review (2020 creator flow: race carousel → Body and Face → Clothing → Items → Pose → Base; advanced pose editor; conditional marker bases): https://blog.worldanvil.com/reviews/eldritch-foundry-bring-your-characters-to-life/
- Nerds on Earth — EF review (2020; menu flow, likeness building): https://nerdsonearth.com/2020/03/eldritch-foundry/
- All3DP — 3D-printing miniatures guide (EF recommended "for more realistic proportions"; Unlimited explained): https://all3dp.com/2/3d-printing-miniatures-get-started/
- SkipTheCAD — generator catalogues & licence audit (EF classified "Paid" in all tables; account "Not needed" for design; STL + multicolour 3MF exports; Merchant License $550/yr, prints sellable, files never; checked Sep–Oct 2026): https://skipthecad.com/generators/ · https://skipthecad.com/guides/selling-prints-from-generators/ · https://skipthecad.com/multicolor-3mf-generators/
- Accio — Hero Forge alternatives market report (EF: $25+ physical, $5 STL, $10/mo unlimited): https://www.accio.com/business/hero-forge
- TechnicalUstad — Hero Forge alternatives (EF $4.99 STL, May 2025 testing; 50+ races / 500+ items claim; beta merchant licence note — low-authority SEO source, used only where consistent with primary pages): https://technicalustad.com/hero-forge-alternatives/
- CB Insights — Eldritch Foundry company profile (founded 2018, Petah Tikva, Israel; subscription + monthly Core sets): https://www.cbinsights.com/company/the-table-of-ultimate-gaming/financials
- GeekDad / GamingTrend / Hi-Tech Chic — 2019 Kickstarter coverage (funded in 3 hours; 3DSystems partnership; 32-micron, wax supports; "wings and a tail and fangs" pitch; conditional marker bases): http://geekdad.com/2019/05/kickstarter-alert-eldritch-foundry-superior-quality-custom-minis/ · https://gamingtrend.com/news/create-your-own-character-with-eldritch-foundrys-newest-kickstarter/

*Verification note: Eldritch Foundry publishes no canonical ancestry list, part count, or colour-system documentation; ancestry status distinguishes EF's own statements (homepage staff picks, Nov 2026 = live: Leonine, Tortugan, Lizard, Naga) from its Oct 2023 announced slate (wolf, werewolf, minotaur, centaur, mouse, pig, shark — announced, not re-verified live). The Modular Realms comparison is EF-sponsored and says so; its feature descriptions are corroborated by EF's own UI captures, its superlatives are discounted accordingly. Prices are as published on pages crawled Oct–Nov 2026; EF's site contains mutually stale copy (colour beta "Q1 2025" vs "now open"), so pricing should be re-verified before any commercial decision. No EF purchase, account, or download was made for this study — Joe's zero-funds constraint was the brief, and §6 records that no free route to EF geometry exists in any case.*
