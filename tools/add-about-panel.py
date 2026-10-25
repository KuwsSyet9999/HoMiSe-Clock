"""Add the long-press "about" panel on the version block.

Content is user-facing only: what the app is, and how to drive it. Dismissable by the
corner X or a tap anywhere outside the card. Layout is tuned to fit one screen.
"""
import io

PATH = r"D:\DSHin\HoMiSe\app\src\main\kotlin\com\homise\clock\ClockScreen.kt"

PANEL = '''
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
    // 遮罩本身可点击，点击即关闭
    Box(
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
                .widthIn(max = 360.dp)
                .fillMaxWidth(0.86f)
                // 卡片自身吞掉点击，避免穿透到遮罩
                .pointerInput(Unit) { detectTapGestures(onTap = {}) }
                .background(colors.background)
                .border(1.dp, colors.dimmed, RoundedCornerShape(10.dp))
                .padding(horizontal = 18.dp, vertical = 14.dp),
        ) {
            Column {
                // 标题行：应用名 + 右上角关闭
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.Top,
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "HoMiSe · 时分秒",
                            color = colors.digits,
                            fontSize = 17.sp,
                            fontWeight = FontWeight.SemiBold,
                        )
                        Text(
                            text = "版本 " + BuildConfig.DISPLAY_VERSION + BUILD_TAG,
                            color = colors.dimmed,
                            fontSize = 12.sp,
                        )
                    }
                    CloseBox(onDismiss)
                }

                Spacer(Modifier.height(10.dp))
                Text(
                    text = "全屏常亮、纯黑底的数码管时钟。不联网、不申请任何权限、不打扰。",
                    color = colors.label,
                    fontSize = 12.sp,
                    lineHeight = 17.sp,
                )

                Spacer(Modifier.height(12.dp))
                SectionTitle("怎么用", colors)
                Spacer(Modifier.height(4.dp))
                val gestures = listOf(
                    "单击背景" to "重播信息提示",
                    "双击时钟" to "开关灰色底衬",
                    "双击背景" to "黑白配色互换",
                    "双击字体名" to "小写等宽开关",
                    "单击信息块" to "该块常驻显示",
                    "长按背景" to "最高亮度",
                    "左右滑动" to "换字体风格",
                    "上下滑动" to "换字重与倾斜",
                )
                gestures.forEach { (k, v) ->
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(vertical = 1.5.dp),
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

                Spacer(Modifier.height(10.dp))
                SectionTitle("其他", colors)
                Spacer(Modifier.height(4.dp))
                AboutRow("长按版本号", "打开本页", colors)
                AboutRow("桌面图标", "随字体 / 配色 / 底衬更新，需离开应用后生效", colors)

                Spacer(Modifier.height(14.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.End,
                ) {
                    ResetButton(onResetDefaults, colors)
                }
            }
        }
    }
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
private fun AboutRow(key: String, value: String, colors: ClockColors) {
    Row(modifier = Modifier.fillMaxWidth().padding(vertical = 1.5.dp)) {
        Text(text = key, color = colors.label, fontSize = 12.sp, modifier = Modifier.width(88.dp))
        Text(text = value, color = colors.digits, fontSize = 12.sp, modifier = Modifier.weight(1f))
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
        Text(text = "\\u00D7", color = colors.digits, fontSize = 16.sp)
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
'''


def main():
    t = io.open(PATH, encoding="utf-8").read()
    orig = t

    # 1) 插入面板组件（放在 hitModifier 之前）
    if "fun androidx.compose.foundation.layout.BoxScope.AboutPanel" not in t:
        anchor = "private fun hitModifier("
        t = t.replace(anchor, PANEL.lstrip("\n") + "\n" + anchor, 1)
        print("  AboutPanel inserted")

    # 2) 版本号块加长按，打开面板
    t = t.replace(
        ".then(hitModifier(pinVersion, phase) { pinVersion = !pinVersion }),",
        ".then(\n"
        "                    hitModifier(\n"
        "                        pinned = pinVersion,\n"
        "                        phase = phase,\n"
        "                        onLongPress = { showAbout = true },\n"
        "                    ) { pinVersion = !pinVersion },\n"
        "                ),",
        1,
    )

    # 3) hitModifier 增加 onLongPress
    t = t.replace(
        """private fun hitModifier(
    pinned: Boolean,
    phase: InfoPhase,
    onDoubleTap: (() -> Unit)? = null,
    onTap: () -> Unit,
): Modifier =""",
        """private fun hitModifier(
    pinned: Boolean,
    phase: InfoPhase,
    onDoubleTap: (() -> Unit)? = null,
    onLongPress: (() -> Unit)? = null,
    onTap: () -> Unit,
): Modifier =""",
        1,
    )
    t = t.replace(
        """            detectTapGestures(
                onTap = { onTap() },
                onDoubleTap = onDoubleTap?.let { cb -> { _: Offset -> cb() } },
            )""",
        """            detectTapGestures(
                onTap = { onTap() },
                onDoubleTap = onDoubleTap?.let { cb -> { _: Offset -> cb() } },
                onLongPress = onLongPress?.let { cb -> { _: Offset -> cb() } },
            )""",
        1,
    )

    io.open(PATH, "w", encoding="utf-8", newline="").write(t)
    print("changed:", t != orig)


if __name__ == "__main__":
    main()
