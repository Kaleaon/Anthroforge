# Hyper Animation — Craft & Timing Extraction

*Compiled Nov 12, 2026 (Joe: "check out hyper animations different artists have done").
Feeds: the soft-tissue dynamics spec (`dynamics/SOFT_DYNAMICS.md`, sibling work), the
Kaleaon unique-anatomy parts (`parts-lab/kaleaon-anatomy/`), and the hyper-range
architecture (`hyper/HYPER_RANGES.md`, sibling work).*

## 0. Method & honesty box

**Tag discipline** (house standard): **[S]** = sourced from a named publication, guide,
or artist statement · **[M]** = measured in this run (method stated) · **[E]** = estimate /
calibration fit, for first builds to tighten. Nothing in §7's parameter table is presented
as measured from an artist's scene file — no artist scene files were available; the table
is *derived* from the sourced ranges and the measured model in §2, and says so per row.

**What was actually examined:**

| Source | Kind | What was extracted |
|---|---|---|
| Roster in `character_assets/bara-hyper-artists/MANIFEST.md` | Starting map | Wolke (WLK_MEAT hyper anatomy, VRChat), Sombreve (Hypermancer growth games + Rev base), Monty / washbearmonty (2D/3D bara animator, "Tiddy Jiggle" channel), BruBearBrown (2D hyper), Nicoreda's belly/WG side channel |
| Loay Shaban — ragdoll-dynamics muscle-jiggle tutorial (via 80.lv report, Jul 2026) | 3D craft | Belly/neck/thigh jiggle on a gorilla-lioness creature; controller categorisation; stiffness ↔ frequency+amplitude; "Record to Layer" exaggeration check [S] |
| YasuhikoArts — "Jiggle walk" test (DeviantArt, Aug 2025) | 2D/3D test | Artist's own critique: extra-heavy unsupported bounce works, but **side-to-side swing is what's missing** [S] |
| FattyDragonite — door/inflation loop (via Instagram summaries) | 2D growth gag | Instant-gain staging: mundane action → exhale → growth completes in a few seconds → deadpan hold [S] |
| ChonkyArtBun — post-buffet waddle loop (via Instagram summaries) | 3D hyper walk | Slow waddle, camera lowers to the mass, sit-down as the loop's terminal gag — gait + staging evidence [S] |
| Jeff-3659 — "Oxyna Temptation" GIF (DeviantArt, Dec 2023) | 2D loop GIF | Metadata only: 560×560, 3.53 MB, tagged loop/belly/thighs — a seamless idle-loop inflation/belly piece; the file itself sits behind DeviantArt's tokenised CDN and was **not** downloaded [S] |
| Nighdruth Animations — "Alien Growth" commission WIP (Patreon via Pawchive, Oct 2026) | 3D growth staging | 3–4 min growth narrative structure: incidental small growth → reaction/enjoyment beat → voluntary massive growth → environment can't contain it [S] |
| VRChat PhysBones docs + VRC School + community guides | Runtime tuning | Parameter semantics and ranges (§7 anchors) [S] |
| VRM SpringBone spec / UniVRM-lineage docs / bevy_vrm, VRM4U | Runtime tuning | Verlet step, stiffness/drag/gravity ranges and defaults [S] |
| Unity Dynamic Bone guides (Steam/Melody's Escape 2 mod guide; COM3D2 wiki) | Runtime tuning | Recommended Damping 0.01–0.3, Elasticity 0.1–0.3, Stiffness 0–0.1, Gravity Y −0.05…−0.1 [S] |
| TavernGuests jiggle config (Nexus Mods) | Runtime tuning | A shipped jiggle preset with numbers: **Frequency 3 Hz, Damping 0.25 (0.1 = long bounce, 1 = no overshoot), MaxAngle 25°**, plus the warning that **below ~2.5 Hz the jiggle resonates with footsteps** [S] |
| Obesity gait literature (Spyropoulos 1991; Browning & Kram 2006; 2024 gait meta-analysis) | Biomechanics | Stride/cadence/width/stance numbers in §5 [S] |
| Animation-principle literature (Thomas & Johnston via Lasseter 1987; Goldberg, *Character Animation Crash Course*; walk-cycle timing guides) | Craft | Timing/anticipation/follow-through scalings in §3–§4 [S] |
| **Own driven-spring simulation** (this run, §2) | **[M]** | Phase lag, amplitude gain, overshoot and settle for four mass classes under a walk drive, computed with a 240 Hz second-order model and reported at 24 fps and 5 FPS sampling |

**What could not be done, plainly:** frame-by-frame extraction from the artists' actual
videos. Bluesky/X/YouTube/Instagram video is platform-walled from this VM (the project's
standing finding: yt-dlp hits a bot sign-in wall; social video plays only in Joe's
browser). No clip was downloaded in this run — the one candidate GIF was token-gated.
So the frame-level numbers below come from (a) the published tuning/gait data above and
(b) a transparent simulation of exactly the spring every runtime in §7 implements,
sampled the way a frame analysis would sample it. Where a rule rests only on the
simulation, it is tagged [M]; where it rests on judgement over the corpus, [E].

**A sampling warning that falls out of the method:** Joe's media rule (sample video at
4–6 FPS) resolves sac-, belly- and hyper-scale motion fine (all < 1.5 Hz), but
**aliases teat/ear-scale bounce (2.5–3 Hz)** — at 5 FPS a 2.8 Hz bounce folds to an
apparent 2.2 Hz and its lag reads wrong. Small parts need full-rate sampling; big
parts are exactly the ones 5 FPS is good for.

---

## 1. The one-sentence version

Hyper mass does not move *with* the body; it moves **after** it, **slower** than it,
**longer** than it, and — past a threshold — **instead of** it, surging at its own
natural frequency while the body steps underneath. Every rule below is that sentence
with numbers on it.

## 2. The physics backbone (why the numbers are what they are)

A soft part on a spring chain is, to first order, a damped second-order system.
Two frequencies matter, and animators who conflate them get mush:

- **Bounce (spring) frequency** — vertical jiggle:
  `f = (1/2π)·√(k/m)` — heavier (↑m) or softer (↓k) ⇒ slower. [S]
- **Sway (pendulum) frequency** — side-to-side / fore-aft swing of a hanging mass:
  `f = (1/2π)·√(g/L)` — depends on **hang length L, not mass**. A longer drape swings
  slower no matter what it weighs. [S]

Pendulum frequencies for the drape lengths this project actually builds [M]:

| Hang length L | 0.04 m | 0.10 m | 0.20 m | 0.30 m | 0.50 m | 0.65 m | 0.80 m |
|---|---|---|---|---|---|---|---|
| Sway f | 2.49 Hz | 1.58 Hz | 1.11 Hz | 0.91 Hz | 0.70 Hz | **0.62 Hz** | 0.56 Hz |

(Kaleaon's sac drape is the 0.65 m row by design — canon is extreme-low drape,
"when in doubt, lower and longer". Its sway period is ~1.6 s. It *cannot* swing
step-by-step at any walk cadence; see Rule 14.)

**Damping ratio ζ** sets the character of the settle: step overshoot is
`exp(−πζ/√(1−ζ²))` — ζ 0.28 ⇒ 40% overshoot, ζ 0.18 ⇒ 56%, ζ 0.15 ⇒ 62%,
ζ 0.11 ⇒ 71% [M]. Flesh that reads "heavy-soft" in the corpus lives at ζ ≈ 0.10–0.20:
it overshoots *more than half* its displacement once, visibly, then argues about
stopping for another cycle or two. ζ ≥ 0.4 reads as muscle or rubber; ζ ≤ 0.07
reads as jelly/water and breaks the weight read (it settles *too* long — see Rule 9).

**Measured driven response** [M] — each class modelled at its §7 starting frequency
and ζ, driven by the vertical bob of a walk (normal = 2.0 steps/s; heavy = 1.35
steps/s, §5), 240 Hz integration:

| Class (f_n, ζ) | Drive | Phase lag | Lag @24 fps | Amplitude gain | Settle to 10% after drive stops | Step overshoot |
|---|---|---|---|---|---|---|
| Teat (2.8 Hz, 0.28) | normal 2.0 Hz | 39° | 1.3 f | ×1.58 | 0.30 s | 40% |
| Teat | heavy 1.35 Hz | 19° | 1.0 f | ×1.23 | — | — |
| Sac (1.15 Hz, 0.18) | normal 2.0 Hz | 163° | 5.4 f | ×0.47 | 1.53 s | 56% |
| Sac | heavy 1.35 Hz | 132° | **6.5 f** | ×1.76 | — | — |
| Belly (1.35 Hz, 0.15) | normal 2.0 Hz | 160° | 5.3 f | ×0.78 | 1.56 s | 62% |
| Belly | heavy 1.35 Hz | **90°** | 4.4 f | **×3.33** | — | — |
| Full-hyper (0.70 Hz, 0.11) | normal 2.0 Hz | 175° | 5.8 f | ×0.14 | > 2 s (see Rule 9) | 71% |
| Full-hyper | heavy 1.35 Hz | 171° | **8.5 f** | ×0.36 | theory 2% settle ≈ 8.3 s | — |

Three load-bearing readings:

1. **The belly at a heavy cadence is a resonance machine.** When the step rate falls
   to the belly's own frequency (which is *why* heavy characters walk slower — §5),
   gain triples and the belly swings a quarter-cycle behind the hips. This is the
   single most recognisable "hyper walk" visual, and it is free if the frequencies
   are placed right.
2. **Full-hyper mass is above resonance at any cadence** (drive ≫ f_n): per-step gain
   collapses to ×0.14–0.36 and phase approaches 180°. The mass doesn't jiggle per
   step — it *ignores* individual steps and oscillates at its own ~0.6–0.7 Hz,
   driven by the accumulated pushes. Animating per-step jiggle onto full-hyper mass
   is the most common hyper-animation error.
3. **Small parts stay honest.** Teat-scale motion is nearly in phase (1 frame of lag)
   and settles in 0.3 s. If a teat-scale part lags 6 frames, it reads as a water
   balloon, not flesh.

---

## 3. Timing & anticipation — weight is frame count

**Rule 1 — Frames are mass.** At 24 fps a normal step is 12 frames; a tired/heavy
step is 20+ frames (≤ 1.2 steps/s) [S]. Budget every hyper action the same way:
if it takes the same number of frames as the lean version, no amount of jiggle
will make it read heavy.

**Rule 2 — Anticipation scales with the mass being moved.** Light action: 1–2 of
6 frames are anticipation (fast sprite norm) [S]; heavy actions invert the ratio.
Starting budgets at 24 fps [E, from the timing literature + §2 settle data]:
lean 3–4 f · bara 6–8 f · hyper 10–16 f (0.42–0.67 s) for a jump, a lift, a
stand-up, a turn initiation. The anticipation for a hyper stand-up is mostly the
*mass pre-shifting*: belly/sac swing slightly *away* from the intended direction
first (counter-swing), then the body commits.

**Rule 3 — Anticipation is done by the soft parts, not just the skeleton.**
Before a hyper character steps, the hanging mass settles *back*; before a stop,
it is still arriving. Pose the skeleton's anticipation subtle and let the lagging
mass supply most of the wind-up read — this is what the corpus's best loops do,
and it's why spring-driven parts beat hand-keyed jiggle: the anticipation is
automatic if ζ and f_n are right.

**Rule 4 — Slow-in is longer than slow-out for hyper.** Heavy mass accelerates
reluctantly and decelerates by overshoot, not by easing: use a long ease-in
(30–40% of the move), a comparatively committed middle, and replace ease-out
with overshoot-and-settle (§4). A symmetric easeInOut on a hyper part is the
"floaty balloon" tell.

**Rule 5 — Holds are where hyper lives.** Growth sequences, landings, and stops
all need a true hold *on the skeleton* while the mass finishes arriving
(Rules 9, 21). A hold is not frozen: the skeleton holds, the soft parts are
still travelling. Budget the hold from the settle column in §2, truncated per
Rule 9.

## 4. Follow-through, lag, overshoot, settle

**Rule 6 — Lag budget by class (at 24 fps, heavy walk).** Teat-scale: **1 frame**.
Sac-scale: **5–7 frames**. Belly-scale: **4–6 frames**. Full-hyper: **8–9 frames**
— but see Rule 14: at full-hyper the lag concept breaks into sub-harmonic surge.
Use these as QA gates on our own bakes: measure peak-to-peak offset between the
driving bone and the soft part's lowest point. [M]

**Rule 7 — Chain lag compounds distally.** Each successive joint in a chain
arrives after the one above it (shoulder → elbow → wrist → fingers is the classic
statement [S]). On a soft chain, halve stiffness per joint down the chain
(a shipped spring-bone convention [S]) and the compounding happens by itself;
a uniform-stiffness chain moves like a rigid paddle and reads as a prosthesis.

**Rule 8 — Overshoot once, big; then argue briefly.** Target first-overshoot
40% (teat) → 56% (sac) → 62% (belly) → 71% (full-hyper) of the driving
displacement [M, from the §7 ζ values]. One big overshoot + 1–2 decaying cycles
is the flesh signature. Three or more full cycles read as jelly; zero overshoot
reads as a statue with a physics checkbox.

**Rule 9 — Never animate the full settle.** True settle-to-2% for belly/sac is
~3.1 s and for full-hyper ~8.3 s [M] — no shot holds that long. Artists truncate:
play the overshoot + first return (≈ settle-to-10%: teat 0.3 s, sac/belly ~1.5 s),
then either (a) cut, (b) loop-mask it (§6), or (c) keep the part in perpetual
low-amplitude idle motion (breathing, weight shifts) so "still settling" is
indistinguishable from "alive". Full-hyper idle is *never* at rest — Rule 26.

**Rule 10 — Squash is volume-preserving and contact-timed.** On footstrike the
belly/sac squash vertically and widen laterally: vertical −5–8% with matching
widening at bara scale, −10–15% at hyper [E]. The squash peak lands 1–2 frames
*after* foot contact (it's the mass arriving, Rule 6), and the rebound is the
overshoot of Rule 8. Squash on the same frame as contact reads as the *ground*
being soft, not the character.

**Rule 11 — Lateral is not optional.** The corpus's own self-critique (YasuhikoArts:
the bounce worked, "I would prefer a bit more swinging from side to side" [S])
generalises: vertical-only jiggle reads as a pogo stick. Pelvis roll drives a
lateral sway at **40–60% of the vertical amplitude** for sac and belly in a walk
[E], phase-shifted a quarter-cycle from the vertical (roll peaks at passing,
bob bottoms at double support). Teats sway laterally less (25–40%) — they're
carried by the chest, not the pelvis.

**Rule 12 — Categorise controllers, tune per category.** Shaban's tutorial makes
the point structurally: belly, neck, and thigh jiggle each get their own
controller set and parameters, and the exaggeration check is done per category
(record to a layer, eyeball, adjust) [S]. One global "jiggle amount" slider is
an anti-pattern; §7's per-class table is the correction.

**Rule 13 — Amplitude caps are anatomy, not taste.** Shipped jiggle configs cap
swing (e.g. MaxAngle 25° at chest scale [S]). Our caps: teat 20–25°, belly
chain joints 35–45° total, sac 60–75°, full-hyper 75–90° — enforced by angle
limits + collision, because past the cap the part interpenetrates the thighs/
ground and the weight read collapses into clipping. At extreme drape the
*ground and thigh contact* is the cap (Kaleaon canon: contact-truncated swing
is correct, not a bug).

## 5. Gait as mass increases

Measured human data, which the furry corpus exaggerates but does not contradict:

**Rule 14 — Cadence falls, and the soft parts change regime when it does.**
Obese vs lean walkers: stride length 1.25 m vs 1.67 m (**−25%**), stride width
0.16 m vs 0.08 m (**×2**; +30% in Browning & Kram's speed-controlled data),
slower cadence and speed, longer stance and double-support phases [S];
meta-analysis confirms gait speed ↓, cadence ↓, step length ↓, step width ↑,
stance/double-stance ↑ [S]. Peak vertical ground force is ~**+60%** at matched
speeds [S] — the footstrike the mass must answer (Rule 10) is genuinely harder.
Animation translation [E]: normal walk 2.0 steps/s → bara 1.6–1.7 → heavy
1.3–1.4 → full-hyper 1.0–1.15 steps/s, with stride shortening ~5% per class
beyond bara and step width growing ~25–30% per class (legs must clear the mass;
the waddle *is* the clearance).

**Rule 15 — The waddle is roll, timed.** Wider steps ⇒ pelvis roll amplitude
grows (roughly with step width) and the lateral mass sway of Rule 11 grows with
it. Roll frequency = step frequency; the soft lateral response lags it per
Rule 6. If the feet widen but the pelvis doesn't roll, the character reads as
walking on stilts around the belly instead of carrying it.

**Rule 16 — Bounce frequency is the class frequency, not the step frequency.**
Vertical bob of the *skeleton* stays locked to steps (2 bobs per stride). The
*soft parts* oscillate at their own f_n: teat ≈ per-step (f_n above cadence,
follows), belly ≈ resonant at heavy cadence (one big swing per step), sac ≈
one swing per step at heavy cadence but a half-cycle stale, full-hyper ≈
**one surge per two steps** (f_n ≈ cadence/2 — animate/bake it as a 2-step
cycle, or the loop will fight itself, §6). [M]

**Rule 17 — Heavier = lower, longer down.** Deepen the down pose and linger in
it: heavy-walk craft adds 1–3 frames of settle at each down and slows the
recovery out of it [S]. In curve terms: the pelvis vertical curve flattens at
the bottom and steepens never. Combined with Rule 14 this is most of the
"weight" in a walk — the jiggle is the garnish on this, not the meal.

**Rule 18 — Arms counter-swing less, brace more.** As mass rises, arm swing
amplitude drops and elbows carry slightly out (clearance + balance). Keep arm
lag teat-class (they're muscle-led, not hanging mass) even on a hyper body —
a common error is putting the whole character on the hyper lag budget.

**Rule 19 — Turning is a multi-beat event.** A hyper character does not pivot:
the turn is stepped (2–4 small steps for 180° [E]), the mass's pendulum keeps
the *old* heading for the first beat, wraps toward the thighs, and arrives
last, overshooting into the new heading. Single-frame pivots with hyper mass
are physically illiterate in a way audiences feel instantly.

## 6. Growth sequences

**Rule 20 — Growth is pulses and holds, never a ramp.** A linear scale ramp
spends 80% of its duration between 10% and 90% growth — it reads as a morph
slider being dragged [M, curve analysis §2 method]. The corpus's structures
agree: growth happens in **staged pulses** (each pulse an S-curve: logistic
10→90% compressed into ~60% of the pulse's own duration [M]), separated by
**reaction holds** where growth stops and the character (and audience) registers
the new size. Nighdruth's 3–4 minute structure is the long form: incidental
small growth → enjoyment/reaction beat → chosen massive growth → containment
failure [S]. FattyDragonite's gag is the short form: 0 holds before (mundane),
growth in a few seconds, one long deadpan hold after [S].

**Rule 21 — The settle after each pulse belongs to the NEW size.** Every pulse
changes m and L, so f_n drops and settle lengthens *as the sequence proceeds*.
Pulse 1 (belly-class) settles in ~1.5 s; the final pulse (hyper-class) needs
its overshoot truncated per Rule 9 or the ending drags. Conversely the
*first* pulse may use the old, faster settle. Baking one jiggle setting across
a whole growth sequence is wrong in a way that compounds.

**Rule 22 — Growth order follows storage order.** Fitness-morph and growth
corpus alike fill proximal/central first: chest & shoulders → abdomen →
hips/thighs → back & distal last [S for the morph corpus; E as a general
rule]. Within a pulse, parts grow in that order with 10–20% phase offsets —
simultaneous uniform growth reads as inflation of a balloon, sequential growth
reads as a body.

**Rule 23 — Secondary growth is delayed growth.** Hair/fur, clothing strain,
and the soft-part *response* (new mass begins to lag, sway, squash against
thighs/floor) arrive after the volume that causes them. Clothing failure
(seams, buttons) is staged at pulse *ends*, during the hold, never mid-pulse:
the hold is when the audience looks, so the hold is when things pop. [E]

**Rule 24 — Scale the camera's respect.** As growth proceeds, staging widens
or the frame is increasingly filled; the corpus's end-states (building-busting,
frame-filling sit-down [S]) are the same rule at gag scale. In app terms: a
growth preview should ease its framing out with size, or the final size reads
smaller than the identical mesh in a fixed frame.

## 7. Loop construction (idle & walk)

**Rule 25 — The loop period must be a common multiple.** A loop pops wherever
a soft part's phase doesn't close. With step period T_s and part period T_p,
loop at the smallest near-common multiple: e.g. heavy walk T_s = 0.74 s
(1.35 steps/s), belly T_p ≈ 0.74 s at resonance ⇒ 2-step loop closes cleanly;
sac T_p ≈ 0.87 s ⇒ use a 4-step loop (2.96 s ≈ 3.4 sac cycles — still not
closed) **or retune the sac stiffness so T_p divides the loop** (T_p = 0.74 s
or 0.99 s). Rule of craft: *tune the part to the loop, not the loop to the
part* — a ±10% stiffness change is invisible, a phase pop is not. [M/E]

**Rule 26 — Idle is a driven system, not a rest pose.** Idle drivers: breath
at 0.20–0.30 Hz (12–18/min) moving belly/chest at small amplitude, weight
shifts every 2–4 s exciting the pendulum modes, and the perpetual truncated
settle of Rule 9. A hyper idle loop is typically 4–8 s (breath × sway common
multiple), vs 2–4 s for a lean idle. If the hyper idle ever reaches true rest,
it reads as death, not calm. [E]

**Rule 27 — Walk loops: 2 steps for lean/bara, 4 steps for hyper.** Because
of Rule 16's two-step surge, a full-hyper walk needs a 4-step loop (2 surges)
to close without a visible period-2 pop in alternate steps — or accept and
hide the pop inside the footstrike squash (Rule 10), the busiest frame.
Left/right asymmetry (Rule 11's phase-shifted sway) also only closes on even
step counts. [M/E]

**Rule 28 — Loop the parameters, not just the pose.** In a growth-capable
system, a walk loop authored at one mass is wrong at another (Rules 14, 16,
21). Loops ship as *skeleton cycles*; the soft layer is simulated or baked
per mass class. This is the loop-level statement of the dynamics spec's core
decision: dynamics are data + runtime, never one baked jiggle.

---

## 8. Parameter table — starting values for the soft-tissue dynamics spec

Canonical columns are the spec's own terms (per-chain, applied root→tip with
Rule 7's halving gradient). Runtime columns are translations into the three
systems our exports target; they are **[E] starting points derived from the
sourced ranges cited**, to be tuned in-engine — with the canonical f_n / ζ as
the ground truth to tune *toward* (measure lag & settle in-engine against
Rules 6/8/9 and adjust).

**Class definitions** (by the part's own scale, not the character's):
**Teat-scale** — small pendant parts, hang ≤ ~6 cm, ≲ 0.5 kg (teats, small
dewlaps, ear tips ride one class stiffer). **Sac-scale** — hang 10–35 cm,
~1–15 kg per part (sac, sheath mass, tail base mass, cheek/ruff mass).
**Belly-scale** — the apron/pannus system, hang 15–40 cm, ~5–40 kg, anchored
across the abdomen rather than at a point. **Full-hyper** — any part whose
hang exceeds ~40 cm or mass exceeds ~40 kg, or a whole-body hyper composite
(Kaleaon's sac at canon drape sits on the sac/full-hyper boundary: use
sac-scale bounce with full-hyper sway).

| Parameter | Teat-scale | Sac-scale | Belly-scale | Full-hyper |
|---|---|---|---|---|
| **Natural frequency f_n (bounce)** | 2.5–3.0 Hz | 1.0–1.3 Hz | 1.2–1.5 Hz | 0.6–0.8 Hz |
| **Sway (pendulum) f** — from hang L | 2.2–2.5 Hz (L≈5 cm) | 0.9–1.1 Hz (L≈25 cm) | 0.85–1.0 Hz (L≈30 cm) | 0.55–0.70 Hz (L 50–80 cm) |
| **Damping ratio ζ** | 0.25–0.30 | 0.16–0.20 | 0.13–0.17 | 0.09–0.13 |
| **Step overshoot target** | ~40% | ~56% | ~62% | ~71% |
| **Lag @ heavy walk (24 fps)** | ~1 f | 5–7 f | 4–6 f | 8–9 f / sub-harmonic |
| **Settle to 10% (truncate here)** | ~0.3 s | ~1.5 s | ~1.5 s | ~2 s visible, then loop-mask |
| **Gravity scale** (1.0 = full sag to rest-under-gravity) | 0.3–0.5 | 0.8–1.0 | 0.7–0.9 | 1.0 (contact-capped) |
| **Max swing (chain total)** | 20–25° | 60–75° | 35–45° | 75–90° (contact-capped) |
| — *VRM SpringBone* — stiffness (0–4) | 2.5–3.5 | 0.8–1.2 | 1.0–1.5 | 0.35–0.60 |
| VRM dragForce (0–1) | 0.55–0.65 | 0.35–0.45 | 0.30–0.40 | 0.22–0.32 |
| VRM gravityPower (0–2) | 0.3–0.6 | 1.2–1.8 | 0.8–1.2 | 1.5–2.0 |
| VRM hitRadius | part radius ×0.8 | part radius ×0.9 | per-node, abdomen capsules | part radius, + thigh/ground colliders mandatory |
| — *VRChat PhysBones 1.1 (Advanced)* — Pull | 0.45–0.60 | 0.18–0.28 | 0.25–0.35 | 0.08–0.15 |
| PhysBones Momentum | 0.30–0.40 | 0.65–0.80 | 0.60–0.75 | 0.80–0.95 |
| PhysBones Stiffness | 0.50–0.60 | 0.10–0.20 | 0.15–0.25 | 0.03–0.10 |
| PhysBones Gravity | 0.10–0.20 | 0.55–0.75 | 0.35–0.55 | 0.70–1.00 |
| PhysBones Gravity Falloff | 0.6–0.8 | 0.2–0.3 | 0.35–0.45 | 0.1–0.2 |
| PhysBones Immobile (All Motion) | 0.0–0.1 | 0.1–0.2 | 0.1–0.2 | 0.20–0.35 (stops locomotion whipping the mass) |
| PhysBones Max Stretch / Stretch Motion | 0 / 0 | 1.05 / 0.2 | 1.05 / 0.3 | 1.10 / 0.4 (volume read via Rule 10 squash) |
| — *Unity Dynamic Bone (legacy)* — Damping (rec. 0.01–0.3 [S]) | 0.25–0.30 | 0.12–0.18 | 0.10–0.16 | 0.05–0.10 |
| Dynamic Bone Elasticity (rec. 0.1–0.3 [S]) | 0.25–0.30 | 0.13–0.18 | 0.16–0.20 | 0.07–0.10 (below range — deliberate, see note) |
| Dynamic Bone Stiffness (rec. 0–0.1 [S]) | 0.07–0.10 | 0.02–0.04 | 0.03–0.05 | 0.00–0.02 |
| Dynamic Bone Gravity Y (rec. −0.05…−0.1 [S]) | −0.02 | −0.08…−0.10 | −0.05…−0.07 | −0.10 |
| **Softness-field paint value** (0 = bone-firm, 1 = loosest; extends the AF softness field) | 0.35–0.45 (tip 0.55) | 0.70–0.80 | 0.65–0.75 (core 0.45) | 0.85–0.95 |

**Reasoning, per class (the short version the table compresses):**

- **Teat-scale** sits *above* walk cadence (f_n 2.5–3.0 Hz vs steps ≤ 2 Hz), so
  it follows the host with ~1 frame of lag and a quick 0.3 s settle [M]. Its
  numbers bracket the one shipped jiggle preset found in the wild (3 Hz,
  damping 0.25, 25° cap [S]) — deliberately: that preset is chest/teat-scale
  and it works. Gravity stays low because the part is mostly *carried*; high
  gravity on a small part reads as melting.
- **Sac-scale** is a pendulum first (L-driven sway ~1 Hz) with a bounce near
  the heavy cadence, so it resonates gently (×1.76 [M]) and lags ~6 frames.
  Gravity is near-full: a sac's rest state *is* its hang, and gravity falloff
  stays low so the hang survives posing. ζ 0.16–0.20 keeps the overshoot at
  the fleshy ~56% without a second full cycle.
- **Belly-scale** is tuned *onto* the heavy-walk resonance (f_n ≈ 1.35 Hz at
  1.35 steps/s, gain ×3.33, 90° lag [M]) — the apron is driven by the whole
  pelvis, anchored wide, so its angle cap is lower than the sac's despite the
  larger mass (the motion is translation/squash more than swing; Rules 10–11).
  Its stiffness sits above the sac's in every runtime because the anchor is
  fascia across the abdomen, not a stalk.
- **Full-hyper** drops f_n to 0.6–0.8 Hz — below any cadence — accepting the
  ×0.14–0.36 per-step gain [M] and designing for the sub-harmonic surge
  (Rule 16) instead of fighting it. Damping is the lowest of the four
  (ζ ~0.11, 71% overshoot) but immobile/inertia terms are the *highest*:
  the mass must not be whipped by locomotion translation, only by its own
  accumulated momentum. Gravity is full and contact is the real limiter
  (Rule 13). Dynamic Bone elasticity goes below the recommended range
  deliberately — inside the range, a >40 kg part snaps back like a 2 kg one;
  the range was written for hair and skirts.

**Cross-class rules for the spec:**

1. **Per-joint gradient:** stiffness ×0.5 per joint root→tip [S]; damping
   ×0.85 per joint; gravity constant per chain. Root joint takes the class
   value from the table.
2. **Mass changes re-derive the row.** A part that grows across a class
   boundary (growth sequences, hyper slider travel) interpolates *all* table
   values by its current hang/mass — never keeps its small-size tuning
   (Rule 21). The interpolation variable is log(mass), because f_n moves
   with √(1/m).
3. **Resonance guard for export:** if a tuned f_n lands within ±10% of the
   target platform's dominant drive (walk cadence for locomotion previews,
   ~2.5 Hz step resonance noted in shipped configs [S]) and the class is *not*
   belly-scale, shift stiffness ±15% to step off the peak — unintended
   resonance reads as a bug; intended resonance (belly) reads as weight.
4. **QA gates (from §2/§4):** bake or simulate each class once against the
   heavy walk; pass = lag within Rule 6's budget ±1 frame, first overshoot
   within ±10 pts of Rule 8, no more than 2 visible post-stop cycles, zero
   interpenetration at the Rule 13 caps.

---

## 9. Sources

- Roster & artist corpus: `~/workspace/character_assets/bara-hyper-artists/MANIFEST.md`
  (Wolke, Sombreve, Monty/washbearmonty, BruBearBrown, Nicoreda) — Nov 12, 2026.
- 80.lv, "3D Artist Shares a Tutorial on Creating Natural-Looking Muscle Jiggle"
  (Loay Shaban ragdoll-dynamics tutorial), Jul 2026.
- YasuhikoArts, "Video test: Jiggle walk," DeviantArt, Aug 16, 2025 (artist's
  own side-swing critique).
- Jeff-3659, "Oxyna Temptation [Animation]," DeviantArt, Dec 15, 2023
  (560×560 GIF, 3.53 MB — metadata only, file not downloaded).
- Nighdruth Animations, "Alien Growth Animation Commission, WIP Images,"
  Patreon via Pawchive, Oct 27, 2026 (growth staging structure).
- FattyDragonite inflation loop & ChonkyArtBun waddle loop — via Instagram
  post summaries, Feb/May 2025 (staging/gait descriptions).
- VRChat Creator Docs, "PhysBones"; VRChat Wiki, "PhysBones" (v1.1 semantics:
  gravity as rest-direction ratio, stiffness as orientation retention);
  VRC School, "Phys Bones" (Pull/Spring/Momentum/Stiffness behaviour);
  Threedium fursona guide (tail starting values: Pull 0.2–0.35, Spring 0.4–0.7,
  Stiffness 0.1–0.25, Gravity 0.05–0.15, falloff ~0.5).
- VRM SpringBone: VRM spec docs (stiffness 0–4, gravityPower 0–2, dragForce
  0–1); bevy_vrm / VRM4U implementation notes (Verlet step: inertia ×(1−drag)
  + stiffness + gravity; VRM 1.0 joint defaults stiffness 0.5 / drag 0.5 /
  gravityPower 1 in one reference impl.); Gmod VRM import notes (VRoid hair
  trails 45–63° at 2 m/s with stiffness 0.4–0.8 / drag 0.4 — locomotion-drag
  warning behind the Immobile row).
- Dynamic Bone recommended ranges: Melody's Escape 2 mod guide (Steam
  Community) — Damping 0.01–0.3, Elasticity 0.1–0.3, Stiffness 0–0.1,
  Gravity Y −0.05…−0.1; COM3D2 modding wiki (parameter ranges).
- TavernGuests v0.5.0 jiggle config (Nexus Mods): Frequency 3 Hz, Damping
  0.25 (0.1 long bounce / 1 no overshoot), MaxAngle 25°, sub-2.5 Hz step
  resonance warning.
- Cobalt/Engage spring-bone wiki: stiffness halving per joint down a chain.
- Blender Dynamic Skinning (Rohmer et al., IEEE TVCG 2026) & EXea Jiggle:
  frequency/damping/amplitude as the artist-facing jiggle triplet; per-layer
  stiffness/damping/gravity.
- Gait: Spyropoulos et al. 1991 (stride 1.25 vs 1.67 m, width 0.16 vs 0.08 m);
  Browning & Kram 2006 (width +30%, peak vertical GRF ~+60%); gait-difference
  meta-analysis, 2024 (speed/cadence/step length ↓; width/stance/double support ↑).
- Timing craft: Lasseter 1987 (Lasseter's principles paper); Goldberg,
  *Character Animation Crash Course* (heavier = slower; heavy-fast keeps bulk
  low, recoils short, contacts hard); Animperia walk-cycle guide (12 f/step
  normal, 20+ f/step heavy at 24 fps); Cursa walk-weight notes (deepen down,
  +1–3 f settle, slow recovery); Bouncing Ball Academy, "Leading and
  Following" (overlap lives in the breakdown; chain arrival order).
- Own simulation: second-order driven-spring model, 240 Hz, this run —
  script was scratch (deleted); all outputs are tabulated in §2 so the
  numbers stand without it.

*End of CRAFT.md — §8 is the deliverable the dynamics spec consumes; §§3–7 are
its evidence.*
