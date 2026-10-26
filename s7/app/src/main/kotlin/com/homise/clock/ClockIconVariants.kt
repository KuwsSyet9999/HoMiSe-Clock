package com.homise.clock

import android.content.ComponentName
import android.content.Context
import android.content.pm.PackageManager
import android.util.Log

/**
 * 应用图标的 96 个变体：8 个字体族 × 6 个样式 × 2 种配色。
 *
 * Android 无法在运行时替换图标资源，只能为每个变体预先声明一个 `activity-alias`
 * （见 AndroidManifest.xml），切换时**启用目标别名并禁用其余**。
 * 因此必须保证任意时刻恰有一个别名处于启用状态——全都禁用会让应用从桌面消失。
 *
 * 别名与图标资源由 `tools/make-icon-variants.py` 生成，索引顺序为
 * `族 → 样式 → 配色 → 灰底`，本类必须与之保持一致。
 */
object ClockIconVariants {

    /** 4 族 × 6 样式 × 2 配色 × 2 灰底 = 96 */
    const val COUNT = 96

    private const val SCHEMES = 2
    private const val PHASES = 2
    private const val TAG = "ClockIconVariants"

    /**
     * 别名组件名以**运行时包名**（`packageName`）为前缀。
     *
     * 清单里别名写作 `${applicationId}.icon.IconV{i}`，会展开成**最终**包名（含
     * debug 变体的 `.debug` 后缀），因此这里必须用 `packageName` 而不是源码 namespace。
     *
     * 这一点极易踩坑：`PackageManager` 拒绝操作**包前缀与应用包名不一致**的组件
     * （"not a component of this package"），一旦前缀对不上，
     * `getComponentEnabledSetting` 就抛 IllegalArgumentException，图标永远切不动。
     * 注意 MainActivity 不受此限——组件能否被*加载*看的是完整类名，与这条规则无关。
     */
    private fun componentOf(pkg: String, index: Int) =
        ComponentName(pkg, "$pkg.icon.IconV$index")

    /**
     * 由当前字体与配色算出变体序号。
     * 遍历顺序必须与生成脚本一致：family 外层，style 次之，配色最内层。
     */
    fun indexOf(
        family: DsegFamily,
        style: DsegStyle,
        colorsInverted: Boolean,
        ghostVisible: Boolean,
    ): Int =
        family.ordinal * (DsegStyle.entries.size * SCHEMES * PHASES) +
            style.ordinal * (SCHEMES * PHASES) +
            (if (colorsInverted) 1 else 0) * PHASES +
            if (ghostVisible) 0 else 1

    /** 一次切换的诊断快照，用于在界面上判定"启用到底有没有生效"。 */
    data class Report(
        val want: Int,
        /** 目标别名在设置前的状态码（0=DEFAULT 1=ENABLED 2=DISABLED） */
        val before: Int,
        /** 设置后立即回读的状态码 */
        val after: Int,
        /** 全部处理完后，实际处于启用态的变体序号（-1 表示一个都没有） */
        val active: Int,
    )

    /** 读取单个组件的启用状态；组件不可操作时返回 -1。 */
    private fun readState(pm: PackageManager, pkg: String, index: Int): Int =
        try {
            pm.getComponentEnabledSetting(componentOf(pkg, index))
        } catch (e: IllegalArgumentException) {
            Log.w(TAG, "icon alias not operable: IconV$index", e)
            -1
        }

    /**
     * 切换到指定变体，并返回诊断快照。
     *
     * 先启用目标、再禁用其余。反序会在切换途中出现"一个入口都没有"的空窗，
     * 此时系统会回退到 `<application android:icon>`，桌面图标便不再跟随选择。
     *
     * 单个别名不可操作不应拖垮整个应用，因此逐个 try/catch。
     */
    fun apply(context: Context, index: Int): Report {
        val pm = context.packageManager
        val pkg = context.packageName
        val before = readState(pm, pkg, index)
        setState(pm, pkg, index, PackageManager.COMPONENT_ENABLED_STATE_ENABLED)
        val after = readState(pm, pkg, index)
        for (i in 0 until COUNT) {
            if (i == index) continue
            setState(pm, pkg, i, PackageManager.COMPONENT_ENABLED_STATE_DISABLED)
        }
        return Report(want = index, before = before, after = after, active = activeIndex(context))
    }

    /** 单个别名的状态同步；不可操作时只记日志，不抛给调用方。 */
    private fun setState(pm: PackageManager, pkg: String, index: Int, state: Int) {
        val component = componentOf(pkg, index)
        try {
            if (pm.getComponentEnabledSetting(component) != state) {
                pm.setComponentEnabledSetting(component, state, PackageManager.DONT_KILL_APP)
            }
        } catch (e: IllegalArgumentException) {
            Log.w(TAG, "icon alias not operable: $component", e)
        }
    }

    /**
     * 只读诊断快照：不做任何修改，仅反映"期望 vs 实际"。
     *
     * 真正的切换发生在 [MainActivity.onStop]，而不是用户操作当下——
     * 在前台禁用当前正在承载任务的别名，系统会结束该任务（表现为闪退）。
     */
    fun report(context: Context, want: Int): Report {
        val state = readState(context.packageManager, context.packageName, want)
        return Report(want = want, before = state, after = state, active = activeIndex(context))
    }

    /**
     * 回读当前实际生效的变体序号，供诊断显示。
     *
     * 判据是"未被显式禁用"而不只是 ENABLED：清单里 `android:enabled="true"` 的别名
     * 读回来是 COMPONENT_ENABLED_STATE_DEFAULT，并非 ENABLED。
     * 返回 -1 表示没有任何可用入口。
     */
    fun activeIndex(context: Context): Int {
        val pm = context.packageManager
        val pkg = context.packageName
        for (i in 0 until COUNT) {
            val state = try {
                pm.getComponentEnabledSetting(componentOf(pkg, i))
            } catch (e: IllegalArgumentException) {
                continue
            }
            if (state != PackageManager.COMPONENT_ENABLED_STATE_DISABLED) return i
        }
        return -1
    }
}
