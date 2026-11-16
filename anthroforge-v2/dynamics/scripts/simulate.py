"""AnthroForge soft-tissue spring-chain simulation (numpy, Blender-free).

Model: VRM SpringBone-style verlet chain.
  - particles integrated with verlet + gravity + drag
  - a positional stiffness spring pulls each particle toward its REST position
    in the current root frame (the animated pose); lag/sway emerge from the
    root moving faster than the particles follow
  - distance constraints re-impose segment lengths (2 iterations)
Parameters use VRM vocabulary: stiffness (spring rate, 1/s), drag_force
(velocity loss 0..1 per step scale), gravity_power (multiplier on g).
Per-segment softness (0..1, from the AF_softness paintable field) softens the
local spring: k_i = k * (1 - 0.6 * softness_i). Teats run softer than the sac
body, the sac softer than a belly core -- same code, different field values.

API: run_chain(root_pos, root_R, rest_offsets, params, softness, dt_frame,
               substeps) -> positions array (n_frames, n_joints, 3)
root_pos: (F,3) world positions of the chain root (attach point)
root_R:   (F,3,3) world rotation of the root frame; rest_offsets are in it.
"""
import numpy as np

G = np.array([0.0, 0.0, -9.81])


def _rot_between(a, b):
    """Rotation matrix taking unit vector a to unit vector b."""
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    v = np.cross(a, b)
    c = float(np.clip(np.dot(a, b), -1, 1))
    if np.linalg.norm(v) < 1e-10:
        if c > 0:
            return np.eye(3)
        # 180 deg: rotate about any perpendicular axis
        axis = np.array([1.0, 0, 0]) if abs(a[0]) < 0.9 else np.array([0, 1.0, 0])
        axis = axis - a * np.dot(axis, a)
        axis /= np.linalg.norm(axis)
        return 2 * np.outer(axis, axis) - np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * ((1 - c) / (np.linalg.norm(v) ** 2))


def _slerp_dir(cur, target, t):
    """Move unit vector cur toward target by fraction t of the arc."""
    c = float(np.clip(np.dot(cur, target), -1, 1))
    ang = np.arccos(c)
    if ang < 1e-8:
        return target.copy()
    s = np.sin(ang)
    return (np.sin((1 - t) * ang) / s) * cur + (np.sin(t * ang) / s) * target


def run_chain(root_pos, root_R, rest_offsets, params, softness=None,
              dt_frame=1.0 / 30.0, substeps=4):
    root_pos = np.asarray(root_pos, float)
    root_R = np.asarray(root_R, float)
    rest_offsets = np.asarray(rest_offsets, float)
    n_frames = len(root_pos)
    n_seg = len(rest_offsets)
    seg_len = np.linalg.norm(rest_offsets, axis=1)
    rest_dirs = rest_offsets / seg_len[:, None]
    if softness is None:
        softness = np.zeros(n_seg)
    softness = np.asarray(softness, float)

    k_base = params['stiffness']
    drag = params['drag_force']
    grav = G * params['gravity_power']
    dt = dt_frame / substeps

    # constant relative rotations between consecutive rest directions
    Q_rel = [None] + [_rot_between(rest_dirs[i - 1], rest_dirs[i])
                      for i in range(1, n_seg)]

    # rest joint positions in root frame
    rest_joints_local = np.vstack([np.zeros(3),
                                   np.cumsum(rest_offsets, axis=0)])

    # initialise at rest under frame-0 root
    p = (root_R[0] @ rest_joints_local.T).T + root_pos[0]
    p_prev = p.copy()
    blend = 1.0 - np.exp(-k_base * (1.0 - 0.6 * softness) * dt)

    out = np.empty((n_frames, n_seg + 1, 3))
    for f in range(n_frames):
        for _ in range(substeps):
            vel = (p - p_prev) * (1.0 - drag)
            p_prev = p.copy()
            p = p + vel + grav * dt * dt
            # angular (bend) stiffness marched root->tip: each segment is
            # slerped toward its rest direction RELATIVE to its parent's
            # current direction (segment 1: relative to the root frame).
            # Resists kinking, not swinging -- a true pendulum chain whose
            # hang angle is set by spring-vs-gravity balance at the root.
            for _ in range(2):
                p[0] = root_pos[f]
                for i in range(1, n_seg + 1):
                    if i == 1:
                        desired_dir = root_R[f] @ rest_dirs[0]
                    else:
                        prev_dir = p[i - 1] - p[i - 2]
                        prev_dir /= (np.linalg.norm(prev_dir) + 1e-12)
                        desired_dir = Q_rel[i - 1] @ prev_dir
                    cur = p[i] - p[i - 1]
                    cur /= (np.linalg.norm(cur) + 1e-12)
                    new_dir = _slerp_dir(cur, desired_dir, blend[i - 1])
                    p[i] = p[i - 1] + new_dir * seg_len[i - 1]
            p[0] = root_pos[f]
        out[f] = p
    return out


def chain_metrics(positions, root_pos, root_R, rest_offsets, fps=30.0):
    """Lag/settle metrics for a simulated chain.

    lag angle: angle between the root->tip direction now and the root->tip
    REST direction under the current root frame (deg).
    Returns dict of per-frame arrays + summary stats filled by caller.
    """
    rest_tip_local = np.sum(np.asarray(rest_offsets, float), axis=0)
    rest_tip_local /= np.linalg.norm(rest_tip_local)
    tip_dir = positions[:, -1, :] - positions[:, 0, :]
    tip_dir /= (np.linalg.norm(tip_dir, axis=1, keepdims=True) + 1e-12)
    rest_world = np.einsum('fij,j->fi', root_R, rest_tip_local)
    cosang = np.clip(np.sum(tip_dir * rest_world, axis=1), -1, 1)
    lag_deg = np.degrees(np.arccos(cosang))
    # forward/side decomposition of tip offset from desired tip position
    desired_tip = np.einsum('fij,j->fi', root_R,
                            np.sum(np.asarray(rest_offsets, float), axis=0)) + root_pos
    tip_err = positions[:, -1, :] - desired_tip
    return {'lag_deg': lag_deg, 'tip_err': tip_err,
            'tip_pos': positions[:, -1, :]}


def settle_time(lag_deg, freeze_start, fps=30.0, thresh_deg=2.0):
    """Frames after freeze_start until |lag - final| stays < thresh."""
    tail = lag_deg[freeze_start:]
    final = np.mean(tail[-10:])
    dev = np.abs(tail - final)
    for i in range(len(dev)):
        if np.all(dev[i:] < thresh_deg):
            return i / fps, final
    return len(tail) / fps, final


if __name__ == '__main__':
    # --- synthetic tuning run: root bobs/sways like a walk cycle -----------
    fps = 30.0
    cycle = 32  # frames per stride (Walk clip: 33 frames, loop = 32)
    n_walk = cycle * 3
    n_settle = 90
    F = n_walk + n_settle
    t = np.arange(F) / fps
    stride_f = fps / cycle
    root_pos = np.zeros((F, 3))
    root_pos[:, 0] = 0.018 * np.sin(2 * np.pi * stride_f * t)          # sway
    root_pos[:, 2] = 1.02 + 0.022 * np.sin(4 * np.pi * stride_f * t)   # bob 2x
    root_pos[n_walk:] = root_pos[n_walk - 1]                            # freeze
    pitch = np.radians(2.0) * np.sin(2 * np.pi * stride_f * t)
    yaw = np.radians(5.0) * np.sin(2 * np.pi * stride_f * t)
    roll = np.radians(4.0) * np.sin(2 * np.pi * stride_f * t + 0.7)
    pitch[n_walk:] = pitch[n_walk - 1]
    yaw[n_walk:] = yaw[n_walk - 1]
    roll[n_walk:] = roll[n_walk - 1]
    root_R = np.zeros((F, 3, 3))
    for f in range(F):
        cp, sp = np.cos(pitch[f]), np.sin(pitch[f])
        cy, sy = np.cos(yaw[f]), np.sin(yaw[f])
        cr, sr = np.cos(roll[f]), np.sin(roll[f])
        Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
        Ry = np.array([[cr, 0, sr], [0, 1, 0], [-sr, 0, cr]])
        Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
        root_R[f] = Rz @ Rx @ Ry
    rest_offsets = np.array([[0, 0.010, -0.0995],
                             [0, 0.014, -0.1091],
                             [0, 0.018, -0.1085],
                             [0, 0.020, -0.0980]])
    softness = np.array([0.20, 0.50, 0.80, 1.00])
    for name, params in [('SOFT', {'stiffness': 3.0, 'drag_force': 0.025,
                                   'gravity_power': 1.0}),
                         ('FIRM', {'stiffness': 14.0, 'drag_force': 0.025,
                                   'gravity_power': 1.0})]:
        pos = run_chain(root_pos, root_R, rest_offsets, params, softness)
        m = chain_metrics(pos, root_pos, root_R, rest_offsets)
        walk = m['lag_deg'][cycle * 2:n_walk]
        st, final = settle_time(m['lag_deg'], n_walk)
        print(f"{name}: walk lag peak {walk.max():.1f} deg  rms "
              f"{np.sqrt((walk ** 2).mean()):.1f}  settle {st:.2f}s "
              f"(final lag {final:.1f})")
