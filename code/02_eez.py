"""Step 2. National waters: the Marine Regions Exclusive Economic Zones, joint regimes and overlapping (disputed) claims,
rasterised at twice the zoom 4 resolution and given to each sea cell by majority.
Inputs: MR/sel.tsv (EEZ and joint regime ids), MR/claims.tsv (whole overlapping claims, not their per-sea parts),
MR/mrgid/<MRGID>.geojson. Outputs (WORK): eez.npy, eezs.json
Run: python3 code/02_eez.py
"""
import csv
import numpy as np
import rasterio.features, rasterio.transform
from shapely.geometry import shape, box
from common import *

HALF = 20037508.342789244
M = 2 * N
T = rasterio.transform.from_origin(-HALF, HALF, 2 * HALF / M, 2 * HALF / M)
clip = box(-180, -MERC_LAT, 180, MERC_LAT)
water = np.load(f"{WORK}/water.npy")

eezs = [None]; items = []
rows = [r + ["eez"] for r in csv.reader(open(f"{MR}/sel.tsv", encoding="utf-8"), delimiter="\t") if r[2] in ("EEZ", "Joint regime (EEZ)")]
rows += [r + ["claim"] for r in csv.reader(open(f"{MR}/claims.tsv", encoding="utf-8"), delimiter="\t")]
for mid, nm, typ, kind in rows:
    g = shape(jload(f"{MR}/mrgid/{mid}.geojson")["geometry"]).buffer(0).intersection(clip)
    eezs.append(dict(i=len(eezs), mrgid=int(mid), name=nm.replace("Exclusive economic Zone", "Exclusive Economic Zone"),
                     kind="joint" if typ.startswith("Joint") else kind))
    if not g.is_empty:
        items.append((to_merc(g), len(eezs) - 1))
fine = rasterio.features.rasterize(items, out_shape=(M, M), transform=T, fill=0, dtype="int16")
sub = fine.reshape(N, 2, N, 2).transpose(0, 2, 1, 3).reshape(N, N, 4)
eez = np.zeros((N, N), np.int16); best = np.zeros((N, N), np.int8)
for k in range(4):
    v = sub[..., k]; cnt = (sub == v[..., None]).sum(-1)
    take = (v > 0) & (cnt > best); eez[take] = v[take]; best[take] = cnt[take]
eez[water == 0] = 0
np.save(f"{WORK}/eez.npy", eez)
jsave(eezs, f"{WORK}/eezs.json")
print("zones", len(eezs) - 1, "sea cells in a zone", int((eez > 0).sum()), "of", int((water > 0).sum()))
