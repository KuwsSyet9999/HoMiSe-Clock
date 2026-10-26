"""Generate the S7 icon set: vector layers + tinted layer-lists.

Plan B from the size study: each font contributes two white vector layers
(digits + all-lit ghost); the four colour/ghost combinations reuse them through
`<item android:tint>`, so the path data is stored once instead of per variant.

Outputs (all under s7/app/src/main/res):
  drawable/d_<font>.xml          digits layer
  drawable/g_<font>.xml          ghost layer
  drawable/layer_v<N>.xml        96 layer-list variants
  mipmap-anydpi-v26/ic_v<N>.xml  96 adaptive icons
  values/ic_variants.xml         background colours
Also rewrites the launcher aliases in AndroidManifest.xml (96 entries).
"""
import os
import re
import sys
import importlib.util

from fontTools.ttLib import TTFont

ROOT = r"D:\DSHin\HoMiSe\s7"
RES = os.path.join(ROOT, "app", "src", "main", "res")
FONT_DIR = os.path.join(RES, "font")
MANIFEST = os.path.join(ROOT, "app", "src", "main", "AndroidManifest.xml")

spec = importlib.util.spec_from_file_location("mk", r"D:\DSHin\HoMiSe\tools\make-icon-variants.py")
mk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mk)

S = mk.S
SAFE = mk.SAFE
FAMS = ["hseg_7_classic", "hseg_7_classic_mini", "hseg_7_modern", "hseg_7_modern_mini"]
STYLES = ["light", "light_italic", "regular", "italic", "bold", "bold_italic"]
SCHEMES = [("dark", "#FFFFFF", "#333333", "#000000"),
           ("light", "#000000", "#CCCCCC", "#FFFFFF")]
PHASES = [True, False]
COUNT = len(FAMS) * len(STYLES) * len(SCHEMES) * len(PHASES)

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


def vector_xml(path):
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    android:width="108dp" android:height="108dp"\n'
        '    android:viewportWidth="432" android:viewportHeight="432">\n'
        '    <path android:fillColor="#FFFFFF" android:pathData="%s" />\n'
        '</vector>\n'
    ) % path


def ensure_dir(p):
    os.makedirs(p, exist_ok=True)


def main():
    drawable = os.path.join(RES, "drawable")
    anydpi = os.path.join(RES, "mipmap-anydpi-v26")
    values = os.path.join(RES, "values")
    for d in (drawable, anydpi, values):
        ensure_dir(d)

    colors = ['<?xml version="1.0" encoding="utf-8"?>', "<resources>"]
    index = []
    n = 0
    for fam in FAMS:
        for style in STYLES:
            fpath = os.path.join(FONT_DIR, "%s_%s.ttf" % (fam, style))
            if not os.path.exists(fpath):
                raise SystemExit("missing font: " + fpath)
            gpath, dpath = geometry(fpath)
            base = "%s_%s" % (fam, style)
            with open(os.path.join(drawable, "d_%s.xml" % base), "w", encoding="utf-8") as f:
                f.write(vector_xml(dpath))
            with open(os.path.join(drawable, "g_%s.xml" % base), "w", encoding="utf-8") as f:
                f.write(vector_xml(gpath))
            for sch, fg, dim, bg in SCHEMES:
                for ghost_on in PHASES:
                    items = ""
                    if ghost_on:
                        items += '    <item android:drawable="@drawable/g_%s" android:tint="%s" />\n' % (base, dim)
                    items += '    <item android:drawable="@drawable/d_%s" android:tint="%s" />\n' % (base, fg)
                    layer = ('<?xml version="1.0" encoding="utf-8"?>\n'
                             '<layer-list xmlns:android="http://schemas.android.com/apk/res/android">\n'
                             '%s</layer-list>\n') % items
                    with open(os.path.join(drawable, "layer_v%d.xml" % n), "w", encoding="utf-8") as f:
                        f.write(layer)
                    with open(os.path.join(anydpi, "ic_v%d.xml" % n), "w", encoding="utf-8") as f:
                        f.write(
                            '<?xml version="1.0" encoding="utf-8"?>\n'
                            '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                            '    <background android:drawable="@color/ic_v%d_bg" />\n'
                            '    <foreground android:drawable="@drawable/layer_v%d" />\n'
                            '</adaptive-icon>\n' % (n, n))
                    colors.append('    <color name="ic_v%d_bg">%s</color>' % (n, bg))
                    index.append("%d\t%s\t%s\t%s\t%s" % (n, fam, style, sch,
                                                        "ghost_on" if ghost_on else "ghost_off"))
                    n += 1

    colors.append("</resources>")
    with open(os.path.join(values, "ic_variants.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(colors) + "\n")

    # ---- manifest aliases ----
    text = open(MANIFEST, encoding="utf-8").read()
    text = re.sub(r"\n *<activity-alias.*?</activity-alias>", "", text, flags=re.S)
    text = text.replace(
        'android:icon="@mipmap/ic_launcher"\n        android:roundIcon="@mipmap/ic_launcher_round"',
        'android:icon="@mipmap/ic_v0"\n        android:roundIcon="@mipmap/ic_v0"')
    text = re.sub(
        r'(<activity\b[^>]*?\bandroid:name="\.MainActivity"[^>]*?>)\s*'
        r'<intent-filter>.*?</intent-filter>\s*(</activity>)',
        r"\1\2", text, flags=re.S)
    text = text.replace(">\n        </activity>", " />")
    alias = """        <activity-alias
            android:name="${{applicationId}}.icon.IconV{i}"
            android:enabled="{enabled}"
            android:exported="true"
            android:icon="@mipmap/ic_v{i}"
            android:label="@string/app_name"
            android:targetActivity=".MainActivity">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity-alias>
"""
    aliases = "\n" + "".join(
        alias.format(i=i, enabled="true" if i == 0 else "false") for i in range(COUNT))
    text = text.replace("    </application>", aliases + "    </application>")
    with open(MANIFEST, "w", encoding="utf-8") as f:
        f.write(text)

    print("generated %d variants, %d drawables" % (COUNT, len(FAMS) * len(STYLES) * 2 + COUNT))
    print("manifest aliases:", COUNT)


if __name__ == "__main__":
    main()
