"""Step 3. Depth statistics from the zoom 4 grid, every cell weighted by its true area (and by the share of it that is sea).

- Sea floor depth of a cell = minus its height where that is below 0; sea cells whose 10 km average is above 0 (reefs,
  coasts) count as 0 m deep. The Arctic Ocean north of 85.05 N comes from ETOPO10.
- The whole Earth: land heights from the same grid (south of 85.05 S from ETOPO10) for the combined height and depth curve.
- By ocean (IHO sea areas grouped into five oceans), by IHO sea, by Exclusive Economic Zone (Marine Regions; overlapping
  and disputed claims are not in the open copy, so they count as outside national waters).
- A cross-check against Natural Earth's bathymetry polygons (areas deeper than 0, 200, 1,000 ... 10,000 m).
Outputs (WORK): stats.json; data/: depth_bands.csv, hypsometry_earth.csv, oceans.csv, seas.csv, eez.csv, eez_by_state.csv
Run: python3 code/03_stats.py
"""
import csv
import numpy as np
from shapely.geometry import shape
import shapely
from common import *

E = np.load(f"{WORK}/elev.npy")
W = np.load(f"{WORK}/water.npy")
IHO = np.load(f"{WORK}/iho.npy"); EEZ = np.load(f"{WORK}/eez.npy")
RA = np.load(f"{WORK}/row_area.npy")
ihos = jload(f"{WORK}/ihos.json"); eezs = jload(f"{WORK}/eezs.json")
cap = np.load(f"{WORK}/cap_n.npz")
EARTH = 4 * np.pi * R_EARTH ** 2

# Arctic cap cells: all sea; their EEZ by point in polygon
cap_e = cap["elev"].ravel(); cap_a = cap["area"].ravel()
clon = np.tile(-180 + (np.arange(2160) + .5) / 6, len(cap["lat"])); clat = np.repeat(cap["lat"], 2160)
cap_eez = np.zeros(len(cap_e), np.int16)
for z in eezs[1:]:
    g = shape(jload(f"{MR}/mrgid/{z['mrgid']}.geojson")["geometry"])
    if g.bounds[3] < MERC_LAT: continue
    cap_eez[shapely.contains_xy(g, clon, clat)] = z["i"]
ARCTIC = [i["i"] for i in ihos[1:] if i["name"] == "Arctic Ocean"][0]

# flat arrays of sea cells
m = W > 0
rr, cc = np.where(m)
dep = np.concatenate([np.maximum(-E[m], 0), np.maximum(-cap_e, 0)]).astype(np.float32)
area = np.concatenate([(RA[:, None] * W)[m], cap_a])
iho = np.concatenate([IHO[m], np.full(len(cap_e), ARCTIC, np.int16)])
eez = np.concatenate([EEZ[m], cap_eez])
lon = np.concatenate([lonlat_of_rc(rr, cc)[0], clon]).astype(np.float32); lat = np.concatenate([lonlat_of_rc(rr, cc)[1], clat]).astype(np.float32)
del rr, cc
print("sea cells", len(dep), "area M km2", area.sum() / 1e6)

OCEANS = ["Pacific", "Atlantic", "Indian", "Southern", "Arctic"]
OCEAN_OF = {}
for i in ihos[1:]:
    s = i["id"]; k = int(re.match(r"\d+", s).group())
    if s in ("5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "14A", "16", "16A", "17", "17A"): o = "Arctic"
    elif s == "67": o = "Southern"
    elif k <= 34 or s in ("15", "15A"): o = "Atlantic"
    elif 35 <= k <= 45 or s in ("46A", "62", "62A"): o = "Indian"
    else: o = "Pacific"
    OCEAN_OF[i["i"]] = o
LUT = np.zeros(len(ihos), np.int8)
for k, o in OCEAN_OF.items(): LUT[k] = OCEANS.index(o)
ocean = LUT[iho]


def wmedian(d, a):
    h = np.bincount(np.minimum(d, 11999).astype(np.int32), weights=a, minlength=12000)   # 1 m bins
    c = np.cumsum(h); return float(np.searchsorted(c, c[-1] / 2))


def summary(sel):
    d, a = dep[sel], area[sel]
    k = int(np.argmax(d))
    out = dict(area=float(a.sum()), mean=float((d * a).sum() / a.sum()), median=wmedian(d, a), max=float(d[k]),
               max_lon=round(float(lon[sel][k]), 3), max_lat=round(float(lat[sel][k]), 3), cells=int(sel.sum()),
               volume=float((d * a).sum() / 1000))
    for lo_, hi_ in zip(BANDS[:-1], BANDS[1:]):
        out[f"b{lo_}"] = float(a[(d >= lo_) & (d < hi_)].sum() / a.sum())
    out["shelf"] = float(a[d < 200].sum() / a.sum()); out["slope"] = float(a[(d >= 200) & (d < 3000)].sum() / a.sum())
    out["abyssal"] = float(a[(d >= 3000) & (d < 6000)].sum() / a.sum()); out["hadal"] = float(a[d >= 6000].sum() / a.sum())
    return out


S = {}
allsea = np.ones(len(dep), bool)
S["ocean"] = summary(allsea)
S["ocean"]["earth_share"] = S["ocean"]["area"] / EARTH
S["earth_km2"] = EARTH
for t in (1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000):
    S["ocean"][f"deeper{t}"] = float(area[dep >= t].sum() / area.sum())
S["oceans"] = {o: summary(ocean == OCEANS.index(o)) for o in OCEANS}
for o in OCEANS: S["oceans"][o]["share"] = S["oceans"][o]["area"] / S["ocean"]["area"]

# ---- the whole Earth: land heights too (zoom 4 grid; Antarctic interior south of 85.05 S from ETOPO10) ----
landfrac = 1 - W
hL = E[landfrac > 0]; aL = (RA[:, None] * landfrac)[landfrac > 0]
e10 = np.fromfile(ETOPO10, "<i2").reshape(1081, 2161)[:, :2160].astype(np.float64)
lat10 = 90 - np.arange(1081) / 6.0; srow = np.where(lat10 < -MERC_LAT)[0]
lo = np.clip(lat10[srow] - 1 / 12, -90, None); hi = np.minimum(lat10[srow] + 1 / 12, -MERC_LAT)
sa = (R_EARTH ** 2 * np.radians(1 / 6) * (np.sin(np.radians(hi)) - np.sin(np.radians(lo))))[:, None] * np.ones((1, 2160))
hL = np.concatenate([hL, e10[srow].ravel()]).astype(np.float32); aL = np.concatenate([aL, sa.ravel()]).astype(np.float32)
del landfrac, E, W, e10
area = area.astype(np.float32)
z_all = np.concatenate([np.minimum(-dep, 0), hL]); a_all = np.concatenate([area, aL]).astype(np.float64)
print("earth area check", a_all.sum() / EARTH)
S["earth_check"] = float(a_all.sum() / EARTH)
# histogram of the Earth's surface in 250 m steps (sea cells at their depth, land at its height; land below 0 stays below 0)
edges = np.arange(-11000, 9001, 250)
hist, _ = np.histogram(np.clip(z_all, -10999, 8999), bins=edges, weights=a_all)
S["earth_hist"] = [[int(edges[i]), float(hist[i] / a_all.sum())] for i in range(len(hist))]
S["earth_mean"] = float((z_all * a_all).sum() / a_all.sum())
S["land_mean"] = float((hL * aL).sum() / aL.sum())
with open(f"{DATA}/hypsometry_earth.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["from_m", "to_m", "share_of_earth_surface", "area_km2"])
    for i in range(len(hist)): w.writerow([int(edges[i]), int(edges[i + 1]), round(hist[i] / a_all.sum(), 6), round(hist[i])])
# cumulative curve of sea depth: share of the ocean deeper than each depth (100 m steps)
del z_all, a_all, hL, aL
hb = np.bincount(np.minimum(dep, 11999).astype(np.int32), weights=area, minlength=12000); cb = np.cumsum(hb[::-1])[::-1] / hb.sum()   # cb[t]: share at least t m deep
S["curve"] = [[int(t), round(float(cb[t]), 5)] for t in range(0, 11001, 100)]
S["curve"][0][1] = 1.0

with open(f"{DATA}/depth_bands.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["band", "from_m", "to_m", "zone", "area_km2", "share_of_ocean", "share_of_earth"] + [f"share_of_{o.lower()}" for o in OCEANS])
    for lo_, hi_ in zip(BANDS[:-1], BANDS[1:]):
        a = area[(dep >= lo_) & (dep < hi_)].sum()
        zone = "continental shelf" if hi_ <= 200 else "slope and rise" if hi_ <= 3000 else "abyssal" if hi_ <= 6000 else "hadal"
        w.writerow([f"{lo_} to {hi_ if hi_ < 12000 else 'deepest'} m", lo_, hi_ if hi_ < 12000 else "", zone, round(a), round(a / area.sum(), 5), round(a / EARTH, 5)]
                   + [round(S["oceans"][oc][f"b{lo_}"], 5) for oc in OCEANS])

# ---- IHO seas ----
seas = []
for i in ihos[1:]:
    sel = iho == i["i"]
    if sel.sum() < 3: continue
    s = summary(sel); s.update(id=i["id"], name=i["name"], mrgid=i["mrgid"], ocean=OCEAN_OF[i["i"]]); seas.append(s)
seas.sort(key=lambda s: -s["max"])
S["seas"] = seas
with open(f"{DATA}/seas.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["iho_id", "name", "ocean", "area_km2", "mean_depth_m", "median_depth_m", "deepest_cell_m", "deepest_lon", "deepest_lat", "share_shelf", "share_hadal"])
    for s in sorted(seas, key=lambda s: s["name"]):
        w.writerow([s["id"], s["name"], s["ocean"], round(s["area"]), round(s["mean"]), round(s["median"]), round(s["max"]), s["max_lon"], s["max_lat"], round(s["shelf"], 4), round(s["hadal"], 4)])
with open(f"{DATA}/oceans.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["ocean", "area_km2", "share_of_sea", "mean_depth_m", "median_depth_m", "deepest_cell_m", "deepest_lon", "deepest_lat", "share_shelf", "share_slope_rise", "share_abyssal", "share_hadal", "volume_km3"])
    for oc in OCEANS + ["All"]:
        s = S["ocean"] if oc == "All" else S["oceans"][oc]
        w.writerow([oc, round(s["area"]), round(s["area"] / S["ocean"]["area"], 4), round(s["mean"]), round(s["median"]), round(s["max"]), s["max_lon"], s["max_lat"],
                    round(s["shelf"], 4), round(s["slope"], 4), round(s["abyssal"], 4), round(s["hadal"], 4), round(s["volume"])])

# ---- EEZs ----
def state_of(name):
    n = name.replace("Exclusive economic Zone", "Exclusive Economic Zone")
    if name.startswith("Joint regime") or name.startswith("Overlapping"): return name
    if name.startswith("Isle of Man"): return "British"
    return re.sub(r"\s*Exclusive Economic Zone.*$", "", n).strip()


zs = []
for z in eezs[1:]:
    sel = eez == z["i"]
    if not sel.any(): continue
    s = summary(sel); s.update(mrgid=z["mrgid"], name=z["name"], kind=z["kind"], joint=z["kind"] != "eez", state=state_of(z["name"])); zs.append(s)
zs.sort(key=lambda s: -s["max"])
S["eez"] = zs
inn = eez > 0
S["national"] = dict(area=float(area[inn].sum()), share=float(area[inn].sum() / area.sum()), mean=float((dep[inn] * area[inn]).sum() / area[inn].sum()),
                     hadal_share=float(area[inn & (dep >= 6000)].sum() / area[dep >= 6000].sum()))
hs = ~inn
k = int(np.argmax(np.where(hs, dep, -1)))
S["high_seas"] = dict(area=float(area[hs].sum()), share=float(area[hs].sum() / area.sum()), mean=float((dep[hs] * area[hs]).sum() / area[hs].sum()),
                      max=float(dep[k]), max_lon=round(float(lon[k]), 3), max_lat=round(float(lat[k]), 3))
st = {}
for s in zs:
    if s["joint"]: continue
    g = st.setdefault(s["state"], dict(state=s["state"], zones=0, area=0, vol=0, max=0, max_zone=None, max_lon=None, max_lat=None))
    g["zones"] += 1; g["area"] += s["area"]; g["vol"] += s["mean"] * s["area"]
    if s["max"] > g["max"]: g.update(max=s["max"], max_zone=s["name"], max_lon=s["max_lon"], max_lat=s["max_lat"])
for g in st.values(): g["mean"] = g["vol"] / g["area"]; del g["vol"]
S["eez_states"] = sorted(st.values(), key=lambda g: -g["max"])
with open(f"{DATA}/eez.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["mrgid", "zone", "group", "kind", "area_km2_on_grid", "mean_depth_m", "median_depth_m", "deepest_cell_m", "deepest_lon", "deepest_lat", "share_shelf", "share_hadal"])
    for s in sorted(zs, key=lambda s: s["name"]):
        w.writerow([s["mrgid"], s["name"], s["state"], s["kind"], round(s["area"]), round(s["mean"]), round(s["median"]), round(s["max"]), s["max_lon"], s["max_lat"], round(s["shelf"], 4), round(s["hadal"], 4)])
with open(f"{DATA}/eez_by_state.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["group (Marine Regions adjective)", "zones", "area_km2_on_grid", "mean_depth_m", "deepest_cell_m", "deepest_zone", "deepest_lon", "deepest_lat"])
    for g in sorted(st.values(), key=lambda g: g["state"]):
        w.writerow([g["state"], g["zones"], round(g["area"]), round(g["mean"]), round(g["max"]), g["max_zone"], g["max_lon"], g["max_lat"]])

# ---- Natural Earth bathymetry cross-check (equal-area areas of the 'deeper than' polygons) ----
from pyproj import Geod
geod = Geod(ellps="WGS84")
ne = []
for k, t in [("L", 0), ("K", 200), ("J", 1000), ("I", 2000), ("H", 3000), ("G", 4000), ("F", 5000), ("E", 6000), ("D", 7000), ("C", 8000), ("B", 9000), ("A", 10000)]:
    F = jload(f"{NE_BATHY}/ne_10m_bathymetry_{k}_{t}.geojson")["features"]
    a = 0.0
    for f in F:
        g = shape(f["geometry"])
        for p in getattr(g, "geoms", [g]):
            a += abs(geod.geometry_area_perimeter(p)[0]) / 1e6
    grid = float(area[dep >= max(t, 1e-9)].sum()) if t > 0 else float(area.sum())
    ne.append(dict(depth=t, ne_km2=a, grid_km2=grid))
    print("NE deeper than", t, round(a / 1e6, 2), "grid", round(grid / 1e6, 2))
S["ne_check"] = ne
jsave(S, f"{WORK}/stats.json")
o = S["ocean"]
print("ocean", round(o["area"] / 1e6, 1), "M km2", round(o["earth_share"], 4), "mean", round(o["mean"]), "median", round(o["median"]), "max", o["max"], o["max_lon"], o["max_lat"])
print("zones shelf %.3f slope %.3f abyssal %.3f hadal %.4f" % (o["shelf"], o["slope"], o["abyssal"], o["hadal"]))
for oc in OCEANS: print(oc, {k: round(v, 3) if isinstance(v, float) else v for k, v in S["oceans"][oc].items() if k in ("area", "mean", "median", "max", "max_lon", "max_lat", "share")})
print("national", S["national"]); print("high seas", S["high_seas"])
print("deepest EEZ", [(s["name"], round(s["max"])) for s in zs[:8]])
print("deepest seas", [(s["name"], round(s["max"])) for s in seas[:8]])
