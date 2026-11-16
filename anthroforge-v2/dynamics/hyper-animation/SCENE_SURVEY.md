# Hyper Animation — Artist Scene Survey

Run: Nov 12, 2026 (Joe: "check out hyper animations different artists have done").
Method: web/social search across Bluesky, X-indexed pages, YouTube, FurAffinity (via mirrors/archives), itch.io, Gumroad/Ko-fi product pages, VRChat wiki — starting from the roster in `~/workspace/character_assets/bara-hyper-artists/MANIFEST.md` and expanding to animators specifically. One work was frame-sampled at 5 FPS per Joe's media rule (see §3.1); the sample was deleted after analysis. **Study only — nothing downloaded for keeping, nothing redistributed.** Downloads this run: one 843 KB video, sampled and deleted; scratch cleaned.

Tags: **[V]** = technique verified from the work itself or the artist's own spec sheet · **[D]** = described by artist/storefront, not frame-checked · **[I]** = inferred from pipeline, treat as hypothesis.

---

## 1. The headline finding

The scene's hyper motion splits cleanly into the same two channels as its hyper *modelling* (body-diversity sweep verdict), plus a third channel for life:

1. **Growth over time** = an animated parameter, not a new model. 2D artists step a drawn silhouette through pulses; 3D artists drive blendshape weights (and bone scale for length/height) along a curve. Nobody re-sculpts per frame.
2. **Softness in motion** = spring systems, never keyframes. VRChat's PhysBones/SquishyBones, VRM spring bones, and Blender cloth-proxy jiggle rigs all do the same job: a chain/cloth sim with stiffness, damping, gravity — parameterised per part, exactly the data format our SOFT_DYNAMICS spec already targets.
3. **Size changes the movement vocabulary.** The most sophisticated work (Hypermancer) swaps locomotion sets at size thresholds and scales stride/animation speed with size. Growth that doesn't change *how the body moves* reads as a balloon; growth that does reads as mass.

---

## 2. Roster — hyper animators

### 2D animators

| Artist | Where | Hyper motion | Technique |
|---|---|---|---|
| **FattyDragonite** (Luke Bouwhuis, NL) | YouTube (channel "Corruptorlugia"), FA /user/fattydragonite, Bluesky @fattydragonite.bsky.social, X @FattyDragonite | The fandom's reference WG animator — animated fat/growth shorts ("Million Calorie Burger", "Morning Jog", "Lardizard Binge", "BOBSLED"); **2022 Ursa Major Award winner** for animation. Full YouTube archive mirrored on archive.org | Hand-drawn 2D, growth as **stepped silhouette pulses + fold accretion** — frame-sampled, see §3.1 **[V]** |
| **Unnymations** (@unknownwolf.bsky.social) | Bluesky; mods r/AnimatorFurries | 2D muscle-growth animation, pec-focused growth loops ("Animating pecs to life") | Hand-drawn 2D growth, extreme overshoot on the growing part **[D]** |
| **trash_eaterr** | TikTok (reposted widely, e.g. Instagram @bellyfatfurry) | Rapid belly-inflation loops: slim dog → belly to the knees in seconds, pats it, sits down under the weight | 2D loop; growth continuous-fast, then the *settle* (sitting because of size) sells the mass **[D]** |
| **Tibba** | Instagram/TikTok loops (signature "@Tibba" on the work) | Static-pose belly jiggle loops — huge abdomen in a straining shirt, jiggle shown with motion lines | 2D; jiggle as a 2–3 drawing oscillation loop + motion-line convention, no sim **[D]** |
| **FluffleStuff** (@flufflestuff.bsky.social) | Bluesky, FA | Fat/inflation animation commissions (incl. blueberry inflation), all mouse-drawn; posts foley/sound work too | Hand-drawn 2D, full-body squash as the body fills **[D]** |
| **Gillpanda** (Battu) | linktr.ee/Gillpanda, Bluesky | Professional furry animator/comic artist; WG sequences mostly stills, some animated work | 2D; sequence-first (key poses carry the growth, in-betweens sparse) **[D]** |
| **Ritz** (RitzBeretta) | FA, DeviantArt, WikiFur entry | Growth/hyper art since 2006 incl. Flash animation era work; "GrowthAvatar" craze | Flash-era vector tweens — growth as interpolated scale of grouped shapes **[D]** |
| **Charem** | FA (historical) | Classic Flash-era furry WG animations/games | Flash symbol-tween growth **[D, historical]** |

### 3D animators

| Artist | Where | Hyper motion | Technique |
|---|---|---|---|
| **Nighdruth** (@nighdruth.bsky.social) | Patreon /c/nighdruthANIMATIONS, Bluesky, FA | **The 3D growth-animation specialist.** Long-form (3–4 min) muscle/hyper growth commissions; current project: alien symbiote character drinks growth serum — muscles swell, genitals lengthen/thicken, height increases to macro, over minutes. Model overhauled mid-project to be "extra juicy and clean" | 3D (Blender-class pipeline); growth = **blendshape weights + bone scale animated together over long curves**, staged in waves (slight growth → indulgence → explosive growth) **[D/I]** |
| **Sombreve** | itch sombreve.itch.io, Patreon, Telegram "Sombreve Growth Chamber" | **Hypermancer** (Unreal, fully 3D bara growth RPG): growth is gameplay — and **at size thresholds the character gets new run/walk animations, longer stride distance, slower animation playback**; procedural hand-placement animation; cel-shaded "playable growth comic" look. Rev VRChat base: 15 per-muscle blendshapes, dynamic pec deformation, auto bicep flex | Blendshape growth driven by a stat; **locomotion set switches + stride/speed scaling with size**; clothes blend transitions sped up as size system matures **[V — devlog 0.0.7]** |
| **Yosebose** (Billy) | Patreon /c/Yosebose, Bluesky | "Growth and Muscle Animator & 3D artist" — growth animation commissions | 3D growth, blendshape-driven **[D]** |
| **Fouzoul** (@fattypaca) | Bluesky, YouTube @fattypaca | Self-described "3D fat animator" — fat-focused 3D animation | 3D fat animation **[D]** |
| **SnakeMayo** (@snakemayo.gay) | Bluesky | NSFW 3D artist/animator, furry | 3D animation, hyper-adjacent **[D]** |
| **Zero Visuals** | YouTube @realzerovisuals + @musclegrowthworld, Patreon | 3D muscle-growth transformation *videos* with story — skinny→huge over a narrative. **Human, not furry** — included as the clearest public example of long-form 3D growth timing | 3D morph growth, growth paced to story beats **[D]** |
| **Monty** (washbearmonty) | Bluesky, Telegram "Monty's Tiddy Jiggle" | 2D/3D bara animator (roster, round 1) — channel name alone tells you the specialisation: chest jiggle | Mixed 2D/3D; jiggle as a signature **[D]** |

### Avatar/VRChat — hyper and soft motion as a *system* (the most directly stealable work)

| Who / what | Where | Technique |
|---|---|---|
| **RitualNeo — Fat Wickerbeast DLC** | ritualneo.gumroad.com/l/fatwickerbeast, Ko-fi | The single most instructive spec sheet found. One fat control parameter drives: **1 fat blendshape + 5 squish blendshapes + 2 breathing blendshapes (with a Unity idle animation) + 3 rigged bones, one of them a weight-painted dynamic (spring) bone + PhysBone collision that RESCALES with size + animated collision receivers**. Size, softness, breathing and collision all slaved to one "fat" value **[V — product page]** |
| **Wolke — avatar line + WLK_MEAT** | wolkehond.itch.io, Twitch build streams | Every avatar ships "jiggle physics" as a headline feature (VRC PhysBones + VSeeFace/VSF spring physics for the VTuber versions); anatomy sliders animated in showcases. The jiggle is a *selling point in the title block*, not a footnote **[D]** |
| **Arkoren Art — Spectrum Redux / Bunnic** | arkorenart.itch.io | Body blendshapes exposed as **in-game sliders** (thin→fully chubby/round, per-part limb thickness); PhysBones on belly specifically "**at larger body sizes**" — physics chains enabled/tuned conditional on the size value; breathing toggle; boop-contact snoot squish (contact → blendshape) **[V — product page]** |
| **Ghostly — PapaGen** | Docs PDF (kemono mirror) | Muscle↔fat body slider that **cross-fades two materials** (muscle texture ↔ no-muscle texture) in step with the blendshape — definition disappears via texture as fat covers it **[V — documentation]** |
| **The VRChat platform itself** | wiki.vrchat.com (PhysBones, Animations) | PhysBones (2022): spring chains with pull/spring/gravity per chain, grabbable. **SquishyBones (2023): dedicated squash-and-stretch bones** — volume-preserving squash as a first-class component. Avatar animation clips can keyframe **blendshape weights, bone scale, and PhysBone parameters** — so "growth animations" in VRC are literally parameter timelines **[V — wiki]** |
| **ZarZar-line showcase avatars** (Stein, Kira, Xia, Nalo, Reyna…) | Payhip | "Physbones / Body Jiggle Physbones" is boilerplate in every listing; showcases are *dance videos* — jiggle quality is judged in locomotion/dance, filmed by credited showcase videographers. The market's QA bar for soft motion is "does it read while dancing" **[D]** |

### Tooling evidence (what the 3D scene actually uses for jiggle)

| Tool | What it is | Why it matters to us |
|---|---|---|
| **GOE Jiggle Studio Adult** (SuperHive, $19.99) | Blender add-on: cloth-sim **proxy presets** (Chest S/M/L, Belly, Glute, Thigh, Generic Soft Part) bound to the mesh via Surface Deform; **Ripple Maker** for localised contact/impact deformation; bake tools | The belly/teat/sac case is exactly its preset list; proxy-cloth → surface-deform is a viable alternative to spring bones for *authored* (non-runtime) soft motion, and Ripple Maker is contact deformation as a productised feature **[V — product page]** |
| **EXea Jiggle** (Blender Extensions) | Spring-bone jiggle layers for Blender armatures, per-layer stiffness/damping/gravity, **bakes to plain keyframes** | Spring-bone authoring inside Blender with a bake-out — matches our "dynamics are data, baked as bone animation" prototype route **[V — extension page]** |
| **Blender Spring Bones add-on** (the long-standing one) | Per-bone spring + rotation in Pose Mode, interactive | The tutorial-scene standard (countless jiggle tutorials); same parameter vocabulary as VRM SpringBone **[D]** |

---

## 3. Work notes

### 3.1 Frame-sampled: FattyDragonite — "Million Calorie Burger — WG quickie" (2D) **[V]**

Source: archive.org mirror of his YouTube (843 KB IA mp4, 854×480, 15 fps, 9.8 s). Sampled at 5 fps (49 frames), contact-sheet read, file deleted.

- **0.0–1.2 s** — Charizard (already round) holds the burger, looks about, smiles. Setup holds; nothing grows.
- **1.4–2.6 s** — The bite: head throws back, huge chomp, chew with eyes squeezed shut. Anticipation and chew are given *more* time than the growth that follows.
- **2.8–4.0 s** — Swallow; growth starts **subtly and in the neck/chin first** — the jawline thickens before the belly visibly moves.
- **4.2–5.4 s** — Belly pushes out in a **pulse**, then a short hold. Expression hasn't caught up yet.
- **5.6–6.8 s** — Second, bigger pulse; the belly gains **fold lines** — new creases appear as it expands, so volume reads as layered rolls, never a smooth balloon. Head sinks relative to the rising chest line (mass grows *up around* the head too). Eyes widen — reaction lags the growth by ~half a second.
- **7.0–8.4 s** — Final pulse to full size; torso is now a stacked-fold mass wider than the frame's old silhouette. At ~8.2 s the belly outline **drops slightly past its line and eases back** — a one-beat squash-settle that sells the weight landing.
- **8.6–9.8 s** — Hold at final size: expression cycles alarm → resigned contentment; belly contour keeps a faint breathing-scale micro-motion.

**Transferable rules:** (a) growth in **pulses with holds**, not a continuous ramp — each pulse ≈0.4–0.6 s, holds between; (b) **proximal-first ordering** — neck/chin thicken before the belly peak moves; (c) **fold accretion** — surface detail (creases) is *added* as volume grows, it's what separates fat from inflation; (d) **reaction lag** — the face responds ~0.5 s after the body; (e) **settle overshoot** — one downward overshoot-and-recover on the mass at growth end; (f) breathing micro-motion on the held final state so the result isn't a statue.

### 3.2 Hypermancer (Sombreve) — growth that re-choreographs the body **[V, devlog]**

From the 0.0.7 devlog, verbatim facts: "Added new run/walk animations when players reach a certain size." / "Growing in size now increases your distance travelled and slows your animations." / "Improved some hand placements in some procedural animations." / "Made blend transition between clothes faster."

Read: size is a continuous stat (blendshapes), but **locomotion is thresholded** — discrete gait sets keyed to size bands, with stride length and playback rate scaled inside a band. This is precisely our BODY_PLANS "plan carries its own locomotion set" doctrine, with size bands playing the role of sub-plans. It is the only surveyed work where growth changes *gait*, and it's the difference between "bigger" and "heavier".

### 3.3 RitualNeo Fat Wickerbeast — one parameter, five systems **[V, product page]**

The architecture worth copying outright: a single user-facing **fat control** fans out to (1) shape blend, (2) **squish blendshapes** (contact/idle deformation vocabulary), (3) **breathing** (2 shapes + looping animation — the "alive at rest" layer), (4) a **weight-painted dynamic bone** (spring layer for the belly mass), (5) **collision that rescales with the fat value** (PhysBone colliders + animated receivers). Every subsystem we've specced separately — hyper ranges, soft dynamics, contact — is here already integrated behind one dial, on a bara-adjacent base (Wickerbeast), in the wild.

### 3.4 Nighdruth — long-form 3D growth pacing **[D]**

His commissions run 3–4 **minutes** of growth (vs the 2D scene's 10 s). The published plot structure for the alien piece: incidental small growth → character seeks more → massive growth event (muscles, genitals, height to macro) → release. Pacing lesson: at 3D fidelity, growth is staged in **acts with plateaus**, and the model itself was rebuilt mid-project for the growth to read ("extra juicy") — i.e. the *base* was re-authored so the morph extremes hold up, the same conclusion as our hyper-range failure-mapping.

---

## 4. Technique taxonomy (what to steal, mapped to our systems)

| Technique | Who proves it | Our system it feeds |
|---|---|---|
| Growth as animated blendshape weight + bone-scale (length/height) | Nighdruth, Sombreve, VRC growth clips | Hyper ranges: two-channel rule holds in animation too |
| **Pulsed growth timing** (pulse → hold → pulse), proximal-first | FattyDragonite **[V]** | Growth-curve presets for the dynamics layer: ease curves should be stepped, not linear |
| Fold/crease accretion with volume | FattyDragonite **[V]** | Hyper morph authoring: detail shapes keyed to growth % (crease shapes fade in with the mass) |
| Settle overshoot on mass at motion/growth end | FattyDragonite, trash_eaterr (sit-down) | Spring params: under-damped settle on belly/sac chains |
| Locomotion set switches + stride/rate scaling at size thresholds | Hypermancer **[V]** | BODY_PLANS: size bands as locomotion sub-plans |
| One master size parameter fanning out to shape + squish + breath + spring + collision scale | RitualNeo **[V]** | Character record: `size` drives dynamics params (spring gravity/stiffness scale with part volume) |
| Squish shapes as a named vocabulary (5 squish blendshapes) | RitualNeo | Contact system: squish = blendshape set, contact = spring/proxy — both, not either |
| Breathing as 2 shapes + loop, slaved to size | RitualNeo, Arkoren | Idle layer in the dynamics spec |
| Definition cross-fade via material/texture with fat % | Ghostly PapaGen **[V]** | Muscle×Tissue model: definition attenuation gets a *texture* channel, not just geometry (matches our A-curve attenuation — this is its runtime form) |
| Spring chains per soft part, params per chain (stiffness/damping/gravity) | PhysBones, VRM, EXea Jiggle, Wolke line | SOFT_DYNAMICS chain records — the vocabulary is already standard; adopt it verbatim |
| Squash-and-stretch bones (volume-preserving) | VRChat SquishyBones | Sac/teat chains: squash on impact axis, stretch on swing axis |
| Cloth-proxy → surface-deform jiggle + ripple contact | GOE Jiggle Studio | Authored-animation route for renders/film, vs spring bones for runtime |
| Physics enabled/tuned conditional on size value | Arkoren Spectrum (belly PhysBones "at larger body sizes") | Dynamics records need an activation range on the size parameter, not just params |
| Growth reaction lag (face follows body ~0.5 s) | FattyDragonite **[V]** | Expression system: emotion vectors get a delay parameter on growth events |

---

## 5. Shortlist — most instructive examples (in order)

1. **RitualNeo, Fat Wickerbeast DLC** (ritualneo.gumroad.com/l/fatwickerbeast) — the integration pattern: one fat dial → shape/squish/breath/spring/collision. Read the product page as a spec; it's the closest existing thing to our intended architecture.
2. **Sombreve, Hypermancer devlogs** (sombreve.itch.io/hypermancer) — the only growth work that re-choreographs locomotion at size thresholds. Directly validates BODY_PLANS locomotion sets; watch for future devlogs on the Rev base's dynamic pecs/auto-flex.
3. **FattyDragonite, "Million Calorie Burger" + "Morning Jog"** (archive.org/details/FattyDragonite-Youtube-Archive) — 2D timing masterclass: pulsed growth, proximal-first, fold accretion, settle overshoot. §3.1 has the frame notes; "Morning Jog" is the one to sample next for growth *in locomotion*.
4. **Nighdruth's growth commissions** (bsky.app/profile/nighdruth.bsky.social, patreon.com/c/nighdruthANIMATIONS) — long-form 3D growth pacing and base-rebuilding for morph extremes; the "Alien Growth" WIP posts are a public production diary.
5. **VRChat PhysBones + SquishyBones docs** (wiki.vrchat.com) — the standard parameter vocabulary our soft-dynamics records should speak; SquishyBones' squash model is the teat/sac impact behaviour.
6. **GOE Jiggle Studio Adult** (SuperHive) — cloth-proxy jiggle + ripple contact as a shipped Blender workflow; the authoring-side counterpart to runtime springs.

## 6. Gaps / honest limits

- Bluesky/X video posts (Nighdruth's clips, Unnymations' loops) are described from post text and previews, not frame-sampled — the platforms don't expose clean small downloads to this VM. The one frame-sampled work (FattyDragonite) came from the archive.org mirror of his own channel.
- Drages (the FA dragon-inflation animator) did not surface in this run's searches — the name may be misremembered or delisted; not rostered rather than guessed.
- Fek's **Rack 2** is confirmed as a deep-customisation 3D furry game, but no public source in this run documents growth *animation* technique specifically — left off the roster's technique claims.
- Prices/availability not re-verified this run except where quoted from pages actually read (RitualNeo spec via search-indexed page text; GOE $19.99 from its SuperHive page).
