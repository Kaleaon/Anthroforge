"""The six spec'd presets: files load, every slider validates against
the registry, share codes round-trip, and the vectors carry the
specs' load-bearing values (post-harmonisation)."""

import json
from pathlib import Path

import pytest

from core import sharecode
from core.build import Library, evaluate_character
from core.character import Character

APP = Path(__file__).resolve().parent.parent
PRESETS = APP / "library" / "presets"

FILES = {
    "orc_bara_strongman": "chr_preset_orc_bara_strongman",
    "orc_bara_bodybuilder": "chr_preset_orc_bara_bodybuilder",
    "pyn": "chr_preset_pyn",
    "sen": "chr_preset_sen",
    "sen_muscle_bear": "chr_preset_sen_muscle_bear",
    "jorge": "chr_preset_jorge",
    # batch 2 (presets-titan-batch2.md)
    "gamma": "chr_preset_gamma",
    "alpha": "chr_preset_alpha",
    "beta": "chr_preset_beta",
    "delta": "chr_preset_delta",
    "sage": "chr_preset_sage",
    "sage_pony": "chr_preset_sage_pony",
    "thatch": "chr_preset_thatch",
    "hollis": "chr_preset_hollis",
}


@pytest.fixture(scope="module")
def library():
    return Library.load(APP / "library")


@pytest.fixture(scope="module")
def index():
    return json.loads((PRESETS / "INDEX.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("stem,cid", sorted(FILES.items()))
def test_preset_loads_validates_and_roundtrips(stem, cid, library, index):
    char = Character.load(PRESETS / f"{stem}.afchar.json")
    assert char.id == cid
    report, _ = evaluate_character(char, library)
    assert report.ok, f"{cid}: {report.errors}"
    row = next(r for r in index["presets"] if r["id"] == cid)
    decoded = sharecode.decode(row["share_code"])
    assert decoded.to_dict(include_provenance=False) == \
        char.to_dict(include_provenance=False)


def test_orc_poles_differ_only_in_tissue(library):
    """BARA_LESSONS doctrine: the poles are tissue moves, never muscle
    moves — the unified MuscleVector is identical in both orcs."""
    sm = Character.load(PRESETS / "orc_bara_strongman.afchar.json")
    bb = Character.load(PRESETS / "orc_bara_bodybuilder.afchar.json")
    for sid in ("body.muscle", "body.himbo.arms_traps",
                "body.himbo.arms_traps_meat", "body.himbo.arms_traps_push",
                "body.arms.delts", "body.himbo.legs_size",
                "body.himbo.legs_thigh"):
        assert sm.sliders[sid] == bb.sliders[sid] == pytest.approx(
            {"body.muscle": 0.80, "body.himbo.arms_traps": 0.95,
             "body.himbo.arms_traps_meat": 1.00, "body.himbo.arms_traps_push": 0.90,
             "body.arms.delts": 0.95, "body.himbo.legs_size": 1.00,
             "body.himbo.legs_thigh": 1.00}[sid])
    # ...while the tissue thesis inverts: strongman shrink 25 vs
    # bodybuilder shrink 85 on TorsoWaistSize ("Shrink Waist").
    assert sm.sliders["body.himbo.torso_waist_size"] == pytest.approx(0.25)
    assert bb.sliders["body.himbo.torso_waist_size"] == pytest.approx(0.85)
    assert sm.sliders["body.chubby"] == pytest.approx(0.65)
    assert bb.sliders["body.chubby"] == pytest.approx(0.05)
    # NeckMass: the strongman calls it at 90 (BARA_LESSONS section 6 B).
    assert sm.sliders["body.neck.mass"] == pytest.approx(0.9)


def test_sen_muscle_bear_holds_muscle_moves_tissue(library):
    sen = Character.load(PRESETS / "sen.afchar.json")
    mb = Character.load(PRESETS / "sen_muscle_bear.afchar.json")
    moved = {sid for sid in set(sen.sliders) | set(mb.sliders)
             if sen.sliders.get(sid) != mb.sliders.get(sid)}
    assert moved == {
        "body.chubby", "body.tissue.mass_smooth",
        "body.definition.traps_valleys", "body.definition.back",
        "body.himbo.pecs_saggy", "body.belly.pot",
    }
    assert mb.sliders["body.muscle"] == sen.sliders["body.muscle"] == pytest.approx(0.65)
    assert mb.sliders["body.chubby"] == pytest.approx(0.55)
    assert mb.sliders["body.definition.back"] == pytest.approx(0.50)


def test_titan_head_vectors_ride_in_species_preset():
    sen = Character.load(PRESETS / "sen.afchar.json")
    head = sen.species_preset["head_sliders"]
    assert len(head) == 30  # 31 spec sliders minus BrowProjection (canonical)
    assert head["EarTipPoint"] == -80 and head["RuffVolume"] == 70
    assert sen.sliders["head.brow.projection"] == pytest.approx(-20.0)
    assert sen.species_preset["export_scale"] == pytest.approx(1.74)
    assert sen.fur["profile"] == "species.bear.coat"
    jorge = Character.load(PRESETS / "jorge.afchar.json")
    assert jorge.species_preset["head_sliders"]["StopAngle"] == 90
    assert jorge.species_preset["head_sliders"]["BrowScowl"] == 0
    pyn = Character.load(PRESETS / "pyn.afchar.json")
    assert pyn.species_preset["head_sliders"]["EarHeight"] == 100


# ------------------------------------------------------------- batch 2

def _b2(stem):
    return Character.load(PRESETS / f"{stem}.afchar.json")


def test_wolves_share_species_head_vector_verbatim():
    """Batch 2 s.1: all four wolves carry the species-head-spec wolf
    column unchanged - no per-wolf head deltas exist in the files and
    none may be invented (coats/faces are the wolves' own choices)."""
    heads = {}
    for stem in ("gamma", "alpha", "beta", "delta"):
        ch = _b2(stem)
        head = ch.species_preset["head_sliders"]
        assert len(head) == 30
        assert head["MuzzleLength"] == 45 and head["CraniumWidth"] == -25
        assert head["CheekWidth"] == -25 and head["JawDepth"] == 25
        assert ch.sliders["head.brow.projection"] == pytest.approx(-25.0)
        assert ch.fur["profile"] == "species.wolf.coat"
        heads[stem] = head
    assert len({json.dumps(h, sort_keys=True) for h in heads.values()}) == 1


def test_twins_same_frame_delta_is_the_runner():
    """Joe's Nov 4 2026 ruling: Delta is 9'0" like Gamma (same export
    scale), 350 kg vs 408 - the vector is Gamma's at the spec's ~74%
    segment-mass rule with legs/glutes/calf held (cursorial)."""
    g, d = _b2("gamma"), _b2("delta")
    assert g.species_preset["export_scale"] == d.species_preset["export_scale"] \
        == pytest.approx(1.57)
    assert g.species_preset["mass_kg"] == 408
    assert d.species_preset["mass_kg"] == 350
    # tissue drops hard, muscle holds (lean is a tissue fact - doctrine)
    assert d.sliders["body.chubby"] < g.sliders["body.chubby"]
    assert d.sliders["body.muscle"] == pytest.approx(0.80)
    assert g.sliders["body.muscle"] == pytest.approx(0.85)
    # the poles invert between the twins
    assert g.sliders["body.himbo.lean"] == pytest.approx(-1.0)
    assert d.sliders["body.himbo.lean"] == pytest.approx(0.35)
    # cursorial exceptions: calf ABOVE the twin's, glutes held high
    assert d.sliders["body.himbo.legs_calf_size"] > \
        g.sliders["body.himbo.legs_calf_size"]
    assert d.sliders["body.himbo.legs_glutes"] == pytest.approx(0.85)
    # neck-mass ordering follows the specs' neck segment shares
    assert g.sliders["body.neck.mass"] == pytest.approx(0.95)
    assert d.sliders["body.neck.mass"] == pytest.approx(0.65)


def test_alpha_leader_not_warrior():
    """Master Decisions #37/#38: Alpha's 250 kg is held below Gamma's
    408 BY DESIGN (authority vs force); the narrow endurance chest is
    the load-bearing slider difference."""
    a, g = _b2("alpha"), _b2("gamma")
    assert a.species_preset["mass_kg"] == 250
    assert a.species_preset["export_scale"] == pytest.approx(1.48)
    assert a.sliders["body.himbo.torso_width"] == pytest.approx(0.70)
    assert g.sliders["body.himbo.torso_width"] == pytest.approx(0.90)
    assert a.sliders["body.muscle"] < g.sliders["body.muscle"]


def test_beta_gentle_density():
    """Beta: densest wolf (204 kg at 221 cm), softest tissue thesis -
    highest wolf Chubby with Muscle held at Sen's 65."""
    b = _b2("beta")
    assert b.species_preset["export_scale"] == pytest.approx(1.26)
    assert b.sliders["body.chubby"] == pytest.approx(0.60)
    assert b.sliders["body.muscle"] == pytest.approx(0.65)
    assert b.sliders["body.tissue.mass_smooth"] == pytest.approx(0.70)
    for stem in ("gamma", "alpha", "delta"):
        assert _b2(stem).sliders["body.chubby"] < b.sliders["body.chubby"]


def test_sage_stud_and_pony_variant():
    """Sage stud is the design point (274 cm / ~480 kg, hindquarters
    pinned); the pony is a flagged scale variant sharing the vector."""
    sage, pony = _b2("sage"), _b2("sage_pony")
    sp = sage.species_preset
    assert sp["export_scale"] == pytest.approx(1.57)
    assert sp["mass_kg"] == 480 and sp["height_cm"] == 274
    # hindquarter mass lives in legs/glutes on the biped plan
    assert sage.sliders["body.himbo.legs_glutes"] == pytest.approx(1.0)
    assert sage.sliders["body.himbo.legs_thigh"] == pytest.approx(1.0)
    assert sage.fur["profile"] == "species.clydesdale.coat"
    assert pony.species_preset["variant_of"] == "chr_preset_sage"
    assert pony.species_preset["export_scale"] == pytest.approx(1.34)
    assert pony.species_preset["mass_kg"] == 300
    assert pony.sliders == sage.sliders  # shared vector, flagged in doc


def test_no_head_species_are_empty_and_flagged():
    """Sage/Thatch/Hollis: no equine/avian/serval head vector exists -
    head_sliders must be EMPTY (never borrowed) and the record must
    carry the flag; no brow projection slider is set."""
    for stem in ("sage", "sage_pony", "thatch", "hollis"):
        ch = _b2(stem)
        assert ch.species_preset["head_sliders"] == {}
        assert "empty BY DESIGN" in ch.species_preset["head_note"]
        assert "head.brow.projection" not in ch.sliders


def test_thatch_compact_barrel_no_fur_substitute():
    """Thatch: barrel carried by width at near-zero mass sliders; owl
    neck kept low on purpose; feathers have no library profile, so fur
    stays empty rather than borrowing a mammal coat."""
    t = _b2("thatch")
    assert t.species_preset["export_scale"] == pytest.approx(0.99)
    assert t.species_preset["mass_kg"] == 70
    assert "body.himbo.body_mass" not in t.sliders  # held at 0
    assert t.sliders["body.himbo.torso_width"] == pytest.approx(0.75)
    assert t.sliders["body.neck.mass"] == pytest.approx(0.30)
    assert t.fur == {}


def test_hollis_adjacent_provisional_and_slight():
    """Hollis is ADJACENT, not a Titan; his record must say so, must
    carry the provisional flag (shape decisions are his), and the
    vector is the batch's slight-spring pole."""
    h = _b2("hollis")
    sp = h.species_preset
    assert "ADJACENT, not a Titan" in sp["adjacency"]
    assert "provisional" in sp["provisional"]
    assert sp["export_scale"] == pytest.approx(1.05)
    assert sp["mass_kg"] == pytest.approx(54.1)
    assert h.fur == {}  # no serval profile exists; none invented
    # pounce engine: glutes are his strongest leg value
    assert h.sliders["body.himbo.legs_glutes"] == pytest.approx(0.50)
    assert h.sliders["body.himbo.legs_glutes"] > \
        h.sliders["body.himbo.legs_thigh"]
