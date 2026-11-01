"""Shared drawing helpers for the figures, the header and the collage: fonts, the page's depth palette, and a shaded
relief world image built from the zoom 4 grid (resampled from Web Mercator to longitude and latitude, the polar caps from
ETOPO10) and reprojected to Equal Earth."""
import os, sys
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    fm.fontManager.addfont(os.path.join(FONTS, f))
DISP = fm.FontProperties(fname=os.path.join(FONTS, "FrauncesVar.ttf"), weight=900)
SER, MONO = "Source Serif 4", "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 11})
BG, FG, MUT, RULE, PAPER = "#F3F6F5", "#14222E", "#56656F", "#D3DEDF", "#FBFCFC"
NAVY, KELP, ICE, CORAL, PLUM, SAND = "#1F4E79", "#3D7A6A", "#2B5F8A", "#C0533A", "#5A2D63", "#D7C7A3"
# depth (positive down) -> colour, as on the page
DEEP = [(0, (226, 243, 245)), (100, (204, 234, 240)), (200, (182, 222, 234)), (500, (152, 204, 225)), (1000, (124, 184, 215)), (2000, (94, 158, 202)), (3000, (68, 130, 187)),
        (4000, (47, 102, 167)), (5000, (34, 76, 141)), (6000, (30, 54, 113)), (7000, (40, 39, 93)), (8000, (56, 31, 85)), (9000, (74, 27, 81)), (11000, (98, 25, 84))]
LANDC = [(0, (236, 232, 222)), (500, (228, 222, 207)), (1500, (214, 205, 187)), (3000, (200, 190, 174)), (5000, (228, 226, 224)), (7000, (246, 246, 246))]
LEG_T = [0, 200, 500, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 11000]


def ramp(stops, x):
    x = np.asarray(x, float); xs = [s[0] for s in stops]; cs = np.array([s[1] for s in stops]) / 255
    return np.stack([np.interp(x, xs, cs[:, k]) for k in range(3)], axis=-1).astype(np.float32)


deep_rgb = lambda d: ramp(DEEP, d)
land_rgb = lambda h: ramp(LANDC, h)
hexd = lambda d: matplotlib.colors.to_hex(deep_rgb(d))


def style(ax, grid=True, axis="x"):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(MUT)
    ax.tick_params(colors=FG, labelsize=10)
    if grid: ax.grid(axis=axis, color=RULE, lw=.8); ax.set_axisbelow(True)


def lonlat_grid(res=0.075):
    """Heights (negative = depth) and a sea mask on a regular longitude/latitude grid (cached). Sea is the study's
    water mask (share of the cell that is sea >= 0.5); north of 85.05 N all sea, south of 85.05 S all land (ETOPO10)."""
    fn = f"{WORK}/lonlat_{res}.npz"
    if os.path.exists(fn):
        z = np.load(fn); return z["h"], z["sea"], z["lat"], z["lon"]
    E = np.load(f"{WORK}/elev.npy").astype(np.float32); Wt = np.load(f"{WORK}/water.npy")
    nx, ny = int(round(360 / res)), int(round(180 / res))
    lon = -180 + (np.arange(nx) + .5) * res; lat = 90 - (np.arange(ny) + .5) * res
    r, _ = rc_of(0, np.clip(lat, -MERC_LAT + 1e-6, MERC_LAT - 1e-6)); r = r - .5
    c = (lon + 180) / 360 * N - .5
    r0 = np.clip(np.floor(r).astype(int), 0, N - 2); ty = np.clip(r - r0, 0, 1)[:, None]
    c0 = np.floor(c).astype(int) % N; c1 = (c0 + 1) % N; tx = (c - np.floor(c))[None, :].astype(np.float32)
    h = np.empty((ny, nx), np.float32); sea = np.empty((ny, nx), bool)
    rn = np.clip(np.round(r).astype(int), 0, N - 1); cn = np.round(c).astype(int) % N
    for a in range(0, ny, 400):
        b = slice(a, a + 400); R0, T = r0[b], ty[b]
        h[b] = (E[R0][:, c0] * (1 - tx) + E[R0][:, c1] * tx) * (1 - T) + (E[R0 + 1][:, c0] * (1 - tx) + E[R0 + 1][:, c1] * tx) * T
        sea[b] = Wt[rn[b]][:, cn] >= .5
    e10 = np.fromfile(ETOPO10, "<i2").reshape(1081, 2161)[:, :2160].astype(np.float32)
    pol = np.abs(lat) > MERC_LAT - .05
    ri = np.clip(np.round((90 - lat[pol]) * 6).astype(int), 0, 1080); ci = np.clip(np.floor((lon + 180) * 6).astype(int), 0, 2159)
    h[pol] = e10[ri][:, ci]
    sea[pol] = (lat[pol] > 0)[:, None] & (h[pol] < 0)
    np.savez(fn, h=h, sea=sea, lat=lat, lon=lon)
    return h, sea, lat, lon


def hillshade(h, lat, res, exag=14.0, az=315, alt=42):
    dy = res * 111320.0; dx = dy * np.cos(np.radians(lat))[:, None]
    gy, gx = np.gradient(h.astype(np.float32))
    sx = gx / dx * exag; sy = -gy / dy * exag          # rows run north to south
    slope = np.arctan(np.hypot(sx, sy)); aspect = np.arctan2(sy, -sx)
    azm = np.radians(360 - az + 90); zen = np.radians(90 - alt)
    hs = np.cos(zen) * np.cos(slope) + np.sin(zen) * np.sin(slope) * np.cos(azm - aspect)
    return np.clip(hs, 0, 1).astype(np.float32)


def relief_rgb(h, sea, lat, res, exag=14.0, land_k=.5):
    """RGB image (0..1): depth tints times strong shading at sea; quiet sand-coloured, lightly shaded land."""
    hs = hillshade(np.where(sea, h, h * land_k), lat, res, exag)
    img = np.empty(h.shape + (3,), np.float32)
    img[sea] = deep_rgb(np.maximum(-h[sea], 0))
    img[~sea] = land_rgb(np.maximum(h[~sea], 0))
    f = np.where(sea, .55 + .6 * hs, .74 + .34 * hs)[..., None]
    return np.clip(img * f, 0, 1)


def ee_crs(lon0=0):
    return "EPSG:8857" if lon0 == 0 else f"+proj=eqearth +lon_0={lon0} +datum=WGS84 +units=m +no_defs"


def equal_earth(img, lat, lon, width, lat_min=-90, lat_max=90, bg=(1, 1, 1), lon0=0):
    """Reproject a lon/lat image to Equal Earth (EPSG 8857, or centred on lon0). Returns RGBA, extent (x0, x1, y0, y1)
    and a lon/lat -> x/y function."""
    from pyproj import Transformer
    fwd = Transformer.from_crs(4326, ee_crs(lon0), always_xy=True); inv = Transformer.from_crs(ee_crs(lon0), 4326, always_xy=True)
    X0, _ = fwd.transform(lon0 - 180 + 1e-9, 0); X1, _ = fwd.transform(lon0 + 180 - 1e-9, 0)
    _, Y0 = fwd.transform(lon0, lat_min); _, Y1 = fwd.transform(lon0, lat_max)
    height = int(round(width * (Y1 - Y0) / (X1 - X0)))
    xs = np.linspace(X0, X1, width); ys = np.linspace(Y1, Y0, height)
    out = np.zeros((height, width, 4), np.float32)
    res = lat[0] - lat[1]
    for a in range(0, height, 300):
        XX, YY = np.meshgrid(xs, ys[a:a + 300])
        lo, la = inv.transform(XX, YY)
        ok = np.isfinite(lo) & np.isfinite(la) & (np.abs(lo) <= 180)
        xb, _ = fwd.transform(np.where(ok, lo, 0), np.where(ok, la, 0))
        ok &= np.abs(xb - XX) < 1000
        lo = ((lo + 180) % 360) - 180
        ri = np.clip(((lat[0] + res / 2 - la) / res).astype(int), 0, len(lat) - 1)
        ci = np.clip(((lo + 180) / res).astype(int), 0, len(lon) - 1)
        blk = img[ri, ci]; blk[~ok] = bg
        out[a:a + 300, :, :3] = blk; out[a:a + 300, :, 3] = ok
    return out, (X0, X1, Y0, Y1), lambda lo, la: fwd.transform(lo, la)
