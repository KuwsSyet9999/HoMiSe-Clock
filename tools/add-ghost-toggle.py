"""Add the ghost-background toggle.

Double-tap on the clock digits flips the ghost layer; double-tap on the background
elsewhere keeps swapping the colour scheme. Defaults put the ghost on:
  * clock   : ghost (dimmed full-lit glyph) visible, digits white
  * info    : text white, ghost frame visible
After a double-tap on the digits:
  * clock   : ghost hidden
  * info    : text turns dimmed, ghost frame hidden
"""
import io
import re

PATH = r"D:\DSHin\HoMiSe\app\src\main\kotlin\com\homise\clock\ClockScreen.kt"

# 1) ClockScreen signature
SIG_OLD = """    /** 是否启用等宽小写（双击字体名块切换） */
    monoLowercase: Boolean = false,"""
SIG_NEW = """    /** 是否显示灰底（双击时钟数字区切换；默认显示） */
    ghostVisible: Boolean = true,
    /** 切换灰底的回调 */
    onToggleGhost: () -> Unit = {},
    /** 是否启用等宽小写（双击字体名块切换） */
    monoLowercase: Boolean = false,"""

# 2) InfoText gains showFrame
INFOTEXT_OLD = """    modifier: Modifier = Modifier,
    maxLines: Int = 1,
    softWrap: Boolean = false,
    textAlign: TextAlign? = null,
    onTextLayout: ((TextLayoutResult) -> Unit)? = null,
) {
    Box(modifier = modifier) {
        if (BuildConfig.DEBUG) {"""
INFOTEXT_NEW = """    modifier: Modifier = Modifier,
    /** 是否铺描灰色字框；由灰底开关控制，与调试无关 */
    showFrame: Boolean = true,
    maxLines: Int = 1,
    softWrap: Boolean = false,
    textAlign: TextAlign? = null,
    onTextLayout: ((TextLayoutResult) -> Unit)? = null,
) {
    Box(modifier = modifier) {
        if (showFrame) {"""


def main():
    t = io.open(PATH, encoding="utf-8").read()
    orig = t

    # ClockScreen 签名
    if SIG_OLD in t:
        t = t.replace(SIG_OLD, SIG_NEW, 1)
    else:
        print("!! signature anchor missing")

    # InfoText：showFrame 取代 DEBUG 判断
    if INFOTEXT_OLD in t:
        t = t.replace(INFOTEXT_OLD, INFOTEXT_NEW, 1)
    else:
        print("!! InfoText anchor missing")

    # 5 个 InfoText 调用补 showFrame
    t = re.sub(r"(InfoText\(\n)(\s+)", lambda m: m.group(1) + m.group(2) + "showFrame = ghostVisible,\n" + m.group(2), t)

    # 信息文字颜色：白 ↔ 灰
    t = t.replace("            color = colors.digits,\n            frameColor = colors.dimmed,",
                  "            color = if (ghostVisible) colors.digits else colors.label,\n"
                  "            frameColor = colors.dimmed,")

    # 时钟组件加 showGhost
    t = t.replace("""private fun LandscapeClock(
    time: ClockTime,
    fontSize: TextUnit,
    color: Color,
    ghostDigit: Char,
    modifier: Modifier = Modifier,
) {
    // 底数由当前族的全亮字形重复而成：7 段为 "88"，14 段为 "~~"
    val ghost = ghostDigit.toString().repeat(2)
    Box(modifier = modifier, contentAlignment = Alignment.Center) {
        // 底层：灰色全亮字形，冒号常亮（使冒号熄灭时同样显示为灰色）
        LandscapeRow(ghost, ghost, ghost, fontSize, LocalClockColors.current.dimmed, colonVisible = true)""",
"""private fun LandscapeClock(
    time: ClockTime,
    fontSize: TextUnit,
    color: Color,
    ghostDigit: Char,
    showGhost: Boolean,
    modifier: Modifier = Modifier,
) {
    // 底数由当前族的全亮字形重复而成：7 段为 "88"，14 段为 "~~"
    val ghost = ghostDigit.toString().repeat(2)
    Box(modifier = modifier, contentAlignment = Alignment.Center) {
        // 底层：灰色全亮字形，冒号常亮（使冒号熄灭时同样显示为灰色）
        // 双击数字区可关闭这一层（只看纯亮段）
        if (showGhost) {
            LandscapeRow(ghost, ghost, ghost, fontSize, LocalClockColors.current.dimmed, colonVisible = true)
        }""")

    t = t.replace("""private fun PortraitClock(
    time: ClockTime,
    fontSize: TextUnit,
    color: Color,
    ghostDigit: Char,""",
"""private fun PortraitClock(
    time: ClockTime,
    fontSize: TextUnit,
    color: Color,
    ghostDigit: Char,
    showGhost: Boolean,""")

    io.open(PATH, "w", encoding="utf-8", newline="").write(t)
    print("changed:", t != orig, " lines:", len(t.splitlines()))


if __name__ == "__main__":
    main()
