# AnthroForge — Anatomy and Sona Architecture

Status: architecture and validation groundwork, not a claim that production anatomy meshes are complete.

## Review of the current implementation

The creator currently has two partially disconnected paths:

1. The Babylon prototype builds a visible avatar from procedural lofts, legacy morph state and a 32-bone rig.
2. The Python Core Service stores \` .afchar.json \` records, validates canonical sliders and exports a base mesh with applied slider deltas.

Those paths are not yet one end-to-end character pipeline.

### Findings

- \`Character.from_dict()\` only checks that each part entry has string \`slot\` and \`part\` fields. It does not resolve the part manifest, confirm that its mesh exists, check its rig, or verify fit against the selected body plan.
- The Python \`build_character()\` path currently applies slider instances to a base and writes the base triangles. It does not assemble \`Character.parts\`, fur geometry, material layers or part-specific animation into that GLB.
- \`core/vocabulary.py\` deliberately carries legacy \`sos.*\` values through \`identity\`; it does not convert those values into a canonical anatomy part or rigged asset. A value surviving a save is not proof that its geometry is present in an export.
- The Babylon prototype does have a \`GenBase\`, \`GenScrot\`, and \`Gen01\`–\`Gen04\` chain, plus length/girth/curve controls and procedural pelvis variants. This is a useful prototype, not yet a production part system.
- The prototype creates separate loft meshes for chain segments and calls the generic distance-based skin-weight routine. That routine estimates weights from nearby bones; it does not consume authored, reviewed weight maps from an anatomy asset. Seam continuity and deformation under extreme poses therefore need explicit validation.
- The legacy variants are hard-coded in one function. The current selector groups feline and equine under one label/branch, and the variants are not independently fitted to all four body plans.
- The body-plan spec correctly states that \`pelvis.genital\` exists across biped, taur, feral and naga plans, but its placement follows the job of the pelvis. A biped transform must not be reused as a universal location.

## The target architecture

A sona should be assembled from independent, inspectable layers:

\`\`\`text
Character record
  ├─ identity + species lineage
  ├─ body plan (biped / taur / feral / naga)
  ├─ body and head shape vectors
  ├─ anatomy part manifest
  │    ├─ plan-specific socket + fit region
  │    ├─ LOD meshes + authored skin weights
  │    ├─ morph channels / corrective shapes
  │    ├─ motion chain + collision profile
  │    └─ materials / fur acceptance / provenance
  ├─ coat, markings and palettes
  └─ expressions, pose and animation state
             ↓
      shared assembly + validation service
             ↓
   preview / GLB / FBX / BLEND / Unity / VRChat
\`\`\`

Species should be composable, not a single mutually-exclusive dropdown. A wolf-like sona may combine canid head structure, a selected body plan, an individual tail, custom ear carriage, paw and hock modules, coat profile, markings and user-authored proportions. Hybrid species should be possible without copying the whole character.

## Anatomy part contract

The new \`core/anatomy.py\` module adds validation for anatomy part manifests using the repository's existing \`anthroforge.part\` v1 format and \`PARTS_STANDARD.md\` fields.

For a genital module mounted at \`pelvis.genital\`, the contract requires:

- Explicit adult-only metadata; the default application setting does not equip adult-only anatomy.
- An existing, non-empty LOD0 asset inside the part folder. The current validator checks containment and presence, not GLB parsing or topology quality; those remain export-time QA gates.
- Own skin weights for the shared rig; rigid attachment is not accepted for an articulated module.
- The complete \`GenBase → Gen01 → Gen02 → Gen03 → Gen04\` motion chain and \`GenScrot\` bone.
- Named morph channels and a collision-profile identifier.
- An explicit supported body-plan list and a plan-specific socket override when needed.
- One occupant at the genital socket, with validation before export.

The application-level \`adult_content_enabled\` argument is a visibility/export preference, **not age verification**. A shipping application must apply its own account and age policy.

## What this change does not claim

This change adds a reusable contract and validator. The LOD0 check verifies a non-empty file exists; it does not yet parse the mesh or verify its topology. It does not ship a genital mesh, create an anatomical model from a reference photo, generate authored skin weights, implement PhysBones/SpringBones, or prove collision-free animation. Those require actual assets, Blender/Unity runtime checks and pose-suite QA.

## Required next implementation passes

1. **Reference-driven base anatomy:** measure the supplied sona reference and author the correct head/body proportions, markings, coat and distinctive appendages. Keep reference-derived features as editable parameters, not baked identity.
2. **Plan-aware body meshes:** biped, taur, feral and naga must have separate fit regions, pelvis transforms, locomotion and socket instances.
3. **Rigged anatomy assets:** create continuous, watertight, weighted meshes with morph targets and corrective shapes. Use authored weights; retain the current procedural loft only as a preview/prototyping route.
4. **Collision and motion:** test neutral, walk, run, crouch, sit, tail poses and extreme slider endpoints. Validate body, clothing and fur clearances.
5. **Single assembly pipeline:** make the Core Service resolve part manifests, assemble geometry/materials, validate the final mesh and export the same character the Babylon viewport previews. Until that adapter lands, selected parts are rejected by the Python exporter so incomplete builds cannot be mistaken for complete ones.
6. **Platform profiles:** generate platform-specific rigs and reports. VRChat setup still requires Unity Humanoid validation, Avatar Descriptor, expressions, colliders/PhysBones and SDK Build & Test.

## Reference handling

The Google Photos share link supplied for the user's sona could not be fetched by the repository/web environment. Do not infer its colors, species, proportions or distinctive traits. Ask the user to attach the reference image directly; use it only for this project unless the user explicitly asks to save it as a persistent reference.
