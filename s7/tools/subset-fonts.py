"""Subset the S7 fonts to the glyphs the UI can actually render.

S7 has no font-name block, so the only text is: clock digits, the ISO stamp
(`0-9 - : + T Z`), the version (`v`, `.`) and the battery (`.:`).
Originals are backed up once to tools/font-backup/.
"""
import os
import shutil

from fontTools import subset

ROOT = r"D:\DSHin\HoMiSe\s7"
FONT_DIR = os.path.join(ROOT, "app", "src", "main", "res", "font")
BACKUP = os.path.join(ROOT, "tools", "font-backup")
CHARS = "0123456789:.-+TZv"

os.makedirs(BACKUP, exist_ok=True)
print("charset:", CHARS)

total_before = total_after = 0
count = 0
for name in sorted(os.listdir(FONT_DIR)):
    if not (name.startswith("hseg_7_") and name.endswith(".ttf")):
        continue
    src = os.path.join(FONT_DIR, name)
    backup = os.path.join(BACKUP, name)
    if not os.path.exists(backup):
        shutil.copy2(src, backup)
    before = os.path.getsize(src)
    opts = subset.Options()
    opts.layout_features = []
    opts.hinting = False
    opts.notdef_outline = True
    font = subset.load_font(src, opts)
    ss = subset.Subsetter(options=opts)
    ss.populate(text=CHARS)
    ss.subset(font)
    subset.save_font(font, src, opts)
    after = os.path.getsize(src)
    total_before += before
    total_after += after
    count += 1

print("subset %d fonts: %.1f KB -> %.1f KB" % (count, total_before / 1024, total_after / 1024))
