"""Unit tests for the shared pure-Python ``anthroforge-v2/body_machinery`` package
and ``.target`` / coupling-validation consolidation across ``anthroforge-v2``.
"""

from __future__ import annotations

import io
import subprocess
import sys
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import numpy as np
import pytest

APP = Path(__file__).resolve().parent.parent
WS = APP.parent
V2 = WS / "anthroforge-v2"
BARA_SCRIPTS = V2 / "bara-proof" / "scripts"
KALEAON_HEAD_SCRIPTS = V2 / "characters" / "kaleaon-head" / "scripts"

for _p in (str(V2), str(BARA_SCRIPTS), str(KALEAON_HEAD_SCRIPTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import body_machinery as bm  # noqa: E402
from core.bases import BaseRegistry  # noqa: E402
from core.geometry import count_flips, face_normals, parse_target, write_target  # noqa: E402


@pytest.fixture(scope="module")
def hm08():
    return BaseRegistry(APP / "library" / "bases").load("makehuman_hm08")


def test_body_machinery_import_has_zero_side_effects():
    """Importing ``body_machinery`` and every submodule performs zero data file
    reads, zero mesh computations, and zero stdout/stderr prints."""
    probe = (
        "import builtins, io, sys\n"
        f"sys.path.insert(0, {str(V2)!r})\n"
        "real_open = builtins.open\n"
        "opened = []\n"
        "def guarded_open(file, *a, **kw):\n"
        "    s = str(file)\n"
        "    if not s.endswith(('.py', '.pyc')):\n"
        "        opened.append(s)\n"
        "    return real_open(file, *a, **kw)\n"
        "builtins.open = guarded_open\n"
        "import body_machinery\n"
        "from body_machinery import axes, labels, loops, osd, repair, transfer\n"
        "assert opened == [], f'unexpected file reads on import: {opened}'\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        check=True,
    )
    assert proc.stdout == ""
    assert proc.stderr == ""

    # Verify numpy-only operation (no scipy required, matching CI & Blender Python).
    no_scipy_probe = (
        "import sys, numpy as np\n"
        f"sys.path.insert(0, {str(V2)!r})\n"
        "sys.modules['scipy'] = None\n"
        "sys.modules['scipy.spatial'] = None\n"
        "import body_machinery as bm\n"
        "P = np.array([[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[1.,1.,0.]])\n"
        "F = np.array([[0,1,2],[1,3,2]])\n"
        "cp, dd = bm.ParamSurface(P, F).closest(np.array([[0.25,0.25,0.5]]), k=4)\n"
        "assert np.allclose(cp[0], [0.25, 0.25, 0.0]) and np.isclose(dd[0], 0.5)\n"
    )
    subprocess.run([sys.executable, "-c", no_scipy_probe], check=True)


def test_torso_params_default_arguments_resolve_cleanly(hm08):
    """``torso_params(pos)`` resolves ``crotch_of`` and ``neck_base`` without
    ``NameError`` and matches explicit ``torso_cylindrical``."""
    pos = hm08.positions[: bm.BODY_END]
    buf = io.StringIO()
    with redirect_stdout(buf):
        h, theta, r, ax, crotch, neck, length = bm.torso_params(pos)
    assert "chest" in buf.getvalue() and "neck base" in buf.getvalue()
    assert -0.25 < crotch < 0.05
    assert 0.40 < neck < 0.75
    assert length == pytest.approx(neck - crotch)
    assert length > 0.50

    # Silent mode produces identical arrays with zero console output.
    buf_silent = io.StringIO()
    with redirect_stdout(buf_silent):
        h2, theta2, r2, ax2, crotch2, neck2, length2 = bm.torso_params(
            pos, verbose=False
        )
    assert buf_silent.getvalue() == ""
    assert np.allclose(h, h2)
    assert np.allclose(theta, theta2)
    assert np.allclose(r, r2)
    assert np.allclose(ax, ax2)
    assert (crotch2, neck2, length2) == pytest.approx((crotch, neck, length))

    # Matches explicit compute_axis + torso_cylindrical convention.
    ctr, axis = bm.compute_axis(pos)
    hc, thc, axc, rc = bm.torso_cylindrical(pos, ctr, axis, crotch, neck)
    assert np.allclose(h, hc)
    assert np.allclose(theta, thc)
    assert np.allclose(ax, axc)
    assert np.allclose(r, rc)

    # Front midline (+y, x == axis_x) maps to theta == 0.
    mid_z = 0.5 * (crotch + neck)
    ax_mid = bm.axis_at(ctr, axis, np.array([mid_z]))[0]
    front_pt = np.array([[ax_mid[0], ax_mid[1] + 0.15, mid_z]])
    _, th_front, _, _ = bm.torso_cylindrical(front_pt, ctr, axis, crotch, neck)
    assert th_front[0] == pytest.approx(0.0, abs=1e-12)


def test_neck_base_log_modes_and_interpolation_helpers(hm08):
    pos = hm08.positions[: bm.BODY_END]
    ctr, axis = bm.compute_axis(pos)
    crotch = bm.crotch_of(pos)

    out_chest = io.StringIO()
    with redirect_stdout(out_chest):
        n1 = bm.neck_base(pos, ctr, axis, crotch, "hm08", log_mode="chest")
    assert "hm08: chest" in out_chest.getvalue()

    out_neck = io.StringIO()
    with redirect_stdout(out_neck):
        n2 = bm.neck_base(pos, ctr, axis, crotch, "hm08", log_mode="neck")
    assert out_neck.getvalue().strip().startswith("hm08: neck base")

    out_none = io.StringIO()
    with redirect_stdout(out_none):
        n3 = bm.neck_base(pos, ctr, axis, crotch, "hm08", log_mode=None)
    assert out_none.getvalue() == ""
    assert n1 == pytest.approx(n2) == pytest.approx(n3)

    with pytest.raises(ValueError, match="unknown neck_base log_mode"):
        bm.neck_base(pos, ctr, axis, crotch, "hm08", log_mode="invalid")

    # sstep, smoothstep, cosfade, axis_at_3d
    xs = np.array([-0.5, 0.0, 0.5, 1.0, 1.5])
    assert np.allclose(bm.sstep(xs, 0.0, 1.0), bm.smoothstep(0.0, 1.0, xs))
    cf = bm.cosfade(0.0, 1.0, xs)
    assert cf[0] == pytest.approx(1.0) and cf[-1] == pytest.approx(0.0)
    assert cf[2] == pytest.approx(0.5)
    p3 = bm.axis_at_3d(ctr, axis, float(ctr[10]))
    assert p3.shape == (3,) and p3[2] == pytest.approx(ctr[10])


def test_hi_diff_warning_discipline_and_osd_helpers(tmp_path):
    blocks = {
        "HIMBO - BodyBig": {
            "indices": np.array([1, 3]),
            "diffs": np.array([[1.0, 2.0, 3.0], [-1.0, 0.0, 0.5]]),
        }
    }
    missed: set[str] = set()
    err = io.StringIO()
    with redirect_stderr(err):
        d_ok = bm.hi_diff(blocks, 5, "Big", warn_missing=True, missed=missed)
        d_miss1 = bm.hi_diff(blocks, 5, "Nope", warn_missing=True, missed=missed)
        d_miss2 = bm.hi_diff(blocks, 5, "Nope", warn_missing=True, missed=missed)
    assert d_ok[1] == pytest.approx([1.0, 2.0, 3.0])
    assert not d_miss1.any() and not d_miss2.any()
    assert missed == {"Nope"}
    # Warning emitted once when tracked via `missed`.
    assert err.getvalue().count("WARNING: hi_diff('Nope')") == 1

    # Silent mode emits no stderr warning.
    err_silent = io.StringIO()
    with redirect_stderr(err_silent):
        d_silent = bm.hi_diff(blocks, 5, "StillNope", warn_missing=False)
    assert not d_silent.any()
    assert err_silent.getvalue() == ""

    comp = bm.compose_osd(
        blocks, 5, {"Big": 2.0, "Missing": 1.0}, scale=0.5, warn_missing=False
    )
    assert comp[1] == pytest.approx([1.0, 2.0, 3.0])

    # extract_base_positions on a synthetic 32-byte f32 vertex stream.
    rng = np.random.default_rng(42)
    n_syn = 120
    rec = np.zeros((n_syn, 8), dtype="<f4")
    rec[:, 0] = rng.uniform(-10.0, 10.0, n_syn)
    rec[:, 1] = rng.uniform(-8.0, 8.0, n_syn)
    rec[:, 2] = np.linspace(0.1, 120.0, n_syn)
    buf = b"\x00\x00" + rec.tobytes() + b"\x00" * 64
    extracted = bm.extract_base_positions(buf, expect_min_verts=100)
    assert extracted is not None and extracted.shape == (n_syn, 3)
    assert np.allclose(extracted, rec[:, :3], atol=1e-5)

    # dense_from_osd with custom loader and isolated tmp_path.
    tmp_osd = tmp_path / "sample.osd"
    D, bname, names = bm.dense_from_osd(
        b"OSD\x00",
        4,
        "Muscle",
        lambda p: {
            "blocks": [
                {
                    "name": "BodyMuscle",
                    "indices": np.array([2]),
                    "diffs": np.array([[0.5, -0.5, 1.0]]),
                }
            ]
        },
        tmp_path=str(tmp_osd),
    )
    assert bname == "BodyMuscle" and names == ["BodyMuscle"]
    assert D[2] == pytest.approx([0.5, -0.5, 1.0])

    # align_macro_base and load_mpfb_base_obj.
    raw = np.array([[0.0, 0.0, 0.0], [2.0, 4.0, 6.0], [9.0, 9.0, 9.0]])
    mac = np.array([[10.0, 20.0, 30.0], [20.0, 40.0, 60.0]])
    aligned = bm.align_macro_base(raw, mac, body_end=2)
    assert np.allclose(aligned[:2], raw[:2])
    assert np.allclose(aligned[2], [9.0, 9.0, 9.0])

    zpath = tmp_path / "mpfb2.zip"
    obj_txt = (
        "v 1.0 2.0 3.0\n"
        "v 4.0 5.0 6.0\n"
        "v 7.0 8.0 9.0\n"
        "v 10.0 11.0 12.0\n"
        "f 1/1 2/2 3/3 4/4\n"
    )
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("mpfb/data/3dobjs/base.obj", obj_txt)
    V, F, Fb = bm.load_mpfb_base_obj(zpath, with_first_tri_faces=True, body_end=3)
    assert V[0] == pytest.approx([0.1, 0.3, 0.2])
    assert F.shape == (1, 3) and len(Fb) == 1
    Vp, polys = bm.load_mpfb_base_obj(zpath, with_poly_faces=True)
    assert np.allclose(Vp, V) and polys == [[0, 1, 2, 3]]


def test_labels_region_weights_w3_and_limb_extraction(hm08):
    pos = hm08.positions
    tris = hm08.triangles
    body_mask = np.arange(len(pos)) < bm.BODY_END
    h, _th, r, _ax, crotch, neck, _L = bm.torso_params(
        pos[: bm.BODY_END], verbose=False
    )
    h_full, _, r_full, _, _, _, _ = bm.torso_params(
        pos, crotch, neck, verbose=False
    )
    lab = bm.label_mesh(pos, crotch, neck, body_mask=body_mask)
    assert set(lab["lm"].keys()) == {"armR", "armL", "legR", "legL"}

    for kind in ("arm", "leg"):
        for sname in ("R", "L"):
            ch = bm.chain_of(lab, kind, sname)
            assert ch is not None
            segs, ref, _lm = ch
            t, phi, rdir, ah, seg_len, rl = bm.seg_params(
                pos[:100], segs[0][0], segs[0][1], ref
            )
            assert seg_len > 0.1
            assert t.shape == phi.shape == rl.shape == (100,)
            assert rdir.shape == (100, 3) and ah.shape == (3,)

    w_torso = bm.sstep(h_full, -0.05, 0.05) * (1.0 - bm.sstep(h_full, 1.0, 1.1))
    w_torso[~body_mask] = 0.0
    W3, edges = bm.region_weights_w3(
        pos, lab, h_full, r_full, w_torso, tris, body_end=bm.BODY_END, verbose=False
    )
    assert W3.shape == (len(pos), 3)
    sup = W3.sum(axis=1) > 0
    assert sup[: bm.BODY_END].sum() > 10000
    assert np.allclose(W3[sup].sum(axis=1), 1.0, atol=1e-6)

    torso_f = np.ones((len(pos), 3))
    limb_f = {
        ("arm", "R"): np.ones((len(pos), 3)),
        ("leg", "R"): np.ones((len(pos), 3)),
    }
    blended = bm.blend_regions(torso_f, limb_f, W3)
    assert blended.shape == (len(pos), 3)
    assert np.isfinite(blended).all()

    limbs = bm.extract_limbs(pos[: bm.BODY_END], verbose=False)
    assert set(limbs.keys()) == {"arm_R", "arm_L", "leg_R", "leg_L"}
    s, dist, phi, er, adir = bm.limb_params(pos[:200], limbs["arm_R"])
    assert s.shape == dist.shape == phi.shape == (200,)
    assert er.shape == adir.shape == (200, 3)


def test_transfer_and_param_surface_helpers():
    rng = np.random.default_rng(7)
    sa = rng.uniform(0.0, 1.0, 60)
    sb = rng.uniform(-1.0, 1.0, 60)
    v1 = 0.02 * np.sin(sa * np.pi)
    v2 = 0.01 * np.cos(sb * np.pi)
    o1, o2 = bm.pair_field(sa, sb, v1, v2, sa[:10], sb[:10], 0.08, 0.12)
    assert np.allclose(o1, v1[:10], atol=5e-3)
    assert np.allclose(o2, v2[:10], atol=5e-3)

    cv = bm.pair_cv(sa, sb, v1, v2, 0.08, 0.12)
    assert cv is not None and cv["n"] >= 40 and cv["median_cm"] < 0.2

    tris = bm.tri_list([[0, 1, 2, 3], [0, 2, 4]])
    assert tris.shape == (3, 3)

    P = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0],
        ]
    )
    F = np.array([[0, 1, 2], [1, 3, 2]])
    surf = bm.ParamSurface(P, F)
    Q = np.array([[0.25, 0.25, 0.5], [2.0, 0.5, 0.0]])
    cp, dd = surf.closest(Q, k=4)
    assert cp[0] == pytest.approx([0.25, 0.25, 0.0])
    assert dd[0] == pytest.approx(0.5)
    assert cp[1] == pytest.approx([1.0, 0.5, 0.0])
    assert dd[1] == pytest.approx(1.0)


def test_repair_slope_limit_and_quantise_helpers():
    # Simple planar 2-triangle mesh where pushing vertex 0 across edge 1-2 flips face 0.
    pos = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.1, 0.0, 0.0],
            [0.0, 0.1, 0.0],
            [0.1, 0.1, 0.0],
        ]
    )
    faces = np.array([[0, 1, 2], [1, 3, 2]])
    edges = bm.body_edges(faces)
    assert edges.shape == (5, 2)
    assert set(bm.neighbours_of(np.array([0]), edges).tolist()) == {0, 1, 2}

    bad_delta = np.array([[0.12, 0.12, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
    nf_strict, min_dot = bm.fold_stats(pos, faces, bad_delta, flip_tol=0.0)
    nf_tol, _ = bm.fold_stats(pos, faces, bad_delta, flip_tol=-1e-12)
    assert nf_strict == 1 and nf_tol == 1 and min_dot < -0.9
    cos, ok = bm.cos_fold_stats(pos, bad_delta, faces)
    assert ok.all() and cos[0] == pytest.approx(-1.0)

    rep, att, traj = bm.repair(
        bad_delta,
        [(pos, np.zeros_like(pos))],
        "unit",
        faces=faces,
        edges=edges,
        ref_pos=pos,
        kappa=10.0,
        verbose=False,
    )
    assert bm.fold_stats(pos, faces, rep, flip_tol=-1e-12)[0] == 0
    assert att[0] < 1.0 and traj[0] > 0

    inc_rep, _, _ = bm.repair_inc(
        np.zeros_like(pos),
        bad_delta,
        "unit_inc",
        bases=[(pos, "base")],
        faces=faces,
        edges=edges,
        ref_pos=pos,
        kappa=10.0,
        verbose=False,
    )
    assert bm.fold_stats(pos, faces, inc_rep, flip_tol=-1e-12)[0] == 0

    supp = np.array([True, True, True, False])
    Ds_in = np.array([[0.2, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.05, 0.0, 0.0]])
    Ds_lim, iters = bm.slope_limit_iter(Ds_in, edges, pos, kappa=0.55, supp_mask=supp)
    assert iters > 0
    assert np.allclose(Ds_lim[3], 0.0)

    q = bm.quantise(np.array([[0.01234, 0.05678, -0.09123]]))
    dq = bm.dequantise(q)
    assert dq[0] == pytest.approx([0.0123, 0.0568, -0.0912])


def test_loops_volume_girths_and_grade(hm08):
    # Closed unit cube [0, 1]^3: volume = 1.0 m^3, horizontal slice perimeter = 4.0 m.
    cube_v = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 1.0],
            [1.0, 1.0, 1.0],
            [0.0, 1.0, 1.0],
        ]
    )
    cube_f = np.array(
        [
            [0, 2, 1], [0, 3, 2],
            [4, 5, 6], [4, 6, 7],
            [0, 1, 5], [0, 5, 4],
            [2, 3, 7], [2, 7, 6],
            [1, 2, 6], [1, 6, 5],
            [3, 0, 4], [3, 4, 7],
        ]
    )
    assert bm.mesh_volume(cube_v, cube_f) == pytest.approx(1.0)
    loops = bm.plane_loops(cube_v, cube_f, np.array([0.0, 0.0, 1.0]), np.array([0.0, 0.0, 0.5]))
    assert len(loops) == 1
    assert bm.loop_perim(loops[0]) == pytest.approx(4.0)
    assert bm.girth_ellipse(2.0, 2.0) == pytest.approx(2.0 * np.pi, rel=1e-4)
    assert bm.band(1.2, 1.0, 1.5) == "PASS"
    assert bm.band(1.8, 1.0, 1.5) == "miss"

    # Real hm08 scorecard via pure `grade` and `girths`.
    pos = hm08.positions
    faces_b = hm08.triangles[hm08.body_face_mask]
    h_mh, th_mh, _r, _ax, crotch, neck, L_mh = bm.torso_params(
        pos[: bm.BODY_END], verbose=False
    )
    h_full, th_full, _, _, _, _, _ = bm.torso_params(pos, crotch, neck, verbose=False)
    lab = bm.label_mesh(
        pos, crotch, neck, body_mask=np.arange(len(pos)) < bm.BODY_END
    )
    g_no_hip = bm.girths(pos, crotch, neck, 0.35, include_hip=False)
    g_hip = bm.girths(pos, crotch, neck, 0.35, include_hip=True)
    assert "hip" not in g_no_hip and "hip" in g_hip
    assert g_no_hip["chest"] > 0.7

    sm = bm.side_mass(np.ones_like(pos) * 0.01, h_full, th_full)
    assert "chest" in sm and "belly" in sm

    sr = bm.slice_ratio(pos, faces_b, crotch, L_mh, float(pos[hm08.navel, 2]))
    assert 1.0 < sr < 1.8

    score = bm.grade(
        pos,
        lab,
        faces_b=faces_b,
        mh_crotch=crotch,
        mh_neck=neck,
        mh_pos_mac=pos,
        navel_mh=hm08.navel,
        h_mh=h_full,
    )
    assert score["height_m"] == pytest.approx(1.69, abs=0.05)
    assert score["M4_chest_waist"] == pytest.approx(sr)


def test_coupling_validation_module_import_is_pure():
    """Importing ``build_coupling_validation`` does not run the build pipeline
    and exposes ``load_coupling_validation_context``."""
    out = io.StringIO()
    with redirect_stdout(out):
        import build_coupling_validation as bcv
    assert out.getvalue() == ""
    assert callable(bcv.load_coupling_validation_context)


def test_kaleaon_io_consolidates_dihedral_fold_stats():
    """``kaleaon_io.fold_stats`` computes both unsplit diagnostic and cage-split
    dihedral fold statistics without requiring ``bpy``."""
    import kaleaon_io

    class _FakePoly:
        def __init__(self, vertices):
            self.vertices = vertices

    class _FakeVerts:
        def __init__(self, coords: np.ndarray):
            self._coords = np.asarray(coords, dtype=np.float64)

        def __len__(self):
            return len(self._coords)

        def foreach_get(self, attr: str, out: np.ndarray):
            assert attr == "co"
            out[:] = self._coords.ravel()

    class _FakeMesh:
        def __init__(self, coords: np.ndarray, polys: list[list[int]]):
            self.vertices = _FakeVerts(coords)
            self.polygons = [_FakePoly(p) for p in polys]

    class _FakeObj:
        def __init__(self, coords: np.ndarray, polys: list[list[int]]):
            self.matrix_world = np.eye(4)
            self.data = _FakeMesh(coords, polys)

    # Two planar adjacent quads sharing edge (1, 2): dihedral dot == +1.0 -> 0 flips.
    pos = np.array(
        [
            [-1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [-1.0, 1.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
        ]
    )
    quads = [[0, 1, 2, 3], [1, 4, 5, 2]]
    fs_ok = kaleaon_io.fold_stats(_FakeObj(pos, quads))
    assert fs_ok["n_below_0"] == 0
    assert fs_ok["min_dot"] == pytest.approx(1.0)

    # Fold the right quad sharply back over the left quad -> interior edge dot < -0.5.
    folded = pos.copy()
    folded[4] = [-0.8, 0.0, 0.05]
    folded[5] = [-0.8, 1.0, 0.05]
    fs_fold = kaleaon_io.fold_stats(_FakeObj(folded, quads))
    assert fs_fold["n_below_0"] >= 1
    assert fs_fold["min_dot"] < -0.5

    # Cage-split mode (stage3_basefold / stage3_tissue convention).
    fs_ext = kaleaon_io.fold_stats(
        _FakeObj(folded, quads), cage_idx=[], include_worst=True
    )
    assert fs_ext["exterior_below_0.01"] >= 1
    assert fs_ext["cage_pairs"] == 0
    assert len(fs_ext["exterior_worst"]) >= 1

    fs_caged = kaleaon_io.fold_stats(
        _FakeObj(folded, quads), cage_idx=[1, 4, 5, 2], include_worst=True
    )
    assert fs_caged["cage_below_0.01"] >= 1


def test_shipped_v2_targets_parse_and_roundtrip_via_core_geometry(tmp_path):
    """Representative shipped ``.target`` files across ``bara-proof``,
    ``first-proof``, ``masculine-base``, ``hyper``, and ``characters`` parse
    via ``core.geometry.parse_target`` and round-trip cleanly via
    ``core.geometry.write_target``."""
    candidates = [
        V2 / "bara-proof" / "body.muscle.target",
        V2 / "first-proof" / "body.belly.protrusion.target",
        V2 / "masculine-base" / "body.belly.protrusion.target",
        V2 / "hyper" / "body.belly.protrusion.hyper2.target",
        V2 / "characters" / "brand" / "targets" / "body.muscle.target",
        V2 / "characters" / "jorge" / "targets" / "body.jorge.target",
        V2 / "characters" / "pyn" / "targets" / "body.pyn.target",
        V2 / "characters" / "sen" / "targets" / "body.muscle.target",
    ]
    existing = [p for p in candidates if p.is_file()]
    assert len(existing) == len(candidates)
    for idx, src in enumerate(existing):
        field = parse_target(src, bm.HM08_N_VERTS)
        assert field.shape == (bm.HM08_N_VERTS, 3)
        dst = tmp_path / f"{idx}_{src.name}"
        n_written = write_target(dst, field, f"roundtrip {src.name}")
        assert n_written > 0
        reparsed = parse_target(dst, bm.HM08_N_VERTS)
        assert np.allclose(reparsed, field, atol=1e-4)

    # Also verify core.geometry.face_normals + count_flips work cleanly.
    tri_pos = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    tris = np.array([[0, 1, 2]])
    assert face_normals(tri_pos, tris)[0] == pytest.approx([0.0, 0.0, 1.0])
    assert count_flips(tri_pos, tri_pos, tris) == 0


def test_region_weights_w3_and_grade_match_committed_bara_proof_artifacts():
    """Verify bit/float64 parity of ``region_weights_w3`` and ``grade`` against
    committed ``bara_fields.npz`` and ``qa_numbers_bara.json`` artifacts."""
    import json

    mh_pos = np.load(V2 / "hyper" / "work" / "proof_states.npz")["base"].astype(
        np.float64
    )
    mac = np.load(V2 / "first-proof" / "work" / "mh_macro_base.npz")["pos_canonical_m"]
    mh_pos_mac = bm.align_macro_base(mh_pos, mac, body_end=bm.BODY_END)

    corr = np.load(V2 / "first-proof" / "work" / "correspondence.npz")
    mh_crotch, mh_neck = [float(x) for x in corr["mh_landmarks"]]
    navel_mh = int(corr["navel_mh"])
    mh_tris = corr["mh_tris"]
    faces_b = mh_tris[np.all(mh_tris < bm.BODY_END, axis=1)]
    w_torso_v4 = np.load(V2 / "first-proof" / "work" / "belly_v4.npz")[
        "torso_weight"
    ].astype(np.float64)

    body_mask = np.zeros(len(mh_pos), bool)
    body_mask[: bm.BODY_END] = True
    mh_lab = bm.label_mesh(mh_pos_mac, mh_crotch, mh_neck, body_mask)
    h_mh, _, r_mh, _, _, _, _ = bm.torso_params(
        mh_pos_mac, mh_crotch, mh_neck, "hm08", verbose=False
    )

    W3, _ = bm.region_weights_w3(
        mh_pos_mac,
        mh_lab,
        h_mh,
        r_mh,
        w_torso_v4,
        mh_tris,
        body_end=bm.BODY_END,
        verbose=False,
    )
    bf = np.load(V2 / "bara-proof" / "work" / "bara_fields.npz")
    assert np.allclose(W3, bf["region_weights"], atol=1e-12)

    score_base = bm.grade(
        mh_pos_mac,
        mh_lab,
        faces_b=faces_b,
        mh_crotch=mh_crotch,
        mh_neck=mh_neck,
        mh_pos_mac=mh_pos_mac,
        navel_mh=navel_mh,
        h_mh=h_mh,
        body_end=bm.BODY_END,
    )
    qa_bara = json.loads(
        (V2 / "bara-proof" / "work" / "qa_numbers_bara.json").read_text(
            encoding="utf-8"
        )
    )
    for key, ref_val in qa_bara["grades"]["base"].items():
        if isinstance(ref_val, (int, float)) and key in score_base:
            assert score_base[key] == pytest.approx(ref_val, abs=1e-9)

