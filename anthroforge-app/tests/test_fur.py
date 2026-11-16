"""Fur data: the eight species profiles validate and resolve from a
character record; platform budgets are readable."""

from pathlib import Path

import pytest

from core.errors import FurDataError
from core.fur import FurLibrary

APP = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def fur():
    return FurLibrary(APP / "library" / "fur")


def test_eight_species_profiles(fur):
    assert fur.profile_ids() == [
        "species.badger.coat", "species.bear.coat", "species.clydesdale.coat",
        "species.fennec.coat", "species.lion.coat", "species.red_fox.coat",
        "species.saint_bernard.coat", "species.wolf.coat",
    ]


def test_bear_profile_carries_sen_relevant_values(fur):
    bear = fur.profile("species.bear.coat")
    # Moon-bear ruff is the roster's long pole among the Titan species.
    assert bear["regions"]["ruff"]["length_m"] == pytest.approx(0.150)
    crescent = bear["regions"]["torso.front"]["layer"]["note"]
    assert "crescent" in crescent  # the markings fur-colour override pointer
    fennec = fur.profile("species.fennec.coat")
    assert fennec["regions"]["feet"]["layer"]["note"] == \
        "covers pads — unique on roster"


def test_profile_resolves_from_character_fur_block(fur):
    assert fur.profile_for({"profile": "species.wolf.coat"})["profile"] == \
        "species.wolf.coat"
    assert fur.profile_for({}) is None
    with pytest.raises(FurDataError, match="unknown fur profile"):
        fur.profile_for({"profile": "species.dragon.coat"})


def test_platform_budgets(fur):
    desktop = fur.platform_budget("desktop_glb")
    assert desktop["fur_lod0_tris_max"] == 48000
    mobile = fur.platform_budget("webgl_mobile")
    assert mobile["tiers"]["high"]["whole_character_tris_max"] == 60000
    assert mobile["tiers"]["low"]["fur_lod1_tris_max"] == 12000
    sl = fur.platform_budget("second_life")
    assert sl["fur_attachment_tris"]["Lowest"] == 500  # hand-authored impostor
    zones = fur.budgets["zones_lod0"]["card_subtotal_tris"]
    assert zones == {"desktop": 43600, "webgl": 22400}
    with pytest.raises(FurDataError, match="unknown fur budget platform"):
        fur.platform_budget("holodeck")
