# Animation Retarget Prototype — one clip set, every proportion

**Question:** AnthroForge characters range from a ~1.1 m fennec to a ~2.7 m bara orc.
Can one authored animation set (Idle / Walk / Wave / Dance) serve all of them?

**Verdict:** Yes — with rotation-delta retargeting plus one cheap compensation:
scale the hips (root) translation by the target/source leg-length ratio.
Compensation improved *every* foot-drift metric on both test targets and brought
stride-normalised drift to **or below the source clip's own baseline**. What it does
not fix is rest-pose/chain-geometry differences on a foreign rig (the fennec's Wave
hand path deviates ~31 % of arm length) — that is a mapping/rest-pose problem, not a
scaling problem, and it is worst exactly where bone *names and topology* differ, not
where proportions differ (the proportion-only orc test: 2.9 % hand error).

Raw numbers: `metrics.json` (this folder). Reproduce: `work/retarget.py` (build +
bake), `work/metrics2.py` (measurement), Blender 5.2.3 headless.

---

## Rigs used

| Rig | Role | Bones | Hip height | Notes |
|---|---|---|---|---|
| Bara wolf (Mixamo, 65 bones) | **Source** — owns the authored Idle/Walk/Wave/Dance | 65 | 1.03 m | Clips from the furry lineup GLB; Walk is in-place, hips carry bob/sway only |
| Pyn fennec (Codaj, 107 bones) | **Target A** — foreign rig, foreign names, digitigrade | 107 | 0.56 m | Leg ratio vs wolf **0.544**; completely different bone naming/topology |
| "Orc-sim" wolf clone | **Target B** — same rig, rescaled proportions | 65 | 1.25 m | Edit-bone rescale of the wolf: legs ×1.20, spine ×1.25, arms ×1.40 → measured hip ratio **1.215**, arm ratio **1.416**, height 2.20 → **2.71 m (×1.234)** |

22 bone pairs were mapped wolf→fennec (hips, spine chain, neck/head, shoulders,
arms, forearms, hands, thighs, shins, feet, toes). Unmapped fennec bones — fingers,
ears, tail (11 bones), toe fingers, the secondary "hombro" chest bones — hold their
rest pose during clips (see Limitations). Orc-sim uses the identity map.

## Method

**Rotation-delta transfer, in armature space.** For each frame and mapped bone:
`Q_target(f) = (Q_src(f) · Q_src_rest⁻¹) · Q_target_rest` — the source bone's
rotation *away from its own rest pose*, re-applied on top of the target's rest pose.
Positions are **not** copied: each target bone's head position falls out of the
target's own chain (parent's posed matrix × rest offset), so target limb lengths are
respected exactly. The one exception is the hips/root translation, which is where
the two variants differ:

- **C0 — no compensation:** hips translation delta copied 1 : 1 in metres.
- **C1 — scale compensation:** hips translation delta × leg-length ratio
  (fennec 0.544, orc-sim 1.215). Nothing else changes.

Baking decomposes each desired pose matrix into pose channels via
`B = R_b⁻¹ · R_p · P_p⁻¹ · P_b`. Two traps were hit and are worth recording:

1. Setting `pose_bone.matrix` and keyframing immediately bakes garbage (probe:
   1.9 m / 261° error) — the channels don't sync without an evaluation pass. The
   explicit basis decomposition reproduces desired matrices **exactly**
   (validation on all four Walk bakes: 0.00 mm / 0.000° max deviation).
2. The fennec GLB hangs its armature under a chain of empties (Sketchfab/FBX
   hierarchy), so its world frame is rotated vs the wolf's. All measurement below
   is done in a **per-rig character frame** (right / forward / up derived from the
   rest pose) — comparing raw world coordinates across rigs is meaningless.

**Measurement.** Walk is an in-place cycle, so foot sliding is measured against a
fitted treadmill: contact frames = toe in its lowest height band; treadmill speed =
least-squares ground speed over both feet's contact segments; **drift** = the
ground-relative path the ankle still travels while it should be planted. Because an
FK-authored in-place cycle swings the stance foot on a pendulum arc, the *source
clip itself* has substantial baseline drift — every figure below is comparative,
same method for all versions. Wave error = RMS distance between target and source
hand-tip trajectories, each taken relative to its own shoulder and normalised by
its own arm-chain length.

## Walk — foot drift (contact frames of the cycle)

| Version | Treadmill m/s | Drift path cm/step | Drift net cm/step | Contact RMS cm | Drift ÷ stride | Stride m | Min toe vs floor cm | Mean contact toe cm |
|---|---|---|---|---|---|---|---|---|
| Wolf (source) | 1.37 | 33.9 | 29.0 | 11.1 | 0.398 | 0.851 | −7.4 | −2.1 |
| Fennec C0 | 0.39* | 20.8 | 20.7 | 7.5 | 0.432 | 0.481 | −1.5 | +0.3 |
| **Fennec C1** | 0.53* | **17.0** | **16.9** | **6.3** | **0.353** | 0.481 | **−0.4** | +1.0 |
| Orc-sim C0 | 2.20 | 30.6 | 24.1 | 10.3 | 0.305 | 1.003 | −4.1 | +1.5 |
| **Orc-sim C1** | 2.50 | **23.0** | **12.2** | **6.7** | **0.229** | 1.003 | −4.7 | +0.9 |

\* The least-squares treadmill fit is soft on the fennec (stride ÷ cycle time gives
0.55 m/s; C1's fit lands close, C0's is skewed by its deeper floor penetration
changing the contact windows). Stride lengths are identical C0 vs C1 on both
targets — compensation moves the root, not the pose.

Reading:

- **Compensation helps everywhere it can.** Fennec net drift −18 %, contact RMS
  −16 %, floor penetration −1.5 → −0.4 cm. Orc-sim net drift −50 %, contact RMS
  −35 %. Stride-normalised drift ends *below* the source's own 0.398 on both
  compensated targets — the retarget is not the weak link; the authored cycle is.
- **Uncompensated is worst exactly where you'd predict:** a 1:1-metre hips bob on a
  half-size character (fennec C0 has the worst normalised drift, 0.432, and the
  deepest penetration). On the orc the C0 penalty shows up as gross net slide
  (24 cm/step) because the root under-travels the longer stride.
- The source clip's own −7.4 cm toe dip (foot-roll in the hand-authored cycle) sets
  the floor for penetration figures; orc C1's −4.7 cm is inside that noise.

## Wave — hand-target error

| Version | Hand RMS error (% of arm length) | …in cm at target scale | Peak hand above head (× arm length) |
|---|---|---|---|
| Source reference | — | — | 0.21 |
| Fennec C1 (= C0) | 31.1 % | 11.2 cm | 0.26 |
| Orc-sim C1 | 2.9 % | 3.3 cm | 0.24 |

- C0 and C1 are **identical** on Wave — the clip contains zero hips translation, so
  there is nothing for scale compensation to scale. Compensation is a root-motion
  tool; it neither helps nor harms upper-body clips.
- The orc's 2.9 % shows pure proportion change is nearly free for rotation-delta
  transfer. The fennec's 31 % is the price of a *foreign rig*: different rest arm
  direction, an extra clavicle segment, and a spine whose chest bone hangs off a
  different parent. The gesture still reads — peak hand height above the head is
  preserved (0.26 vs source 0.21) — but the path is the fennec's own, not a copy.
  Delta retargeting transfers *motion*, not absolute pose; if a future clip needs
  an exact end-effector path (holding a prop, touching a point), it will need an
  IK/contact pass on top, per rig.

## Limitations

- **Digitigrade feet are approximated.** The fennec's long "shin" is partly a foot
  lever; mapping wolf Foot→Foot1 / Toe→Foot2 keeps ground contact honest (see
  penetration numbers) but toe-off timing shifts — one reason the fennec's right-foot
  contact fragmented into 3 segments under C1 in the detector.
- **No contact-lock / IK cleanup pass.** The remaining drift is the authored
  cycle's arc, visible even in the source. A stance-phase IK pin would cut drift
  across the board and is the obvious next quality step; it is also per-character
  post-processing, not part of the clip.
- **Unmapped bones are static.** Ears, tail, fingers hold rest pose on the fennec.
  In production these want procedural secondary motion (lag/spring on the source's
  motion), not baked keys.
- Dance (384 f) was retargeted to the fennec (C1) and ships in the deliverables,
  but was not put through the drift metrics — it has no ground-contact contract to
  measure against. Timings assume 30 fps throughout.

## Recommended pose-library format for the app

Borrow Eldritch Foundry's split (ELDRITCH_FOUNDRY.md §5) — **stance presets own the
legs, per-part offsets own everything expressive** — and store clips so retargeting
is a load-time operation, not an authoring one:

1. **Clip = rotation deltas + root track, against a named rest pose.** Store each
   clip as per-bone rotation deltas from the *canonical rig's* rest pose plus the
   hips translation track, tagged with the canonical rig id. Never store baked
   per-character copies; retarget on load/equip.
2. **Proportions profile per character.** Each character carries `leg_ratio`,
   `arm_ratio`, hip height and stride length (all derivable from its rig at import).
   Load-time retarget applies rotation deltas directly and scales the root track by
   `leg_ratio` — the C1 rule, which is one multiply and bought −18…−50 % net drift
   here.
3. **Stance layer (legs) vs expression layer (arms/head/ears/tail).** Following EF:
   locomotion/idle *stances* are whole-leg presets that own legs + root track and
   are the only layer allowed to move the root; upper-body clips (wave, gestures,
   ear/tail life) are additive offsets that never touch the root. This makes the
   compensation rule structural: root scaling lives in exactly one layer.
4. **Contact metadata in the clip.** Stance clips ship their contact windows and
   stride length (measured once, at authoring). The app derives treadmill/playback
   speed from stride ÷ cycle time per character instead of trusting the clip —
   and a future IK contact-lock pass has the data it needs.
5. **Secondary bones are procedural.** Ears/tail/fingers are excluded from clips
   and driven by spring-lag parameters in the character's proportions profile —
   one clip set stays valid for a 107-bone rig and a 65-bone rig alike.

## Deliverables

- `retarget_prototype.blend` — wolf (original clips on NLA), fennec (Idle/Walk/
  Wave/Dance C1 + Walk/Wave C0 on NLA), orc-sim (Idle/Walk/Wave C1 + Walk C0 baked).
  *Mute NLA tracks before evaluating a single assigned action.*
- `fennec_retargeted.glb` — the fennec with all six retargeted actions; verified
  by re-import (107 bones, actions intact, Walk animates the toe chain).
- `metrics.json` — every number above, plus per-foot contact counts and the
  stride-normalised table.
- `work/` — build/bake script, measurement script, inspection/probe scripts, logs.
