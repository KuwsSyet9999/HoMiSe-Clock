package com.homise.clock.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

/**
 * 时钟主题：当前为纯色方案（纯黑底 + 纯白字）。
 * 固定深色，因为时钟多在夜间常亮使用。
 */
private val ClockColors = darkColorScheme(
    background = ClockBackground,
    surface = ClockBackground,
    onBackground = ClockOnBackground,
    onSurface = ClockOnBackground,
    primary = ClockOnBackground,
)

@Composable
fun HoMiSeTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = ClockColors,
        content = content,
    )
}
