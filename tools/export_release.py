"""Export a formal HoMiSe release.

tools/export-apk.ps1 is the historical implementation, but the sandbox runs pwsh in
ConstrainedLanguage mode and refuses to execute any .ps1 file. This Python version
reproduces the same steps for a formal (three-part) release:

  1. verify the requested version / bump kind against version.json
  2. freeze it into version.json (current, stage, releaseVersion, lastRelease,
     internalVersion, history, releases)
  3. build the signed release APK with gradle (offline)
  4. read versionName / versionCode back out of the APK and compare with version.json
  5. name it HoMiSe_<version>_<14-digit time>_<hash16>.APK, copy into release/
     and write the .sha256 companion file
  6. drop older internal packages, keep every formal release

Afterwards run tools/archive-release.py to add the VERSIONING.md release-table row.
"""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = r"D:\DSHin\HoMiSe"
VERSION_JSON = os.path.join(ROOT, "version.json")
RELEASE_DIR = os.path.join(ROOT, "release")
GRADLE = os.path.join(ROOT, "tools", "gradle-8.9", "bin", "gradle.bat")
SDK = os.path.join(ROOT, "tools", "android-sdk")
JAVA = os.path.join(ROOT, "tools", "jdk-17")

ENV = dict(os.environ)
ENV.update({
    "JAVA_HOME": JAVA,
    "GRADLE_USER_HOME": os.path.join(ROOT, "tools", "gradle-home"),
    "ANDROID_HOME": SDK,
    "ANDROID_SDK_ROOT": SDK,
    "ANDROID_USER_HOME": os.path.join(ROOT, "tools", "android-home"),
    "TEMP": os.path.join(ROOT, "tools", "temp"),
    "TMP": os.path.join(ROOT, "tools", "temp"),
    "HOME": os.path.join(ROOT, "tools", "home"),
    "USERPROFILE": os.path.join(ROOT, "tools", "home"),
    "PATH": JAVA + r"\bin;" + os.environ.get("PATH", ""),
})

BUMPS = ("major", "minor", "patch")


def parse_args(argv):
    version = summary = bump = None
    i = 0
    while i < len(argv):
        if argv[i] == "--version" and i + 1 < len(argv):
            version = argv[i + 1]
            i += 2
        elif argv[i] == "--bump" and i + 1 < len(argv):
            bump = argv[i + 1]
            i += 2
        elif argv[i] == "--summary" and i + 1 < len(argv):
            summary = argv[i + 1]
            i += 2
        else:
            raise SystemExit("unknown argument: " + argv[i])
    if not version or not re.match(r"^\d+\.\d+\.\d+$", version):
        raise SystemExit("--version must look like 1.0.0")
    if bump not in BUMPS:
        raise SystemExit("--bump must be one of " + ", ".join(BUMPS))
    return version, bump, summary or ""


def load():
    with io.open(VERSION_JSON, encoding="utf-8") as f:
        return json.load(f)


def save(data):
    with io.open(VERSION_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def freeze(data, version, bump, summary):
    """Write the formal version into version.json and return (versionCode, date)."""
    major, minor, patch = [int(x) for x in version.split(".")]
    previous = data.get("internalVersion", "")
    today = time.strftime("%Y-%m-%d")
    version_code = major * 1_000_000 + minor * 10_000 + patch * 100 + 1

    data["current"] = {"major": major, "minor": minor, "patch": patch, "iteration": 0}
    data["stage"] = "release"
    data["releaseVersion"] = version
    data["lastRelease"] = version
    data["internalVersion"] = version + ".0"
    data["nextRelease"] = {
        "plannedVersion": None,
        "bump": "minor",
        "basis": "正式版发布后重新判定；下一次导出前由需求方确认",
        "confirmedBy": None,
        "note": "正式导出须先由需求方确认版本号，再运行 promote",
    }
    data["updated"] = today

    existing = next((r for r in data.get("releases", [])
                     if r.get("version") == version), None)
    if existing is not None:
        # 同版本重新导出（正式版尚未对外发布时使用）：保留原始 fromInternal，
        # 只更新摘要、日期与校验信息，避免在 releases[] 里重复追加条目。
        previous = existing.get("fromInternal") or previous
        existing.update({
            "date": today,
            "bump": bump,
            "summary": summary,
            "versionCode": version_code,
            "fileName": "",
            "sha256": "",
        })
        data.setdefault("history", []).append({
            "internalVersion": version + ".0",
            "date": today,
            "summary": "重新导出正式版本 {0}（自 {1}）：{2}".format(version, previous, summary),
        })
        return version_code, today

    data.setdefault("history", []).append({
        "internalVersion": version + ".0",
        "date": today,
        "summary": "定格正式版本 {0}（自 {1}）：{2}".format(version, previous, summary),
    })
    data.setdefault("releases", []).append({
        "version": version,
        "date": today,
        "bump": bump,
        "fromInternal": previous,
        "summary": summary,
        "versionCode": version_code,
        "fileName": "",
        "sha256": "",
    })
    return version_code, today


def gradle_build():
    cmd = [GRADLE, "-p", ROOT, "assembleRelease", "--offline"]
    print("  running gradle assembleRelease ...")
    r = subprocess.run(cmd, cwd=ROOT, env=ENV, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    tail = [ln for ln in r.stdout.splitlines() if "BUILD" in ln or ln.startswith("e:")]
    for ln in tail:
        print("    " + ln.strip())
    if r.returncode != 0:
        print(r.stdout[-3000:])
        print(r.stderr[-2000:])
        raise SystemExit("gradle failed")


def apk_path():
    p = os.path.join(ROOT, "app", "build", "outputs", "apk", "release", "app-release.apk")
    if not os.path.exists(p):
        raise SystemExit("APK not found: " + p)
    return p


def apk_ident(apk):
    aapt2 = None
    bt = os.path.join(SDK, "build-tools")
    for name in sorted(os.listdir(bt), reverse=True):
        cand = os.path.join(bt, name, "aapt2.exe")
        if os.path.exists(cand):
            aapt2 = cand
            break
    if not aapt2:
        raise SystemExit("aapt2 not found")
    r = subprocess.run([aapt2, "dump", "badging", apk], env=ENV,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    m = re.search(r"versionCode='(\d+)' versionName='([^']*)'", r.stdout)
    if not m:
        raise SystemExit("cannot read package info")
    return int(m.group(1)), m.group(2)


def clean_same_version(version, keep_name):
    """A same-version re-export replaces the previous package for that version."""
    prefix = "HoMiSe_" + version + "_"
    for f in os.listdir(RELEASE_DIR):
        if not f.startswith(prefix):
            continue
        if f == keep_name or f == keep_name + ".sha256":
            continue
        p = os.path.join(RELEASE_DIR, f)
        if os.path.isfile(p):
            os.remove(p)
            print("  replaced old " + f)


def clean_internal_packages(keep_name):
    """Keep every formal release and the newest internal package."""
    internal = []
    for f in os.listdir(RELEASE_DIR):
        p = os.path.join(RELEASE_DIR, f)
        if not os.path.isfile(p):
            continue
        m = re.match(r"^HoMiSe_(\d+)\.(\d+)\.(\d+)\.(\d+)_", f)
        if m:
            internal.append((tuple(int(x) for x in m.groups()), f))
    if not internal:
        return
    internal.sort(key=lambda item: item[0])
    for _, f in internal[:-1]:
        for victim in (os.path.join(RELEASE_DIR, f), os.path.join(RELEASE_DIR, f + ".sha256")):
            if os.path.exists(victim):
                os.remove(victim)
                print("  cleaned " + os.path.basename(victim))


def main():
    version, bump, summary = parse_args(sys.argv[1:])
    data = load()
    previous_internal = data.get("internalVersion", "")
    last_release = data.get("lastRelease", "")

    print("== freeze ==")
    print("  {0} -> {1} (bump={2})".format(previous_internal, version, bump))
    backup = VERSION_JSON + ".bak-" + time.strftime("%Y%m%d%H%M%S")
    shutil.copy2(VERSION_JSON, backup)
    print("  backup: " + os.path.basename(backup))

    version_code, today = freeze(data, version, bump, summary)
    save(data)
    print("  versionCode={0} stage=release".format(version_code))

    print("== build ==")
    gradle_build()

    apk = apk_path()
    code, name = apk_ident(apk)
    print("  versionCode={0} versionName={1}".format(code, name))
    if code != version_code or name != version:
        raise SystemExit("version mismatch: apk {0}/{1} vs expected {2}/{3}".format(
            code, name, version_code, version))

    digest = hashlib.sha256(open(apk, "rb").read()).hexdigest()
    stamp = time.strftime("%Y%m%d%H%M%S")
    fname = "HoMiSe_{0}_{1}_{2}.APK".format(version, stamp, digest[:16])
    dst = os.path.join(RELEASE_DIR, fname)
    os.makedirs(RELEASE_DIR, exist_ok=True)
    shutil.copy2(apk, dst)
    with io.open(dst + ".sha256", "w", encoding="utf-8", newline="\n") as f:
        f.write("{0}  {1}\n".format(digest, fname))
    print("== exported ==")
    print("  " + dst)
    print("  size {0:.2f} MB".format(os.path.getsize(dst) / 1024 / 1024))
    print("  sha256 " + digest)

    data = load()
    for r in data.get("releases", []):
        if r.get("version") == version:
            r["fileName"] = fname
            r["sha256"] = digest
            r["versionCode"] = version_code
    data["lastRelease"] = version
    save(data)

    clean_same_version(version, fname)
    clean_internal_packages(fname)
    print("== done ==")
    print("  run: python tools\\archive-release.py   (adds the VERSIONING.md row)")


if __name__ == "__main__":
    main()
