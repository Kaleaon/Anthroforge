# AnthroForge Model Critique — The Review Rubric

**Status:** canonical template, Nov 12, 2026 (B20, model-craft wave).
**Applies to:** every model AnthroForge imports, builds, or exports — library
assets, learned bases, parts, and our own exports. A model that has not been
through this review is *unevaluated*, whatever the QA gauntlet says: the
gauntlet checks that a file is well-formed; this review checks that a model
is **good**.

Worked examples: [`REVIEWS.md`](REVIEWS.md) (border collie / pyn fennec /
bunny, scored with this rubric). Tooling: [`tools/`](tools/)
(`b20_inspect.py` — numeric evidence; `reframe_panel.py` — annotation
panels). Machine gate: `anthroforge-v2/qa-gauntlet/validate_glb.py`.

---

## 1. Where this method comes from

Professional character review is *outside-in and fail-fast*, in a fixed
order, because each stage is cheaper to fix than everything after it:

- **Silhouette first.** Studio practice opens with a 5-second blacked-out
  read (solid dark material, standard ortho views, no zoom): if the story
  isn't clear in silhouette, no texturing or detailing will fix it — the
  flaw is structural and everything downstream is wasted polish.
- **Proportion before anatomy.** Blockout discipline judges the model in
  head-units and joint landmarks (wrist at pelvis, pelvis at ~half height)
  before any surface form is discussed; proportion errors are the most
  expensive to discover late.
- **Staged gates.** Production checklists run progressive reviews
  (30% integrity → 60% topology/UV → 90% performance/export): catch each
  class of defect at the gate where it is still cheap.
- **Topology is judged by what it must do.** Edge flow matters where the
  mesh bends — loops around eyes, mouth, shoulders, elbows, knees; poles
  kept out of deformation zones; density where curvature and detail live,
  not spread uniformly.
- **UVs are judged on evidence, not presence.** Checker-style evidence:
  texel density consistent across shells, no collapsed/stretched islands,
  texture space actually used.
- **Deformation is judged on data, not promises.** A rig that exists on
  paper (a skin block) but carries no weights is worse than no rig,
  because every downstream tool trusts it.

The rubric below keeps that order and those evidence standards, with
AnthroForge-specific checks (species read, ear/tail chains, slider and
fur readiness) folded into the categories they belong to.

## 2. Gate 0 — machine checks (pass/fail, before any human scoring)

Run the QA gauntlet. Any of these ends the review until fixed:

| Gate-0 failure | Why it stops the line |
|---|---|
| Parse failure / NaN vertices | File is corrupt; nothing else is meaningful. |
| Skin declared but **zero weighted primitives** | The file *claims* a rig it does not have (the bunny failure mode). Verdict is capped at *Static/reference only* and the skin must be stripped or repaired before any other use. |
| Skin without inverse bind matrices | Cannot pose, full stop. |
| External texture URIs on an export candidate | Breaks the self-contained-file rule. |

Record the gauntlet line (verts/tris, joints, morphs, textures, scale flag)
at the top of every review. Then score.

## 3. The six categories — in order, never reordered

Score each **0–5** against the anchors. Every score needs *evidence*:
a panel, a measurement, or an inspector number. "Looks fine" is not
evidence. Review in the anatomical frame — if the file stores the
character lying or rotated, re-frame it (tool provided) and note the
stored orientation under Silhouette; don't score a model for your
viewer's default camera.

### 3.1 Silhouette — *does it read in 5 seconds, blacked out?*
Evidence: front + side silhouette panel.
Judge: species/character identity readable at a glance; appendages
separate (arms don't merge into torso, ears read as ears, tail reads);
no stray shells or props polluting the outline; pose is a neutral
A/T-pose, not a random action frame.
AnthroForge checks: ear silhouette carries species (fennec vs wolf is an
ear read); digitigrade leg break visible in profile; tail present and
proportioned.
Anchors: **5** instant, unambiguous read, clean outline · **4** instant
read, minor outline noise · **3** reads, but a feature merges/flattens in
one view · **2** generic — could be several species/characters · **1**
ambiguous mass · **0** unreadable or wrong (reads as another thing).

### 3.2 Proportion — *are the ratios right for what it claims to be?*
Evidence: skeleton landmark ratios (from the inspector) + head-unit
estimates from the panel. Judge against **intent**: a chibi is scored on
chibi coherence, a realistic base on anatomical ratios — but *internal
consistency* is always scored, and a stated scale that is wrong in the
file (cm/mm exports, a character instanced at two sizes) is always a
defect, because "the model's size" must be a fact, not a guess.
Checks: pelvis ≈ 50–60% of standing height; wrist lands near pelvis
height; head (+ears, for anthro) fraction stated and plausible for the
style; shoulder:hip relationship matches the build's Muscle×Tissue
intent; total height in metres is sane and single-valued.
Anchors: **5** all landmarks land, scale exact · **4** landmarks land,
minor scale/presentation untidiness · **3** coherent intent, one ratio
off or scale needs a documented fix · **2** mixed signals (reads between
two intents) · **1** landmark errors a viewer can see · **0** broken
(puppet proportions on a realistic claim, etc.).

### 3.3 Anatomy — *is the surface built like a body?*
Evidence: shaded front + side panel (Lambert is enough; beauty renders
are not required).
Judge: primary forms (muscle groups, chest/back/pelvis volumes) present
and placed over the skeleton they imply; secondary form where the style
promises it; face structure beyond a muzzle blob (brow, stop, jaw) for
head-bearing models; hands/feet structured, not mittens, unless the
style is explicitly mitten. Follows the house construction rule:
skull → muscle → tissue must be *inferable* from the surface.
Anchors: **5** primary + secondary form, landmarks all findable ·
**4** primary form solid, secondary thin in places · **3** primary
volumes read but generic/smooth — anatomy implied, not built · **2**
blobby: forms suggested by texture or not at all · **1** mannequin
tubes · **0** no anatomical structure.

### 3.4 Topology — *will the wiring survive subdivision and bending?*
Evidence: inspector topology block. **Honesty rule:** a GLB is already
triangulated, so source quad flow is *not directly recoverable* — score
the proxies and say so: non-manifold edges (must be 0), bad-winding
edges (must be 0), boundary-edge structure (open shells are normal for
multi-part characters; a *single* shell with thousands of boundary edges
has openings/seam splits to explain), valence distribution (poles =
valence ≥7 share; valence-3 share; mean), and density-vs-detail
(density spent where curvature/detail is, not uniform over blobs).
Anchors: **5** manifold, even flow proxies, density matched to detail ·
**4** manifold, mild irregularity · **3** manifold but pole-heavy
patches, shell sprawl, or density/detail mismatch · **2** non-manifold
or winding defects in non-critical areas · **1** defects in deformation
zones · **0** broken mesh.

### 3.5 UV & Textures — *is the surface paintable, and proven?*
Evidence: inspector UV block + texture inventory.
Judge: every character shell UV'd; texel density (median UV-area per m²)
consistent across shells — a >10× spread means one texture resolution
cannot serve the model; collapsed UVs (zero-area triangle share) ≈ 0;
texture space used, not a corner of it; textures embedded and present —
**an untextured model with UVs is *unproven*, not good**: cap at 3
unless the model's role is explicitly untextured.
Anchors: **5** consistent density, full coverage, textures shipped and
embedded · **4** minor density variance or a small un-UV'd accessory ·
**3** usable layout, unproven (no textures) or moderate variance ·
**2** big density spread (>50×), collapsed patches, or wasted space ·
**1** UVs unusable (overlap soup) · **0** no UVs on a model that needs
paint.

### 3.6 Deformation — *does it actually move, and say so honestly?*
Evidence: inspector weight block + joint inventory + morph/animation
data. This is the category where AnthroForge lives: sliders, retargets,
and poses all spend this budget.
Judge: weights present on every skinned shell, sums = 1.0, ≤4
influences, zero unweighted verts; joint set covers the character
(spine chain, jaw, ear chains, tail chain, fingers where the style has
them) with clean, correctly-spelled, consistently-numbered names —
names are an API; mojibake and typos are defects; morph targets present
where the creator needs them (and stored as *deltas* — targets whose
accessor bounds are identical across targets and ~100× mesh scale are
absolute positions in source units and will explode a naive consumer);
at least a test animation or documented retarget proof is a plus.
Contract note: foreign joint names are **not** a quality defect — they
are a *mapping cost*, recorded in the fix list, never scored here.
Anchors: **5** clean weights, full joint coverage, morphs + proven
motion · **4** clean weights and coverage, one gap (no morphs, or morph
framing needs normalization) · **3** weights work but coverage or names
need repair · **2** partial weighting (some shells unweighted) ·
**1** weights exist but broken (bad sums, unweighted regions) ·
**0** **no deformation data — including a vestigial skin that pretends
otherwise.**

## 4. Scoring rules

- Total = sum of six categories, /30.
- **Verdict bands:** 26–30 *Reference standard* · 21–25 *Adopt with
  fixes* · 16–20 *Usable — work order required* · 11–15
  *Static/reference only* · ≤10 *Reject*.
- **Caps (override the band):** Deformation 0 → verdict capped at
  *Static/reference only*. Silhouette ≤1 → *Reject* eligible regardless
  of total. Gate-0 skin failure → the cap applies *and* the fix list's
  first item is the strip/repair.
- **No averaging away a zero.** The verdict line must name the weakest
  category explicitly ("weakest: Deformation 0").
- Re-review after fixes re-scores only the affected categories, but the
  full panel set is regenerated — fixes love to break silhouettes.

## 5. Fix-list format

Every review ends with a fix list. Each item:

`[severity] Category — defect (evidence) → fix. Effort: S/M/L`

- **blocker** — gates a use the model is wanted for.
- **major** — costs real time or quality downstream.
- **minor** — hygiene; fix when the file is open anyway.
- Effort: **S** < 1 h · **M** an evening · **L** a project.
- A fix names the *action* ("strip the vestigial skin block"), not the
  feeling ("improve the rig").

## 6. Process

1. **Triage (15 min):** Gate 0 + silhouette panel + scores for
   Silhouette/Proportion only. Enough to shelve or shortlist.
2. **Full review (~1 h):** inspector run, all six categories, fix list.
   Required before a model becomes a base, a part donor, or a preset
   reference.
3. **Re-review:** after the fix list is worked; deltas recorded at the
   foot of the original review (never edit history — append).

## 7. Blank review template

```markdown
# Review — <file> (<author/source>)
Date · Reviewer · Gate-0 line: <verts/tris · joints · morphs · textures · scale flag>
Panel: renders/<name>_panel.png · Inspector: <key numbers inline>

| Category | Score | Evidence (one line) |
|---|---|---|
| Silhouette | /5 | |
| Proportion | /5 | |
| Anatomy | /5 | |
| Topology | /5 | |
| UV & Textures | /5 | |
| Deformation | /5 | |
| **Total** | **/30** | **Verdict:** — weakest: |

## Notes per category
...

## Fix list
- [blocker|major|minor] Category — defect (evidence) → fix. Effort: S/M/L

## Re-review log
- <date> — categories re-scored: … new total/verdict: …
```

---

*Method sources (professional practice, Nov 12, 2026 study pass):
silhouette-first evaluation and the 5-second blacked-out read;
blockout/proportion-gate workflow (head-units, joint landmarks);
staged 30/60/90 production review cadence; topology judged at
deformation zones with poles kept out of them; UV quality judged on
texel-density consistency and collapsed-island evidence; deformation
judged on weight data, never on the presence of a skin block alone.*
