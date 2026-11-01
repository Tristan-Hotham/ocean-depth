"""Step 5. data/results.json: every number quoted on the page, in the paper, blog, collage and post, rounded once here.
Run: python3 code/05_results.py
"""
import numpy as np
from common import *

S = jload(f"{WORK}/stats.json"); F = jload(f"{WORK}/features.json"); G = jload(f"{WORK}/grid_meta.json")
r0 = lambda v: int(round(v)); r3 = lambda v: round(float(v), 4)
o = S["ocean"]
R = {"meta": dict(slug=SLUG, page=PAGE_URL, repo=REPO, tiles=TILE_URL)}
lat_e = lat_of_row(np.array([N / 2, N / 2 + 1]))
km_eq = 2 * np.pi * R_EARTH / N
R["grid"] = dict(px=N, km_equator=round(km_eq, 1), km_60=round(km_eq * .5, 1), n_spikes=G["n_spikes"], cap_km2=r0(G["cap_km2"]), cap_m=round(G["cap_km2"] / 1e6, 2))
R["ocean"] = dict(area=r0(o["area"]), area_m=round(o["area"] / 1e6, 1), earth_share=r3(o["earth_share"]), mean=r0(o["mean"]), median=r0(o["median"]),
                  max=r0(o["max"]), max_lat=o["max_lat"], max_lon=o["max_lon"], volume_bn=round(o["volume"] / 1e9, 2),
                  shelf=r3(o["shelf"]), slope=r3(o["slope"]), abyssal=r3(o["abyssal"]), hadal=r3(o["hadal"]),
                  deeper={str(t): r3(o[f"deeper{t}"]) for t in (1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000)})
R["ocean"]["shelf_earth"] = r3(o["shelf"] * o["earth_share"]); R["ocean"]["abyssal_earth"] = r3(o["abyssal"] * o["earth_share"])
R["ocean"]["hadal_earth"] = round(o["hadal"] * o["earth_share"], 5); R["ocean"]["hadal_km2"] = r0(o["hadal"] * o["area"])
R["ocean"]["deeper3000_earth"] = r3(o["deeper3000"] * o["earth_share"])
R["bands"] = [dict(lo=lo, hi=hi if hi < 12000 else None, share=r3(o[f"b{lo}"]), earth=r3(o[f"b{lo}"] * o["earth_share"]), km2=r0(o[f"b{lo}"] * o["area"])) for lo, hi in zip(BANDS[:-1], BANDS[1:])]
PUB = {"Pacific": "mariana", "Atlantic": "puertorico", "Indian": "java", "Southern": "factorian", "Arctic": "molloy"}
TR = {t["key"]: t for t in F["trenches"]}
R["oceans"] = []
for name in ["Pacific", "Atlantic", "Indian", "Southern", "Arctic"]:
    s = S["oceans"][name]; t = TR[PUB[name]]
    R["oceans"].append(dict(name=name, area_m=round(s["area"] / 1e6, 1), share=r3(s["share"]), mean=r0(s["mean"]), median=r0(s["median"]), max=r0(s["max"]), max_lat=s["max_lat"], max_lon=s["max_lon"],
                            shelf=r3(s["shelf"]), hadal=r3(s["hadal"]), abyssal=r3(s["abyssal"]), pub_name=t["deep"], pub_trench=t["name"], pub=t["published"], pub_src=t["src"]))
R["oc"] = {d["name"]: d for d in R["oceans"]}
R["earth"] = dict(mean=r0(S["earth_mean"]), land_mean=r0(S["land_mean"]), hist=[[a, round(b, 5)] for a, b in S["earth_hist"]],
                  km2_m=round(S["earth_km2"] / 1e6, 1), land_share=r3(1 - o["earth_share"]))
pk = sorted(S["earth_hist"], key=lambda x: -x[1])
lowpk = max([h for h in S["earth_hist"] if h[0] < -1000], key=lambda x: x[1]); highpk = max([h for h in S["earth_hist"] if h[0] >= -1000], key=lambda x: x[1])
R["earth"]["peak_deep"] = [lowpk[0], lowpk[0] + 250, round(lowpk[1], 4)]; R["earth"]["peak_high"] = [highpk[0], highpk[0] + 250, round(highpk[1], 4)]
R["curve"] = S["curve"]
R["trenches"] = [dict(key=t["key"], name=t["name"], deep=t["deep"], ocean=t["ocean"], published=t["published"], unc=t["unc"], src=t["src"], grid=r0(t["grid"]),
                      shortfall=r0(t["shortfall"]), lat=t["lat"], lon=t["lon"], pub_pt=t["pub_pt"], grid_lat=t["grid_lat"], grid_lon=t["grid_lon"]) for t in F["trenches"]]
R["tr"] = {t["key"]: t for t in R["trenches"]}
R["n_trenches"] = len(R["trenches"])
R["n_grid_deeper"] = sum(1 for t in R["trenches"] if t["shortfall"] < 0)
R["grid_deeper_names"] = [t["name"] for t in R["trenches"] if t["shortfall"] < 0]
mt = TR["mariana"]
R["mariana"] = dict(published=mt["published"], unc=mt["unc"], grid=r0(mt["grid"]), cell_at_point=r0(mt["cell_at_point"]), short=r0(mt["shortfall"]),
                    everest=EVEREST, above_everest=mt["published"] - EVEREST, above_everest_grid=r0(mt["grid"]) - EVEREST,
                    five_deeps=10924, prof_min=r0(-F["profile"]["min"]), prof=F["profile"],
                    vs_mean=round(mt["published"] / o["mean"], 1), tonga_grid_deeper=TR["tonga"]["grid"] > mt["grid"])
SB = SEABED2030
unm = 1 - SB["pct"] / 100
R["seabed2030"] = dict(pct=SB["pct"], prev=SB["prev"], grid=SB["grid"], year=SB["year"], mapped_m=SB["mapped_mkm2"], added_m=SB["added_mkm2"],
                       unmapped_pct=round(100 - SB["pct"], 1), unmapped_m=r0(unm * o["area"] / 1e6), gain=round(SB["pct"] - SB["prev"], 1),
                       years_left=round((100 - SB["pct"]) / (SB["pct"] - SB["prev"])), to2030=round((100 - SB["pct"]) / (2030 - SB["year"]), 1))
ft = F["features"]
R["features"] = dict(n=ft["n"], counts=ft["counts"], seamountlike=ft["n_seamountlike"], seamounts=ft["counts"]["Seamount(s)"], guyots=ft["counts"]["Guyot"], knolls=ft["counts"]["Knoll(s)"],
                     trenches=ft["counts"]["Trench"], deeps=ft["counts"]["Deep"], kw2011=KW2011["n"], named_vs_kw=round(KW2011["n"] / ft["n_seamountlike"], 1),
                     smt_median_grid=r0(ft["smt_median_grid"]))
nat, hs = S["national"], S["high_seas"]
zs = [z for z in S["eez"] if z["kind"] == "eez"]
R["eez"] = dict(n_zones=len(S["eez"]), national_share=r3(nat["share"]), high_share=r3(hs["share"]), national_mean=r0(nat["mean"]), high_mean=r0(hs["mean"]),
                hadal_national=r3(nat["hadal_share"]), high_m=round(hs["area"] / 1e6, 1),
                top=[dict(name=z["name"].replace(" Exclusive Economic Zone", " EEZ"), max=r0(z["max"]), lat=z["max_lat"], lon=z["max_lon"], mean=r0(z["mean"]), area=r0(z["area"])) for z in zs[:12]],
                deepest_mean=[dict(name=z["name"].replace(" Exclusive Economic Zone", " EEZ"), mean=r0(z["mean"]), area=r0(z["area"])) for z in sorted([z for z in zs if z["area"] > 2e5], key=lambda z: -z["mean"])[:10]],
                biggest=[dict(state=g["state"], area_m=round(g["area"] / 1e6, 2), mean=r0(g["mean"]), max=r0(g["max"]), zones=g["zones"]) for g in sorted(S["eez_states"], key=lambda g: -g["area"])[:10]])
R["seas"] = dict(deepest=[dict(name=s["name"], ocean=s["ocean"], max=r0(s["max"]), mean=r0(s["mean"])) for s in S["seas"][:12]],
                 deep_mean=[dict(name=s["name"], mean=r0(s["mean"]), max=r0(s["max"]), area_m=round(s["area"] / 1e6, 2)) for s in sorted([s for s in S["seas"] if s["area"] > 3e5 and "Ocean" not in s["name"]], key=lambda s: -s["mean"])[:10]],
                 n=len(S["seas"]))
SE = {s["name"]: s for s in S["seas"]}
R["sea"] = {k: dict(mean=r0(SE[n]["mean"]), max=r0(SE[n]["max"]), shelf=r3(SE[n]["shelf"]), area_m=round(SE[n]["area"] / 1e6, 2))
            for k, n in [("north", "North Sea"), ("baltic", "Baltic Sea"), ("med_e", "Mediterranean Sea - Eastern Basin"), ("caribbean", "Caribbean Sea"), ("philippine", "Philippine Sea"),
                         ("black", "Black Sea"), ("hudson", "Hudson Bay"), ("scs", "South China Sea"), ("arctic", "Arctic Ocean"), ("celtic", "Celtic Sea"), ("english", "English Channel"),
                         ("irish", "Irish Sea and St. George's Channel"), ("persian", "Persian Gulf"), ("japan", "Japan Sea"), ("bengal", "Bay of Bengal")]}
R["ne_check"] = [dict(depth=c["depth"], ne_m=round(c["ne_km2"] / 1e6, 1), grid_m=round(c["grid_km2"] / 1e6, 1)) for c in S["ne_check"]]
nc = {c["depth"]: c for c in S["ne_check"]}
R["ne"] = dict(d4000=round(nc[4000]["grid_km2"] / nc[4000]["ne_km2"] - 1, 3), d200=round(nc[200]["grid_km2"] / nc[200]["ne_km2"] - 1, 3), d6000_ne=round(nc[6000]["ne_km2"] / 1e6, 1), d6000_grid=round(nc[6000]["grid_km2"] / 1e6, 1))
R["derived"] = dict(sea_vs_land=round(o["mean"] / S["land_mean"], 1), everest_cells=None,
                    shelf_m=round(o["shelf"] * o["area"] / 1e6, 1), abyssal_m=round(o["abyssal"] * o["area"] / 1e6, 1),
                    ocean_vol_shelf_pct=None, tonga_minus_mariana_grid=r0(TR["tonga"]["grid"] - TR["mariana"]["grid"]),
                    deeper6000_vs_uk=round(o["hadal"] * o["area"] / 243610, 0))
R["charette"] = dict(mean=CHARETTE["mean"], volume_bn=CHARETTE["volume_bn"])
R["sources"] = SOURCES
R["seabed2030_src"] = SEABED2030["src"]; R["kw2011_src"] = KW2011["src"]
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("ocean", "mariana", "seabed2030", "eez", "ne", "derived")}, indent=0, ensure_ascii=False)[:4000])
print([(b["lo"], b["share"]) for b in R["bands"]]); print([(x["name"], x["mean"], x["max"]) for x in R["oceans"]]); print(R["earth"]["peak_deep"], R["earth"]["peak_high"], R["earth"]["mean"], R["earth"]["land_mean"])
