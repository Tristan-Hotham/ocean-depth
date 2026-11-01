"""Shared paths and helpers for the ocean-depth study ("How deep is the sea?").

Raw inputs (read in place, never copied into the repo):
  TILES    AWS Terrain Tiles, Terrarium encoding, zoom 4 (16 x 16 tiles of 256 px, Web Mercator):
           TILES/4/{x}/{y}.png, height_m = R*256 + G + B/256 - 32768 (negative = below sea level).
           Live copies: https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png
           Ocean depths in the tiles come from ETOPO1, GEBCO and SRTM15+ (see
           https://github.com/tilezen/joerd/blob/master/docs/attribution.md).
  ETOPO10  10 arc minute grid derived from ETOPO1 (fills the Arctic Ocean north of the Mercator limit, 85.05 N)
  NE_BATHY Natural Earth 10m bathymetry polygons (ne_10m_bathymetry_{A_10000..L_0}.geojson) and marine area names
           (ne_10m_geography_marine_polys.geojson), from
           https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/
  MR       Marine Regions (VLIZ, CC BY 4.0) as packaged by https://github.com/CatalogueOfLife/col-gazetteers:
           iho/features/*.geojson (IHO S-23 sea areas, 101) and mrgid/features/<MRGID>.geojson for every
           Exclusive Economic Zone, joint regime, trench, deep, seamount, guyot, knoll and other undersea feature
           listed in mrgid/labels.tsv (selection in MR/sel.tsv).
  GEO      Natural Earth 10m countries (land) and populated places; Natural Earth 10m lakes in BORDERS.
Intermediates are written to WORK (outside the repo by default)."""
import json, os, re, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW3 = os.environ.get("OCEAN_RAW", "/home/claude/newdata/raw3")
TILES = os.path.join(RAW3, "terrarium_z4")
ETOPO10 = os.path.join(RAW3, "dem", "etopo10", "etopo10_ice_g_i2.bin")
OCEAN = os.path.join(RAW3, "ocean")
NE_BATHY = OCEAN
MR = os.path.join(OCEAN, "mr")
BORDERS = os.path.join(RAW3, "borders")
GEO = os.environ.get("OCEAN_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("FONT_DIR", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
PAGE = os.path.join(DATA, "page")
WORK = os.environ.get("OCEAN_WORK", "/home/claude/work/ocean-depth")
for d in (DATA, PAGE, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "ocean-depth"
PAGE_URL = "https://maps.tristanhotham.com/ocean-depth/"
REPO = "https://github.com/Tristan-Hotham/ocean-depth"
TILE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

Z = 4
N = 256 * 2 ** Z           # 4096 pixels around the world
R_EARTH = 6371.0088        # mean radius, km (for areas)
MERC_LAT = math.degrees(math.atan(math.sinh(math.pi)))   # 85.0511
BANDS = [0, 200, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 12000]   # depth bands, metres below sea level

# Published depths of the deepest places (cited in the paper; the grid's own values are computed in 03_features.py).
# Each: key, name, deepest point, ocean, published depth m, +/- m or None, source key, lon, lat (published point where given),
# and a search box (lon0, lat0, lon1, lat1) for the grid's deepest cell along the trench.
SOURCES = {
    "greenaway": "Greenaway, S.F., Sullivan, K.D., Umfress, S.H., Beittel, A.B. and Wagner, K.D. (2021) Revised depth of the Challenger Deep from submersible transects; including a general method for precise, pressure-derived depth estimates. Progress in Oceanography, 195, 102564.",
    "bongiovanni": "Bongiovanni, C., Stewart, H.A. and Jamieson, A.J. (2022) High-resolution multibeam sonar bathymetry of the deepest place in each ocean. Geoscience Data Journal, 9(1), 108 to 123. doi:10.1002/gdj3.122",
    "stewart": "Stewart, H.A. and Jamieson, A.J. (2019) The five deeps: the location and depth of the deepest place in each of the world's oceans. Earth-Science Reviews, 197, 102896.",
    "wptrench": "Wikipedia contributors (2026) Oceanic trench, table of the deepest trenches. English Wikipedia, CC BY-SA 4.0. https://en.wikipedia.org/wiki/Oceanic_trench",
}
TRENCHES = [
    ("mariana", "Mariana Trench", "Challenger Deep", "Pacific", 10935, 6, "greenaway", 142.588, 11.372, (141.0, 10.5, 148.5, 21.0)),
    ("tonga", "Tonga Trench", "Horizon Deep", "Pacific", 10816, 16, "bongiovanni", -174.73, -23.26, (-177.5, -27.0, -172.0, -14.5)),
    ("philippine", "Philippine Trench", "Emden Deep", "Pacific", 10540, None, "wptrench", 126.6, 10.4, (125.8, 5.5, 128.5, 14.5)),
    ("kermadec", "Kermadec Trench", "Scholl Deep", "Pacific", 10047, None, "wptrench", -177.4, -31.9, (-179.6, -37.0, -175.5, -27.0)),
    ("izubonin", "Izu-Ogasawara (Bonin) Trench", "deepest point", "Pacific", 9810, None, "wptrench", 142.8, 29.0, (140.5, 23.5, 145.0, 34.5)),
    ("kuril", "Kuril-Kamchatka Trench", "deepest point", "Pacific", 9604, None, "wptrench", 150.2, 44.1, (143.5, 40.5, 164.0, 55.0)),
    ("japan", "Japan Trench", "deepest point", "Pacific", 8412, None, "wptrench", 144.2, 39.0, (141.5, 35.6, 146.0, 41.0)),
    ("puertorico", "Puerto Rico Trench", "Brownson Deep", "Atlantic", 8378, None, "bongiovanni", -67.311, 19.712, (-70.5, 18.6, -61.5, 20.6)),
    ("southsandwich", "South Sandwich Trench", "Meteor Deep", "Atlantic", 8265, 13, "bongiovanni", -26.0, -55.5, (-29.5, -60.0, -23.5, -54.0)),
    ("atacama", "Peru-Chile (Atacama) Trench", "Richards Deep", "Pacific", 8055, None, "wptrench", -71.6, -23.4, (-82.0, -45.0, -70.5, -3.0)),
    ("cayman", "Cayman Trough", "deepest point", "Atlantic", 7686, None, "wptrench", -80.0, 18.5, (-86.0, 17.0, -75.0, 20.5)),
    ("factorian", "South Sandwich Trench, south of 60° S", "Factorian Deep", "Southern", 7432, None, "bongiovanni", -25.542, -60.479, (-28.5, -61.5, -23.0, -60.0)),
    ("java", "Java (Sunda) Trench", "deepest point", "Indian", 7187, None, "bongiovanni", 114.942, -11.129, (95.0, -13.0, 122.0, -5.0)),
    ("molloy", "Molloy Hole, Fram Strait", "Molloy Hole", "Arctic", 5551, None, "bongiovanni", 2.706, 79.194, (0.0, 78.5, 5.5, 80.0)),
]
EVEREST = 8849             # Mount Everest, 2020 China-Nepal survey
SEABED2030 = dict(pct=28.7, prev=27.3, grid="GEBCO_2026", year=2026, mapped_mkm2=104, added_mkm2=5,
                  src="Seabed 2030 and GEBCO, 'Release of the GEBCO_2026 grid' (gebco.net) and IHO news release, 2026: '28.7% of the world's ocean floor has now been mapped to modern standards', up from 27.3% in the 2025 grid; about 104 million km² mapped, almost 5 million km² added in a year.")
CHARETTE = dict(mean=3682.2, volume_bn=1.332, src="Charette, M.A. and Smith, W.H.F. (2010) The volume of Earth's ocean. Oceanography, 23(2), 112 to 114.")
KW2011 = dict(n=24646, src="Kim, S.-S. and Wessel, P. (2011) New global seamount census from altimetry-derived gravity data. Geophysical Journal International, 186(2), 615 to 631. The catalogue file KWSMTSv01.txt (header: '24,646 potential seamounts') is published at http://www.soest.hawaii.edu/PT/SMTS/kwsmts/, which the build container could not reach.")


def dash(v):
    """House style: no em or en dashes, no double hyphens, in anything written to data/."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, tuple):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def _np(o):
    import numpy as np
    if isinstance(o, np.integer): return int(o)
    if isinstance(o, np.floating): return float(o)
    if isinstance(o, np.bool_): return bool(o)
    if isinstance(o, np.ndarray): return o.tolist()
    raise TypeError(type(o))


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"), default=_np)


def jload(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def lat_of_row(j):
    """Latitude of the top edge of row j (0..N) on the zoom 4 grid."""
    import numpy as np
    return np.degrees(np.arctan(np.sinh(np.pi * (1 - 2 * np.asarray(j, float) / N))))


def rc_of(lon, lat):
    """Row and column (floats) of a lon/lat point on the zoom 4 grid."""
    import numpy as np
    lat = np.clip(np.asarray(lat, float), -MERC_LAT + 1e-9, MERC_LAT - 1e-9)
    x = (np.asarray(lon, float) + 180) / 360 * N
    y = (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / np.pi) / 2 * N
    return y, x


def lonlat_of_rc(r, c):
    import numpy as np
    lon = (np.asarray(c, float) + .5) / N * 360 - 180
    return lon, lat_of_row(np.asarray(r, float) + .5)


def hav(lon1, lat1, lon2, lat2):
    import numpy as np
    p = np.pi / 180
    a = np.sin((lat2 - lat1) * p / 2) ** 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * np.sin((lon2 - lon1) * p / 2) ** 2
    return 2 * R_EARTH * np.arcsin(np.sqrt(a))


def to_merc(g):
    """Shapely geometry lon/lat -> EPSG 3857 metres."""
    import numpy as np, shapely
    from pyproj import Transformer
    tr = Transformer.from_crs(4326, 3857, always_xy=True)
    return shapely.transform(g, lambda xy: np.column_stack(tr.transform(xy[:, 0], np.clip(xy[:, 1], -MERC_LAT, MERC_LAT))))
