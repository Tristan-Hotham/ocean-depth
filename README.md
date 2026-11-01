# How deep is the sea?

A detailed world map of ocean depth, drawn live in the browser from the open AWS Terrain Tiles at every zoom (depth tints, shaded sea floor relief, depth bands, a readout of any point), with the deepest trenches at their measured depths, named seamounts and national waters, and a study of how deep the sea is and how little of its floor is mapped.

**Interactive version:** https://maps.tristanhotham.com/ocean-depth/

**Paper and archived release:** {https://doi.org/10.5281/zenodo.23850291}

**Blog post:** {https://blog.tristanhotham.com/2026/10/31/ocean-depth/}

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

- The sea covers 362.9 million km², 71.2% of the Earth, with a mean depth of 3,675 m (median 4,089 m) and a volume of 1.33 billion km³ (Charette and Smith 2010: 3,682 m and 1.332 billion km³).
- Continental shelf above 200 m is 7.7% of the sea floor; slopes, rises and ridges from 200 to 3,000 m 17.3%; abyssal depths from 3,000 to 6,000 m 74.1%, more than half of the planet's surface; the hadal zone below 6,000 m 1.00%.
- Oceans: Pacific 3,943 m, Indian 3,775 m, Atlantic 3,606 m, Southern 3,213 m, Arctic 1,205 m on average.
- The Challenger Deep is 10,935 ± 6 m (Greenaway et al. 2021): Everest would sit 2,086 m under water. The 10 km grid's deepest Mariana cell is 10,264 m; its deepest cell anywhere is in the Tonga Trench (10,467 m); in 4 of 14 deep places it is deeper than any measured depth, pointing to errors in the source grids.
- National waters (EEZs, joint regimes and claims) cover 39% of the sea and hold 37% of the floor deeper than 6,000 m.
- Seabed 2030 reported in 2026 that 28.7% of the ocean floor is mapped to modern standards; about 259 million km² is known only roughly.

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Method in brief

- **Depths.** AWS Terrain Tiles (Terrarium encoding: height = R × 256 + G + B / 256 − 32,768 m; under the sea from ETOPO1, GEBCO and SRTM15+). The page decodes them live at zoom 0 to 14. The statistics use zoom 4, a 4,096 × 4,096 Web Mercator grid (9.8 km at the equator), each cell weighted by its exact area on a sphere and by its share of sea; 13 corrupt cells replaced by their neighbours' median. The Arctic north of 85.05° N from ETOPO10.
- **Sea.** Outside Natural Earth 1:10m land and lakes and joined to the world ocean (Caspian out, Black Sea in), rasterised at twice the grid's resolution. Sea cells averaging above 0 m count as 0 m deep. Sea under Antarctic ice shelves is missing.
- **Oceans, seas and national waters.** Marine Regions IHO sea areas (grouped into five oceans) and Exclusive Economic Zones, joint regimes and overlapping claims.
- **Trenches.** The deepest grid cell in a box round each of 14 trenches, set beside published depths (Greenaway et al. 2021; Bongiovanni, Stewart and Jamieson 2022; Stewart and Jamieson 2019; Wikipedia).
- **Check.** Natural Earth's bathymetry polygons give almost the same areas deeper than 200 m and 5.4% less deeper than 4,000 m.

## Files

| Path | What it is |
|---|---|
| `index.html` | The interactive page (results embedded; borders, places, national waters and undersea names load from `data/page/`; depth tiles load live from Amazon). |
| `header.png` | Social card (1200 by 630). |
| `data/depth_bands.csv` | Area and share of the sea floor (and of the Earth) in each depth band, overall and by ocean. |
| `data/oceans.csv`, `data/seas.csv` | Area, mean, median and deepest cell of each ocean and of each IHO sea area. |
| `data/eez.csv`, `data/eez_by_state.csv` | The same for each Exclusive Economic Zone, joint regime and claim, and grouped by state. |
| `data/trenches.csv` | 14 deepest places: published depth and source, point, and the grid's deepest cell along the trench. |
| `data/mariana_profile.csv` | Profile along 142.6° E through the Challenger Deep, every km. |
| `data/hypsometry_earth.csv` | Share of the Earth's surface in each 250 m step of height or depth. |
| `data/undersea_features.csv` | 5,638 named undersea features from the Marine Regions gazetteer with the grid depth at each. |
| `data/results.json` | Every number used anywhere. |
| `data/page/` | Page files. |
| `code/` | Numbered scripts (below), page, paper and blog templates. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `release/` | Paper PDF and LaTeX (its figures are the blog figures), blog post and figures, Zenodo metadata (with the list of files to upload) and the code-and-data zip. |
| `qa/` | Screenshots from the last check of the page. |

## Known limits

- The statistics are smoothed to about 10 km: trenches look hundreds of metres shallower and seamounts lower than they are, and band shares are good to about a percentage point.
- Most of the sea floor in the sources is predicted from satellite altimetry; some cells are wrong by hundreds of metres, as the trench comparison shows. Only 28.7% of the floor is mapped to modern standards (Seabed 2030, 2026).
- The grouping of IHO seas into oceans is one reasonable choice; Marine Regions zones include disputed claims. Published depths of the deepest places differ in age and accuracy.
- The global seamount census of Kim and Wessel (2011), 24,646 likely seamounts, is cited, not used: its host (soest.hawaii.edu) could not be reached when building.

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
- Published depths: Greenaway et al. (2021); Bongiovanni, Stewart and Jamieson (2022); Stewart and Jamieson (2019). Seabed 2030 and GEBCO (GEBCO_2026). Charette and Smith (2010). Kim and Wessel (2011).
- Base map tiles on the page © Esri.

## Citation

Hotham, T. (2026) How deep is the sea? Ocean depth, trenches and the unmapped sea floor, from open data. Zenodo. {https://doi.org/10.5281/zenodo.23850291}

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
