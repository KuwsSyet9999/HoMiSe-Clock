"""Replace the S7 fonts with the faces from the HSEG7 1.1.0 collection."""
import os

from fontTools.ttLib import TTCollection

ROOT = r"D:\DSHin\HoMiSe\s7"
FONT_DIR = os.path.join(ROOT, "app", "src", "main", "res", "font")
TTC = r"D:\DSHin\HoMiSe\release\HSEG7_1.1.0_20261027002759_774d36e5b003ed83.ttc"

FAMILY = {
    "HSEG7Classic": "hseg_7_classic",
    "HSEG7ClassicMini": "hseg_7_classic_mini",
    "HSEG7Modern": "hseg_7_modern",
    "HSEG7ModernMini": "hseg_7_modern_mini",
}
STYLE = {
    "Light": "light",
    "LightItalic": "light_italic",
    "Regular": "regular",
    "Italic": "italic",
    "Bold": "bold",
    "BoldItalic": "bold_italic",
}

coll = TTCollection(TTC)
print("faces:", len(coll.fonts))
n = 0
for face in coll.fonts:
    ps = face["name"].getDebugName(6)
    family, style = ps.split("-", 1)
    if family not in FAMILY or style not in STYLE:
        print("skip", ps)
        continue
    target = os.path.join(FONT_DIR, "%s_%s.ttf" % (FAMILY[family], STYLE[style]))
    if not os.path.exists(target):
        print("missing", target)
        continue
    face.save(target)
    n += 1
print("replaced", n)
