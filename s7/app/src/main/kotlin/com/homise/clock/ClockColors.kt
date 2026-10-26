package com.homise.clock

import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color

/**
 * 一套界面配色。黑白两套互为「互换」——双击画面即在两者之间切换。
 *
 * 每个颜色都有对应的反向取值：换成白底时，必须把熄灭段、调试基准线、标签灰
 * 一并换成浅色，否则这些灰会落在白底上而看不见。
 */
data class ClockColors(
    /** 画面底色 */
    val background: Color,
    /** 点亮的数字 */
    val digits: Color,
    /** 熄灭段（底层全 8 的灰） */
    val dimmed: Color,
    /** 调试井字线 */
    val debugLine: Color,
    /** 右下角版本号与诊断文字 */
    val label: Color,
)

/** 默认：纯黑底 + 白色数字。 */
val DarkClockColors = ClockColors(
    background = Color(0xFF000000),
    digits = Color(0xFFFFFFFF),
    dimmed = Color(0xFF333333),
    debugLine = Color(0xFF3A3A3A),
    label = Color(0xFF6B6B6B),
)

/** 互换：纯白底 + 黑色数字，各灰阶同步反相。 */
val LightClockColors = ClockColors(
    background = Color(0xFFFFFFFF),
    digits = Color(0xFF000000),
    dimmed = Color(0xFFCCCCCC),
    debugLine = Color(0xFFC0C0C0),
    label = Color(0xFF909090),
)

/** 当前配色，由 ClockScreen 在根节点提供，子组件直接取用。 */
val LocalClockColors = staticCompositionLocalOf { DarkClockColors }
