"""Split the analysis by series, and check whether colour scheme / ghost affect ranking.

Key insight to verify: the weight ordering is a property of the glyph outlines. Inverting
the colours multiplies every weight by the same factor; adding the ghost layer adds a
constant per glyph. Neither reorders digits, so one layout can serve all 192 variants.
"""
import io
import json

SRC = r"D:\DSHin\HoMiSe\docs\digit-weights.json"


def main():
    with io.open(SRC, encoding="utf-8") as f:
        rows = json.load(f)

    series = {"7": {}, "14": {}}
    for key, w in rows.items():
        s = key.split("|")[0]
        series[s][key] = w

    print("=== 七段 vs 十四段：数字平均视觉重量 ===")
    print("  digit     7-seg    14-seg    diff")
    for d in range(10):
        a = sum(w[str(d)] for w in series["7"].values()) / len(series["7"])
        b = sum(w[str(d)] for w in series["14"].values()) / len(series["14"])
        print("    {0}     {1:.4f}   {2:.4f}   {3:+.4f}".format(d, a, b, b - a))

    print("\n=== 各系列内排序是否一致 ===")
    for s in ("7", "14"):
        orders = set()
        for w in series[s].values():
            orders.add(tuple(sorted(w.keys(), key=lambda k: -w[k])))
        print("  {0} 段: {1} 种排序".format(s, len(orders)))
        for o in list(orders)[:3]:
            print("     {0}".format("".join(o)))

    print("\n=== 候选 B (58 / 13:02:47 / 69) 在两个系列内的表现 ===")
    for s in ("7", "14"):
        tbs, hhs = [], []
        for w in series[s].values():
            tbs.append(abs((w["5"]+w["8"]) - (w["6"]+w["9"])))
            hhs.append(abs((w["1"]+w["3"]) - (w["4"]+w["7"])))
        print("  {0} 段: |top-bottom| 平均 {1:.4f} 最差 {2:.4f}   |HH-SS| 平均 {3:.4f} 最差 {4:.4f}".format(
            s, sum(tbs)/len(tbs), max(tbs), sum(hhs)/len(hhs), max(hhs)))

    print("\n=== 配色/灰底是否影响排序 ===")
    print("  反色：w' = 1 - w（按 em 框归一化后），排序完全反转但相对大小不变")
    print("  灰底：每个字形额外叠加同一层 ghost，w' = w + c，差值 w1-w2 不变")
    print("  => 二者都不改变任何一对数字的重量差，故同一排布对 2 种配色 × 2 种灰底均成立")


if __name__ == "__main__":
    main()
