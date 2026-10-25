"""Append any internal-iteration entries missing from VERSIONING.md's table.

The changelog table in VERSIONING.md is the human-readable mirror of version.json's
`history` array; the two must stay in sync (per the project's versioning rules).
Entries are matched by their version string, so re-running is idempotent.
"""
import io
import json
import os

ROOT = r"D:\DSHin\HoMiSe"
TICK = "`"


def main():
    vj = json.load(io.open(os.path.join(ROOT, "version.json"), encoding="utf-8"))
    md_path = os.path.join(ROOT, "VERSIONING.md")
    md = io.open(md_path, encoding="utf-8").read()

    rows = []
    for h in vj["history"]:
        ver = h["internalVersion"]
        # Iteration x.y.z.0 produced that formal release and is already covered by the
        # release-table row, so only x.y.z.1+ needs its own changelog line.
        if ver.count(".") == 3 and not ver.endswith(".0"):
            summary = h["summary"].replace("|", "/")
            rows.append("| " + h["date"] + " | " + TICK + ver + TICK + " " + summary + " |")

    missing = [r for r in rows if r not in md]
    print("history 中 0.2.0.x 条目: {0}，其中未写入文档: {1}".format(len(rows), len(missing)))
    if missing:
        if not md.endswith("\n"):
            md += "\n"
        md += "\n".join(missing) + "\n"
        io.open(md_path, "w", encoding="utf-8").write(md)
        print("已追加 {0} 行".format(len(missing)))
    else:
        print("无需追加")
    print("VERSIONING.md 行数: {0}".format(
        len(io.open(md_path, encoding="utf-8").readlines())))


if __name__ == "__main__":
    main()
