"""Re-search with the vignette blocks required to be legal time values.

Earlier searches only constrained the clock line to a legal HH:MM:SS and let the two
vignette blocks take any remaining digits -- which produced 69 and 79, both illegal.
The blocks display minutes/seconds, so each must be <= 59.

Constraints now:
  * clock line : legal HH:MM:SS, six pairwise-distinct digits
  * top block  : two digits forming a value <= 59
  * bottom blk : two digits forming a value <= 59
  * all ten digits used exactly once
Objective (lexicographic):
  * |w(top) - w(bot)|          visual weight balance of the two vignettes
  * edge gap                   exposed whitespace at the outer edges when the ghost is off
  * |w(HH) - w(SS)|            symmetry of the clock line about its colons
"""
import io
import json
import time

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

WEIGHTS = r"D:\DSHin\HoMiSe\docs\digit-weights.json"
FONT = r"D:\DSHin\HoMiSe\app\src\main\res\font\dseg_14_classic_regular.ttf"


def gaps_table():
    f = TTFont(FONT, lazy=False)
    glyf, cmap, hmtx = f["glyf"], f.getBestCmap(), f["hmtx"]
    out = {}
    for d in "0123456789":
        gn = cmap[ord(d)]
        g = glyf[gn]; g.recalcBounds(glyf)
        adv = hmtx[gn][0]
        out[d] = (g.xMin / adv, (adv - g.xMax) / adv)
    return out


def pair_ok(s):
    """Two digits forming a legal minutes/seconds value."""
    return int(s) <= 59


def legal_times():
    out = []
    for h in range(24):
        hh = "{0:02d}".format(h)
        if len(set(hh)) != 2: continue
        for m in range(60):
            mm = "{0:02d}".format(m)
            if len(set(mm)) != 2: continue
            for s in range(60):
                ss = "{0:02d}".format(s)
                if len(set(ss)) != 2: continue
                ds = hh + mm + ss
                if len(set(ds)) == 6:
                    out.append((hh, mm, ss, ds))
    return out


def main():
    with io.open(WEIGHTS, encoding="utf-8") as f:
        rows = json.load(f)
    avg = {str(d): sum(r[str(d)] for r in rows.values()) / len(rows) for d in range(10)}
    gaps = gaps_table()

    best = None
    checked = 0

    def check(hh, mm, ss, t1, b1):
        nonlocal best, checked
        if not pair_ok(t1) or not pair_ok(b1):
            return
        if "1" in (hh + mm + ss):
            return
        if "1" in t1 and not t1.endswith("1"):
            return
        if "1" in b1 and not b1.endswith("1"):
            return
        checked += 1
        top, bot = t1, b1
        wbal = abs((avg[top[0]] + avg[top[1]]) - (avg[bot[0]] + avg[bot[1]]))
        edge = gaps[hh[0]][0] + gaps[ss[1]][1] + gaps[top[0]][0] + gaps[bot[1]][1]
        lone = 0.0
        for s in (hh, mm, ss):
            if "1" in s:
                lone += 0.765
        if "1" in (t1 + b1):
            lone += 0.30
        score = (round(wbal, 4), round(edge + lone, 4),
                 abs((avg[hh[0]] + avg[hh[1]]) - (avg[ss[0]] + avg[ss[1]])))
        if best is None or score < best[0]:
            best = (score, hh, mm, ss, t1, b1)
    for hh, mm, ss, ds in legal_times():
        rest = [str(x) for x in range(10) if str(x) not in ds]
        a, b, c, d4 = rest
        for top, bot in (((a, b), (c, d4)), ((a, c), (b, d4)), ((a, d4), (b, c))):
            t1, b1 = "".join(top), "".join(bot)
            if not pair_ok(t1) or not pair_ok(b1):
                continue
            # `1` 只允许出现在上下块里，且须位于块右侧（留白落在块内部）
            if "1" in (hh + mm + ss):
                continue
            if "1" in t1 and not t1.endswith("1"):
                continue
            if "1" in b1 and not b1.endswith("1"):
                continue
            checked += 1
            wbal = abs((avg[top[0]] + avg[top[1]]) - (avg[bot[0]] + avg[bot[1]]))
            edge = gaps[hh[0]][0] + gaps[ss[1]][1] + gaps[top[0]][0] + gaps[bot[1]][1]
            lone = 0.0
            for s in (hh, mm, ss):
                if "1" in s:
                    lone += 0.765
            if "1" in (t1 + b1):
                lone += 0.30      # 块内仍有空隙，但读作字距
            score = (round(wbal, 4), round(edge + lone, 4),
                     abs((avg[hh[0]] + avg[hh[1]]) - (avg[ss[0]] + avg[ss[1]])))
            if best is None or score < best[0]:
                best = (score, hh, mm, ss, t1, b1)

    print("合法候选（三块都合法）:", checked)
    score, hh, mm, ss, top, bot = best
    print("\n=== 最优且三块均合法的排布 ===")
    print("     {0}".format(top))
    print("     {0}:{1}:{2}".format(hh, mm, ss))
    print("     {0}".format(bot))
    print("  上下块重量差: {0:.4f}".format(score[0]))
    print("  边缘+1的空隙: {0:.3f}".format(score[1]))
    print("  |HH-SS|:      {0:.4f}".format(score[2]))
    print("  合法性: 上块 {0}={1} ok  下块 {2}={3} ok  时钟 {4}:{5}:{6} ok".format(
        top, int(top), bot, int(bot), hh, mm, ss))
    digits = sorted(top + bot + hh + mm + ss)
    print("  数字: {0}  完整: {1}".format("".join(digits),
          "OK" if digits == [str(i) for i in range(10)] else "BAD"))

    # 渲染
    stamp = time.strftime("%Y%m%d-%H%M%S")
    f = TTFont(FONT, lazy=False)
    cmap = f.getBestCmap()
    adv = {c: (f["hmtx"][cmap[ord(c)]][0] if ord(c) in cmap else 400) for c in "0123456789:"}
    PX, W, H = 62, 640, 600
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    lf = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 20)
    font = ImageFont.truetype(FONT, PX)

    def meas(t):
        return sum(adv[c] / 1000.0 * PX for c in t)

    rows_txt = [top, "{0}:{1}:{2}".format(hh, mm, ss), bot]
    for ghost in (True, False):
        ox = 0 if ghost else W // 2
        pass
    # 两栏：灰底开 / 灰底关
    img = Image.new("RGBA", (W * 2, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    for gi, ghost in enumerate((True, False)):
        cx = W * gi + W // 2
        d.text((W * gi + 14, 20), "灰底" + ("开" if ghost else "关"), font=lf, fill=(150, 150, 150, 255))
        for j, txt in enumerate(rows_txt):
            y = 80 + j * (PX + 18)
            x = cx - meas(txt) / 2
            for c in txt:
                if ghost:
                    d.text((x, y), "8" if c != ":" else ":", font=font, fill=(52, 52, 52, 255))
                d.text((x, y), c, font=font, fill=(255, 255, 255, 255))
                x += adv[c] / 1000.0 * PX
    out = r"D:\DSHin\HoMiSe\docs\cover-legal-{0}.png".format(stamp)
    img.convert("RGB").save(out, "PNG")
    print("\nsaved:", out)


if __name__ == "__main__":
    main()
