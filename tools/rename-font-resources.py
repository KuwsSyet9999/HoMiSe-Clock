"""Rename the font resources so their names match the real family names.

  hsseg_7_*  -> hseg_7_*     (family is "HSEG 7 ...")
  dseg_14_*  -> hseg_16_*    (family is "HSEG 16 ...")

Touches: the 48 ttf files, ClockFont.kt's FONT_RESOURCES + fallbacks, and both tooling
scripts that reference the resource prefix.
"""
import io
import os
import re

FONT_DIR = r"D:\DSHin\HoMiSe\app\src\main\res\font"
CLOCK_FONT = r"D:\DSHin\HoMiSe\app\src\main\kotlin\com\homise\clock\ClockFont.kt"
ICON_TOOL = r"D:\DSHin\HoMiSe\tools\make-icon-variants.py"
REPLACE_TOOL = r"D:\DSHin\HoMiSe\tools\replace-fonts-with-ttc.py"

RENAMES = [("hsseg_7_", "hseg_7_"), ("dseg_14_", "hseg_16_")]


def rename_files():
    n = 0
    for old, new in RENAMES:
        for name in sorted(os.listdir(FONT_DIR)):
            if not name.startswith(old) or not name.endswith(".ttf"):
                continue
            src = os.path.join(FONT_DIR, name)
            dst = os.path.join(FONT_DIR, new + name[len(old):])
            if os.path.exists(dst):
                print("  ! exists, skip:", dst)
                continue
            os.rename(src, dst)
            n += 1
    print("  files renamed:", n)
    return n


def patch_text(path, pairs, label):
    t = io.open(path, encoding="utf-8").read()
    orig = t
    for pat, rep in pairs:
        t = t.replace(pat, rep)
    if t != orig:
        io.open(path, "w", encoding="utf-8", newline="").write(t)
        print("  patched:", label)
    else:
        print("  no change:", label)


def main():
    rename_files()

    # Kotlin: resource ids + fallbacks + comments
    patch_text(CLOCK_FONT, [
        ("R.font.hsseg_7_", "R.font.hseg_7_"),
        ("R.font.dseg_14_", "R.font.hseg_16_"),
        ("hsseg_7_", "hseg_7_"),
        ("dseg_14_", "hseg_16_"),
    ], "ClockFont.kt")

    # Icon generator
    patch_text(ICON_TOOL, [
        ('"hsseg_7_', '"hseg_7_'),
        ('"dseg_14_', '"hseg_16_'),
        ("hsseg_7_", "hseg_7_"),
        ("dseg_14_", "hseg_16_"),
    ], "make-icon-variants.py")

    # Font replacement tool
    patch_text(REPLACE_TOOL, [
        ('"hsseg_7_', '"hseg_7_'),
        ('"dseg_14_', '"hseg_16_'),
        ("hsseg_7_", "hseg_7_"),
        ("dseg_14_", "hseg_16_"),
    ], "replace-fonts-with-ttc.py")

    # 确认没有漏网的旧前缀
    leftovers = []
    for name in os.listdir(FONT_DIR):
        if name.startswith(("hsseg_7_", "dseg_14_")):
            leftovers.append(name)
    print("\n  leftover old-prefix fonts:", leftovers if leftovers else "none")


if __name__ == "__main__":
    main()
