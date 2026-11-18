# 3D agent skills catalogue

This directory records the discovery catalogue from [zhuyansen/awesome-3d-skills](https://github.com/zhuyansen/awesome-3d-skills).

- `catalog.json` contains all **211** categorized project entries from the upstream README at the retrieval date.
- The source list is dedicated to the public domain under CC0 1.0; see the upstream [LICENSE](https://github.com/zhuyansen/awesome-3d-skills/blob/main/LICENSE).
- The source repository's security labels and descriptions are third-party metadata, not AnthroForge security reviews.
- Each linked project retains its own code, assets, trademarks and license. The CC0 dedication of the list does not relicense any linked project.

## What "imported" means

This commit imports the discovery metadata only. It does not vendor 211 codebases, install 211 MCP servers, execute third-party scripts, or imply that those projects are safe or compatible. The catalogue is a research input for choosing tools that improve AnthroForge's actual modeling, rigging, inspection and export pipeline.

## Recommended evaluation order for AnthroForge

1. **Blender authoring and automation** — evaluate `ahujasid/mcp-for-blender` as the first candidate for repeatable Blender scene operations and editable `.blend` outputs. Separately review `arjun988/blender-skills`, `EL4CTEO/blender-skills`, and `majidmanzarpour/blender-game-skills` for modeling, topology, rigging and game-ready asset workflows.
2. **Character-specific workflows** — review `icesixgod/awesome-astra-blender-characters` for reference-driven character modeling and visual QA, and `squall01337/mixamo-llm-mocap` for animation/retargeting ideas. Treat their outputs as candidates requiring AnthroForge's own mesh, skeleton and deformation validators.
3. **Runtime/editor automation** — evaluate Unity/Godot/Unreal entries only where they support a concrete target export or preview workflow. Do not add multiple competing engine bridges to the core application.
4. **Web 3D** — compare Three.js/WebGPU tools with the existing viewport stack before adopting anything. Prefer reusing the current renderer rather than introducing a second renderer without a measurable benefit.
5. **CAD** — reserve CAD integrations for hard-surface props, fixtures and measured accessories; they are not substitutes for organic character topology and deformation workflows.
6. **Text/image-to-3D generation** — treat generated meshes as rough source assets. Require retopology, manifold/normal checks, scale normalization, UV/material validation, rigging and reference comparison before a generated asset can enter the production library.

## Adoption gate for every candidate

Before adding a dependency or enabling an agent tool, record:

- upstream URL, exact commit/release and maintainer activity;
- explicit software license and obligations for code, models, sample assets and generated outputs;
- install/runtime dependencies, supported Blender/engine/Python versions and platform support;
- network access, telemetry, credential handling, file-system scope and command execution behavior;
- whether tools are read-only or can modify/delete files, run arbitrary code, or access external services;
- reproducible smoke test and an uninstall/disable path;
- measurable benefit to AnthroForge versus direct Blender Python and existing app APIs.

Do not execute unreviewed install scripts. Prefer pinned versions, isolated environments, least-privilege filesystem access and explicit approval for destructive or network-capable operations.

## Provenance and updates

The catalogue is a snapshot, not a live dependency. To refresh it, compare the upstream README and record the retrieval date and diff. Preserve source URLs and curator labels, but independently re-check current project state before adoption.
