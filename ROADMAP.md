# AnthroForge Development Roadmap

This roadmap is an execution plan for the existing repository. It separates validated core behavior from prototype work and defines observable completion criteria so that new systems do not become disconnected demos.

## Product direction

Build a desktop-first, extensible 3D character creator for anthropomorphic and fantasy species. A character is a persistent, editable specification whose body plan, species features, anatomy modules, materials, rig and exports remain coherent. The creator should support both authored assets and procedural generation; procedural blockouts are scaffolding, not substitutes for finished meshes.

## Workstreams and order

### P0 — Reliability and reproducible development

- Keep character, anatomy, geometry and export validation deterministic.
- Reject malformed, non-finite and out-of-bounds input at the boundary where it enters the system.
- Keep asset references workspace-confined, including Windows paths and symlinks.
- Run the Python regression suite on every relevant pull request.
- Add small fixtures for every bug fixed; record commands and results in each PR.

**Exit criteria:** clean CI on supported Python versions; malformed assets fail with actionable domain errors; no silent data loss or invalid GLB output.

### P1 — Species/body-plan mesh pipeline

- Establish a canonical species profile schema: body plan, proportions, landmarks, appendages, topology expectations, sockets and rig mapping.
- Treat biped, taur, feral/quadruped and naga as distinct body plans, not a single human mesh with cosmetic add-ons.
- Separate shared anatomical regions from species-specific geometry and keep topology/landmarks stable where interchange is required.
- Promote blockouts only after surface continuity, normals, manifoldness, scale and landmark checks pass.
- Store provenance and generation parameters beside every generated asset.

**Exit criteria:** each supported plan has a reproducible LOD0 mesh, documented landmarks, validation report and preview; no profile is described as production-ready while it only emits primitives.

### P2 — Live creator and anatomy editing

- Connect character records and anatomy manifests to actual viewport objects.
- Make parameter changes regenerate only affected geometry and preserve unrelated edits.
- Support add/remove/replace modules, per-part settings, undo/redo and persistent save/reload.
- Provide explicit adult-content preference gates and clear UI state; the preference is not identity or age verification.
- Keep modular anatomy data separate from the base body so creators can swap compatible assets.

**Exit criteria:** a user can edit a supported character, see the mesh update, save, restart, reload and recover the same configuration without missing or silently ignored parts.

### P3 — Rigging, deformation and collision

- Define a canonical skeleton contract per body plan and explicit retarget maps.
- Generate or author skin weights with normalization and influence-count checks.
- Add corrective shapes for high-strain joints and species-specific motion.
- Test collision/clearance at representative slider extremes and animation poses, not only at the neutral pose.
- Keep deformation QA reports attached to the asset/profile version.

**Exit criteria:** validated weights, no unreported unweighted vertices, bounded deformation error and collision tests across a documented pose/parameter matrix.

### P4 — Materials, fur and rendering

- Standardize material slots, texture conventions, fur/groom metadata and preview lighting.
- Keep viewport materials and export materials semantically aligned.
- Make quality/performance settings explicit and measurable.

**Exit criteria:** stable material appearance in the creator and supported interchange formats, with documented fallbacks.

### P5 — Interchange and release quality

- Treat GLB as the first portable round-trip target; then validate FBX/Blender/Unity paths where supported.
- Preserve transforms, skeletons, morphs, materials, naming and metadata across export/import.
- Add golden fixtures and automated round-trip comparisons.
- Produce versioned sample characters and a reproducible release build.

**Exit criteria:** documented format support backed by round-trip tests; no format is advertised as supported solely because a file can be written.

## Immediate implementation queue

1. Harden geometry field ingestion against NaN/Infinity, invalid gamma values, malformed shapes and non-finite slider values.
2. Harden GLB writing against malformed topology, invalid indices, empty geometry and non-finite normals.
3. Add regression CI and establish a baseline report for the current test suite.
4. Audit the anatomy manifest contract and connect its resolved parts to the build pipeline.
5. Define a versioned species profile schema and promote one body plan at a time from blockout to validated mesh.

## Engineering rules

- Work in focused branches and submit pull requests; do not silently push experimental changes to `main`.
- A PR must state scope, risks, tests run, tests not run and known limitations.
- Prefer small, composable validators and explicit data contracts over implicit conventions.
- Preserve backward compatibility where possible; version schema changes and provide migrations when it is not.
- Never claim a species, rig, editor or export path is complete until its exit criteria are met.
