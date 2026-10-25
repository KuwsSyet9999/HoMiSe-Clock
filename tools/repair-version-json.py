"""Repair version.json after a long -Summary argument truncated an entry.

The 0.3.2.2 summary was cut mid-string at `x[99,717,`, then the 0.3.2.3 object was
spliced in, then the remainder of 0.3.2.2 appeared after it — leaving invalid JSON.
This replaces exactly that damaged block with three well-formed entries and keeps
every other byte of the file untouched.
"""
import io
import json
import os

P = r"D:\DSHin\HoMiSe\version.json"

# 1-based 419..434 is the damaged block (see inspection).
START = 418          # 0-based start line
END = 434            # 0-based exclusive end line

BLOCK = [
    "    ,\n",
    "    {\n",
    '      "internalVersion": "0.3.2.1",\n',
    '      "date": "2026-10-20",\n',
    '      "summary": "字体替换测试版（HSSeg7 v2）：把 HSSeg7 的 ttc 解包覆盖 res/font 下 24 个七段字体资源，'
    '命名与代码引用不变；已验证每个字重的 colon 为 2 轮廓、period 为 1 轮廓、zero advance 816，'
    '度量与 DSEG7 一致；原字体备份于 tools/font_backup_dseg7"\n',
    "    },\n",
    "    {\n",
    '      "internalVersion": "0.3.2.2",\n',
    '      "date": "2026-10-23",\n',
    '      "summary": "十四段换字体测试版（第一版，已判定不可用）：HSSeg16 ttc 覆盖 dseg_14_ 全部 24 个资源；'
    '发现 ~ 只有 4 轮廓（非十六段全亮）、冒号右移超出 advance，故未作为交付版本"\n',
    "    },\n",
    "    {\n",
    '      "internalVersion": "0.3.2.3",\n',
    '      "date": "2026-10-23",\n',
    '      "summary": "十四段换字体测试版 v3：HSSeg16（20261023041504）覆盖 dseg_14_ 全部 24 个资源；'
    '已验收冒号为 22 点圆角、顶/底横段连续无缺口、中横拉齐共边、~ 为 16 轮廓满格、字重 300/400/700 正确；'
    '原 DSEG14 备份于 tools/font_backup_dseg14"\n',
    "    }\n",
    "  ],\n",
]


def main():
    lines = io.open(P, encoding="utf-8").readlines()
    before = len(lines)
    out = lines[:START] + BLOCK + lines[END:]
    io.open(P, "w", encoding="utf-8", newline="").writelines(out)
    print("行数: {0} -> {1}".format(before, len(out)))

    # 解析校验
    data = json.load(io.open(P, encoding="utf-8"))
    print("JSON 解析: OK")
    print("  history 条目: {0}".format(len(data["history"])))
    print("  releases 条目: {0}".format(len(data["releases"])))
    print("  current: {0}.{1}.{2}.{3}".format(
        data["current"]["major"], data["current"]["minor"],
        data["current"]["patch"], data["current"]["iteration"]))
    tail = [h["internalVersion"] for h in data["history"][-4:]]
    print("  最后 4 条: {0}".format(", ".join(tail)))


if __name__ == "__main__":
    main()
