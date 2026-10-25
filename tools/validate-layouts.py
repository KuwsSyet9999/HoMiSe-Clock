"""Validate the candidate layouts across all 48 faces.

Candidates:
  A. avg-optimal :  58 / 01:24:37 / 69   (|top-bottom| = 0 on the average weights)
  B. mode        :  58 / 13:02:47 / 69   (most frequent per-face optimum)
  C. old         :  09 / 16:25:38 / 47   (current cover)

For each face we report |top-bottom| and |HH-SS|, then the worst / mean case, so we can
judge whether one shared layout is good enough for all 192 icon variants.
"""
import io
import json

SRC = r"D:\DSHin\HoMiSe\docs\digit-weights.json"

CANDIDATES = [
    ("A avg-optimal", "58", "01", "24", "37", "69"),
    ("B mode",        "58", "13", "02", "47", "69"),
    ("C old cover",   "09", "16", "25", "38", "47"),
]


def main():
    with io.open(SRC, encoding="utf-8") as f:
        rows = json.load(f)

    print("{0:14s} {1:>8s} {2:>8s} {3:>8s} {4:>8s}".format(
        "candidate", "tb_mean", "tb_worst", "hhss_mean", "hhss_worst"))
    for name, top, hh, mm, ss, bot in CANDIDATES:
        tbs, hhs = [], []
        for key, w in rows.items():
            t = w[top[0]] + w[top[1]]
            b = w[bot[0]] + w[bot[1]]
            h = w[hh[0]] + w[hh[1]]
            s = w[ss[0]] + w[ss[1]]
            tbs.append(abs(t - b))
            hhs.append(abs(h - s))
        print("{0:14s} {1:8.4f} {2:8.4f} {3:8.4f} {4:8.4f}".format(
            name, sum(tbs)/len(tbs), max(tbs), sum(hhs)/len(hhs), max(hhs)))

    # 每个字重的最优 vs 候选 A 的差距
    print("\n=== 候选 A 与各字重自身最优的差距（上下块平衡项）===")
    diffs = []
    for key, w in rows.items():
        best = None
        for a in range(10):
            for b in range(a+1, 10):
                for c in range(10):
                    if c in (a, b):
                        continue
                    for d in range(c+1, 10):
                        if d in (a, b):
                            continue
                        diff = abs((w[str(a)]+w[str(b)]) - (w[str(c)]+w[str(d)]))
                        if best is None or diff < best:
                            best = diff
        cand = abs((w["5"]+w["8"]) - (w["6"]+w["9"]))
        diffs.append(cand - best)
    print("  平均落后于理论最优: {0:.4f}".format(sum(diffs)/len(diffs)))
    print("  最差落后:           {0:.4f}".format(max(diffs)))
    better = sum(1 for d in diffs if d < 0.0005)
    print("  与最优几乎相同的字重数: {0}/48".format(better))

    # 逐字重看 A 的上下块是否仍平衡
    print("\n=== 各字重下 A 的上下块差值分布 ===")
    buckets = {"<=0.01": 0, "<=0.03": 0, "<=0.06": 0, ">0.06": 0}
    for key, w in rows.items():
        d = abs((w["5"]+w["8"]) - (w["6"]+w["9"]))
        if d <= 0.01: buckets["<=0.01"] += 1
        elif d <= 0.03: buckets["<=0.03"] += 1
        elif d <= 0.06: buckets["<=0.06"] += 1
        else: buckets[">0.06"] += 1
    for k, v in buckets.items():
        print("  {0:8s} {1:3d} 个字重".format(k, v))


if __name__ == "__main__":
    main()
