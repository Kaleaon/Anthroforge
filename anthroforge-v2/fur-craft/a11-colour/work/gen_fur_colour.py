#!/usr/bin/env python3
"""
AnthroForge A11 — fur colour patterning prototype.

Implements the two-level fur colour model (see ../FUR_COLOUR.md):

  HAIR LEVEL  — a parametric banded-shaft profile. Bands are (centre,
  width, pigment) along hair parameter t (0 = root, 1 = tip). The
  pheomelanin band widths are driven by one biological knob, the ASIP
  "pulse width": ASIP pulses during growth switch the melanocyte from
  eumelanin to pheomelanin; a longer pulse = a wider light band.
  CORIN suppresses ASIP (wider band = "wideband"/golden); stripe-zone
  follicles run pulse ~ 0 (melanic hairs).

  COAT LEVEL  — a markings mask (MARKINGS.md generators) becomes a
  melanism field m in [0,1]; each follicle's profile is the ground
  profile with its pheomelanin bands shrunk by (1-m). Tabby/tiger
  stripes are therefore NOT a second texture: they are the same shaft
  program with the pulse turned down, which is what the biology does
  (stripe hairs are uniformly eumelanin; ground hairs are banded).

Outputs (../textures, ../renders):
  shaft profiles JSON (character-record format), shaft atlas image,
  card textures recoloured from the fur-prototype's baked strand alpha
  (real strand layout, our colour), an undercoat card set, shell alpha
  erosion levels, coat-level diffuse for wolf + tabby (the markings
  mask driving fur colour directly), and a PIL contact sheet incl. the
  distance-read test (optical mixing of the cards).

Deps: PIL + numpy. Textures follow the fur-prototype card convention:
512x1024 RGBA, image row 0 = hair ROOT, row H-1 = hair TIP.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEX = os.path.join(ROOT, "textures")
REN = os.path.join(ROOT, "renders")
SRC_ALPHA = os.path.expanduser(
    "~/workspace/anthroforge-v2/fur-prototype/fur_card_texture_a.png")
SRC_ALPHA_B = os.path.expanduser(
    "~/workspace/anthroforge-v2/fur-prototype/fur_card_texture_b.png")
MARKINGS = os.path.expanduser("~/workspace/anthroforge-v2/markings-lab")
os.makedirs(TEX, exist_ok=True)
os.makedirs(REN, exist_ok=True)

# ---------------------------------------------------------------- pigments

def hx(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

# A band: centre/width in t, colour, and whether ASIP pulse width scales it.
# Eumelanin bands are the "default state"; pheomelanin bands are the pulse.
def profile_from_bands(bands, melanism=0.0, n=1024):
    """Sample a shaft profile to an (n,3) float array, t = 0..1 root->tip.

    Pheomelanin bands shrink toward their centre as melanism rises
    (pulse width -> 0); eumelanin absorbs the freed length because the
    profile is evaluated as nearest-band-centre in a warped t space:
    we build the profile by painting bands in order over an eumelanin
    ground, with soft edges, so shrinking a pheo band exposes eumelanin.
    """
    t = np.linspace(0, 1, n)
    # ground = the eumelanin "base" colour (first band marked ground)
    ground = hx(next(b["colour"] for b in bands if b.get("ground")))
    prof = np.tile(np.array(ground), (n, 1))
    for b in bands:
        if b.get("ground"):
            continue
        w = b["width"] * ((1.0 - melanism) ** 1.35 if b.get("pulse") else 1.0)
        if w <= 0.004:
            continue
        d = np.abs(t - b["centre"]) / (w / 2.0)
        soft = b.get("soft", 0.35)
        a = np.clip((1.0 - d) / soft + 0.5, 0, 1) if soft > 0 else (d < 1).astype(float)
        c = np.array(hx(b["colour"]))
        prof = prof * (1 - a[:, None]) + c * a[:, None]
    return prof

def integral_colour(prof):
    """Length-weighted mean = the colour the coat reads at distance,
    and the correct tint for LOD3 / texture-only floors."""
    return prof.mean(axis=0)

# ---------------------------------------------------------------- profiles
# Wolf guard hair (dorsal): dark base, tan pheo band, pale cream band,
# black tip — the classic multi-band agouti that reads grizzled.
WOLF_GUARD = [
    {"centre": 0.0, "width": 0.30, "colour": "#38312b", "ground": True},
    {"centre": 0.34, "width": 0.26, "colour": "#a97e4f", "pulse": True},
    {"centre": 0.60, "width": 0.24, "colour": "#d9c49a", "pulse": True},
    {"centre": 0.90, "width": 0.30, "colour": "#201c19"},
]
# Wolf undercoat: woolly, near-solid pale warm grey, darker root third.
WOLF_UNDER = [
    {"centre": 0.0, "width": 0.4, "colour": "#6f6455", "ground": True},
    {"centre": 0.62, "width": 0.9, "colour": "#a3967f"},
]
# Wolf ventral hair: ventral promoter => solid pheomelanin, NO banding.
WOLF_VENTRAL = [
    {"centre": 0.0, "width": 0.3, "colour": "#8a6f4d", "ground": True},
    {"centre": 0.6, "width": 0.95, "colour": "#c8ab7d"},
]
# Tabby ground hair (brown tabby): several fine bands = visible ticking.
TABBY_GROUND = [
    {"centre": 0.0, "width": 0.26, "colour": "#453729", "ground": True},
    {"centre": 0.30, "width": 0.22, "colour": "#b0824a", "pulse": True},
    {"centre": 0.50, "width": 0.10, "colour": "#4c3b2a"},
    {"centre": 0.66, "width": 0.20, "colour": "#c09a5c", "pulse": True},
    {"centre": 0.90, "width": 0.26, "colour": "#231b13"},
]
# Tiger ground hair (cross-check species): dark base AND tip, single
# sub-apical pheomelanin band (Xu et al. 2017) — derived from TABBY by
# construction in the doc; kept here as a third profile family.
TIGER_GROUND = [
    {"centre": 0.0, "width": 0.34, "colour": "#3d2c1c", "ground": True},
    {"centre": 0.62, "width": 0.30, "colour": "#c07f36", "pulse": True},
    {"centre": 0.93, "width": 0.26, "colour": "#191008"},
]

PROFILES = {
    "wolf.guard.dorsal":   (WOLF_GUARD, 0.0),
    "wolf.undercoat":      (WOLF_UNDER, 0.0),
    "wolf.ventral":        (WOLF_VENTRAL, 0.0),
    "tabby.ground":        (TABBY_GROUND, 0.0),
    "tabby.stripe":        (TABBY_GROUND, 0.97),   # same program, pulse ~ 0
    "tiger.ground":        (TIGER_GROUND, 0.0),
    "tiger.stripe":        (TIGER_GROUND, 0.97),
}

# ---------------------------------------------------------------- helpers

def smooth_noise_1d(n, scale, rng):
    """Low-frequency 1D noise in [0,1] via upsampled random control points."""
    k = max(2, int(n / scale))
    pts = rng.random(k + 2)
    x = np.linspace(0, k + 1, n)
    return np.interp(x, np.arange(k + 2), pts)

def load_alpha(path):
    im = Image.open(path).convert("RGBA")
    return np.asarray(im).astype(np.float32) / 255.0

def bake_card(alpha_rgba, prof_fn, out_path, seed=7, phase_amp=0.14):
    """Recolour a baked strand-alpha card through a shaft profile.

    prof_fn(t, x_frac) -> (H,W,3) float colour. Two-octave per-column
    phase jitter: neighbouring follicles are NOT band-synchronised
    (hairs sit at different growth phases and lengths), so band edges
    must break up at strand scale — a clean strata card reads as a
    flag, not fur. Coarse octave keeps loose neighbourhood coherence,
    fine octave decorrelates strand-to-strand.
    """
    H, W = alpha_rgba.shape[:2]
    rng = np.random.default_rng(seed)
    alpha = alpha_rgba[..., 3]
    t = np.linspace(0, 1, H)[:, None] * np.ones((1, W))
    jitter = ((smooth_noise_1d(W, 44, rng) - 0.5) * 0.45
              + (smooth_noise_1d(W, 5, rng) - 0.5) * 1.55) * phase_amp
    tt = np.clip(t + jitter[None, :], 0, 1)
    xf = np.linspace(0, 1, W)[None, :] * np.ones((H, 1))
    col = prof_fn(tt, xf)
    val = 0.88 + 0.24 * smooth_noise_1d(W, 9, rng)[None, :, None]
    grain = 0.96 + 0.08 * rng.random((H, W, 1)).astype(np.float32)
    col = np.clip(col * val * grain, 0, 1)
    out = np.zeros((H, W, 4), dtype=np.float32)
    out[..., :3] = col
    out[..., 3] = alpha
    Image.fromarray((out * 255).astype(np.uint8), "RGBA").save(out_path)
    return out

def prof_sampler(bands, melanism=0.0, n=1024):
    prof = profile_from_bands(bands, melanism, n)
    def sample(tt, xf=None):
        idx = np.clip((tt * (n - 1)).astype(int), 0, n - 1)
        return prof[idx]
    return sample, prof

# ---------------------------------------------------------------- cards

def main():
    rng = np.random.default_rng(11)
    alpha_a = load_alpha(SRC_ALPHA)
    alpha_b = load_alpha(SRC_ALPHA_B)

    # --- wolf agouti guard cards (dense + sparse, matching prototype A/B)
    s_wolf, prof_wolf = prof_sampler(WOLF_GUARD)
    bake_card(alpha_a, s_wolf, os.path.join(TEX, "card_wolf_agouti_a.png"), seed=7)
    bake_card(alpha_b, s_wolf, os.path.join(TEX, "card_wolf_agouti_b.png"), seed=8)

    # --- tabby: pure ground card + stripe-boundary card.
    # The boundary card is a follicle-zone patch: melanism field m(x)
    # sweeps 0 -> 1 across the card width, so hairs grade from banded
    # ground hairs to melanic stripe hairs exactly as they do across a
    # real stripe edge (pulse width narrows, dark bands merge).
    s_ground, prof_ground = prof_sampler(TABBY_GROUND, 0.0)
    bake_card(alpha_a, s_ground, os.path.join(TEX, "card_tabby_ground.png"), seed=9)

    n = 1024
    K = 33
    ms = np.linspace(0, 0.97, K)
    LUT = np.stack([profile_from_bands(TABBY_GROUND, float(mm), n)
                    for mm in ms]).astype(np.float32)   # (K, n, 3)
    def boundary_fn(tt, xf):
        m = np.clip((xf - 0.30) / 0.40, 0, 1)          # stripe edge sweep
        m = m * m * (3 - 2 * m) * 0.97
        pos = m / 0.97 * (K - 1)
        i0 = np.clip(np.floor(pos).astype(int), 0, K - 2)
        fi = (pos - i0)[..., None]
        tf = tt * (n - 1)
        j0 = np.clip(np.floor(tf).astype(int), 0, n - 2)
        fj = (tf - j0)[..., None]
        return (LUT[i0, j0] * (1 - fi) * (1 - fj) + LUT[i0 + 1, j0] * fi * (1 - fj)
                + LUT[i0, j0 + 1] * (1 - fi) * fj + LUT[i0 + 1, j0 + 1] * fi * fj)
    bake_card(alpha_a, boundary_fn, os.path.join(TEX, "card_tabby_boundary.png"), seed=10)

    # --- undercoat card: own strand alpha (short, dense, wavy, woolly)
    H, W = 512, 512
    uc = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(uc)
    for _ in range(1500):
        x0 = rng.uniform(-10, W)
        ln = rng.uniform(0.35, 0.62) * H
        amp = rng.uniform(2, 7)
        ph = rng.uniform(0, 6.28)
        pts = [(x0 + amp * math.sin(ph + y / ln * 5.0), y)
               for y in np.linspace(0, ln, 14)]
        dr.line(pts, fill=int(rng.uniform(90, 200)), width=2)
    uc = uc.filter(ImageFilter.GaussianBlur(0.7))
    uc_a = np.asarray(uc).astype(np.float32) / 255.0
    alpha_uc = np.zeros((H, W, 4), dtype=np.float32)
    alpha_uc[..., 3] = uc_a
    s_under, prof_under = prof_sampler(WOLF_UNDER)
    bake_card(alpha_uc, s_under, os.path.join(TEX, "card_wolf_undercoat.png"),
              seed=12, phase_amp=0.10)

    # --- shell alpha erosion levels (tileable; shells threshold by level)
    S = 512
    base = Image.new("L", (S, S), 0)
    dr = ImageDraw.Draw(base)
    for _ in range(2600):
        x, y = rng.uniform(0, S, 2)
        ln = rng.uniform(18, 60)
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                dr.line([(x + dx, y + dy), (x + dx + rng.uniform(-3, 3), y + dy + ln)],
                        fill=int(rng.uniform(120, 255)), width=1)
    base_a = np.asarray(base).astype(np.float32) / 255.0
    for lvl, keep in enumerate((0.95, 0.75, 0.5, 0.28)):
        a = np.clip((base_a - (1 - keep)) / max(keep, 1e-6), 0, 1)
        Image.fromarray((a * 255).astype(np.uint8), "L").save(
            os.path.join(TEX, f"shell_alpha_l{lvl}.png"))

    # --- coat-level diffuse (shell tint + texture-only floor).
    # Wolf dorsal: integral (distance) colour of the guard profile over
    # undercoat show-through speckle. Tabby: the MARKINGS stripes mask
    # selects ground vs stripe integral colours — the mask driving the
    # fur colour function directly, per MARKINGS.md section 1.1.
    sys.path.insert(0, MARKINGS)
    from generate_markings import gen_stripes  # noqa: E402

    def speckle(shape, rng, amp=0.10):
        n1 = rng.random(shape)
        n2 = np.asarray(Image.fromarray((n1 * 255).astype(np.uint8))
                        .filter(ImageFilter.GaussianBlur(1.2))).astype(float) / 255.0
        return 1.0 - amp / 2 + amp * n2

    C = 512
    int_wolf = integral_colour(prof_wolf)
    int_under = integral_colour(prof_under)
    sp = speckle((C, C), rng)
    show = (rng.random((C, C)) > 0.72).astype(float)  # undercoat peeks
    show = np.asarray(Image.fromarray((show * 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(2))).astype(float) / 255.0
    wolf_coat = (int_wolf[None, None, :] * (1 - show[..., None] * 0.55)
                 + int_under[None, None, :] * (show[..., None] * 0.55))
    wolf_coat = np.clip(wolf_coat * sp[..., None], 0, 1)
    Image.fromarray((wolf_coat * 255).astype(np.uint8), "RGB").save(
        os.path.join(TEX, "coat_wolf_dorsal.png"))

    mask = gen_stripes({"seed": 4177, "count": 30, "width_px": 11,
                        "branch_prob": 0.35, "softness": 0.3}, size=C)
    m = np.asarray(mask).astype(float) / 255.0
    _, prof_stripe = prof_sampler(TABBY_GROUND, 0.97)
    int_ground = integral_colour(prof_ground)
    int_stripe = integral_colour(prof_stripe)
    tabby_coat = (int_ground[None, None, :] * (1 - m[..., None])
                  + int_stripe[None, None, :] * m[..., None])
    tabby_coat = np.clip(tabby_coat * sp[..., None], 0, 1)
    Image.fromarray((tabby_coat * 255).astype(np.uint8), "RGB").save(
        os.path.join(TEX, "coat_tabby.png"))
    mask.save(os.path.join(TEX, "coatmask_tabby_stripes.png"))

    # --- shaft atlas image: one row per profile, t along x (root left)
    rows = []
    labels = []
    for name, (bands, mel) in PROFILES.items():
        p = profile_from_bands(bands, mel, 1024)
        rows.append(p)
        labels.append(name)
    atlas = np.zeros((len(rows) * 48, 1024, 3))
    for i, p in enumerate(rows):
        atlas[i * 48:(i + 1) * 48] = p[None, :, :]
    Image.fromarray((atlas * 255).astype(np.uint8), "RGB").save(
        os.path.join(TEX, "shaft_atlas.png"))

    # --- profiles JSON in character-record shape + measurements
    def bands_json(bands, melanism):
        return {"pattern": "agouti" if any(b.get("pulse") for b in bands) else "solid",
                "melanism": melanism,
                "bands": [{k: b[k] for k in ("centre", "width", "colour")
                           } | ({"pulse": True} if b.get("pulse") else {})
                          | ({"ground": True} if b.get("ground") else {})
                          for b in bands]}
    out = {"format": "anthroforge.fur_colour v2 (extends APP_BLUEPRINT 9.5)",
           "convention": "t: 0 = root, 1 = tip; card textures: row 0 = root",
           "profiles": {}}
    for name, (bands, mel) in PROFILES.items():
        p = profile_from_bands(bands, mel)
        ic = integral_colour(p)
        out["profiles"][name] = bands_json(bands, mel) | {
            "distance_colour": "#" + "".join(f"{int(round(c * 255)):02x}" for c in ic),
            "pheo_fraction": round(float(np.mean(
                [profile_from_bands(bands, 0.0)[i] for i in range(1024)])), 4)
                if False else None}
    # pheomelanin fraction = share of shaft length whose nearest band is a
    # pulse band at melanism 0 (report measured value instead of the stub)
    for name, (bands, mel) in PROFILES.items():
        t = np.linspace(0, 1, 1024)
        pulse = np.zeros(1024, bool)
        for b in bands:
            if b.get("pulse"):
                w = b["width"] * (1 - mel) ** 1.35
                pulse |= np.abs(t - b["centre"]) < w / 2
        out["profiles"][name]["pheo_fraction"] = round(float(pulse.mean()), 3)
    with open(os.path.join(TEX, "fur_colour_profiles.json"), "w") as f:
        json.dump(out, f, indent=2)

    for name in PROFILES:
        p = out["profiles"][name]
        print(f"{name:18s} distance={p['distance_colour']}  pheo_len={p['pheo_fraction']}")
    print("textures:", sorted(os.listdir(TEX)))

if __name__ == "__main__":
    main()
