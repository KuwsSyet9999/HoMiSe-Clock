"""Search the best digit layout for the cover, across the measured faces.

Layout that must be filled (10 digits, each used exactly once):

    AB            top block   (2 digits)
    CD:EF:GH      clock line  (6 digits, must be a legal HH:MM:SS)
    IJ            bottom block (2 digits)

Goals, in order:
  1. the clock line must be a legal time with 6 distinct digits
  2. |weight(top) - weight(bottom)| minimal, so the two vignette blocks balance
  3. |weight(HH) - weight(SS)| minimal, so the clock line is symmetric about the colons

Also verifies whether the per-face weight ordering is stable enough to justify one
shared layout for all 48 faces (and therefore all 192 icon variants).
"""
import io
import json
import os

SRC = r"D:\DSHin\HoMiSe\docs\digit-weights.json"


def load():
    with io.open(SRC, encoding="utf-8") as f:
        return json.load(f)


def legal_times():
    """All HH:MM:SS whose six digits are pairwise distinct."""
    out = []
    for h in range(24):
        hh = "{0:02d}".format(h)
        if len(set(hh)) != 2:
            continue
        for m in range(60):
            mm = "{0:02d}".format(m)
            if len(set(mm)) != 2:
                continue
            for s in range(60):
                ss = "{0:02d}".format(s)
                if len(set(ss)) != 2:
                    continue
                ds = hh + mm + ss
                if len(set(ds)) == 6:
                    out.append((hh, mm, ss, ds))
    return out


def balance_pairs(rest, w):
    """Split the 4 remaining digits into two pairs with the closest total weight."""
    a, b, c, d = rest
    pairs = [
        ((a, b), (c, d)),
        ((a, c), (b, d)),
        ((a, d), (b, c)),
    ]
    best = None
    for top, bot in pairs:
        diff = abs((w[top[0]] + w[top[1]]) - (w[bot[0]] + w[bot[1]]))
        if best is None or diff < best[0]:
            best = (diff, top, bot)
    return best


def solve(w, times):
    best = None
    for hh, mm, ss, ds in times:
        wc = w[hh[0]] + w[hh[1]] + w[mm[0]] + w[mm[1]] + w[ss[0]] + w[ss[1]]
        sym = abs((w[hh[0]] + w[hh[1]]) - (w[ss[0]] + w[ss[1]]))
        rest = [str(x) for x in range(10) if str(x) not in ds]
        bal = balance_pairs(rest, w)
        score = (bal[0], sym)
        # 低分优先：先平衡上下块，再平衡 HH 与 SS
        if best is None or score < best[0]:
            best = (score, hh, mm, ss, bal, wc)
    return best


def ordering_stable(rows):
    """Do all faces rank the digits the same way?"""
    rank_sets = set()
    for r in rows:
        order = tuple(sorted(r.keys(), key=lambda k: -r[k]))
        rank_sets.add(order)
    return len(rank_sets), rank_sets


def main():
    rows = load()
    times = legal_times()
    print("legal HH:MM:SS with 6 distinct digits:", len(times))

    n_order, orders = ordering_stable(list(rows.values()))
    print("distinct weight orderings across 48 faces:", n_order)

    avg = {str(d): sum(r[str(d)] for r in rows.values()) / len(rows) for d in range(10)}
    print("\n=== 按平均重量求最优排布 ===")
    score, hh, mm, ss, bal, wc = solve(avg, times)
    top, bot = bal[1], bal[2]
    print("  clock line : {0}:{1}:{2}".format(hh, mm, ss))
    print("  top block  : {0}{1}".format(*top))
    print("  bottom blk : {0}{1}".format(*bot))
    diff = score[0]
    print("  |top-bottom| = {0:.4f}   |HH-SS| = {1:.4f}".format(score[0], score[1]))

    print("\n  排布：")
    print("    {0}{1}".format(*top))
    print("    {0}:{1}:{2}".format(hh, mm, ss))
    print("    {0}{1}".format(*bot))
    digits = sorted(top + bot + tuple(hh + mm + ss))
    print("  数字集合: {0}  完整度: {1}".format("".join(digits), "OK" if digits == [str(i) for i in range(10)] else "BAD"))

    # 与旧方案对比
    print("\n=== 旧方案对比 ===")
    old = {"top": ("0", "9"), "clock": ("16", "25", "38"), "bot": ("4", "7")}
    ot = avg[old["top"][0]] + avg[old["top"][1]]
    ob = avg[old["bot"][0]] + avg[old["bot"][1]]
    ohh = avg["1"] + avg["6"]
    oss = avg["3"] + avg["8"]
    print("  旧: 09 / 16:25:38 / 47   |top-bottom|={0:.4f}  |HH-SS|={1:.4f}".format(abs(ot - ob), abs(ohh - oss)))

    # 各字重分别求解，看是否收敛
    print("\n=== 48 个字重分别求解的最优时钟行分布 ===")
    from collections import Counter
    cnt = Counter()
    layout_cnt = Counter()
    for key, w in rows.items():
        s, hh, mm, ss, bal, _ = solve(w, times)
        cnt["{0}:{1}:{2}".format(hh, mm, ss)] += 1
        layout_cnt["{0}{1} / {2}:{3}:{4} / {5}{6}".format(
            bal[1][0], bal[1][1], hh, mm, ss, bal[2][0], bal[2][1])] += 1
    for k, v in cnt.most_common(8):
        print("  {0:10s} 出现 {1} 次".format(k, v))
    print("\n  完整排布众数:")
    for k, v in layout_cnt.most_common(6):
        print("    {0:28s} {1} 次".format(k, v))


if __name__ == "__main__":
    main()
