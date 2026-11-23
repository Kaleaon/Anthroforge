"""MCP tool-surface catalogue (stub transport — handlers land here).

The 28 tools of APP_BLUEPRINT §4.3, named exactly as specced there.
Phase 1 (MVP, blueprint §15) ships tools #1–10, #18–21, #25 and #27
over stdio; the rest follow in their phases. Entries stay marked
``status: "stub"`` until their handler is wired to the Core Service —
this module deliberately contains no MCP SDK dependency and no
business logic, per the §4 design rule ("the MCP server contains no
implementation"): handlers only marshal arguments into Core Service
calls (core/build.py) and marshal results back.

Live since the Nov 12, 2026 integration pass (INTEGRATION.md):
``validate_character`` (#27) and ``export_run`` (#20).
"""

from __future__ import annotations

from pathlib import Path

# (blueprint §4.3 row, tool name, in Phase-1 MVP scope?)
_TOOLS: list[tuple[int, str, bool]] = [
    # Character lifecycle
    (1, "character_create", True),
    (2, "character_load", True),
    (3, "character_save", True),
    (4, "character_share_code", True),
    (5, "character_duplicate", True),
    (5, "character_delete", True),
    # Shaping
    (6, "sliders_list", True),
    (7, "sliders_get", True),
    (8, "sliders_set", True),
    (9, "preset_apply", True),
    (10, "blend_set", True),
    (11, "anatomy_inspect", False),
    # Parts & teeth
    (12, "parts_search", False),
    (13, "part_equip", False),
    (14, "part_remove", False),
    (15, "teeth_set", False),
    # Fur & materials
    (16, "fur_set", False),
    (17, "material_set", False),
    (18, "library_search", True),
    # Render, export, jobs
    (19, "render_preview", True),
    (20, "export_run", True),
    (21, "jobs_list", True),
    (21, "job_get", True),
    (21, "job_cancel", True),
    # Learning pipeline
    (22, "intake_import", False),
    (23, "intake_learn", False),
    (24, "intake_finalize", False),
    # System
    (25, "app_status", True),
    (26, "rig_get", False),
    (27, "validate_character", True),
    (28, "undo", False),
    (28, "redo", False),
]

TOOL_NAMES: list[str] = [name for _, name, _ in _TOOLS]
MVP_TOOL_NAMES: list[str] = [name for _, name, mvp in _TOOLS if mvp]

_LIVE_TOOLS = frozenset({"validate_character", "export_run"})


def describe_tools() -> list[dict]:
    """The full §4.3 surface as descriptors."""
    return [
        {"name": name, "blueprint_row": row, "mvp": mvp,
         "status": "live" if name in _LIVE_TOOLS else "stub"}
        for row, name, mvp in _TOOLS
    ]


# ---------------------------------------------------------------------------
# Live handlers — argument marshalling only; all logic is core.build.
# ---------------------------------------------------------------------------

def _character_from_args(arguments: dict):
    from core.character import Character

    if "character" in arguments:
        return Character.from_dict(arguments["character"])
    if "path" in arguments:
        return Character.load(arguments["path"])
    raise ValueError("tool arguments need a 'character' record or a 'path' to one")


def _validate_character(arguments: dict) -> dict:
    """#27: validate a character + return its effective vector."""
    from core.build import Library, _merge_warnings, evaluate_character

    character = _character_from_args(arguments)
    library = Library.load()
    report, effective = evaluate_character(character, library)
    return {
        "ok": report.ok,
        "errors": report.errors,
        "warnings": _merge_warnings(report, effective),
        "effective_sliders": effective.sliders,
        "derived": effective.derived,
    }


def _export_run(arguments: dict) -> dict:
    """#20: evaluate a character onto its base, export a GLB, and run
    the QA gauntlet. Arguments: 'character' (record) or 'path'
    (.afchar.json), 'out' (GLB path), optional 'belly_variant'
    ('contact'), 'strict' (fold gate raises), 'run_qa' (default true)."""
    from core.build import Library, build_character

    character = _character_from_args(arguments)
    out = arguments.get("out")
    if not out:
        raise ValueError("export_run needs an 'out' GLB path")
    library = Library.load()
    report = build_character(
        character, library,
        out_path=Path(out),
        belly_variant=arguments.get("belly_variant"),
        strict=bool(arguments.get("strict", False)),
        run_qa=bool(arguments.get("run_qa", True)),
    )
    return {
        "ok": report.ok,
        "character_id": report.character_id,
        "base_id": report.base_id,
        "glb_path": report.glb_path,
        "applied": report.applied,
        "unapplied": report.unapplied,
        "flips_body": report.flips_body,
        "flips_all": report.flips_all,
        "derived": report.derived,
        "warnings": report.warnings,
        "qa": report.qa,
    }


_HANDLERS = {
    "validate_character": _validate_character,
    "export_run": _export_run,
}


def call_tool(name: str, arguments: dict | None = None) -> dict:
    """Dispatch. Live tools delegate to the Core Service; the rest
    raise until their phase wires them — loudly, never silently."""
    if name not in TOOL_NAMES:
        raise KeyError(f"unknown MCP tool: {name!r}")
    handler = _HANDLERS.get(name)
    if handler is None:
        raise NotImplementedError(
            f"MCP tool {name!r} is a stub: the stdio transport and Core Service "
            "handlers land in Phase 1 (APP_BLUEPRINT §15). The Core API it will "
            "wrap lives in the `core` package."
        )
    return handler(arguments or {})
