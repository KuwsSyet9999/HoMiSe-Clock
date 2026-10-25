"""Export a HoMiSe APK without PowerShell.

The project's existing tools/export-apk.ps1 cannot run here: the sandbox runs pwsh in
ConstrainedLanguage mode, which refuses to execute any .ps1 file. Everything that script
does is reachable from Python, so this reimplements the parts needed for an internal
(iteration) export:

  1. bump the iteration number in version.json (internal builds only)
  2. build the debug APK with gradle
  3. read versionCode / versionName back out of the APK and compare with version.json
  4. name it HoMiSe_<version>_<14-digit time>_<hash16>.APK and copy it into release/
  5. drop older internal packages, keep every formal release

No elevation required.
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
import zipfile

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


def load_version():
    with io.open(VERSION_JSON, encoding="utf-8") as f:
        return json.load(f)


def save_version(data):
    with io.open(VERSION_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def bump_iteration(summary):
    data = load_version()
    data["current"]["iteration"] += 1
    c = data["current"]
    ver = "{0}.{1}.{2}.{3}".format(c["major"], c["minor"], c["patch"], c["iteration"])
    data["internalVersion"] = ver
    data["stage"] = "internal"
    data["history"].append({
        "internalVersion": ver,
        "date": time.strftime("%Y-%m-%d"),
        "summary": summary,
    })
    data["updated"] = time.strftime("%Y-%m-%d")
    save_version(data)
    print("  iteration -> " + ver)
    return ver


def gradle_build():
    cmd = [GRADLE, "-p", ROOT, "assembleDebug", "--offline"]
    print("  running gradle assembleDebug ...")
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
    p = os.path.join(ROOT, "app", "build", "outputs", "apk", "debug", "app-debug.apk")
    if not os.path.exists(p):
        raise SystemExit("APK not found: " + p)
    return p


def apk_ident(apk):
    """versionCode / versionName live in the binary manifest; aapt2 can dump them."""
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


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    nobump = "--nobump" in sys.argv
    summary = args[0] if args else "内部迭代构建"

    if nobump:
        data = load_version()
        c = data["current"]
        ver = "{0}.{1}.{2}.{3}".format(c["major"], c["minor"], c["patch"], c["iteration"])
        print("== bump skipped ==")
        print("  iteration stays " + ver)
    else:
        print("== bump ==")
        ver = bump_iteration(summary)

    print("== build ==")
    gradle_build()

    apk = apk_path()
    code, name = apk_ident(apk)
    print("  versionCode={0} versionName={1}".format(code, name))

    data = load_version()
    c = data["current"]
    # build.gradle.kts: code = maj*1_000_000 + min*10_000 + patch*100 + 1 + iteration
    expect_code = (c["major"] * 1_000_000 + c["minor"] * 10_000
                   + c["patch"] * 100 + 1 + c["iteration"])
    # debug variant appends "-internal" to the name and never carries the iteration
    expect_name = "{0}.{1}.{2}-internal".format(c["major"], c["minor"], c["patch"])
    if code != expect_code or name != expect_name:
        raise SystemExit("version mismatch: apk {0}/{1} vs expected {2}/{3}".format(
            code, name, expect_code, expect_name))

    digest = hashlib.sha256(open(apk, "rb").read()).hexdigest()
    stamp = time.strftime("%Y%m%d%H%M%S")
    fname = "HoMiSe_{0}_{1}_{2}.APK".format(ver, stamp, digest[:16])
    dst = os.path.join(RELEASE_DIR, fname)
    os.makedirs(RELEASE_DIR, exist_ok=True)
    shutil.copy2(apk, dst)
    print("== exported ==")
    print("  " + dst)
    print("  size {0:.2f} MB".format(os.path.getsize(dst) / 1024 / 1024))
    print("  sha256 " + digest)

    # keep only the newest internal package; formal releases are never touched
    keep = fname
    for f in os.listdir(RELEASE_DIR):
        p = os.path.join(RELEASE_DIR, f)
        if not os.path.isfile(p):
            continue
        if not re.match(r"^HoMiSe_\d+\.\d+\.\d+\.\d+_", f):
            continue          # formal release -> keep
        if f == keep:
            continue
        for suffix in ("", ".sha256"):
            victim = p + suffix if suffix else p
            if os.path.exists(victim):
                os.remove(victim)
                print("  cleaned " + os.path.basename(victim))


if __name__ == "__main__":
    main()
