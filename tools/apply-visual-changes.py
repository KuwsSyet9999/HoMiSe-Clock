"""Apply this round's visual changes to ClockScreen.kt.

1. Info-block text switches from the muted label grey to the digit colour, and each
   block gains a translucent grey plate -- the plate makes glyph offsets visible.
2. The coloured hit-box overlay is removed (it was obscuring the glyphs it marked).
3. Line-based edits are applied bottom-up so earlier line numbers stay valid.
"""
import io
import re

PATH = r"D:\DSHin\HoMiSe\app\src\main\kotlin\com\homise\clock\ClockScreen.kt"

# 1-based line numbers of info-block `color = colors.label,` occurrences (inside the overlay)
COLOR_LINES = [794, 831, 844, 870, 891]
# Matches a block's Text(...) color line so we can add the plate right after it.
PLATE = "            .background(colors.dimmed.copy(alpha = 0.55f)),\n"


def main():
    lines = io.open(PATH, encoding="utf-8").readlines()
    print("original lines:", len(lines))

    # --- 1) colours: label -> digits (bottom-up) ---
    for ln in sorted(COLOR_LINES, reverse=True):
        idx = ln - 1
        if "colors.label" not in lines[idx]:
            print("  ! line {0} not a label colour: {1}".format(ln, lines[idx].strip()))
            continue
        lines[idx] = lines[idx].replace("colors.label", "colors.digits")
    print("  colours switched: {0}".format(len(COLOR_LINES)))

    text = "".join(lines)

    # --- 2) drop the hit-box block ---
    text, n1 = re.subn(
        r"\n    // 调试：把四块的实际命中范围画出来。.*?\n    if \(showHitBoxes\) \{.*?\n    \}\n",
        "\n",
        text,
        flags=re.S,
    )
    # --- 3) drop the HitBox composable ---
    text, n2 = re.subn(
        r"\n/\*\*\n \* 调试用：用彩色方框标出一块信息的实际命中范围。.*?\n\}\n",
        "\n",
        text,
        flags=re.S,
    )
    # --- 4) drop showHitBoxes parameter and its call-site argument ---
    text, n3 = re.subn(r"\n *showHitBoxes: Boolean = false,", "", text)
    text, n4 = re.subn(r"\n *showHitBoxes = showDebugMarks,", "", text)

    print("  removed: block={0} composable={1} param={2} call={3}".format(n1, n2, n3, n4))

    io.open(PATH, "w", encoding="utf-8", newline="").write(text)
    print("written, lines now:", len(text.splitlines()))


if __name__ == "__main__":
    main()
