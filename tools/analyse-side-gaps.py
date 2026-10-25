"""Analyse side gaps, then re-search the layout for the *no-ghost* case.

The ghost layer fills the whole em box, so with it on, a narrow digit still looks like it
occupies its full advance. With the ghost off, only the lit segments show, and any large
side gap becomes visible empty space.

`1` is the extreme case: its ink sits at x[624,717] inside an 816 advance, i.e. 0.624em of
empty space on its LEFT. Placed at the start of the clock line, the whole line appears
indented when the ghost is hidden.

So the layout must also keep wide-gap digits away from the edges. This script measures the
gaps and searches for a layout that is good on BOTH metrics: weight balance and edge gaps.
"""
import io
import json

SRC = r"D:\DSHin\HoMiSe\docs\digit-weights.json"
TTF = r"D:\DSHin\HoMiSe\app\src\main\res\font\dseg_14_classic_regular.ttf"

from fontTools.ttLib import TTFont


def side_gaps(ttf_path):
    f = TTFont(ttf_path, lazy=False)
    glyf, cmap, hmtx = f["glyf"], f.getBestCmap(), f["hmtx"]
    out = {}
    for d in "0123456789":
        gn = cmap[ord(d)]
        g = glyf[gn]
        g.recalcBounds(glyf)
        adv = hmtx[gn][0]
        out[d] = (g.xMin / adv, (adv - g.xMax) / adv)   # (left, right) as fraction of advance
    return out


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
    gaps = side_gaps(TTF)
    print("=== 每个数字的左右留白（占 advance 比例）===")
    print("  digit   left    right   说明")
    for d in "0123456789":
        l, r = gaps[d]
        note = ""
        if l > 0.4: note = "← 左留白极大"
        if r > 0.4: note = "← 右留白极大"
        print("    {0}   {1:.3f}   {2:.3f}   {3}".format(d, l, r, note))

    with io.open(SRC, encoding="utf-8") as f:
        rows = json.load(f)
    avg = {str(d): sum(r[str(d)] for r in rows.values()) / len(rows) for d in range(10)}

    times = legal_times()

    def edge_gap(hh, ss, top, bot):
        """外侧留白：时钟行左端(1)+右端(1)+上下块各自外侧。"""
        # 时钟行：HH左端首位、SS右端末位
        g = gaps[hh[0]][0] + gaps[ss[1]][1]
        # 上下块是两个单字块，各自外侧也有留白
        g += min(gaps[top[0]][0], gaps[top[1]][0]) * 0.5
        g += min(gaps[bot[0]][1], gaps[bot[1]][1]) * 0.5
        return g

    best = None
    for hh, mm, ss, ds in times:
        rest = [str(x) for x in range(10) if str(x) not in ds]
        a, b, c, d4 = rest
        for top, bot in (((a, b), (c, d4)), ((a, c), (b, d4)), ((a, d4), (b, c))):
            wbal = abs((avg[top[0]] + avg[top[1]]) - (avg[bot[0]] + avg[bot[1]]))
            sym = abs((avg[hh[0]] + avg[hh[1]]) - (avg[ss[0]] + avg[ss[1]]))
            eg = edge_gap(hh, ss, top, bot)
            # 综合评分：重量平衡为主，边缘留白为约束
            score = (round(wbal, 4), round(eg, 4), round(sym, 4))
            if best is None or score < best[0]:
                best = (score, hh, mm, ss, top, bot)

    score, hh, mm, ss, top, bot = best
    print("\n=== 同时考虑左右留白后的最优排布 ===")
    print("     {0}{1}".format(*top))
    print("     {0}:{1}:{2}".format(hh, mm, ss))
    print("     {0}{1}".format(*bot))
    print("  上下块重量差: {0:.4f}".format(score[0]))
    print("  边缘留白合计: {0:.3f}".format(score[1]))
    print("  |HH-SS|:      {0:.4f}".format(score[2]))

    # 对比：原推荐方案在“边缘留白”上的表现
    print("\n=== 对比 ===")
    for label, hh2, mm2, ss2, top2, bot2 in [
        ("旧封面", "16", "25", "38", ("0", "9"), ("4", "7")),
        ("重量最优 58/13:02:47/69", "13", "02", "47", ("5", "8"), ("6", "9")),
        ("本方案", hh, mm, ss, top, bot),
    ]:
        eg = edge_gap(hh2, ss2, top2, bot2)
        wb = abs((avg[top2[0]] + avg[top2[1]]) - (avg[bot2[0]] + avg[bot2[1]]))
        print("  {0:26s} 重量差={1:.4f}  边缘留白={2:.3f}  时钟行={3}:{4}:{5}".format(
            label, wb, eg, hh2, mm2, ss2))


if __name__ == "__main__":
    main()
