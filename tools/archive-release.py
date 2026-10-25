"""Finish archiving formal releases.

The export script only *reminds* about documentation, so two things remain:
  1. version.json's `releases[]` entries lack fileName / sha256;
  2. VERSIONING.md's release table has no row for the newest release.

Idempotent: existing values are preserved, and a table row is only added when that
version is not already mentioned.
"""
import glob
import io
import json
import os
import re

ROOT = r"D:\DSHin\HoMiSe"
RELEASE_DIR = os.path.join(ROOT, "release")
MD = os.path.join(ROOT, "VERSIONING.md")
VJ = os.path.join(ROOT, "version.json")
TICK = "`"

SUMMARIES = {
    "0.3.0": (
        "新增字体系统（8 族 × 6 样式 = 48 组合，四向滑屏切换并记忆）、"
        "图标随选择自动切换（96 变体；切换延后到退至后台执行，避免结束当前任务）、"
        "横屏过渡提示（ISO 时间 + 字体全名 + 版本号，淡入停留淡出、单击重播与延长、"
        "字体名交叉淡化）；图标资源改用无损 WebP 并只保留两档密度（4.23MB → 0.98MB）。"
    ),
}


def change_type(bump):
    """把 version.json 里的 bump 映射为发布表的中文变化类型。"""
    return {
        "major": "主版本（核心功能巨大变动）",
        "minor": "子版本（加入新模块、新功能）",
        "patch": "末版本（修补缺陷、小幅增强）",
    }.get(bump or "", "子版本（加入新模块、新功能）")


def sha_of(apk_name):
    path = os.path.join(RELEASE_DIR, apk_name + ".sha256")
    if not os.path.exists(path):
        return ""
    return io.open(path, encoding="utf-8").read().strip().split()[0]


def main():
    vj = json.load(io.open(VJ, encoding="utf-8"))

    # 1) 补齐 releases 的文件名与校验值
    for r in vj["releases"]:
        if r.get("fileName"):
            continue
        cands = sorted(glob.glob(os.path.join(
            RELEASE_DIR, "HoMiSe_" + r["version"] + "_*.APK")))
        if cands:
            name = os.path.basename(cands[-1])
            r["fileName"] = name
            r["sha256"] = sha_of(name)
            print("补全 release {0}: {1}".format(r["version"], name))

    with io.open(VJ, "w", encoding="utf-8") as f:
        json.dump(vj, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # 2) 发布表补行（同版本重新导出时替换旧行）
    md = io.open(MD, encoding="utf-8").read()
    added = 0
    for r in vj["releases"]:
        ver = r["version"]
        summary = SUMMARIES.get(ver, r.get("summary", "")).rstrip()
        # 摘要与「导出文件」之间补一个句号，避免两句话粘在一起
        if summary and summary[-1] not in "。；":
            summary += "。"
        row = ("| " + TICK + ver + TICK + " | " + r.get("date", "") +
               " | " + change_type(r.get("bump")) + " | " + summary +
               "导出文件 " + TICK + (r.get("fileName") or "") + TICK +
               "（versionCode " + str(r.get("versionCode", "")) +
               "，SHA-256 前 16 位 " + TICK + (r.get("sha256") or "")[:16] + TICK + "） |")
        pattern = re.compile(r"^\| " + re.escape(TICK + ver + TICK) + r" \|.*$", re.M)
        found = pattern.search(md)
        if found is not None:
            if found.group(0) == row:
                print("发布表已有 {0}，跳过".format(ver))
                continue
            md = md[:found.start()] + row + md[found.end():]
            added += 1
            print("发布表更新 {0}".format(ver))
            continue
        if not md.endswith("\n"):
            md += "\n"
        md += row + "\n"
        added += 1
        print("发布表追加 {0}".format(ver))

    if added:
        with io.open(MD, "w", encoding="utf-8") as f:
            f.write(md)
    print("新增发布表行: {0}".format(added))


if __name__ == "__main__":
    main()
