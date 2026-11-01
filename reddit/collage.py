"""r/dataisbeautiful collage for ocean-depth: 3000 x 3750 px, light background. Numbers from data/results.json.

Label rules, checked geometrically below:
- each trench is a numbered dot; the number sits on land or on the paper outside the map (Natural Earth 1:50m land kept
  25 km clear of the coast) within 900 km, with a short leader, or else right beside its dot over abyssal sea that is not
  itself trench (every sample under it between 3,000 and 6,000 m deep); no number box, leader or dot overlaps another,
  and no leader passes over another trench's dot; the key below the map gives names and measured depths;
- ocean names sit inside their own ocean over deep sea only (every sample under the label deeper than 3,000 to 4,200 m,
  so they never cover shelves, ridges or trenches; the cramped Arctic only needs open sea) and clear of the trench dots.
Run: python3 reddit/collage.py
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figlib import *
from matplotlib.patches import Rectangle, Polygon as MPoly
import matplotlib.patheffects as pe
import shapely
from shapely.geometry import shape, box as sbox, LineString, Polygon
from shapely.ops import unary_union
from pyproj import Transformer

R = jload(f"{DATA}/results.json")
fmt = lambda v: f"{round(v):,}"
pc = lambda v, d=0: f"{v * 100:.{d}f}%"
CBG = "#F6F8F7"
RES = 0.075
LAT0, LAT1 = -78, 90
h, sea, lat, lon = lonlat_grid(RES)
img = relief_rgb(h, sea, lat, RES, exag=18)
LON0 = -160                     # centred on the Pacific: the cut runs at 20 E, through Europe and Africa, so every ocean is whole
out, ext, P = equal_earth(img, lat, lon, 3600, LAT0, LAT1, bg=tuple(np.array([246, 248, 247]) / 255), lon0=LON0)

fig = plt.figure(figsize=(12, 15), dpi=250, facecolor=CBG)
fig.text(.04, .975, "How deep is the sea?", fontproperties=DISP, fontsize=58, color=FG, va="top")
fig.text(.04, .912, f"The depth of the whole ocean floor, in colour, with shaded relief. The average sea floor lies {fmt(R['ocean']['mean'])} m down,\n"
         f"and {pc(R['ocean']['abyssal'])} of it is abyssal plain and hill between 3,000 and 6,000 m. The deepest place, the Challenger Deep\n"
         f"({R['mariana']['published']:,} m), would hide Everest with {R['mariana']['above_everest']:,} m to spare.",
         family=SER, fontsize=13.5, color=FG, va="top", linespacing=1.4)

ax = fig.add_axes([.005, .478, .99, .368]); ax.imshow(out, extent=ext, interpolation="lanczos", zorder=0); ax.axis("off")
ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
fw = Transformer.from_crs(4326, ee_crs(LON0), always_xy=True); iv = Transformer.from_crs(ee_crs(LON0), 4326, always_xy=True)
CUT = LON0 + 180                 # land is split at the cut meridian before projecting
halves = [sbox(-180, -90, CUT - 1e-3, 90), sbox(CUT + 1e-3, -90, 180, 90)]
LANDP = unary_union([shapely.make_valid(shapely.transform(shapely.segmentize(shape(f["geometry"]).buffer(0).intersection(hb), .5), lambda xy: np.column_stack(fw.transform(xy[:, 0], np.clip(xy[:, 1], LAT0, LAT1))))).buffer(0)
                     for f in jload(f"{GEO}/ne_50m_land.geojson")["features"] for hb in halves if shape(f["geometry"]).intersects(hb)])
# the map outline (Equal Earth edge between LAT0 and LAT1): anything outside it is paper
la = np.linspace(LAT0, LAT1, 200)
edge = [fw.transform(CUT - 1e-6, y) for y in la] + [fw.transform(CUT + 1e-6, y) for y in la[::-1]]
WORLD = Polygon(edge)
LAND_IN = LANDP.buffer(-25000); shapely.prepare(LAND_IN); shapely.prepare(WORLD)
PAPER = sbox(*ext[:1], ext[2], ext[1], ext[3]).difference(WORLD.buffer(60000)) if False else None
XL, YL = ax.get_xlim(), ax.get_ylim()
FRAME = sbox(XL[0], YL[0], XL[1], YL[1])
halo = [pe.withStroke(linewidth=3, foreground="white")]
fig.canvas.draw(); rend = fig.canvas.get_renderer(); inv = ax.transData.inverted()
TR = R["tr"]
# trenches: a numbered dot each, the number placed on land or paper close by (with a short leader) where there is room,
# otherwise right beside the dot over abyssal sea that is not itself trench (no cell deeper than 6,000 m under it);
# the key below the map gives names and measured depths
ORDER = ["mariana", "tonga", "philippine", "kermadec", "kuril", "puertorico", "southsandwich", "atacama", "java", "molloy"]
TP = {k: P(TR[k]["lon"], TR[k]["lat"]) for k in ORDER}


def depth_at(xs, ys):
    lo_, la_ = iv.transform(xs, ys)
    ri = np.clip(((lat[0] + RES / 2 - la_) / RES).astype(int), 0, len(lat) - 1); ci = np.clip(((lo_ + 180) / RES).astype(int), 0, len(lon) - 1)
    return np.where(sea[ri, ci], -h[ri, ci], -1)


placed = []                       # (box, leader or None)
DOTS = [shapely.Point(p).buffer(90000) for p in TP.values()]
for n, k in enumerate(ORDER, 1):
    tx = ax.text(0, 0, str(n), ha="center", va="center", fontsize=8.5, weight="bold", color="#2B0F33", family=MONO, zorder=7,
                 bbox=dict(boxstyle="circle,pad=.18", fc=(1, 1, 1, .95), ec="#2B0F33", lw=.6))
    fig.canvas.draw(); bb = tx.get_bbox_patch().get_window_extent(rend)
    (x0, y0), (x1, y1) = inv.transform([[bb.x0, bb.y0], [bb.x1, bb.y1]]); w, hh = x1 - x0, y1 - y0
    FX, FY = TP[k]; best = None
    for rad in np.arange(w * .9, 2.6e6, 60000):
        for ang in np.linspace(0, 2 * np.pi, 48, endpoint=False):
            gx, gy = FX + rad * np.cos(ang), FY + rad * np.sin(ang)
            bx = sbox(gx - w / 2, gy - hh / 2, gx + w / 2, gy + hh / 2)
            if not FRAME.contains(bx): continue
            if any(bx.buffer(20000).intersects(o[0]) or (o[1] is not None and o[1].intersects(bx)) for o in placed): continue
            if any(bx.intersects(dt) for dt in DOTS): continue
            ok_land = LAND_IN.contains(bx) or not bx.buffer(30000).intersects(WORLD)
            if ok_land:
                ln = LineString([(FX, FY), (gx, gy)]) if rad > w * 1.3 else None
                if ln is not None and any(ln.intersects(o[0]) or (o[1] is not None and ln.intersects(o[1])) for o in placed): continue
                if ln is not None and any(ln.distance(shapely.Point(TP[k2])) < 60000 for k2 in TP if k2 != k): continue
                cand = (0 if rad <= 9e5 else 2, rad, gx, gy, bx, ln, "land or paper")
            elif rad < w * 1.25:
                xs, ys = np.meshgrid(np.linspace(gx - w / 2, gx + w / 2, 5), np.linspace(gy - hh / 2, gy + hh / 2, 5))
                dd = depth_at(xs.ravel(), ys.ravel())
                if dd.min() < 3000 or dd.max() > 6000: continue
                cand = (1, rad, gx, gy, bx, None, "abyssal sea beside the dot")
            else:
                continue
            if best is None or cand[:2] < best[:2]: best = cand
        if best is not None and best[0] == 0: break
    if best is None: print('debug', k, FX, FY, w, hh, FRAME.bounds)
    assert best, ("no place for", k)
    _, rad, gx, gy, bx, ln, where = best
    print(f"{n:2d} {k:14s} on {where} ({rad / 1e3:.0f} km)")
    tx.set_position((gx, gy))
    if ln is not None: ax.plot(*LineString([(FX, FY), (gx - (gx - FX) * (w / 2) / max(rad, 1), gy - (gy - FY) * (w / 2) / max(rad, 1))]).xy, color="#2B0F33", lw=.7, zorder=5)
    placed.append((bx, ln))
for k in ORDER: ax.plot([TP[k][0]], [TP[k][1]], "o", ms=4.4, mfc="#5A2D63", mec="white", mew=1, zorder=6)
for i, (bx, ln) in enumerate(placed):
    for j, (bx2, ln2) in enumerate(placed):
        if i != j: assert not bx.intersects(bx2) and (ln2 is None or not ln2.intersects(bx)) and (ln is None or ln2 is None or not ln.intersects(ln2)), (ORDER[i], ORDER[j])
print("trench numbers placed:", len(placed))

# ocean names over abyssal sea only
# name, hint, minimum depth under the label, and the box of longitude and latitude its centre must fall in
OCN = [("PACIFIC OCEAN", (-150, 14), 4200, (-180, -60, 180, 50)), ("ATLANTIC\nOCEAN", (-45, 32), 3000, (-75, -55, 15, 65)),
       ("INDIAN\nOCEAN", (80, -30), 3500, (25, -55, 115, 25)), ("SOUTHERN OCEAN", (-120, -62), 3500, (-180, -75, 180, -58)),
       ("ARCTIC OCEAN", (-150, 84), 1, (-180, 70, 180, 90))]
oplaced = []
for t, (lo_, la_), thr, (bx0, by0, bx1, by1) in OCN:
    tx = ax.text(0, 0, t, ha="center", va="center", fontsize=8 if t.startswith("ARCTIC") else 10.5, color="#0E2A47", family=SER, style="italic", linespacing=1.0, zorder=4, path_effects=[pe.withStroke(linewidth=2.2, foreground="white")])
    fig.canvas.draw(); bb = tx.get_window_extent(rend)
    (x0, y0), (x1, y1) = inv.transform([[bb.x0, bb.y0], [bb.x1, bb.y1]]); w, hh = x1 - x0, y1 - y0
    HX, HY = P(lo_, la_); best = None
    for gx in np.linspace(HX - 5e6, HX + 5e6, 101):
        for gy in np.linspace(HY - 3e6, HY + 3e6, 61):
            d = np.hypot(gx - HX, gy - HY)
            if best is not None and d >= best[0]: continue
            bx = sbox(gx - w / 2, gy - hh / 2, gx + w / 2, gy + hh / 2)
            if not FRAME.contains(bx) or not WORLD.contains(bx): continue
            clo, cla = iv.transform(gx, gy)
            if not (bx0 <= clo <= bx1 and by0 <= cla <= by1): continue
            xs, ys = np.meshgrid(np.linspace(gx - w / 2, gx + w / 2, 14), np.linspace(gy - hh / 2, gy + hh / 2, 5))
            if depth_at(xs.ravel(), ys.ravel()).min() < thr: continue
            if any(np.hypot(gx - X, gy - Y) < 4e5 + w / 2 for X, Y in TP.values()): continue
            if any(bx.buffer(1e5).intersects(o[0]) or (o[1] is not None and o[1].intersects(bx)) for o in placed): continue
            best = (d, gx, gy, bx)
    assert best, ("no abyssal place for", t)
    tx.set_position(best[1:3]); oplaced.append(best[3])
    print(f"{t:15s} placed {best[0] / 1e3:5.0f} km from its hint")
print("ocean names over abyssal sea:", len(oplaced))

# legend under the map
lg = fig.add_axes([.17, .446, .66, .022]); lg.axis("off")
T = LEG_T; n = len(T) - 1
for i in range(n):
    for k in range(10):
        v = T[i] + (T[i + 1] - T[i]) * k / 10
        lg.add_patch(Rectangle((i + k / 10, .45), .1001, .55, fc=deep_rgb(v), ec="none"))
lg.add_patch(Rectangle((0, .45), n, .55, fc="none", ec=MUT, lw=.6))
for i, t in enumerate(T): lg.text(i, .3, f"{t:,}", ha="center", va="top", fontsize=9.5)
lg.add_patch(Rectangle((n + .9, .45), .6, .55, fc=land_rgb(300), ec=MUT, lw=.6)); lg.text(n + 1.2, .3, "land", ha="center", va="top", fontsize=9.5)
lg.set_xlim(-.4, n + 1.8); lg.set_ylim(-.6, 1.4)
fig.text(.5, .472, "Depth below sea level, metres (colour steps not to scale) · Equal Earth projection centred on 160° W",
         ha="center", fontsize=10.2, color=MUT)

# key to the numbered trenches
nm = lambda t: (t["deep"] + ", " if t["deep"] != "deepest point" and not t["name"].startswith(t["deep"]) else "") + t["name"].replace(", Fram Strait", " (Arctic)").replace("Peru-Chile (Atacama)", "Atacama").replace(" (Sunda)", "")
for n, k in enumerate(ORDER, 1):
    t = TR[k]; col, row = (n - 1) // 4, (n - 1) % 4
    x, y = .04 + col * .33, .424 - row * .0145
    fig.text(x, y, f"{n}", fontsize=9.2, weight="bold", color="#2B0F33", va="top")
    fig.text(x + .018, y, f"{nm(t)}  {t['published']:,} m", fontsize=9.2, color=FG, va="top")
fig.text(.70, .424 - 2 * .0145, "Measured depths from sonar or pressure surveys\n(sources below); the 10 km map is shallower.", fontsize=8.6, color=MUT, va="top", linespacing=1.4)

nums = [(f"{fmt(R['ocean']['mean'])} m", NAVY, f"average depth of the sea\nfloor (median {fmt(R['ocean']['median'])} m)"),
        (pc(R["ocean"]["abyssal"]), ICE, "of the sea floor is abyssal,\n3,000 to 6,000 m down"),
        (pc(R["ocean"]["shelf"], 1), KELP, "is shallow continental\nshelf, under 200 m"),
        (f"{R['seabed2030']['pct']}%", CORAL, f"mapped to modern standards\n(Seabed 2030, {R['seabed2030']['year']})")]
for i, (big, col, small) in enumerate(nums):
    x = .04 + i * .24
    fig.text(x, .364, big, fontproperties=DISP, fontsize=36, color=col, va="top")
    fig.text(x, .326, small, fontsize=10.6, color=FG, va="top", linespacing=1.4)

# panel 1: Mariana profile with Everest
a1 = fig.add_axes([.08, .125, .5, .13]); a1.set_facecolor(CBG)
M = R["mariana"]; pr = np.array(M["prof"]["h"]); x = np.arange(len(pr)); D, ev = M["published"], M["everest"]
for k in range(60):
    a_, b_ = -11500 * k / 60, -11500 * (k + 1) / 60; a1.axhspan(b_, a_, color=deep_rgb(-(a_ + b_) / 2), lw=0, zorder=0)
a1.fill_between(x, pr, -11800, color="#E9E3D4", zorder=2); a1.plot(x, pr, color=FG, lw=1.1, zorder=3)
xd = int(np.argmin(pr)); wE = 70
a1.add_patch(MPoly([(xd - wE, -D), (xd - wE * .35, -D + ev * .62), (xd - wE * .12, -D + ev * .78), (xd, -D + ev), (xd + wE * .3, -D + ev * .7), (xd + wE, -D)], closed=True, fc=(1, 1, 1, .9), ec=CORAL, lw=1.3, zorder=4))
a1.axhline(-D, color=CORAL, ls="--", lw=1, zorder=4); a1.axhline(0, color=FG, lw=1)
a1.text(xd + 14, -D + ev + 200, f"Everest, {ev:,} m tall:\nsummit {D - ev:,} m down", fontsize=9.5, zorder=5, va="bottom", path_effects=halo)
a1.text(len(pr) - 5, -D + 200, f"Challenger Deep {D:,} m", fontsize=9.5, ha="right", zorder=5, path_effects=halo)
a1.set_xlim(0, len(pr) - 1); a1.set_ylim(-11800, 500)
a1.set_yticks(range(-10000, 1, 2000), [f"{-v // 1000}k" if v else "0" for v in range(-10000, 1, 2000)])
a1.set_xlabel("km south from 14.5° N along 142.6° E (10 km grid)", fontsize=9.5); a1.set_ylabel("metres down", fontsize=9.5)
style(a1, grid=False); a1.tick_params(labelsize=9)
a1.set_title("A slice through the Mariana Trench, with Everest for scale", loc="left", fontsize=12, pad=10)

# panel 2: depth bands
a2 = fig.add_axes([.73, .125, .23, .13]); a2.set_facecolor(CBG)
B = R["bands"]; yb = np.arange(len(B))[::-1]
a2.barh(yb, [b["share"] * 100 for b in B], color=[deep_rgb((b["lo"] + (b["hi"] or 9000)) / 2) for b in B], height=.75, edgecolor="#00000025")
a2.set_yticks(yb, [f"{b['lo'] // 1000 if b['lo'] >= 1000 else b['lo']}{'k' if b['lo'] >= 1000 else ''} to {(b['hi'] // 1000) if b['hi'] >= 1000 else b['hi']}{'k' if b['hi'] >= 1000 else ''}" if b["hi"] else f"> {b['lo'] // 1000}k" for b in B], fontsize=9)
for yy, b in zip(yb, B): a2.text(b["share"] * 100 + .6, yy, f"{b['share'] * 100:.{2 if b['share'] < .01 else 1}f}%", va="center", fontsize=8.8)
a2.set_xlim(0, 42); style(a2); a2.tick_params(axis="x", labelsize=8.5); a2.set_xlabel("% of the sea floor", fontsize=9.5)
a2.set_title("Share of the sea floor\nat each depth (m)", loc="left", fontsize=12, pad=10)

fig.text(.04, .012, "Sources: AWS Terrain Tiles (Mapzen Terrarium; under the sea ETOPO1, GEBCO and SRTM15+; attribution at github.com/tilezen/joerd), zoom 4 grid of about\n"
         "10 km, every cell weighted by its true area; ETOPO10 north of 85° N. Measured depths: Greenaway et al. 2021 (Challenger Deep); Bongiovanni, Stewart and\n"
         "Jamieson 2022 (Horizon, Brownson, Meteor, Java, Molloy); Wikipedia, Oceanic trench (Emden, Scholl, Kuril, Richards). Mapping share: Seabed 2030 / GEBCO.\n"
         "Land: Natural Earth. Everest 8,849 m (2020 survey). A 10 km grid smooths trenches, so the profile is shallower than the measured Deep.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/ocean-depth",
         fontsize=8.3, color=MUT, linespacing=1.45, va="bottom")
outp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "how_deep_is_the_sea.png")
fig.savefig(outp, facecolor=CBG, dpi=250)
print("ok", outp)
