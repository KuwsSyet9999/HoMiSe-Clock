package com.homise.clock

/**
 * 时钟布局的尺寸计算（纯函数，便于单元测试精确验证）。
 *
 * ## 版面基准：冒号「:」
 *
 * 四周留白 = **一个冒号的笔迹宽度**（`COLON_INK_RATIO`）。
 * 用笔迹而非 advance 作基准，是因为 advance 内框含大量空白（数字 advance 0.816em，
 * 笔迹仅 0.618em），按内框留白会让四周显得过空、数字偏小。
 *
 * ## 两种口径必须分清
 *
 * 屏幕上真正看得见的是**笔迹（ink）**，但排版占位走的是 **advance**：
 *
 * | 用途 | 口径 |
 * | --- | --- |
 * | 一行/一列能否放下 | advance |
 * | 留白、可见间隙 | ink |
 *
 * 实测度量（`hsseg_7_classic_regular.ttf`，unitsPerEm 1000）：
 *
 * | 字形 | advance | 笔迹 x 范围 | 左右内空白 |
 * | --- | --- | --- | --- |
 * | 数字 | 0.816em | [99, 717] | 各 0.099em |
 * | 冒号 | 0.200em | [38, 162] | 各 0.038em |
 *
 * 由此可得两个"天然视觉间隙"：
 *   - 同组两位数字之间：`2 × 0.099 = 0.198em`
 *   - 冒号与相邻数字之间（占位紧邻时）：`0.099 + 0.038 = 0.137em`
 */
object ClockLayout {

    /** 数字 advance（内框宽）。 */
    const val DIGIT_ADVANCE_RATIO = 0.816f

    /** 数字笔迹宽度（717−99）。 */
    const val DIGIT_INK_RATIO = 0.618f

    /** 数字笔迹左侧内空白（xMin=99），两侧相同。 */
    const val DIGIT_SIDE_INK_RATIO = 0.099f

    /** 冒号 advance。 */
    const val COLON_ADVANCE_RATIO = 0.2f

    /** 冒号笔迹宽度（162−38）—— 四周留白的基准。 */
    const val COLON_INK_RATIO = 0.124f

    /**
     * 半个冒号笔迹宽 —— 数字**可见笔迹**与挖孔（刘海/打孔）之间要保持的间距。
     * 挖孔区不可绘制，故与它的间距按半个冒号宽计，比普通边距更紧凑。
     */
    const val HALF_COLON_INK_RATIO = COLON_INK_RATIO / 2f

    /** 冒号笔迹左侧内空白（xMin=38）。 */
    const val COLON_SIDE_INK_RATIO = 0.038f

    /**
     * 单行占位高度相对字号的比值。
     * 数字笔迹高 1.0em，但 Compose 的行框还含少量上下余量，取 1.2 才不至于让相邻两行
     * 的字形互相压住（曾把 1.0 当行高，结果竖屏三行重叠）。
     */
    const val LINE_HEIGHT_RATIO = 1.2f

    /**
     * 横屏「:」两侧附加的组间距（advance 口径）。
     *
     * 固定为 0：曾试图用负值（−0.013em）把可见间隙补偿到恰好一个冒号宽，但 Compose 对负间距
     * 的处理不可靠，实测导致 Row 挤压、秒的两位数字互相堆叠。取消该补偿后布局宽度可精确预测。
     */
    const val COLON_GAP_RATIO = 0f

    /**
     * 竖屏行与行之间的**附加**间距，取 0。
     *
     * 行间可见间隙已经由行框自带：LINE_HEIGHT_RATIO = 1.2em 而数字笔迹仅 1.0em，
     * 行框上下各留 0.1em，两行相邻时天然形成 0.2em ≈ 2×0.099em 的可见间隙，
     * 与行内两位数字之间的间隙一致 —— 无需再插入额外间距。
     */
    const val LINE_GAP_RATIO = 0f

    /** 横屏一行：6 位数字（3 组，每组两位）+ 2 个冒号 + 4 段组间距。 */
    const val LANDSCAPE_PAIR_COUNT = 3
    const val LANDSCAPE_DIGIT_COUNT = 6
    const val LANDSCAPE_COLON_COUNT = 2
    const val LANDSCAPE_GAP_SEGMENTS = 4

    /** 竖屏每行 2 位数字，共 3 行。 */
    const val PORTRAIT_DIGIT_COUNT = 2
    const val PORTRAIT_LINE_COUNT = 3

    const val MIN_FONT_SIZE = 20f
    const val MAX_FONT_SIZE = 400f

    /**
     * 字号安全余量。
     *
     * 取 0.995：内容必须**接近填满**可用空间（留出余量会让居中排列把剩余空间分到两侧、
     * 可见留白变大），但也不能零余量 —— 零余量时横屏最后一个 Text 会因组件宽度之和
     * 略大于整串测量值而约束不足，导致 `Text("29")` 换行、秒的两位上下叠放。
     */
    const val FONT_SAFETY = 0.995f

    /** 一次布局推算的结果（全部为 dp）。 */
    data class Result(
        val fontSizeSp: Float,
        /** 实际施加的 padding：已扣掉字形内空白 */
        val marginDp: Float,
        /** 屏幕边到数字可见笔迹边缘的距离 = 一个冒号笔迹宽 */
        val visibleMarginDp: Float,
        /** 竖屏行与行之间的附加间距 */
        val lineGapDp: Float,
    )

    /**
     * 推算字号与留白。
     *
     * 留白口径：**屏幕边到数字「可见笔迹」边缘 = 一个冒号笔迹宽**。
     *
     * 数字字形框自带 0.099em 的左右内空白，若把留白锚在字形框上（padding = 0.124em），
     * 眼睛看到的留白会变成 0.124 + 0.099 ≈ 0.223em，观感偏大且横竖不一致。
     * 因此这里把 padding 扣掉内空白，使**可见留白**恰为一个冒号笔迹宽：
     * `padding = COLON_INK_RATIO − DIGIT_SIDE_INK_RATIO = 0.025em`
     */
    /**
     * 字体实测度量（全部相对字号）。默认值是按字体表推算，运行时应以 TextMeasurer 实测覆盖。
     *
     * [lineBoxRatio] 必须与实际渲染所用的 `lineHeight` 一致：若测量时用字体默认行高、
     * 渲染时又设了 `lineHeight`，测得的行高会偏小，竖屏将按错误行高算出过大字号而**越界**。
     */
    data class Metrics(
        /** 单个数字的推进宽度 */
        val digitRatio: Float,
        /** 一组两位数字的宽度 */
        val digitPairRatio: Float,
        /** 冒号宽度 */
        val colonRatio: Float,
        /** 单行行框高度（含 lineHeight 设置） */
        val lineBoxRatio: Float,
    ) {
        companion object {
            /** 按字体表推算的理论值，用于单元测试与兜底 */
            val Theoretical = Metrics(
                digitRatio = DIGIT_ADVANCE_RATIO,
                digitPairRatio = 2f * DIGIT_ADVANCE_RATIO,
                colonRatio = COLON_ADVANCE_RATIO,
                lineBoxRatio = LINE_HEIGHT_RATIO,
            )
        }
    }

    /** 横屏内容宽度（相对字号）。 */
    fun landscapeContentRatio(m: Metrics = Metrics.Theoretical): Float =
        // 按**实际组件划分**累加：横屏是 3 个「两位数字」Text + 2 个冒号 Text，
        // 而不是 6 个单数字。两位数字的实测宽度未必恰好等于单数字的两倍（字距可能不同），
        // 按组件口径累加才与真实排版一致。
        LANDSCAPE_PAIR_COUNT * m.digitPairRatio +
            LANDSCAPE_COLON_COUNT * m.colonRatio +
            LANDSCAPE_GAP_SEGMENTS * COLON_GAP_RATIO

    /** 竖屏内容宽度（每行两位数字）。 */
    fun portraitContentRatio(m: Metrics = Metrics.Theoretical): Float =
        PORTRAIT_DIGIT_COUNT * m.digitRatio

    /** 按字体表推算的横屏整行宽度，供诊断显示与对照。 */
    fun theoreticalLandscapeContentRatio(): Float = landscapeContentRatio(Metrics.Theoretical)

    /**
     * 推算字号与留白。
     *
     * 宽度与高度**双向取小**，避免任一方向越界：
     *   - 横屏通常受宽度约束，但屏幕很矮时行框会超出屏高；
     *   - 竖屏通常受高度约束，但极窄屏会横向超出屏宽。
     */
    fun compute(
        widthDp: Float,
        heightDp: Float,
        isLandscape: Boolean,
        metrics: Metrics = Metrics.Theoretical,
    ): Result {
        // 可见留白（屏幕边 → 数字笔迹边缘）
        val visibleMargin = COLON_INK_RATIO
        // 排版占位（padding）需扣掉字形自带的内空白，使可见留白等于上面那个值
        val paddingRatio = (COLON_INK_RATIO - DIGIT_SIDE_INK_RATIO).coerceAtLeast(0f)

        val contentW = if (isLandscape) landscapeContentRatio(metrics) else portraitContentRatio(metrics)
        val contentH = if (isLandscape) {
            metrics.lineBoxRatio
        } else {
            // 竖屏三行行框；行间距不再单独计入 —— 行框高度已含笔迹上下的自带留白，
            // 两行相邻时天然形成约 0.2em 可见间隙，恰等于行内两位数字之间的间距。
            PORTRAIT_LINE_COUNT * metrics.lineBoxRatio
        }

        val byWidth = widthDp / (contentW + 2f * paddingRatio)
        val byHeight = heightDp / (contentH + 2f * paddingRatio)
        val raw = minOf(byWidth, byHeight)

        // 注意：这里只留 FONT_SAFETY 的微小余量。此前曾对横屏额外收紧 2% 来掩盖
        // TextMeasurer 宽度测量偏小的问题，但那会让数字整体变小、离留白线更远。
        // 正确做法是由调用方用渲染后实测的宽度迭代校正字号（见 ClockScreen），
        // 使内容恰好顶到留白边界。
        val fontSize = (raw * FONT_SAFETY).coerceIn(MIN_FONT_SIZE, MAX_FONT_SIZE)

        return Result(
            fontSizeSp = fontSize,
            // 实际 padding：扣掉字形内空白，使可见留白恰好等于一个冒号笔迹宽
            marginDp = fontSize * paddingRatio,
            // 可见留白，仅供界面核对与调试显示
            visibleMarginDp = fontSize * visibleMargin,
            // 附加行间距为 0：行间可见间隙由行框自带留白形成
            lineGapDp = fontSize * LINE_GAP_RATIO,
        )
    }
}
