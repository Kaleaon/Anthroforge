import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from glb_lib import load_glb, meshes

OUT = "/home/hatch/workspace/anthroforge-v2/model-craft/b12-face/"
gltf, bin_chunk = load_glb("/home/hatch/workspace/anthroforge-v2/base-head-v3/neutral_base_head_v3.glb")
MS = meshes(gltf, bin_chunk)
def weld(pos, idx, tol=1e-4):
    key = np.round(pos / tol).astype(np.int64)
    _, first, inv = np.unique(key, axis=0, return_index=True, return_inverse=True)
    widx = inv[idx]
    ok = (widx[:,0]!=widx[:,1]) & (widx[:,1]!=widx[:,2]) & (widx[:,0]!=widx[:,2])
    return pos[first], widx[ok]

tp, ti = weld(*MS["TissueHead"][0])
eyeL = np.array([0.131, -0.008, -0.082]); eyeR = np.array([-0.131, -0.008, -0.082])
d_eye = np.minimum(np.linalg.norm(tp-eyeL,axis=1), np.linalg.norm(tp-eyeR,axis=1))
region = np.full(len(tp), "other", dtype=object)
region[(np.abs(tp[:,0])<0.17)&(tp[:,1]>0.02)&(tp[:,2]>-0.28)&(tp[:,2]<0.08)] = "brow band"
region[d_eye<0.20] = "eye zone"
region[(tp[:,2]<-0.25)&(tp[:,1]>-0.30)] = "muzzle"
region[(np.abs(tp[:,0])>0.19)&(tp[:,2]>-0.28)&(tp[:,2]<0.12)&(tp[:,1]<0.06)] = "cheek"
colors = {"brow band":"#d97706","eye zone":"#2563eb","muzzle":"#059669","cheek":"#9333ea","other":"#9ca3af"}

fig, ax = plt.subplots(figsize=(5.2,5.2), dpi=200)
for rn in ["other","cheek","muzzle","brow band","eye zone"]:
    m = region==rn
    ax.scatter(tp[m,0], tp[m,1], s=3, c=colors[rn], label=f"{rn} ({int(m.sum())})", linewidths=0)
for e in (eyeL, eyeR):
    ax.add_patch(plt.Circle((e[0], e[1]), 0.075, fill=False, ec="k", lw=1.2))
ax.set_aspect("equal"); ax.set_xlabel("x (L)"); ax.set_ylabel("y (L)")
ax.set_title("v3 TissueHead - front: regions + orbit O 0.15 L", fontsize=10)
ax.legend(fontsize=7, markerscale=3, loc="lower center", ncol=3, frameon=False)
fig.tight_layout(); fig.savefig(OUT+"annotation_front_regions.png"); plt.close(fig)

mid = tp[np.abs(tp[:,0])<0.012]
o = np.argsort(mid[:,2]); prof = mid[o]
fig, ax = plt.subplots(figsize=(5.6,4.2), dpi=200)
ax.scatter(tp[:,2], tp[:,1], s=1.5, c="#d1d5db", linewidths=0)
ax.plot(prof[:,2], prof[:,1], c="#111827", lw=1.6, label="dorsal midline profile")
ax.axhline(-0.180, color="#2563eb", ls="--", lw=1, label="palatal line (y = -0.180)")
ax.plot([eyeL[2]], [eyeL[1]], "o", color="#2563eb", ms=6, label="eye centre (OrbitHeight 0.172)")
ax.plot([-0.27],[0.062], "x", color="#dc2626", ms=10, mew=2, label="stop: max profile curvature (z = -0.27)")
ax.annotate("profile slope 0.65 -> 2.81", xy=(-0.27,0.062), xytext=(-0.02,0.30),
            fontsize=8, arrowprops=dict(arrowstyle="->", lw=0.8))
ax.set_xlabel("z (L, nose at left)"); ax.set_ylabel("y (L)")
ax.set_title("v3 profile - stop break in the palatal frame", fontsize=10)
ax.legend(fontsize=7, loc="lower left", frameon=False)
fig.tight_layout(); fig.savefig(OUT+"annotation_profile_stop.png"); plt.close(fig)

ep, ei = weld(*MS["Eyelid_L"][0]); bp, bi = weld(*MS["Eyeball_L"][0])
fig, ax = plt.subplots(figsize=(4.6,4.6), dpi=200)
m = d_eye < 0.30
ax.scatter(tp[m,0], tp[m,1], s=5, c="#9ca3af", label="skin (no opening, no rim loop)", linewidths=0)
ax.scatter(ep[:,0], ep[:,1], s=2, c="#f59e0b", label="Eyelid_L: closed sphere-cap shell", linewidths=0)
ax.scatter(bp[:,0], bp[:,1], s=2, c="#2563eb", label="Eyeball_L: sphere r = 0.075", linewidths=0)
ax.add_patch(plt.Circle((eyeL[0], eyeL[1]), 0.075, fill=False, ec="k", lw=1))
ax.set_xlim(0.55, -0.25); ax.set_ylim(-0.30, 0.28)
ax.set_xlabel("x (L)"); ax.set_ylabel("y (L)")
ax.set_title("Eye station (left) - grafted assembly over unbroken skin", fontsize=9)
ax.legend(fontsize=7, loc="lower left", frameon=False)
fig.tight_layout(); fig.savefig(OUT+"annotation_eye_station.png"); plt.close(fig)

ap, ai = weld(*MS["Ear_L"][0])
c = ap.mean(0); U,S,Vt = np.linalg.svd(ap-c, full_matrices=False)
pc = (ap-c)@Vt.T
fig, ax = plt.subplots(figsize=(4.4,5.2), dpi=200)
sc = ax.scatter(pc[:,0], pc[:,1], c=pc[:,2], cmap="coolwarm", s=26, vmin=-0.04, vmax=0.04, linewidths=0)
ax.set_aspect("equal"); ax.set_xlabel("ear plane axis 1 (L)"); ax.set_ylabel("ear plane axis 2 (L)")
ax.set_title("Ear_L relief map (76 verts) - one shallow cup,\nno resolved antihelix / scapha / tragus", fontsize=9)
cb = fig.colorbar(sc, ax=ax, shrink=0.8); cb.set_label("signed depth from ear plane (L)", fontsize=8)
fig.tight_layout(); fig.savefig(OUT+"annotation_ear_relief.png"); plt.close(fig)

nlp, nli = weld(*MS["NoseLeather"][0])
fig, ax = plt.subplots(figsize=(4.8,4.8), dpi=200)
mm = (tp[:,2]<-0.30)&(tp[:,1]>-0.36)&(tp[:,1]<0.02)
ax.scatter(tp[mm,0], tp[mm,1], s=6, c="#9ca3af", label="muzzle skin", linewidths=0)
lip = mm & (tp[:,1]>-0.30)&(tp[:,1]<-0.16)
ax.scatter(tp[lip,0], tp[lip,1], s=8, c="#059669", label="lip-line zone (crease only, no loop)", linewidths=0)
ax.scatter(nlp[:,0], nlp[:,1], s=3, c="#dc2626", label="NoseLeather cap (separate closed shell)", linewidths=0)
ax.set_aspect("equal"); ax.set_xlabel("x (L)"); ax.set_ylabel("y (L)")
ax.set_title("Muzzle front - nose cap seating + lip zone", fontsize=10)
ax.legend(fontsize=7, loc="lower center", frameon=False)
fig.tight_layout(); fig.savefig(OUT+"annotation_muzzle_nose.png"); plt.close(fig)
print("figures written")
