"""Step 4. Trenches, seamounts and named undersea features, the Mariana profile, and the page's vector files.

- Trenches: for each trench in common.TRENCHES, the deepest sea cell of the zoom 4 grid inside its search box, set beside the
  published depth of its deepest point (sources in common.SOURCES).
- Profile: heights sampled every kilometre (bilinear on the grid) along a north to south line through the Challenger Deep.
- Named features: every Marine Regions gazetteer point of the undersea types in MR/sel.tsv, with the grid depth at it.
- Page files (data/page/): features.json, seas.json (names and figures of seas), borders.json (Natural Earth 50m countries,
  simplified), eez.json (Marine Regions zones, simplified), places.json (Natural Earth populated places).
Outputs: WORK/features.json; data/trenches.csv, data/undersea_features.csv, data/mariana_profile.csv, data/page/*.json
Run: python3 code/04_features.py
"""
import csv
import numpy as np
from shapely.geometry import shape, mapping, Polygon
from shapely.ops import unary_union
from common import *

E = np.load(f"{WORK}/elev.npy").astype(np.float64)
W = np.load(f"{WORK}/water.npy")
S = jload(f"{WORK}/stats.json")


def sample(lon, lat):
    r, c = rc_of(lon, lat); r = np.asarray(r) - .5; c = np.asarray(c) - .5
    r0 = np.clip(np.floor(r).astype(int), 0, N - 2); c0 = np.floor(c).astype(int) % N; c1 = (c0 + 1) % N
    ty = np.clip(r - r0, 0, 1); tx = c - np.floor(c)
    return (E[r0, c0] * (1 - tx) + E[r0, c1] * tx) * (1 - ty) + (E[r0 + 1, c0] * (1 - tx) + E[r0 + 1, c1] * tx) * ty


def cell(lon, lat):
    r, c = rc_of(lon, lat); return float(E[int(r), int(c) % N])


PUB_PT = {"mariana", "puertorico", "factorian", "java", "molloy"}
T = []
for key, nm, deep, oc, pub, unc, src, plon, plat, (x0, y0, x1, y1) in TRENCHES:
    r0, c0 = rc_of(x0, y1); r1, c1 = rc_of(x1, y0)
    r0, r1, c0, c1 = int(r0), int(r1) + 1, int(c0), int(c1) + 1
    sub = np.where(W[r0:r1, c0:c1] > 0, E[r0:r1, c0:c1], 0)
    k = np.unravel_index(np.argmin(sub), sub.shape)
    glon, glat = lonlat_of_rc(r0 + k[0], c0 + k[1])
    t = dict(key=key, name=nm, deep=deep, ocean=oc, published=pub, unc=unc, src=src, grid=float(-sub[k]), grid_lon=round(float(glon), 3), grid_lat=round(float(glat), 3),
             pub_pt=key in PUB_PT, lon=plon if key in PUB_PT else round(float(glon), 3), lat=plat if key in PUB_PT else round(float(glat), 3))
    t["cell_at_point"] = -cell(plon, plat) if key in PUB_PT else None
    t["shortfall"] = pub - t["grid"]
    T.append(t)
    print(f"{nm:40s} published {pub:6d}  grid {t['grid']:7.0f}  short {t['shortfall']:6.0f}  at {t['grid_lon']}, {t['grid_lat']}")
T.sort(key=lambda t: -t["published"])
with open(f"{DATA}/trenches.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["trench", "deepest_point", "ocean", "published_depth_m", "published_uncertainty_m", "source", "point_lon", "point_lat", "point_is_published",
                                   "deepest_grid_cell_m", "grid_cell_lon", "grid_cell_lat", "published_minus_grid_m"])
    for t in T:
        w.writerow([t["name"], t["deep"], t["ocean"], t["published"], t["unc"] or "", SOURCES[t["src"]].split(" (")[0], t["lon"], t["lat"], int(t["pub_pt"]),
                    round(t["grid"]), t["grid_lon"], t["grid_lat"], round(t["shortfall"])])

# ---- the Mariana profile: north to south through the Challenger Deep ----
lon0 = 142.588
lats = np.arange(14.5, 7.999, -1 / 111.2)
prof = sample(np.full(len(lats), lon0), lats)
dist = (14.5 - lats) * 111.2
with open(f"{DATA}/mariana_profile.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["distance_km_from_14.5N", "lat", "lon", "height_m_zoom4_bilinear"])
    for d_, la, h in zip(dist, lats, prof): w.writerow([round(d_, 1), round(la, 4), lon0, round(h)])
PROF = dict(lon=lon0, lat0=14.5, lat1=8.0, step_km=1, h=[int(round(v)) for v in prof], min=float(prof.min()), min_lat=round(float(lats[np.argmin(prof)]), 3),
            guam_side_max=float(prof[:150].max()))
print("profile min", PROF["min"], "at", PROF["min_lat"])

# ---- named undersea features (Marine Regions gazetteer) ----
TYPES = {"Trench": "t", "Deep": "d", "Seamount(s)": "s", "Guyot": "g", "Knoll(s)": "k", "Seamount Chain": "c", "Seamount Province": "c", "Abyssal Plain": "p", "Plain": "p",
         "Basin": "b", "Ridge": "r", "Rise": "r", "Plateau": "u", "Fracture Zone": "f", "Trough": "h", "Escarpment": "e", "Canyon(s)": "n"}
feats = []
for mid, nm, typ in csv.reader(open(f"{MR}/sel.tsv", encoding="utf-8"), delimiter="\t"):
    if typ not in TYPES: continue
    g = jload(f"{MR}/mrgid/{mid}.geojson")["geometry"]
    if g["type"] != "Point": continue
    lo_, la_ = g["coordinates"][:2]
    if not (-180 <= lo_ <= 180 and -90 <= la_ <= 90): continue
    h = cell(lo_, la_) if abs(la_) < MERC_LAT else None
    feats.append(dict(mrgid=int(mid), name=nm, type=typ, code=TYPES[typ], lon=round(lo_, 4), lat=round(la_, 4), grid=None if h is None else round(h)))
from collections import Counter
cnt = Counter(f["type"] for f in feats)
print(cnt)
with open(f"{DATA}/undersea_features.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["mrgid", "name", "type", "lon", "lat", "grid_height_m_at_point"])
    for o in sorted(feats, key=lambda o: (o["type"], o["name"])): w.writerow([o["mrgid"], o["name"], o["type"], o["lon"], o["lat"], o["grid"]])
smt = [f for f in feats if f["code"] in "sgk" and f["grid"] is not None]
FEAT = dict(counts=dict(cnt), n=len(feats), n_seamountlike=sum(cnt[k] for k in ("Seamount(s)", "Guyot", "Knoll(s)")),
            smt_median_grid=float(np.median([-f["grid"] for f in smt])), smt_above_minus1000=sum(1 for f in smt if f["grid"] > -1000))
jsave(dict(trenches=T, profile=PROF, features=FEAT), f"{WORK}/features.json")

# ---- page files ----
def rnd(x, d=3):
    return [rnd(y, d) for y in x] if isinstance(x[0], (list, tuple)) else [round(x[0], d), round(x[1], d)]


# undersea features: [name, code, lat, lon, grid depth (positive down), mrgid]
jsave([[o["name"], o["code"], o["lat"], o["lon"], None if o["grid"] is None else -o["grid"], o["mrgid"]] for o in feats], f"{PAGE}/features.json")
# trenches for the page: [name, deepest point, lat, lon, published, unc, source key, grid depth, ocean, point is published]
jsave([[t["name"], t["deep"], t["lat"], t["lon"], t["published"], t["unc"], t["src"], round(t["grid"]), t["ocean"], int(t["pub_pt"])] for t in T], f"{PAGE}/trenches.json")
# seas: Natural Earth marine names (label points) with IHO figures where the name matches
iho = {s["name"]: s for s in S["seas"]}
alias = {"Mediterranean Sea": None, "Barents Sea": "Barentsz Sea", "East China Sea": "Eastern China Sea", "Sea of Japan": "Japan Sea", "Persian Gulf": "Persian Gulf",
         "Andaman Sea": "Andaman or Burma Sea", "Molucca Sea": "Molukka Sea", "Bay of Biscay": "Bay of Biscay"}
seas = []
for f in jload(f"{NE_BATHY}/ne_10m_geography_marine_polys.geojson")["features"]:
    p = f["properties"]
    if not p.get("name") or p["featurecla"] in ("river", "lagoon", "reef"): continue
    g = shape(f["geometry"]).buffer(0); pt = g.representative_point()
    nm = p["name"].replace("\r", " ").replace("\n", " ").strip()
    st = iho.get(alias.get(nm, nm)) if alias.get(nm, nm) else None
    seas.append([nm, p["featurecla"], round(pt.y, 3), round(pt.x, 3), float(p.get("min_label") or 9), round(float(p.get("scalerank") or 9), 1),
                 [round(st["mean"]), round(st["max"]), round(st["area"]), st["max_lat"], st["max_lon"], round(st["shelf"], 3)] if st else None])
# IHO areas without a Natural Earth name of their own still go in (search and labels)
have = {s[0] for s in seas}
for s in S["seas"]:
    if s["name"] in have or alias.get(s["name"]): continue
    g = shape(jload(f"{MR}/iho/{s['id']}.geojson")["geometry"]).buffer(0); pt = g.representative_point()
    seas.append([s["name"], "iho", round(pt.y, 3), round(pt.x, 3), 5.0, 5.0, [round(s["mean"]), round(s["max"]), round(s["area"]), s["max_lat"], s["max_lon"], round(s["shelf"], 3)]])
jsave(seas, f"{PAGE}/seas.json")
feats_b = []
for f in jload(f"{GEO}/ne_50m_admin_0_countries.geojson")["features"]:
    g = mapping(shape(f["geometry"]).simplify(.03, preserve_topology=True))
    feats_b.append({"type": "Feature", "properties": {"a3": f["properties"]["ADM0_A3"], "n": f["properties"]["NAME"]}, "geometry": {"type": g["type"], "coordinates": rnd(g["coordinates"])}})
jsave({"type": "FeatureCollection", "features": feats_b}, f"{PAGE}/borders.json")
zs = {z["mrgid"]: z for z in S["eez"]}
fe = []
for z in jload(f"{WORK}/eezs.json")[1:]:
    if z["mrgid"] not in zs: continue
    g = shape(jload(f"{MR}/mrgid/{z['mrgid']}.geojson")["geometry"]).buffer(0)
    # outline only: drop the island holes and slivers, which the map does not need, then simplify
    g = unary_union([Polygon(p.exterior, [h for h in p.interiors if Polygon(h).area > .5]) for p in getattr(g, "geoms", [g]) if p.area > .002]).simplify(.08, preserve_topology=True)
    if g.is_empty: continue
    gj = mapping(g); s = zs[z["mrgid"]]
    fe.append({"type": "Feature", "properties": {"n": s["name"].replace(" Exclusive Economic Zone", " EEZ"), "k": s["kind"], "m": round(s["mean"]), "x": round(s["max"]), "a": round(s["area"]),
                                                 "id": z["mrgid"], "xl": [s["max_lat"], s["max_lon"]]},
               "geometry": {"type": gj["type"], "coordinates": rnd(gj["coordinates"], 2)}})
jsave({"type": "FeatureCollection", "features": fe}, f"{PAGE}/eez.json")
PPL = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")["features"]
pl = sorted([[f["properties"]["name"], round(f["geometry"]["coordinates"][1], 3), round(f["geometry"]["coordinates"][0], 3), int(f["properties"]["pop_max"] or 0)] for f in PPL], key=lambda r: -r[3])
jsave(pl, f"{PAGE}/places.json")
for fn in sorted(os.listdir(PAGE)): print(fn, os.path.getsize(f"{PAGE}/{fn}") // 1024, "KB")
