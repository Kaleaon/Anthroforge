# Hero Forge — Teardown of the Parts-First Character Creator, and Rules for AnthroForge

*Design research, Nov 12, 2026. Companion to [CREATOR_LESSONS.md](sandbox://workspace/anthroforge-v2/CREATOR_LESSONS.md) (the twelve game creators). Commissioned by Joe: "also look at heroforge" — plus his addendum, "is there any way to grab the parts from heroforge?", answered honestly in §9. Method: web teardown — Hero Forge's own support docs, FAQs and release notes, pricing pages, community deep-dives and build logs. Prices checked against pages crawled Nov 2026 and marked as current-published; they drift, re-verify before quoting commercially.*

---

## 0. What Hero Forge is, in one paragraph

Hero Forge (Sky Castle Studios) is a browser WebGL character creator whose output is not an avatar for a game but a **tabletop miniature**: you assemble a character from a parts library of thousands of items, pose and colour it, and then either buy a physical print (plastic from $19.99, colour-printed from ~$44.99, bronze $99.99+) or buy the STL and print it yourself. Designing is free and needs no account; saving needs an account; *taking the geometry away is the product*. It is the most successful parts-first creator in the world — a decade old, updated weekly, with a species catalogue that now runs deep into anthropomorphic animals — and it achieves slider-rivalling variety with almost no sliders. That inversion is why it's in this survey: AnthroForge's swappable-parts system is the same bet, made for rigged avatars instead of 30 mm prints.

---

## 1. The parts model

The creator is a sequence of menus over **one shared part library**:

| Menu | Contents |
|---|---|
| Species | A preset bundle (see §2) — the entry point, not a locked mode |
| Head | Face/head mesh, ears, horns/antlers, hair, beard, (Face Customizer: facial feature sliders + expression sliders, §3/§5) |
| Body | Body type, proportion sliders (height, build, shoulder width, muscle mass…), tails, wings, extra arms, prosthetics |
| Clothing | Tops, bottoms, footwear, gloves, cloaks — layered outfit slots |
| Gear | Held items per hand, holstered/back items, spell effects |
| Base | Display base + stage/scenery items |
| Pose | Preset poses + Advanced Posing + expressions (§5) |
| Color | Zone painting, materials, decals (§4) |

Key structural facts:

- **Parts are authored against body plans, not against individual characters.** A shirt fits every humanoid body because bodies share a skeleton and proportion envelopes; a part is a mesh + an attachment/anchor + colour zones. New parts arrive **weekly** (release notes are a decade-long changelog) — the library is the product's compounding asset.
- **Scale is a first-class transform.** Characters can be rescaled (including XL sizes); parts are expected to survive rescaling, which is one reason HF parts are chunkier than game assets (§8).
- **Two-character minis and mounts.** A mini can carry a second character, a mount, or a familiar — each is a full additional character assembled from the same library, sharing the base. Composition is part of the design surface, not an afterthought.
- **Kitbash mode (Pro/Pro+ only) is the free-attach escape hatch.** Any part can be placed *anywhere* on the mini with full position/rotation/scale, up to ~20 kitbash pieces; it also exposes the skeleton for direct bone-level posing down to individual fingers. It is explicitly framed as breaking the rules the slot system enforces — and it ships behind a paywall *and* a printability acknowledgement quiz (§8). This is Soulcalibur VI's free-attach accessories (§2.9 of CREATOR_LESSONS) with two extra years of governance thinking: gate the dangerous freedom behind commitment (subscription + a quiz), don't ban it.

## 2. Species — and the mixing rule that matters

**The headline mechanic: a Hero Forge "species" is not a body. It is a preset — a preselected bundle of ordinary choices in the Head and Body menus** (head mesh, ears, muzzle, tail, body type, fur/skin defaults). Picking "Male Fox" sets those slots; afterwards *every slot stays independently editable*. Community build logs show the pattern plainly: one documented build starts from species Giggle-Dog (Male), then overrides Head → Hyena Head, Ears → Canine Ears, Hair → Hyena Mohawk, Tail → Straight Tail, and carries on. Nothing complains. Nothing re-locks.

- **The anthro catalogue is large and growing.** Forty-two species by 2020 (OnTableTop's count at the 2.0 launch); since then a numbered "species" release series has added, among others, birdfolk (eagle/owl/robin heads), stoatfolk, cyclops, otterfolk, minotaurs — plus licensed Collaborator Collections (Daggerheart's frog-like Ribbet, fungus Fungril, monkey Simiah with monkey/orangutan/tamarin subtypes; §6). Classic fantasy races (elf, dwarf, orc, dragonborn, tiefling, warforged, tabaxi-style catfolk, lizardfolk, gnolls…) are table stakes underneath.
- **Heads, ears, snouts, tails are separate slots.** An animal head is a head-slot choice; ears are their own slot; the tail is a body-slot choice. The combinatorial consequence: "fox head, wolf ears, demon tail, human body, dragon wings" is a legal build in a way it never is in race-locked creators (BG3!). Species identity is *emergent from the part combination*, exactly like AnthroForge's design goal.
- **Where mixing stops — body plans.** Some choices are structural, not cosmetic: centaur and naga lower bodies replace the leg plan; mounts/families are separate characters; digitigrade vs plantigrade legs are body-level options, not per-part. Within a body plan you mix freely; across body plans you don't mix at all — you switch plans and re-dress. This is a *hard partition with total freedom inside it*, and it's the single most transferable design decision in this whole teardown (Rule HF2).
- **Compatibility is metadata, and it leaks.** Not every head supports every system: Face Customizer marks compatible heads with a gear icon; legacy heads convert on edit (horns/ears/teeth/expressions are preserved "as best we can" — some change, and undo can't take you back). Some faces disable other customisation entirely (the mouthless face locks out facial posing). Hair and beard pieces are effectively authored per head family and can sit wrong on cross-species heads. HF's answer is not to forbid the combination but to let it look wrong — at 30 mm, users tolerate a lot (§8).

## 3. Customisation depth: parts ≫ sliders, but sliders exist

Hero Forge is usually described as slider-free. It isn't — the sliders live *under* the parts:

- **Body sliders** tune the assembled body: height, proportions, shoulder width, muscle mass, build. They deform the shared body plan; they do not sculpt freely.
- **Face Customizer sliders** (free, all users) adjust facial features — chin, cheeks, nose, lips, brow — and feature size/position, on compatible heads. The Face Customizer's unified colour-zone/morphology system is explicitly what lets it "blend between different morphologies and expressions" — i.e., HF has been quietly moving slider-morph tech into its heads for the newest part generation, while keeping the *interface* part-first.
- **Expression sliders** (§5) are the third slider family.

**The depth balance is the lesson:** where a game creator spends its budget on morph resolution, Hero Forge spends it on *catalogue breadth*. A user perceives "thousands of items" as deeper than "200 sliders," because every part is a visible, nameable, screenshot-able choice, while slider differences blur. But the parts only feel infinite because three slider systems (body, face, expression) quietly absorb the fine variation the parts can't express. Parts-first is a *presentation* strategy layered over a morph substrate — not an alternative to one.

## 4. Colour: zones, materials, decals

The colour system is the most sophisticated part of the product and the closest analogue to AnthroForge's material design:

- **Colour zones, not textures.** Every part ships pre-segmented into named zones (a tunic's trim, body, and shading are separate zones). Painting is: pick a paint, click a zone. Zones are discoverable (a gear menu lists a part's zones) and are the reason non-artists get clean results — it's paint-by-numbers with professional palettes. Zone bleeding/fuzz at edges is a recurring bug class in the release notes, i.e., zone authoring quality is a permanent production cost.
- **Paints are materials.** Fourteen material categories (Cloth, Leather, Paint, Plastic, Metal, Skin, Hair, Plant, Stone, Wood, Fire, Gem, Glass, Eye). A paint carries a base colour plus material behaviour; the Mix tool builds custom paints as **base / layer / highlight** triples, and advanced options expose roughness, fuzz, glow, metallic, opacity per paint. Community members publish shareable paint sets ("AMRs" — Advanced Materials Resources). Pro users can save their own paints into the library.
- **Presets as colour architecture.** Body presets colour everything that's "the character"; Theme presets colour clothing/gear. Two coordinated palettes, one click each — the same preset-is-a-point-in-space discipline CREATOR_LESSONS R1 demands, applied to colour.
- **Decals are the detail layer.** Layered, re-orderable projected decals (scars, dirt, blood, cheek colour, eyelashes, patterns with tiling) applied per part or across parts — where detail lives that zones are too coarse for. Note the Face Customizer migration detail: animal-head colour markings that used to be colour zones *became decals* when heads went morphable. Zones serve rigid parts; decals serve morphing surfaces. That split is a design rule, not trivia (Rule HF5).

## 5. Posing and expression

- **Preset poses** cover the common cases (stances, action poses, mounted). **Advanced Posing** (free) exposes joint-level adjustment on any preset — rotate limbs, adjust the figure's position — with a **mirror** toggle. **Kitbash mode** (Pro) goes further: direct bone manipulation, fingers included.
- **Expressions are slider blends.** Face Customizer's expression controls are sliders, each a named emotion/facial configuration, freely mixable ("bemused smarmy" is a reviewer's blend of two). The authoring advice the community converged on — *design the face neutral, add expression in Pose → Face* — mirrors our R12 separation: neutral anatomy in the base, expression as a downstream layer.
- **Poses are importable.** The Importing system copies Species / Face / Expression / Pose / Kitbash Parts / Theme Colors *independently* from any other mini (including community-shared ones) — a design is a bundle of separately remixable layers. "APR" (Advanced Posing Resource) minis exist purely as pose donors: people share characters whose only value is their pose. When your parameter vector is decomposable, a remix economy appears on its own.

## 6. Business model: design free, geometry is the product

| Tier | Price (current published, Nov 2026 crawl) | What it buys |
|---|---|---|
| Basic | Free | Full design tools, weekly content, screenshots, share links |
| Pro | $3.99/mo (12-mo) · $4.99 (3-mo) · $5.99 monthly | Kitbash mode, Token Maker (VTT), Scene Maker, HD portraits, folders, import pose/outfit from another mini, early access |
| Pro+ Download | $14.99/mo (12-mo) · $16.99 (3-mo) · $19.99 monthly | Pro + **5 digital credits/mo** (roll over) for STL / 3D-digital downloads + monthly pre-made digital packs |
| À la carte | STL $7.99/design · pre-made digital packs $7.99 or 1 credit · physical minis $19.99+ | The geometry, one design at a time |

What the placement does:

- **The paywall sits exactly on export, nowhere else.** Creation is unrestricted and unhurried — users sink hours (the engagement *is* the funnel), then pay $7.99 at the moment the design has become *their character*. Every creator in CREATOR_LESSONS that charged earlier or for editing (MHW vouchers) is resented; HF charges at the point of maximum emotional ownership and is beloved. The screenshot is free; the file is the product.
- **Pro sells power tools, not parts.** Kitbash/Token Maker/Scene Maker are *capabilities*; the parts catalogue stays free for everyone. The first breach of that line — the 2025 Daggerheart Collaborator Collections selling licensed ancestry part-sets at $7.99 *each, on top of print costs* — produced immediate, organised fan backlash, precisely because it moved the wall from output to input. Users had a decade of "parts are free, prints cost money" as an implicit contract.
- **Subscription math favours the platform.** Pro+ at $14.99–19.99/mo bundles 5 credits (≈$40 of à-la-carte STLs) — heavy users feel clever, light users subsidise. Credits roll over, defusing the use-it-or-lose-it resentment.
- **Designs are platform-locked assets.** Your library lives in your HF account; STL downloads are only *guaranteed* available in your account for six months. The design file format is a server-side config (share links are `heroforge.com/load_config=<id>`), not a file you hold. Convenience now, custody risk forever (§9).

## 7. Tech: a WebGL library-streaming machine

- **Browser WebGL app.** The whole creator runs client-side; parts stream in on demand from the catalogue rather than shipping as one download — the only way a thousands-of-parts library stays loadable in a browser tab. Design state is a server-saved **config**: the share link *is* the config ID, and anyone opening it loads your exact mini (and can copy/remix it via Importing, §5).
- **Accounts are the save system.** No account → design in the tab, screenshot if you like; account → saved heroes library, folders (Pro), purchases, download vault.
- **Exports are server-generated.** The STL/3D-digital files are produced from your config on purchase and delivered to the account downloads page — the client never holds exportable geometry of the full assembled design. This is deliberate architecture, not an accident (§9).
- **The "3D Digital" export** (a colour file for virtual tabletops) shows the same config re-targeted at a second medium — the design vector outlives any single output format. AnthroForge's omniversal records aim at exactly this property.

## 8. Limits people actually hit

1. **Print scale dictates the art.** Everything is authored to read at ~30 mm: exaggerated heads/hands, thick weapons, chunky details, simplified faces. Fine detail (thin accessories, delicate kitbashes) may not survive printing; the pipeline **auto-thickens weak elements** by default, and kitbashing makes you pass a quiz acknowledging your creation may be physically impossible. The constraint is honest and *communicated by the tools*, not discovered at the printer — mostly. Users still report detail loss and designs they must "take on faith" at checkout.
2. **Clipping and fit are tolerated, not solved.** Cross-species hair, beards on muzzles, hats on horns: parts intersect, and the fix is user-side (swap, scale, kitbash it). At mini scale the audience forgives it; the release notes show a permanent background rate of per-part geometry/zone fixes — parts libraries accrete fit debt forever.
3. **Compatibility generations.** Face Customizer split the head catalogue into compatible/incompatible generations; converting a legacy head is one-way and lossy at the edges. Any long-lived parts system will face this migration at least once — HF's handling (convert on edit, warn, keep a copy) is the pragmatic template.
4. **Posing ceiling.** Without kitbash, poses are preset+adjustment; with it, you're hand-posing a skeleton with no physics — interpenetration is your problem. There is no animation; the "pose" is a statue.
5. **The locked-config ceiling.** You cannot take your design to another tool except through the paid fused STL (§9). Your creative work's *editable* form lives on their server, under their terms, indefinitely.

## 9. Addendum (Joe, Nov 12, 12:26 CST): "Is there any way to grab the parts from Hero Forge?"

Short answer: **no — there is no legitimate way to obtain Hero Forge's parts as parts.** Here is the full picture, because the *shape* of the no is instructive for AnthroForge's own asset strategy.

### 9.1 Parts are never sold or licensed individually — at any price

- There is no parts store, no asset licence, no API, no "creator tier" that grants part reuse. The parts are Sky Castle Studios' proprietary production assets; what is sold is (a) physical prints, (b) a fused STL of *your assembled design*, (c) subscriptions to tools.
- The Terms of Service are unusually explicit: Sky Castle retains all ownership in the 3D models; downloadable models "may be printed or otherwise used for **personal, noncommercial use** and may not be resold, redistributed, or made available to third parties," and even *physical prints* from them may not be sold. A historically controversial ToS clause further assigned IP in user Character Designs themselves to Sky Castle (they clarified publicly that they claim the asset combinations, not your underlying character — but the assets were never yours either way).
- The client architecture enforces the licence: parts stream into a WebGL session as needed, and the assembled design's geometry only ever exists as a server-generated export. Extracting streamed assets from the client would breach the ToS and is not a route we use — same rule as the SL no-cache-ripping line in our other work. **Reference yes (it is a superb visual/structural reference — proportions, attachment logic, zone layouts are all observable in the free designer), geometry no.**

### 9.2 The STL purchase route — what you actually receive

| Fact | Detail (Hero Forge help/pricing pages + verified secondary sources) |
|---|---|
| Price | **$7.99 per design** à la carte; or via Pro+ Download ($14.99/mo annual-term – $19.99/mo monthly) at **5 digital credits/month**, credits roll over; pre-made digital packs $7.99 / 1 credit |
| Delivery | Zipped STL to your account's Digital Downloads page (purchases are non-refundable; re-download guaranteed only ~6 months — archive your files) |
| The mesh | **One fused, posed miniature** — the whole design (figure + gear + base content) merged into a single tessellated mesh, up to ~100k triangles, ~5–10 MB. Tessellated means no quads, no UV/material structure to speak of, **no rig** ("not rigged for animation" — their own FAQ) |
| Scale | **30 mm scale on a 1-inch base** by default; figure and base are one piece unless you tick **"Separate base"**, which splits only the base off |
| Print processing | **Strength adjustments applied by default** (thin/fragile elements auto-thickened for miniature scale; can be switched off). No supports included |
| Samples | Two free sample STLs exist to test your printer — the only free geometry Hero Forge has ever released |
| Also sold | "3D Digital" colour file for virtual tabletops — a different product, not print geometry |

### 9.3 What a purchased STL can and can't teach us

**Can:** overall proportions and silhouette decisions at a readable scale; how parts were *composed* (where a tail emerges, how a muzzle sits, what chunk a horn needs to read at 30 mm); posing/composition reference; print-engineering reference (what wall thicknesses survive). Measuring a fused export is the same class of study as measuring any bought miniature — legitimate reference for our own learned-deformation pipeline's *targets*.

**Can't:** part boundaries (the fusion erases them — you cannot recover "the fox head" from a fused fox-headed mini in any usable form); attachment points, sockets or skin weights (none exist in the file); colour zones/materials (gone — it's bare STL); slider/morph data (the export is one frozen pose/state); and reuse — the licence forbids redistribution and commercial use outright, so even a measured part could only ever inform *our own* authored geometry, never ship as or inside a product.

**Bottom line for Joe:** budget-wise, a handful of $7.99 STLs of the most instructive anthro builds (a foxfolk, a minotaur, a birdfolk — chosen in the free designer) would be cheap, legal *measurement reference* for the parts library, filed reference-tier like our other study material. The parts themselves are not, and will never be, obtainable. Our parts library has to be authored/learned the way the rest of AnthroForge is — which is, of course, the entire premise of the learn-then-delete pipeline.

---

## 10. Rules for AnthroForge

Each rule: do/avoid, the Hero Forge evidence, and the AnthroForge system it lands on.

**HF1 — Species is a preset bundle over parts, never a body lock.**
DO: represent every species (wolf, fox, orc, the Titan family) as a named bundle of part choices + a slider vector over shared slots — head, ears, muzzle, tail, body plan — and let users override any element after applying it. HF's fox→hyena-head build logs prove users *will* mix, and love the system for letting them.
AVOID: race-locked bodies (BG3's wall, R1) and species-as-monolith modelling.
*Lands on:* species presets + swappable parts.

**HF2 — Partition by body plan; total freedom inside the partition.**
DO: define a small set of body plans (plantigrade biped, digitigrade biped, taur, naga…) as the hard structural boundary — parts declare which plans they fit; within a plan, everything mixes. HF's centaur/naga partition shows a hard line users accept *because* everything on their side of it is free.
AVOID: soft per-part compatibility chaos where any two parts *might* work — fit debt explodes combinatorially (HF still ships per-part geo fixes weekly, a decade in, even *with* the partition).
*Lands on:* swappable rigged parts (plan-fit metadata on every part record) + R4's conflict metadata.

**HF3 — Parts-first presentation over a morph substrate.**
DO: present the library as visible, nameable parts; keep body/face/expression sliders underneath to absorb the variation parts can't. HF proves perceived depth = catalogue breadth × slider fine-tuning, and its newest heads quietly adopted morph tech (Face Customizer) *without changing the parts-first interface*.
AVOID: exposing the slider laboratory as the front door (Elden Ring) when a part choice would say it faster; or shipping parts with no morph layer and hitting the fit ceiling.
*Lands on:* editor UX + learned-morph sliders.

**HF4 — Charge (and gate) at export and at power tools — never at parts or editing.**
DO: if AnthroForge ever monetises, the HF evidence says the wall belongs on (a) geometry export, (b) pro capabilities (our kitbash-equivalent: free-attach + fit re-solve tools), while parts, presets and re-editing stay free. HF's Daggerheart part-pack backlash is the controlled experiment for what happens when you wall the *inputs*: a decade of goodwill spent in a week.
AVOID: paywalled part packs and paid re-edits (MHW, R7) — the two most resented moves in this entire survey, now with a third data point.
*Lands on:* product policy; export profiles (app blueprint §10).

**HF5 — Zones for rigid parts, decals for morphing surfaces.**
DO: ship every part with named colour zones (paint-by-numbers authoring discipline), and put markings/scars/patterns on a layered decal system for anything that morphs (heads, bodies) — HF literally migrated animal-head markings from zones to decals when its heads became morphable.
AVOID: texture-painting as the primary colour UX for non-artists; and zones on morph surfaces, where they smear.
*Lands on:* materials system; species markings; orc warpaint.

**HF6 — Make designs decomposable, and a remix economy appears.**
DO: store characters as independently swappable layers (species bundle / face vector / expression / pose / parts list / colour theme) with per-layer import — HF's Importing menu and its pose-donor "APR" minis show users spontaneously trading *layers*, not just characters. This is R2's share code with structure: the code should address layers, so "steal this pose" is a first-class act.
AVOID: monolithic save files where borrowing one attribute means adopting the whole character.
*Lands on:* character file format + share codes; Titan family presets (borrow Sen's pose, keep your own build).

**HF7 — The export profile is a product: fused, scaled, print-checked.**
DO: AnthroForge's STL/print profile should do what HF's does — merge to a watertight posed mesh at a declared scale, apply a *strength pass* (auto-thicken with an off switch and a report), split the base as an option, and run printability validation before export (extending v2's GLB validation gates). HF's kitbash quiz is the UX version: make the user acknowledge physical impossibility *in the tool*, not at the printer.
AVOID: exporting raw rigged assemblies as "print ready"; and silent thickening — HF tells you it does it.
*Lands on:* STL/print export profile in the app blueprint; fursuit route (our 30 mm is their life-size, but the thickening/validation logic transfers directly).

**HF8 — Keep custody of the user's editable design.**
DO: character files are user-held files (our format), exportable and archivable without the vendor's server. HF's six-month download guarantee and server-side configs are the cautionary tale: a decade of users' creative work exists at one company's pleasure.
AVOID: config-on-our-server as the only editable form of a character.
*Lands on:* data model + MCP connector design (the connector should read/write user files, not a hosted library).

**HF9 — Plan the compatibility migration before you need it.**
DO: version part records and head systems from day one (HF's Face Customizer generation split + convert-on-edit + "keep a copy" warning is the least-bad template), and make conversion *loss-reporting*, not silent.
AVOID: discovering at v3 that v1 parts can't express v3 morphs, with users' saved characters as the battlefield.
*Lands on:* part record format; learned-morph versioning.

**HF10 — Let committed users break the fit rules — with the risk labelled.**
DO: ship a kitbash-equivalent free-attach mode (R9) with HF's two governance additions: gate it behind intent (a "workshop mode" toggle, not necessarily money) and attach printability/conformance warnings to the result instead of blocking it (matches R4's conformance flag).
AVOID: free-attach with no risk signalling (SCVI's patched-after-scandal route).
*Lands on:* free-attach slots + extremes regime.

---

## 11. Sources

- Hero Forge — Color support doc (zones, presets, paints/material categories, Mix base/layer/highlight, decals): https://heroforge.com/content/support-docs/color/
- Hero Forge — Face Customizer FAQ (unified zones enabling morphology/expression blending; conversion behaviour; compatibility icon): https://heroforge.com/content/support-docs/face-customizer/
- Hero Forge — Importing support doc (per-layer import: Species/Face/Expression/Pose/Kitbash Parts/Theme Colors; APR pose donors): https://heroforge.com/content/support-docs/importing/
- Hero Forge — Subscriptions page (Pro/Pro+ structure and upgrade terms): https://heroforge.com/content/product-information/subscriptions/
- Hero Forge — Release Notes (weekly content drops; zone/geo fix rate; decal layering work): https://heroforge.com/content/news/release-notes/
- Know Direction — Hero Forge Color review (species = preselected Head/Body options; fox build walkthrough; expression sliders; colour presets): https://knowdirectionpodcast.com/2020/08/alex-analyzes-here-we-are-in-the-future-a-hero-forge-color-review/
- SkipTheCAD — Hero Forge generator profile (STL: 30 mm, 1-inch base, ≤100k tris, separate-base option, strength adjustments, two free samples, personal-use terms, 6-month download guarantee): https://skipthecad.com/generators/heroforge/
- Guideflow / Char-Gen / Cartosmith pricing checks, Oct–Nov 2026 (Pro $3.99–5.99; Pro+ $14.99–19.99 with 5 credits; packs $7.99): https://www.guideflow.com/blog/character-creation-software · https://char-gen.com/blogs/top-10-dnd-character-creator-tools · https://sprite.cartosmith.app/dnd-token-makers-compared/
- Wargamer — Hero Forge prices & kitbash review (STL $7.99; physical tiers; kitbash bone control, 20 pieces, printability warnings): https://www.wargamer.com/hero-forge · https://www.wargamer.com/dnd/hero-forge-kitbash-grimdark
- OnTableTop — Hero Forge 2.0 launch (42 species in 2020; colour system): https://www.ontabletop.com/news/heroforge-2-0-makes-a-splash-with-a-colorful-launch/
- DeviantArt build log — "Building a Hero Forge Galian Beast" (Giggle-Dog species start, Hyena Head + Canine Ears + Straight Tail overrides — cross-species mixing in practice): https://www.deviantart.com/no-soupforyou/journal/Building-a-Hero-Forge-Galian-Beast-873441207
- TechRaptor / TheGamer / EGW — Daggerheart Collaborator Collections ($7.99 per ancestry part-set; fan backlash): https://techraptor.net/tabletop/news/hero-forge-launches-new-collaborator-collections-series-featuring-daggerheart · https://www.thegamer.com/critical-role-hero-forge-paid-daggerheart-collaboration/
- GeekNative — ToS mythbusting (Sky Castle retains ownership of 3D Models; personal noncommercial use; no resale/redistribution; prints may not be sold): https://www.geeknative.com/131759/mythbusting-can-you-instagram-your-hero-forge-models/
- Plagiarism Today — Hero Forge ToS controversy (Character Design IP assignment clause + Sky Castle's clarification): https://www.plagiarismtoday.com/2020/10/19/hero-forge-and-the-copyright-controversy-over-miniatures/
- GameFromScratch — Hero Forge as a game-dev tool, licence analysis ("not rigged for animation" FAQ; personal-use licence): https://gamefromscratch.com/hero-forge-this-could-be-an-awesome-game-development-tool/
- Vivu — Hero Forge FAQ mirror (STL zips ~5–10 MB, tessellated, unrigged; physical from $19.99, STL digital $7.99): https://vivu.tv/what-is-hero-forge/

*Verification note: Hero Forge does not publish a single canonical species list or part count; species counts are dated to their sources (42 in 2020, growing weekly since). Prices are as published on pages crawled in November 2026 and should be re-verified before any commercial decision. The STL mesh facts (fused/single mesh, ≤100k tris, 30 mm, separate-base option, strength pass) are consistent across Hero Forge's own help material as summarised by SkipTheCAD and the FAQ mirrors.*
