"""End-to-end builds: character -> couplings -> geometry -> GLB -> QA.

Acceptance anchors are the proofs' own published numbers: the belly
system at +1 folds 0 body faces and moves the navel +11.27/-6.99 cm
(Blender); the bara combined build folds 0 faces at +1; the Sen
composition was built by the six-agent round from these same targets.
"""

from pathlib import Path

import numpy as np
import pytest

from core.build import Library, build_character, evaluate_character
from core.character import Character

APP = Path(__file__).resolve().parent.parent
LIB = APP / "library"


@pytest.fixture(scope="module")
def library():
    return Library.load(LIB)


def test_belly_build_holds_the_fold_gate(tmp_path, library):
    char = Character(name="Belly proof", sliders={"body.belly.protrusion": 1.0})
    rep = build_character(char, library, out_path=tmp_path / "belly.glb")
    assert rep.applied == ["body.belly.protrusion"]
    assert rep.flips_body == 0
    assert rep.qa is not None and rep.qa["blocked"] is False
    base = library.bases.load(rep.base_id)
    import core.geometry as geom

    rec = library.sliders.get("body.belly.protrusion")
    fld = geom.load_instance(rec.id, rec.instances[base.id], base.id,
                             base.n_verts, APP.parent)
    navel = base.positions[base.navel] + fld.at(1.0)[base.navel]
    delta = navel - base.positions[base.navel]
    assert delta[1] == pytest.approx(0.1127, abs=0.006)
    assert delta[2] == pytest.approx(-0.0699, abs=0.006)


def test_belly_contact_variant_builds(tmp_path, library):
    char = Character(name="Contact", sliders={"body.belly.protrusion": 1.0})
    rep = build_character(char, library, out_path=tmp_path / "c.glb",
                          belly_variant="contact")
    assert rep.flips_body == 0


def test_bara_combined_build_holds_the_fold_gate(tmp_path, library):
    char = Character(name="Bara", sliders={"body.build.bara_strongman": 1.0})
    rep = build_character(char, library, out_path=tmp_path / "bara.glb")
    assert rep.applied == ["body.build.bara_strongman"]
    assert rep.flips_body == 0


def test_bara_components_sum_to_the_combined_build(tmp_path, library):
    """The three component builds at +1 must reproduce the combined
    target's geometry (BARA_PROOF: max deviation 0.020 cm)."""
    import core.geometry as geom

    base = library.bases.load("makehuman_hm08")
    total = base.positions.copy()
    for sid in ("body.build.muscle", "body.build.chest_width",
                "body.build.tissue_strongman"):
        rec = library.sliders.get(sid)
        fld = geom.load_instance(sid, rec.instances[base.id], base.id,
                                 base.n_verts, APP.parent)
        total = total + fld.at(1.0)
    rec = library.sliders.get("body.build.bara_strongman")
    fld = geom.load_instance(rec.id, rec.instances[base.id], base.id,
                             base.n_verts, APP.parent)
    combined = base.positions + fld.at(1.0)
    dev_cm = np.abs(total - combined).max() * 100
    assert dev_cm <= 0.03


def test_masculine_base_belly_instance(tmp_path, library):
    char = Character(name="Masc", base={"body": "makehuman_hm08_masculine",
                                        "head": "af_head_neutral_v2"},
                     sliders={"body.belly.protrusion": 1.0})
    rep = build_character(char, library, out_path=tmp_path / "m.glb")
    assert rep.base_id == "makehuman_hm08_masculine"
    assert rep.applied == ["body.belly.protrusion"]
    assert rep.flips_body == 0


def test_sen_preset_evaluates_and_builds(tmp_path, library):
    """The Sen preset: every slider validates, the coupling layer
    resolves his tissue regionally, and the sliders that carry hm08
    geometry today (his definition values at their attenuated
    effective values, the neck/forearm correctives absent — Sen's
    vector predates them) apply without folding."""
    sen = Character.load(LIB / "presets" / "sen.afchar.json")
    report, effective = evaluate_character(sen, library)
    assert report.ok, report.errors
    assert effective.derived["tissue.level"] > 0.5  # strongman tissue load
    assert effective.derived["tissue.abdomen"] > effective.derived["tissue.forearm"]
    rep = build_character(sen, library, out_path=tmp_path / "sen.glb")
    assert "body.definition.traps_valleys" in rep.applied
    assert rep.flips_body == 0
    # The HIMBO vocabulary majority is record-only for now — reported,
    # never silently dropped.
    assert len(rep.unapplied) > 20


def test_every_hm08_instance_holds_the_fold_gate_at_full_value(tmp_path, library):
    """The instance sweep: each slider carrying hm08 geometry, alone
    at +1, folds zero body faces (the packs are verified the same way
    by scripts/build_instance_packs.py at build time)."""
    swept = []
    for sid in library.sliders.ids():
        rec = library.sliders.get(sid)
        if "makehuman_hm08" not in (rec.instances or {}):
            continue
        char = Character(name=sid, sliders={sid: 1.0})
        rep = build_character(char, library, out_path=tmp_path / f"{sid}.glb",
                              run_qa=False)
        assert rep.applied == [sid]
        assert rep.flips_body == 0, f"{sid}: {rep.flips_body} flips, " \
                                    f"min dot {rep.min_body_dot}"
        swept.append(sid)
    assert swept == [
        "body.belly.protrusion", "body.build.bara_strongman",
        "body.build.chest_width", "body.build.muscle",
        "body.build.tissue_strongman", "body.definition.back",
        "body.definition.flat_abs", "body.definition.pecs_crease",
        "body.definition.traps_valleys", "body.forearm.mass",
        "body.neck.mass",
    ]


def test_unknown_slider_character_refuses_to_build(tmp_path, library):
    char = Character(sliders={"body.nope": 1.0})
    with pytest.raises(Exception):
        build_character(char, library, out_path=tmp_path / "x.glb")
