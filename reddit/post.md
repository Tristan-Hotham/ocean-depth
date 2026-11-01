## Title

[OC] How deep is the sea? The average sea floor is 3,675 m down, 74% of it lies 3 to 6 km deep, and Everest would fit in the Mariana Trench with 2,086 m of water to spare

## Body

I mapped the depth of the whole ocean floor from the open AWS Terrain Tiles (under the sea: ETOPO1, GEBCO and SRTM15+), with every 10 km cell weighted by its true area. The sea covers 71.2% of the Earth with a mean depth of 3,675 m (median 4,089 m). Only 7.7% of the floor is shallow continental shelf; 74% is abyssal plain and hill between 3,000 and 6,000 m, more than half of the planet's surface. The Pacific averages 3,943 m, the Arctic 1,205 m. The Challenger Deep is 10,935 m (2021 submersible survey). Caveat: a 10 km grid smooths the trenches (its deepest Mariana cell is 10,264 m, and its deepest cell overall is in the Tonga Trench), and only 28.7% of the sea floor is mapped to modern standards (Seabed 2030, 2026), so most of this map is a satellite-based estimate. Interactive map, where you can click anywhere for its depth: https://maps.tristanhotham.com/ocean-depth/

## Source comment

Source: AWS Terrain Tiles, Terrarium format (Mapzen; under the sea ETOPO1, GEBCO and SRTM15+; attribution at github.com/tilezen/joerd), zoom 4 grid; ETOPO10 north of 85° N; sea areas, Exclusive Economic Zones and undersea feature names from Marine Regions (VLIZ, CC BY 4.0); land and lakes from Natural Earth (public domain). Measured depths: Greenaway et al. 2021 (Challenger Deep); Bongiovanni, Stewart and Jamieson 2022 (Horizon, Brownson, Meteor, Java, Molloy); Wikipedia's Oceanic trench table for the rest. Mapping share: Seabed 2030 / GEBCO_2026.

Tools: Python (numpy, rasterio, shapely, pyproj, matplotlib); Leaflet for the interactive map, which decodes the depth tiles live in the browser.

Interactive version: https://maps.tristanhotham.com/ocean-depth/
Paper: https://doi.org/10.5281/zenodo.23850291
Blog post: https://blog.tristanhotham.com/2026/10/31/ocean-depth/
