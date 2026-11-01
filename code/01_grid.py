"""Step 1. The zoom 4 depth grid and the masks that say what is sea, which ocean and whose waters.

- Mosaics the 256 Terrarium tiles at zoom 4 into one 4096 x 4096 Web Mercator grid of heights (metres; negative below sea level)
  and replaces the few corrupt cells (isolated spikes of kilometres) by the median of their neighbours.
- Rasterises, at twice that resolution (8192 x 8192) so each cell gets fractions:
  land (Natural Earth 10m countries), lakes and reservoirs (Natural Earth 10m lakes, so the Caspian is not sea),
  and the IHO sea area (Marine Regions IHO v3, sub-areas over their parents). National waters follow in 02_eez.py.
- Web Mercator stops at 85.05 N: the Arctic Ocean north of it (about 0.95 million km2) comes from ETOPO10.
Outputs (WORK): elev.npy, water.npy (share of each cell that is sea), iho.npy, row_area.npy, cap_n.npz, ihos.json
Run: python3 code/01_grid.py
"""
import csv
import numpy as np, shapely
from PIL import Image
import rasterio.features, rasterio.transform
from shapely.geometry import shape, box
from scipy.ndimage import median_filter, distance_transform_edt
from common import *

# ---- heights ----
elev = np.zeros((N, N), np.float32)
for x in range(16):
    for y in range(16):
        a = np.asarray(Image.open(f"{TILES}/4/{x}/{y}.png").convert("RGB"), np.float64)
        elev[y * 256:(y + 1) * 256, x * 256:(x + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
med = median_filter(elev, size=3, mode="nearest")
d = elev - med
# isolated spikes: high ones on land or shelf, deep holes in shallow ground (atolls amid deep ocean are real and kept,
# and trenches are tens of km wide, so a trench cell always has deep neighbours)
spike = ((d > 2500) & (med > -500)) | ((d < -2500) & (med > -1000))
print("spikes replaced:", int(spike.sum()), [(int(r), int(c), float(elev[r, c]), float(med[r, c])) for r, c in zip(*np.where(spike))][:12])
meta = {"n_spikes": int(spike.sum()), "spike_min": float(elev[spike].min()) if spike.any() else None}
elev[spike] = med[spike]
np.save(f"{WORK}/elev.npy", elev)
print("heights", elev.min(), elev.max())

# ---- fine rasters at 2x ----
HALF = 20037508.342789244
M = 2 * N
T = rasterio.transform.from_origin(-HALF, HALF, 2 * HALF / M, 2 * HALF / M)
clip = box(-180, -MERC_LAT, 180, MERC_LAT)


def burn(items, dtype="int16"):
    shp = []
    for g, v in items:
        g = g.buffer(0).intersection(clip)
        if not g.is_empty:
            shp.append((to_merc(g), v))
    return rasterio.features.rasterize(shp, out_shape=(M, M), transform=T, fill=0, dtype=dtype)


def frac(mask):
    return mask.reshape(N, 2, N, 2).mean(axis=(1, 3)).astype(np.float32)


def majority(fine):
    sub = fine.reshape(N, 2, N, 2).transpose(0, 2, 1, 3).reshape(N, N, 4)
    out = np.zeros((N, N), fine.dtype)
    best = np.zeros((N, N), np.int8)
    for k in range(4):
        v = sub[..., k]
        cnt = (sub == v[..., None]).sum(-1)
        take = (v > 0) & (cnt > best)
        out[take] = v[take]; best[take] = cnt[take]
    return out


land = burn([(shape(f["geometry"]), 1) for f in jload(f"{GEO}/ne_10m_admin_0_countries.geojson")["features"]], "uint8")
lakes = burn([(shape(f["geometry"]), 1) for f in jload(f"{BORDERS}/ne_10m_lakes.geojson")["features"]
              if f["properties"]["featurecla"] in ("Lake", "Reservoir")], "uint8")
sea_fine = (land == 0) & (lakes == 0)
water = frac(sea_fine)
# keep only sea joined to the world ocean (drops lakes Natural Earth does not list, such as small salt lakes)
from scipy.ndimage import label
lab, n = label(water > 0)
big = np.bincount(lab.ravel()); big[0] = 0
keep = np.isin(lab, np.where(big > 2000)[0])
# the Caspian is a lake (Natural Earth 10m lakes do not include it), so its component is dropped; the Black Sea stays,
# joined to the ocean by the Bosporus, which is too narrow for the grid
rc, cc = rc_of(50.5, 42.0)
keep[lab == lab[int(rc), int(cc)]] = False
print("water components", n, "kept sizes", sorted(big[big > 2000])[-5:], "dropped cells", int(((water > 0) & ~keep).sum()))
water[~keep] = 0
np.save(f"{WORK}/water.npy", water)
del land, lakes

# ---- IHO sea areas ----
ihos = [None]
items = []
labels = list(csv.reader(open(f"{MR}/iho_labels.tsv", encoding="utf-8"), delimiter="\t"))
# parents first, sub-areas (lowercase suffix) after so they overwrite their parent
labels.sort(key=lambda r: (bool(re.search(r"[a-z]$", r[0])), r[0]))
for sid, nm in labels:
    f = jload(f"{MR}/iho/{sid}.geojson")
    ihos.append(dict(i=len(ihos), id=sid, name=nm, mrgid=f["properties"].get("mrgid")))
    items.append((shape(f["geometry"]), len(ihos) - 1))
fine = np.zeros((M, M), np.int16)
for g, v in items:                                    # in order, so later (sub-areas) win
    r = burn([(g, v)]); fine[r > 0] = v
iho = majority(fine)
del fine
# water cells outside every IHO polygon (simplified coasts): take the nearest IHO area
miss = (water > 0) & (iho == 0)
_, (ri, ci) = distance_transform_edt(iho == 0, return_indices=True)
iho[miss] = iho[ri[miss], ci[miss]]
print("IHO: water cells filled from nearest area", int(miss.sum()))
np.save(f"{WORK}/iho.npy", iho)
jsave(ihos, f"{WORK}/ihos.json")

# ---- cell areas (km2): exact for a Mercator row between its two latitudes ----
lat_e = lat_of_row(np.arange(N + 1))
row_area = R_EARTH ** 2 * np.radians(360 / N) * (np.sin(np.radians(lat_e[:-1])) - np.sin(np.radians(lat_e[1:])))
np.save(f"{WORK}/row_area.npy", row_area)

# ---- Arctic cap from ETOPO10 (rows north of the Mercator limit) ----
e10 = np.fromfile(ETOPO10, "<i2").reshape(1081, 2161)   # rows 90 N (first) to 90 S (last)
lat10 = 90 - np.arange(1081) / 6.0
rows = np.where(lat10 > MERC_LAT)[0]
cap = e10[rows][:, :2160].astype(np.float64)
cl = lat10[rows]
hi = np.clip(cl + 1 / 12, None, 90); lo = np.maximum(cl - 1 / 12, MERC_LAT)
cap_area = (R_EARTH ** 2 * np.radians(1 / 6) * (np.sin(np.radians(hi)) - np.sin(np.radians(lo))))[:, None] * np.ones((1, 2160))
np.savez(f"{WORK}/cap_n.npz", elev=cap, area=cap_area, lat=cl)
print("Arctic cap", cap.shape, round(cap_area.sum()), "km2, mean", round((cap * cap_area).sum() / cap_area.sum()), "min", cap.min(), "max", cap.max())
meta["cap_km2"] = float(cap_area.sum())
jsave(meta, f"{WORK}/grid_meta.json")

A = row_area[:, None] * water
print("sea area in grid", round(A.sum() / 1e6, 2), "M km2 + cap", round(cap_area.sum() / 1e6, 2))
for nm, lon, lat in [("Challenger", 142.588, 11.372), ("Caspian", 50.5, 42.0), ("Black Sea", 34, 43), ("Red Sea", 38, 21), ("N Atlantic", -40, 35)]:
    r, c = rc_of(lon, lat); r, c = int(r), int(c)
    print(nm, elev[r, c], "water", water[r, c], "iho", ihos[iho[r, c]]["name"] if iho[r, c] else None)
