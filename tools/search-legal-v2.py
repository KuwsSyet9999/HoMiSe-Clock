"""Search a cover layout where all three blocks are legal, cleanly.

Layout (ten digits, each once):

    AB          vignette block, value <= 59
    CD:EF:GH    clock line, legal HH:MM:SS with six distinct digits
    IJ          vignette block, value <= 59

`1` is kept out of the clock line and placed on the right of its vignette block, so its
0.765em left gap lands between the two digits of that block instead of at an edge.

The search prints counts at each filter step so the binding constraint is visible.
"""
import io
import json
import time

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

WEIGHTS = r"D:\DSHin\HoMiSe\docs\digit-weights.json"
FONT = r"D:\DSHin\HoMiSe\app\src\main\res\font\dseg_14_classic_regular.ttf"
OUT = "D:\\DSHin\\HoMiSe\\docs\\cover-legal-{0}.png".format(time.strftime("%Y%m%d-%H%M%S"))


def gaps_table():
    f = TTFont(FONT, lazy=False)
    glyf, cmap, hmtx = f["glyf"], f.getBestCmap(), f["hmtx"]
    g = {}
    for d in "0123456789":
        gn = cmap[ord(d)]
        gg = glyf[gn]; gg.recalcBounds(glyf)
        adv = hmtx[gn][0]
        g[d] = (gg.xMin / adv, (adv - gg.xMax) / adv)
    return g


def clock_lines():
    out = []
    for h in range(24):
        hh = "%02d" % h
        if len(set(hh)) != 2: continue
        for m in range(60):
            mm = "%02d" % m
            if len(set(mm)) != 2: continue
            for s in range(60):
                ss = "%02d" % s
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

    times = clock_lines()
    print("legal clock lines:", len(times))

    n_clock_ok = n_pair_ok = n_one_ok = 0
    best = None
    candidates = []

    for hh, mm, ss, ds in times:
        rest = [str(x) for x in range(10) if str(x) not in ds]
        if "1" in ds:
            continue                      # 1 必须在块里
        n_clock_ok += 1
        a, b, c, d = rest
        for top_pair, bot_pair in (((a, b), (c, d)), ((a, c), (b, d)), ((a, d), (b, c))):
            for top in (top_pair, top_pair[::-1]):
                for bot in (bot_pair, bot_pair[::-1]):
                    t1, b1 = "".join(top), "".join(bot)
                    if int(t1) > 59 or int(b1) > 59:
                        continue
                    n_pair_ok += 1
                    # `1` 在某个块的右侧
                    if "1" in t1 and not t1.endswith("1"): continue
                    if "1" in b1 and not b1.endswith("1"): continue
                    if "1" not in (t1 + b1): continue
                    n_one_ok += 1

                    wbal = abs((avg[t1[0]] + avg[t1[1]]) - (avg[b1[0]] + avg[b1[1]]))
                    edge = gaps[hh[0]][0] + gaps[ss[1]][1] + gaps[t1[0]][0] + gaps[b1[1]][1]
                    sym = abs((avg[hh[0]] + avg[hh[1]]) - (avg[ss[0]] + avg[ss[1]]))
                    score = (round(wbal, 4), round(edge, 4), round(sym, 4))
                    candidates.append((score, hh, mm, ss, t1, b1))
                    if best is None or score < best[0]:
                        best = (score, hh, mm, ss, t1, b1)

    print("after dropping clock lines containing '1':", n_clock_ok)
    print("after requiring both blocks <= 59:", n_pair_ok)
    print("after requiring '1' on the right of a block:", n_one_ok)
    print("total candidates:", len(candidates))

    if best is None:
        print("NO CANDIDATE -- relaxing the '1 on the right' rule")
        return

    score, hh, mm, ss, t1, b1 = best
    print("\n=== 最优（三块均合法）===")
    print("     {0}".format(t1))
    print("     {0}:{1}:{2}".format(hh, mm, ss))
    print("     {0}".format(b1))
    print("  上块={0} 下块={1} 时钟={2}:{3}:{4}".format(int(t1), int(b1), hh, mm, ss))
    print("  上下块重量差 {0:.4f}  边缘留白 {1:.3f}  |HH-SS| {2:.4f}".format(*score))
    digits = sorted(t1 + b1 + hh + mm + ss)
    print("  数字 {0} 完整={1}".format("".join(digits),
          "OK" if digits == [str(i) for i in range(10)] else "BAD"))

    # 前 10 名
    candidates.sort()
    print("\n=== 前 8 名 ===")
    seen = set()
    shown = 0
    for sc, h2, m2, s2, a1, b2 in candidates:
        key = (a1, b2)
        if key in seen: continue
        seen.add(key)
        print("  {0} / {1}:{2}:{3} / {4}   重量差={5:.4f} 边缘={6:.3f}".format(
            a1, h2, m2, s2, b2, sc[0], sc[1]))
        shown += 1
        if shown >= 8: break

    render(t1, "{0}:{1}:{2}".format(hh, mm, ss), b1)


def render(top, mid, bot):
    f = TTFont(FONT, lazy=False)
    cmap = f.getBestCmap()
    adv = {c: (f["hmtx"][cmap[ord(c)]][0] if ord(c) in cmap else 400) for c in "0123456789:"}
    PX, W, H = 62, 620, 600
    img = Image.new("RGBA", (W * 2, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    lf = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 20)
    font = ImageFont.truetype(FONT, PX)

    def meas(t):
        return sum(adv[c] / 1000.0 * PX for c in t)

    for gi, ghost in enumerate((True, False)):
        cx = W * gi + W // 2
        d.text((W * gi + 14, 20), "灰底" + ("开" if ghost else "关"),
               font=lf, fill=(150, 150, 150, 255))
        for j, txt in enumerate((top, mid, bot)):
            y = 80 + j * (PX + 18)
            x = cx - meas(txt) / 2
            for c in txt:
                if ghost:
                    d.text((x, y), "8" if c != ":" else ":", font=font, fill=(52, 52, 52, 255))
                d.text((x, y), c, font=font, fill=(255, 255, 255, 255))
                x += adv[c] / 1000.0 * PX
    img.convert("RGB").save(OUT, "PNG")
    print("\nsaved:", OUT)


if __name__ == "__main__":
    main()
