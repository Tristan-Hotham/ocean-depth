"""Step 7. Figures for the blog and the paper (release/blog/b_*.png, used by both), and header.png (1200 x 630).
Every number drawn comes from data/results.json.
Run: python3 code/07_figures.py
"""
from figlib import *
from matplotlib.patches import Rectangle, Polygon as MPoly

R = jload(f"{DATA}/results.json")
BL = os.path.join(ROOT, "release", "blog"); os.makedirs(BL, exist_ok=True)
fmt = lambda v: f"{round(v):,}"
pc = lambda v, d=0: f"{v * 100:.{d}f}%"


def save(fig, name):
    fig.savefig(f"{BL}/b_{name}.png", dpi=200, facecolor=fig.get_facecolor())
    plt.close(fig)


def depth_legend(ax, x0, y0, w, hh, fs=9):
    T = LEG_T; n = len(T) - 1
    for i in range(n):
        for k in range(8):
            v = T[i] + (T[i + 1] - T[i]) * k / 8
            ax.add_patch(Rectangle((x0 + w * (i + k / 8) / n, y0), w / n / 8 + 1e-4, hh, transform=ax.transAxes, fc=deep_rgb(v), ec="none", clip_on=False))
    ax.add_patch(Rectangle((x0, y0), w, hh, transform=ax.transAxes, fc="none", ec=MUT, lw=.5, clip_on=False))
    for i, t in enumerate(T):
        ax.text(x0 + w * i / n, y0 - hh * .5, f"{t:,}" if t < 1000 or t == 1000 else f"{t // 1000}k", transform=ax.transAxes, ha="center", va="top", fontsize=fs, color=FG)


RES = 0.075
h, sea, lat, lon = lonlat_grid(RES)
img = relief_rgb(h, sea, lat, RES, exag=16)
PAPER_BG = tuple(np.array([243, 246, 245]) / 255)

# ---- 1. world ocean depth ----
out, ext, P = equal_earth(img, lat, lon, 3000, -78, 86, bg=PAPER_BG)
fig = plt.figure(figsize=(12, 6.4), facecolor=BG)
ax = fig.add_axes([0, .13, 1, .87]); ax.imshow(out, extent=ext, interpolation="lanczos"); ax.axis("off")
for t in R["trenches"]:
    if t["key"] in ("mariana", "tonga", "puertorico", "java", "factorian", "molloy"):
        x, y = P(t["lon"], t["lat"]); ax.plot(x, y, "o", ms=5, mfc=PLUM, mec="white", mew=1.2)
lg = fig.add_axes([0, 0, 1, .12]); lg.axis("off")
depth_legend(lg, .2, .4, .6, .2)
lg.text(.5, .98, "Depth below sea level, metres (tints, steps not to scale) with shaded relief · dots: deepest known place in each ocean", ha="center", va="top", fontsize=10, color=FG, transform=lg.transAxes)
save(fig, "world_depth")

# ---- 2. depth bands ----
B = R["bands"]
fig, ax = plt.subplots(figsize=(10, 5.2), facecolor=BG); ax.set_facecolor(BG)
y = np.arange(len(B))[::-1]
labs = [f"{b['lo']:,} to {b['hi']:,} m" if b["hi"] else f"deeper than {b['lo']:,} m" for b in B]
ax.barh(y, [b["share"] * 100 for b in B], color=[deep_rgb((b["lo"] + (b["hi"] or 9000)) / 2) for b in B], edgecolor="#00000030", height=.72)
ax.set_yticks(y, labs)
for yy, b in zip(y, B): ax.text(b["share"] * 100 + .5, yy, f"{b['share'] * 100:.{2 if b['share'] < .01 else 1}f}%", va="center", fontsize=10)
zones = [(0, 0, "shelf"), (1, 3, "slope and rise"), (4, 6, "abyssal"), (7, 8, "hadal")]
for a, b_, nm in zones:
    ax.annotate("", xy=(37, y[a] + .38), xytext=(37, y[b_] - .38), arrowprops=dict(arrowstyle="-", color=MUT, lw=1.2))
    ax.text(37.6, (y[a] + y[b_]) / 2, nm, va="center", fontsize=10, color=MUT)
ax.set_xlim(0, 45); style(ax); ax.set_xlabel("share of the ocean floor (%)")
ax.set_title(f"How much of the sea floor lies at each depth: {pc(R['ocean']['abyssal'])} is abyssal (3,000 to 6,000 m)", loc="left", fontsize=12)
fig.tight_layout(); save(fig, "depth_bands")

# ---- 3. the two levels of the Earth ----
hs = np.array(R["earth"]["hist"])
fig, ax = plt.subplots(figsize=(10, 4.8), facecolor=BG); ax.set_facecolor(BG)
ax.bar(hs[:, 0] + 125, hs[:, 1] * 100, width=230, color=[deep_rgb(-m - 125) if m < 0 else np.array([215, 199, 163]) / 255 for m in hs[:, 0]])
ax.axvline(0, color=FG, lw=1)
pd_, ph = R["earth"]["peak_deep"], R["earth"]["peak_high"]
ax.annotate("the ocean floor,\n4 to 5 km down", (pd_[0] + 125, pd_[2] * 100), xytext=(-8200, 7.5), fontsize=10.5, arrowprops=dict(arrowstyle="-", color=MUT, lw=.8))
ax.annotate("lowland, just\nabove the sea", (ph[0] + 125, ph[2] * 100), xytext=(2200, 8.5), fontsize=10.5, arrowprops=dict(arrowstyle="-", color=MUT, lw=.8))
ax.set_xlim(-11000, 9000); ax.set_ylim(0, 11); style(ax, axis="y")
ax.set_xticks(range(-10000, 9000, 2000), [f"{v // 1000}k" for v in range(-10000, 9000, 2000)])
ax.set_xlabel("metres below (left) and above (right) sea level"); ax.set_ylabel("% of the Earth's surface per 250 m")
ax.set_title("The two levels of the Earth: continents and ocean floor", loc="left", fontsize=12)
fig.tight_layout(); save(fig, "two_levels")

# ---- 4. oceans ----
OC = R["oceans"]
fig, ax = plt.subplots(figsize=(10, 4.6), facecolor=BG); ax.set_facecolor(BG)
y = np.arange(len(OC))[::-1]
ax.barh(y, [o["mean"] for o in OC], color=[deep_rgb(o["mean"]) for o in OC], height=.6, label="mean depth (10 km grid)")
ax.scatter([o["pub"] for o in OC], y, s=60, color=PLUM, edgecolor="white", zorder=3, label="deepest known place (sonar surveys)")
for yy, o in zip(y, OC):
    ax.text(o["mean"] - 80, yy, f"{fmt(o['mean'])} m", va="center", ha="right", fontsize=10, color="white")
    ax.text(o["pub"] + 180, yy, f"{o['pub_name']}, {fmt(o['pub'])} m", va="center", fontsize=9.5)
ax.set_yticks(y, [o["name"] for o in OC]); ax.set_xlim(0, 14500); style(ax)
ax.set_xlabel("metres below sea level"); ax.legend(frameon=False, loc="lower right", fontsize=9.5)
ax.set_title("The five oceans: average depth and deepest place", loc="left", fontsize=12)
fig.tight_layout(); save(fig, "oceans")

# ---- 5. trenches: measured and grid ----
T = R["trenches"]
fig, ax = plt.subplots(figsize=(10, 6.2), facecolor=BG); ax.set_facecolor(BG)
y = np.arange(len(T))[::-1]
nm = lambda t: t["name"] if t["deep"] == "deepest point" or t["name"].startswith(t["deep"]) else f"{t['deep']}, {t['name']}".replace(" Trench, south of 60° S", " (S of 60°)").replace(" Trench", "")
for yy, t in zip(y, T):
    ax.plot([t["grid"], t["published"]], [yy, yy], color=MUT, lw=1.3, zorder=1)
ax.scatter([t["grid"] for t in T], y, s=55, facecolor=BG, edgecolor=ICE, lw=2, zorder=2, label="deepest 10 km grid cell")
ax.scatter([t["published"] for t in T], y, s=60, color=PLUM, edgecolor="white", zorder=3, label="measured depth")
ax.set_yticks(y, [nm(t) for t in T], fontsize=9.5); ax.set_xlim(5000, 11200); style(ax)
ax.set_xticks(range(5000, 11001, 1000), [f"{v:,}" for v in range(5000, 11001, 1000)])
ax.set_xlabel("metres below sea level"); ax.legend(frameon=False, loc="lower right")
ax.set_title("The deepest places: measured depth and the 10 km grid", loc="left", fontsize=12)
fig.tight_layout(); save(fig, "trenches")


# ---- 6. Mariana profile with Everest ----
def profile(ax, fs=10):
    M = R["mariana"]; pr = np.array(M["prof"]["h"]); x = np.arange(len(pr))
    D, ev = M["published"], M["everest"]
    for k in range(60):
        a, b = -11500 * k / 60, -11500 * (k + 1) / 60
        ax.axhspan(b, a, color=deep_rgb(-(a + b) / 2), lw=0, zorder=0)
    ax.fill_between(x, pr, -11800, color="#E9E3D4", zorder=2); ax.plot(x, pr, color=FG, lw=1.2, zorder=3)
    xd = int(np.argmin(pr)); wE = 70
    ax.add_patch(MPoly([(xd - wE, -D), (xd - wE * .35, -D + ev * .62), (xd - wE * .12, -D + ev * .78), (xd, -D + ev), (xd + wE * .3, -D + ev * .7), (xd + wE, -D)],
                       closed=True, fc=(1, 1, 1, .88), ec=CORAL, lw=1.4, zorder=4))
    ax.axhline(-D, color=CORAL, ls="--", lw=1.1, zorder=4)
    ax.text(xd + 14, -D + ev + 150, f"Everest ({ev:,} m): summit\n{D - ev:,} m below the surface", fontsize=fs, zorder=5, va="bottom")
    ax.text(len(pr) - 5, -D + 160, f"Challenger Deep, {D:,} m (measured)", fontsize=fs, ha="right", zorder=5, color=FG)
    ax.axhline(0, color=FG, lw=1)
    ax.set_xlim(0, len(pr) - 1); ax.set_ylim(-11800, 600)
    ax.set_yticks(range(-10000, 1, 2000), [f"{-v:,}" for v in range(-10000, 1, 2000)])
    ax.set_xlabel("km south from 14.5° N along 142.6° E", fontsize=fs); ax.set_ylabel("metres below sea level", fontsize=fs)
    style(ax, grid=False)


fig, ax = plt.subplots(figsize=(10, 4.8), facecolor=BG); profile(ax)
ax.set_title("A slice through the Mariana Trench (10 km grid), with Everest for scale", loc="left", fontsize=12)
fig.tight_layout(); save(fig, "mariana")

# ---- 7. national waters ----
Z = R["eez"]["top"][:10][::-1]
fig, axs = plt.subplots(1, 2, figsize=(11, 4.8), facecolor=BG, gridspec_kw=dict(width_ratios=[.8, 1.6]))
e = R["eez"]
axs[0].bar([0, 1], [e["national_share"] * 100, e["high_share"] * 100], color=[KELP, ICE], width=.6)
for i, (v, m) in enumerate([(e["national_share"], e["national_mean"]), (e["high_share"], e["high_mean"])]):
    axs[0].text(i, v * 100 + 1.5, f"{v * 100:.0f}% of the sea\nmean {m:,} m", ha="center", fontsize=9.5)
axs[0].set_xticks([0, 1], ["national waters", "high seas"]); axs[0].set_ylim(0, 80); axs[0].set_yticks([])
axs[0].set_title("Whose sea?", loc="left", fontsize=12)
axs[1].barh(range(len(Z)), [z["max"] for z in Z], color=[deep_rgb(z["max"]) for z in Z], height=.65)
axs[1].set_yticks(range(len(Z)), [z["name"].replace(" EEZ", "").replace("United States", "US") for z in Z], fontsize=9.5)
for i, z in enumerate(Z): axs[1].text(z["max"] + 100, i, f"{fmt(z['max'])} m", va="center", fontsize=9.5)
axs[1].set_xlim(0, 12500); axs[1].set_title("Deepest 10 km cell in each Exclusive Economic Zone", loc="left", fontsize=12)
for a in axs: style(a); a.set_facecolor(BG)
fig.tight_layout(); save(fig, "eez")

# ---- header 1200 x 630 ----
outh, exth, Ph = equal_earth(img, lat, lon, 1600, -70, 84, bg=PAPER_BG)
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.32, .05, .68, .9]); ax.imshow(outh, extent=exth, interpolation="lanczos"); ax.axis("off")
fig.text(.035, .86, "How deep\nis the sea?", fontproperties=DISP, fontsize=46, color=FG, va="top", linespacing=.95)
fig.text(.035, .50, f"The average sea floor lies\n{fmt(R['ocean']['mean'])} m down. The deepest\nplace, {R['mariana']['published']:,} m, would\nhide Everest with {R['mariana']['above_everest']:,} m\nto spare.", fontsize=15, family=SER, color=FG, va="top", linespacing=1.35)
fig.text(.035, .07, "maps.tristanhotham.com/ocean-depth", fontsize=10.5, color=MUT)
fig.patches.append(Rectangle((0, 0), .012, 1, transform=fig.transFigure, fc=NAVY))
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG); plt.close(fig)
print("figures done", sorted(os.listdir(BL)))
