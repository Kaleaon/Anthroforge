"""MCP surface: the catalogue is intact; validate_character and
export_run are live and delegate to the Core; the rest stay stubs."""

from pathlib import Path

import pytest

from mcp import server

APP = Path(__file__).resolve().parent.parent


def test_catalogue_shape_unchanged():
    tools = server.describe_tools()
    assert len(tools) == 32  # 28 blueprint rows, some rows name several tools
    live = {t["name"] for t in tools if t["status"] == "live"}
    assert live == {"validate_character", "export_run"}
    assert set(server.MVP_TOOL_NAMES) <= set(server.TOOL_NAMES)


def test_validate_character_live():
    out = server.call_tool("validate_character", {
        "path": str(APP / "library" / "presets" / "sen.afchar.json"),
    })
    assert out["ok"] is True
    assert out["errors"] == []
    assert out["derived"]["tissue.level"] > 0.5


def test_validate_character_merges_validation_and_coupling_warnings(tmp_path):
    char_dict = {
        "format": "anthroforge.character",
        "version": 1,
        "name": "Warning merge check",
        "sliders": {
            "head.brow.projection": 500.0,  # validation range clamp warning
            "body.muscle": 0.1,
            "body.belly.pot": 0.9,          # coupling bare-belly advisory
        },
    }
    validated = server.call_tool("validate_character", {"character": char_dict})
    assert validated["ok"] is True
    assert len(validated["warnings"]) >= 2
    assert "head.brow.projection: requested 500.0 is above range max 150.0" in validated["warnings"][0]
    assert any("tissue-only" in msg for msg in validated["warnings"][1:])
    exported = server.call_tool("export_run", {
        "character": char_dict,
        "out": str(tmp_path / "warn.glb"),
        "run_qa": False,
    })
    assert exported["warnings"][:len(validated["warnings"])] == validated["warnings"]


def test_export_run_live(tmp_path):
    out_path = tmp_path / "pyn.glb"
    result = server.call_tool("export_run", {
        "character": {
            "format": "anthroforge.character", "version": 1,
            "name": "Export check",
            "sliders": {"body.belly.protrusion": 1.0},
        },
        "out": str(out_path),
    })
    assert result["ok"] is True
    assert result["flips_body"] == 0
    assert result["applied"] == ["body.belly.protrusion"]
    assert out_path.is_file() and out_path.stat().st_size > 100_000


def test_stub_tools_still_raise_loudly():
    with pytest.raises(NotImplementedError, match="stub"):
        server.call_tool("parts_search", {})
    with pytest.raises(KeyError, match="unknown MCP tool"):
        server.call_tool("not_a_tool", {})
