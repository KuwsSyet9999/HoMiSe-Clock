"""Replace the Canvas-based tilde backdrop with a two-Text stack.

Why the Canvas version drifted:
  * Text uses textAlign = Center inside a wrapContentWidth(unbounded) box, so the glyphs
    do not start at x = 0 -- but the Canvas painted from x = 0.
  * lineHeight differed (Unspecified vs the Text default), shifting the baseline.

A second Text carrying the same string (with every character except `.` and `:` replaced
by `~`) inherits the exact same alignment, line height and metrics, so it lines up by
construction. Measured advances: every character is 816 except `:` (200) and `.` (0),
so the substitution does not change the total width at all.
"""
import io
import re

PATH = r"D:\DSHin\HoMiSe\app\src\main\kotlin\com\homise\clock\ClockScreen.kt"

HELPER = '''
/**
 * 调试铺底用的字符串：除 `.` 和 `:` 外，每个字符都换成 `~`。
 *
 * 字体里除这两个符号外，所有字符的 advance 都是 816（含 `_`、`-`、`+`、`(`、`)`、`%`
 * 与全部字母数字），所以替换后**总宽度完全不变**。保留 `.` 与 `:` 是为了让它们的位置
 * 在被铺底时依然可见——它们是零宽/窄宽字符，换成 `~` 反而会把版面撑开。
 */
private fun tildeFrame(text: String): String = buildString(text.length) {
    for (c in text) append(if (c == '.' || c == ':') c else '~')
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
    font: FontFamily,
    fontSize: TextUnit,
    color: Color,
    frameColor: Color,
    modifier: Modifier = Modifier,
    textAlign: TextAlign? = null,
    onTextLayout: ((TextLayoutResult) -> Unit)? = null,
) {
    Box(modifier = modifier) {
        if (BuildConfig.DEBUG) {
            Text(
                text = tildeFrame(text),
                fontFamily = font,
                fontSize = fontSize,
                color = frameColor,
                maxLines = 1,
                softWrap = false,
                textAlign = textAlign,
            )
        }
        Text(
            text = text,
            fontFamily = font,
            fontSize = fontSize,
            color = color,
            maxLines = 1,
            softWrap = false,
            textAlign = textAlign,
            onTextLayout = onTextLayout ?: {},
        )
    }
}
'''


def main():
    t = io.open(PATH, encoding="utf-8").read()
    orig = t

    # 1) remove the old Canvas helper
    t, n_old = re.subn(
        r"/\*\*\n \* 调试用：在每个字符位下方铺一个 `~` 全亮字形.*?\n\}\n",
        "",
        t,
        flags=re.S,
    )
    print("  old helper removed:", n_old)

    # 2) add the new helpers before hitModifier
    anchor = "private fun hitModifier("
    t = t.replace(anchor, HELPER.lstrip("\n") + "\n" + anchor, 1)
    print("  new helpers inserted")

    io.open(PATH, "w", encoding="utf-8", newline="").write(t)
    print("changed:", t != orig, " lines:", len(t.splitlines()))


if __name__ == "__main__":
    main()
