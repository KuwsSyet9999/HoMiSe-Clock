"""Measure the visual weight of each digit in all 48 HSEG faces.

Weight = fraction of lit pixels inside the glyph's em box, rendered from the real TTF.
That captures stroke thickness and segment count together, which bbox area cannot.

Output: docs/digit-weights.json plus a readable table.
"""
import io
import json
import os

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = r"D:\DSHin\HoMiSe\app\src\main\res\font"
OUT = r"D:\DSHin\HoMiSe\docs\digit-weights.json"

FAMILIES = [
    ("Classic", "classic"),
    ("Classic Mini", "classic_mini"),
    ("Modern", "modern"),
    ("Modern Mini", "modern_mini"),
]
STYLES = [
    ("Light", "light"),
    ("Light Italic", "light_italic"),
    ("Regular", "regular"),
    ("Italic", "italic"),
    ("Bold", "bold"),
    ("Bold Italic", "bold_italic"),
]
SERIES = [("7", "hsseg_7"), ("14", "dseg_14")]

PX = 160          # render size; enough to resolve strokes
SAMPLES = 400     # supersample grid density when counting


def weight(font: ImageFont.FreeTypeFont, ch: str) -> float:
    img = Image.new("L", (PX * 2, PX * 2), 0)
    ImageDraw.Draw(img).text((PX // 2, PX // 2), ch, font=font, fill=255)
    box = img.getbbox()
    if not box:
        return 0.0
    # 以字形自身的 em 框为分母：高度按 PX，宽度按数字 advance 0.816em
    em_w = PX * 0.816
    em_h = PX
    px = sum(1 for v in img.getdata() if v > 127)
    return px / (em_w * em_h)


def main():
    rows = {}
    for series, prefix in SERIES:
        for fam_name, fam_key in FAMILIES:
            for style_name, style_key in STYLES:
                path = os.path.join(FONT_DIR, "{0}_{1}_{2}.ttf".format(prefix, fam_key, style_key))
                if not os.path.exists(path):
                    print("  ! missing", path)
                    continue
                font = ImageFont.truetype(path, PX)
                key = "{0}|{1}|{2}".format(series, fam_name, style_name)
                rows[key] = {str(d): round(weight(font, str(d)), 4) for d in range(10)}

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print("faces:", len(rows), "-> ", OUT)

    # 汇总：每个数字在 48 字重里的平均视觉重量
    avg = {}
    for d in range(10):
        vals = [r[str(d)] for r in rows.values()]
        avg[str(d)] = round(sum(vals) / len(vals), 4)
    print("\n=== 每个数字的平均视觉重量（48 字重平均）===")
    for d in sorted(avg, key=lambda k: -avg[k]):
        bar = "#" * int(avg[d] * 300)
        print("  {0}: {1:.4f}  {2}".format(d, avg[d], bar))

    sd = {}
    for d in range(10):
        vals = [r[str(d)] for r in rows.values()]
        m = sum(vals) / len(vals)
        var = sum((v - m) ** 2 for v in vals) / len(vals)
        sd[str(d)] = round(var ** 0.5, 4)
    print("\n=== 各数字在不同字重间的波动（标准差，越小越稳定）===")
    for d in sorted(sd, key=lambda k: -sd[k]):
        print("  {0}: sd={1:.4f}".format(d, sd[d]))


if __name__ == "__main__":
    main()
