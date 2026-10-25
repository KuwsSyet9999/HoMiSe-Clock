"""Render the recommended cover layout against the current one, with the ghost layer.

Left : current cover   09 / 16:25:38 / 47
Right: recommended     58 / 13:02:47 / 69

Both drawn with the same face (Classic Regular, 14-segment) and the same ghost layer the
app uses, so the weight difference between the two vignette blocks is directly visible.
"""
import os

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

FONT = r"D:\DSHin\HoMiSe\app\src\main\res\font\dseg_14_classic_regular.ttf"
OUT = r"D:\DSHin\HoMiSe\docs\cover-layout-compare.png"

PX = 54
GHOST = (58, 58, 58, 255)
WHITE = (255, 255, 255, 255)
LABEL = (150, 150, 150, 255)
BG = (0, 0, 0, 255)


def main():
    f = TTFont(FONT, lazy=False)
    cmap = f.getBestCmap()
    adv = {c: (f["hmtx"][cmap[ord(c)]][0] if ord(c) in cmap else 400) for c in "0123456789:"}

    img = Image.new("RGBA", (1240, 520), BG)
    d = ImageDraw.Draw(img)
    lf = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 20)
    font = ImageFont.truetype(FONT, PX)

    def measure(text):
        return sum(adv[ch] / 1000.0 * PX for ch in text)

    def line(text, x, y):
        # ghost layer first, then white digits on top — same as the app
        xx = x
        for ch in text:
            d.text((xx, y), "8" if ch != ":" else ":", font=font, fill=GHOST)
            d.text((xx, y), ch, font=font, fill=WHITE)
            xx += adv[ch] / 1000.0 * PX
        return xx - x

    def cover(title, top, mid, bot, ox, oy, box_w):
        # 每块以 box_w 为容器水平居中——与图标里的居中排布一致
        d.text((ox, oy - 30), title, font=lf, fill=LABEL)
        cx = ox + box_w / 2
        for i, txt in enumerate((top, mid, bot)):
            y = oy + i * (PX + 22)
            line(txt, cx - measure(txt) / 2, y)

    cover("当前：09 / 16:25:38 / 47", "09", "16:25:38", "47", 40, 70, 540)
    cover("推荐：58 / 13:02:47 / 69", "58", "13:02:47", "69", 640, 70, 540)

    # 标注上下块的视觉重量差
    d.text((40, 430), "上下块重量差 0.230（居中后仍明显不均）", font=lf, fill=(200, 90, 90, 255))
    d.text((640, 430), "上下块重量差 0.000（居中后完全均等）", font=lf, fill=(90, 200, 120, 255))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.convert("RGB").save(OUT, "PNG")
    print("saved:", OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
