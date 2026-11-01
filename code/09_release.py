"""Step 9. Blog post (release/blog/post.html from code/blog_template.html) and release/blog/meta.json, the Zenodo folder
(metadata.json and a code-and-data zip; the other files to upload are listed in metadata.json), README.md and LICENSE.
Image tokens {{IMG|file|alt|caption}} and the placeholders 10.5281/zenodo.23850291, https://doi.org/10.5281/zenodo.23850291, https://blog.tristanhotham.com/2026/10/31/ocean-depth/ are left for the publisher.
Run: python3 code/09_release.py
"""
import importlib.util, json, os, re, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "06_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
NAME = "Hotham_How_Deep_Is_the_Sea"
DASH = ("—", "–", "--")
TOK = re.compile(r"\{\{(?!IMG\|)([^{}|]+)(\|(\w+))?\}\}")
pc = lambda v, d=0: f"{v * 100:.{d}f}%"
# numbers written into the blog's alt text and words
assert [round(x["share"] * 100, 1) for x in R["bands"][:7]] == [7.7, 4.3, 4.4, 8.6, 22.4, 31.7, 19.9]
assert [o["mean"] for o in R["oceans"]] == [3943, 3606, 3775, 3213, 1205] and [o["pub"] for o in R["oceans"]] == [10935, 8378, 7187, 7432, 5551]
assert R["bands"][5]["earth"] > .2                                                       # 'better than one in five'
assert round(R["eez"]["national_share"] * 100) == 39 and round(R["eez"]["high_share"] * 100) == 61 and R["eez"]["national_mean"] == 2731 and R["eez"]["high_mean"] == 4273
assert [z["max"] for z in R["eez"]["top"][:3]] == [10467, 10264, 9990]
assert R["n_trenches"] == 14 and "Puerto Rico Trench" in R["grid_deeper_names"]
assert R["features"]["named_vs_kw"] > 9

# blog
t = open(os.path.join(HERE, "blog_template.html"), encoding="utf-8").read()
t = TOK.sub(b.sub, t)
left = set(re.findall(r"\{\{(\w+)\}\}", t)); assert left <= b.PLACEHOLDERS, left
vis = re.sub(r"<!--.*?-->", "", t, flags=re.S)
for bad in DASH + ("DSIT", "DCMS", "civil serv"): assert bad not in vis, bad
for ln in t.splitlines():
    if "{{IMG|" in ln: assert ln.startswith("{{IMG|") and ln.endswith("}}"), ln
BL = os.path.join(ROOT, "release", "blog"); os.makedirs(BL, exist_ok=True)
open(os.path.join(BL, "post.html"), "w", encoding="utf-8").write(t)
imgs = re.findall(r"\{\{IMG\|([^|]+)\|", t)
for m in imgs: assert os.path.exists(os.path.join(BL, m)), m
assert 5 <= len(imgs) <= 8, len(imgs)
for fn in os.listdir(BL):
    if fn.startswith("b_") and fn not in imgs: os.remove(os.path.join(BL, fn))
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
O, M, S = R["ocean"], R["mariana"], R["seabed2030"]
meta = dict(
    title="How deep is the sea? The ocean floor, its trenches and seamounts, on one map",
    slug="ocean-depth",
    excerpt=(f"A map of the floor of the whole ocean, sharp from ocean basins to seamounts. The average sea floor lies {O['mean']:,} m down, {pc(O['abyssal'])} of it is abyssal, "
             f"the Challenger Deep would hide Everest with {M['above_everest']:,} m to spare, and only {S['pct']}% of the floor is mapped to modern standards."),
    seo_description="An interactive world map of ocean depth, with shaded sea floor relief, the deepest trenches, seamounts and how little of the floor is mapped.",
    tags=["ocean", "bathymetry", "sea floor", "ocean depth", "Mariana Trench", "seamounts", "maps", "data visualisation"],
    header_alt=(f"Title card reading 'How deep is the sea?' in black on pale grey, with the line: the average sea floor lies {O['mean']:,} m down; the deepest place, "
                f"{M['published']:,} m, would hide Everest with {M['above_everest']:,} m to spare. Beside it a world map in the Equal Earth projection with sandy land and "
                "a sea floor shaded from pale turquoise shelves to deep navy plains and dark trenches."))
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
for v in meta.values():
    for bad in DASH: assert bad not in str(v)
json.dump(meta, open(os.path.join(BL, "meta.json"), "w"), indent=2, ensure_ascii=False)

# README
E, OC, T = R["eez"], R["oc"], R["tr"]
readme = f"""# How deep is the sea?

A detailed world map of ocean depth, drawn live in the browser from the open AWS Terrain Tiles at every zoom (depth tints, shaded sea floor relief, depth bands, a readout of any point), with the deepest trenches at their measured depths, named seamounts and national waters, and a study of how deep the sea is and how little of its floor is mapped.

**Interactive version:** https://maps.tristanhotham.com/ocean-depth/

**Paper and archived release:** {{https://doi.org/10.5281/zenodo.23850291}}

**Blog post:** {{https://blog.tristanhotham.com/2026/10/31/ocean-depth/}}

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

- The sea covers {O['area_m']} million km², {pc(O['earth_share'], 1)} of the Earth, with a mean depth of {O['mean']:,} m (median {O['median']:,} m) and a volume of {O['volume_bn']:.2f} billion km³ (Charette and Smith 2010: 3,682 m and 1.332 billion km³).
- Continental shelf above 200 m is {pc(O['shelf'], 1)} of the sea floor; slopes, rises and ridges from 200 to 3,000 m {pc(O['slope'], 1)}; abyssal depths from 3,000 to 6,000 m {pc(O['abyssal'], 1)}, more than half of the planet's surface; the hadal zone below 6,000 m {pc(O['hadal'], 2)}.
- Oceans: Pacific {OC['Pacific']['mean']:,} m, Indian {OC['Indian']['mean']:,} m, Atlantic {OC['Atlantic']['mean']:,} m, Southern {OC['Southern']['mean']:,} m, Arctic {OC['Arctic']['mean']:,} m on average.
- The Challenger Deep is {M['published']:,} ± {M['unc']} m (Greenaway et al. 2021): Everest would sit {M['above_everest']:,} m under water. The 10 km grid's deepest Mariana cell is {M['grid']:,} m; its deepest cell anywhere is in the Tonga Trench ({T['tonga']['grid']:,} m); in {R['n_grid_deeper']} of {R['n_trenches']} deep places it is deeper than any measured depth, pointing to errors in the source grids.
- National waters (EEZs, joint regimes and claims) cover {pc(E['national_share'])} of the sea and hold {pc(E['hadal_national'])} of the floor deeper than 6,000 m.
- Seabed 2030 reported in {S['year']} that {S['pct']}% of the ocean floor is mapped to modern standards; about {S['unmapped_m']} million km² is known only roughly.

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Method in brief

- **Depths.** AWS Terrain Tiles (Terrarium encoding: height = R × 256 + G + B / 256 − 32,768 m; under the sea from ETOPO1, GEBCO and SRTM15+). The page decodes them live at zoom 0 to 14. The statistics use zoom 4, a 4,096 × 4,096 Web Mercator grid ({R['grid']['km_equator']} km at the equator), each cell weighted by its exact area on a sphere and by its share of sea; {R['grid']['n_spikes']} corrupt cells replaced by their neighbours' median. The Arctic north of 85.05° N from ETOPO10.
- **Sea.** Outside Natural Earth 1:10m land and lakes and joined to the world ocean (Caspian out, Black Sea in), rasterised at twice the grid's resolution. Sea cells averaging above 0 m count as 0 m deep. Sea under Antarctic ice shelves is missing.
- **Oceans, seas and national waters.** Marine Regions IHO sea areas (grouped into five oceans) and Exclusive Economic Zones, joint regimes and overlapping claims.
- **Trenches.** The deepest grid cell in a box round each of {R['n_trenches']} trenches, set beside published depths (Greenaway et al. 2021; Bongiovanni, Stewart and Jamieson 2022; Stewart and Jamieson 2019; Wikipedia).
- **Check.** Natural Earth's bathymetry polygons give almost the same areas deeper than 200 m and {pc(R['ne']['d4000'], 1)} less deeper than 4,000 m.

## Files

| Path | What it is |
|---|---|
| `index.html` | The interactive page (results embedded; borders, places, national waters and undersea names load from `data/page/`; depth tiles load live from Amazon). |
| `header.png` | Social card (1200 by 630). |
| `data/depth_bands.csv` | Area and share of the sea floor (and of the Earth) in each depth band, overall and by ocean. |
| `data/oceans.csv`, `data/seas.csv` | Area, mean, median and deepest cell of each ocean and of each IHO sea area. |
| `data/eez.csv`, `data/eez_by_state.csv` | The same for each Exclusive Economic Zone, joint regime and claim, and grouped by state. |
| `data/trenches.csv` | {R['n_trenches']} deepest places: published depth and source, point, and the grid's deepest cell along the trench. |
| `data/mariana_profile.csv` | Profile along 142.6° E through the Challenger Deep, every km. |
| `data/hypsometry_earth.csv` | Share of the Earth's surface in each 250 m step of height or depth. |
| `data/undersea_features.csv` | {R['features']['n']:,} named undersea features from the Marine Regions gazetteer with the grid depth at each. |
| `data/results.json` | Every number used anywhere. |
| `data/page/` | Page files. |
| `code/` | Numbered scripts (below), page, paper and blog templates. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `release/` | Paper PDF and LaTeX (its figures are the blog figures), blog post and figures, Zenodo metadata (with the list of files to upload) and the code-and-data zip. |
| `qa/` | Screenshots from the last check of the page. |

## Known limits

- The statistics are smoothed to about 10 km: trenches look hundreds of metres shallower and seamounts lower than they are, and band shares are good to about a percentage point.
- Most of the sea floor in the sources is predicted from satellite altimetry; some cells are wrong by hundreds of metres, as the trench comparison shows. Only {S['pct']}% of the floor is mapped to modern standards (Seabed 2030, {S['year']}).
- The grouping of IHO seas into oceans is one reasonable choice; Marine Regions zones include disputed claims. Published depths of the deepest places differ in age and accuracy.
- The global seamount census of Kim and Wessel (2011), {R['features']['kw2011']:,} likely seamounts, is cited, not used: its host (soest.hawaii.edu) could not be reached when building.

## How to rerun

Needs Python 3 with numpy, scipy, shapely, rasterio, pyproj, matplotlib and Pillow; xelatex and pdftotext; Playwright for the QA step. Raw inputs are read in place from the paths in `code/common.py` (set `OCEAN_RAW`, `OCEAN_GEO`, `OCEAN_WORK` to change); Natural Earth bathymetry and marine polygons come from github.com/nvkelso/natural-earth-vector and the Marine Regions files from github.com/CatalogueOfLife/col-gazetteers (`iho/` and `mrgid/`).

```
python3 code/01_grid.py        # depth grid, sea and IHO masks, Arctic cap
python3 code/02_eez.py         # national waters
python3 code/03_stats.py       # statistics and CSVs
python3 code/04_features.py    # trenches, profile, named features, page files
python3 code/05_results.py     # results.json
python3 code/06_build_site.py  # index.html
python3 code/07_figures.py     # figures and header
python3 code/08_paper.py       # paper PDF
python3 code/09_release.py     # blog, Zenodo files, README, LICENSE
python3 reddit/collage.py      # collage
python3 code/10_qa.py          # screenshots and console check
```

## Sources and licences

- AWS Terrain Tiles, Mapzen and the Registry of Open Data on AWS: https://registry.opendata.aws/terrain-tiles/. Sources and terms: https://github.com/tilezen/joerd/blob/master/docs/attribution.md (under the sea ETOPO1, GEBCO and SRTM15+; on land SRTM, GMTED2010 and national models). The tiles are not redistributed here.
- ETOPO1 and ETOPO10 (NOAA, Amante and Eakins 2009). Public domain.
- Marine Regions (Flanders Marine Institute, VLIZ): IHO Sea Areas v3, Exclusive Economic Zones, gazetteer. CC BY 4.0. Via https://github.com/CatalogueOfLife/col-gazetteers.
- Natural Earth (public domain). English Wikipedia, 'Oceanic trench' (CC BY-SA 4.0).
- Published depths: Greenaway et al. (2021); Bongiovanni, Stewart and Jamieson (2022); Stewart and Jamieson (2019). Seabed 2030 and GEBCO ({S['grid']}). Charette and Smith (2010). Kim and Wessel (2011).
- Base map tiles on the page © Esri.

## Citation

Hotham, T. (2026) How deep is the sea? Ocean depth, trenches and the unmapped sea floor, from open data. Zenodo. {{https://doi.org/10.5281/zenodo.23850291}}

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
"""
for bad in DASH: assert bad not in readme.replace("|---|---|", ""), bad
assert "DSIT" not in readme and "DCMS" not in readme
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write("""MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, the figures and the derived data in data/ are released
under CC BY 4.0. Derived data include material from Marine Regions (Flanders
Marine Institute, CC BY 4.0: sea areas, zones and feature names), which must be
credited when reused. Natural Earth is public domain. Depth statistics are
derived from the AWS Terrain Tiles; see
https://github.com/tilezen/joerd/blob/master/docs/attribution.md for the terms
of each source. The tiles are not redistributed.
""")

# Zenodo
Z = os.path.join(ROOT, "release", "zenodo"); os.makedirs(Z, exist_ok=True)
pt = open(os.path.join(ROOT, "release", "paper", NAME + ".tex"), encoding="utf-8").read()
ab = pt.split("\\begin{center}\\textbf{Abstract}\\end{center}")[1].split("\\textbf{Keywords:}")[0].strip()
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("~", " ").replace("$\\pm$", "±")
assert "\\" not in ab and "$" not in ab, ab
zmeta = dict(
    title="How Deep Is the Sea? Ocean Depth, Trenches and the Unmapped Sea Floor, from Open Data",
    upload_type="publication", publication_type="workingpaper",
    description=(f"<p>{ab}</p><p>Interactive version: <a href=\"https://maps.tristanhotham.com/ocean-depth/\">https://maps.tristanhotham.com/ocean-depth/</a>. "
                 "Data and code: <a href=\"https://github.com/Tristan-Hotham/ocean-depth\">https://github.com/Tristan-Hotham/ocean-depth</a>. Blog post: https://blog.tristanhotham.com/2026/10/31/ocean-depth/.</p>"
                 "<p>Text, figures and derived data: CC BY 4.0; code: MIT. Depths: AWS Terrain Tiles (Mapzen; under the sea ETOPO1, GEBCO and SRTM15+, sources listed at "
                 "github.com/tilezen/joerd), not redistributed. Sea areas, Exclusive Economic Zones and undersea feature names: Marine Regions (VLIZ), CC BY 4.0. "
                 "Land, lakes and bathymetry polygons: Natural Earth (public domain).</p>"),
    creators=[{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
    keywords=["bathymetry", "ocean depth", "sea floor", "hypsometry", "ocean trenches", "hadal zone", "seamounts", "exclusive economic zones", "Mariana Trench", "Seabed 2030", "terrain tiles", "data visualisation"],
    license="cc-by-4.0", language="eng",
    related_identifiers=[
        dict(identifier="https://github.com/Tristan-Hotham/ocean-depth", relation="isSupplementedBy", resource_type="software"),
        dict(identifier="https://maps.tristanhotham.com/ocean-depth/", relation="isSupplementedBy", resource_type="other"),
        dict(identifier="https://registry.opendata.aws/terrain-tiles/", relation="isDerivedFrom", resource_type="dataset"),
        dict(identifier="10.7289/V5C8276M", relation="isDerivedFrom", scheme="doi", resource_type="dataset"),
        dict(identifier="10.14284/323", relation="isDerivedFrom", scheme="doi", resource_type="dataset"),
        dict(identifier="https://www.marineregions.org/", relation="isDerivedFrom", resource_type="dataset"),
        dict(identifier="https://www.naturalearthdata.com/", relation="isDerivedFrom", resource_type="dataset")])
s = json.dumps(zmeta, ensure_ascii=False)
for bad in DASH: assert bad not in s, bad
zmeta["upload_files"] = [f"release/paper/{NAME}.pdf", "release/zenodo/ocean-depth_code_and_data.zip"] + [f"data/{f}" for f in
                         ["results.json", "depth_bands.csv", "oceans.csv", "seas.csv", "eez.csv", "eez_by_state.csv", "trenches.csv", "mariana_profile.csv", "hypsometry_earth.csv", "undersea_features.csv"]]
json.dump(zmeta, open(os.path.join(Z, "metadata.json"), "w"), indent=2, ensure_ascii=False)
for fn in os.listdir(Z):
    if fn not in ("metadata.json", "ocean-depth_code_and_data.zip"): os.remove(os.path.join(Z, fn))
zp = os.path.join(Z, "ocean-depth_code_and_data.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zf:
    for base in ("code", "data", "reddit"):
        for dp, dn, fn in os.walk(os.path.join(ROOT, base)):
            dn[:] = [d for d in dn if d != "__pycache__"]
            for f in fn:
                if f.endswith(".png") or f.endswith(".pdf"): continue
                zf.write(os.path.join(dp, f), os.path.join("ocean-depth", os.path.relpath(os.path.join(dp, f), ROOT)))
    for f in ("README.md", "LICENSE", "index.html", "header.png"): zf.write(os.path.join(ROOT, f), os.path.join("ocean-depth", f))
print("release written; blog words", words, "images", len(imgs))
for f in sorted(os.listdir(Z)): print(" ", f, os.path.getsize(os.path.join(Z, f)) // 1024, "KB")
