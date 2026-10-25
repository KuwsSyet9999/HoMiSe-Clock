"""Render the four cases: old/new layout x ghost on/off.

Output filename carries a UTC timestamp so a stale file can never masquerade as the new one.
"""
import os
import time

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

FONT = r"D:\DSHin\HoMiSe\app\src\main\res\font\dseg_14_classic_regular.ttf"
STAMP = time.strftime("%Y%m%d-%H%M%S")
OUT = r"D:\DSHin\HoMiSe\docs\cover-layout-{0}.png".format(STAMP)

PX = 46
CELL = 620
GHOST = (52, 52, 52, 255)
WHITE = (255, 255, 255, 255)
LABEL = (140, 140, 140, 255)
RED = (200, 90, 90, 255)
GREEN = (90, 200, 120, 255)
BG = (0, 0, 0, 255)


def main():
    f = TTFont(FONT, lazy=False)
    cmap = f.getBestCmap()
    adv = {c: (f["hmtx"][cmap[ord(c)]][0] if ord(c) in cmap else 400)
           for c in "0123456789:"}

    img = Image.new("RGBA", (CELL * 2, 760), BG)
    d = ImageDraw.Draw(img)
    lf = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 19)
    sf = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 16)
    font = ImageFont.truetype(FONT, PX)

    def measure(text):
        return sum(adv[ch] / 1000.0 * PX for ch in text)

    def draw_line(text, cx, y, ghost):
        x = cx - measure(text) / 2
        for ch in text:
            if ghost:
                d.text((x, y), "8" if ch != ":" else ":", font=font, fill=GHOST)
            d.text((x, y), ch, font=font, fill=WHITE)
            x += adv[ch] / 1000.0 * PX

    def panel(cx, cy, title, top, mid, bot, ghost, note, note_color):
        d.text((cx - CELL // 2 + 10, cy - 26), title, font=lf, fill=LABEL)
        base = cy + 30
        # 三行以同一中心线居中
        draw_line(top, cx, base, ghost)
        draw_line(mid, cx, base + PX + 16, ghost)
        draw_line(bot, cx, base + (PX + 16) * 2, ghost)
        # 边缘留白标注线
        w = measure(mid)
        d.line([(cx - w / 2, base + PX + 8), (cx + w / 2, base + PX + 8)],
               fill=(70, 70, 70, 255), width=1)
        d.text((cx - CELL // 2 + 10, base + (PX + 16) * 3 + 8), note, font=sf, fill=note_color)

    # 上排：有灰底；下排：无灰底
    panel(CELL // 2, 60, "旧 09 / 16:25:38 / 47  ·  灰底开", "09", "16:25:38", "47", True,
          "1 在最左：左端 0.765em 由灰底补足，看起来正常", GREEN)
    panel(CELL * 3 // 2, 60, "新 58 / 01:24:37 / 69  ·  灰底开", "58", "01:24:37", "69", True,
          "1 在中段：左端是 0（留白仅 0.121em）", GREEN)

    panel(CELL // 2, 420, "旧 09 / 16:25:38 / 47  ·  灰底关", "09", "16:25:38", "47", False,
          "左端缩进 0.765em —— 整行明显右移", RED)
    panel(CELL * 3 // 2, 420, "新 58 / 01:24:37 / 69  ·  灰底关", "58", "01:24:37", "69", False,
          "左端缩进 0.121em —— 与右端基本对称", GREEN)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.convert("RGB").save(OUT, "PNG")
    print("saved:", OUT)


if __name__ == "__main__":
    main()
