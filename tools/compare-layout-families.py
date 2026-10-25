"""Compare two families of layouts and render the best of each.

Family A: `1` allowed inside the clock line (its gap shows up as loose tracking).
Family B: `1` forced into a vignette block, so its one-sided gap sits between two digits
          of the same block and is balanced by the block's own centring.

Metrics used:
  weight   = |w(top)-w(bot)|       lower is better
  edge     = left gap of clock's first digit + right gap of clock's last digit
  lone     = the gap `1` introduces against its neighbour (0 if `1` is in a block,
             since the block is centred and the gap is halved across the pair)
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


def legal_times(no1=False):
    out = []
    for h in range(24):
        hh = "{0:02d}".format(h)
        if len(set(hh)) != 2: continue
        if no1 and "1" in hh: continue
        for m in range(60):
            mm = "{0:02d}".format(m)
            if len(set(mm)) != 2: continue
            if no1 and "1" in mm: continue
            for s in range(60):
                ss = "{0:02d}".format(s)
                if len(set(ss)) != 2: continue
                if no1 and "1" in ss: continue
                ds = hh + mm + ss
                if len(set(ds)) == 6:
                    out.append((hh, mm, ss, ds))
    return out


def search(avg, gaps, times, force_one_in_block):
    best = None
    for hh, mm, ss, ds in times:
        rest = [str(x) for x in range(10) if str(x) not in ds]
        a, b, c, d4 = rest
        for top, bot in (((a, b), (c, d4)), ((a, c), (b, d4)), ((a, d4), (b, c))):
            if force_one_in_block and "1" not in (top + bot):
                continue
            wbal = abs((avg[top[0]] + avg[top[1]]) - (avg[bot[0]] + avg[bot[1]]))
            # 时钟行两端 + 上下块各自的外侧端（块的内侧留白读作字距，不算边缘）
            edge = gaps[hh[0]][0] + gaps[ss[1]][1] + gaps[top[0]][0] + gaps[bot[1]][1]
            # `1` 与邻位的额外空隙
            lone = 0.0
            for s in (hh, mm, ss):
                if "1" in s:
                    lone += 0.765
            if force_one_in_block:
                # 在块内：空隙被块内两字分担，且块居中，视觉只体现为字距
                lone *= 0.25
            sym = abs((avg[hh[0]] + avg[hh[1]]) - (avg[ss[0]] + avg[ss[1]]))
            score = (round(wbal, 4), round(edge + lone, 4), round(sym, 4))
            if best is None or score < best[0]:
                best = (score, hh, mm, ss, top, bot)
    return best


def render(picks, stamp):
    f = TTFont(FONT, lazy=False)
    cmap = f.getBestCmap()
    adv = {c: (f["hmtx"][cmap[ord(c)]][0] if ord(c) in cmap else 400) for c in "0123456789:"}
    PX, CELL = 60, 620
    img = Image.new("RGBA", (CELL * len(picks), 620), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    lf = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 19)
    sf = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 16)
    font = ImageFont.truetype(FONT, PX)

    def meas(t):
        return sum(adv[c] / 1000.0 * PX for c in t)

    for i, (label, top, mid, bot, note, color) in enumerate(picks):
        cx = CELL * i + CELL // 2
        d.text((CELL * i + 12, 24), label, font=lf, fill=(150, 150, 150, 255))
        for j, txt in enumerate((top, mid, bot)):
            y = 80 + j * (PX + 18)
            x = cx - meas(txt) / 2
            for c in txt:
                d.text((x, y), "8" if c != ":" else ":", font=font, fill=(52, 52, 52, 255))
                d.text((x, y), c, font=font, fill=(255, 255, 255, 255))
                x += adv[c] / 1000.0 * PX
        d.text((CELL * i + 12, 480), note, font=sf, fill=color)

    out = r"D:\DSHin\HoMiSe\docs\cover-final-{0}.png".format(stamp)
    img.convert("RGB").save(out, "PNG")
    return out


def main():
    with io.open(WEIGHTS, encoding="utf-8") as f:
        rows = json.load(f)
    avg = {str(d): sum(r[str(d)] for r in rows.values()) / len(rows) for d in range(10)}
    gaps = gaps_table()

    A = search(avg, gaps, legal_times(no1=False), force_one_in_block=False)
    B = search(avg, gaps, legal_times(no1=True), force_one_in_block=True)
    # 再搜一个“1 在块内且靠右”的变体：块内 1 放右侧，左侧留白落在两字之间
    def search_one_right(avg, gaps, times):
        best = None
        for hh, mm, ss, ds in times:
            rest = [str(x) for x in range(10) if str(x) not in ds]
            a, b, c, d4 = rest
            for top, bot in (((a, b), (c, d4)), ((a, c), (b, d4)), ((a, d4), (b, c))):
                if "1" not in (top + bot):
                    continue
                # 1 必须位于块的右侧，让它的左留白落在块内部
                t1 = "".join(top); b1 = "".join(bot)
                if "1" in t1 and not t1.endswith("1"): continue
                if "1" in b1 and not b1.endswith("1"): continue
                wbal = abs((avg[top[0]] + avg[top[1]]) - (avg[bot[0]] + avg[bot[1]]))
                edge = gaps[hh[0]][0] + gaps[ss[1]][1] + gaps[top[0]][0] + gaps[bot[1]][1]
                sym = abs((avg[hh[0]] + avg[hh[1]]) - (avg[ss[0]] + avg[ss[1]]))
                score = (round(wbal, 4), round(edge, 4), round(sym, 4))
                if best is None or score < best[0]:
                    best = (score, hh, mm, ss, top, bot)
        return best

    C = search_one_right(avg, gaps, legal_times(no1=True))

    for name, r in (("A 1可在时钟行", A), ("B 1进块(不限侧)", B), ("C 1进块且靠右", C)):
        s, hh, mm, ss, top, bot = r
        print("=== {0} ===".format(name))
        print("    {0}{1}".format(*top))
        print("    {0}:{1}:{2}".format(hh, mm, ss))
        print("    {0}{1}".format(*bot))
        print("  weight={0:.4f}  edge+lone={1:.3f}  sym={2:.4f}".format(*s))
        print()

    stamp = time.strftime("%Y%m%d-%H%M%S")
    picks = []
    s, hh, mm, ss, top, bot = A
    picks.append(("A 重量+边缘最优  {0}{1} / {2}:{3}:{4} / {5}{6}".format(*top, hh, mm, ss, *bot),
                  "".join(top), "{0}:{1}:{2}".format(hh, mm, ss), "".join(bot),
                  "1 在中段：行首不缩进，但与 0 之间空隙 0.886em", (200, 170, 90, 255)))
    s, hh, mm, ss, top, bot = C
    picks.append(("C 1 进块且靠右  {0}{1} / {2}:{3}:{4} / {5}{6}".format(*top, hh, mm, ss, *bot),
                  "".join(top), "{0}:{1}:{2}".format(hh, mm, ss), "".join(bot),
                  "1 在块内右侧：留白落在块中间，两侧边缘都紧", (90, 200, 120, 255)))

    out = render(picks, stamp)
    print("saved:", out)


if __name__ == "__main__":
    main()
