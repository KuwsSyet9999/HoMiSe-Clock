package com.homise.clock

import android.content.Context

/**
 * 用户偏好，用 SharedPreferences 持久化，重启应用后仍然保持。
 *
 * 目前包含四项：
 *   - **[colorsInverted]**：是否把背景色与数字色互换（双击画面切换）；
 *   - **[fontFamily]**：DSEG 字体族（自右向左滑切换）；
 *   - **[fontStyle]**：字体的字重/斜体样式（自下向上滑切换）；
 *   - **[pinnedInfoBlocks]**：已设为「常驻」的信息块标识集合。
 *
 * 它们都以**名称/标识字符串**而非序号存储：这样即使以后调整枚举顺序或增删信息块，
 * 也不会把用户的选择错配到别处。
 *
 * 亮度**不做继承**：每次启动都恢复默认的最大亮度，长按切换只在本次运行期间有效，
 * 因此这里刻意不保存亮度状态。
 */
class ClockPreferences(context: Context) {

    private val prefs = context.applicationContext
        .getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    /** 是否互换配色：false = 黑底白字（默认），true = 白底黑字。 */
    var colorsInverted: Boolean
        get() = prefs.getBoolean(KEY_INVERTED, false)
        set(value) = prefs.edit().putBoolean(KEY_INVERTED, value).apply()

    /** 当前字体族；名称无法识别（例如版本降级）时回退到默认值。 */
    var fontFamily: DsegFamily
        get() = prefs.getString(KEY_FONT_FAMILY, null)
            ?.let { name -> DsegFamily.entries.firstOrNull { it.name == name } }
            ?: DefaultDsegFamily
        set(value) = prefs.edit().putString(KEY_FONT_FAMILY, value.name).apply()

    /** 当前字体样式；同样以名称存储并带兜底。 */
    var fontStyle: DsegStyle
        get() = prefs.getString(KEY_FONT_STYLE, null)
            ?.let { name -> DsegStyle.entries.firstOrNull { it.name == name } }
            ?: DefaultDsegStyle
        set(value) = prefs.edit().putString(KEY_FONT_STYLE, value.name).apply()

    /**
     * 已设为「常驻」的信息块标识集合，重启后保持。
     *
     * 用标识字符串而非序号：以后增删信息块时，旧值不会因顺序变化而错配到别的块上。
     */
    var pinnedInfoBlocks: Set<String>
        // 默认值含电量：电量默认常驻（见 DEFAULT_PINNED_INFO_BLOCKS）。
        // 用户取消后会写入空集合/其余组合，重启即为用户的选择，不会被默认值覆盖。
        get() = prefs.getStringSet(KEY_PINNED_BLOCKS, DEFAULT_PINNED_INFO_BLOCKS)
            ?: DEFAULT_PINNED_INFO_BLOCKS
        set(value) = prefs.edit().putStringSet(KEY_PINNED_BLOCKS, value.toSet()).apply()

    /**
     * 是否显示灰底：时钟的熄灭段（全亮字形的暗色层）与信息块的字框。
     *
     * 默认显示。双击时钟数字区切换；切换后时钟只剩纯亮段、信息文字转灰并隐藏字框。
     */
    var ghostVisible: Boolean
        get() = prefs.getBoolean(KEY_GHOST, true)
        set(value) = prefs.edit().putBoolean(KEY_GHOST, value).apply()

    /**
     * 是否把信息文本里的小写字母替换为等宽字形（字体私有区 U+E000~U+E019）。
     *
     * 字体中小写字母的**笔迹窄但占位是全宽**（例如 `i` 的空白占比达 89%），字距过宽、
     * 阅读不顺；等宽码位提供 408（数字宽的一半）的占位，可在完全不改动原字体的前提下
     * 收紧排版。双击字体名块切换。
     */
    var monoLowercase: Boolean
        get() = prefs.getBoolean(KEY_MONO_LOWER, false)
        set(value) = prefs.edit().putBoolean(KEY_MONO_LOWER, value).apply()

    /**
     * 尚未落地的图标变体序号（-1 表示无）。
     *
     * 图标只能在 onStop 里切换，而「强制停止」不会触发任何生命周期回调，
     * 内存里的待切换值会随进程一起丢失。写入偏好后，下次启动可以接着完成。
     */
    var pendingIconVariant: Int
        get() = prefs.getInt(KEY_PENDING_ICON, -1)
        set(value) = prefs.edit().putInt(KEY_PENDING_ICON, value).apply()

    /** 清空全部偏好，恢复出厂设置（含未落实的图标切换）。 */
    fun resetAll() {
        prefs.edit().clear().apply()
    }

    private companion object {
        const val PREFS_NAME = "homise_clock_prefs"
        const val KEY_INVERTED = "colors_inverted"
        const val KEY_FONT_FAMILY = "font_family"
        const val KEY_FONT_STYLE = "font_style"
        const val KEY_PINNED_BLOCKS = "pinned_info_blocks"
        const val KEY_MONO_LOWER = "mono_lowercase"
        const val KEY_GHOST = "ghost_visible"
        const val KEY_PENDING_ICON = "pending_icon_variant"
    }
}
