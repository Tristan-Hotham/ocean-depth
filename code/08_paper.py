"""Step 8. Paper PDF: fill code/paper_template.tex from data/results.json, write release/paper/Hotham_How_Deep_Is_the_Sea.tex
and compile it with xelatex (figures from step 7, read from release/blog/). Set OCEAN_DOI (for example
10.5281/zenodo.1234567) to print the DOI; without it the paper shows the placeholder 10.5281/zenodo.23850291.
Run: python3 code/08_paper.py
"""
import importlib.util, os, re, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("b", os.path.join(HERE, "06_build_site.py")); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
R = b.R
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_How_Deep_Is_the_Sea"
DOI = os.environ.get("OCEAN_DOI", "")
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "abs": return f"{abs(int(round(v))):,}"
    if f == "pct": return f"{v * 100:.0f}\\%"
    if f == "pct1": return f"{v * 100:.1f}\\%"
    if f == "pct2": return f"{v * 100:.2f}\\%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    return tex(str(v))


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(b.get(path.strip()), f.strip() or "raw")


P = lambda w: f">{{\\raggedright\\arraybackslash}}p{{{w}}}"
TS = ("\\begin{table}[tbp]\\centering\\small\\caption{Sources, what was used and licences.}\\label{tab:sources}"
      f"\\begin{{tabular}}{{{P('3.8cm')}{P('7.4cm')}{P('3.2cm')}}}\\toprule Source & Used & Licence\\\\\\midrule\n"
      "AWS Terrain Tiles (Terrarium; sea floor from ETOPO1, GEBCO, SRTM15+) & Zoom 4 grid for statistics; all zooms on the map & Per source; mostly public domain\\\\\n"
      "ETOPO10 (from ETOPO1) & Arctic north of 85.05 N; Antarctic interior for the Earth histogram & Public domain\\\\\n"
      "Natural Earth & Land, lakes, countries, places, marine names; bathymetry polygons as a check & Public domain\\\\\n"
      f"Marine Regions (VLIZ) & IHO sea areas; {R['eez']['n_zones']} EEZs, joint regimes and claims; {R['features']['n']:,} undersea feature names & CC BY 4.0\\\\\n"
      "Published surveys and Wikipedia & Depths of the deepest places (Table~\\ref{tab:trenches}) & Cited; Wikipedia CC BY-SA 4.0\\\\\n"
      "Seabed 2030 / GEBCO & Share of the floor mapped to modern standards & Cited\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{o['name']} & {o['area_m']:.1f} & {o['mean']:,} & {o['median']:,} & {o['shelf'] * 100:.1f} & {o['hadal'] * 100:.2f} & {o['max']:,} & {tex(o['pub_name'])}, {o['pub']:,}\\\\\n" for o in R["oceans"])
o = R["ocean"]
TO = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{The five oceans on the zoom 4 grid: area (million km²), mean and median depth (m), shares shallower than 200 m and deeper than 6,000 m (\\%), "
      "deepest grid cell (m) and the deepest measured place (m).}\\label{tab:oceans}"
      "\\begin{tabular}{lrrrrrrl}\\toprule Ocean & Area & Mean & Median & Shelf & Hadal & Deepest cell & Deepest measured\\\\\\midrule\n" + rows +
      f"\\midrule All & {o['area_m']:.1f} & {o['mean']:,} & {o['median']:,} & {o['shelf'] * 100:.1f} & {o['hadal'] * 100:.2f} & {o['max']:,} & Challenger Deep, {R['mariana']['published']:,}\\\\\n\\bottomrule\\end{{tabular}}\\end{{table}}".replace("{{", "{").replace("}}", "}"))
SRC = {"greenaway": "Greenaway et al. 2021", "bongiovanni": "Bongiovanni et al. 2022", "stewart": "Stewart and Jamieson 2019", "wptrench": "Wikipedia"}
rows = "".join(f"{tex(t['name'].replace(', south of 60° S', ' (S of 60°)'))} & {tex(t['deep'])} & {t['published']:,}{(' $\\pm$ ' + str(t['unc'])) if t['unc'] else ''} & {SRC[t['src']]} & {t['grid']:,} & {t['shortfall']:,}\\\\\n" for t in R["trenches"])
TT = ("\\begin{table}[tbp]\\centering\\footnotesize\\setlength{\\tabcolsep}{4pt}\\caption{The deepest places: published depth and source, deepest cell of the zoom 4 grid along the trench, and the difference (m; negative where the grid is deeper).}\\label{tab:trenches}"
      f"\\begin{{tabular}}{{{P('4.2cm')}{P('2.4cm')}rlrr}}\\toprule Trench & Deepest point & Published & Source & Grid & Difference\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{c['depth']:,} & {c['ne_m']:.1f} & {c['grid_m']:.1f}\\\\\n" for c in R["ne_check"] if c["depth"] <= 8000)
TN = ("\\begin{table}[tbp]\\centering\\small\\caption{Sea area deeper than each depth: Natural Earth's bathymetry polygons (areas on the WGS84 ellipsoid) and the zoom 4 grid (million km²).}\\label{tab:ne}"
      "\\begin{tabular}{rrr}\\toprule Deeper than (m) & Natural Earth & Grid\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(HERE, "paper_template.tex"), encoding="utf-8").read()
link = f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\}\\}"
t = t.replace("{{DOILINK}}", link).replace("{{TABLE_SOURCES}}", TS).replace("{{TABLE_OCEANS}}", TO).replace("{{TABLE_TRENCHES}}", TT).replace("{{TABLE_NE}}", TN)
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_)([^{}]+?)\}\}", sub, t)
assert "{{" not in t.replace("\\{\\{DOI\\}\\}", "") and "--" not in t and "\u2014" not in t and "\u2013" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:10])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013"))
