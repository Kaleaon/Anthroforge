"""Geometry layer: .target parsing (units/axes), instance loading,
the gravity-coupled decomposition, GLB writing, and the fold gate.

The navel assertions are grounded in the proof lineage's own QA
(first-proof GRAVITY_V5.md v5.1 addendum): at belly +1 the navel moves
forward 11.14 cm / down 6.99 cm (numpy) — the numbers that pin the
.target unit/axis convention.
"""

from pathlib import Path

import numpy as np
import pytest

from core.bases import BaseRegistry
from core.errors import GeometryError
from core.geometry import count_degenerate_faces, count_flips, load_instance, parse_target, write_glb
from core.sliders import SliderRegistry

APP = Path(__file__).resolve().parent.parent
WS = APP.parent
LIB = APP / "library"


@pytest.fixture(scope="module")
def bases():
    return BaseRegistry(LIB / "bases")


@pytest.fixture(scope="module")
def registry():
    return SliderRegistry.from_folder(LIB / "sliders")


def test_target_units_and_axes_at_the_navel(bases, registry):
    base = bases.load("makehuman_hm08")
    rec = registry.get("body.belly.protrusion")
    fld = load_instance(rec.id, rec.instances["makehuman_hm08"],
                        base.id, base.n_verts, WS)
    disp = fld.at(1.0)[base.navel]
    # stored axes: [width, depth(+forward), height(+up)]
    assert disp[1] == pytest.approx(0.1114, abs=0.004)   # forward 11.14 cm
    assert disp[2] == pytest.approx(-0.0699, abs=0.004)  # down 6.99 cm
    assert abs(disp[0]) < 0.03                           # near the midline


def test_gravity_decomposition_is_not_linear(bases, registry):
    """shape(w) = w*LIN + sign(w)|w|^2 * SAG: at w=0.5 the sag term
    contributes a quarter of its +1 weight, so the field differs from
    a naive 0.5 * combined — by exactly the sag share."""
    base = bases.load("makehuman_hm08")
    rec = registry.get("body.belly.protrusion")
    fld = load_instance(rec.id, rec.instances["makehuman_hm08"],
                        base.id, base.n_verts, WS)
    assert fld.sag is not None and fld.gamma == 2.0
    half = fld.at(0.5)
    naive = 0.5 * fld.at(1.0)
    expect = naive - 0.25 * fld.sag  # 0.5*SAG linear share vs 0.25 actual
    assert np.allclose(half, expect)
    assert not np.allclose(half, naive)


def test_contact_variant_swaps_the_combined_field(bases, registry):
    base = bases.load("makehuman_hm08")
    rec = registry.get("body.belly.protrusion")
    plain = load_instance(rec.id, rec.instances["makehuman_hm08"],
                          base.id, base.n_verts, WS)
    contact = load_instance(rec.id, rec.instances["makehuman_hm08"],
                            base.id, base.n_verts, WS, variant="contact")
    assert not np.allclose(plain.at(1.0), contact.at(1.0))
    assert np.allclose(plain.sag, contact.sag)  # same v3 sag decomposition
    with pytest.raises(GeometryError, match="unknown instance variant"):
        load_instance(rec.id, rec.instances["makehuman_hm08"],
                      base.id, base.n_verts, WS, variant="nope")


def test_parse_target_rejects_bad_index(tmp_path):
    bad = tmp_path / "bad.target"
    bad.write_text("# basemesh hm08\n999999 0.1 0.0 0.0\n")
    with pytest.raises(GeometryError, match="outside"):
        parse_target(bad, 19158)


@pytest.mark.parametrize("delta", ["nan", "inf", "-inf"])
def test_parse_target_rejects_non_finite_deltas(tmp_path, delta):
    target = tmp_path / "non_finite.target"
    target.write_text(f"# basemesh hm08\n5 {delta} 0.0 0.0\n")
    with pytest.raises(GeometryError, match="finite"):
        parse_target(target, 10)


@pytest.mark.parametrize("n_verts", [0, -1, True, 1.5])
def test_parse_target_requires_positive_integer_vertex_count(tmp_path, n_verts):
    target = tmp_path / "empty.target"
    target.write_text("# basemesh hm08\n")
    with pytest.raises(GeometryError, match="positive integer"):
        parse_target(target, n_verts)


def test_instance_field_rejects_mismatched_or_non_finite_fields():
    from core.geometry import InstanceField

    with pytest.raises(GeometryError, match="sag field shape"):
        InstanceField("test.slider", "test.base", np.zeros((3, 3)), np.zeros((2, 3)))
    with pytest.raises(GeometryError, match="linear field contains non-finite"):
        InstanceField("test.slider", "test.base", np.array([[np.nan, 0., 0.]]))


@pytest.mark.parametrize("gamma", [0, -1, float("nan"), float("inf")])
def test_instance_field_rejects_invalid_gamma(gamma):
    from core.geometry import InstanceField

    with pytest.raises(GeometryError, match="gamma"):
        InstanceField("test.slider", "test.base", np.zeros((1, 3)), gamma=gamma)


def test_instance_field_rejects_non_finite_slider_value():
    from core.geometry import InstanceField

    field = InstanceField("test.slider", "test.base", np.zeros((1, 3)))
    with pytest.raises(GeometryError, match="slider value must be finite"):
        field.at(float("nan"))


def test_parse_target_dm_to_stored_axes(tmp_path):
    t = tmp_path / "t.target"
    t.write_text("# basemesh hm08\n5 1.0 2.0 3.0\n")
    field = parse_target(t, 10)
    # file (dx, dy, dz) dm -> stored (dx, dz, dy) * 0.1 m
    assert field[5] == pytest.approx([0.1, 0.3, 0.2])
    assert not field[:5].any() and not field[6:].any()


def test_glb_roundtrip_through_the_gauntlet(tmp_path, bases):
    base = bases.load("makehuman_hm08")
    out = write_glb(tmp_path / "base.glb", base.positions, base.triangles)
    from core.build import run_qa_gauntlet

    qa = run_qa_gauntlet(out)
    assert qa is not None, "qa-gauntlet/validate_glb.py expected on this machine"
    assert qa["parses"] is True
    assert qa["nan_vertices"] == 0
    assert qa["blocked"] is False
    assert qa["max_extent_m"] == pytest.approx(1.695, abs=0.01)


@pytest.mark.parametrize(
    "positions,triangles,message",
    [
        (np.empty((0, 3)), np.array([[0, 1, 2]]), "positions"),
        (np.zeros((3, 2)), np.array([[0, 1, 2]]), "positions"),
        (np.zeros((3, 3)), np.empty((0, 3), dtype=int), "triangles"),
        (np.zeros((3, 3)), np.array([[0, 1, 3]]), "outside"),
        (np.zeros((3, 3)), np.array([[0.0, 1.0, 2.0]]), "integers"),
        (np.array([[0., 0., 0.], [1., 0., 0.], [np.inf, 1., 0.]]),
         np.array([[0, 1, 2]]), "non-finite"),
    ],
)
def test_glb_writer_rejects_invalid_geometry(tmp_path, positions, triangles, message):
    with pytest.raises(GeometryError, match=message):
        write_glb(tmp_path / "invalid.glb", positions, triangles)


def test_fold_gate_counts_a_known_flip():
    # A single triangle wound backwards vs the base = exactly 1 flip.
    pos = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.]])
    tris = np.array([[0, 1, 2]])
    flipped = pos.copy()
    assert count_flips(pos, flipped, tris) == 0
    assert count_flips(pos, pos[[0, 2, 1]], tris[[0]]) == 1



def test_degenerate_face_gate_detects_collapsed_triangles():
    positions = np.array([[0., 0., 0.], [1., 0., 0.], [2., 0., 0.]])
    triangles = np.array([[0, 1, 2]])
    assert count_degenerate_faces(positions, triangles) == 1
    healthy = positions.copy()
    healthy[2] = [0., 1., 0.]
    assert count_degenerate_faces(healthy, triangles) == 0
