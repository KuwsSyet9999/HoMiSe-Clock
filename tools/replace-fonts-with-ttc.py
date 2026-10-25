"""Replace the app's font resources with the faces packed in an HSSeg .ttc.

Each .ttc is a TrueType Collection holding 24 faces (4 families x 6 styles). Every
face is extracted and written over the matching resource, so the resource names the
app already references stay untouched.

Two families are handled:

  * HSSeg7  -> dseg_7_*   (seven-segment series)
  * HSSeg16 -> hseg_16_*  (the app keeps the hseg_16_* resource names for the
                           fourteen-segment series; sixteen-segment artwork is used
                           to fill them)

Originals are copied to tools/font_backup_dseg7 / tools/font_backup_dseg14 first —
the replacement is destructive, and that backup is the only way back. A backup is
only written when one does not already exist, so re-running never overwrites the
pristine originals.
"""
import os
import shutil
import sys

from fontTools.ttLib import TTCollection

ROOT = r"D:\DSHin\HoMiSe"
FONT_DIR = os.path.join(ROOT, "app", "src", "main", "res", "font")
BACKUP_DIR_7 = os.path.join(ROOT, "tools", "font_backup_dseg7")
BACKUP_DIR_14 = os.path.join(ROOT, "tools", "font_backup_dseg14")
TTC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    ROOT, "release", "HSSeg7_0.1.0_20261020012110_ed67cf4743f917a9.ttc")

FAMILY_MAP = {
    "HSSeg7Classic": "dseg_7_classic",
    "HSSeg7ClassicMini": "dseg_7_classic_mini",
    "HSSeg7Modern": "dseg_7_modern",
    "HSSeg7ModernMini": "dseg_7_modern_mini",
    # 十六段字族用于填充应用中的十四段资源（资源名保持不变）
    "HSSeg16Classic": "hseg_16_classic",
    "HSSeg16ClassicMini": "hseg_16_classic_mini",
    "HSSeg16Modern": "hseg_16_modern",
    "HSSeg16ModernMini": "hseg_16_modern_mini",
    # 字体侧后来把家族名从 HSSeg16 改为 HSEG16，映射同步
    "HSEG16Classic": "hseg_16_classic",
    "HSEG16ClassicMini": "hseg_16_classic_mini",
    "HSEG16Modern": "hseg_16_modern",
    "HSEG16ModernMini": "hseg_16_modern_mini",
    # 七段的正式版族名是 HSEG7，资源名现为 hseg_7_*（另一轮把 dseg_7_ 改名为 hseg_7_）
    "HSEG7Classic": "hseg_7_classic",
    "HSEG7ClassicMini": "hseg_7_classic_mini",
    "HSEG7Modern": "hseg_7_modern",
    "HSEG7ModernMini": "hseg_7_modern_mini",
}
STYLE_MAP = {
    "Light": "light",
    "LightItalic": "light_italic",
    "Regular": "regular",
    "Italic": "italic",
    "Bold": "bold",
    "BoldItalic": "bold_italic",
}


def backup_dir_for(res_name):
    """Serif families back up separately so one replacement cannot clobber the other."""
    return BACKUP_DIR_14 if res_name.startswith("hseg_16_") else BACKUP_DIR_7


def main():
    os.makedirs(BACKUP_DIR_7, exist_ok=True)
    os.makedirs(BACKUP_DIR_14, exist_ok=True)
    coll = TTCollection(TTC)
    print("ttc 内字体数: {0}".format(len(coll.fonts)))

    replaced = 0
    skipped = 0
    for face in coll.fonts:
        ps = face["name"].getDebugName(6)          # e.g. HSSeg16Classic-LightItalic
        family, style = ps.split("-", 1)
        if family not in FAMILY_MAP:
            print("  ! 未配置的家族，跳过: " + family)
            skipped += 1
            continue
        res_name = FAMILY_MAP[family] + "_" + STYLE_MAP[style] + ".ttf"
        target = os.path.join(FONT_DIR, res_name)

        if not os.path.exists(target):
            print("  ! 目标不存在，跳过: " + res_name)
            skipped += 1
            continue

        # 只在**尚无备份**时备份：否则重复运行会用"上一次替换后的字体"覆盖原始备份，
        # 把唯一的回退来源弄丢。
        backup_path = os.path.join(backup_dir_for(res_name), res_name)
        if not os.path.exists(backup_path):
            shutil.copy2(target, backup_path)

        face.save(target)
        replaced += 1
        print("  {0:34s} <- {1}".format(res_name, ps))

    print("\n已替换 {0} 个文件，跳过 {1} 个".format(replaced, skipped))


if __name__ == "__main__":
    main()
