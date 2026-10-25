"""Generate every launcher-icon variant: font family x style x colour scheme.

8 families x 6 styles x 2 schemes = 96 adaptive icons, each rendered at 5 densities.

Layout inside every icon (same as the confirmed design):

        09
    16:25:38
        47

with a grey "all-segments-lit" ghost underneath -- `8` for the 7-segment families,
`~` for the 14-segment ones. The ghost is drawn with the *same* font as the digits,
so the two layers stay in register.

Per-variant font size is measured from that font's own ghost row, so "one colon ink
width of clearance to the safe-zone edge" holds for every family rather than only
for DSEG7 Classic.

Outputs:
  res/mipmap-<density>/ic_v<N>_fg.png     foreground (transparent)
  res/mipmap-anydpi-v26/ic_v<N>.xml       adaptive-icon descriptor
  res/values/ic_variants.xml              one background colour per variant
"""
import os
import glob
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = r"D:\DSHin\HoMiSe\app\src\main\res\font"
RES_DIR = r"D:\DSHin\HoMiSe\app\src\main\res"
OUT_INDEX = r"D:\DSHin\HoMiSe\docs\icon\variants.txt"

S = 432                    # 108 dp @ 4x
SAFE = 264                 # 66 dp adaptive-icon safe zone
MARGIN = (S - SAFE) / 2
COLON_INK = 0.124          # DSEG7 Classic reference; refined per family below
DIGIT_SIDE = 0.099

FAMILIES = [
    ("7classic", "hseg_7_classic", "8"),
    ("7classicmini", "hseg_7_classic_mini", "8"),
    ("7modern", "hseg_7_modern", "8"),
    ("7modernmini", "hseg_7_modern_mini", "8"),
    ("14classic", "hseg_16_classic", "~"),
    ("14classicmini", "hseg_16_classic_mini", "~"),
    ("14modern", "hseg_16_modern", "~"),
    ("14modernmini", "hseg_16_modern_mini", "~"),
]
STYLES = ["light", "light_italic", "regular", "italic", "bold", "bold_italic"]
SCHEMES = [
    ("dark", (0, 0, 0, 255), (255, 255, 255, 255), (51, 51, 51, 255)),
    ("light", (255, 255, 255, 255), (0, 0, 0, 255), (204, 204, 204, 255)),
]
DENSITIES = [("xxhdpi", 324), ("xxxhdpi", 432)]
# Only two densities are shipped. With minSdk 26 the real-world densities are >= 420 dpi,
# so mdpi / hdpi / xhdpi (43 % of the files) would never be picked on a modern device.
#
# Output format is LOSSLESS WebP: measured at 36 % of the PNG size on this artwork
# (flat colours plus crisp strokes), with no quality loss at all.
# Lossy WebP is *worse* here -- 86 % of PNG -- because these icons are almost all
# high-contrast edges, which lossy compression handles poorly.
FORMAT = "WEBP"
SAVE_KWARGS = {"lossless": True, "method": 6}
EXT = ".webp"


def draw_text(draw, text, px, cx, cy, fill):
    font = ImageFont.truetype(px[0], px[1])
    draw.text((cx, cy), text, font=font, fill=fill, anchor="mm")


REF = 200          # probe font size
PROBE_CANVAS = 1600  # generously large so a full row is never clipped


def probe_ink(font_path, text):
    """Return (ink_width_ratio, ink_centre_offset_ratio) of `text`, by rendering it.

    Measured by rendering rather than via `font.getbbox`: the latter reports a range
    wider than the advance box for this family, which would under-size the icons.
    The probe canvas is deliberately oversized -- at a precise probe size a full row
    is wider than a 432 px canvas and clipping would silently shrink the measurement.
    """
    img = Image.new("RGBA", (PROBE_CANVAS, PROBE_CANVAS), (0, 0, 0, 0))
    draw_text(ImageDraw.Draw(img), text, (font_path, REF),
              PROBE_CANVAS / 2, PROBE_CANVAS / 2, (255, 255, 255, 255))
    arr = np.array(img)
    xs = np.where(((arr[:, :, 0] > 20) & (arr[:, :, 3] > 0)).any(axis=0))[0]
    left, right = int(xs.min()), int(xs.max())
    # draw_text uses anchor "mm", i.e. the ADVANCE centre sits on the canvas centre
    return (right - left) / REF, ((left + right) / 2 - PROBE_CANVAS / 2) / REF


_PROBE_CACHE = {}


def probe_cached(font_path, text):
    """probe_ink with memoisation: 96 variants share only 48 fonts x 2 probe strings."""
    key = (font_path, text)
    if key not in _PROBE_CACHE:
        _PROBE_CACHE[key] = probe_ink(font_path, text)
    return _PROBE_CACHE[key]


def render(font_path, ghost, bg, fg, dim, ghost_on=True):
    """Return the 432 px foreground (transparent plate) for one variant.

    `ghost_on` decides whether the grey all-lit layer is drawn. The font size is always
    measured from the ghost row, so both states share identical geometry -- only the
    grey underlayer differs.
    """
    ghost_pair = ghost * 2
    ghost_long = ":".join([ghost_pair] * 3)

    # "one colon ink width" comes from THIS font, not from DSEG7 Classic:
    # the 14-segment families have noticeably different colon metrics.
    row_ink, row_offset = probe_cached(font_path, ghost_long)
    colon_ink, _ = probe_cached(font_path, ":")
    px = int(round(SAFE / (row_ink + 2 * colon_ink)))

    # centre the icon by the ghost row's ink, not by its advance box
    dx = -row_offset * px

    line_box = px * 1.2
    # 排布经 48 字重实测选出：上下块 21 / 47 均为合法时间值（<=59），
    # 重量差 0.0015、边缘留白 0.485；`1` 置于上块右侧，其 0.765em 左留白落在块内
    rows = [(ghost_pair, "21"), (ghost_long, "09:36:58"), (ghost_pair, "47")]

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if ghost_on:
        for i, (g, _) in enumerate(rows):
            draw_text(d, g, (font_path, px), S / 2 + dx, S / 2 + (i - 1) * line_box, dim)
    for i, (_, w) in enumerate(rows):
        draw_text(d, w, (font_path, px), S / 2 + dx, S / 2 + (i - 1) * line_box, fg)
    return img, px


def main(limit=None):
    os.makedirs(os.path.dirname(OUT_INDEX), exist_ok=True)

    # Drop any previously generated variant artwork, so switching format or density
    # list never leaves stale files behind (they would still be packaged).
    for old in glob.glob(os.path.join(RES_DIR, "mipmap-*", "ic_v*_fg.*")):
        os.remove(old)
    for old in glob.glob(os.path.join(RES_DIR, "mipmap-anydpi-v26", "ic_v*.xml")):
        os.remove(old)

    colors_xml = ['<?xml version="1.0" encoding="utf-8"?>', "<resources>"]
    index = []
    n = 0
    PHASES = (True, False)   # 灰底开 / 关，作为独立图标维度
    total = len(FAMILIES) * len(STYLES) * len(SCHEMES) * len(PHASES)
    for fam_key, fam_res, ghost in FAMILIES:
        for style in STYLES:
            font_path = os.path.join(FONT_DIR, f"{fam_res}_{style}.ttf")
            if not os.path.exists(font_path):
                raise SystemExit(f"missing font: {font_path}")
            for sch_key, bg, fg, dim in SCHEMES:
              for ghost_on in PHASES:
                if limit is not None and n >= limit:
                    return index, colors_xml
                fg_img, px = render(font_path, ghost, bg, fg, dim, ghost_on)
                for density, size in DENSITIES:
                    d_dir = os.path.join(RES_DIR, "mipmap-" + density)
                    os.makedirs(d_dir, exist_ok=True)
                    fg_img.resize((size, size), Image.LANCZOS).save(
                        os.path.join(d_dir, f"ic_v{n}_fg{EXT}"), FORMAT, **SAVE_KWARGS)
                xml_dir = os.path.join(RES_DIR, "mipmap-anydpi-v26")
                os.makedirs(xml_dir, exist_ok=True)
                with open(os.path.join(xml_dir, f"ic_v{n}.xml"), "w", encoding="utf-8") as f:
                    f.write(
                        '<?xml version="1.0" encoding="utf-8"?>\n'
                        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
                        f'    <background android:drawable="@color/ic_v{n}_bg" />\n'
                        f'    <foreground android:drawable="@mipmap/ic_v{n}_fg" />\n'
                        "</adaptive-icon>\n"
                    )
                r, g, b, _ = bg
                colors_xml.append(
                    f'    <color name="ic_v{n}_bg">#{r:02X}{g:02X}{b:02X}</color>'
                )
                index.append(
                    f"{n}\t{fam_key}\t{style}\t{sch_key}\t{px}\t{ghost}\t"
                    f"{'ghost_on' if ghost_on else 'ghost_off'}"
                )
                n += 1
    colors_xml.append("</resources>")
    return index, colors_xml


if __name__ == "__main__":
    import sys
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    idx, colors = main(lim)
    if lim is None:
        # Only persist the index / colours on a full run -- a probe run must not
        # overwrite them with a partial list.
        with open(OUT_INDEX, "w", encoding="utf-8") as f:
            f.write("\n".join(idx) + "\n")
        with open(os.path.join(RES_DIR, "values", "ic_variants.xml"), "w", encoding="utf-8") as f:
            f.write("\n".join(colors) + "\n")
    print(f"generated {len(idx)} variants" + (f" (limited to {lim})" if lim else ""))
    for line in idx[:4]:
        print("  " + line)
    print(f"  colour entries: {len(colors) - 2}")
    print(f"  index written  : {OUT_INDEX if lim is None else '(skipped: limited run)'}")
    print(f"  colours written: {os.path.join(RES_DIR, 'values', 'ic_variants.xml') if lim is None else '(skipped)'}")
