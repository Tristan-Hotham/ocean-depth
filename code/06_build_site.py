"""Step 6. Build index.html from code/page_template.html, code/page_style.css and code/fullscreen_snippet.html. Every
number in the text is a {{path|format}} token filled from data/results.json; facts stated in words are checked by the
asserts below (they cover the page, paper, blog and collage). 10.5281/zenodo.23850291, https://doi.org/10.5281/zenodo.23850291 and https://blog.tristanhotham.com/2026/10/31/ocean-depth/ are left for the publisher.
Run: python3 code/06_build_site.py
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path.insert(0, HERE)
R = json.load(open(os.path.join(ROOT, "data", "results.json"), encoding="utf-8"))
PLACEHOLDERS = {"DOI", "DOI_URL", "BLOG_URL"}


def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(v):,}"
    if f == "abs": return f"{abs(round(v)):,}"
    if f == "pct": return f"{round(v * 100)}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "pct2": return f"{v * 100:.2f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    raise ValueError(f)


def sub(m):
    if m.group(1).strip() in PLACEHOLDERS:
        return m.group(0)
    return fmt(get(m.group(1).strip()), m.group(3))


# ---- facts stated in words (page, paper, blog, collage) ----
o, oc = R["ocean"], R["oc"]
assert o["median"] > 4000                                                  # 'half the sea floor is deeper than four kilometres'
assert o["abyssal_earth"] > .5                                             # 'more than half of the whole planet's surface'
assert o["abyssal"] > .7 and o["shelf"] < .08 and o["hadal"] < .011
assert max(R["oceans"], key=lambda x: x["mean"])["name"] == "Pacific" and max(R["oceans"], key=lambda x: x["area_m"])["name"] == "Pacific"
assert [x["name"] for x in sorted(R["oceans"], key=lambda x: -x["mean"])] == ["Pacific", "Indian", "Atlantic", "Southern", "Arctic"]
assert .35 < oc["Arctic"]["shelf"] < .45                                   # 'two fifths of it is shallow continental shelf'
assert R["sea"]["philippine"]["mean"] > oc["Pacific"]["mean"]
assert R["ocean"]["max_lat"] < -20 and R["ocean"]["max_lon"] < -170       # the deepest grid cell is in the Tonga Trench
assert R["tr"]["tonga"]["grid"] == R["ocean"]["max"] and R["mariana"]["tonga_grid_deeper"]
assert R["eez"]["top"][0]["name"] == "Tongan EEZ" and R["eez"]["top"][1]["name"] == "Micronesian EEZ"
assert R["n_grid_deeper"] == 4, R["grid_deeper_names"]
assert R["mariana"]["above_everest"] == 2086 and R["mariana"]["published"] == 10935
assert R["seabed2030"]["unmapped_m"] > 150                                 # 'larger than all the land on Earth' (about 149 million km2)
assert R["eez"]["national_mean"] < R["eez"]["high_mean"]
assert abs(R["ocean"]["mean"] - R["charette"]["mean"]) < 15
assert max(R["trenches"], key=lambda t: t["shortfall"])["key"] == "philippine"
assert R["grid_deeper_names"] == ["Puerto Rico Trench", "Cayman Trough", "Java (Sunda) Trench", "Molloy Hole, Fram Strait"], R["grid_deeper_names"]
assert 95 < R["oc"]["Indian"]["max_lon"] < 105 and -25 < R["oc"]["Indian"]["max_lat"] < -15        # 'a narrow trough in the Wharton Basin'
assert R["ne"]["d200"] < .01 and R["ne"]["d4000"] > .03
assert R["bands"][5]["lo"] == 4000 and R["bands"][5]["share"] == max(b["share"] for b in R["bands"])
assert R["earth"]["peak_deep"][0] in (-5000, -4750, -4500, -4250) and R["earth"]["peak_high"][0] == 0
# Challenger Deep in the Micronesian zone (point in polygon on the Marine Regions shape)
from common import MR, jload
from shapely.geometry import shape, Point
fsm = [z for z in jload(os.path.join(os.environ.get("OCEAN_WORK", "/home/claude/work/ocean-depth"), "eezs.json"))[1:] if z["name"].startswith("Micronesian")][0]
assert shape(jload(f"{MR}/mrgid/{fsm['mrgid']}.geojson")["geometry"]).contains(Point(R["tr"]["mariana"]["lon"], R["tr"]["mariana"]["lat"]))
guam = [z for z in jload(os.path.join(os.environ.get("OCEAN_WORK", "/home/claude/work/ocean-depth"), "eezs.json"))[1:] if "(Guam)" in z["name"]][0]
assert shape(jload(f"{MR}/mrgid/{guam['mrgid']}.geojson")["geometry"]).distance(Point(R["tr"]["mariana"]["lon"], R["tr"]["mariana"]["lat"])) < 1.0   # 'just south of Guam's waters'

TOK = re.compile(r"\{\{([^}|]+)(\|(\w+))?\}\}")


def check_text(html):
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in vis, bad
    return vis


if __name__ == "__main__":
    tpl = open(os.path.join(HERE, "page_template.html"), encoding="utf-8").read()
    tpl = tpl.replace("/*CSS*/", open(os.path.join(HERE, "page_style.css"), encoding="utf-8").read())
    tpl = tpl.replace("/*FULLSCREEN*/", open(os.path.join(HERE, "fullscreen_snippet.html"), encoding="utf-8").read().strip())
    html = TOK.sub(sub, tpl)
    PD = dict(R=R, trenches=json.load(open(os.path.join(ROOT, "data", "page", "trenches.json"), encoding="utf-8")),
              seas=json.load(open(os.path.join(ROOT, "data", "page", "seas.json"), encoding="utf-8")))
    html = html.replace("/*PD*/", json.dumps(PD, ensure_ascii=False, separators=(",", ":")))
    left = set(re.findall(r"\{\{(\w+)\}\}", html))
    assert left <= PLACEHOLDERS and "{{" not in re.sub(r"\{\{(DOI|DOI_URL|BLOG_URL)\}\}", "", html), left
    check_text(html)
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()), "bytes")
