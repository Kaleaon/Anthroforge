# Coordination note — from the duplicate sibling agent on this same task

Two agents were spawned for this identical build (earlier spawn b672ba4a +
later spawn d2dab903). This note is from the earlier one, which did canon
verification, independent QA, and one corrective fix. Direct agent messaging
is DB-timing-out, so this file is the handoff.

## 1. Girth key bug — FOUND + FIXED (23:13)

The saved `kaleaon_anatomy_parts.blend` had **both `GirthPlus` and
`GirthMinus` stored at value 1.0** on all four shafts (Blender's
`shape_key_add` leaves new key values at 1.0), so the evaluated rest state
was not the canon basis: shaft volumes at file-open measured
5.941 / 6.927 L instead of 5.301 / 6.182 L.

`scripts/fix_girth_rest.py` zeroed all girth keys and re-saved. Evaluated
rest volumes are now exactly **5.301 / 6.182 / 5.301 / 6.182 L**.
⚠️ Re-running `build_parts.py` reintroduces this — zero key values before
saving, or re-run the fix afterwards.

## 2. Intersection QA — use the strict numbers for the report

`qa_parts.py`'s tri_tri counts grazing/coplanar contact as intersection
(every BVH candidate pair "hit": 240/240, 271/271, …) and it ran while the
girth keys were at 1.0. The strict Möller–Trumbore run at TRUE rest is in
`work/verify_numbers.json` (script `scripts/verify_parts.py`):

- shaft × shaft: only Shaft_1 × Shaft_3 = **28 tris** (the mirrored centre
  pair genuinely overlaps — the canon cluster is four bundled lofts;
  inherited host geometry, not a build defect)
- shaft × sac: 247–314 tris per shaft (root embed + cloth-sim settled
  contact — inherited from the sacdrape host)
- teat × sac: 38–66 tris per teat (root embed, by design; roots are sunk
  22 mm into the sac)
- teat × shaft: **0** · teat × teat: **0**
- Parts vs Body (the clean gate, from qa_numbers.json KDTree): shafts
  ≥ 0.98 mm, sac 1.9 mm minimum vertex distance — **no body penetration**,
  matching the sacdrape REPORT.

## 3. Channel + articulation numbers (verify_numbers.json)

- Length (bone-scale): Shaft_2 Base+Tip Y × 1.25 → tip travel 0.261 m,
  volume 6.182 → 9.738 L. Channel works.
- Girth channels measured clean on the FIXED file
  (`work/girth_channels.json`, script `scripts/girth_plus_check.py`):
  rest 5.301 / 6.182 L · GirthPlus 8.601 / 10.024 L · GirthMinus
  3.268 / 3.813 L (outer pair / inner pair). Fix verified persistent.
- Static articulation pose (shafts fanned ±3–7° + pitch, Sac +12° swing,
  teats −8° lag): all part volumes stable (sac 209.83 L evaluated),
  teat tips stay ≥ 0.023 m above ground, teat × shaft still 0,
  shaft × sac 253–348 tris (same inherited embed/contact class).
- Teat tip ground clearance at rest (qa_numbers.json): 0.0555 / 0.0468 /
  0.0443 / 0.0388 m — all above the sac bottom 0.031 m. ✔ canon "never
  touching" holds for the whole assembly.
- Bone count in parts blend: 93 (89 host + 4 Teat_N, parented to Sac).

## 4. Cost records (PARTS_STANDARD formula: ceil(verts/1000) + bones + 2×morphs)

- Each shaft part: 626 verts → 1 + 2 bones + 2 morphs × 2 = **7 pts**
  (standard anatomy cap 12 ✔). Quad set total 28 pts.
- SacUdder: 1730 verts → 2 + 1 bone + 0 morphs = **3 pts**.
- Each teat sub-part: 109 verts → 1 + 1 bone = **2 pts** (×4 = 8).
- Anatomy set total: **39 of the 128-pt character pool**.
- Socket for all: `pelvis.genital`, Class A, plan-locked to the Kaleaon
  biped host (anchor `CC_Base_Pelvis`; host bone names preserved).

The earlier agent is standing back from the .blend / GLB / renders / MD to
avoid write races and is reporting the duplicate-spawn situation plus this
QA picture to the parent.
