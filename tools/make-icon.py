"""Generate the HoMiSe launcher icon.

Layout -- three rows on one vertical axis, uniform font size:

        09
    16:25:38
        47

with a grey "all-8" ghost underneath (88 / 88:88:88 / 88) marking the unlit
segments, exactly as the app renders them.

CALIBRATION RULE (requested): the icon is centred **by the grey ghost**, not by
the white digits. The ghost uses full, symmetric character cells ("8" lights
every segment), so it is the trustworthy reference. White digits such as
"16:25:38" begin with a "1" whose ink sits far right inside its own cell
(ink x=[624,717]); measuring against that would bias the centring.

SAFE ZONE = 66 dp (264 px when the canvas is 108 dp = 432 px). 72 dp is only the
*visible* area of the launcher mask -- content reaching out to 72 dp gets clipped
by round masks, which is why the icon must be laid out inside 66 dp.
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = r"D:\DSHin\HoMiSe\app\src\main\res\font\dseg_7_classic_regular.ttf"
OUT_DIR = r"D:\DSHin\HoMiSe\docs\icon"
os.makedirs(OUT_DIR, exist_ok=True)

S = 432                                  # 108 dp @ 4x
SAFE = 264                               # 66 dp safe zone
MARGIN = (S - SAFE) / 2                  # 84
BG = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
GREY = (51, 51, 51, 255)                 # app's extinguished-segment grey #333333

COLON_INK = 0.124                        # colon ink width, per em
DIGIT_ADV = 0.816                        # digit advance, per em
DIGIT_SIDE_INK = 0.099                   # digit side bearing (ink x=[99,717])

# Font size comes from the GREY ghost: its full-width row plus one colon ink
# width of clearance on each side must equal the safe zone.
GREY_LONG_INK = 6 * DIGIT_ADV + 2 * 0.2 - 2 * DIGIT_SIDE_INK     # 5.098 em
PX = int(round(SAFE / (GREY_LONG_INK + 2 * COLON_INK)))
GAP = PX * 1.2                           # same 1.2 em row box as the app
CY = S / 2

ROWS = [
    ("88", "09", CY - GAP),
    ("88:88:88", "16:25:38", CY),
    ("88", "47", CY + GAP),
]


def draw_text(draw, text, px, cx, cy, fill):
    font = ImageFont.truetype(FONT_PATH, px)
    draw.text((cx, cy), text, font=font, fill=fill, anchor="mm")


def render(with_grey=True, with_white=True, background=BG):
    img = Image.new("RGBA", (S, S), background)
    d = ImageDraw.Draw(img)
    if with_grey:
        for grey_text, _, y in ROWS:
            draw_text(d, grey_text, PX, S / 2, y, GREY)
    if with_white:
        for _, white_text, y in ROWS:
            draw_text(d, white_text, PX, S / 2, y, WHITE)
    return img


icon = render()
icon.save(os.path.join(OUT_DIR, "icon_final_grey.png"))
render(with_grey=False).save(os.path.join(OUT_DIR, "icon_final_plain.png"))


def ink_bounds(img, grey_layer):
    """Bounding box of the ink to be calibrated: the grey ghost, or the white digits."""
    arr = np.array(img)
    if grey_layer:
        mask = (arr[:, :, 0] > 20) & (arr[:, :, 0] < 120) & (arr[:, :, 3] > 0)
    else:
        mask = (arr[:, :, 0] > 250) & (arr[:, :, 3] > 0)
    xs = np.where(mask.any(axis=0))[0]
    ys = np.where(mask.any(axis=1))[0]
    return int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())


ghost = render(with_white=False, background=(0, 0, 0, 0))
gl, gr, gt, gb = ink_bounds(ghost, grey_layer=True)
wl, wr, wt, wb = ink_bounds(icon, grey_layer=False)

print(f"font size            : {PX} px   (safe zone {SAFE} px = 66 dp)")
print(f"one colon ink width  : {PX * COLON_INK:.1f} px")
print()
print("--- calibrated by the GREY ghost (the reference) ---")
print(f"ghost ink x          : {gl}..{gr}   centre {(gl + gr) / 2:.1f}  (canvas centre {S / 2})")
print(f"ghost ink y          : {gt}..{gb}   centre {(gt + gb) / 2:.1f}")
print(f"horizontal clearance : {gl - MARGIN:.0f} / {(S - MARGIN) - gr:.0f} px")
print(f"vertical clearance   : {gt - MARGIN:.0f} / {(S - MARGIN) - gb:.0f} px")
print()
print("--- white digits (informational) ---")
print(f"white ink x          : {wl}..{wr}   centre {(wl + wr) / 2:.1f}")

# launcher-size preview
small = Image.new("RGBA", (96 * 2 + 30, 96 + 40), (24, 24, 24, 255))
small.paste(icon.resize((96, 96), Image.LANCZOS), (10, 20))
small.paste(render(with_grey=False).resize((96, 96), Image.LANCZOS), (10 + 96 + 10, 20))
small.save(os.path.join(OUT_DIR, "preview_final_small.png"))

sheet = Image.new("RGBA", (2 * 432 + 3 * 24, 432 + 2 * 24), (18, 18, 18, 255))
sheet.paste(icon, (24, 24))
sheet.paste(render(with_grey=False), (24 + 432 + 24, 24))
sheet.save(os.path.join(OUT_DIR, "compare_final.png"))

# ---- export adaptive-icon FOREGROUND at every density ----
RES_DIR = r"D:\DSHin\HoMiSe\app\src\main\res"
foreground = render(background=(0, 0, 0, 0))
print("\nforeground layers (108 dp, content inside the 66 dp safe zone):")
for density, px in [("mdpi", 108), ("hdpi", 162), ("xhdpi", 216), ("xxhdpi", 324), ("xxxhdpi", 432)]:
    target_dir = os.path.join(RES_DIR, "mipmap-" + density)
    os.makedirs(target_dir, exist_ok=True)
    foreground.resize((px, px), Image.LANCZOS).save(
        os.path.join(target_dir, "ic_launcher_foreground.png"))
    print(f"  mipmap-{density}/ic_launcher_foreground.png  {px}x{px}")
