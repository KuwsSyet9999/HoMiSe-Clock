package com.homise.clock

import android.content.Context
import android.content.Intent
import android.content.res.Configuration
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.asPaddingValues
import androidx.compose.foundation.layout.displayCutout
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.systemBars
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.boundsInParent
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.text.TextMeasurer
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.text.style.LineHeightStyle
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.Density
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.homise.clock.ui.theme.HoMiSeTheme
import kotlinx.coroutines.delay
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter
import kotlin.math.abs
import androidx.compose.ui.text.drawText
import androidx.compose.ui.text.PlatformTextStyle
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.TextLayoutResult
import androidx.compose.ui.layout.boundsInRoot
import androidx.compose.ui.graphics.Shadow
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.layout.widthIn
import androidx.compose.ui.text.font.FontWeight

/**
 * 数码管时钟界面。
 *
 * 布局规则：
 *   - 横屏：`时:分:秒` 排成一行，字号由左右两侧各一个冒号宽度的留白决定；
 *   - 竖屏：时、分、秒各占一行，字号由上下两侧各一个冒号宽度的留白决定；
 *   - 四周留白与竖屏行间距都等于**一个冒号的笔迹宽度**；
 *   - 只显示时、分、秒，不显示日期。
 *
 * 手势：
 *   - **双击**：背景色与数字色互换（黑底白字 ⇄ 白底黑字）；
 *   - **长按**：取消 / 恢复最大亮度。
 * 两个状态都由调用方持久化，重启后保持。
 *
 * @param colorsInverted true 时使用反相配色（白底黑字）
 * @param onToggleColors 双击回调
 * @param onToggleBrightness 长按回调
 * @param fontFamily 当前数码管字体族（横向滑动切换）
 * @param fontStyle 当前字体的字重/斜体样式（纵向滑动切换）
 * @param onCycleFamily 自右向左滑：字体族正向循环
 * @param onCycleFamilyReverse 自左向右滑：字体族反向循环
 * @param onCycleStyle 自下向上滑：样式正向循环
 * @param onCycleStyleReverse 自上向下滑：样式反向循环
 * @param showDiagnostics 显示屏幕参数与字号，仅供调试
 * @param showDebugMarks 显示留白基准井字线，仅供调试
 * @param forceLandscape 非空时强制指定布局，仅供调试包使用
 */
@Composable
fun ClockScreen(
    time: ClockTime,
    modifier: Modifier = Modifier,
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
    /** 是否显示灰底（双击时钟数字区切换；默认显示） */
    ghostVisible: Boolean = true,
    /** 切换灰底的回调 */
    onToggleGhost: () -> Unit = {},
    /** 恢复默认设置（长按版本号的面板里触发） */
    onResetDefaults: () -> Unit = {},
    /** 是否启用等宽小写（双击字体名块切换） */
    monoLowercase: Boolean = false,
    /** 切换等宽小写的回调 */
    onToggleMono: () -> Unit = {},
    /** 图标切换诊断快照（want/before/after/active），仅用于诊断显示 */
    iconReport: ClockIconVariants.Report? = null,
) {
    // 过渡提示的播放控制：
    //   停留期内单击 → 延长停留；淡入／淡出期间单击 → 忽略；已结束后单击 → 重播。
    var infoPhase by remember { mutableStateOf(InfoPhase.Hidden) }
    // 长按版本号打开的应用信息面板
    var showAbout by remember { mutableStateOf(false) }
    var infoRestart by remember { mutableStateOf(0) }
    var infoExtend by remember { mutableStateOf(0) }
    val isLandscape = forceLandscape
        ?: (LocalConfiguration.current.orientation == Configuration.ORIENTATION_LANDSCAPE)
    val colors = if (colorsInverted) LightClockColors else DarkClockColors
    // 时钟数字区的点击矩形（根坐标系，px）：用于区分"双击数字"与"双击背景"
    var clockDigitsRect by remember { mutableStateOf<Rect?>(null) }
    // 诊断：双击次数与最后一次落点判定
    var dblTapCount by remember { mutableStateOf(0) }
    var dblTapLast by remember { mutableStateOf("-") }
    val textColor = colors.digits
    val clockFont = dsegFontFamily(fontFamily, fontStyle)
    val swipeThresholdPx = with(LocalDensity.current) { SWIPE_THRESHOLD.toPx() }

    // 把配色与字体注入 CompositionLocal，供下方各子组件取用：
    //   - 配色不注入的话，子组件会读到默认深色配色，白底模式下熄灭段与标签灰无法辨认；
    //   - 字体不注入的话，切换字体后熄灭段仍会用旧字体，与数字错位。
    CompositionLocalProvider(
        LocalClockColors provides colors,
        LocalClockFont provides clockFont,
    ) {
    BoxWithConstraints(
        modifier = modifier
            .fillMaxSize()
            .background(colors.background)
            // 点击类手势：双击换配色，长按切换最大亮度。
            .pointerInput(Unit) {
                detectTapGestures(
                    // 单击重播横屏过渡提示（ISO 时间／字体名／版本号）
                    onTap = {
                        when (infoPhase) {
                            InfoPhase.Holding -> infoExtend++   // 停留中：延长停留
                            InfoPhase.Hidden -> infoRestart++   // 已结束：重播一轮
                            else -> Unit                        // 淡入／淡出中：不响应
                        }
                    },
                    onDoubleTap = { at ->
                        // 双击落在时钟数字区 -> 切换灰底；落在背景 -> 互换配色。
                        // 放在根层统一判断，避免子级手势被父级吞掉。
                        val r = clockDigitsRect
                        val inside = r != null && r.contains(at)
                        dblTapCount++
                        dblTapLast = if (inside) "clock->ghost" else "bg->colors"
                        if (inside) onToggleGhost() else onToggleColors()
                    },
                    onLongPress = { onToggleBrightness() },
                )
            }
            // 滑动手势：自右向左切字体族、自下向上切字重/斜体样式。
            // 与点击手势分处两个 pointerInput，互不吞掉对方的事件。
            .pointerInput(Unit) {
                var total = Offset.Zero
                detectDragGestures(
                    onDragStart = { total = Offset.Zero },
                    onDrag = { change, dragAmount ->
                        total += dragAmount
                        change.consume()
                    },
                    onDragEnd = {
                        // 以位移较大的那个轴判定方向，避免斜向滑动误触发；
                        // 同一条轴上正反两个方向分别正向 / 反向循环。
                        if (abs(total.x) > abs(total.y)) {
                            when {
                                // 横向：自右向左为 x 负（正向），自左向右为 x 正（反向）
                                total.x < -swipeThresholdPx -> onCycleFamily()
                                total.x > swipeThresholdPx -> onCycleFamilyReverse()
                            }
                        } else {
                            when {
                                // 纵向：自下向上为 y 负（正向），自上向下为 y 正（反向）
                                total.y < -swipeThresholdPx -> onCycleStyle()
                                total.y > swipeThresholdPx -> onCycleStyleReverse()
                            }
                        }
                    },
                )
            },
        contentAlignment = Alignment.Center,
    ) {
        // 实测真实渲染比例：字体表的 hmtx advance 与 Android 实际排版宽度并不一致，
        // 早先按字体表推算导致横屏内容实际超宽、秒的两位被压在同一位置。
        // 这里在参考字号下直接测量，得到与渲染完全一致的比值。
        // 信息块常驻状态（跨重启保持）。用 remember 持有实例，避免每次重组新建。
        val context = LocalContext.current
        val prefs = remember { ClockPreferences(context) }
        var pinnedBlocks by remember { mutableStateOf(prefs.pinnedInfoBlocks) }

        // 电量百分比：广播注册即回传当前值，横屏时显示在左下角
        val batteryPercent = rememberBatteryPercent()

        val measurer = rememberTextMeasurer()
        val probeDensity = LocalDensity.current
        val measured = remember(measurer, probeDensity, clockFont) {
            val probeSp = 100f
            val emPx = probeSp * probeDensity.density * probeDensity.fontScale
            // 必须用**当前字体**测量：各族度量差异很大（Mini 更窄、14 段更宽、
            // Light/Bold 笔迹粗细不同），沿用固定字体会让字号与留白全部算错。
            val style = TextStyle(
                fontFamily = clockFont,
                fontSize = probeSp.sp,
            )
            // 宽度按**实际组件划分**分别测量：横屏是 3 组数字 + 2 个冒号共 5 个独立 Text，
            // 各组件宽度之和会略大于整串一次测量值，按组件累加才能反映真实占用。
            ClockLayout.Metrics(
                digitRatio = measurer.measure("0", style).size.width / emPx,
                digitPairRatio = measurer.measure("00", style).size.width / emPx,
                colonRatio = measurer.measure(":", style).size.width / emPx,
                // 行框高度**不采用测量值**：TextMeasurer 返回的 height 是字体自然行高
                // （实测恒为 1.0em），不含 TextStyle.lineHeight 的扩展量，因此测不到真实
                // 行框高度。而渲染行高由 DigitText 显式设为 LINE_HEIGHT_RATIO，直接采用它。
                lineBoxRatio = ClockLayout.LINE_HEIGHT_RATIO,
            )
        }

        // 挖孔（刘海/打孔）避让。规则（需求方确认）：
        //   * 无挖孔的方向：数字**可见笔迹**距屏幕边缘 = 一个冒号笔迹宽；
        //   * 有挖孔的方向：数字可见笔迹距**挖孔边缘** = 半个冒号笔迹宽；
        //   * 挖孔高度不超过半个冒号宽时，该方向仍按一个冒号宽的边距处理
        //     —— 因为整个冒号宽的边距本来就把它覆盖了。
        // 三句可合成一条：`padding = max(0, 挖孔高度 − 半个冒号宽)`。
        //
        // padding 依赖字号、字号又依赖可用空间，因此迭代数轮收敛（3 轮即稳定）。
        // safeInset 随方向自动换边：竖屏是 top，横屏旋转后变成 left/right，无需分方向写。
        val cutoutPadding = WindowInsets.displayCutout.asPaddingValues()
        val layoutDirection = LocalLayoutDirection.current
        val cutTop = cutoutPadding.calculateTopPadding()
        val cutBottom = cutoutPadding.calculateBottomPadding()
        val cutLeft = cutoutPadding.calculateLeftPadding(layoutDirection)
        val cutRight = cutoutPadding.calculateRightPadding(layoutDirection)

        val halfColon = { fontSizeSp: Float ->
            (fontSizeSp * ClockLayout.HALF_COLON_INK_RATIO).dp
        }
        fun padsFor(fontSizeSp: Float) = listOf(
            (cutTop - halfColon(fontSizeSp)).coerceAtLeast(0.dp),
            (cutBottom - halfColon(fontSizeSp)).coerceAtLeast(0.dp),
            (cutLeft - halfColon(fontSizeSp)).coerceAtLeast(0.dp),
            (cutRight - halfColon(fontSizeSp)).coerceAtLeast(0.dp),
        )

        var pads = padsFor(0f)                       // 起点：按挖孔全额避让
        var layout = ClockLayout.compute(
            widthDp = (maxWidth - pads[2] - pads[3]).value,
            heightDp = (maxHeight - pads[0] - pads[1]).value,
            isLandscape = isLandscape,
            metrics = measured,
        )
        repeat(3) {
            pads = padsFor(layout.fontSizeSp)
            layout = ClockLayout.compute(
                widthDp = (maxWidth - pads[2] - pads[3]).value,
                heightDp = (maxHeight - pads[0] - pads[1]).value,
                isLandscape = isLandscape,
                metrics = measured,
            )
        }
        val padTop = pads[0]
        val padBottom = pads[1]
        val padLeft = pads[2]
        val padRight = pads[3]
        val usableWidth = (maxWidth - padLeft - padRight).coerceAtLeast(0.dp)
        val usableHeight = (maxHeight - padTop - padBottom).coerceAtLeast(0.dp)
        val canvasWidthDp = maxWidth.value
        val canvasHeightDp = maxHeight.value

        // ---- 调试用诊断状态 ----
        // 内容（三行字形）在可用区内的实际上下边界，单位 dp，原点为可用区左上角。
        // 与 usableHeight 相减即可判定是否越界。
        var contentTopDp by remember { mutableStateOf(-1f) }
        var contentBottomDp by remember { mutableStateOf(-1f) }
        // 竖屏一行文字的实际布局高度（px）。与固定行框对比，可判断字形是否溢出行框。
        var glyphLineHeightPx by remember { mutableStateOf(0) }

        // 系统栏 / 安全区诊断。
        // 平板（Android 12L+）底部常有**常驻任务栏**，它不属于 displayCutout，
        // 若可用高度按整块画布算，底部内容就会压在任务栏/手势条之下 —— 这正是竖屏下方越界的主因嫌疑。
        // 沉浸模式隐藏系统栏后这些 inset 往往仍会报值，因此必须实测而非假设为 0。
        val navBarPad = WindowInsets.navigationBars.asPaddingValues()
        val sysBarPad = WindowInsets.systemBars.asPaddingValues()
        val safePad = WindowInsets.safeDrawing.asPaddingValues()
        val navBottomDp = navBarPad.calculateBottomPadding().value
        val sysBottomDp = sysBarPad.calculateBottomPadding().value
        val safeBottomDp = safePad.calculateBottomPadding().value
        val safeLeftDp = safePad.calculateLeftPadding(layoutDirection).value
        val safeRightDp = safePad.calculateRightPadding(layoutDirection).value

        // 字号以 sp 计会随系统「字体大小」放大，而边距是 dp 不会跟着放大，
        // 两者比例就会失衡。这里抵消 fontScale，使实际渲染尺寸严格等于按屏幕算出的值。
        val fontScale = LocalDensity.current.fontScale.takeIf { it > 0f } ?: 1f
        val paddingRatio = (ClockLayout.COLON_INK_RATIO - ClockLayout.DIGIT_SIDE_INK_RATIO)
            .coerceAtLeast(0f)

        // 横屏字号**实测校正**。
        //
        // TextMeasurer 的宽度测量比实际排版约小 1.8%（多字符 Text 的字距未完全计入），
        // 按它算出的字号偏大：内容一旦超宽，Row 的 Arrangement.Center 会退化为左对齐，
        // 溢出量全部堆到右侧 —— 现象正是"左侧留白正常、右侧贴边"。
        //
        // 不要用"整体缩小安全系数"去掩盖：那会让数字整体变小、离留白线更远。
        // 这里改为渲染后实测内容宽度，按 (可用宽 / (实测比例 + 2×padding)) 反解字号并迭代，
        // 使内容**恰好顶到留白边界**；偏差小于 0.5% 即停止，避免反复重排。
        var landscapeSizeSp by remember(layout.fontSizeSp) { mutableStateOf(layout.fontSizeSp) }
        var landscapeWidthDp by remember { mutableStateOf(0f) }

        LaunchedEffect(landscapeWidthDp, isLandscape) {
            if (!isLandscape || landscapeWidthDp <= 0f || landscapeSizeSp <= 0f) return@LaunchedEffect
            val measuredRatio = landscapeWidthDp / landscapeSizeSp
            if (measuredRatio <= 0f) return@LaunchedEffect
            val target = usableWidth.value / (measuredRatio + 2f * paddingRatio)
            if (abs(target - landscapeSizeSp) / landscapeSizeSp > 0.005f) {
                landscapeSizeSp = target
            }
        }

        val usedFontSizeSp = if (isLandscape) landscapeSizeSp else layout.fontSizeSp
        val fontSize = (usedFontSizeSp / fontScale).sp
        val margin = (usedFontSizeSp * paddingRatio).dp
        val lineGap = layout.lineGapDp.dp

        // 时钟与版本号叠放；版本号与调试标记不占布局空间，不影响上面算出的字号。
        // 整体再按挖孔安全区收边，使内容完整落在可绘制且不被遮挡的区域内。
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(start = padLeft, top = padTop, end = padRight, bottom = padBottom),
        ) {
            if (isLandscape) {
                LandscapeClock(
                    time = time,
                    fontSize = fontSize,
                    color = textColor,
                    // 底数用当前族的「全亮字形」：7 段是 8，14 段是 ~
                    ghostDigit = fontFamily.ghostDigit,
                    showGhost = ghostVisible,
                    onToggleGhost = onToggleGhost,
                    modifier = Modifier
                        .align(Alignment.Center)
                        .padding(margin)
                        // unbounded 是关键：父 Box 给出 maxWidth = 可用宽 的约束，内容超宽时
                        // Row 的布局宽度被钳在约束值上，onGloballyPositioned 只能测到约束宽度
                        // （实测 mw 恰等于 usable−2×margin），字号校正因此误判"已达标"，
                        // 而 Text 在约束不足时仍会越界绘制 —— 表现为数字压过留白灰线。
                        .wrapContentWidth(Alignment.CenterHorizontally, unbounded = true)
                        // 放在 padding 之后：这里拿到的才是**字形内容**的外框（不含留白），
                        // 其坐标已平移到可用区内，可直接与 usableHeight 比较
                        .onGloballyPositioned { coords ->
                            val r = coords.boundsInParent()
                            contentTopDp = r.top / probeDensity.density
                            contentBottomDp = r.bottom / probeDensity.density
                            clockDigitsRect = coords.boundsInRoot()
                            // 横屏：记录内容真实宽度，供字号实测校正使用
                            landscapeWidthDp = coords.size.width / probeDensity.density
                        },
                )
            } else {
                PortraitClock(
                    time = time,
                    fontSize = fontSize,
                    fontSizeDp = layout.fontSizeSp,
                    color = textColor,
                    ghostDigit = fontFamily.ghostDigit,
                    showGhost = ghostVisible,
                    onToggleGhost = onToggleGhost,
                    lineGap = lineGap,
                    onGlyphHeight = { glyphLineHeightPx = it },
                    modifier = Modifier
                        .align(Alignment.Center)
                        .padding(margin)
                        .onGloballyPositioned { coords ->
                            val r = coords.boundsInParent()
                            contentTopDp = r.top / probeDensity.density
                            contentBottomDp = r.bottom / probeDensity.density
                            clockDigitsRect = coords.boundsInRoot()
                            // 必须用根坐标：根手势的 at 就是根坐标系
                            clockDigitsRect = coords.boundsInRoot()
                        },
                )
            }

            // 横屏过渡提示：时间上方显示「日期T时间+时区」，下方显示当前字体全名。
            // 只在横屏出现；竖屏三行已经占满，没有上下空白可用。
            if (isLandscape) {
                ClockInfoOverlay(
                    fontFamily = fontFamily,
                    fontStyle = fontStyle,
                    colorsInverted = colorsInverted,
                    // 注意用**可见留白**（墨迹到屏幕边的距离，= 一个冒号笔迹宽），
                    // 而不是 layout.marginDp（那是字形骨架与墨迹之间的内空白，本例仅 3dp）。
                    // 两者混用会让目标宽度每边多出约 12dp，表现为文字顶出边距。
                    visibleMargin = layout.visibleMarginDp.dp,
                    usableWidth = usableWidth,
                    // 时钟行高：字号 × 行框比例，用于把提示贴在时钟上下方
                    clockHeight = (layout.fontSizeSp * ClockLayout.LINE_HEIGHT_RATIO).dp,
                    measurer = measurer,
                    restart = infoRestart,
                    extend = infoExtend,
                    onPhaseChange = { infoPhase = it },
                    batteryPercent = batteryPercent,
                    pinnedBlocks = pinnedBlocks,
                    onPinnedChange = { pinnedBlocks = it; prefs.pinnedInfoBlocks = it },
                    ghostVisible = ghostVisible,
                    onShowAbout = { showAbout = true },
                    monoLowercase = monoLowercase,
                    onToggleMono = onToggleMono,
                )
            }

            if (showDebugMarks) {
                DebugGrid(
                    isLandscape = isLandscape,
                    visibleMarginDp = layout.visibleMarginDp,
                    contentTopDp = contentTopDp,
                    contentBottomDp = contentBottomDp,
                )
            }


            // 诊断区：**只在调试包出现**——正式包连版本号都不导出。
            // 整块贴到屏幕最下缘、字号压到最小，尽量避开时钟与横屏过渡提示所占的中央空白。
            if (showAbout) {
            AboutPanel(
                onDismiss = { showAbout = false },
                onResetDefaults = {
                    showAbout = false
                    onResetDefaults()
                },
            )
        }

        // 诊断文字会压在面板之上，面板打开时让位（仅调试包有诊断）
        if (showDiagnostics && !showAbout) {
                val density = LocalDensity.current
                val pxW = (canvasWidthDp * density.density).toInt()
                val pxH = (canvasHeightDp * density.density).toInt()
                Column(
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(horizontal = VERSION_LABEL_MARGIN, vertical = 2.dp),
                    horizontalAlignment = Alignment.End,
                ) {
                    Text(
                        text = "v${BuildConfig.DISPLAY_VERSION}$BUILD_TAG  " +
                        "ghost=${if (ghostVisible) "ON" else "OFF"}  dbl=$dblTapCount/$dblTapLast  " +
                        "digitsRect=" + (clockDigitsRect?.let {
                            "${it.left.toInt()},${it.top.toInt()},${it.right.toInt()},${it.bottom.toInt()}"
                        } ?: "-") + "  " +
                            "w=${canvasWidthDp.toInt()}dp/${pxW}px h=${canvasHeightDp.toInt()}dp/${pxH}px " +
                            "den=${density.density} font=${density.fontScale} size=${usedFontSizeSp.toInt()}sp${if (isLandscape) " (base ${layout.fontSizeSp.toInt()}, mw ${"%.1f".format(landscapeWidthDp)}dp)" else ""}",
                        color = colors.label,
                        fontSize = DIAG_FONT_SIZE,
                        // 诊断文本会叠在数字上，加半透明黑底 + 描边阴影保证可读
                        style = TextStyle(
                            shadow = Shadow(
                                color = Color.Black,
                                offset = Offset.Zero,
                                blurRadius = 4f,
                            ),
                        ),
                        modifier = Modifier
                            .background(Color.Black.copy(alpha = 0.72f))
                            .padding(horizontal = 4.dp, vertical = 1.dp),
                    )
                    Text(
                        text = "line=${"%.1f".format(layout.visibleMarginDp)}dp/" +
                            "${(layout.visibleMarginDp * density.density).toInt()}px " +
                            "= ${"%.3f".format(layout.visibleMarginDp / layout.fontSizeSp)}em  " +
                            "pad=${"%.1f".format(layout.marginDp)}dp  " +
                            "cut=T${cutTop.value.toInt()}/B${cutBottom.value.toInt()}/" +
                            "L${cutLeft.value.toInt()}/R${cutRight.value.toInt()} " +
                            "pad=T${padTop.value.toInt()}/B${padBottom.value.toInt()}/" +
                            "L${padLeft.value.toInt()}/R${padRight.value.toInt()} " +
                            "usable=${usableWidth.value.toInt()}x${usableHeight.value.toInt()}dp",
                        color = colors.label,
                        fontSize = DIAG_FONT_SIZE,
                        // 诊断文本会叠在数字上，加半透明黑底 + 描边阴影保证可读
                        style = TextStyle(
                            shadow = Shadow(
                                color = Color.Black,
                                offset = Offset.Zero,
                                blurRadius = 4f,
                            ),
                        ),
                        modifier = Modifier
                            .background(Color.Black.copy(alpha = 0.72f))
                            .padding(horizontal = 4.dp, vertical = 1.dp),
                    )
                    Text(
                        text = "measL=${"%.3f".format(measured.digitRatio * 6 + measured.colonRatio * 2)}em " +
                            "lineBox=${"%.3f".format(measured.lineBoxRatio)}em(设定) " +
                            "theoryL=${"%.3f".format(ClockLayout.theoreticalLandscapeContentRatio())}em " +
                            "digitInk=${(layout.fontSizeSp * ClockLayout.DIGIT_INK_RATIO).toInt()}dp " +
                            "colonInk=${(layout.fontSizeSp * ClockLayout.COLON_INK_RATIO).toInt()}dp  " +
                            "icon want=${iconReport?.want ?: -1}" +
                            " before=${iconReport?.before ?: -9}" +
                            " after=${iconReport?.after ?: -9}" +
                            " active=${iconReport?.active ?: -9}  " +
                            "${fontFamily.label}/${fontStyle.label}" +
                            if (colorsInverted) " 白底" else " 黑底",
                        color = colors.label,
                        fontSize = DIAG_FONT_SIZE,
                        // 诊断文本会叠在数字上，加半透明黑底 + 描边阴影保证可读
                        style = TextStyle(
                            shadow = Shadow(
                                color = Color.Black,
                                offset = Offset.Zero,
                                blurRadius = 4f,
                            ),
                        ),
                        modifier = Modifier
                            .background(Color.Black.copy(alpha = 0.72f))
                            .padding(horizontal = 4.dp, vertical = 1.dp),
                    )
                    // 内容边界与越界量：over > 0 即内容底部越出可用区（就是"下方越界"）
                    Text(
                        text = "content T=${"%.1f".format(contentTopDp)}dp " +
                            "B=${"%.1f".format(contentBottomDp)}dp " +
                            "H=${"%.1f".format(contentBottomDp - contentTopDp)}dp  " +
                            "over=${"%.1f".format(contentBottomDp - usableHeight.value)}dp  " +
                            "lineBox=${"%.1f".format(layout.fontSizeSp * ClockLayout.LINE_HEIGHT_RATIO)}dp " +
                            "need3=${"%.1f".format(
                                3f * layout.fontSizeSp * ClockLayout.LINE_HEIGHT_RATIO +
                                    2f * layout.marginDp
                            )}dp " +
                            "glyph=${"%.1f".format(glyphLineHeightPx / density.density)}dp " +
                            "x3=${"%.1f".format(3 * glyphLineHeightPx / density.density)}dp",
                        color = colors.label,
                        fontSize = DIAG_FONT_SIZE,
                        // 诊断文本会叠在数字上，加半透明黑底 + 描边阴影保证可读
                        style = TextStyle(
                            shadow = Shadow(
                                color = Color.Black,
                                offset = Offset.Zero,
                                blurRadius = 4f,
                            ),
                        ),
                        modifier = Modifier
                            .background(Color.Black.copy(alpha = 0.72f))
                            .padding(horizontal = 4.dp, vertical = 1.dp),
                    )
                    // 系统栏 / 安全区：平板任务栏不属于 displayCutout，若此处有值而 pad 未覆盖即为越界根因
                    Text(
                        text = "inset navB=${"%.1f".format(navBottomDp)}dp " +
                            "sysB=${"%.1f".format(sysBottomDp)}dp " +
                            "safeB=${"%.1f".format(safeBottomDp)}dp " +
                            "safeL/R=${"%.1f".format(safeLeftDp)}/${"%.1f".format(safeRightDp)}dp  " +
                            "padB=${"%.1f".format(padBottom.value)}dp " +
                            if (isLandscape) "landscape" else "portrait",
                        color = colors.label,
                        fontSize = DIAG_FONT_SIZE,
                        // 诊断文本会叠在数字上，加半透明黑底 + 描边阴影保证可读
                        style = TextStyle(
                            shadow = Shadow(
                                color = Color.Black,
                                offset = Offset.Zero,
                                blurRadius = 4f,
                            ),
                        ),
                        modifier = Modifier
                            .background(Color.Black.copy(alpha = 0.72f))
                            .padding(horizontal = 4.dp, vertical = 1.dp),
                    )
                }
            }
        }
    }
    }
}

/** 右下角版本号：固定字号，不参与时钟的字号自适应。 */
private val VERSION_LABEL_FONT_SIZE = 11.sp
private val VERSION_LABEL_MARGIN = 8.dp

private val DEBUG_LINE_THICKNESS = 1.dp

/**
 * 触发滑屏切换所需的最小位移。
 * 过小会与双击/长按抢事件，过大则手感迟钝；48dp 约等于拇指一次轻扫。
 */
private val SWIPE_THRESHOLD = 48.dp

/** 横屏过渡提示：淡入时长、停留时长、淡出时长。 */
private const val INFO_FADE_IN_MS = 400
private const val INFO_HOLD_MS = 3000L
private const val INFO_FADE_OUT_MS = 600

/** 提示文字与时钟行之间的间距。 */
private val INFO_GAP = 22.dp

/** 过渡提示内部的行距系数（与时钟行框一致）。 */
private const val INFO_LINE_SPACING = 1.2f

/** 字体名交叉淡化的时长：旧名淡出的同时，新名淡入。 */
private const val INFO_CROSS_FADE_MS = 400

/** 过渡提示的播放阶段，决定单击如何响应。 */
enum class InfoPhase { Hidden, FadingIn, Holding, FadingOut }

/** 诊断文字字号：比版本标签更小，便于整块塞进边角空白。 */
private val DIAG_FONT_SIZE = 9.sp

/**
 * 电量百分比字号。用当前数码字体渲染，需比版本号大一些才清晰；
 * 仍远小于时钟数字，不干扰读数。
 */
private val BATTERY_FONT_SIZE = 18.sp

/**
 * 调试包在版本号后缀上「(CS)」，与正式包一眼区分。
 * 应用名同样由 debug source set 的 strings.xml 追加该标识。
 */
private val BUILD_TAG = if (BuildConfig.DEBUG) "(CS)" else ""

/**
 * 项目仓库地址，显示在应用信息面板的标题里：
 * 横屏接在「时分秒(HoMiSe)」后面，竖屏另起一行放在下面。
 *
 * 仓库尚未正式发布，此处为暂定地址；确定后只需改这一行。
 */
private const val REPO_URL = "https://github.com/KuwsSyet9999/HoMiSe-Clock"

/**
 * ISO 8601 串样本。长度固定为 25 字符，用来**定格**上方那一行的字号，
 * 使其恰好顶到左右边距。
 */
private const val INFO_STAMP_SAMPLE = "2026-10-17T06:41:02U08:00"

/**
 * 可能出现的最长字体名，用来定格下方那一行的**通用字号**。
 *
 * 各字体名长短不一（`HSSeg 7 Classic Light` 与
 * `DSEG14 Classic Mini Mono Bold Italic` 相差 19 个字符），
 * 若按当前名称逐次算字号，切换时会看到字号忽大忽小。
 * 统一按这条最长样本定格一次，任何字体名都不会超宽。
 */
// 字号按**实际显示**的最宽字体名计算。
// 关键：字体里空格 advance 只有 200，而下划线是 816；信息块显示前会把空格换成
// 下划线（见 displayText），所以基准串必须用下划线，否则算出的字号会偏大、
// 真正显示时超出边界。此处取所有 变体×样式×Mono 组合里最宽的一个
// （Light Italic 比 Bold Italic 多一个字符）。
private const val INFO_LONGEST_NAME = "HSEG16_Classic_Mini_Mono_Light_Italic"

/**
 * 首帧字号安全系数。`TextMeasurer` 的估算宽度比实际排版宽度小约 5%，
 * 故字号取估算值的 95% 作为起点，再由渲染实测迭代收敛。
 */
private const val INFO_WIDTH_SAFETY = 0.95f

/**
 * 求一个字号（sp），使 [sample] 在该字体下渲染后，**可见宽度不超过** [contentWidthDp]，
 * 即左右落在边距之内。
 *
 * 用实测量比例反推：先在 100sp 探针下测出宽度，再按比例换算并留 [INFO_WIDTH_SAFETY] 余量。
 * 字体缺字而回退到系统字形时，测量结果同样有效，因此不需要假设等宽。
 */
private fun fitFontSizeSp(
    measurer: TextMeasurer,
    font: FontFamily,
    sample: String,
    contentWidthDp: Float,
    density: Density,
): Float {
    val probeSp = 100f
    val probeWidthPx = measurer.measure(
        text = sample,
        style = TextStyle(fontFamily = font, fontSize = probeSp.sp),
    ).size.width
    if (probeWidthPx <= 0) return 12f
    val contentWidthPx = with(density) { contentWidthDp.dp.toPx() }
    return probeSp * contentWidthPx / probeWidthPx * INFO_WIDTH_SAFETY
}

/**
 * 两个等长的 ISO 样本：S7 版字体（HSEG7）本身含 `+` 字形，两个样本一致。
 */
private const val INFO_STAMP_SAMPLE_7 = "2026-10-17T06:41:02+08:00"
private const val INFO_STAMP_SAMPLE_14 = "2026-10-17T06:41:02+08:00"

private fun stampSampleOf(family: DsegFamily): String =
    if (family.series == 7) INFO_STAMP_SAMPLE_7 else INFO_STAMP_SAMPLE_14

/**
 * 当前的 ISO 8601 时刻串，如 `2026-10-17T06:41:02+08:00`。
 * HSEG7 自带 `+` 字形，不再替换成 `U`（那是旧 DSEG7 时代的兼容处理）。
 */
private fun currentStamp(family: DsegFamily): String =
    OffsetDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ssXXX"))

/**
 * 横屏过渡提示：
 *   - 时间**上方**：`日期T时间+时区`（ISO 8601，如 `2026-10-17T06:41:02U08:00`）
 *   - 时间**下方**：当前字体全名（如 `HSSeg 7 Modern Mini Bold Italic`）
 *
 * 均用当前字体、灰色；两行**紧邻时钟**上下，而不是贴在屏幕边缘；
 * 字号由"顶到左右边距"反推——上方按固定长度的 ISO 串，下方按最长字体名定格通用字号。
 * 淡入 → 停留 3 秒 → 淡出，每次切换字体／样式／配色都重播。
 *
 * 用 `alpha` 而不是 `AnimatedVisibility`：后者出现时会占用布局空间，把时钟挤动。
 */
@Composable
private fun androidx.compose.foundation.layout.BoxScope.ClockInfoOverlay(
    fontFamily: DsegFamily,
    fontStyle: DsegStyle,
    colorsInverted: Boolean,
    visibleMargin: androidx.compose.ui.unit.Dp,
    usableWidth: androidx.compose.ui.unit.Dp,
    clockHeight: androidx.compose.ui.unit.Dp,
    measurer: TextMeasurer,
    /** 重播计数：自增即从头播放一轮 */
    restart: Int = 0,
    /** 延长计数：停留期内自增则重新计时 */
    extend: Int = 0,
    /** 上报当前阶段，供点击逻辑判断"此刻该延长、重播还是忽略" */
    onPhaseChange: (InfoPhase) -> Unit = {},
    /** 调试：用彩色方框标出各块的实际命中范围 */
    /** 已常驻的信息块（来自持久化），作为初始状态 */
    pinnedBlocks: Set<String> = DEFAULT_PINNED_INFO_BLOCKS,
    /** 常驻状态变化时回调，供上层写回持久化 */
    onPinnedChange: (Set<String>) -> Unit = {},
    /** 是否显示灰底（双击时钟数字区切换）；关闭时信息文字转灰、不铺字框 */
    ghostVisible: Boolean = true,
    /** 长按版本号：打开应用信息面板 */
    onShowAbout: () -> Unit = {},
    /** 是否启用等宽小写（双击字体名块切换） */
    monoLowercase: Boolean = false,
    /** 切换等宽小写的回调 */
    onToggleMono: () -> Unit = {},
    /** 电量百分比；-1 表示不可用，不显示 */
    batteryPercent: Int = -1,
) {
    // 等宽只对十四段生效：七段字体没有 U+E000~U+E019 这些码位，
    // 强行映射会渲染成豆腐块。
    val monoActive = monoLowercase && fontFamily.series != 7
    val colors = LocalClockColors.current
    val font = LocalClockFont.current
    val density = LocalDensity.current
    val tildeMeasurer = rememberTextMeasurer()
    val alpha = remember { Animatable(0f) }
    var stamp by remember(fontFamily) { mutableStateOf(currentStamp(fontFamily)) }

    // 四块信息各自的「常驻」状态：
    // 单击某一块即在横屏常驻显示（不再随提示淡出），再次单击同一块则重新加入淡入淡出组。
    var pinIso by remember { mutableStateOf(INFO_BLOCK_ISO in pinnedBlocks) }
    var pinName by remember { mutableStateOf(INFO_BLOCK_NAME in pinnedBlocks) }
    var pinVersion by remember { mutableStateOf(INFO_BLOCK_VERSION in pinnedBlocks) }
    var pinBattery by remember { mutableStateOf(INFO_BLOCK_BATTERY in pinnedBlocks) }

    // 播放阶段。块被常驻后即使整体淡出仍然可见，若点击区域一直有效，
    // 就会在"信息未显示"时被点中而凭空钉出一块来 —— 所以只有停留显示阶段
    // （或该块已经常驻、需要取消）才允许切换常驻。
    var phase by remember { mutableStateOf(InfoPhase.Hidden) }

    // 各块的实际命中范围（相对可用区，px）。这些矩形就是"非背景"的判定范围——
    // 落在其中会切换该块常驻，落在之外则视为点击背景（重播/延长提示）。
    var isoBox by remember { mutableStateOf<Rect?>(null) }
    var nameBox by remember { mutableStateOf<Rect?>(null) }
    var nameOuterBox by remember { mutableStateOf<Rect?>(null) }
    var versionBox by remember { mutableStateOf<Rect?>(null) }
    var versionOuterBox by remember { mutableStateOf<Rect?>(null) }
    var batteryBox by remember { mutableStateOf<Rect?>(null) }

    // 常驻权重：0 → 1 为淡入，1 → 0 为淡出。
    // 用 animateFloatAsState 而不是直接读布尔，取消常驻时才会以**淡出**形式退出，
    // 而不是 alpha 瞬间跳变、看起来"啪"地消失。
    val pinIsoAlpha by animateFloatAsState(if (pinIso) 1f else 0f, tween(INFO_FADE_OUT_MS))
    val pinNameAlpha by animateFloatAsState(if (pinName) 1f else 0f, tween(INFO_FADE_OUT_MS))
    val pinVersionAlpha by animateFloatAsState(if (pinVersion) 1f else 0f, tween(INFO_FADE_OUT_MS))
    val pinBatteryAlpha by animateFloatAsState(if (pinBattery) 1f else 0f, tween(INFO_FADE_OUT_MS))

    // 字体名两层共用的权重（交叉淡化在其上叠加）
    val nameAlpha = maxOf(alpha.value, pinNameAlpha)

    // 常驻状态持久化：任一变化即写回，重启后继续生效。
    // 四块共用一条写回路径，避免各自遗漏（此前四个布尔只存在于内存，重启必然归零）。
    LaunchedEffect(pinIso, pinName, pinVersion, pinBattery) {
        onPinnedChange(
            buildSet {
                if (pinIso) add(INFO_BLOCK_ISO)
                if (pinName) add(INFO_BLOCK_NAME)
                if (pinVersion) add(INFO_BLOCK_VERSION)
                if (pinBattery) add(INFO_BLOCK_BATTERY)
            }
        )
    }

    // 左右边距以内就是提示文字可以占满的宽度
    val contentWidth = usableWidth - visibleMargin * 2
    val contentWidthDp = contentWidth.value
    val contentWidthPx = with(density) { contentWidth.toPx() }

    // 七段用 U 样本、十四段用 + 样本，字形宽度不同，需分别定格
    val stampSample = stampSampleOf(fontFamily)
    val stampBaseSize = remember(measurer, font, contentWidthDp, density, stampSample) {
        fitFontSizeSp(measurer, font, stampSample, contentWidthDp, density)
    }
    val nameBaseSize = remember(measurer, font, contentWidthDp, density) {
        fitFontSizeSp(measurer, font, INFO_LONGEST_NAME, contentWidthDp, density)
    }

    // 字号迭代校正。
    //
    // 不能把 TextMeasurer 的估算值直接当最终字号：它与实际排版宽度有约 5% 偏差，
    // 且该偏差随字号非线性变化，用固定系数补偿不掉。这里改为"渲染后按实测宽度等比
    // 修正**当前**字号"，迭代到偏差小于 1% 即停——宽度与字号成正比，一两轮即收敛。
    //
    // 两个前提缺一不可：
    //   1) 该行不能加 .width() 约束，否则实测宽度被钳制在约束值上，测不到真实宽度；
    //   2) 修正必须基于**当前**字号；若拿初始估算字号去乘，每轮都从错误基准出发，
    //      字号会来回震荡——这正是"文字抽搐"的成因。
    var stampSize by remember(contentWidthPx, stampSample) { mutableStateOf(stampBaseSize) }
    var stampRenderedPx by remember { mutableStateOf(0f) }

    // 字体名与版本号的字号由**理论最长**字体名一次定格，之后固定不变。
    // 若改用当前名称逐次校正，短名字也会被放大到顶满边距，切换字体时字号忽大忽小。
    // 代价是最长名之外的名称不顶满而是居中——这正是"固定字号"应有的表现。
    val nameSizeValue = nameBaseSize
    val nameSize = nameSizeValue.sp

    // 字体名的交叉淡化：切换字体时不让名字瞬间跳变，而是旧名淡出、新名淡入、两者同步。
    // 它与整体的淡入淡出相乘（见下方 alpha），因此提示自身的出现/消失节奏不受影响。
    // 两层都用**当前**字体渲染——字体已经切过去了，旧名无法再用旧字体重绘。
    val fullName = fontFamily.fullFontName(fontStyle, monoActive)
    var shownName by remember { mutableStateOf(fullName) }
    var outgoingName by remember { mutableStateOf<String?>(null) }
    val cross = remember { Animatable(1f) }

    LaunchedEffect(fullName) {
        if (shownName != fullName) {
            outgoingName = shownName
            shownName = fullName
            cross.snapTo(0f)
            cross.animateTo(1f, tween(INFO_CROSS_FADE_MS))
            outgoingName = null
        }
    }

    LaunchedEffect(stampRenderedPx) {
        if (stampRenderedPx > 0f) {
            val ratio = contentWidthPx / stampRenderedPx
            if (abs(ratio - 1f) > 0.01f) stampSize *= ratio
        }
    }

    // 与中央时钟同步步进：每整秒刷新，避免两处秒数不一致。
    // 对齐到下一个整秒边界，与 ClockRoute 的做法一致；切字体时重启以立即用新字形。
    LaunchedEffect(fontFamily) {
        while (true) {
            stamp = currentStamp(fontFamily)
            delay(1000L - System.currentTimeMillis() % 1000L)
        }
    }

    // 切换字体／样式／配色，或用户单击时重播淡入淡出；
    // 停留期内再次单击则重新计时（用 rememberUpdatedState 读取最新延长信号，
    // 否则协程捕获的是启动那一刻的旧值）。
    val extendState = rememberUpdatedState(extend)
    LaunchedEffect(fontFamily, fontStyle, colorsInverted, restart) {
        phase = InfoPhase.FadingIn
        onPhaseChange(InfoPhase.FadingIn)
        alpha.snapTo(0f)
        alpha.animateTo(1f, tween(INFO_FADE_IN_MS))
        phase = InfoPhase.Holding
        onPhaseChange(InfoPhase.Holding)
        var seen = extendState.value
        while (true) {
            delay(INFO_HOLD_MS)
            if (extendState.value == seen) break
            seen = extendState.value
        }
        phase = InfoPhase.FadingOut
        onPhaseChange(InfoPhase.FadingOut)
        alpha.animateTo(0f, tween(INFO_FADE_OUT_MS))
        phase = InfoPhase.Hidden
        onPhaseChange(InfoPhase.Hidden)
    }

    // 以时钟行中心为基准上下偏移，让提示紧贴时钟而不是贴屏幕边
    val halfClockWithGap = clockHeight / 2 + INFO_GAP

    InfoText(
        showFrame = ghostVisible,
        series = fontFamily.series,
        text = displayText(applyMonoLowercase(stamp, monoActive)),
        fontFamily = font,
        fontSize = stampSize.sp,
        color = if (ghostVisible) colors.digits else colors.label,
        frameColor = colors.dimmed,
        maxLines = 1,
        softWrap = false,
        textAlign = TextAlign.Center,
        onTextLayout = { result ->
            stampRenderedPx = result.getLineRight(0) - result.getLineLeft(0)
        },
        // unbounded 是关键：父 Box 会给出 maxWidth = 屏宽的约束，超宽文字会被钳在屏宽上，
        // 实测值随之恒为屏宽，迭代校正就会把"仍被钳制"误判成"已达标"而提前停止。
        modifier = Modifier
            .align(Alignment.Center)
            .wrapContentWidth(Alignment.CenterHorizontally, unbounded = true)
            .offset(y = -halfClockWithGap)
            // 常驻时强制不透明；否则跟随整体淡入淡出。
            // 单击该块即切换常驻状态（块自身消费点击，不会冒泡到全屏手势）。
            .alpha(maxOf(alpha.value, pinIsoAlpha))
            .onGloballyPositioned { isoBox = it.boundsInParent() }
            .then(hitModifier(pinIso, phase) { pinIso = !pinIso })
    )
    // S7 版：不显示字体名块（字号仍由 nameSizeValue 定格，供版本号复用）
    // 版本号：外层 Box 提供固定宽度以实现右对齐，内层 Text 再按**自身字符宽度**测量。
    // 若只用一个 Text 加 width(contentWidth)，命中范围会覆盖整行，与另外三块"只包住文字"
    // 不一致 —— 那样行内空白处也会被判为元素、吞掉背景手势。
    Box(
        modifier = Modifier
            .align(Alignment.Center)
            .offset(y = halfClockWithGap + (nameSizeValue * INFO_LINE_SPACING).dp)
            .width(contentWidth)
            .onGloballyPositioned { versionOuterBox = it.boundsInParent() },
        contentAlignment = Alignment.CenterEnd,
    ) {
        InfoText(
            showFrame = ghostVisible,
            series = fontFamily.series,
            text = displayText(applyMonoLowercase("v${BuildConfig.DISPLAY_VERSION}$BUILD_TAG", monoActive)),
            fontFamily = font,
            fontSize = nameSize,
            color = if (ghostVisible) colors.digits else colors.label,
            frameColor = colors.dimmed,
            maxLines = 1,
            softWrap = false,
            modifier = Modifier
                .wrapContentWidth(Alignment.End, unbounded = true)
                .alpha(maxOf(alpha.value, pinVersionAlpha))
                .onGloballyPositioned { versionBox = it.boundsInParent() }
                .then(
                    hitModifier(
                        pinned = pinVersion,
                        phase = phase,
                        onLongPress = onShowAbout,
                    ) { pinVersion = !pinVersion },
                ),
        )
    }

    // 横屏左下角：电量百分比。
    // 七段字体没有 % 字形，用 ".:"（点 + 冒号）代替。
    // 位置对齐到留白边界（一个冒号笔迹宽）以内，与井字线的左/下边界一致；
    // 它与上面三块共用同一套淡入淡出，单击本块同样可切换常驻。
    if (batteryPercent >= 0) {
        InfoText(
            showFrame = ghostVisible,
            // 七段字体没有 % 字形，用 ".:" 代替；十四段字体有 % 字形则直接用
            text = "${batteryPercent}${if (fontFamily.series == 7) ".:" else "%"}",
            series = fontFamily.series,
            fontFamily = font,
            fontSize = BATTERY_FONT_SIZE,
            color = if (ghostVisible) colors.digits else colors.label,
            frameColor = colors.dimmed,
            maxLines = 1,
            softWrap = false,
            modifier = Modifier
                .align(Alignment.BottomStart)
                .padding(start = visibleMargin, bottom = visibleMargin)
                .alpha(maxOf(alpha.value, pinBatteryAlpha))
                .onGloballyPositioned { batteryBox = it.boundsInParent() }
                .then(hitModifier(pinBattery, phase) { pinBattery = !pinBattery })
        )
    }

}

/**
 * 一块信息的点击修饰符。
 *
 * 仅当该块**可见**（已常驻，或提示正处于停留显示阶段）时才挂上点击处理；
 * 其余时候不挂，点击会穿透到背景手势上，按"点空白"处理（重播 / 延长停留）。
 * 若一直挂着，隐藏状态的块会默默吞掉点击，背景手势就再也收不到。
 */

/**
 * 调试铺底用的字符串：除 `.` 和 `:` 外，每个字符都换成 `~`。
 *
 * 字体里除这两个符号外，所有字符的 advance 都是 816（含 `_`、`-`、`+`、`(`、`)`、`%`
 * 与全部字母数字），所以替换后**总宽度完全不变**。保留 `.` 与 `:` 是为了让它们的位置
 * 在被铺底时依然可见——它们是零宽/窄宽字符，换成 `~` 反而会把版面撑开。
 */
private fun tildeFrame(text: String, series: Int): String {
    // 全亮字形：七段是 `8`（七段全亮），十四段/十六段是 `~`（全部段点亮）。
    // 七段字体里没有 `~`，用它做铺底会渲染成豆腐块。
    val frame = if (series == 7) '8' else '~'
    return buildString(text.length) {
        for (c in text) append(if (c == '.' || c == ':') c else frame)
    }
}

/**
 * 信息文本：底下叠一层 `~` 全亮字形作为字形框，便于肉眼核对每个字形是否偏移。
 *
 * 用**两个 Text 层叠**而不是 Canvas 绘制：Text 的 textAlign 与行高决定字形位置，
 * 另起一层 Canvas 无法复现（曾因此整体偏移）。同样的字符串 + 同样的 style，
 * 两层的排版结果必然一致。
 */
@Composable
private fun InfoText(
    text: String,
    series: Int,
    fontFamily: FontFamily,
    fontSize: TextUnit,
    color: Color,
    frameColor: Color,
    modifier: Modifier = Modifier,
    /** 是否铺描灰色字框；由灰底开关控制，与调试无关 */
    showFrame: Boolean = true,
    maxLines: Int = 1,
    softWrap: Boolean = false,
    textAlign: TextAlign? = null,
    onTextLayout: ((TextLayoutResult) -> Unit)? = null,
) {
    Box(modifier = modifier) {
        if (showFrame) {
            Text(
                text = tildeFrame(text, series),
                fontFamily = fontFamily,
                fontSize = fontSize,
                color = frameColor,
                maxLines = maxLines,
                softWrap = softWrap,
                textAlign = textAlign,
            )
        }
        Text(
            text = text,
            fontFamily = fontFamily,
            fontSize = fontSize,
            color = color,
            maxLines = maxLines,
            softWrap = softWrap,
            textAlign = textAlign,
            onTextLayout = onTextLayout ?: {},
        )
    }
}

/**
 * 应用信息面板：长按版本号块打开。
 *
 * 面向使用者，只讲「这是什么」和「怎么操作」，不出现 versionCode、包名、密度等技术项。
 * 关闭方式：右上角 × ，或点卡片以外的任何区域。
 */
@Composable
private fun androidx.compose.foundation.layout.BoxScope.AboutPanel(
    onDismiss: () -> Unit,
    onResetDefaults: () -> Unit,
) {
    val colors = LocalClockColors.current
    val landscape = LocalConfiguration.current.orientation == Configuration.ORIENTATION_LANDSCAPE
    // 遮罩本身可点击，点击即关闭
    BoxWithConstraints(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black.copy(alpha = 0.62f))
            .pointerInput(Unit) {
                detectTapGestures(onTap = { onDismiss() })
            },
        contentAlignment = Alignment.Center,
    ) {
        Box(
            modifier = Modifier
                .widthIn(max = 560.dp)
                .fillMaxWidth(0.86f)
                // 内容高于可用高度时在卡片内滚动，避免上下被屏幕裁掉
                .heightIn(max = maxHeight - 16.dp)
                // 卡片自身吞掉点击，避免穿透到遮罩
                .pointerInput(Unit) { detectTapGestures(onTap = {}) }
                .background(colors.background, RoundedCornerShape(10.dp))
                .border(1.dp, colors.dimmed, RoundedCornerShape(10.dp))
                .padding(horizontal = 18.dp, vertical = 12.dp),
        ) {
            Column(modifier = Modifier.verticalScroll(rememberScrollState())) {
                // 标题行：应用名 +（横屏同一行的）仓库地址 + 右上角关闭
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.Top,
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = "时分秒S7(HMSS7)",
                                color = colors.digits,
                                fontSize = 17.sp,
                                fontWeight = FontWeight.SemiBold,
                            )
                            if (landscape) {
                                // 横屏：地址接在应用名后面，点击用浏览器打开仓库
                                Spacer(Modifier.width(10.dp))
                                Text(
                                    text = REPO_URL,
                                    color = colors.dimmed,
                                    fontSize = 10.sp,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                    textDecoration = TextDecoration.Underline,
                                    modifier = Modifier.openRepoLink(),
                                )
                            }
                        }
                    }
                    Spacer(Modifier.width(10.dp))
                    CloseBox(onDismiss)
                }
                if (!landscape) {
                    // 竖屏：地址另起一行并独占整行。放在标题行的 weight 列里会被右侧的 ×
                    // 挤掉约 36dp，10sp 的地址实际需要约 306dp，必然折行，故移出该行。
                    Spacer(Modifier.height(2.dp))
                    RepoUrlLine(colors)
                }

                // 版本行：版本号后面紧接「恢复默认设置」
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "版本 " + BuildConfig.DISPLAY_VERSION + BUILD_TAG,
                        color = colors.dimmed,
                        fontSize = 12.sp,
                    )
                    Spacer(Modifier.width(10.dp))
                    ResetButton(onResetDefaults, colors)
                }

                Spacer(Modifier.height(8.dp))
                Text(
                    text = "纯净的七段数码管风格时钟。",
                    color = colors.label,
                    fontSize = 12.sp,
                    lineHeight = 17.sp,
                )

                Spacer(Modifier.height(8.dp))
                SectionTitle("操作", colors)
                Spacer(Modifier.height(4.dp))
                val gestures = listOf(
                    "单击背景" to "重播信息提示",
                    "双击时钟" to "开关灰色底衬",
                    "双击背景" to "黑白配色互换",
                    "单击信息块" to "该块常驻显示",
                    "长按背景" to "开关最高亮度",
                    "左右滑动" to "换字体风格",
                    "上下滑动" to "换字重与倾斜",
                )
                if (landscape) {
                    // 两列排布：横屏一行放下 4 组，避免卡片被屏幕高度截断。
                    // 键宽与 AboutRow 保持一致（88dp），否则上下两段的说明列会错开。
                    gestures.chunked(4).let { cols ->
                        Row(modifier = Modifier.fillMaxWidth()) {
                            cols.forEachIndexed { ci, col ->
                                Column(modifier = Modifier.weight(1f)) {
                                    col.forEach { (k, v) ->
                                        Row(
                                            modifier = Modifier.fillMaxWidth()
                                                .padding(vertical = 1.dp),
                                            verticalAlignment = Alignment.CenterVertically,
                                        ) {
                                            Text(
                                                text = k,
                                                color = colors.label,
                                                fontSize = 12.sp,
                                                modifier = Modifier.width(88.dp),
                                            )
                                            Text(text = v, color = colors.digits, fontSize = 12.sp)
                                        }
                                    }
                                }
                                if (ci == 0) Spacer(Modifier.width(16.dp))
                            }
                        }
                    }
                } else {
                    // 竖屏：两列，每项上下两行（操作名在上、说明在下）。360dp 竖屏下
                    // 卡片内容宽约 274dp，两列各约 129dp，正好容纳 6 字以内的说明；
                    // 上下排布让说明从整列宽度换行，而不是被"键 + 说明"的窄列挤成多行。
                    gestures.chunked(4).let { cols ->
                        Row(modifier = Modifier.fillMaxWidth()) {
                            cols.forEachIndexed { ci, col ->
                                Column(modifier = Modifier.weight(1f)) {
                                    col.forEach { (k, v) -> StackedEntry(k, v, colors) }
                                }
                                if (ci == 0) Spacer(Modifier.width(16.dp))
                            }
                        }
                    }
                }

                Spacer(Modifier.height(6.dp))
                SectionTitle("其他", colors)
                Spacer(Modifier.height(4.dp))
                if (landscape) {
                    // 第一行两列放两条短说明：「长按版本号」在左，「竖屏状态」在右
                    Row(modifier = Modifier.fillMaxWidth()) {
                        AboutRow(
                            "长按版本号", "打开本页", colors,
                            modifier = Modifier.weight(1f),
                        )
                        Spacer(Modifier.width(16.dp))
                        AboutRow(
                            "竖屏状态", "只显示时钟", colors,
                            modifier = Modifier.weight(1f),
                        )
                    }
                    // 说明较长，独占整行
                    AboutRow("桌面图标", "随字体 / 配色 / 底衬更新，返回桌面后生效", colors)
                } else {
                    Row(modifier = Modifier.fillMaxWidth()) {
                        StackedEntry(
                            "长按版本号", "打开本页", colors,
                            modifier = Modifier.weight(1f),
                        )
                        Spacer(Modifier.width(16.dp))
                        StackedEntry(
                            "竖屏状态", "只显示时钟", colors,
                            modifier = Modifier.weight(1f),
                        )
                    }
                    StackedEntry("桌面图标", "随字体 / 配色 / 底衬更新，返回桌面后生效", colors)
                }

            }
        }
    }
}

/**
 * 竖屏标题下方的项目仓库地址。
 *
 * 地址较长（44 字符），若按固定 10sp 排版会超出卡片宽度而折行；
 * 这里先按 10sp 实测宽度，再按可用宽度等比缩小字号，保证始终单行显示。
 */
@Composable
private fun RepoUrlLine(colors: ClockColors) {
    val measurer = rememberTextMeasurer()
    val density = LocalDensity.current
    BoxWithConstraints(modifier = Modifier.fillMaxWidth()) {
        val availPx = with(density) { maxWidth.toPx() }
        val baseSize = 10f
        val measuredPx = remember(availPx) {
            measurer.measure(
                text = AnnotatedString(REPO_URL),
                style = TextStyle(fontSize = baseSize.sp),
            ).size.width.toFloat()
        }
        // 0.98 留一点余量，避免测量与实际排版的细微偏差导致折行
        val fit = if (measuredPx > 0f && availPx > 0f) {
            (availPx * 0.98f / measuredPx).coerceAtMost(1f)
        } else {
            1f
        }
        Text(
            text = REPO_URL,
            color = colors.dimmed,
            fontSize = (baseSize * fit).sp,
            maxLines = 1,
            softWrap = false,
            overflow = TextOverflow.Ellipsis,
            textDecoration = TextDecoration.Underline,
            modifier = Modifier.openRepoLink(),
        )
    }
}

/**
 * 打开项目仓库地址。
 *
 * 用 ACTION_VIEW 交给系统选择浏览器；设备上没有可处理的应用时静默忽略，
 * 不弹错误提示（面板里只是一个便利入口）。
 */
private fun openRepo(context: Context) {
    runCatching {
        context.startActivity(
            Intent(Intent.ACTION_VIEW, Uri.parse(REPO_URL))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
        )
    }
}

/** 让地址看起来可点：加下划线，点击即打开仓库；去掉水波纹，避免在纯色卡片上留下痕迹。 */
@Composable
private fun Modifier.openRepoLink(): Modifier {
    val context = LocalContext.current
    return clickable(
        interactionSource = remember { MutableInteractionSource() },
        indication = null,
    ) { openRepo(context) }
}

@Composable
private fun SectionTitle(text: String, colors: ClockColors) {
    Text(
        text = text,
        color = colors.dimmed,
        fontSize = 11.sp,
        letterSpacing = 1.sp,
    )
}

@Composable
private fun AboutRow(
    key: String,
    value: String,
    colors: ClockColors,
    modifier: Modifier = Modifier,
) {
    Row(modifier = modifier.fillMaxWidth().padding(vertical = 1.dp)) {
        Text(text = key, color = colors.label, fontSize = 12.sp, modifier = Modifier.width(88.dp))
        Text(text = value, color = colors.digits, fontSize = 12.sp, modifier = Modifier.weight(1f))
    }
}

/**
 * 竖屏用的上下两行条目：操作名在上、说明在下。
 *
 * 竖屏内容宽约 274dp，左右两列或左右对齐都会让说明只剩约 130~190dp；
 * 上下排布后说明独占整行，短说明不会再被折成两行。
 */
@Composable
private fun StackedEntry(
    key: String,
    value: String,
    colors: ClockColors,
    modifier: Modifier = Modifier,
) {
    Column(modifier = modifier.fillMaxWidth().padding(vertical = 2.dp)) {
        Text(text = key, color = colors.label, fontSize = 12.sp)
        Text(text = value, color = colors.digits, fontSize = 12.sp, lineHeight = 16.sp)
    }
}

/** 右上角的方框 ×，点击关闭。 */
@Composable
private fun CloseBox(onDismiss: () -> Unit) {
    val colors = LocalClockColors.current
    Box(
        modifier = Modifier
            .size(26.dp)
            .border(1.dp, colors.dimmed, RoundedCornerShape(4.dp))
            .pointerInput(Unit) {
                detectTapGestures(onTap = { onDismiss() })
            },
        contentAlignment = Alignment.Center,
    ) {
        Text(text = "\u00D7", color = colors.digits, fontSize = 16.sp)
    }
}

@Composable
private fun ResetButton(onReset: () -> Unit, colors: ClockColors) {
    var confirm by remember { mutableStateOf(false) }
    Box(
        modifier = Modifier
            .border(1.dp, if (confirm) colors.digits else colors.dimmed, RoundedCornerShape(5.dp))
            .pointerInput(confirm) {
                detectTapGestures(
                    onTap = {
                        if (confirm) {
                            onReset()
                            confirm = false
                        } else {
                            confirm = true
                        }
                    },
                )
            }
            .padding(horizontal = 12.dp, vertical = 6.dp),
    ) {
        Text(
            text = if (confirm) "再点一次确认" else "恢复默认设置",
            color = colors.digits,
            fontSize = 12.sp,
        )
    }
}

private fun hitModifier(
    pinned: Boolean,
    phase: InfoPhase,
    onDoubleTap: (() -> Unit)? = null,
    onLongPress: (() -> Unit)? = null,
    onTap: () -> Unit,
): Modifier =
    if (pinned || phase == InfoPhase.Holding) {
        Modifier.pointerInput(Unit) {
            detectTapGestures(
                onTap = { onTap() },
                onDoubleTap = onDoubleTap?.let { cb -> { _: Offset -> cb() } },
                onLongPress = onLongPress?.let { cb -> { _: Offset -> cb() } },
            )
        }
    } else {
        Modifier
    }

/**
 * 四条灰线组成「井」字，标出留白的边界位置：
 *   - 横屏：左右两条竖线（贯穿全高）+ 上下两条横线（贯穿全宽）；
 *   - 竖屏：上下两条横线（贯穿全宽）+ 左右两条竖线（贯穿全高）。
 *
 * 线心正对 [visibleMarginDp]（屏幕边到数字笔迹的可见留白），
 * 因此「线到屏幕边」的距离就是当前实际留白值。
 */
@Composable
private fun androidx.compose.foundation.layout.BoxScope.DebugGrid(
    isLandscape: Boolean,
    visibleMarginDp: Float,
    contentTopDp: Float = -1f,
    contentBottomDp: Float = -1f,
) {
    val m = visibleMarginDp.dp
    val t = DEBUG_LINE_THICKNESS
    if (isLandscape) {
        // 左右两条竖线：贯穿全高，线心落在左右留白边界
        Box(Modifier.align(Alignment.CenterStart).padding(start = m - t / 2f)
            .width(t).fillMaxHeight().background(LocalClockColors.current.debugLine))
        Box(Modifier.align(Alignment.CenterEnd).padding(end = m - t / 2f)
            .width(t).fillMaxHeight().background(LocalClockColors.current.debugLine))
        // 上下两条横线：贯穿全宽
        Box(Modifier.align(Alignment.TopCenter).padding(top = m - t / 2f)
            .height(t).fillMaxWidth().background(LocalClockColors.current.debugLine))
        Box(Modifier.align(Alignment.BottomCenter).padding(bottom = m - t / 2f)
            .height(t).fillMaxWidth().background(LocalClockColors.current.debugLine))
    } else {
        Box(Modifier.align(Alignment.TopCenter).padding(top = m - t / 2f)
            .height(t).fillMaxWidth().background(LocalClockColors.current.debugLine))
        Box(Modifier.align(Alignment.BottomCenter).padding(bottom = m - t / 2f)
            .height(t).fillMaxWidth().background(LocalClockColors.current.debugLine))
        Box(Modifier.align(Alignment.CenterStart).padding(start = m - t / 2f)
            .width(t).fillMaxHeight().background(LocalClockColors.current.debugLine))
        Box(Modifier.align(Alignment.CenterEnd).padding(end = m - t / 2f)
            .width(t).fillMaxHeight().background(LocalClockColors.current.debugLine))
    }

    // 红色细线：标注**字形内容**在可用区内的真实上下边界（由 onGloballyPositioned 实测）。
    // 与灰线（留白边界）对比即可看出内容是否越出留白、甚至越出可用区。
    // 横竖屏都画——竖屏越界正是当前要排查的问题。
    if (contentTopDp >= 0f && contentBottomDp > contentTopDp) {
        val mark = Color.Red.copy(alpha = 0.55f)
        Box(
            Modifier.align(Alignment.TopStart)
                .offset(y = contentTopDp.dp)
                .fillMaxWidth()
                .height(t)
                .background(mark)
        )
        Box(
            Modifier.align(Alignment.TopStart)
                .offset(y = contentBottomDp.dp - t)
                .fillMaxWidth()
                .height(t)
                .background(mark)
        )
    }
}

/**
 * 横屏：`时:分:秒` 一行，组间用冒号分隔。
 *
 * 底层先画一层灰色**全 8**（所有段都点亮的状态），上层再画白色实际时间：
 * 已点亮的段被白色覆盖，未点亮的段透出底层灰色 —— 即数码管的「熄灭」表示。
 * 两层使用**完全相同的布局参数**，同处一个 Box 内叠放，保证逐段严格对齐。
 */
@Composable
private fun LandscapeClock(
    time: ClockTime,
    fontSize: TextUnit,
    color: Color,
    ghostDigit: Char,
    showGhost: Boolean,
    onToggleGhost: () -> Unit,
    modifier: Modifier = Modifier,
) {
    // 底数由当前族的全亮字形重复而成：7 段为 "88"，14 段为 "~~"
    val ghost = ghostDigit.toString().repeat(2)
    Box(modifier = modifier, contentAlignment = Alignment.Center) {
        // 底层：灰色全亮字形，冒号常亮（使冒号熄灭时同样显示为灰色）
        // 双击数字区可关闭这一层（只看纯亮段）
        if (showGhost) {
            LandscapeRow(ghost, ghost, ghost, fontSize, LocalClockColors.current.dimmed, colonVisible = true)
        }
        // 上层：白色实际时间，冒号按 1 秒周期闪烁
        LandscapeRow(
            hour = time.hourText,
            minute = time.minuteText,
            second = time.secondText,
            fontSize = fontSize,
            color = color,
            colonVisible = time.colonVisible,
        )
    }
}

/** 横屏一行：三组数字 + 两个冒号。两层共用同一实现，确保参数与位置完全一致。 */
@Composable
private fun LandscapeRow(
    hour: String,
    minute: String,
    second: String,
    fontSize: TextUnit,
    color: Color,
    colonVisible: Boolean,
) {
    Row(
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        DigitText(hour, fontSize, color)
        ColonGap(fontSize)
        BlinkingColon(fontSize, color, colonVisible)
        ColonGap(fontSize)
        DigitText(minute, fontSize, color)
        ColonGap(fontSize)
        BlinkingColon(fontSize, color, colonVisible)
        ColonGap(fontSize)
        DigitText(second, fontSize, color)
    }
}

/** 冒号两侧的组间距，使「:」与相邻数字的视觉间距等于一个冒号笔迹宽。 */
@Composable
private fun ColonGap(fontSize: TextUnit) {
    Spacer(Modifier.width((fontSize.value * ClockLayout.COLON_GAP_RATIO).dp))
}

/**
 * 竖屏：时、分、秒各占一行。
 *
 * 每行由**固定高度的行框**承载（高度 = LINE_HEIGHT_RATIO × 字号），不依赖 Text 的
 * `lineHeight` —— TextMeasurer 测不到 `lineHeight` 的扩展量（实测恒返回字体自然行高），
 * 而固定高度让三行总高完全可控、可与字号计算严格对齐。
 * 字形在行框内垂直居中，天然形成上下各约 0.1em 留白；两行相邻即约 0.2em 可见间隙，
 * 与行内两位数字之间的间距一致。
 *
 * 与横屏一样叠放两层：底层灰色全亮字形，上层白色实际时间，用于表现「熄灭」的段。
 */
@Composable
private fun PortraitClock(
    time: ClockTime,
    fontSize: TextUnit,
    /** 物理 dp 基准（= layout.fontSizeSp），固定行框的高度必须由它算出 */
    fontSizeDp: Float,
    color: Color,
    ghostDigit: Char,
    showGhost: Boolean,
    onToggleGhost: () -> Unit,
    lineGap: androidx.compose.ui.unit.Dp,
    onGlyphHeight: ((Int) -> Unit)? = null,
    modifier: Modifier = Modifier,
) {
    // 行框高度必须用**物理 dp 基准**（layout.fontSizeSp），而不是渲染用的 fontSize.value。
    //
    // fontSize 是为抵消系统字体缩放而**除以过 fontScale** 的 sp 值，拿它的数值当 dp 用会引入
    // 1/fontScale 的比例偏差：
    //   * fontScale < 1（平板常见，实测 0.85）→ 行框被放大 1.18 倍，
    //     三行 3×273×1.2 本应 982.8dp，实际算成 385.4×3 = 1156dp > 可用 1003dp，底部越界；
    //   * fontScale > 1 → 行框偏小，行间字形重叠。
    // 而字形自身的物理高度恒为 fontSize.value × fontScale = layout.fontSizeSp（dp），
    // 所以行框只需按 layout.fontSizeSp × LINE_HEIGHT_RATIO 计算，与 fontScale 无关。
    val lineBox = (fontSizeDp * ClockLayout.LINE_HEIGHT_RATIO).dp
    // 底数由当前族的全亮字形重复而成：7 段为 "88"，14 段为 "~~"
    val ghost = ghostDigit.toString().repeat(2)
    Box(modifier = modifier, contentAlignment = Alignment.Center) {
        // 底层：灰色全亮字形（双击数字区可关闭，只看纯亮段）
        if (showGhost) {
            PortraitColumn(ghost, ghost, ghost, fontSize, LocalClockColors.current.dimmed, lineBox)
        }
        // 上层：白色实际时间
        PortraitColumn(
            hour = time.hourText,
            minute = time.minuteText,
            second = time.secondText,
            fontSize = fontSize,
            color = color,
            lineBox = lineBox,
            onGlyphHeight = onGlyphHeight,
        )
    }
}

/** 竖屏三行。两层共用同一实现，确保行框高度与位置完全一致。 */
@Composable
private fun PortraitColumn(
    hour: String,
    minute: String,
    second: String,
    fontSize: TextUnit,
    color: Color,
    lineBox: androidx.compose.ui.unit.Dp,
    onGlyphHeight: ((Int) -> Unit)? = null,
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        // 只有第一行回报文字行高：三行参数完全相同，测一行即可
        ClockLine(hour, fontSize, color, lineBox, onGlyphHeight)
        ClockLine(minute, fontSize, color, lineBox)
        ClockLine(second, fontSize, color, lineBox)
    }
}

/** 一行数字：固定高度的行框，字形在框内垂直居中。 */
@Composable
private fun ClockLine(
    text: String,
    fontSize: TextUnit,
    color: Color,
    lineBox: androidx.compose.ui.unit.Dp,
    onGlyphHeight: ((Int) -> Unit)? = null,
) {
    Box(
        modifier = Modifier.height(lineBox),
        contentAlignment = Alignment.Center,
    ) {
        DigitText(text, fontSize, color, onGlyphHeight)
    }
}

/**
 * 一组数码管数字。
 * 不设 `lineHeight`：行框高度一律由外层固定高度的 [ClockLine] 决定，
 * 避免 Compose 行高与测量值不一致（曾导致竖屏三行总高失控、末行越界）。
 */
@Composable
private fun DigitText(
    text: String,
    fontSize: TextUnit,
    color: Color,
    onMeasured: ((Int) -> Unit)? = null,
) {
    Text(
        text = text,
        fontFamily = LocalClockFont.current,
        fontSize = fontSize,
        color = color,
        // 时钟必须单行：一旦约束不足而换行，秒的两位会上下叠放（曾误判为"重叠"）
        softWrap = false,
        maxLines = 1,
        onTextLayout = if (onMeasured != null) {
            { result -> onMeasured(result.size.height) }
        } else {
            null
        },
    )
}

/**
 * 冒号闪烁：亮灭各 500ms，完整周期 1 秒。
 * 熄灭时保持占位（透明），数字位置因此不会跳动。
 */
@Composable
private fun BlinkingColon(fontSize: TextUnit, color: Color, visible: Boolean) {
    Text(
        text = ":",
        fontFamily = LocalClockFont.current,
        fontSize = fontSize,
        color = if (visible) color else Color.Transparent,
        softWrap = false,
        maxLines = 1,
    )
}

private val previewTime = formatClockTime(hour = 14, minute = 5, second = 30)

@Preview(showBackground = true, backgroundColor = 0xFF000000, widthDp = 360, heightDp = 640)
@Composable
private fun PortraitPreview() {
    HoMiSeTheme { ClockScreen(time = previewTime, forceLandscape = false) }
}

@Preview(showBackground = true, backgroundColor = 0xFF000000, widthDp = 640, heightDp = 360)
@Composable
private fun LandscapePreview() {
    HoMiSeTheme { ClockScreen(time = previewTime, forceLandscape = true) }
}
