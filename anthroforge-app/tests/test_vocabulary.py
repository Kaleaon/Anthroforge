"""Web <-> Core vocabulary: translation, JS twin sync, end-to-end validation.

The Mini App / desktop web apps speak a rendering vocabulary
(morph.*, bodyslide.*, sos.*, driver.*, web bodies); the Core speaks
canonical slider records. This test proves the split-brain is fixed:
a record built the way the web UIs build it translates to a record
``Character.validate()`` accepts against the real slider registry.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from core.character import Character
from core.sliders import SliderRegistry
from core.vocabulary import (
    BASE_BODY_MAP,
    CARRIED_PREFIXES,
    HEAD_MAP,
    SLIDER_MAP,
    canonical_to_web_slider,
    translate_record,
)

ROOT = Path(__file__).resolve().parent.parent


def web_record(**overrides):
    rec = {
        "format": "anthroforge.character",
        "version": 1,
        "id": "chr_testvocab0000000000000001",
        "name": "Test Fennec",
        "base": {"body": "max", "head": "web_v2"},
        "sliders": {
            "morph.height": 0.95,
            "morph.ears": 1.42,
            "bodyslide.samson": 50,
            "bodyslide.glutes": 25,
            "bodyslide.meaner": 20,
            "sos.length": 1.0,
            "sos.knot": 25,
            "driver.jawOpen": 12,
        },
        "species_preset": {"preset": "fennec", "label": "Fennec Fox Preset"},
        "parts": [{"slot": "head", "part": "head_fennec"}],
        "fur": {},
        "materials": {"colors": {"primary": "#e09f5a"}},
        "identity": {"source": "telegram-miniapp", "species": "fennec"},
    }
    rec.update(overrides)
    return rec


def test_bases_translate_and_web_ids_preserved():
    out, warnings = translate_record(web_record())
    assert out["base"] == {"body": "af_body_neutral_v1", "head": "af_head_neutral_v2"}
    assert out["identity"]["base_body"] == "max"
    assert out["identity"]["base_head"] == "web_v2"
    assert warnings == []


def test_bodyslide_scales_to_canonical():
    out, _ = translate_record(web_record())
    assert out["sliders"]["body.build.muscle"] == pytest.approx(0.5)
    assert out["sliders"]["body.himbo.legs_glutes"] == pytest.approx(0.25)
    assert out["sliders"]["head.brow.projection"] == pytest.approx(30.0)


def test_morph_sos_driver_carried_not_mapped():
    out, _ = translate_record(web_record())
    assert out["identity"]["morphs"] == {"height": 0.95, "ears": 1.42}
    assert out["identity"]["sos"] == {"length": 1.0, "knot": 25}
    assert out["identity"]["drivers"] == {"jawOpen": 12}
    assert not any(k.startswith(("morph.", "sos.", "driver.")) for k in out["sliders"])


def test_unknown_slider_preserved_and_warned():
    rec = web_record()
    rec["sliders"]["bodyslide.nonsense"] = 7
    out, warnings = translate_record(rec)
    assert out["identity"]["unmapped_sliders"] == {"bodyslide.nonsense": 7}
    assert any("bodyslide.nonsense" in w for w in warnings)


def test_canonical_record_passes_through_unchanged():
    rec = {
        "format": "anthroforge.character",
        "version": 1,
        "id": "chr_testvocab0000000000000002",
        "name": "Sen",
        "base": {"body": "af_body_neutral_v1", "head": "af_head_neutral_v2"},
        "sliders": {"body.build.muscle": 0.8, "body.belly.protrusion": 0.3},
        "species_preset": None,
        "parts": [],
        "fur": {},
        "materials": {},
        "identity": {},
    }
    out, warnings = translate_record(rec)
    assert out == rec
    assert warnings == []


def test_input_is_not_mutated():
    rec = web_record()
    snapshot = json.dumps(rec, sort_keys=True)
    translate_record(rec)
    assert json.dumps(rec, sort_keys=True) == snapshot


def test_inverse_mapping():
    assert canonical_to_web_slider("body.build.muscle") == ("bodyslide.samson", 100.0)
    assert canonical_to_web_slider("head.brow.projection") == ("bodyslide.meaner", 1.0 / 1.5)
    assert canonical_to_web_slider("body.himbo.weight_0_to_1") is None


def test_translated_record_validates_against_registry():
    registry = SliderRegistry.from_folder(ROOT / "library" / "sliders")
    out, _ = translate_record(web_record())
    char = Character.from_dict(out)
    report = char.validate(registry)
    assert report.errors == [], report.errors


def test_all_preset_files_translate_and_validate():
    registry = SliderRegistry.from_folder(ROOT / "library" / "sliders")
    for path in sorted((ROOT / "library" / "presets").glob("*.afchar.json")):
        char = Character.load(path)
        out, warnings = translate_record(char.to_dict())
        assert out == char.to_dict()
        assert warnings == []
        assert Character.from_dict(out).validate(registry).errors == []


def _load_js_table():
    """Extract the AF_VOCABULARY object literal from vocabulary.js."""
    text = (ROOT / "telegram-miniapp" / "vocabulary.js").read_text()
    start = text.index("var AF_VOCABULARY = ") + len("var AF_VOCABULARY = ")
    assert text[start] == "{"
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise AssertionError("AF_VOCABULARY literal not closed")


def test_js_twin_matches_python_table():
    js = _load_js_table()
    assert js["version"] == 1
    assert js["base_body_map"] == BASE_BODY_MAP
    assert js["head_map"] == HEAD_MAP
    assert js["carried_prefixes"] == CARRIED_PREFIXES
    js_sliders = {k: tuple(v) for k, v in js["slider_map"].items()}
    assert js_sliders == SLIDER_MAP


SHARED_SCRIPTS = ("sharecode.js", "vocabulary.js", "presets.js", "record.js")


def test_both_web_apps_reference_shared_scripts_and_embed_no_duplicates():
    miniapp_dir = ROOT / "telegram-miniapp"
    miniapp_html = (miniapp_dir / "index.html").read_text(encoding="utf-8")
    v2_path = ROOT.parent / "anthroforge-v2" / "anthroforge_3d_pro_v2.html"
    v2_html = v2_path.read_text(encoding="utf-8")

    for script_name in SHARED_SCRIPTS:
        canonical = (miniapp_dir / script_name).resolve()
        assert canonical.is_file(), f"missing shared script {canonical}"

        v2_rel = f"../anthroforge-app/telegram-miniapp/{script_name}"
        assert re.search(
            rf'<script\s+src=["\']{re.escape(v2_rel)}["\']\s*></script>',
            v2_html,
        ), f"anthroforge_3d_pro_v2.html must load {v2_rel} as a classic script"
        assert (v2_path.parent / v2_rel).resolve() == canonical

        assert re.search(
            rf'<script\s+src=["\']{re.escape(script_name)}["\']\s*></script>',
            miniapp_html,
        ), f"telegram-miniapp/index.html must load {script_name} as a classic script"

    for forbidden in (
        "AF_VOCABULARY",
        "decodeShareCode",
        "AF_PRESETS",
        "buildAfcharRecord",
        "applyAfcharRecord",
    ):
        assert forbidden not in v2_html, (
            f"anthroforge_3d_pro_v2.html must not embed inline {forbidden}"
        )

    assert "AF_VOCABULARY" not in miniapp_html
    assert "function decodeShareCode" not in miniapp_html


def test_js_sharecode_and_record_suite():
    node = shutil.which("node")
    if node is None:
        pytest.skip("node runtime not installed")
    res = subprocess.run(
        [node, str(ROOT / "tests" / "test_sharecode_js.mjs")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}"
