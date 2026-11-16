"""AnthroForge soft-tissue soft-dynamics settings (shared by build scripts).

Two stiffness settings. Tuned first on synthetic walk motion, then
re-anchored on the REAL sampled Walk clip (root rotation dominates lag
there, so the pair is chosen for settle-time separation):
  SOFT k=1.5 -> settle 1.60 s, equilibrium hang offset 7.1 deg,
                walk dynamic swing peak 4.2 deg, lag peak 10.9 deg
  FIRM k=8.0 -> settle 0.43 s, hang offset 5.8 deg, swing peak 3.2 deg
(k in 1/s; response is resonance-sensitive near stride frequency, which is
the point -- heavy soft tissue near its pendulum resonance sways most.)
"""
FPS = 30.0
CYCLE = 32                 # Walk action frames 1..32 loop (33 = loop dupe)
N_WALK = CYCLE * 3         # 96 frames of walking
N_SETTLE = 90              # then root freezes, chain settles
N_FRAMES = N_WALK + N_SETTLE
PREROLL = 30               # discarded frames so the chain starts settled

# sac chain: 4 segments, root-frame offsets (x=side, y=forward, z=up), metres
REST_OFFSETS = [[0.0, 0.010, -0.0995],
                [0.0, 0.014, -0.1091],
                [0.0, 0.018, -0.1085],
                [0.0, 0.020, -0.0980]]
SEG_SOFTNESS = [0.20, 0.50, 0.80, 1.00]     # AF_softness at segment midpoints

SETTINGS = {
    'SOFT': {'stiffness': 1.5, 'drag_force': 0.025, 'gravity_power': 1.0},
    'FIRM': {'stiffness': 8.0, 'drag_force': 0.025, 'gravity_power': 1.0},
}

# teat chains: 1 segment each, hang from the sac tip. Short pendulums
# (4.8 cm, natural freq ~2.3 Hz) track FASTER than the sac despite softer
# tissue: softness 1.0 (field max -- teats are the softest tissue on the
# part) but k_teat = 2.0x sac stiffness, because the softness->stiffness
# mapping carries a length term (short chain, less spring relief needed).
# First run at 0.55x / free flail gave an absurd 55-60 deg swing.
TEAT_OFFSET = [0.0, 0.004, -0.048]          # in tip frame (x=side out, y=fwd, z=up)
TEAT_SOFTNESS = [1.0]
TEAT_K_SCALE = 2.0
