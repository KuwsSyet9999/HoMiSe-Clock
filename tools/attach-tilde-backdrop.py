"""Attach the per-character tilde backdrop to the five info Text blocks.

Each block gets `.tildeBackdrop(...)` as the first modifier, wrapped in a DEBUG check so
release builds stay clean. The backdrop receives the *same* text expression as the block,
so the frames line up with the glyphs actually drawn (including the mono mapping).
"""
import io
import re

PATH = r"D:\DSHin\HoMiSe\app\src\main\kotlin\com\homise\clock\ClockScreen.kt"

# (modifier line number, text expression, fontSize expression) — 1-based, bottom-up
TARGETS = [
    (903, 'applyMonoLowercase("${batteryPercent}${if (fontFamily.series == 7) ".:" else "%"}", monoLowercase)', "BATTERY_FONT_SIZE"),
    (882, 'applyMonoLowercase("v${BuildConfig.DISPLAY_VERSION}$BUILD_TAG", monoLowercase)', "nameSize"),
    (856, 'applyMonoLowercase(shownName + if (monoLowercase) " mono" else "", monoLowercase)', "nameSize"),
    (843, 'applyMonoLowercase(old, monoLowercase)', "nameSize"),
    (812, 'applyMonoLowercase(stamp, monoLowercase)', "stampSize.sp"),
]

IMPORTS = [
    "import androidx.compose.ui.text.TextMeasurer",
    "import androidx.compose.ui.text.drawText",
    "import androidx.compose.ui.text.rememberTextMeasurer",
    "import androidx.compose.ui.text.PlatformTextStyle",
    "import androidx.compose.ui.unit.TextUnit",
]


def main():
    lines = io.open(PATH, encoding="utf-8").readlines()

    for ln, text_expr, size_expr in TARGETS:
        idx = ln - 1
        if "modifier = Modifier" not in lines[idx]:
            print("  ! line {0} not a modifier anchor: {1}".format(ln, lines[idx].strip()))
            continue
        indent = re.match(r"^(\s*)", lines[idx]).group(1) + "    "
        block = (
            indent + ".then(\n"
            + indent + "    if (BuildConfig.DEBUG) {\n"
            + indent + "        Modifier.tildeBackdrop(\n"
            + indent + "            text = " + text_expr + ",\n"
            + indent + "            font = font,\n"
            + indent + "            fontSize = " + size_expr + ",\n"
            + indent + "            lineHeight = TextUnit.Unspecified,\n"
            + indent + "            color = colors.dimmed,\n"
            + indent + "            measurer = tildeMeasurer,\n"
            + indent + "        )\n"
            + indent + "    } else {\n"
            + indent + "        Modifier\n"
            + indent + "    },\n"
            + indent + ")\n"
        )
        lines.insert(idx + 1, block)
        print("  backdrop attached at line", ln)

    text = "".join(lines)

    # add missing imports
    for imp in IMPORTS:
        if imp + "\n" not in text:
            # insert after the last existing import
            m = list(re.finditer(r"(?m)^import .+$", text))
            if m:
                pos = m[-1].end() + 1
                text = text[:pos] + imp + "\n" + text[pos:]
                print("  import added:", imp.split(".")[-1])

    io.open(PATH, "w", encoding="utf-8", newline="").write(text)
    print("done, lines:", len(text.splitlines()))


if __name__ == "__main__":
    main()
