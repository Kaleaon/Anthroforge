"""Coupling layer: the Muscle x Tissue interaction model
(MUSCLE_TISSUE_MODEL.md). Covers record loading, the composition
invariant, attenuation behaviour, the TissueDefinition dial, the
PowerBelly terms, the mass-distribution axis, and the gachimuchi
worked example (Sen vs sen_muscle_bear)."""

from pathlib import Path

import pytest

from core.character import Character
from core.sliders import (
    PIPELINE_STAGES,
    CouplingRegistry,
    SliderRegistry,
    evaluate_effective_vector,
)

ROOT = Path(__file__).resolve().parent.parent
SLIDERS_DIR = ROOT / "library" / "sliders"
COUPLINGS_DIR = ROOT / "library" / "couplings"


@pytest.fixture(scope="module")
def registry() -> SliderRegistry:
    return SliderRegistry.from_folder(SLIDERS_DIR)


@pytest.fixture(scope="module")
def couplings() -> CouplingRegistry:
    return CouplingRegistry.from_folder(COUPLINGS_DIR)


def ev(registry, couplings, raw):
    return evaluate_effective_vector(registry, couplings, raw)


# -- records & doctrine -----------------------------------------------------


def test_coupling_registry_loads_seven_records(couplings):
    # Eight records since the Nov 12, 2026 wrap amendment added
    # muscle_tissue.tissue_wrap (MUSCLE_TISSUE_MODEL.md section 4).
    assert couplings.ids() == [
        "muscle_tissue.composition",
        "muscle_tissue.definition_attenuation",
        "muscle_tissue.distribution",
        "muscle_tissue.power_belly",
        "muscle_tissue.regional_tissue",
        "muscle_tissue.show_through",
        "muscle_tissue.tissue_dial",
        "muscle_tissue.tissue_wrap",
    ]


def test_composition_record_agrees_with_code_pipeline(couplings):
    comp = couplings.find_kind("composition_order")
    assert comp.params["evaluation_stages"] == list(PIPELINE_STAGES)
    assert comp.params["field_order"] == [
        "base", "muscle_field", "tissue_field", "gravity_drape",
    ]


# -- composition invariants ---------------------------------------------------


def test_muscle_stage_passes_muscle_through(registry, couplings):
    """Composition invariant: tissue NEVER rewrites the Muscle vector
    itself (poles are tissue moves, BARA_LESSONS R16). body.muscle is
    not a show-through target, so it is bit-identical at any tissue."""
    for chubby in (0.0, 0.5, 1.0):
        out = ev(registry, couplings, {"body.muscle": 0.65, "body.chubby": chubby})
        assert out.sliders["body.muscle"] == 0.65


def test_evaluation_does_not_mutate_raw_vector(registry, couplings):
    raw = {"body.muscle": 0.8, "body.chubby": 0.9,
           "body.definition.traps_valleys": 0.85}
    snapshot = dict(raw)
    ev(registry, couplings, raw)
    assert raw == snapshot


def test_effective_values_land_inside_record_ranges(registry, couplings):
    """Show-through may push a pinned form past 1.0 internally; the
    final clamp pass must land it back in range WITH a warning."""
    out = ev(registry, couplings, {
        "body.neck.mass": 1.0, "body.chubby": 1.0, "body.muscle": 1.0,
    })
    assert out.sliders["body.neck.mass"] == 1.0
    assert any(w.slider_id == "body.neck.mass" and w.kind == "range"
               for w in out.warnings)


# -- regional tissue ------------------------------------------------------------


def test_regional_tissue_follows_android_ordering(registry, couplings):
    out = ev(registry, couplings, {"body.tissue.level": 0.8})
    d = out.derived
    assert d["tissue.level"] == 0.8
    assert d["tissue.abdomen"] > d["tissue.thigh"] > d["tissue.forearm"]
    assert d["tissue.abdomen"] == pytest.approx(0.8)  # profile weight 1.00
    assert d["tissue.forearm"] == pytest.approx(0.8 * 0.25)
    # Terminal regions (MUSCLE_TISSUE_MODEL.md section 4; v5.1 /
    # GRAVITY_V5.md addendum): small but nonzero by design, below
    # forearm, foot above hand.
    assert d["tissue.forearm"] > d["tissue.foot"] > d["tissue.hand"] > 0.0
    assert d["tissue.foot"] == pytest.approx(0.8 * 0.15)
    assert d["tissue.hand"] == pytest.approx(0.8 * 0.12)


def test_terminal_tissue_follows_macro_distribution(registry, couplings):
    """Hand rides the chest macro (like forearm), foot the thighs
    macro (like calf): at the pear anchor (-1) the chest tissue
    factor is 0.55 and thighs 1.40, so terminal tissue must move
    with its limb, not sit at factor 1.0."""
    out = ev(registry, couplings, {
        "body.tissue.level": 0.8, "body.distribution": -1.0,
    })
    d = out.derived
    assert d["tissue.hand"] == pytest.approx(0.8 * 0.12 * 0.55)
    assert d["tissue.foot"] == pytest.approx(0.8 * 0.15 * 1.40)


def test_explicit_tissue_level_overrides_derived(registry, couplings):
    out = ev(registry, couplings, {
        "body.tissue.level": 0.2, "body.chubby": 1.0,
        "body.tissue.mass_smooth": 1.0, "body.belly.pot": 1.0,
    })
    assert out.derived["tissue.level"] == 0.2


# -- definition attenuation -----------------------------------------------------


def test_attenuation_anchor_bodybuilder_pole(registry, couplings):
    """At regional tissue 0.15 (the <10% body-fat band) the abdomen
    curve is at its 0.98 anchor: near-full definition."""
    out = ev(registry, couplings, {
        "body.tissue.level": 0.15, "body.muscle": 1.0,
        "body.definition.vline": 1.0,
    })
    assert out.derived["tissue.abdomen"] == pytest.approx(0.15)
    assert out.sliders["body.definition.vline"] == pytest.approx(0.98)


def test_attenuation_monotonic_in_tissue(registry, couplings):
    """Raising tissue (via Chubby) never raises effective definition."""
    prev = None
    for chubby in (0.0, 0.25, 0.5, 0.75, 1.0):
        out = ev(registry, couplings, {
            "body.muscle": 0.8, "body.chubby": chubby,
            "body.definition.traps_valleys": 0.85,
            "body.definition.vline": 0.85,
        })
        cur = out.sliders["body.definition.traps_valleys"]
        if prev is not None:
            assert cur <= prev + 1e-12
        prev = cur


def test_abdomen_submerges_faster_than_yoke(registry, couplings):
    """Same raw definition, same tissue: at high tissue the V line
    (abdomen curve) is attenuated far harder than trap valleys (yoke
    curve) — the largest forms read last (gachidebu pattern)."""
    out = ev(registry, couplings, {
        "body.tissue.level": 0.9, "body.muscle": 1.0,
        "body.definition.vline": 1.0, "body.definition.traps_valleys": 1.0,
    })
    assert out.sliders["body.definition.vline"] < 0.35
    assert out.sliders["body.definition.traps_valleys"] > 0.55
    assert (out.sliders["body.definition.traps_valleys"]
            > 1.8 * out.sliders["body.definition.vline"])


def test_muscle_gate_floors_definition_without_muscle(registry, couplings):
    """No muscle under the definition: the gate floor (0.5) applies,
    not zero — lean untrained bodies still show separation."""
    out = ev(registry, couplings, {
        "body.tissue.level": 0.0, "body.definition.vline": 1.0,
    })
    assert out.sliders["body.definition.vline"] == pytest.approx(0.5)


# -- TissueDefinition dial -------------------------------------------------------


def test_dial_interpolates_the_orc_tissue_poles(registry, couplings):
    # Muscle pinned at 1.0 so the muscle gate is fully open and the
    # assertions read the dial's own fill values (attenuation at the
    # bodybuilder pole's near-zero tissue is ~1.0 by the anchors).
    sm = ev(registry, couplings, {"body.definition.dial": 0.0, "body.muscle": 1.0})
    bb = ev(registry, couplings, {"body.definition.dial": 1.0, "body.muscle": 1.0})
    assert sm.sliders["body.chubby"] == pytest.approx(0.65)
    assert sm.sliders["body.tissue.mass_smooth"] == pytest.approx(0.65)
    assert bb.sliders["body.chubby"] == pytest.approx(0.05)
    assert bb.sliders["body.tissue.mass_smooth"] == pytest.approx(0.10)
    assert bb.sliders["body.definition.traps_valleys"] == pytest.approx(0.85)
    assert bb.sliders["body.definition.back"] == pytest.approx(0.95, rel=0.01)


def test_dial_never_overrides_explicit_values(registry, couplings):
    out = ev(registry, couplings, {
        "body.definition.dial": 1.0, "body.definition.traps_valleys": 0.30,
        "body.muscle": 1.0,
    })
    # The dial would fill 0.85; the explicit 0.30 stands (attenuation
    # at zero tissue with full muscle leaves it untouched).
    assert out.sliders["body.definition.traps_valleys"] == pytest.approx(0.30)


# -- PowerBelly -------------------------------------------------------------------


def test_power_belly_core_share_scales_with_muscle(registry, couplings):
    strong = ev(registry, couplings, {"body.muscle": 0.65, "body.belly.pot": 0.65})
    weak = ev(registry, couplings, {"body.muscle": 0.10, "body.belly.pot": 0.65})
    assert strong.derived["power_belly.core_share"] == pytest.approx(0.4225)
    assert weak.derived["power_belly.core_share"] == pytest.approx(0.065)
    assert strong.derived["power_belly.tilt_deg"] == pytest.approx(3.0 * 0.4225)
    assert (strong.derived["power_belly.drape_share"]
            < weak.derived["power_belly.drape_share"])


def test_power_belly_bare_belly_advisory(registry, couplings):
    out = ev(registry, couplings, {"body.muscle": 0.1, "body.belly.pot": 0.9})
    assert any(w.kind == "coupling" and "tissue-only" in w.message
               for w in out.warnings)


# -- mass distribution axis ---------------------------------------------------------


def test_distribution_archetype_anchors(registry, couplings):
    pear = ev(registry, couplings, {"body.distribution": -1.0})
    assert pear.derived["distribution.weight.hips_glutes"] == pytest.approx(1.45)
    assert pear.derived["distribution.weight.chest"] == pytest.approx(0.55)
    hourglass = ev(registry, couplings, {"body.distribution": -0.35})
    assert hourglass.derived["distribution.weight.waist"] == pytest.approx(0.70)
    inv = ev(registry, couplings, {"body.distribution": 1.0})
    assert inv.derived["distribution.weight.chest"] == pytest.approx(1.45)
    assert inv.derived["distribution.weight.hips_glutes"] == pytest.approx(0.60)


def test_distribution_muscle_strength_is_reduced(registry, couplings):
    """Muscle deposition follows the axis at 0.6 strength: a pear's
    muscle factor at the hips is 1 + (1.45 - 1) x 0.6 = 1.27, while
    its tissue factor is the full 1.45."""
    pear = ev(registry, couplings, {"body.distribution": -1.0})
    assert pear.derived["distribution.tissue.hips_glutes"] == pytest.approx(1.45)
    assert pear.derived["distribution.muscle.hips_glutes"] == pytest.approx(1.27)


def test_distribution_moves_regional_tissue(registry, couplings):
    pear = ev(registry, couplings, {
        "body.distribution": -1.0, "body.tissue.level": 0.6})
    big_chest = ev(registry, couplings, {
        "body.distribution": 1.0, "body.tissue.level": 0.6})
    assert pear.derived["tissue.thigh"] > pear.derived["tissue.chest"]
    assert big_chest.derived["tissue.chest"] > big_chest.derived["tissue.thigh"]
    # Pear thigh tissue: 0.6 level x 0.80 profile x 1.40 distribution.
    assert pear.derived["tissue.thigh"] == pytest.approx(0.6 * 0.80 * 1.40)


def test_distribution_moves_definition_via_tissue(registry, couplings):
    """Interaction: distribution x attenuation. Same raw pec crease,
    same tissue level — the pear keeps its chest definition (little
    chest tissue), the big-chest build submerges it (chest tissue
    factor 1.45)."""
    base = {"body.tissue.level": 0.6, "body.muscle": 1.0,
            "body.definition.pecs_crease": 0.8}
    pear = ev(registry, couplings, {**base, "body.distribution": -1.0})
    big_chest = ev(registry, couplings, {**base, "body.distribution": 1.0})
    assert (pear.sliders["body.definition.pecs_crease"]
            > big_chest.sliders["body.definition.pecs_crease"])


# -- worked example: gachimuchi (Sen vs sen_muscle_bear) -----------------------------

SEN_RAW = {
    "body.muscle": 0.65, "body.chubby": 0.80, "body.tissue.mass_smooth": 0.75,
    "body.definition.traps_valleys": 0.30, "body.belly.pot": 0.65,
    "body.torso.mass": 1.0, "body.pecs.size": 1.0,
}
SEN_MUSCLE_BEAR_RAW = {
    "body.muscle": 0.65, "body.chubby": 0.55, "body.tissue.mass_smooth": 0.45,
    "body.definition.traps_valleys": 0.55, "body.definition.back": 0.50,
    "body.belly.pot": 0.50, "body.torso.mass": 1.0, "body.pecs.size": 1.0,
}


def test_gachimuchi_variant_reproduces_sen_muscle_bear_intent(registry, couplings):
    """presets-titan-batch1.md section 4.5: the variant holds Sen's
    MuscleVector EXACTLY and moves only tissue. Numerically: muscle
    effective identical, tissue level lower, and effective trap-valley
    definition much higher — from BOTH the raw raise (0.30 -> 0.55)
    and the attenuation relief of the thinner tissue."""
    sen = ev(registry, couplings, SEN_RAW)
    bear = ev(registry, couplings, SEN_MUSCLE_BEAR_RAW)
    assert bear.sliders["body.muscle"] == sen.sliders["body.muscle"] == 0.65
    assert bear.derived["tissue.level"] < sen.derived["tissue.level"]
    assert sen.derived["tissue.level"] == pytest.approx(0.7575)
    assert bear.derived["tissue.level"] == pytest.approx(0.515)
    sen_valleys = sen.sliders["body.definition.traps_valleys"]
    bear_valleys = bear.sliders["body.definition.traps_valleys"]
    assert bear_valleys > 1.7 * sen_valleys
    # Sen's power belly is mostly core-carried; the variant's less so.
    assert sen.derived["power_belly.core_share"] == pytest.approx(0.4225)
    assert bear.derived["power_belly.core_share"] < sen.derived["power_belly.core_share"]


# -- circumferential wrap (Nov 12, 2026 amendment) -------------------------------


def test_wrap_factor_monotonic_in_tissue(registry, couplings):
    """As front tissue rises, the required side-sector share of the
    ring never falls: the flanks lag at lean levels and catch up as
    the band loads (FAT_REFERENCE R2 ordering, closing to a full
    ring at heavy classes)."""
    prev = None
    for level in (0.1, 0.3, 0.55, 0.8, 0.95):
        out = ev(registry, couplings, {"body.tissue.level": level})
        cur = out.derived["wrap.factor.waist"]
        if prev is not None:
            assert cur >= prev - 1e-12
        prev = cur


def test_wrap_high_tissue_character_gains_flank_proportionally(registry, couplings):
    """A high-tissue character must gain flank tissue in proportion,
    not front-only: at level 0.9 the waist wrap factor is at its
    closed-ring anchor (1.0), the resolved flank/abdomen ratio is the
    profile's 0.65 (well over the 0.40 floor), and no stiff-sides
    advisory fires."""
    out = ev(registry, couplings, {"body.tissue.level": 0.9})
    assert out.derived["wrap.factor.waist"] == pytest.approx(1.0)
    # The factor reads the BAND's front tissue, not the global level:
    # chest tissue is 0.9 x 0.60 profile = 0.54, which interpolates to
    # 0.75 + (0.04 / 0.35) x 0.25 on the factor anchors.
    assert out.derived["wrap.factor.chest"] == pytest.approx(0.7786, abs=1e-3)
    assert out.derived["wrap.ratio.waist"] == pytest.approx(0.65)
    assert not any("stiff sides" in w.message for w in out.warnings)


def test_wrap_stiff_sides_advisory_on_stiff_profile(registry, couplings):
    """The failure the check exists for: a regional profile whose
    flanks barely load while the abdomen saturates. Rebuild the
    coupling registry with a doctored lifter profile (flanks 0.10)
    and the wrap audit must flag stiff sides at real front tissue."""
    import json

    records = []
    for path in sorted(COUPLINGS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["id"] == "muscle_tissue.regional_tissue":
            data["params"]["profiles"]["lifter"]["flanks"] = 0.10
        from core.sliders import CouplingRecord
        records.append(CouplingRecord.from_dict(data, source=str(path)))
    from core.sliders import CouplingRegistry as CR
    stiff = CR(records)
    out = ev(registry, stiff, {"body.tissue.level": 0.8})
    assert out.derived["wrap.ratio.waist"] == pytest.approx(0.10)
    assert any(w.kind == "coupling" and "stiff sides" in w.message
               for w in out.warnings)


def test_wrap_quiet_at_zero_tissue(registry, couplings):
    """No tissue, no ring to audit: the factor sits at its lean
    anchor and no advisory fires."""
    out = ev(registry, couplings, {"body.tissue.level": 0.0})
    assert out.derived["wrap.factor.waist"] == pytest.approx(0.35)
    assert "wrap.ratio.waist" not in out.derived
    assert not any("stiff sides" in w.message for w in out.warnings)


def test_chest_broadness_passes_tissue_stage_untouched(registry, couplings):
    """Frame is authored, like the Muscle vector: broadness is not a
    show-through target and no tissue mechanism rewrites it — at
    full tissue it is bit-identical (the lateral tissue gain is the
    wrap coupling's output, not a boost to the frame value)."""
    for chubby in (0.0, 1.0):
        out = ev(registry, couplings, {
            "body.chest.broadness": 0.7, "body.chubby": chubby,
            "body.distribution": 1.0,
        })
        assert out.sliders["body.chest.broadness"] == 0.7


def test_character_effective_sliders_wrapper(registry, couplings):
    char = Character(name="Sen (worked example)", sliders=dict(SEN_RAW))
    out = char.effective_sliders(registry, couplings)
    assert out.sliders["body.muscle"] == 0.65
    assert out.derived["tissue.level"] == pytest.approx(0.7575)
    # The stored record still holds the RAW vector.
    assert char.sliders["body.definition.traps_valleys"] == 0.30
