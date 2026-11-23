#!/usr/bin/env python3
"""Sen head rebuild driver (2026-11-16) — corrected builder + Sen's
tongue direction.

Runs the shared generic builder
(characters/common/build_head.py — side taken from each part's
own position, base-head-v4, parameterised --base) with Sen's
UNCHANGED batch-1 vector (scripts/sen_vector.json) and
--tongue-scale 1.3, in one Blender session, applying the one character
direction the generic vector leaves out: Sen's tongue x1.3, carried
over from the original build (characters/sen/scripts/build_head.py,
its section 4.3; SEN_BUILD.md S3: "Sen canon: huge tongue"). The scale
is applied uniformly about the tongue's posterior base (mean of the 20
most posterior verts), the tongue report is written into
work/head_measure.json in the original's format, and sen_head.glb /
sen_head.blend are exported once with the scaled tongue. Teeth
verification is the builder's (the tongue takes no part in the
upper/lower BVH check).

The original 2026-11-12 script keyed left/right off object names
(side = +1 iff the name ends in "R"); in this head frame Ear_L /
Eyeball_L sit at +x, so Sen's EarSpread and EyeSpacing shifts ran
mirrored. That script is preserved untouched as the historical
record; this driver supersedes it.

Run: HOME=/tmp/af_home xvfb-run -a blender -b --threads 2 \
     --python build_sen_head.py
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEN = HERE.parent
CHARS = SEN.parent
V2 = CHARS.parent
if str(CHARS) not in sys.path:
    sys.path.insert(0, str(CHARS))

from common.build_head import build_head  # noqa: E402

DEFAULT_VECTOR = HERE / "sen_vector.json"
DEFAULT_BASE = V2 / "base-head-v4" / "neutral_base_head_v4.glb"
BUILD_DRIVER = (
    "characters/sen/scripts/build_sen_head.py — "
    "corrected batch builder (common/build_head.py) + tongue x1.3 step"
)


def main(argv=None):
    if argv is None:
        argv = (sys.argv[sys.argv.index("--") + 1:]
                if "--" in sys.argv else [])
    ap = argparse.ArgumentParser()
    ap.add_argument("--vector", default=str(DEFAULT_VECTOR))
    ap.add_argument("--base", default=str(DEFAULT_BASE))
    ap.add_argument("--outdir", default=str(SEN))
    ap.add_argument("--tongue-scale", type=float, default=1.3)
    A = ap.parse_args(argv)
    report = build_head(
        char="sen",
        vector=A.vector,
        base=A.base,
        outdir=A.outdir,
        tongue_scale=A.tongue_scale,
        build_driver=BUILD_DRIVER,
    )
    print("SEN HEAD REBUILD DONE (corrected builder + tongue x1.3)")
    return report


if __name__ == "__main__":
    main()
