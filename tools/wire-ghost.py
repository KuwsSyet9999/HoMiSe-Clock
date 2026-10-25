"""Wire ghostVisible through preferences, ClockRoute and MainActivity."""
import io
import re

PREFS = r"D:\DSHin\HoMiSe\app\src\main\kotlin\com\homise\clock\ClockPreferences.kt"
SCREEN = r"D:\DSHin\HoMiSe\app\src\main\kotlin\com\homise\clock\MainActivity.kt"


def patch_prefs():
    t = io.open(PREFS, encoding="utf-8").read()
    if "ghostVisible" in t:
        print("  prefs already has ghostVisible")
        return
    t = t.replace(
        """    /**
     * 是否把信息文本里的小写字母替换为等宽字形""",
        """    /**
     * 是否显示灰底：时钟的熄灭段（全亮字形的暗色层）与信息块的字框。
     *
     * 默认显示。双击时钟数字区切换；切换后时钟只剩纯亮段、信息文字转灰并隐藏字框。
     */
    var ghostVisible: Boolean
        get() = prefs.getBoolean(KEY_GHOST, true)
        set(value) = prefs.edit().putBoolean(KEY_GHOST, value).apply()

    /**
     * 是否把信息文本里的小写字母替换为等宽字形""", 1)
    t = t.replace('        const val KEY_MONO_LOWER = "mono_lowercase"',
                  '        const val KEY_MONO_LOWER = "mono_lowercase"\n'
                  '        const val KEY_GHOST = "ghost_visible"')
    io.open(PREFS, "w", encoding="utf-8", newline="").write(t)
    print("  prefs patched")


def patch_activity():
    t = io.open(SCREEN, encoding="utf-8").read()
    if "ghostVisible" in t:
        print("  activity already has ghostVisible")
        return

    # ClockRoute 参数
    t = t.replace(
        "    monoLowercase: Boolean = false,",
        "    ghostVisible: Boolean = true,\n"
        "    onToggleGhost: () -> Unit = {},\n"
        "    monoLowercase: Boolean = false,", 1)

    # ClockRoute -> ClockScreen
    t = t.replace(
        "        monoLowercase = monoLowercase,",
        "        ghostVisible = ghostVisible,\n"
        "        onToggleGhost = onToggleGhost,\n"
        "        monoLowercase = monoLowercase,", 1)

    # 状态
    t = t.replace(
        "                var monoLowercase by remember { mutableStateOf(prefs.monoLowercase) }",
        "                var monoLowercase by remember { mutableStateOf(prefs.monoLowercase) }\n"
        "                var ghostVisible by remember { mutableStateOf(prefs.ghostVisible) }", 1)

    # 调用点
    t = t.replace(
        "                    monoLowercase = monoLowercase,",
        "                    ghostVisible = ghostVisible,\n"
        "                    onToggleGhost = {\n"
        "                        ghostVisible = !ghostVisible\n"
        "                        prefs.ghostVisible = ghostVisible\n"
        "                    },\n"
        "                    monoLowercase = monoLowercase,", 1)

    io.open(SCREEN, "w", encoding="utf-8", newline="").write(t)
    print("  activity patched")


if __name__ == "__main__":
    patch_prefs()
    patch_activity()
