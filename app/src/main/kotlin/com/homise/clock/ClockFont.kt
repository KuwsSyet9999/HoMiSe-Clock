package com.homise.clock

import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily

/**
 * 数码管字体的两个维度，滑屏手势各控制一个：
 *
 *   - **自右向左滑**：循环切换 [DsegFamily]（7 Classic → 7 Classic Mini → 7 Modern →
 *     7 Modern Mini → 14 Classic → 14 Classic Mini → 14 Modern → 14 Modern Mini）；
 *   - **自下向上滑**：循环切换 [DsegStyle]（Light → Light Italic → Regular → Italic →
 *     Bold → Bold Italic）。
 *
 * 两个维度正交，共 8 × 6 = 48 种组合。
 *
 * 七段已换成从 DSEG7 派生的 **HSSeg 7**（改过 `R/r` 段位、补了 `colon`/`period`），
 * 资源名 `hseg_7_*`；十四段仍是未修改的 DSEG 原版，资源名 `hseg_16_*`。
 * 类名沿用 `Dseg*` 是为了不动已持久化的枚举名（偏好里存的是 `Classic7` 这类名字）。
 *
 * @param ghostDigit **全亮字形**：该族中点亮全部段的字符，用作灰色「熄灭段」底数。
 *   HSSeg 7 是七段字体，全亮的是 `8`；DSEG14 是十四段字体，全亮的是 `~`
 *   —— 在 14 段里 `8` 只点亮其中 8 段，并非全亮，用它当底数会缺段。
 */
enum class DsegFamily(
    val label: String,
    val ghostDigit: Char,
    /** 段数：7 或 14。用于拼装完整字体名（横屏过渡提示用）。 */
    val series: Int,
    /** 变体名：Classic / Classic Mini / Modern / Modern Mini。 */
    val variant: String,
) {
    Classic7("7 Classic", '8', 7, "Classic"),
    ClassicMini7("7 Classic Mini", '8', 7, "Classic Mini"),
    Modern7("7 Modern", '8', 7, "Modern"),
    ModernMini7("7 Modern Mini", '8', 7, "Modern Mini"),
    Classic14("14 Classic", '~', 14, "Classic"),
    ClassicMini14("14 Classic Mini", '~', 14, "Classic Mini"),
    Modern14("14 Modern", '~', 14, "Modern"),
    ModernMini14("14 Modern Mini", '~', 14, "Modern Mini"),
}

enum class DsegStyle(val label: String) {
    Light("Light"),
    LightItalic("Light Italic"),
    Regular("Regular"),
    Italic("Italic"),
    Bold("Bold"),
    BoldItalic("Bold Italic"),
}

/**
 * 完整字体名，用于横屏切换字体时的过渡提示。
 *
 * 取**字体内部真实名称**，而不是资源名：
 *   - 七段是 HSSeg 派生字体，家族名为 `HSSeg 7 <变体>`；
 *   - 十四段尚未 HSSeg 化，内部仍是 `HSEG16 <变体>`。
 *
 * 长度都不超过 `INFO_LONGEST_NAME`，故提示行字号仍按那一条定格即可。
 */
fun DsegFamily.fullFontName(style: DsegStyle, mono: Boolean = false): String =
    if (series == 7) {
        // 七段没有等宽字形，Mono 不参与
        "HSEG7 $variant ${style.label}"
    } else {
        // 命名顺序按 OpenType 惯例：族名 宽度变体 字重 倾斜。
        // Mono 是宽度变体，因此插在 Modern 之后、Bold 之前
        //（对应 Roboto Condensed Bold Italic 这类写法）。
        "HSEG16 $variant" + (if (mono) " Mono" else "") + " ${style.label}"
    }

/** 默认字体：与首版一致（7 Classic Regular）。 */
val DefaultDsegFamily = DsegFamily.Classic7
val DefaultDsegStyle = DsegStyle.Regular

/**
 * 48 个「族 × 样式」组合到字体资源的映射。
 *
 * 必须逐一静态引用 `R.font.*`：Android 的资源 id 不能用字符串拼出来（`R` 字段不是可反射的
 * 常规字段），因此这里显式列全。好处是任何遗漏都会在编译期暴露。
 */
private val FONT_RESOURCES: Map<Pair<DsegFamily, DsegStyle>, Int> = mapOf(
    // ---- HSSeg 7 Classic ----
    (DsegFamily.Classic7 to DsegStyle.Light) to R.font.hseg_7_classic_light,
    (DsegFamily.Classic7 to DsegStyle.LightItalic) to R.font.hseg_7_classic_light_italic,
    (DsegFamily.Classic7 to DsegStyle.Regular) to R.font.hseg_7_classic_regular,
    (DsegFamily.Classic7 to DsegStyle.Italic) to R.font.hseg_7_classic_italic,
    (DsegFamily.Classic7 to DsegStyle.Bold) to R.font.hseg_7_classic_bold,
    (DsegFamily.Classic7 to DsegStyle.BoldItalic) to R.font.hseg_7_classic_bold_italic,
    // ---- HSSeg 7 Classic Mini ----
    (DsegFamily.ClassicMini7 to DsegStyle.Light) to R.font.hseg_7_classic_mini_light,
    (DsegFamily.ClassicMini7 to DsegStyle.LightItalic) to R.font.hseg_7_classic_mini_light_italic,
    (DsegFamily.ClassicMini7 to DsegStyle.Regular) to R.font.hseg_7_classic_mini_regular,
    (DsegFamily.ClassicMini7 to DsegStyle.Italic) to R.font.hseg_7_classic_mini_italic,
    (DsegFamily.ClassicMini7 to DsegStyle.Bold) to R.font.hseg_7_classic_mini_bold,
    (DsegFamily.ClassicMini7 to DsegStyle.BoldItalic) to R.font.hseg_7_classic_mini_bold_italic,
    // ---- HSSeg 7 Modern ----
    (DsegFamily.Modern7 to DsegStyle.Light) to R.font.hseg_7_modern_light,
    (DsegFamily.Modern7 to DsegStyle.LightItalic) to R.font.hseg_7_modern_light_italic,
    (DsegFamily.Modern7 to DsegStyle.Regular) to R.font.hseg_7_modern_regular,
    (DsegFamily.Modern7 to DsegStyle.Italic) to R.font.hseg_7_modern_italic,
    (DsegFamily.Modern7 to DsegStyle.Bold) to R.font.hseg_7_modern_bold,
    (DsegFamily.Modern7 to DsegStyle.BoldItalic) to R.font.hseg_7_modern_bold_italic,
    // ---- HSSeg 7 Modern Mini ----
    (DsegFamily.ModernMini7 to DsegStyle.Light) to R.font.hseg_7_modern_mini_light,
    (DsegFamily.ModernMini7 to DsegStyle.LightItalic) to R.font.hseg_7_modern_mini_light_italic,
    (DsegFamily.ModernMini7 to DsegStyle.Regular) to R.font.hseg_7_modern_mini_regular,
    (DsegFamily.ModernMini7 to DsegStyle.Italic) to R.font.hseg_7_modern_mini_italic,
    (DsegFamily.ModernMini7 to DsegStyle.Bold) to R.font.hseg_7_modern_mini_bold,
    (DsegFamily.ModernMini7 to DsegStyle.BoldItalic) to R.font.hseg_7_modern_mini_bold_italic,
    // ---- DSEG14 Classic ----
    (DsegFamily.Classic14 to DsegStyle.Light) to R.font.hseg_16_classic_light,
    (DsegFamily.Classic14 to DsegStyle.LightItalic) to R.font.hseg_16_classic_light_italic,
    (DsegFamily.Classic14 to DsegStyle.Regular) to R.font.hseg_16_classic_regular,
    (DsegFamily.Classic14 to DsegStyle.Italic) to R.font.hseg_16_classic_italic,
    (DsegFamily.Classic14 to DsegStyle.Bold) to R.font.hseg_16_classic_bold,
    (DsegFamily.Classic14 to DsegStyle.BoldItalic) to R.font.hseg_16_classic_bold_italic,
    // ---- DSEG14 Classic Mini ----
    (DsegFamily.ClassicMini14 to DsegStyle.Light) to R.font.hseg_16_classic_mini_light,
    (DsegFamily.ClassicMini14 to DsegStyle.LightItalic) to R.font.hseg_16_classic_mini_light_italic,
    (DsegFamily.ClassicMini14 to DsegStyle.Regular) to R.font.hseg_16_classic_mini_regular,
    (DsegFamily.ClassicMini14 to DsegStyle.Italic) to R.font.hseg_16_classic_mini_italic,
    (DsegFamily.ClassicMini14 to DsegStyle.Bold) to R.font.hseg_16_classic_mini_bold,
    (DsegFamily.ClassicMini14 to DsegStyle.BoldItalic) to R.font.hseg_16_classic_mini_bold_italic,
    // ---- DSEG14 Modern ----
    (DsegFamily.Modern14 to DsegStyle.Light) to R.font.hseg_16_modern_light,
    (DsegFamily.Modern14 to DsegStyle.LightItalic) to R.font.hseg_16_modern_light_italic,
    (DsegFamily.Modern14 to DsegStyle.Regular) to R.font.hseg_16_modern_regular,
    (DsegFamily.Modern14 to DsegStyle.Italic) to R.font.hseg_16_modern_italic,
    (DsegFamily.Modern14 to DsegStyle.Bold) to R.font.hseg_16_modern_bold,
    (DsegFamily.Modern14 to DsegStyle.BoldItalic) to R.font.hseg_16_modern_bold_italic,
    // ---- DSEG14 Modern Mini ----
    (DsegFamily.ModernMini14 to DsegStyle.Light) to R.font.hseg_16_modern_mini_light,
    (DsegFamily.ModernMini14 to DsegStyle.LightItalic) to R.font.hseg_16_modern_mini_light_italic,
    (DsegFamily.ModernMini14 to DsegStyle.Regular) to R.font.hseg_16_modern_mini_regular,
    (DsegFamily.ModernMini14 to DsegStyle.Italic) to R.font.hseg_16_modern_mini_italic,
    (DsegFamily.ModernMini14 to DsegStyle.Bold) to R.font.hseg_16_modern_mini_bold,
    (DsegFamily.ModernMini14 to DsegStyle.BoldItalic) to R.font.hseg_16_modern_mini_bold_italic,
)

/** 取「族 × 样式」对应的字体族；组合意外缺失时回退到默认字体。 */
fun dsegFontFamily(family: DsegFamily, style: DsegStyle): FontFamily =
    FontFamily(Font(FONT_RESOURCES[family to style] ?: R.font.hseg_7_classic_regular))

/** 循环切换到下一个族（自右向左滑）。 */
fun DsegFamily.next(): DsegFamily =
    DsegFamily.entries[(ordinal + 1) % DsegFamily.entries.size]

/** 反向循环切换到上一个族（自左向右滑）。 */
fun DsegFamily.previous(): DsegFamily =
    DsegFamily.entries[(ordinal - 1 + DsegFamily.entries.size) % DsegFamily.entries.size]

/** 循环切换到下一个样式（自下向上滑）。 */
fun DsegStyle.next(): DsegStyle =
    DsegStyle.entries[(ordinal + 1) % DsegStyle.entries.size]

/** 反向循环切换到上一个样式（自上向下滑）。 */
fun DsegStyle.previous(): DsegStyle =
    DsegStyle.entries[(ordinal - 1 + DsegStyle.entries.size) % DsegStyle.entries.size]

/**
 * 当前使用的时钟字体，由 ClockScreen 在根节点注入，数字与冒号组件直接取用。
 * 默认值与首版一致（7 Classic Regular）。
 */
val LocalClockFont = staticCompositionLocalOf {
    FontFamily(Font(R.font.hseg_7_classic_regular))
}
