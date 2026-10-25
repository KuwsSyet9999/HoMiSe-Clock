package com.homise.clock

import java.util.Locale

/** 时钟显示的小时制设置。 */
enum class TimeFormat {
    /** 24 小时制，如 14:05 */
    HOUR_24,

    /** 12 小时制，如 02:05 PM */
    HOUR_12,
    ;

    companion object {
        val Default: TimeFormat = HOUR_24
    }
}

/** 一帧要渲染的全部时间字段，避免在界面里重复做字符串格式化。 */
data class ClockTime(
    /** 小时，固定两位，如 "14" 或 "02" */
    val hourText: String,
    /** 分钟，固定两位 */
    val minuteText: String,
    /** 秒，固定两位 */
    val secondText: String,
    /** 12 小时制下的 "AM"/"PM"；24 小时制为空串 */
    val meridiem: String,
    /** 0-59，用于时间文本刷新 */
    val secondOfMinute: Int,
    /** 0-999，用于冒号闪烁节奏 */
    val millisOfSecond: Int,
) {
    /**
     * 冒号是否点亮。
     *
     * 以 500ms 为半周期，即亮/灭各 500ms，**完整周期 1 秒**。
     */
    val colonVisible: Boolean
        get() = millisOfSecond < 500
}

/**
 * 把当前时刻格式化为 [ClockTime]。
 *
 * 小时制跟随 [format]；数字补零使用 [Locale.getDefault]，避免 lint 报隐式区域警告。
 */
fun formatClockTime(
    hour: Int,
    minute: Int,
    second: Int,
    millis: Int = 0,
    format: TimeFormat = TimeFormat.Default,
): ClockTime {
    val locale = Locale.getDefault()
    val is24Hour = format == TimeFormat.HOUR_24
    val displayHour = if (is24Hour) hour else if (hour % 12 == 0) 12 else hour % 12
    val meridiem = if (is24Hour) "" else if (hour < 12) "AM" else "PM"

    return ClockTime(
        hourText = String.format(locale, "%02d", displayHour),
        minuteText = String.format(locale, "%02d", minute),
        secondText = String.format(locale, "%02d", second),
        meridiem = meridiem,
        secondOfMinute = second,
        millisOfSecond = millis,
    )
}

/**
 * 日期文案，如 "2026-10-16 周五"。
 * 当前界面不显示日期，保留此函数以便后续需要时直接启用。
 */
fun formatDateText(year: Int, month: Int, dayOfMonth: Int, dayOfWeek: Int): String {
    val locale = Locale.getDefault()
    return String.format(locale, "%04d-%02d-%02d %s", year, month, dayOfMonth, weekdayLabel(dayOfWeek))
}

/** 星期文案。java.time 的 DayOfWeek 取值 1=周一 … 7=周日。 */
fun weekdayLabel(dayOfWeek: Int): String = when (dayOfWeek) {
    1 -> "周一"
    2 -> "周二"
    3 -> "周三"
    4 -> "周四"
    5 -> "周五"
    6 -> "周六"
    7 -> "周日"
    else -> ""
}
