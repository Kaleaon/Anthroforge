"""Anatomical guards on top of the raw geodesic weights (method B+).

Raw geodesic fields leak across semantic boundaries on connected meshes.
Standard production fix: hard anatomical guards for small rigid parts and a
hinge-plane fade for the jaw. Guards applied:
  Teeth  - per connected component (each tooth / arcade slab is its own
           component): centroid above occlusal plane z=-0.97 -> rigid Head,
           below -> rigid Jaw.
  Rings  - earrings: rigid to Ear_L / Ear_R by x sign.
  Tongue - keep only {Jaw, Head} influences, renormalise.
  Bust   - Jaw weight faded by smoothstep across the hinge plane
           (full below z=-0.45, zero above z=-0.15), renormalise.
Output: geo_weights_guarded.npz in the same top-4 format as geo_weights.npz.
"""
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

W = "/home/hatch/workspace/anthroforge-v2/autoskin-prototype/work"
BONE_NAMES = ['Root','Pelvis','Spine1','Chest','Neck','Head','Jaw','Ear_L','Ear_R',
 'Shoulder_L','Elbow_L','Wrist_L','Shoulder_R','Elbow_R','Wrist_R','Hip_L','Knee_L',
 'Ankle_L','Foot_L','Hip_R','Knee_R','Ankle_R','Foot_R','Wing_L1','Wing_L2','Wing_R1',
 'Wing_R2','Tail_1','Tail_2','Tail_3','GenBase','GenScrot','Gen01','Gen02','Gen03','Gen04']
HI, JA, EL, ER = (BONE_NAMES.index(b) for b in ('Head','Jaw','Ear_L','Ear_R'))
OCCLUSAL_Z = -0.97

def dense(bi, w4, n):
    Wm = np.zeros((n, 36), np.float32)
    np.put_along_axis(Wm, bi, w4, axis=1)
    return Wm

def top4(Wm):
    idx = np.argsort(-Wm, axis=1)[:, :4]
    w4 = np.take_along_axis(Wm, idx, axis=1)
    s = w4.sum(axis=1, keepdims=True); s[s == 0] = 1.0
    return idx.astype(np.int32), (w4 / s).astype(np.float32)

def components(faces, n):
    E = np.vstack([faces[:, [0,1]], faces[:, [1,2]], faces[:, [2,0]]])
    E = np.unique(np.sort(E, axis=1), axis=0)
    G = csr_matrix((np.ones(len(E)), (E[:,0], E[:,1])), shape=(n, n))
    return connected_components(G + G.T, directed=False)[1]

def main():
    d = np.load(f"{W}/bust_meshes.npz")
    w = np.load(f"{W}/geo_weights.npz")
    out = {}
    for k in d.keys():
        if not k.endswith("_v"):
            continue
        name = k[:-2]
        verts, faces = d[k], d[name + "_f"]
        n = len(verts)
        Wm = dense(w[name + "_bi"], w[name + "_w"], n)
        if name.startswith("Teeth"):
            lab = components(faces, n)
            Wm[:] = 0.0
            for c in range(lab.max() + 1):
                sel = lab == c
                vv = verts[sel]
                bone = HI if vv[:, 2].mean() > OCCLUSAL_Z else JA
                # tusk rule: tall front components that taper toward the top
                # are lower tusks erupting up past the occlusal plane
                span = vv[:, 2].max() - vv[:, 2].min()
                if span >= 0.30 and vv[:, 1].mean() < -0.95:
                    zc = (vv[:, 2] - vv[:, 2].min()) / span
                    def spread(s):
                        cxy = s[:, :2].mean(0)
                        return np.linalg.norm(s[:, :2] - cxy, axis=1).mean()
                    if spread(vv[zc > 0.8]) < 0.6 * spread(vv[zc < 0.2]):
                        bone = JA
                Wm[sel, bone] = 1.0
            up = int((Wm[:, HI] > 0).sum()); lo = int((Wm[:, JA] > 0).sum())
            print(f"Teeth: {up} verts -> Head (upper), {lo} verts -> Jaw (lower)")
        elif name.startswith("Rings"):
            Wm[:] = 0.0
            Wm[verts[:, 0] > 0, EL] = 1.0
            Wm[verts[:, 0] <= 0, ER] = 1.0
            print("Rings: rigid to ears by side")
        elif name == "0":  # tongue
            keep = np.zeros(36, bool); keep[[HI, JA]] = True
            Wm[:, ~keep] = 0.0
            s = Wm.sum(axis=1, keepdims=True); s[s == 0] = 1.0; Wm = Wm / s
            print("Tongue: influences restricted to {Head, Jaw}")
        elif name.startswith("OrcBust"):
            z = verts[:, 2]
            t = np.clip((-0.15 - z) / 0.30, 0.0, 1.0)      # 1 below -0.45, 0 above -0.15
            fade = t * t * (3 - 2 * t)                      # smoothstep
            Wm[:, JA] *= fade
            s = Wm.sum(axis=1, keepdims=True); s[s == 0] = 1.0; Wm = Wm / s
            print(f"Bust: jaw hinge-guard applied; verts with jaw w>0.5 now "
                  f"{int((Wm[:, JA] > 0.5).sum())} (was 10712 dominant)")
        Wm[Wm < 0.01] = 0.0
        bi, w4 = top4(Wm)
        out[name + "_bi"], out[name + "_w"] = bi, w4
    np.savez_compressed(f"{W}/geo_weights_guarded.npz", **out)
    print("saved geo_weights_guarded.npz")

if __name__ == "__main__":
    main()
