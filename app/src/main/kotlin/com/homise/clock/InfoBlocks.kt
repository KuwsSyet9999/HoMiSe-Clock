package com.homise.clock

/**
 * 过渡提示中四块信息的标识。
 *
 * 用稳定的字符串作为身份，而不是序号或枚举 ordinal —— 常驻状态会写入
 * SharedPreferences，若用序号存储，将来增删信息块就会把旧值错配到别的块上。
 */
const val INFO_BLOCK_ISO = "iso"
const val INFO_BLOCK_NAME = "name"
const val INFO_BLOCK_VERSION = "version"
const val INFO_BLOCK_BATTERY = "battery"

/**
 * 默认为「常驻」的信息块。
 *
 * 只有电量默认常驻：它是持续变化、需要随时可见的状态量；
 * 其余三块是"这次切换/这个版本是什么"的瞬时说明，默认随提示淡出更合适。
 * 用户仍可单击任一块改变其常驻状态，改动会被记住。
 */
val DEFAULT_PINNED_INFO_BLOCKS: Set<String> = setOf(INFO_BLOCK_BATTERY)

/** 等宽小写字形的私有区起始码位（与字体约定：U+E000 = `a`，U+E019 = `z`）。 */
const val MONO_LOWER_BASE = 0xE000

/**
 * 等宽模式下把 `a`–`z` 映射到字体的私有区等宽字形。
 *
 * 字体里小写字母的笔迹窄、但 advance 与数字同为 816，导致字距过宽（`i` 的空白占比 89%）。
 * 字体另在 U+E000~U+E019 提供了一套 advance 为 408 的等宽字形，这里只做字符替换，
 * **不改动字体本身**，也不影响除小写字母之外的任何字符。
 *
 * @param enabled 关闭时原样返回，便于切换时立即回到原字体排版
 */
fun applyMonoLowercase(text: String, enabled: Boolean): String {
    if (!enabled) return text
    var hasLower = false
    for (c in text) {
        if (c in 'a'..'z') { hasLower = true; break }
    }
    if (!hasLower) return text

    return buildString(text.length) {
        for (c in text) {
            append(if (c in 'a'..'z') (MONO_LOWER_BASE + (c - 'a')).toChar() else c)
        }
    }
}

/**
 * 显示前把空格换成下划线。
 *
 * 数字字体的 space 字形没有笔迹、宽度也不可靠，空格处会留下无法核对宽度的空白；
 * 换成 `_` 后既有可见笔迹、也有确定的 advance，配合 `~` 铺底才能看清对齐。
 */
fun displayText(text: String): String =
    if (' ' !in text) text else text.replace(' ', '_')
