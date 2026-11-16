"""Run the spring-chain sims on the REAL sampled Walk root motion.

Produces work/sim_results.npz (particle positions for baking, preroll
dropped) and work/sim_metrics.json (lag / settle / sag / phase numbers),
plus renders/lag_plot.png.
Run with plain python3 (numpy + matplotlib), no Blender.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_common import (FPS, CYCLE, N_WALK, N_FRAMES, PREROLL,
                          REST_OFFSETS, SEG_SOFTNESS, SETTINGS,
                          TEAT_OFFSET, TEAT_SOFTNESS, TEAT_K_SCALE)
from simulate import run_chain, chain_metrics, settle_time

BASE = os.path.expanduser('~/workspace/anthroforge-v2/dynamics')
rm = np.load(os.path.join(BASE, 'work/root_motion.npz'))
root_pos_all = rm['root_pos']
root_R_all = rm['root_R']
root_pos = root_pos_all[PREROLL:]
root_R = root_R_all[PREROLL:]


def teat_frame(tip_pos, prev_pos, world_R):
    """Per-frame frame at the sac tip: -z continues along the tip segment."""
    d = tip_pos - prev_pos
    d /= (np.linalg.norm(d, axis=1, keepdims=True) + 1e-12)
    up = -d                                     # local +z points back up-chain
    fwd = world_R[:, :, 1]                      # root-frame forward (world)
    fwd = fwd - up * np.sum(fwd * up, axis=1, keepdims=True)
    fwd /= (np.linalg.norm(fwd, axis=1, keepdims=True) + 1e-12)
    side = np.cross(up, fwd)
    side /= (np.linalg.norm(side, axis=1, keepdims=True) + 1e-12)
    fwd = np.cross(side, up)
    R = np.stack([side, fwd, up], axis=2)
    return R, side


def phase_lag_ms(root_z, tip_z, fps=FPS):
    a = root_z - root_z.mean()
    b = tip_z - tip_z.mean()
    corr = np.correlate(b, a, mode='full')
    lag = corr.argmax() - (len(a) - 1)
    return float(lag / fps * 1000.0)


def xcorr_lag_ms(driver, response, fps=FPS):
    """Lag of response behind driver (ms), best over +/- half the window."""
    a = driver - driver.mean()
    b = response - response.mean()
    corr = np.correlate(b, a, mode='full')
    lag = int(corr.argmax() - (len(a) - 1))
    return float(lag / fps * 1000.0)


results = {}
store = {}
for name, params in SETTINGS.items():
    # sac chain on the full (preroll-inclusive) root motion, then drop preroll
    sac_all = run_chain(root_pos_all, root_R_all, REST_OFFSETS, params,
                        SEG_SOFTNESS)
    sac = sac_all[PREROLL:]
    m = chain_metrics(sac, root_pos, root_R, REST_OFFSETS)
    steady = slice(CYCLE * 2, N_WALK)
    lag = m['lag_deg']
    st, equil = settle_time(lag, N_WALK)
    dyn = lag - equil            # dynamic swing about the equilibrium hang
    side_err = np.einsum('fi,fi->f', m['tip_err'], root_R[:, :, 0])
    side_disp = root_pos @ root_R[:, :, 0].mean(axis=0)
    entry = {
        'params': params,
        'walk_lag_peak_deg': float(lag[steady].max()),
        'walk_lag_rms_deg': float(np.sqrt((lag[steady] ** 2).mean())),
        'walk_dynamic_swing_peak_deg': float(np.abs(dyn[steady]).max()),
        'walk_dynamic_swing_rms_deg': float(np.sqrt((dyn[steady] ** 2).mean())),
        'settle_time_s': float(st),
        'equilibrium_hang_offset_deg': float(equil),
        'phase_lag_side_err_vs_root_sway_ms': xcorr_lag_ms(
            side_disp[steady], side_err[steady]),
        'tip_travel_walk_m': float(
            np.linalg.norm(np.diff(sac[steady, -1, :], axis=0), axis=1).sum()),
    }
    # teat chains hang off the sac tip (root frame from the tip segment)
    R_teat, side_teat = teat_frame(sac[:, -1, :], sac[:, -2, :], root_R)
    teat_out = {}
    for sgn, label in [(+1.0, 'R'), (-1.0, 'L')]:
        attach = sac[:, -1, :] + side_teat * (0.05 * sgn)
        off = np.array(TEAT_OFFSET, float)
        off[0] = 0.010 * sgn
        tp = dict(params)
        tp['stiffness'] = params['stiffness'] * TEAT_K_SCALE
        tpos_all = run_chain(np.vstack([root_pos_all[:PREROLL] * 0 +
                                        attach[:1], attach])[:PREROLL + len(attach)],
                             np.concatenate([R_teat[:1].repeat(PREROLL, 0),
                                             R_teat]),
                             [off], tp, TEAT_SOFTNESS)
        tpos = tpos_all[PREROLL:]
        tm = chain_metrics(tpos, attach, R_teat, [off])
        teat_out[label] = tpos
        entry[f'teat{label}_lag_peak_deg'] = float(tm['lag_deg'][steady].max())
        entry[f'teat{label}_lag_rms_deg'] = float(
            np.sqrt((tm['lag_deg'][steady] ** 2).mean()))
    results[name] = entry
    store[f'sac_{name}'] = sac
    store[f'teatL_{name}'] = teat_out['L']
    store[f'teatR_{name}'] = teat_out['R']
    store[f'lag_{name}'] = lag

np.savez(os.path.join(BASE, 'work/sim_results.npz'), **store)
with open(os.path.join(BASE, 'work/sim_metrics.json'), 'w') as f:
    json.dump(results, f, indent=1)
print(json.dumps(results, indent=1))

# --- lag plot ---------------------------------------------------------------
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, ax = plt.subplots(2, 1, figsize=(9, 4.6), sharex=True)
fr = np.arange(N_FRAMES)
for name in SETTINGS:
    ax[0].plot(fr, store[f'lag_{name}'], label=f'{name} tip lag')
ax[0].axvline(N_WALK, color='k', ls='--', lw=0.8)
ax[0].set_ylabel('tip lag (deg)')
ax[0].legend(loc='upper right')
ax[0].set_title('Spring-chain tip lag — 3 walk cycles, then root freezes at frame 96')
ax[1].plot(fr, root_pos[:, 2] - root_pos[:, 2].mean(), color='gray',
           label='root (pelvis) height, demeaned')
ax[1].axvline(N_WALK, color='k', ls='--', lw=0.8)
ax[1].set_ylabel('root z (m)')
ax[1].set_xlabel('frame @30fps')
ax[1].legend(loc='upper right')
fig.tight_layout()
fig.savefig(os.path.join(BASE, 'renders/lag_plot.png'), dpi=110)
print('PLOT_OK')
