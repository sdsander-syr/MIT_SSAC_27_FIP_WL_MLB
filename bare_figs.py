"""
Regenerates absfig1.pdf, absfig3.pdf and "fig_marginal_sm (1).png" under their
EXISTING names, with every title/subtitle above the axes removed and the
overlapping insets gone. Headers are left to LaTeX.

Titles, subtitles and the explanatory inset are removed so they can be typeset
in LaTeX, where they are editable. What remains inside each PDF is only the
plot itself: axes, ticks, axis labels, legend and data. The legend stays
inside the axes because it keys the colours, but it is placed clear of the
surface so it cannot bleed into the data.
"""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from mpl_toolkits.mplot3d import Axes3D  # noqa
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                     "xtick.labelsize": 8.5, "ytick.labelsize": 8.5})
UR, GAM = 0.31, 1.83

def _solve_fstar(path="pitcher_seasons_full.csv", season=2026):
    """Win-neutral anchor, solved from the data rather than hardcoded, so this
    script and the Rmd pipeline can never drift apart."""
    from scipy.optimize import brentq
    t = pd.read_csv(path)
    t = t[(t.season == season) & t.FIP.notna() & (t.IP > 0)]
    g = t.IP / 9

    def f(ref):
        n = (ref + UR) ** GAM
        return float((g * (n / (n + np.maximum(t.FIP.values + UR, 1e-6) ** GAM))).sum()
                     / g.sum() - 0.5)
    return brentq(f, 0.5, 15, xtol=1e-12)

FS = _solve_fstar()
ROLE_C = {"Starter": "#2E6FB7", "Relief": "#E8A33D", "Closer": "#2E9E6B"}
PANEL, ELEV, AZIM = (6.4, 4.6), 25, -60
BOXASP = (1.10, 0.95, 0.80)
LABFS, TICKFS = 10.5, 9


def wp(f, ref=FS):
    n = (ref + UR) ** GAM
    return n / (n + np.maximum(np.asarray(f, float) + UR, 1e-6) ** GAM)


# ---------------- panel A: the win surface, no titles ------------------------
st = pd.read_csv("pitcher_stints_full.csv")
st = st[(st.season == 2026) & st.FIP.notna() & (st.IP >= 20)].copy()
st["g"] = st.IP / 9
st["wr"] = wp(st.FIP.values)
st["fw"] = st.g * st.wr

fig = plt.figure(figsize=(7.9, 4.6))
ax = fig.add_axes([0.235, 0.05, 0.565, 0.84], projection="3d")
ipg = np.linspace(15, 200, 130); fpg = np.linspace(1.0, 6.8, 130)
IP, FP = np.meshgrid(ipg, fpg)
FW = np.where((IP / 9) * wp(FP) > 13, np.nan, (IP / 9) * wp(FP))
surfA = ax.plot_surface(IP, FP, FW, cmap="viridis", alpha=0.55, linewidth=0,
                        antialiased=True, rstride=2, cstride=2, norm=Normalize(0, 13))
ax.plot(ipg, np.full_like(ipg, FS), (ipg / 9) * 0.5, color="#B2182B", lw=2.0, ls="--", zorder=6)
for r, c in ROLE_C.items():
    d = st[st.role == r]
    ax.scatter(d.IP, d.FIP, d.fw, s=12, color=c, alpha=0.85, edgecolor="none",
               depthshade=False, zorder=10)
ax.set_xlabel("Innings pitched  (opportunity)", labelpad=4, fontsize=LABFS)
ax.set_ylabel("FIP  (quality)", labelpad=4, fontsize=LABFS)
ax.set_zlabel("FIP-W  (wins produced)", labelpad=2, fontsize=9.5)
ax.set_zlim(0, 13); ax.set_ylim(1.0, 6.8); ax.invert_yaxis()
ax.view_init(elev=ELEV, azim=AZIM); ax.set_box_aspect(BOXASP)
ax.tick_params(pad=1, labelsize=TICKFS)
for p in (ax.xaxis, ax.yaxis, ax.zaxis):
    p.pane.set_alpha(0.03)
ax.grid(alpha=0.18)
stat = {r: (int((st.role == r).sum()),
            float(np.average(st.loc[st.role == r, "wr"], weights=st.loc[st.role == r, "IP"])))
        for r in ROLE_C}
leg = [Line2D([], [], marker="o", ls="", color=c, markersize=6,
              label="%s  (n=%d, win rate .%03d)" % (r, stat[r][0], round(1000 * stat[r][1])))
       for r, c in ROLE_C.items()]
leg.append(Line2D([], [], color="#B2182B", lw=2.0, ls="--",
                  label="$F^{*}=%.2f$, the .500 ridge" % FS))
ax.legend(handles=leg, fontsize=7.8, frameon=False, loc="upper left",
          bbox_to_anchor=(-0.415, 1.02), handletextpad=0.5, borderpad=0.3)
fig.text(0.012, 0.62,
         "$F^{*}=%.2f$: the .500 ridge (dashed).\nHeight above it is wins above\nbreak-even." % FS,
         fontsize=8.0, color="#B2182B", va="top", linespacing=1.35)
fig.text(0.012, 0.44,
         "Closers (green) sit deep on the\nquality axis but shallow on\nopportunity: the leverage paradox.",
         fontsize=8.0, color="#1B7837", va="top", linespacing=1.35)
cb = fig.colorbar(surfA, ax=ax, shrink=0.52, aspect=15, pad=0.10)
cb.set_label("FIP-W", fontsize=8.5); cb.ax.tick_params(labelsize=7.5)

fig.suptitle("The FIP_WL output surface as a function of Pitcher Innings and FIP",
             fontsize=10.5, fontweight="bold", y=0.975)
fig.savefig("absfig1.pdf"); fig.savefig("absfig1.png", dpi=220); plt.close(fig)

# ---------------- panel B: the reallocation surface, no titles ---------------
P = pd.read_csv("repr_params_full.csv", index_col=0)
MIN_SAL = 0.78
SAL = {"Starter": 6.80, "Relief": 1.60, "Closer": 8.00}
SLOTS = {"Starter": 5, "Relief": 7, "Closer": 1}
OPT = {"Starter": 3.85, "Relief": 4.74, "Closer": 0.78}
BUD = sum(SAL[r] * SLOTS[r] for r in SLOTS)


def q(r, s):
    a = P.loc[r]
    return a.w_max - (a.w_max - a.w_min) * np.exp(-a.k * (np.maximum(s, MIN_SAL) - MIN_SAL))


def staff(rt, ct):
    stt = BUD - rt - ct
    ok = (stt >= 5 * MIN_SAL) & (rt >= 7 * MIN_SAL) & (ct >= MIN_SAL)
    return np.where(ok, 5 * q("Starter", stt / 5) + 7 * q("Relief", rt / 7) + q("Closer", ct), np.nan)


rg = np.linspace(7 * MIN_SAL, 36, 200); cg = np.linspace(MIN_SAL, 15, 200)
RG, CG = np.meshgrid(rg, cg); W = staff(RG, CG)
fig = plt.figure(figsize=PANEL)
ax = fig.add_subplot(111, projection="3d")
ax.plot_surface(RG, CG, W, cmap="viridis", alpha=0.62, linewidth=0, antialiased=True,
                rstride=2, cstride=2, norm=Normalize(np.nanmin(W), np.nanmax(W)))
ax.contour(RG, CG, W, levels=8, zdir="z", offset=70, cmap="viridis", linewidths=0.6, alpha=0.8)
pts = [(7 * SAL["Relief"], SAL["Closer"], "#B2182B", "o",
        "League average: \\$%.1fM relief, \\$%.1fM closer" % (7 * SAL["Relief"], SAL["Closer"])),
       (7 * OPT["Relief"], OPT["Closer"], "#1B7837", "^",
        "Optimum: \\$%.1fM relief, \\$%.1fM closer" % (7 * OPT["Relief"], OPT["Closer"]))]
zs = []
for rt, ct, col, mk, lab in pts:
    z = float(staff(np.array([rt]), np.array([ct]))[0]); zs.append(z)
    ax.plot([rt, rt], [ct, ct], [70, z], color=col, lw=1.0, ls=":", zorder=8)
    ax.scatter(rt, ct, z + 0.4, s=80, color=col, edgecolor="white", linewidth=1.2,
               marker=mk, depthshade=False, zorder=14)
ax.plot([pts[1][0]] * 2, [pts[1][1]] * 2, [zs[0], zs[1]], color="k", lw=2.2, zorder=15)
ax.text(pts[1][0] + 1.5, pts[1][1] + 1.0, (zs[0] + zs[1]) / 2, "$+6.8$", fontsize=9.5,
        fontweight="bold", zorder=16, path_effects=[pe.withStroke(linewidth=2.4, foreground="white")])
ax.set_xlabel("Bullpen \\$M", labelpad=4, fontsize=LABFS)
ax.set_ylabel("Closer \\$M", labelpad=4, fontsize=LABFS)
ax.set_zlabel("Staff FIP-W", labelpad=4, fontsize=LABFS)
ax.set_zlim(70, 92); ax.view_init(elev=ELEV, azim=AZIM); ax.set_box_aspect(BOXASP)
ax.tick_params(pad=1, labelsize=TICKFS)
for p in (ax.xaxis, ax.yaxis, ax.zaxis):
    p.pane.set_alpha(0.03)
ax.grid(alpha=0.18)
leg = [Line2D([], [], marker=m, ls="", color=c, markeredgecolor="white", markersize=7,
              label="%s  $\\rightarrow$  %.1f FIP-W" % (l, z))
       for (_, _, c, m, l), z in zip(pts, zs)]
ax.legend(handles=leg, fontsize=7.8, frameon=False, loc="upper left",
          bbox_to_anchor=(-0.415, 1.02), handletextpad=0.5, borderpad=0.3)
fig.suptitle("A 3-D Surface Plot to Optimize Pitching-Staff\nOutput per Dollar Across Roles",
             fontsize=10.5, fontweight="bold", y=0.985)
fig.subplots_adjust(left=0.02, right=0.94, top=0.94, bottom=0.05)
fig.savefig("absfig3.pdf"); fig.savefig("absfig3.png", dpi=220); plt.close(fig)



# ---------------- fig_marginal_sm (1).png : no panel titles -----------------
C2 = {"Relief": "#E8A33D", "Starter": "#2E6FB7", "Closer": "#2E9E6B"}
LBL = {"Relief": "Non-closing relief", "Starter": "Starter", "Closer": "Closer"}
SAL2 = {"Starter": 6.80, "Relief": 1.60, "Closer": 8.00}
OPT2 = {"Starter": 3.85, "Relief": 4.74, "Closer": 0.78}
LAM, RULE = 3.56, "#DCE1E6"
from matplotlib.patches import FancyArrowPatch


def q2(r, s_):
    a = P.loc[r]
    return a.w_max - (a.w_max - a.w_min) * np.exp(-a.k * (np.maximum(np.asarray(s_, float), 0.78) - 0.78))


def d2(r, s_):
    a = P.loc[r]
    return a.k * (a.w_max - a.w_min) * np.exp(-a.k * (np.maximum(np.asarray(s_, float), 0.78) - 0.78))


fig, ax = plt.subplots(1, 2, figsize=(8.0, 2.6))
fig.subplots_adjust(left=0.075, right=0.985, top=0.97, bottom=0.17, wspace=0.26)
sal = np.linspace(0.78, 11.0, 400)
for r in ["Starter", "Relief", "Closer"]:
    ax[0].plot(sal, q2(r, sal), color=C2[r], lw=1.9, label=LBL[r])
    ax[0].plot(SAL2[r], float(q2(r, SAL2[r])), "o", color=C2[r], ms=6, mec="white", mew=1.2)
    if abs(OPT2[r] - SAL2[r]) > 0.05:
        ax[0].add_patch(FancyArrowPatch((SAL2[r], float(q2(r, SAL2[r]))),
                                        (OPT2[r], float(q2(r, OPT2[r]))),
                                        arrowstyle="-|>", mutation_scale=8, lw=1.3, color=C2[r]))
    ax[0].plot(OPT2[r], float(q2(r, OPT2[r])), "D", color="white", ms=5, mec=C2[r], mew=1.5)
ax[0].set_xlabel("Salary per roster place  (\\$M)", fontsize=9.5)
ax[0].set_ylabel("FIP-W the place produces", fontsize=9.5)
ax[0].grid(color=RULE, lw=0.6); ax[0].set_axisbelow(True)
ax[0].legend(fontsize=8.2, frameon=False, loc="lower right", handlelength=1.3)
ax[0].tick_params(labelsize=8.5)

for r in ["Starter", "Relief", "Closer"]:
    y = 1 / d2(r, sal)
    ax[1].plot(sal, np.where(y <= 13, y, np.nan), color=C2[r], lw=1.9)
    ax[1].plot(SAL2[r], 1 / float(d2(r, SAL2[r])), "o", color=C2[r], ms=6, mec="white", mew=1.2)
    ax[1].plot(OPT2[r], 1 / float(d2(r, OPT2[r])), "D", color="white", ms=5, mec=C2[r], mew=1.5)
ax[1].axhline(LAM, color="#151A1F", lw=1.0, ls="--", alpha=0.75)
ax[1].set_xlabel("Salary per roster place  (\\$M)", fontsize=9.5)
ax[1].set_ylabel("\\$M per win-flip", fontsize=9.5)
ax[1].set_xlim(0, 11); ax[1].set_ylim(0, 13)
ax[1].grid(color=RULE, lw=0.6); ax[1].set_axisbelow(True)
ax[1].tick_params(labelsize=8.5)
fig.savefig("fig_marginal_sm (1).png", dpi=300)
plt.close(fig)
print("regenerated absfig1.pdf, absfig3.pdf, fig_marginal_sm (1).png -- headers baked in")
