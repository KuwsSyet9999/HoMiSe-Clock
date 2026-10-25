"""Fix the plate insertion and wire the mono switch into MainActivity.

The previous pass inserted the plate line with a trailing comma after `modifier = Modifier`,
which breaks the chain, and it also matched two `Box` containers. This removes both Box
occurrences, drops the stray comma from the remaining five, and adds the missing
`monoLowercase` state plus its arguments at the ClockRoute call site.
"""
import io

SCREEN = r"D:\DSHin\HoMiSe\app\src\main\kotlin\com\homise\clock\ClockScreen.kt"
ACTIVITY = r"D:\DSHin\HoMiSe\app\src\main\kotlin\com\homise\clock\MainActivity.kt"

PLATE_COMMA = ".background(colors.dimmed.copy(alpha = 0.55f)),"
PLATE = ".background(colors.dimmed.copy(alpha = 0.55f))"


def fix_screen():
    lines = io.open(SCREEN, encoding="utf-8").readlines()

    # Delete plate lines whose enclosing composable is a Box (2 lines above starts with "Box(").
    drop = []
    for i, ln in enumerate(lines):
        if PLATE_COMMA not in ln:
            continue
        if i >= 2 and lines[i - 2].strip() == "Box(":
            drop.append(i)
    for i in sorted(drop, reverse=True):
        del lines[i]
    print("  removed plate from Box:", len(drop))

    # Drop the trailing comma from every remaining plate line.
    n = 0
    for i, ln in enumerate(lines):
        if PLATE_COMMA in ln:
            lines[i] = ln.replace(PLATE_COMMA, PLATE)
            n += 1
    print("  comma removed on plates:", n)

    io.open(SCREEN, "w", encoding="utf-8", newline="").writelines(lines)


def fix_activity():
    lines = io.open(ACTIVITY, encoding="utf-8").readlines()

    # 1) state declaration after fontStyle
    for i, ln in enumerate(lines):
        if "var fontStyle by remember { mutableStateOf(prefs.fontStyle) }" in ln:
            lines.insert(i + 1,
                         "                var monoLowercase by remember "
                         "{ mutableStateOf(prefs.monoLowercase) }\n")
            print("  state inserted at line", i + 2)
            break

    # 2) arguments just before iconReport in the ClockRoute call
    for i, ln in enumerate(lines):
        if ln.strip() == "iconReport = iconReport,":
            block = (
                "                    monoLowercase = monoLowercase,\n"
                "                    onToggleMono = {\n"
                "                        monoLowercase = !monoLowercase\n"
                "                        prefs.monoLowercase = monoLowercase\n"
                "                    },\n"
            )
            lines.insert(i, block)
            print("  args inserted at line", i + 1)
            break

    io.open(ACTIVITY, "w", encoding="utf-8", newline="").writelines(lines)


if __name__ == "__main__":
    fix_screen()
    fix_activity()
