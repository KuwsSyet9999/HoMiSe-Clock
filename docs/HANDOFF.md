# HoMiSe 交接文档

> 本文件用于在新对话窗口中接手本项目。最后更新于 `1.0.0`。

---

## 一、项目概况

| 项 | 值 |
| --- | --- |
| 项目路径 | `D:\DSHin\HoMiSe` |
| 仓库 | <https://github.com/KuwsSyet9999/HoMiSe-Clock>（公开，代码 MIT，字体 OFL 1.1） |
| 应用 | Android 数码管时钟「时分秒 / HoMiSe」 |
| 技术栈 | Kotlin + Jetpack Compose (BOM 2024.09.00)、AGP 8.7.3、Kotlin 2.0.20、Gradle 8.9、JDK 17 |
| SDK | compileSdk / targetSdk 35，minSdk 26 |
| 当前版本 | **`1.0.0`**（正式版，2026-10-26 导出），versionCode `1000001` |
| 最近产物 | `release/HoMiSe_1.0.0_20261026042354_cb1637750348b2a2.APK`（2.57 MB，发布密钥签名） |

---

## 二、已完成：面板调整（`0.3.2.31` ~ `0.3.2.35`）

需求逐条实施，每轮均在 MuMu（1080×1920 / 480dpi → 360×640dp 竖屏、640×360dp 横屏）实测：

| # | 要求 | 实施结果 |
| --- | --- | --- |
| 1 | 去掉「检查更新」按钮 | 已删除 `UpdateButton` composable 及版本行的调用 |
| 2 | 「恢复默认设置」移到版本号后面 | 已从标题行移到版本行，紧跟版本号 |
| 3 | 仓库地址的显示位置 | 横屏接在「时分秒(HoMiSe)」后面；竖屏另起一行并**独占整行**。竖屏若放在标题行的 `weight` 列里会被右侧 × 挤到约 238dp，而 10sp 地址约需 306dp，必然折行 |
| 4 | 竖屏地址不得折行 | 新增 `RepoUrlLine`：先按 10sp 实测宽度，再按可用宽度等比缩小字号（0.98 余量），横竖屏都保持单行 |
| 5 | 面板被裁 | 卡片限高（`heightIn(max = maxHeight - 16.dp)`）并内部滚动兜底；间距各压缩 2~4dp |
| 6 | 调试诊断压住面板 | 面板打开时隐藏诊断（`showDiagnostics && !showAbout`），仅调试包可见 |
| 7 | 「怎么用」改「操作」、内部两列 | 标题改名；竖屏用两列 × 上下两行（`StackedEntry`），每列约 129dp 恰好容纳 6 字说明，说明不再被挤成两三行 |
| 8 | 「其他」也两列，加「竖屏状态 / 只显示时钟」 | 横屏第一行两列（左「长按版本号」、右「竖屏状态」），竖屏两列 × 上下两行；「桌面图标」说明较长，横竖屏都独占整行 |
| 9 | 描述列对齐 | 横屏「操作」的键宽由 78dp 改为 88dp，与 `AboutRow` 一致；否则两段的说明列相差 10dp。竖屏两段都用 `StackedEntry`，说明从列首开始，本就对齐 |

**横屏面板（640×360dp 实测）**：

```
时分秒(HoMiSe)  https://github.com/KuwsSyet9999/HoMiSe-Clock   [×]
版本 0.3.2.x(CS)  [恢复默认设置]
纯净的数码管风格时钟。
操作
  单击背景    重播信息提示      单击信息块  该块常驻显示
  双击时钟    开关灰色底衬      长按背景    开关最高亮度
  双击背景    黑白配色互换      左右滑动    换字体风格
  双击字体名  小写等宽开关      上下滑动    换字重与倾斜
其他
  长按版本号  打开本页          竖屏状态    只显示时钟
  桌面图标    随字体/配色/底衬更新，返回桌面后生效
```

**竖屏面板（360×640dp 实测，横屏打开后旋转）**：

```
时分秒(HoMiSe)                                   [×]
https://github.com/KuwsSyet9999/HoMiSe-Clock        ← 单行、字号按宽度缩放
版本 0.3.2.x(CS)  [恢复默认设置]
纯净的数码管风格时钟。
操作
  单击背景        单击信息块
  重播信息提示    该块常驻显示
  双击时钟        长按背景
  开关灰色底衬    开关最高亮度
  双击背景        左右滑动
  黑白配色互换    换字体风格
  双击字体名      上下滑动
  小写等宽开关    换字重与倾斜
其他
  长按版本号      竖屏状态
  打开本页        只显示时钟
  桌面图标
  随字体 / 配色 / 底衬更新，返回桌面后生效
```

**位置**：`ClockScreen.kt` 的 `AboutPanel`、`RepoUrlLine`、`StackedEntry`、`ResetButton`，常量 `REPO_URL`。

**说明**：竖屏不渲染 `InfoOverlay`（无版本号块），面板只能在横屏长按版本号打开；旋转到竖屏后 Compose 重组保留 `showAbout`，因此竖屏面板可见但无入口。仓库地址已指向正式仓库（2026-10-26 创建并发布 `1.0.0`），点击可跳转。

---

## 三、已确立的规范与约定

### 3.1 版本号

- 格式：`主版本号.子版本号.末版本号.迭代序号`
- 内部迭代只加第 4 位；正式导出需用户明确确认版本号
- `versionCode = major*1_000_000 + minor*10_000 + patch*100 + 1 + iteration`
- `versionName`：release 为 `x.y.z`，debug 为 `x.y.z-internal`（**debug 不带迭代号**）
- 导出文件名：`HoMiSe_<版本>_<14位导出时间>_<sha256前16位>.APK`

### 3.2 构建与导出

**必须用 Python 脚本，不要用 `.ps1`**：

```powershell
# 导出内部测试包（自动 bump 迭代号）
python tools\export_apk.py "变更摘要"

# 不 bump，仅重新导出
python tools\export_apk.py --nobump

# 导出正式版（须先由需求方确认版本号；三条命令按序执行）
python tools\export_release.py --version 1.0.0 --bump major --summary "变更摘要"
python tools\archive-release.py

# 上传到 GitHub Releases（在项目根执行；文件名需显式给出，不要用通配符）
gh release create v1.0.0 "release/HoMiSe_1.0.0_<时间>_<哈希>.APK" `
  "release/HoMiSe_1.0.0_<时间>_<哈希>.APK.sha256" `
  --title "HoMiSe 1.0.0" --notes "变更摘要"
```

`gh` 通过 API 上传，不受沙箱 schannel 限制；只有 `git push` 需要
`-c http.sslBackend=openssl` 并重试。README 的「下载」一节指向
`releases/latest`，无需每次改链接。

`export_release.py` 会定格 `version.json`（current / release / history / releases）、构建
`assembleRelease`、校验版本、命名 `HoMiSe_<版本>_<时间>_<哈希>.APK` 并写 `.sha256`；
`archive-release.py` 负责补全 `releases[]` 并追加 `VERSIONING.md` 的发布表行。

**原因**：沙箱把 `pwsh` 限制在 `ConstrainedLanguage`，**禁止执行任何 `.ps1` 文件**。`tools/export-apk.ps1` 与 `version.ps1` 仅作正式发布流程的历史遗留，日常构建走 Python。

**摘要要短、不含 `~`、`[`、`]` 等特殊字符** —— 之前长摘要曾把 `version.json` 写坏过一次。

### 3.3 字体

| 系列 | 资源名 | 字体族名 | 数量 |
| --- | --- | --- | --- |
| 七段 | `hseg_7_*` | `HSEG 7 *` | 24 |
| 十六段（应用中作"十四段"使用） | `hseg_16_*` | `HSEG 16 *` | 24 |

- 资源名曾为 `hsseg_7_*` / `dseg_14_*`，已在 `0.3.2.25` 统一重命名
- 特殊字体未重命名：`dseg_7_seggchan_regular`、`dseg_7_seggchanmini_regular`、`dseg_weather`
- **七段**：无 `~`、无 PUA、无 `%`；全亮字形用 **`8`**；电量用 `.:`
- **十六段**：有 `~`（16 轮廓全亮）、有 `%`、含 PUA `U+E000~U+E019`（小写等宽字形，advance 408）
- 字体显示名由 `ClockFont.fullFontName()` 拼接：
  - 七段 `HSEG7 <variant> <style>`
  - 十六段 `HSEG16 <variant>[ Mono] <style>`
- **Mono 的含义**：调整亮段使小写笔迹"铺满"，**不是**窄版；advance 仍是 816

### 3.4 图标

- **192 个**变体 = 8 字体族 × 6 样式 × 2 配色 × **2 灰底**
- 索引顺序：`family.ordinal*24 + style.ordinal*4 + scheme*2 + (ghostVisible ? 0 : 1)`
- 生成：`python tools/make-icon-variants.py`（约 2~4 分钟）
- manifest 注入：`python tools/patch-manifest-icons.py`（192 个 `activity-alias`）
- **图标内容排布**：`21 / 09:36:58 / 47`
  - 依据：48 字重实测视觉重量，上下块差 0.0015、边缘留白 0.485
  - 三块均为合法时间值（≤59 或 ≤23）
  - `1` 置于上块右侧，其 0.765em 左留白藏在块内
- **图标切换只能在 `onStop()` 执行** —— 前台禁用当前别名会结束任务

### 3.5 手势

| 手势 | 位置 | 功能 |
| --- | --- | --- |
| 单击 | 背景 | 重播 / 延长信息提示 |
| 双击 | 时钟（数字区） | 切换灰底 |
| 双击 | 背景 | 黑白配色互换 |
| 双击 | 字体名块 | 小写等宽开关 |
| 单击 | 信息块 | 该块常驻 |
| 长按 | 背景 | 最大亮度（不持久化） |
| 长按 | 版本号块 | 打开应用信息面板 |
| 左右滑动 | 全屏 | 切字体族 |
| 上下滑动 | 全屏 | 切字重/倾斜 |

时钟区与背景区的双击判定：根层统一接收 `Offset`，用 `clockDigitsRect`（`boundsInRoot`）判断落点。

### 3.6 其他约定

- **纯黑底 + 白字**；配色可互换（持久化）
- **灰底开关**（持久化）：默认开 → 时钟有熄灭段、信息块与时钟同色并铺 `8`/`~` 字框；关闭 → 时钟只留亮段、信息块转灰、不铺字框
- **诊断信息**：仅 debug 包显示，带半透明黑底 + 描边阴影
- **启动画面**：`values-v31/themes.xml` 把 splash 图标置为透明（`drawable/splash_blank.xml`），启动为纯黑
- **信息块文字**：`displayText()` 把空格换成 `_`（字体里空格 advance 仅 200，下划线是 816）
- **字号基准**：`INFO_LONGEST_NAME = "HSEG16_Classic_Mini_Mono_Light_Italic"`，必须用**下划线形式**，与真实显示一致

---

## 四、已知限制（无法修复，属系统行为）

| 限制 | 说明 |
| --- | --- |
| 图标切换需离开应用 | 前台切换会结束任务，只能放 `onStop` |
| 强制停止后图标不变 | 系统直接终止进程，不回调任何生命周期方法 |
| 启动画面用前景层 | Android 12+ splash 只取 alias 的 foreground，背景层被丢弃 |

**已做的缓解**：`pendingIconVariant` 持久化到 `SharedPreferences`，下次启动恢复后可在正常退出时补做。

---

## 五、工具与脚本

| 脚本 | 用途 |
| --- | --- |
| `tools/export_apk.py` | **导出（首选）**，bump + 构建 + 校验 + 命名 + 清理旧内部包 |
| `tools/replace-fonts-with-ttc.py` | 从 `.ttc` 解包并替换 `res/font`，自动备份 |
| `tools/make-icon-variants.py` | 生成 192 个图标 + `values/ic_variants.xml` + `docs/icon/variants.txt` |
| `tools/patch-manifest-icons.py` | 注入 192 个 `activity-alias` |
| `tools/rename-font-resources.py` | 字体资源重命名（已完成，留档） |
| `tools/measure-digit-weights.py` | 测 48 字重 × 10 数字的视觉重量 → `docs/digit-weights.json` |
| `tools/search-legal-v2.py` | 搜索合法数字排布（含重量、边缘留白、合法性三项约束） |
| `tools/render-cover-layout.py` 等 | 生成排布示意图（文件名带时间戳，避免缓存顶替） |

**字体备份**：`tools/font_backup_dseg7/`（24 个原 DSEG7）、`tools/font_backup_dseg14/`（24 个原 DSEG14）

---

## 六、代码结构

| 文件 | 职责 |
| --- | --- |
| `ClockScreen.kt` | 主界面、信息 overlay、诊断、`AboutPanel`、手势 |
| `ClockFont.kt` | 48 字体资源表、`fullFontName()`、族/样式枚举 |
| `ClockIconVariants.kt` | 192 变体的 `indexOf` / `apply` / `report` |
| `ClockPreferences.kt` | 配色、字体、常驻块、等宽、灰底、待切换图标 |
| `InfoBlocks.kt` | 信息块标识常量、`applyMonoLowercase()`、`displayText()` |
| `ClockLayout.kt` | 字号/留白计算常量 |
| `MainActivity.kt` | 状态接线、`onStop` 图标切换、启动画面恢复 |

---

## 七、注意事项（踩过的坑）

1. **PowerShell 处于 `ConstrainedLanguage`**：不能执行 `.ps1`、不能用 `[System.IO.File]::`、不能 `.Replace()`。改用 Python 或文件工具。
2. **沙箱临时目录可能丢失**：报错 `--temp is not an existing directory: ...\dsh-XXXX` 时，需重建该目录（一次 `danger-full-access`）。
3. **`Select-String` 过滤 Python 输出的中文会乱码**，验证脚本优先看原始输出或写入文件。
4. **大批量结构改动用精确 `edit`，不要正则批量删** —— 曾因此把 `ClockScreen.kt` 的括号与参数删坏多次。
5. **`hitModifier` 只在 `pinned || phase == Holding` 时挂 `pointerInput`**，否则背景手势会被信息块吞掉。
6. **`Text` 的 `textAlign`/`lineHeight` 决定字形位置** —— 用 Canvas 另画一层必然对不齐；铺底改用"两个 Text 层叠"才解决。
7. **`boundsInParent` 是相对最近父级**，判断根坐标点击必须用 `boundsInRoot`。
8. **`version.json` 曾被长摘要写坏** —— 现在 `export_apk.py` 用短摘要，且损坏后可用 `tools/repair-version-json.py` 修复。
9. **沙箱内 `git` 推送必须绕开 schannel**：默认后端报 `SEC_E_NO_CREDENTIALS`，改用
   `git -c http.sslBackend=openssl -c credential.helper= push <token-url> main` 可成功；
   拉取（fetch/clone）偶发 `Recv failure: Connection was reset`，可改用 `gh api` 读取远端数据。
   `gh` 依赖 PATH 中的 git，调用前需把 `C:\Program Files\Git\cmd` 前置到 PATH。

---

## 八、下一步

`1.0.0` 已于 2026-10-26 正式导出（versionCode 1000001，发布密钥签名），README 已重写并换上
1.0.0 实拍截图（`docs/screenshots/clock-1.0.0-landscape.png`：05:20:13、HSEG16 Modern Mono
Bold Italic、黑底灰衬、91%）。

待办：用户实测确认。仓库已于 2026-10-26 创建并推送（公开，默认分支 `main`；`.gitignore` 排除了
`tools/` 工具链、`release/`、`font-source/`、`repo/`、`keystore/`），面板里的 `REPO_URL` 现在指向
真实仓库，点击可跳转。

`1.0.0` 已发布到 GitHub Releases：<https://github.com/KuwsSyet9999/HoMiSe-Clock/releases/tag/v1.0.0>
（APK 与同名 `.sha256`，API 记录的 digest 与本地一致），README 的「下载」一节指向 `releases/latest`，
以后发新版本只需新建 Release，链接不必改。

内部迭代 `1.0.0.1`（`release/HoMiSe_1.0.0.1_*.APK`）为面板里的仓库地址加了点击跳转
（`Modifier.openRepoLink()` → `ACTION_VIEW`，横竖屏两处都生效，无浏览器时静默）。已在 MuMu 上
实测：点击后 Chrome 打开该地址；仓库创建前显示 404，现在可正常打开。

`1.0.0` 正式包已按用户确认**重新导出**，包含该改动（旧包被替换，`version.json` 与 `VERSIONING.md`
的 1.0.0 记录已更新为新文件名与 SHA-256，`fromInternal` 仍保留 `0.3.2.35`）。`export_release.py`
与 `archive-release.py` 现支持同版本重新导出（更新记录、替换旧包与表行，不重复追加）。
