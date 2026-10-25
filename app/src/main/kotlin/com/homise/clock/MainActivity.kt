package com.homise.clock

import android.os.Build
import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import com.homise.clock.ui.theme.HoMiSeTheme
import kotlinx.coroutines.delay
import java.time.LocalDateTime

class MainActivity : ComponentActivity() {

    /**
     * 待应用的图标变体序号。前台只登记，真正的切换放到 [onStop] 执行。
     */
    private var pendingIconVariant: Int? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        applyWindowSettings()
        val prefs = ClockPreferences(this)
        // 亮度不做继承：每次启动都回到默认的最大亮度。
        applyBrightness(max = true)
        // 恢复上次未落实的图标切换。
        // 「强制停止」不会回调 onStop，落盘值就会留在这里；下次正常退出时补做。
        // 注意不能在这里直接切：前台禁用当前别名会结束本任务。
        val savedPendingIcon = ClockPreferences(this).pendingIconVariant
        if (savedPendingIcon >= 0) pendingIconVariant = savedPendingIcon
        applyImmersiveMode()

        // 调试包可用 intent extra 强制某一种布局，便于在固定方向的设备/模拟器上截图核对：
        //   adb shell am start -n <pkg>/com.homise.clock.MainActivity --ez force_landscape false
        // 正式包忽略该参数，始终跟随真实屏幕方向。
        val forcedLayout: Boolean? = if (BuildConfig.DEBUG) {
            when {
                intent?.hasExtra(EXTRA_FORCE_LANDSCAPE) == true ->
                    intent.getBooleanExtra(EXTRA_FORCE_LANDSCAPE, false)
                else -> null
            }
        } else {
            null
        }

        setContent {
            HoMiSeTheme {
                // 配色与字体持久化，重启保持；亮度**不做继承**，每次启动恒为最大亮度，
                // 长按切换只在本次运行期间有效，因此不写入偏好。
                var colorsInverted by remember { mutableStateOf(prefs.colorsInverted) }
                var maxBrightness by remember { mutableStateOf(true) }
                var fontFamily by remember { mutableStateOf(prefs.fontFamily) }
                var fontStyle by remember { mutableStateOf(prefs.fontStyle) }
                var monoLowercase by remember { mutableStateOf(prefs.monoLowercase) }
                var ghostVisible by remember { mutableStateOf(prefs.ghostVisible) }

                // 亮度状态变化时立刻作用到窗口（BRIGHTNESS_OVERRIDE_NONE 表示跟随系统）
                LaunchedEffect(maxBrightness) { applyBrightness(maxBrightness) }

                // 桌面图标随字体、配色与灰底切换：192 个变体各有自己的 activity-alias。
                // 这里**只登记**目标变体，真正启用/禁用放到 onStop 执行——
                // 见 onStop 的说明（前台切换会结束当前任务，表现为闪退）。
                var iconReport by remember { mutableStateOf<ClockIconVariants.Report?>(null) }
                LaunchedEffect(fontFamily, fontStyle, colorsInverted, ghostVisible) {
                    val want = ClockIconVariants.indexOf(
                        fontFamily, fontStyle, colorsInverted, ghostVisible,
                    )
                    pendingIconVariant = want
                    // 落盘：强制停止不会回调 onStop，内存值会丢
                    prefs.pendingIconVariant = want
                    iconReport = ClockIconVariants.report(this@MainActivity, want)
                }

                // 时钟要真正全屏：不套 Scaffold、不消费 WindowInsets，
                // 让内容延伸到状态栏/导航栏区域（此前 Scaffold 的 innerPadding
                // 把内容限制在系统栏以内，顶部因而留下一条不可绘制黑边）。
                ClockRoute(
                    modifier = Modifier.fillMaxSize(),
                    forceLandscape = forcedLayout,
                    // 调试包：显示屏幕参数与留白基准井字线；正式包两者都不显示
                    showDiagnostics = BuildConfig.DEBUG,
                    showDebugMarks = BuildConfig.DEBUG,
                    colorsInverted = colorsInverted,
                    onToggleColors = {
                        colorsInverted = !colorsInverted
                        prefs.colorsInverted = colorsInverted
                    },
                    onToggleBrightness = {
                        // 仅切换本次运行的状态，不落盘 —— 下次启动仍为最大亮度
                        maxBrightness = !maxBrightness
                    },
                    fontFamily = fontFamily,
                    fontStyle = fontStyle,
                    onCycleFamily = {
                        fontFamily = fontFamily.next()
                        prefs.fontFamily = fontFamily
                    },
                    onCycleFamilyReverse = {
                        fontFamily = fontFamily.previous()
                        prefs.fontFamily = fontFamily
                    },
                    onCycleStyle = {
                        fontStyle = fontStyle.next()
                        prefs.fontStyle = fontStyle
                    },
                    onCycleStyleReverse = {
                        fontStyle = fontStyle.previous()
                        prefs.fontStyle = fontStyle
                    },
                    ghostVisible = ghostVisible,
                    onToggleGhost = {
                        ghostVisible = !ghostVisible
                        prefs.ghostVisible = ghostVisible
                    },
                    onResetDefaults = {
                        // 恢复出厂：清空偏好并把内存状态一并归位
                        prefs.resetAll()
                        colorsInverted = false
                        ghostVisible = true
                        fontFamily = DefaultDsegFamily
                        fontStyle = DefaultDsegStyle
                        monoLowercase = false
                        // 常驻块的状态在 ClockInfoOverlay 内部，清空偏好后
                        // 下次启动即回到默认（电量常驻）
                        pendingIconVariant = null
                    },
                    monoLowercase = monoLowercase,
                    onToggleMono = {
                        monoLowercase = !monoLowercase
                        prefs.monoLowercase = monoLowercase
                    },
                    iconReport = iconReport,
                )
            }
        }
    }

    private companion object {
        const val EXTRA_FORCE_LANDSCAPE = "force_landscape"
    }

    /**
     * 窗口级显示设置。时钟要长时间、远距离也能看清，因此这里统一处理：
     *
     * 1. **允许绘制到挖孔区域**：不设置时 Android 9~14 会把窗口限制在挖孔安全区外，
     *    屏幕上留下一条无法绘制的黑边。安全区的**避让**另由 ClockScreen 读取
     *    `WindowInsets.displayCutout` 处理，两者互不冲突。
     * 2. **阻止息屏**：`FLAG_KEEP_SCREEN_ON` 随窗口生命周期生效，无需 WakeLock，
     *    因此清单中也不再需要 WAKE_LOCK 权限。
     *
     * 亮度不在这里固定，改由 [applyBrightness] 按用户偏好动态控制。
     */
    private fun applyWindowSettings() {
        window.attributes = window.attributes.apply {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                @Suppress("DEPRECATION")
                layoutInDisplayCutoutMode =
                    WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
            }
        }
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
    }

    /**
     * 按偏好设置本窗口亮度。
     *
     * `screenBrightness` 只覆盖**本窗口**：不改动系统设置，也不需要任何权限，
     * 应用退出后自动恢复系统亮度。
     *   - [max] = true  → `BRIGHTNESS_OVERRIDE_FULL`（1.0f，最大亮度）
     *   - [max] = false → `BRIGHTNESS_OVERRIDE_NONE`（-1.0f，跟随系统亮度）
     */
    private fun applyBrightness(max: Boolean) {
        window.attributes = window.attributes.apply {
            screenBrightness = if (max) {
                WindowManager.LayoutParams.BRIGHTNESS_OVERRIDE_FULL
            } else {
                WindowManager.LayoutParams.BRIGHTNESS_OVERRIDE_NONE
            }
        }
    }

    /**
     * 沉浸式全屏：隐藏状态栏与导航栏，让时钟独占整屏。
     *
     * 隐藏的只是**系统栏**（图标/手势条）；挖孔属于物理遮挡，不受影响，
     * 仍由 ClockScreen 读取 `WindowInsets.displayCutout` 单独避让。
     *
     * 采用 BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE：用户从边缘滑动可临时唤出系统栏，
     * 不必退出应用即可操作。
     */
    private fun applyImmersiveMode() {
        WindowInsetsControllerCompat(window, window.decorView).apply {
            hide(WindowInsetsCompat.Type.systemBars())
            systemBarsBehavior =
                WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        }
    }

    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        // 切换应用、旋转屏幕或用户滑动唤出系统栏后，系统栏可能重新出现；获得焦点时重新隐藏。
        if (hasFocus) applyImmersiveMode()
    }

    /**
     * 在这里切换桌面图标，而不是用户操作的那一刻。
     *
     * 原因：禁用**当前正在承载本任务的 launcher 别名**会让系统结束该任务，
     * 表现出来就是一次闪退。退到后台时用户看不到这个过程，等回到桌面，
     * 图标已经换成与选择一致的那一个。
     *
     * 代价是图标不会在切换的瞬间变化，需要离开应用才生效——这是 Android 的机制使然。
     */
    override fun onStop() {
        super.onStop()
        pendingIconVariant?.let { variant ->
            ClockIconVariants.apply(applicationContext, variant)
            pendingIconVariant = null
            // 已落实，清除落盘记录
            ClockPreferences(applicationContext).pendingIconVariant = -1
        }
    }
}

/**
 * 时钟的数据入口：每 100ms 刷新一次状态。
 *
 * 刷新对齐到 100ms 边界以避免累计漂移；时间文本每秒才变化，
 * 但冒号需要 500ms 半周期（完整周期 1 秒），所以按更细的粒度更新。
 */
@Composable
fun ClockRoute(
    modifier: Modifier = Modifier,
    timeFormat: TimeFormat = TimeFormat.Default,
    forceLandscape: Boolean? = null,
    showDiagnostics: Boolean = false,
    showDebugMarks: Boolean = false,
    colorsInverted: Boolean = false,
    onToggleColors: () -> Unit = {},
    onToggleBrightness: () -> Unit = {},
    fontFamily: DsegFamily = DefaultDsegFamily,
    fontStyle: DsegStyle = DefaultDsegStyle,
    onCycleFamily: () -> Unit = {},
    onCycleFamilyReverse: () -> Unit = {},
    onCycleStyle: () -> Unit = {},
    onCycleStyleReverse: () -> Unit = {},
    ghostVisible: Boolean = true,
    onToggleGhost: () -> Unit = {},
    onResetDefaults: () -> Unit = {},
    monoLowercase: Boolean = false,
    onToggleMono: () -> Unit = {},
    iconReport: ClockIconVariants.Report? = null,
) {
    var time by remember { mutableStateOf(currentClockTime(timeFormat)) }

    LaunchedEffect(timeFormat) {
        while (true) {
            val now = LocalDateTime.now()
            // 对齐到下一个 100ms 边界，使冒号闪烁与系统时钟同步
            val nanosToNextTick = 100_000_000L - (now.nano % 100_000_000L)
            delay(nanosToNextTick / 1_000_000L)
            time = currentClockTime(timeFormat)
        }
    }

    ClockScreen(
        time = time,
        modifier = modifier,
        forceLandscape = forceLandscape,
        showDiagnostics = showDiagnostics,
        showDebugMarks = showDebugMarks,
        colorsInverted = colorsInverted,
        onToggleColors = onToggleColors,
        onToggleBrightness = onToggleBrightness,
        fontFamily = fontFamily,
        fontStyle = fontStyle,
        onCycleFamily = onCycleFamily,
        onCycleFamilyReverse = onCycleFamilyReverse,
        onCycleStyle = onCycleStyle,
        onCycleStyleReverse = onCycleStyleReverse,
        ghostVisible = ghostVisible,
        onToggleGhost = onToggleGhost,
        onResetDefaults = onResetDefaults,
        monoLowercase = monoLowercase,
        onToggleMono = onToggleMono,
        iconReport = iconReport,
    )
}

/** 读取系统当前时间并格式化为界面模型。 */
private fun currentClockTime(format: TimeFormat): ClockTime {
    val now = LocalDateTime.now()
    return formatClockTime(
        hour = now.hour,
        minute = now.minute,
        second = now.second,
        millis = now.nano / 1_000_000,
        format = format,
    )
}
