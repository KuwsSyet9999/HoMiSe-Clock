"""Replace the flat grey plate with a per-character `~` frame.

The plate only marked the text box; what is actually needed is the 16-segment glyph
frame underneath every character, so any horizontal drift of the glyph is visible
against it. Each `~` is drawn at the character's own start x, so the frames line up
with the glyphs they sit behind.

Applied only in debug builds.
"""
import io
import re

PATH = r"D:\DSHin\HoMiSe\app\src\main\kotlin\com\homise\clock\ClockScreen.kt"

HELPER = '''
/**
 * 调试用：在每个字符位下方铺一个 `~` 全亮字形（16 段），作为字形对照框。
 *
 * 为什么不是统一的一块灰底：灰底只能标出文字区域，看不出**单个字形**相对字框的偏移。
 * `~` 是 16 段全亮字形，它的左右竖、上下横就是完整的字形框，任何水平漂移一眼可见。
 *
 * 每个 `~` 都画在该字符自己的起始 x 上，因此宽字符（数字 816）和窄字符（冒号 200）
 * 都能各自对齐；`~` 本身固定 816 宽，窄字符位会与相邻的框重叠，这是预期效果。
 */
private fun Modifier.tildeBackdrop(
    text: String,
    font: FontFamily,
    fontSize: TextUnit,
    lineHeight: TextUnit,
    color: Color,
    measurer: TextMeasurer,
): Modifier = this.drawBehind {
    if (text.isEmpty()) return@drawBehind
    val style = TextStyle(
        fontFamily = font,
        fontSize = fontSize,
        lineHeight = lineHeight,
        platformStyle = PlatformTextStyle(includeFontPadding = false),
    )
    val tilde = measurer.measure(AnnotatedString("~"), style, softWrap = false, maxLines = 1)
    var x = 0f
    for (c in text) {
        drawText(tilde, topLeft = Offset(x, 0f), color = color)
        val w = measurer.measure(
            AnnotatedString(c.toString()), style, softWrap = false, maxLines = 1,
        ).size.width
        x += w.toFloat()
    }
}
'''


def main():
    t = io.open(PATH, encoding="utf-8").read()

    # 1) drop the grey plate
    t, n_plate = re.subn(r"\n *\.background\(colors\.dimmed\.copy\(alpha = 0\.55f\)\)", "", t)
    print("  plates removed:", n_plate)

    # 2) insert helper before hitModifier
    anchor = "private fun hitModifier("
    t = t.replace(anchor, HELPER.lstrip("\n") + "\n" + anchor, 1)

    # 3) collect the TextMeasurer once inside the overlay
    t = t.replace(
        "    val density = LocalDensity.current\n    val alpha = remember { Animatable(0f) }",
        "    val density = LocalDensity.current\n"
        "    val tildeMeasurer = rememberTextMeasurer()\n"
        "    val alpha = remember { Animatable(0f) }",
        1,
    )

    io.open(PATH, "w", encoding="utf-8", newline="").write(t)
    print("  helper inserted, measurer added")


if __name__ == "__main__":
    main()
