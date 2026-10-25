"""Second half of this round's changes to ClockScreen.kt and MainActivity.kt.

* adds the translucent grey plate behind each info block (glyph offsets become visible)
* adds `monoLowercase` / `onToggleMono` plumbing, wired to a double-tap on the font-name block
* shows a "mono" marker in the font-name text and routes all block text through
  applyMonoLowercase so switching takes effect immediately
"""
import io
import re

SCREEN = r"D:\DSHin\HoMiSe\app\src\main\kotlin\com\homise\clock\ClockScreen.kt"
ACTIVITY = r"D:\DSHin\HoMiSe\app\src\main\kotlin\com\homise\clock\MainActivity.kt"

PLATE = ".background(colors.dimmed.copy(alpha = 0.55f)),"


def patch_screen():
    t = io.open(SCREEN, encoding="utf-8").read()
    orig = t

    # --- 1) plate behind each info block: insert right after "modifier = Modifier" ---
    def add_plate(m):
        indent = m.group(1)
        return m.group(0) + "\n" + indent + "    " + PLATE

    # only inside the overlay function (between its signature and end of file section)
    start = t.index("private fun androidx.compose.foundation.layout.BoxScope.ClockInfoOverlay(")
    head, tail = t[:start], t[start:]
    tail, n_plate = re.subn(r"(?m)^(\s+)modifier = Modifier$", add_plate, tail)
    t = head + tail

    # --- 2) overlay parameters ---
    t = t.replace(
        "    /** 电量百分比；-1 表示不可用，不显示 */",
        "    /** 是否启用等宽小写（双击字体名块切换） */\n"
        "    monoLowercase: Boolean = false,\n"
        "    /** 切换等宽小写的回调 */\n"
        "    onToggleMono: () -> Unit = {},\n"
        "    /** 电量百分比；-1 表示不可用，不显示 */",
    )

    # --- 3) font-name text: mono marker + lower-case mapping ---
    t = t.replace(
        '            text = "v${BuildConfig.DISPLAY_VERSION}$BUILD_TAG",',
        '            text = applyMonoLowercase("v${BuildConfig.DISPLAY_VERSION}$BUILD_TAG", monoLowercase),',
    )
    t = t.replace(
        "        text = shownName,",
        '        text = applyMonoLowercase(shownName + if (monoLowercase) " mono" else "", monoLowercase),',
    )
    t = t.replace(
        "                text = old,",
        "                text = applyMonoLowercase(old, monoLowercase),",
    )
    t = t.replace(
        "        text = stamp,",
        "        text = applyMonoLowercase(stamp, monoLowercase),",
    )

    # --- 4) double-tap on the font-name block toggles mono ---
    t = t.replace(
        ".then(hitModifier(pinName, phase) { pinName = !pinName })",
        ".then(hitModifier(pinName, phase, onDoubleTap = onToggleMono) { pinName = !pinName })",
    )

    # --- 5) hitModifier gains an optional double-tap ---
    t = t.replace(
        """private fun hitModifier(
    pinned: Boolean,
    phase: InfoPhase,
    onTap: () -> Unit,
): Modifier =
    if (pinned || phase == InfoPhase.Holding) {
        Modifier.pointerInput(Unit) { detectTapGestures(onTap = { onTap() }) }
    } else {
        Modifier
    }""",
        """private fun hitModifier(
    pinned: Boolean,
    phase: InfoPhase,
    onDoubleTap: (() -> Unit)? = null,
    onTap: () -> Unit,
): Modifier =
    if (pinned || phase == InfoPhase.Holding) {
        Modifier.pointerInput(Unit) {
            detectTapGestures(
                onTap = { onTap() },
                onDoubleTap = onDoubleTap?.let { cb -> { _: Offset -> cb() } },
            )
        }
    } else {
        Modifier
    }""",
    )

    if t == orig:
        print("  ! ClockScreen unchanged")
    io.open(SCREEN, "w", encoding="utf-8", newline="").write(t)
    print("  plates inserted:", n_plate)


def patch_activity():
    t = io.open(ACTIVITY, encoding="utf-8").read()
    orig = t

    # ClockRoute signature
    t = t.replace(
        "    iconReport: ClockIconVariants.Report? = null,\n) {",
        "    monoLowercase: Boolean = false,\n"
        "    onToggleMono: () -> Unit = {},\n"
        "    iconReport: ClockIconVariants.Report? = null,\n) {",
    )
    # ClockRoute -> ClockScreen
    t = t.replace(
        "        iconReport = iconReport,\n    )\n}",
        "        monoLowercase = monoLowercase,\n"
        "        onToggleMono = onToggleMono,\n"
        "        iconReport = iconReport,\n    )\n}",
    )
    # state
    t = t.replace(
        "                var pinnedBlocks by remember { mutableStateOf(prefs.pinnedInfoBlocks) }",
        "                var pinnedBlocks by remember { mutableStateOf(prefs.pinnedInfoBlocks) }\n"
        "                var monoLowercase by remember { mutableStateOf(prefs.monoLowercase) }",
    )
    # call site
    t = t.replace(
        "                    onPinnedChange = { pinnedBlocks = it; prefs.pinnedInfoBlocks = it },",
        "                    onPinnedChange = { pinnedBlocks = it; prefs.pinnedInfoBlocks = it },\n"
        "                    monoLowercase = monoLowercase,\n"
        "                    onToggleMono = {\n"
        "                        monoLowercase = !monoLowercase\n"
        "                        prefs.monoLowercase = monoLowercase\n"
        "                    },",
    )

    if t == orig:
        print("  ! MainActivity unchanged")
    io.open(ACTIVITY, "w", encoding="utf-8", newline="").write(t)
    print("  activity patched")


if __name__ == "__main__":
    patch_screen()
    patch_activity()
