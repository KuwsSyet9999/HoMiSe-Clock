"""Regenerate S7 icons as Plan A (one self-contained vector per variant).

The layer-list + item-tint experiment (Plan B) rendered wrong on the launcher:
the digits layer disappeared, leaving only the ghost. Colours are therefore
baked into each vector (Plan A), at the cost of ~240 KB instead of ~143 KB.

Outputs:
  mipmap-anydpi-v26/ic_v<N>_fg.xml   foreground vector (ghost + digits)
  mipmap-anydpi-v26/ic_v<N>.xml      adaptive icon
  values/ic_variants.xml             background colours
"""
import os
import re
import importlib.util

from fontTools.ttLib import TTFont

ROOT = r"D:\DSHin\HoMiSe\s7"
RES = os.path.join(ROOT, "app", "src", "main", "res")
FONT_DIR = os.path.join(RES, "font")
MANIFEST = os.path.join(ROOT, "app", "src", "main", "AndroidManifest.xml")

spec = importlib.util.spec_from_file_location("mk", r"D:\DSHin\HoMiSe\tools\make-icon-variants.py")
mk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mk)

S, SAFE = mk.S, mk.SAFE
FAMS = ["hseg_7_classic", "hseg_7_classic_mini", "hseg_7_modern", "hseg_7_modern_mini"]
STYLES = ["light", "light_italic", "regular", "italic", "bold", "bold_italic"]
SCHEMES = [("dark", "#FFFFFF", "#333333", "#000000"),
           ("light", "#000000", "#CCCCCC", "#FFFFFF")]
COUNT = len(FAMS) * len(STYLES) * len(SCHEMES) * 2

_cache = {}


def geometry(font_path):
    if font_path in _cache:
        return _cache[font_path]
    tt = TTFont(font_path)
    upem = tt["head"].unitsPerEm
    ascent, descent = tt["hhea"].ascent, tt["hhea"].descent
    cmap = tt.getBestCmap()
    glyf = tt["glyf"]
    hmtx = tt["hmtx"]
    gpair = "8" * 2
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
    _cache[font_path] = res
    return res


def path_data(polys):
    return " ".join("M " + " L ".join("%.2f,%.2f" % p for p in poly) + " Z" for poly in polys)


def vector_xml(layers):
    body = "".join(
        '    <path android:fillColor="%s" android:pathData="%s" />\n' % (color, path)
        for color, path in layers)
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    android:width="108dp" android:height="108dp"\n'
        '    android:viewportWidth="432" android:viewportHeight="432">\n'
        '%s</vector>\n'
    ) % body


def main():
    anydpi = os.path.join(RES, "mipmap-anydpi-v26")
    values = os.path.join(RES, "values")
    drawable = os.path.join(RES, "drawable")
    os.makedirs(anydpi, exist_ok=True)
    os.makedirs(values, exist_ok=True)

    # drop the previous Plan-B artefacts
    for f in os.listdir(drawable):
        if f.startswith(("d_", "g_", "layer_", "test_")):
            os.remove(os.path.join(drawable, f))
    for f in os.listdir(anydpi):
        if f.startswith("ic_v"):
            os.remove(os.path.join(anydpi, f))

    colors = ['<?xml version="1.0" encoding="utf-8"?>', "<resources>"]
    n = 0
    for fam in FAMS:
        for style in STYLES:
            gpath, dpath = geometry(os.path.join(FONT_DIR, "%s_%s.ttf" % (fam, style)))
            for sch, fg, dim, bg in SCHEMES:
                for ghost_on in (True, False):
                    layers = []
                    if ghost_on:
                        layers.append((dim, gpath))
                    layers.append((fg, dpath))
                    with open(os.path.join(anydpi, "ic_v%d_fg.xml" % n), "w", encoding="utf-8") as f:
                        f.write(vector_xml(layers))
                    with open(os.path.join(anydpi, "ic_v%d.xml" % n), "w", encoding="utf-8") as f:
                        f.write(
                            '<?xml version="1.0" encoding="utf-8"?>\n'
                            '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                            '    <background android:drawable="@color/ic_v%d_bg" />\n'
                            '    <foreground android:drawable="@mipmap/ic_v%d_fg" />\n'
                            '</adaptive-icon>\n' % (n, n))
                    colors.append('    <color name="ic_v%d_bg">%s</color>' % (n, bg))
                    n += 1
    colors.append("</resources>")
    with open(os.path.join(values, "ic_variants.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(colors) + "\n")

    # manifest was already patched to 96 aliases; ensure the default icon points at v0
    text = open(MANIFEST, encoding="utf-8").read()
    if '@mipmap/ic_launcher"' in text:
        text = text.replace('android:icon="@mipmap/ic_launcher"', 'android:icon="@mipmap/ic_v0"')
    print("regenerated %d variants (plan A)" % n)


if __name__ == "__main__":
    main()
