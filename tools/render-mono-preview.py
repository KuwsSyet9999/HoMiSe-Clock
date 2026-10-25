"""Render a comparison image showing what the Mono fix (advance 816 -> 408, x*0.5) yields.

Three rows, all drawn with the real HSEG16 TTF:

  1. TODAY  - Mono glyphs at advance 816 (what the app shows now)
  2. FIXED  - Mono glyphs at advance 408, glyph width halved, same font size
  3. FIXED+ - the practical outcome: because the string is half as wide, the app's
              fit-to-width sizing can roughly double the font size, so the same block
              occupies the same width with visibly larger glyphs

Every glyph is placed manually at its own advance so the picture reflects real metrics
rather than the renderer's spacing.
"""
import os

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

FONT_TTF = r"D:\DSHin\HoMiSe\app\src\main\res\font\dseg_14_classic_regular.ttf"
OUT = r"D:\DSHin\HoMiSe\docs\mono-effect-preview.png"

BG = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
FRAME = (68, 68, 68, 255)      # 灰色铺底（~ 的颜色）
LABEL = (150, 150, 150, 255)


def advances(ttf_path):
    f = TTFont(ttf_path, lazy=False)
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    def adv(ch):
        gn = cmap.get(ord(ch))
        return hmtx[gn][0] if gn else 400
    return adv


def draw_row(img, text, ttf, px, x0, y0, scale_x, layout_scale, fill, adv_fn):
    """Draw each char at its own advance; scale_x compresses the glyph horizontally."""
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(ttf, px)
    x = float(x0)
    for ch in text:
        tmp = Image.new("RGBA", (px * 2, px * 3), (0, 0, 0, 0))
        ImageDraw.Draw(tmp).text((0, 0), ch, font=font, fill=fill)
        if scale_x != 1.0:
            tmp = tmp.resize((max(1, int(tmp.width * scale_x)), tmp.height), Image.LANCZOS)
        img.paste(tmp, (int(round(x)), int(y0)), tmp)
        x += adv_fn(ch) / 1000.0 * px * layout_scale
    return x


def main():
    adv = advances(FONT_TTF)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)

    W, H = 1500, 720
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img)

    label_font = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 22)
    small = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 18)

    NAME = "DSEG14 Classic Mini Mono Light Italic"

    # 内容区（模拟信息块可用宽度）
    x0, content_w = 40, 1420

    rows = [
        ("① 当前：Mono advance 816（字形原宽）",
         24, 1.0, 1.0, WHITE),
        ("② 修复后：Mono advance 408、字形 x×0.5（字号不变）",
         24, 0.5, 0.5, WHITE),
        ("③ 修复后实际效果：宽度减半 → 字号可放大约 2 倍",
         48, 0.5, 0.5, WHITE),
    ]

    y = 70
    for label, px, sx, ls, fill in rows:
        d.text((x0, y - 34), label, font=label_font, fill=LABEL)

        # 灰色 ~ 铺底（模拟调试铺底）
        draw_row(img, NAME.replace(" ", "_"), FONT_TTF, px, x0, y, sx, ls, FRAME, adv)
        # 白色文字
        end_x = draw_row(img, NAME.replace(" ", "_"), FONT_TTF, px, x0, y, sx, ls, fill, adv)

        d.text((x0, y + px + 8), "宽度 ≈ {0:.0f} px".format(end_x - x0),
               font=small, fill=LABEL)
        y += px + 70

    # 参考线：内容区右边界
    d.line([(x0 + content_w, 40), (x0 + content_w, H - 40)], fill=(120, 40, 40, 255), width=2)
    d.text((x0 + content_w - 190, 20), "信息块右边界", font=small, fill=(180, 90, 90, 255))

    img.convert("RGB").save(OUT, "PNG")
    print("saved:", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
