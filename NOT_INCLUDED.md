# NOT_INCLUDED — redistribution audit (Nov 16, 2026)

AnthroForge's standing rule: **we learn, measure and derive our own work; we
never redistribute other people's.** Study models are pulled into the local
library, measured, and deleted from the pipeline — the *data* ships, the
*models* don't.

Before this repository was published, both trees were audited file by file.
The items below exist in the local working tree but were **deliberately
excluded** from this repo. Paths are relative to the repo root. Everything
not listed here — all documents, code, slider/coupling records, presets,
derived measurement data (learned field packs, `.target`/`.npz` instance
data), and every GLB/blend we built — **is** included.

## Third-party models and direct derivatives

| Excluded path | What it is | Why excluded |
|---|---|---|
| `anthroforge-v2/autoskin-prototype/orc_bust_skinned.glb` | Our skinning applied to "Orc Head Bust *Free*" by Demonic Arts / Jesterz86 (Sketchfab, CC-BY) | The geometry is the third-party sculpt; only the weights are ours (the study doc `AUTOSKIN.md` ships, with credit) |
| `anthroforge-v2/autoskin-prototype/work/bust/` | Downloaded source of the same bust (scene + textures) | Third-party original |
| `anthroforge-v2/model-craft/b2-retopo/orc_head_before.glb` | "orc head" sculpt by demidevil13 (Sketchfab, CC-BY), 855,696 tris | Third-party original |
| `anthroforge-v2/model-craft/b2-retopo/orc_head_retopo.blend`, `orc_head_retopo.glb` | Our retopology of the demidevil13 sculpt | Direct derivative; the .blend also embeds the sculpt as its reference — excluded as uncertain rather than argued over |
| `anthroforge-v2/model-craft/b8-baking/work/bake_scene.blend`, `orc_head_baked.glb`, `maps/` | Bake scene, baked GLB and texture maps for the same demidevil13 orc head | Embeds / is baked directly from the third-party sculpt and retopo |
| `anthroforge-v2/retarget-prototype/fennec_retargeted.glb` | Codaj fennec avatar with our retargeted animation clips | Third-party avatar model |
| `anthroforge-v2/retarget-prototype/retarget_prototype.blend` | Retarget working scene | Embeds the Codaj fennec and the bara wolf rigs |
| `anthroforge-v2/model-craft/b6-optimize/lods/bara_wolf_lod*.glb` (5 files) | Decimation LODs of `bara_wolf_avatar.glb` | Source body is Tripo-AI-generated with a Mixamo skeleton — not authored in-house |
| `anthroforge-v2/fur-prototype/fur_prototype.blend`, `fur-prototype/work/fur_stage1–3.blend` | Fur prototype scenes | Embed `BaraWolfBody` (the Tripo/Mixamo wolf above). The derived fur-card GLBs ship — they contain only our cards (verified: single `FurCards_LOD0` mesh) |
| `anthroforge-v2/fur-craft/a1-shells-fins/shells_fins.blend` | Shell/fin fur study scene | Embeds a copied patch of `BaraWolfBody` surface |
| `anthroforge-v2/fur-craft/a3-geonodes/geonodes_fur.blend` | Geometry-Nodes groom scene | Embeds `BaraWolfBody` |
| `anthroforge-v2/fur-craft/a7-paintmaps/fur_paintable_rev1.blend`, `fur_paintable_rev2.blend`, `out/groom_from_paint_rev1.blend`, `out/groom_from_paint_rev2.blend` | Paint-map groom scenes | Embed `BaraWolfBody` |
| `anthroforge-v2/fur-craft/a14-shortfur/shortfur_compare.blend`, `fur-craft/a17-states/fur_states.blend` | Body-scale fur study scenes from the same wolf-subject series | Embedding not verified file-by-file — excluded as uncertain |
| `anthroforge-v2/export-prototype/border_collie_SL.dae`, `border_collie_Unity.fbx`, `border_collie.blend`, `out/_source_border_collie.glb`, `textures_dae/`, `dumps/interchange.npz`, `dumps/anim_samples.npz` | The "AKM Border Collie Scientist" avatar exported from Second Life, its textures, and raw vertex/animation dumps | Third-party avatar and its data in every form. The study doc (`SURVIVAL.md`), our scripts and the JSON metrics ship |
| `anthroforge-v2/model-craft/b15-clothing/clothing_fit.blend` | Clothing-fit study scene | Built on the AKM Border Collie Scientist (Sketchfab) avatar; embeds the third-party body |
| `anthroforge-v2/fur-craft/a9-photofur/sources/` | Downloaded reference photographs (bear, fox, wolf) and crops | Third-party photographs used for study only |
| `anthroforge-v2/base-head-v3/work/head_source.blend` | The imported GalileoGB cougar source file (CC-BY) that base-head v3 was neutralised from | Raw third-party source. The shipped v3+ heads are our layered rebuilds and carry the CC-BY attribution in `base-head-v3/BUILD_NOTES.md` — they are included |

## Superseded build — rebuild in progress

| Excluded path | What it is | Why excluded |
|---|---|---|
| `anthroforge-v2/characters/kaleaon-head/work/stage2.blend`, `stage3.blend`, `stage4.blend`, `stage5.blend` — and `kaleaon_head.glb` / `renders/`, which are likewise withheld | The Phase-2 Kaleaon head build (on base-head v5) | Rejected on sight Nov 16, 2026 — the sculpt was shattered — and is being rebuilt. The spec (`KALEAON_HEAD_SPEC.md`), the build scripts and the measurement data ship; the rejected geometry doesn't |

## Transient junk (not third-party — just not shipped)

`__pycache__/`, `*.pyc`, `*.blend1` (Blender auto-backups), `*.log`,
`.pytest_cache/` were skipped throughout both trees.

## Kept, with attribution (judgment calls, stated openly)

- **Base heads v3–v5** carry parts derived from the GalileoGB cougar
  (CC-BY): tissue surface, ears, sculpted mouth/teeth slab, tongue —
  neutralised into our skull → muscle → tissue construction. CC-BY permits
  redistribution with attribution; the attribution travels in
  `base-head-v3/BUILD_NOTES.md`.
- **`model-craft/b19-scans/lion_head_clean.glb`** — cleaned Poly Haven
  lion-head photogrammetry scan, CC0.
- **`anthroforge-v2/lib/`** — vendored Babylon.js (Apache-2.0) and Tailwind
  browser build (MIT), so the standalone HTML prototype runs offline.
- **Learned slider fields** (app library instance packs, `slider-lab`
  outputs, `.target` files) — per-vertex deformation *data* measured from
  study models by the learn-then-delete pipeline, transferred onto our own
  bases. No third-party product files (no `.osd`, no Skyrim/SL/BOOTH
  downloads) exist anywhere in either tree; the scan for them is part of
  this audit.
- **Study renders and documents** throughout depict study subjects (that's
  what makes them evidence) but contain no extractable model or texture
  data.
