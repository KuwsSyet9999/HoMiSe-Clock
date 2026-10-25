package com.homise.clock

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * 布局尺寸计算的单元测试（本地运行，不需要设备）。
 *
 * 断言的是需求本身：
 *   - 四周留白 = 一个冒号的笔迹宽度；
 *   - 竖屏行间距与行内数字间距视觉一致；
 *   - 横竖屏都填满屏幕且不溢出。
 */
class ClockLayoutTest {

    /** 常见竖屏：1080x1920 px @ 480dpi => 360x640 dp */
    private val portraitW = 360f
    private val portraitH = 640f

    /** 常见横屏：1920x1080 px @ 480dpi => 640x360 dp */
    private val landscapeW = 640f
    private val landscapeH = 360f

    private fun portrait() = ClockLayout.compute(portraitW, portraitH, false)
    private fun landscape() = ClockLayout.compute(landscapeW, landscapeH, true)

    /** 竖屏可见高度：三行数字笔迹 + 两处行间可见间隙。 */
    private fun portraitInkHeight(f: Float) =
        ClockLayout.PORTRAIT_LINE_COUNT * ClockLayout.LINE_HEIGHT_RATIO * f +
            (ClockLayout.PORTRAIT_LINE_COUNT - 1) * 2f * ClockLayout.DIGIT_SIDE_INK_RATIO * f

    /** 横屏可见宽度：数字笔迹 + 冒号笔迹 + 各段可见间隙。 */
    private fun landscapeInkWidth(f: Float) =
        (ClockLayout.LANDSCAPE_DIGIT_COUNT * ClockLayout.DIGIT_INK_RATIO +
            (ClockLayout.LANDSCAPE_COLON_COUNT + ClockLayout.LANDSCAPE_GAP_SEGMENTS) * ClockLayout.COLON_INK_RATIO) * f

    @Test
    fun portrait_visibleMarginEqualsOneColonInkWidth() {
        val r = portrait()
        assertEquals(r.fontSizeSp * ClockLayout.COLON_INK_RATIO, r.visibleMarginDp, 0.01f)
    }

    @Test
    fun landscape_visibleMarginEqualsOneColonInkWidth() {
        val r = landscape()
        assertEquals(r.fontSizeSp * ClockLayout.COLON_INK_RATIO, r.visibleMarginDp, 0.01f)
    }

    /**
     * 竖屏行间距：行与行之间的可见间隙 = 行内两位数字之间的可见间隙。
     * 二者都由数字字形的内空白构成（各 0.099em），故附加行间距为 0。
     */
    @Test
    fun portrait_lineGapMatchesRowInternalSpacing() {
        val r = portrait()
        assertEquals(0f, r.lineGapDp, 0.01f)
        val withinRow = 2f * ClockLayout.DIGIT_SIDE_INK_RATIO * r.fontSizeSp
        val betweenRows = r.lineGapDp + 2f * ClockLayout.DIGIT_SIDE_INK_RATIO * r.fontSizeSp
        assertEquals(withinRow, betweenRows, 0.01f)
    }

    @Test
    fun portrait_fillsHeightWithoutOverflow() {
        val r = portrait()
        // 填满条件：三行行框 + 上下各一个 padding = 可用高度。
        // 注意"可见留白"不是额外占位 —— 它由 padding 加字形自带的内空白构成。
        val rows = ClockLayout.PORTRAIT_LINE_COUNT * ClockLayout.LINE_HEIGHT_RATIO
        val padding = 2f * (ClockLayout.COLON_INK_RATIO - ClockLayout.DIGIT_SIDE_INK_RATIO)
        val total = r.fontSizeSp * (rows + padding)
        val info = "font=${r.fontSizeSp} margin=${r.marginDp} used=$total/$portraitH"
        assertTrue("竖屏高度溢出: $info", total <= portraitH + 0.5f)
        assertTrue("竖屏高度利用不足（应填满 95% 以上）: $info", total >= portraitH * 0.95f)
    }

    @Test
    fun landscape_fillsWidthWithoutOverflow() {
        val r = landscape()
        // 填满条件：一行 advance 占位 + 左右各一个 padding = 可用宽度
        val advance = ClockLayout.LANDSCAPE_DIGIT_COUNT * ClockLayout.DIGIT_ADVANCE_RATIO +
            ClockLayout.LANDSCAPE_COLON_COUNT * ClockLayout.COLON_ADVANCE_RATIO +
            ClockLayout.LANDSCAPE_GAP_SEGMENTS * ClockLayout.COLON_GAP_RATIO
        val padding = 2f * (ClockLayout.COLON_INK_RATIO - ClockLayout.DIGIT_SIDE_INK_RATIO)
        val total = r.fontSizeSp * (advance + padding)
        val info = "font=${r.fontSizeSp} margin=${r.marginDp} used=$total/$landscapeW"
        assertTrue("横屏宽度溢出: $info", total <= landscapeW + 0.5f)
        assertTrue("横屏宽度利用不足（应填满 95% 以上）: $info", total >= landscapeW * 0.95f)
    }

    @Test
    fun portrait_widthDoesNotOverflow() {
        val r = portrait()
        val w = (ClockLayout.PORTRAIT_DIGIT_COUNT * ClockLayout.DIGIT_INK_RATIO) * r.fontSizeSp +
            2f * r.marginDp
        assertTrue("竖屏宽度溢出: $w / $portraitW", w <= portraitW + 0.5f)
    }

    @Test
    fun fontSize_isClampedIntoAllowedRange() {
        assertEquals(ClockLayout.MIN_FONT_SIZE, ClockLayout.compute(40f, 40f, false).fontSizeSp, 0.01f)
        assertEquals(ClockLayout.MAX_FONT_SIZE, ClockLayout.compute(4000f, 4000f, false).fontSizeSp, 0.01f)
    }

    /** 回归：字体度量必须来自轮廓实测，冒号笔迹明显窄于数字。 */
    @Test
    fun fontMetricsMatchMeasuredOutline() {
        assertEquals(0.816f, ClockLayout.DIGIT_ADVANCE_RATIO, 0.001f)
        assertEquals(0.618f, ClockLayout.DIGIT_INK_RATIO, 0.001f)
        assertEquals(0.124f, ClockLayout.COLON_INK_RATIO, 0.001f)
        assertEquals(0.099f, ClockLayout.DIGIT_SIDE_INK_RATIO, 0.001f)
        assertTrue("冒号笔迹应窄于数字笔迹", ClockLayout.COLON_INK_RATIO < ClockLayout.DIGIT_INK_RATIO)
        assertTrue("数字笔迹应窄于其内框", ClockLayout.DIGIT_INK_RATIO < ClockLayout.DIGIT_ADVANCE_RATIO)
    }
}
