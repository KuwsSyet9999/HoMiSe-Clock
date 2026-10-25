"""Re-archive the 0.3.0 release after re-signing it with the distribution key.

The APK was rebuilt with a different key, so its file name and SHA-256 changed.
Both version.json and VERSIONING.md still record the old (test-signed) values and
must be updated in place rather than appended.
"""
import glob
import io
import json
import os

ROOT = r"D:\DSHin\HoMiSe"
RELEASE_DIR = os.path.join(ROOT, "release")
VJ = os.path.join(ROOT, "version.json")
MD = os.path.join(ROOT, "VERSIONING.md")
TICK = "`"
VERSION = "0.3.0"


def main():
    cands = sorted(glob.glob(os.path.join(RELEASE_DIR, "HoMiSe_" + VERSION + "_*.APK")))
    if not cands:
        raise SystemExit("no APK found for " + VERSION)
    name = os.path.basename(cands[-1])
    sha = io.open(os.path.join(RELEASE_DIR, name + ".sha256"),
                  encoding="utf-8").read().strip().split()[0]
    print("APK : {0}".format(name))
    print("SHA : {0}".format(sha))

    # 1) version.json
    vj = json.load(io.open(VJ, encoding="utf-8"))
    for r in vj["releases"]:
        if r["version"] == VERSION:
            r["fileName"] = name
            r["sha256"] = sha
    with io.open(VJ, "w", encoding="utf-8") as f:
        json.dump(vj, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # 2) VERSIONING.md 的发布表行：就地替换，不追加
    lines = io.open(MD, encoding="utf-8").read().split("\n")
    replaced = 0
    for i, ln in enumerate(lines):
        if ln.startswith("| " + TICK + VERSION + TICK + " |"):
            # 摘要是该行的第 4 个字段，原样保留，只换文件名与校验值
            parts = ln.split(" | ")
            summary = parts[3]
            summary = summary.split("导出文件")[0].rstrip()
            lines[i] = ("| " + TICK + VERSION + TICK + " | 2026-10-17 | 子版本（加入新模块、新功能） | " +
                        summary + "导出文件 " + TICK + name + TICK +
                        "（versionCode 30001，SHA-256 前 16 位 " + TICK + sha[:16] + TICK +
                        "；使用发布密钥签名） |")
            replaced += 1
    if replaced:
        io.open(MD, "w", encoding="utf-8").write("\n".join(lines))
    print("发布表更新行数: {0}".format(replaced))


if __name__ == "__main__":
    main()
