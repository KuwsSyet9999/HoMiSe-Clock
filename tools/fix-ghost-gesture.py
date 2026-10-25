"""Make the ghost toggle actually fire, and add diagnostics for it.

Root cause: the root BoxWithConstraints unconditionally routed every double-tap to the
colour swap, and the child digits' own pointerInput never won the gesture. Instead of
fighting Compose's gesture priority, the root now receives the tap *with its position*
and decides:

  * inside the clock digits rect -> toggle ghost
  * anywhere else                -> swap colours

The digits' own pointerInput handlers are removed. Diagnostics gain the ghost state,
a double-tap counter, which branch was taken, and the digits rect.
"""
import io
import re

PATH = r"D:\DSHin\HoMiSe\app\src\main\kotlin\com\homise\clock\ClockScreen.kt"


def main():
    t = io.open(PATH, encoding="utf-8").read()
    orig = t

    # ---- 1) root gesture: position-aware double tap ----
    t = t.replace(
        """                    onDoubleTap = { onToggleColors() },""",
        """                    onDoubleTap = { at ->
                        // 双击落在时钟数字区 -> 切换灰底；落在背景 -> 互换配色。
                        // 放在根层统一判断，避免子级手势被父级吞掉。
                        val r = clockDigitsRect
                        val inside = r != null && r.contains(at)
                        dblTapCount++
                        dblTapLast = if (inside) "clock->ghost" else "bg->colors"
                        if (inside) onToggleGhost() else onToggleColors()
                    },""", 1)

    # ---- 2) digits rect state ----
    t = t.replace(
        """    val colors = if (colorsInverted) LightClockColors else DarkClockColors""",
        """    val colors = if (colorsInverted) LightClockColors else DarkClockColors
    // 时钟数字区的点击矩形（根坐标系，px）：用于区分"双击数字"与"双击背景"
    var clockDigitsRect by remember { mutableStateOf<Rect?>(null) }
    // 诊断：双击次数与最后一次落点判定
    var dblTapCount by remember { mutableStateOf(0) }
    var dblTapLast by remember { mutableStateOf("-") }""", 1)

    # ---- 3) remove the child pointerInput from both clock composables ----
    t = t.replace(
        """    Box(
        // 双击数字区切换灰底；子级先于根 Box 收到事件并消费，
        // 所以不会同时触发根上的"双击换配色"
        modifier = modifier.pointerInput(Unit) {
            detectTapGestures(onDoubleTap = { onToggleGhost() })
        },
        contentAlignment = Alignment.Center,
    ) {""",
        """    Box(modifier = modifier, contentAlignment = Alignment.Center) {""", 1)

    t = t.replace(
        """    Box(
        modifier = modifier.pointerInput(Unit) {
            detectTapGestures(onDoubleTap = { onToggleGhost() })
        },
        contentAlignment = Alignment.Center,
    ) {
        // 底层：灰色全亮字形（双击数字区可关闭，只看纯亮段）""",
        """    Box(modifier = modifier, contentAlignment = Alignment.Center) {
        // 底层：灰色全亮字形（双击数字区可关闭，只看纯亮段）""", 1)

    # ---- 4) record the digits rect in root coordinates ----
    t = t.replace(
        """                        .onGloballyPositioned { coords ->
                            val r = coords.boundsInParent()
                            contentTopDp = r.top / probeDensity.density
                            contentBottomDp = r.bottom / probeDensity.density
                            // 这里顺带记录布局实测宽度，供字号实战校准使用
                            landscapeWidthDp = coords.size.width / probeDensity.density
                        },""",
        """                        .onGloballyPositioned { coords ->
                            val r = coords.boundsInParent()
                            contentTopDp = r.top / probeDensity.density
                            contentBottomDp = r.bottom / probeDensity.density
                            // 这里顺带记录布局实测宽度，供字号实战校准使用
                            landscapeWidthDp = coords.size.width / probeDensity.density
                            clockDigitsRect = r
                        },""", 1)

    t = t.replace(
        """                        .onGloballyPositioned { coords ->
                            val r = coords.boundsInParent()
                            contentTopDp = r.top / probeDensity.density
                            contentBottomDp = r.bottom / probeDensity.density
                        },""",
        """                        .onGloballyPositioned { coords ->
                            val r = coords.boundsInParent()
                            contentTopDp = r.top / probeDensity.density
                            contentBottomDp = r.bottom / probeDensity.density
                            clockDigitsRect = r
                        },""", 1)

    io.open(PATH, "w", encoding="utf-8", newline="").write(t)
    print("changed:", t != orig, " lines:", len(t.splitlines()))


if __name__ == "__main__":
    main()
