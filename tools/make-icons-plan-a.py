"""Generate every icon variant as a self-contained vector (Plan A).

Each variant is one VectorDrawable holding the ghost layer (optional) and the
digits layer, with colours baked in. `layer-list` + item tint was tried first
(Plan B) and failed on the launcher: only the ghost layer rendered, so every
variant now carries its own colours.

Outputs (app/src/main/res):
  mipmap-anydpi-v26/ic_v<N>_fg.xml  foreground vector
Existing adaptive-icon descriptors `ic_v<N>.xml` keep referencing @mipmap/ic_v<N>_fg.
"""
import os
import importlib.util

from fontTools.ttLib import TTFont

ROOT = r"D:\DSHin\HoMiSe"
RES = os.path.join(ROOT, "app", "src", "main", "res")
FONT_DIR = os.path.join(RES, "font")

spec = importlib.util.spec_from_file_location("mk", os.path.join(ROOT, "tools", "make-icon-variants.py"))
mk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mk)

S, SAFE = mk.S, mk.SAFE
FAMS = [
    ("hseg_7_classic", "8"),
    ("hseg_7_classic_mini", "8"),
    ("hseg_7_modern", "8"),
    ("hseg_7_modern_mini", "8"),
    ("hseg_16_classic", "~"),
    ("hseg_16_classic_mini", "~"),
    ("hseg_16_modern", "~"),
    ("hseg_16_modern_mini", "~"),
]
STYLES = ["light", "light_italic", "regular", "italic", "bold", "bold_italic"]
SCHEMES = [("#FFFFFF", "#333333"), ("#000000", "#CCCCCC")]
COUNT = len(FAMS) * len(STYLES) * len(SCHEMES) * 2

_cache = {}


def geometry(font_path, ghost_char):
    key = (font_path, ghost_char)
    if key in _cache:
        return _cache[key]
    tt = TTFont(font_path)
    upem = tt["head"].unitsPerEm
    ascent, descent = tt["hhea"].ascent, tt["hhea"].descent
    cmap = tt.getBestCmap()
    glyf = tt["glyf"]
    hmtx = tt["hmtx"]
    gpair = ghost_char * 2
    glong = ":".join([gpair] * 3)
    row_ink, row_offset = mk.probe_cached(font_path, glong)
    colon_ink, _ = mk.probe_cached(font_path, ":")
    px = int(round(SAFE / (row_ink + 2 * colon_ink)))
    dx = -row_offset * px
    line_box = px * 1.2
    scale = px / upem
    base_off = (ascent - descent) / 2 * scale
    rows = [(gpair, "21"), (glong, "09:36:58"), (gpair, "47")]

    def polylines(text, cx, cy):
        polys = []
        adv = sum(hmtx[cmap[ord(c)]][0] for c in text if ord(c) in cmap) * scale
        pen = cx - adv / 2
        baseline = cy + base_off
        for c in text:
            if ord(c) not in cmap:
                continue
            g = glyf[cmap[ord(c)]]
            if g.numberOfContours > 0:
                coords, ends, _ = g.getCoordinates(glyf)
                start = 0
                for e in ends:
                    polys.append([(pen + coords[i][0] * scale, baseline - coords[i][1] * scale)
                                  for i in range(start, e + 1)])
                    start = e + 1
            pen += hmtx[cmap[ord(c)]][0] * scale
        return polys

    cx = S / 2 + dx
    ghost_polys, digit_polys = [], []
    for i, (g, w) in enumerate(rows):
        cy = S / 2 + (i - 1) * line_box
        ghost_polys += polylines(g, cx, cy)
        digit_polys += polylines(w, cx, cy)
    res = (path_data(ghost_polys), path_data(digit_polys))
    _cache[key] = res
    return res


def path_data(polys):
    return " ".join("M " + " L ".join("%.2f,%.2f" % p for p in poly) + " Z" for poly in polys)


def vector_xml(layers):
    body = "".join('    <path android:fillColor="%s" android:pathData="%s" />\n' % (c, p)
                   for c, p in layers)
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
            '    android:width="108dp" android:height="108dp"\n'
            '    android:viewportWidth="432" android:viewportHeight="432">\n'
            '%s</vector>\n') % body


def main():
    anydpi = os.path.join(RES, "mipmap-anydpi-v26")
    for dens in ("xxhdpi", "xxxhdpi"):
        d = os.path.join(RES, "mipmap-" + dens)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.startswith("ic_v") and f.endswith(".webp"):
                os.remove(os.path.join(d, f))

    n = 0
    for fam, ghost in FAMS:
        for style in STYLES:
            gpath, dpath = geometry(os.path.join(FONT_DIR, "%s_%s.ttf" % (fam, style)), ghost)
            for fg, dim in SCHEMES:
                for ghost_on in (True, False):
                    layers = []
                    if ghost_on:
                        layers.append((dim, gpath))
                    layers.append((fg, dpath))
                    with open(os.path.join(anydpi, "ic_v%d_fg.xml" % n), "w",
                              encoding="utf-8") as f:
                        f.write(vector_xml(layers))
                    n += 1
    print("generated %d foreground vectors" % n)


if __name__ == "__main__":
    main()
