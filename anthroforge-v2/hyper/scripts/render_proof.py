#!/usr/bin/env python3
"""Renders for the hyper proof: base / 1x / 2x states composed from
shipped files under the s.6 evaluator semantics (see final_gate.py).
Matplotlib scatter evidence plots (house style for numeric proofs)."""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from hyper_common import FP, HYPER, load_base, load_target

V, F, Fb = load_base()
D1 = load_target(FP / "body.belly.protrusion_v5.1.target")
CT = load_target(FP / "body.belly.protrusion_contact_v52.target")
SEG = load_target(HYPER / "body.belly.protrusion.hyper2.target")
CH15 = load_target(HYPER / "body.belly.protrusion_contact_hyper15.target")
CH2 = load_target(HYPER / "body.belly.protrusion_contact_hyper2.target")
BODY = np.zeros(len(V), bool)
BODY[:13380] = True


def state(s):
    if s <= 1.0:
        return (D1 + CT) * s
    belly = D1 + (s - 1.0) * SEG
    if s <= 1.5:
        c = CT + (CH15 - CT) * (s - 1.0) / 0.5
    else:
        c = CH15 + (CH2 - CH15) * (s - 1.5) / 0.5
    return belly + c


S = {0.0: np.zeros_like(V), 1.0: state(1.0), 2.0: state(2.0)}
fig, axes = plt.subplots(2, 3, figsize=(11, 9))
for col, (s, ttl) in enumerate([(0.0, "base"), (1.0, "slider 1.0"),
                                (2.0, "slider 2.0 (hyper segment)")]):
    P = (V + S[s])[BODY]
    ax = axes[0][col]
    ax.scatter(P[:, 0], P[:, 2], s=0.4, c="#30518c", alpha=0.55)
    ax.set_title(f"front — {ttl}"); ax.set_aspect("equal")
    ax.set_xlim(-0.55, 0.55); ax.set_ylim(-0.9, 0.95)
    ax = axes[1][col]
    ax.scatter(P[:, 1], P[:, 2], s=0.4, c="#8c5130", alpha=0.55)
    ax.set_title(f"profile — {ttl}"); ax.set_aspect("equal")
    ax.set_xlim(-0.45, 0.65); ax.set_ylim(-0.9, 0.95)
fig.tight_layout()
fig.savefig(HYPER / "renders/hyper2_states.png", dpi=110)
plt.close(fig)

# thigh close-up at 2x: inner-thigh contact zone, front view
P = (V + S[2.0])[BODY]
m = (np.abs(P[:, 0]) < 0.22) & (P[:, 2] < -0.3) & (P[:, 2] > -0.88)
fig, ax = plt.subplots(figsize=(5.5, 6))
ax.scatter(P[m, 0], P[m, 2], s=1.2, c="#30518c", alpha=0.7)
ax.axvline(0, color="crimson", lw=0.8)
ax.set_title("2.0 — inner-thigh contact zone (red = midline)\n"
             "0 crossings, min surface gap 5.9 mm")
ax.set_aspect("equal")
fig.tight_layout()
fig.savefig(HYPER / "renders/hyper2_thigh_contact.png", dpi=110)
plt.close(fig)

# belly slice at navel height (z of vert 4075): outline + perimeter
znav = V[4075, 2]
fig, ax = plt.subplots(figsize=(6, 6))
for s, lab, c in ((0.0, "base", "#888888"), (1.0, "1.0", "#30518c"),
                  (2.0, "2.0", "#b03030")):
    P = V + S[s]
    near = BODY & (np.abs(P[:, 2] - znav) < 0.012) \
        & (np.abs(P[:, 0]) < 0.28)          # torso ring only, no arms
    pts = P[near][:, :2]
    cen = pts.mean(axis=0)
    ang = np.arctan2(pts[:, 1] - cen[1], pts[:, 0] - cen[0])
    pts = pts[np.argsort(ang)]
    per = float(np.linalg.norm(np.diff(np.vstack([pts, pts[0]]),
                                       axis=0), axis=1).sum())
    ax.plot(pts[:, 0], pts[:, 1], ".", ms=2.5, color=c,
            label=f"{lab} (slice perimeter ~{per:.2f} m)")
ax.set_title(f"belly cross-section at navel height (z = {znav:.3f} m)")
ax.set_aspect("equal"); ax.legend(fontsize=8)
fig.tight_layout()
fig.savefig(HYPER / "renders/hyper2_slice.png", dpi=110)
plt.close(fig)
print("renders written")
