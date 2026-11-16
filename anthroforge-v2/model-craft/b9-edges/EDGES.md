# B9 — Smoothing & Edge Craft

*Model-craft wave, learning agent B9. Subject part: the left ear from our own
neutral base head v4 (`base-head-v4/neutral_base_head_v4.glb`, object
`Ear_L`) — a thin, curved organic shell with a folded rim: the single most
common part shape in the avatar library, and the one that punishes lazy
shading hardest. Demo scene: `edges_demo.blend` (all three finishes kept
live, modifiers unapplied). Renders: `renders/`.*

---

## 1. What a shading normal actually is (the 60-second version)

The geometry normal of a face is a fact. The **shading normal** is an
opinion the renderer is told to believe: at each vertex of each face corner
(a *loop*), the shading normal can point anywhere, and the light gradient
across the face is interpolated from those corner normals. Every smoothing
technique in this document is a way of choosing those corner normals:

- **Flat shading** — corner normals = face normals. Truthful, faceted.
- **Smooth shading** — corner normals at a vertex are averaged across all
  faces sharing it. Continuous gradients, but the average is *unweighted
  and indiscriminate*: a sliver triangle counts as much as a hero face, and
  the average happily leans across a crease you wanted to keep.
- **Custom split normals** — corner normals stored explicitly per loop
  (Blender: `corner_normals`; the legacy name is "custom split normals"
  because corners at one vertex may *split* — point in different
  directions — wherever an edge is marked sharp or an angle threshold is
  exceeded). This is the actual data every other method writes. GLB/glTF
  import gives you split normals whether you asked or not: our ear arrived
  with 1,072 vertices for 536 faces; welding coincident splits
  (`remove_doubles`, 0.1 mm) collapsed it to 285 — the other 787 were the
  same corners stored over and over so the exporter's shading could be
  reproduced exactly. (It carried no sharp-edge *marks* at all — the
  splits lived purely in duplicated vertices, which is why the weld, not
  an edge setting, was the cleanup.)
  **First craft rule: know whether your mesh's normals are authored,
  imported, or accidental. An imported file's shading is its exporter's
  opinion, not the artist's.**

## 2. The three finishes in the demo

All three start from the *identical* welded mesh (285 verts / 536 polys).
Only the normal/edge treatment differs.

### A — Raw auto-smooth ("just turn it on")
Smooth-by-angle, 30° threshold, nothing else touched. Edges whose face
angle is under the threshold share averaged normals; over it, they split.
On this mesh the threshold split **54 of 820 edges** — the rim fold and
the tip crease, mostly; the blade's broad curvature sits under 30°
between neighbours and smooths. (Implementation note: in headless
Blender 5.2 the smooth-by-angle *operator* silently added nothing, so
variant A was authored by the equivalent direct route — smooth faces +
sharp marks written per edge from computed face angles. Same data, same
result; see §7.)

### B — Weighted normals
All faces smooth, plus a Weighted Normal modifier (face-area-with-angle
weighting, keep-sharp on). Corner normals are recomputed as the
**area-weighted** average of surrounding face normals, so the large faces
that carry the form dominate and sliver/rim triangles stop dragging the
gradient. No geometry changes: evaluated mesh is still 285 / 536.

### C — Bevelled + weighted normals (the production finish)
B, plus a small angle-limited bevel (8 mm at this part's scale, 3
segments, hardened normals) *before* the weighted-normal pass. The bevel
adds a real transitional surface at the rim fold, so the highlight has
somewhere honest to live instead of being faked by a normal split.
Evaluated cost: 575 verts / 759 polys — roughly double the vertices on a
285-vert part, i.e. pennies; on a 60 k-vert body the same discipline
applied *only where the angle limit bites* stays similarly cheap because
the bevel modifier only builds geometry at qualifying edges.

Measured loop-normal deviation (angle between each corner's shading
normal and its face normal, over the evaluated mesh — a smear index:
0° = flat truth, high = gradients leaning far from the surfaces):

| Variant | Eval verts/polys | Sharp edges | Deviation mean | Deviation p95 | Loops > 15° |
|---|---|---|---|---|---|
| A auto-smooth 30° | 285 / 536 | 54 | 7.36° | 18.01° | 9.1% |
| B weighted normals | 285 / 536 | 0 | 11.41° | 41.72° | 21.0% |
| C bevel + weighted | 575 / 759 | 0 | 7.89° | 18.64° | 11.4% |

Read the metric correctly: deviation measures how hard the normals are
*steering*, not how good the shading is (flat shading scores a perfect,
useless 0°). Against that reading the table tells a clean story:

- **B steers hardest** — p95 of 41.7° means the corners of the small rim
  faces are being pulled a long way toward the big blade faces' normals.
  On this coarse a mesh that is weighted normals doing exactly their
  job, aggressively: the gradient stays glued to the large forms. The
  cost of that strength on very coarse topology is stretched gradients
  across the small faces themselves (visible as the soft smear at the
  fold in `b_weighted_side.png`) — B's known trade, and the reason C
  exists.
- **C steers no harder than A** (mean 7.9°, p95 18.6°) **while reading
  smoother than both** — because the bevel's transitional faces carry
  the fold, the normals no longer have to lean across it. Geometry did
  the work the normals were faking. This is the demo's headline number.
- A's moderate steering is bought with 54 split edges: the gradient is
  calm *between* splits and interrupted *at* them, which is the
  dashed-crease risk of §3 in statistical form.

## 3. Why auto-smooth alone fails on organic forms

Auto-smooth (smooth-by-angle) is a *global, geometric* rule applied to a
*local, artistic* problem. Four failure modes, all visible on an ear:

1. **The threshold is a cliff, not a judgement.** Two adjacent edges at
   29° and 31° get opposite treatment from a 30° setting. On a sculpted
   organic surface the fold angle varies continuously along its length,
   so one crease can be split at the base, welded at the tip, and
   alternate in between — a dashed line of shading breaks down the exact
   feature you were trying to keep. Artists call the result "candy
   wrapper" shading.
2. **Averaging is unweighted.** Where a big smooth blade meets a strip of
   small rim faces, plain averaging lets the many small faces outvote the
   blade, and the highlight crawls sideways off the surface it belongs
   to. This is the main thing weighted normals fix (§2B).
3. **It cannot create a highlight, only smear one.** A thin shell's rim
   (ear edge, lip line, claw) has almost no surface facing the light at
   grazing angles. No normal trick invents the bright edge line a real
   rim shows; only geometry (a bevel, §2C) or a different material does.
   Auto-smooth on thin parts therefore reads as *paper*: correct normals,
   wrong object.
4. **The terminator problem.** On low-poly smooth-shaded forms the
   light/shadow boundary stair-steps along face edges (the shadow
   terminator follows the averaged normals, the silhouette follows the
   geometry, and they disagree). Denser topology, weighted normals, and
   bevelled key edges all shrink the disagreement; the angle setting
   alone does nothing for it.

None of this makes auto-smooth useless — it makes it a **starting
default, not a finish**. It is the right answer for background props,
hard-surface blockouts, and anything whose creases genuinely are all
above one angle.

## 4. Hard edge / soft edge decision rules

Decide per edge, from what the edge *is*, not from a global number:

| The edge is… | Treatment | Why |
|---|---|---|
| A manufactured/mechanical break (panel line, horn segment ring, armour trim) | **Hard** — sharp mark / split normals, or bevel it | The form genuinely turns there; smoothing lies about the construction |
| A fold in one continuous tissue (ear rim fold, eyelid margin, lip roll, nostril wing) | **Soft, but bevelled if it catches light** | The tissue is continuous, so normals should flow — but the highlight needs a transitional strip |
| A silhouette edge on a thin part (ear blade, fin, membrane) | **Bevel, always** | Silhouettes can't be faked by normals; an unbevelled thin edge reads as cardboard at every angle |
| A broad anatomical transition (cheek → muzzle, neck → jaw, chest → shoulder) | **Soft, weighted normals** | No edge exists in the anatomy; the gradient *is* the anatomy |
| An artefact of topology (valence spike, retopo seam, weld line) | **Soft + weighted normals; fix topology if it still shows** | It isn't a feature; never let it hold a sharp mark |
| Where two parts meet/intersect (horn → skull, tooth → gum, part → socket) | **Hard on the inserted part's base ring** | A clean contact shadow line sells the join; smoothing across an intersection smears |

Two corollaries that save the most rework:

- **Sharp marks are data, not geometry.** Marking an edge sharp costs no
  vertices and survives export in most pipelines (glTF: split vertices).
  Reach for it before reaching for a bevel when the budget is tight —
  but remember it only redirects light, it never adds a silhouette.
- **Bevel width is a proportion decision.** Rule of thumb used in the
  demo: bevel ≈ 3–5% of the part's smallest dimension, 2–3 segments,
  profile left at default (0.5) for organic, lower (→0.2, flatter) for
  machined. A bevel you can *see* as a stripe is too wide; a bevel that
  only shows as a clean highlight line is right.

## 5. Stylised vs realistic discipline

The same tools, opposite defaults:

**Stylised / toony parts** (fursuit bases, chibi and kemono parts, the
stylised end of our style axis)
- Fewer, *bigger* decisions: broad smooth regions, a small number of
  deliberate hard edges that read as graphic shapes (ear tip, muzzle
  break, toe separations).
- Bevels are part of the style: slightly oversized (5–8% of smallest
  dimension), 2 segments, so highlights read as clean graphic bands at
  viewing distance.
- Weighted normals matter *more*, not less: with big flat-ish colour
  regions, any normal smear shows as a visible smudge in the flat
  shading. Keep-sharp off; let the area weighting keep gradients lazy
  and clean.
- Auto-smooth's angle cliff is most dangerous here — a dashed crease on
  a graphic form reads as a mistake, not detail.

**Realistic parts** (scans, CT-derived, the realistic anchor of the
style axis)
- Topology density does most of the work; normals mostly stay out of the
  way. Weighted normals with keep-sharp *on*, so the few true breaks
  (tooth/gum, claw/bed, lid margin) survive.
- Bevels small (1–3% of smallest dimension) and only where anatomy or
  wear rounds an edge — which, on real tissue, is nearly everywhere
  *except* teeth, claws and fresh scars.
- Never mark tissue edges sharp to "add detail". Real detail comes from
  the sculpt and the texture; a sharp normal line on skin reads as a
  rendering bug.

## 6. Decision guide (pin this one)

```
Is the edge a real break in construction or material?
 ├─ yes → will it be seen in silhouette or catch a highlight?
 │         ├─ yes → BEVEL (small, angle-limited, hardened normals)
 │         └─ no  → SHARP MARK / split normals
 └─ no  → is it thin-part rim or a light-catching tissue fold?
           ├─ yes → BEVEL, soft normals over it
           └─ no  → SMOOTH + WEIGHTED NORMALS
                    (and if a gradient still crawls, the topology
                     is wrong — no normal setting fixes that)
```

Default finishing stack for AnthroForge parts, in order:
**weld stray splits → smooth → weighted normals (face-area-with-angle,
keep-sharp on) → angle-limited bevel on rim/silhouette edges →
re-check silhouette at arm's length.** Auto-smooth alone is step 2
stopping early.

## 7. What the demo showed (and its limits)

- From the front, all three shade the blade *acceptably* — the
  differences concentrate at the rim fold and the tip, i.e. in the side
  renders. Look there first (`a_autosmooth_side.png` vs
  `c_bevelled_side.png` is the money comparison).
- In profile, A's rim is a cliff: lit blade, dark fold, no transition —
  the edge reads as a cutout. C's bevel puts a continuous bright line
  down the rim: the ear gains readable *thickness*. B sits between —
  smoother than A on the blade, but its fold transition smears (the
  p95-41.7° steering of §2 made visible).
- C is the only variant whose *silhouette* improves. If a part will be
  seen edge-on (ears always are), that alone justifies the bevel.
- Two pipeline lessons from building this demo, both now standing
  practice for our batch scripts: (1) Blender 5.2's smooth-by-angle
  *operator* is a no-op in headless background mode — check for the
  modifier it should have added, and be ready to author the same data
  directly (variant A does). (2) Edit-mode operators act on **every
  selected object**, and object copies inherit selection — an early
  version of this build marked sharp edges on the source ear and
  silently contaminated every later variant copied from it. The
  giveaway was a deviation metric reading exactly 0.0° (pure flat
  shading) on variants that should have been smooth. Defence: build
  variants by direct attribute writes on one object at a time, and keep
  a metric that can prove a negative.
- Limits: one part, one light rig, clay only, stills not turntable.
  Fur cards, textured skin and SSS will mask some of A's sins and none
  of the silhouette ones. Numbers are this mesh's, not norms — the
  *method* (weld first, measure deviation, compare side-on) is the
  reusable part. Scripts: `work/build_edges.py`,
  `work/measure_deviation.py`; numbers: `stats.json`.

## 8. Sources & provenance

Technique summary from standard practice (Blender 5.2 docs: Weighted
Normal and Bevel modifiers, smooth-by-angle, corner/split normals;
glTF normal handling) applied to our own library geometry — no external
assets used. Ear: AnthroForge base head v4, our own build. Licence
status of the demo: internal study material, like the rest of the wave.
