# 工作指引（操作规范与注意要点）

> 本文件是 HoMiSe / HMSS7 两个工程的**操作手册与踩坑记录**。
> **每轮对话结束前必须增补/修订本文件**（新增的坑、流程变化、版本与产物状态），
> 并与 `docs/HANDOFF.md` 一起提交推送——这样上下文丢失或接近上限时，接手者读这两份就能继续。
>
> 维护顺序：先改 `HANDOFF.md` 的交接状态，再回来补本文件的规范/坑；两者不一致时以本文件为准。

---

## 1. 工程结构

| 工程 | 位置 | 包名 | 说明 |
| --- | --- | --- | --- |
| HoMiSe（完整版） | 仓库根 `app/` | `com.homise.clock`（debug 加 `.debug`） | 48 款 HSEG 字体、192 图标变体 |
| HMSS7（七段简版） | `s7/` 子工程 | `com.homise.hmss7`（debug 加 `.debug`） | 只保留 HSEG7、96 图标变体、无字体名块/Mono |
| 文档 | `docs/` | — | `HANDOFF.md` 交接、`WORKING-GUIDE.md` 本文件、`screenshots/` |
| 版本规则 | `VERSIONING.md` | — | 主/子/末版本判定、内部迭代流水、发布表 |

- 两个工程各有独立的 `version.json`，独立 `settings.gradle.kts`、`gradle.properties`。
- `s7/` 是仓库子目录（不是独立仓库）；`s7/keystore`、`s7/release`、构建产物均被 `.gitignore` 忽略。
- 两版的 `ClockScreen.kt` / `MainActivity.kt` / `ClockPreferences.kt` 是**各自维护的副本**，改一处必须同步另一处（本文件的“同步检查清单”见第 8 节）。

## 2. 工具链与环境

路径（相对仓库根）：

| 项 | 路径 |
| --- | --- |
| JDK | `tools/jdk-17` |
| Gradle | `tools/gradle-8.9/bin/gradle.bat`（8.9） |
| Android SDK | `tools/android-sdk`（build-tools 35.0.0、platform-tools） |
| Gradle 缓存 | `tools/gradle-home` |
| Android 用户目录 | `tools/android-home`（缺它会报 debug.keystore.lock 权限错误） |
| 临时/Home | `tools/temp`、`tools/home` |
| Python | `C:\Users\古成学\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe`（含 Pillow、numpy、fontTools） |
| 模拟器 | MuMu，`adb 127.0.0.1:16384`，桌面 `app.lawnchair` |

每次 gradle / 构建前设置（PowerShell 片段，复制即用）：

```powershell
$root='D:\DSHin\HoMiSe'
$env:JAVA_HOME="$root\tools\jdk-17"
$env:GRADLE_USER_HOME="$root\tools\gradle-home"
$env:ANDROID_HOME="$root\tools\android-sdk"
$env:ANDROID_SDK_ROOT="$root\tools\android-sdk"
$env:ANDROID_USER_HOME="$root\tools\android-home"
$env:TEMP="$root\tools\temp"; $env:TMP="$root\tools\temp"
$env:HOME="$root\tools\home"; $env:USERPROFILE="$root\tools\home"
$env:PATH="$root\tools\jdk-17\bin;" + $env:PATH
```

Python 脚本里不要用 `python -c` 传多行或含中文/双引号的代码（沙箱 PowerShell 会破坏引号），一律写临时 `.py` 再执行。

## 3. 构建、导出与命名

| 场景 | 命令 | 产物命名 |
| --- | --- | --- |
| 完整版正式导出 | `python tools/export_release.py --version X.Y.Z --bump patch|minor|major --summary "…"` | `release/HoMiSe_<ver>_<14位时间>_<hash16>.APK`（**大写**） |
| 完整版迭代包 | `python tools/export_apk.py`（自动 bump iteration、构建 debug） | `release/HoMiSe_<ver>.<iter>_<时间>_<hash16>.apk`（**小写**） |
| S7 正式/迭代 | 手动：改 `s7/version.json` → `gradle -p s7 assembleRelease|assembleDebug` → 复制命名 | 正式 `.APK`、迭代 `.apk`（同样大小写规则） |
| 发布表行 | `python tools/archive-release.py` | 追加 `VERSIONING.md` 发布表（**注意**：脚本会追加到文件末尾，需手动归位到表内） |

- 版本号显示：正式包只显示三位（`DISPLAY_VERSION = versionNameText`）；测试包用 `-PtestBuild` 构建才带迭代号（`versionNameText.iteration`）。
- 测试包桌面名带 `(CS)`：完整版 debug 源集 `app/src/debug/res/values*/strings.xml`，S7 对应 `s7/app/src/debug/res/values*/strings.xml`；正式包不带。
- `export_release.py` 会清理旧内部包、保留全部正式包；`export_apk.py` 只保留最新迭代包。
- S7 的 debug 包名是 `com.homise.hmss7.debug`，**与正式包 `com.homise.hmss7` 共存**——测试时注意别装混（(CS) 只在 debug 包出现）。

## 4. 版本号规则要点

- 判定顺序：主版本（核心功能巨大变动）→ 子版本（新模块/新功能）→ 末版本（修缺陷/改表现形式）。
- 本轮示例：字体锁（新增功能）= 子版本 +1（1.0.1 → 1.1.0；S7 0.1.1 → 0.2.0）；图标改矢量/字体升级 = 末版本（1.0.0 → 1.0.1）。
- `versionCode` 公式：`major*1e6 + minor*1e4 + patch*100 + 1 + iteration`。
- 正式版定格后 `stage=release`、`iteration=0`；迭代包用 `stage=internal` 并递增 iteration。
- 历史摘要要写**真实内容**（不要留“内部迭代构建”这种占位），否则交接时无法核对。

## 5. 模拟器操作规范

- 连接：`adb connect 127.0.0.1:16384`（每次 pwsh 调用 adb daemon 可能重启，需重新 connect）。
- 横屏固定：`wm fixed-to-user-rotation enabled` + `settings put system user_rotation 1`；恢复：`disabled` + `accelerometer_rotation 1` + `user_rotation 0`。
- 时钟改时间：需 `adb root`（先 `adb connect`、`adb root`，等 3-4 秒后重新 connect 并确认 `whoami` 为 root），否则 `date -s` 报 Operation not permitted。
- 电量：`dumpsys battery set level NN`；恢复 `dumpsys battery reset`。
- 写 release 包偏好：非 debuggable 包不能 `adb shell` 直写 `data/`，需 `adb root` 后写 `shared_prefs/homise_clock_prefs.xml`（`chmod 660`）。
- 偏好键：`colors_inverted`、`font_family`（枚举名如 `Classic14`）、`font_style`（如 `LightItalic`）、`mono_lowercase`、`ghost_visible`、`pinned_info_blocks`（iso/name/version/battery）、`font_locked`、`style_locked`、`pending_icon_variant`。
- 图标名/图标刷新：卸载重装可刷新桌面标签；Launcher 图标缓存顽固时 `pm clear app.lawnchair`（会重置桌面布局）。
- 应用信息面板：横屏下先单击背景显示提示，再长按版本号区域（版本号位置随字体变化，可用 `uiautomator dump` 找 `v…` 节点 bounds）。
- 结束前恢复：时间（`auto_time 1` + `TIME_SET` 广播）、电量 reset、旋转恢复、`adb unroot`。

## 6. 截图规范（介绍页）

- 必须：横屏、黑底、灰衬、电量 99%、版本为最新正式版（如 `v1.1.0`）。
- 字体与时间按需求指定（当前：`HSEG16 Classic Mono Light Italic`、`1999-12-31T23:59:59+08:00`）。
- 抓 59 秒帧的方法：`date -s '1999-12-31 23:59:58'` 后连拍 12~14 帧（间隔 120ms），按秒位区域亮度分组
  （实测：`56.7 = 58`、`51.2 = 59`、`54.1 = 00`、`41.3 = 01`、`49.0 = 02`），取 59 组中冒号亮的帧，
  并**放大顶部 ISO 行逐字符确认 `…:59+08:00`**，避免误选跨年帧（曾把 `00:00:01` 当成 59）。
- 保存：`docs/screenshots/clock-<ver>-landscape.png`，README 第 5 行引用，旧图删除。

## 7. 常见坑（持续累积）

1. PowerShell 沙箱：`git push` 默认 schannel 报 `SEC_E_NO_CREDENTIALS` → 用 `-c http.sslBackend=openssl -c credential.helper=`。
2. `github.com:443` 可能被 DNS 解析到不可达 IP（`20.205.243.166`）；可达 IP：`140.82.112.3`、`140.82.113.3`、`20.27.177.113`。绕法：本地 CONNECT 中继（`127.0.0.1:8443` → `140.82.112.3:443`）+ `git -c http.proxy=http://127.0.0.1:8443 … push`；SSH deploy key 也可（但 `GIT_SSH_COMMAND` 会经 sh、沙箱报 signal pipe）。
3. `gh` 命令需把 `C:\Program Files\Git\cmd` 与 `C:\Program Files\GitHub CLI` 前置到 PATH。
4. 用户级 `gh ssh-key add` 需 `admin:public_key` 权限；仓库级 `gh repo deploy-key add --allow-write` 用 `repo` 权限即可；公钥文件末尾必须换行。
5. `Text` 的 `pointerInput(Unit)` 只捕获首次组合的参数——字体锁必须写 `pointerInput(fontLocked, styleLocked)`，否则锁定不生效。
6. `layer-list` 的 `<item android:tint>` 在 launcher 上不可靠（只显示底层）——图标必须用 Plan A：每个变体一个自包含 vector，颜色写死。
7. 图标/资源要删干净旧文件：`mipmap-*` 下的 `ic_v*_fg.webp` 残留会让 APK 多 600+ KB（曾漏删 384 张）。
8. Emoji：`🔒︎`（U+1F512+FE0E）在 Android 仍渲染为彩色、`color` 无效——锁图标用 `ImageVector`（`PathParser` + `ColorFilter.tint`）。
9. `ImageVector.Builder.addPath` 是成员函数，不要 `import …vector.addPath`（会 Unresolved reference）。
10. `export_apk.py` / `export_release.py` 在 GBK 控制台可能 `UnicodeEncodeError` → 设 `$env:PYTHONIOENCODING='utf-8'` 再运行。
11. `archive-release.py` 把表行追加到文件末尾 → 手动移回发布表（1.0.1、1.1.0 都踩过）。
12. 字体替换用 `tools/replace-fonts-with-ttc.py <ttc>`；字体子集见 `tools/font_subset_probe.py`（完整版）与 `s7/tools/subset-fonts.py`（S7）。
13. `adb root` 后 `date -s` 才生效；`unroot` 后需重新 connect。
14. 测试包与正式包同名不同 suffix（`.debug`），`dumpsys package` 核对 `versionCode/versionName` 再判断装的是哪个。
15. 版本记录（`version.json` history/releases）里的摘要要写真实内容；产物文件名要与包内实际 `DISPLAY_VERSION` 一致（曾出现 1.0.1.3 文件名 / 1.0.1.4 内容）。

## 8. 同步检查清单（改两版代码时）

改动下列文件时，**完整版与 S7 都要同步**，并在两版各构建一次 debug 验证：

- `ClockPreferences.kt`（偏好键与默认值）
- `MainActivity.kt`（状态提升、`ClockRoute` 参数、`onResetDefaults`）
- `ClockScreen.kt`（`ClockScreen`/`ClockRoute` 参数、手势 `pointerInput` key、`AboutPanel`、`AboutRow`/`StackedEntry`、锁图标）
- `res/values*/strings.xml`（正式/默认名与 debug 的 `(CS)` 后缀）
- `build.gradle.kts`（`DISPLAY_VERSION` 的 `-PtestBuild` 逻辑、packaging 排除）

## 9. 每轮收尾流程（必须执行）

1. 构建两版（受影响的那版至少 debug）并实机验证关键行为（版本号、锁状态、面板文案）。
2. 导出/归档产物，核对包内 `versionCode`/`versionName`/`DISPLAY_VERSION` 与文件名一致。
3. 更新版本记录：`version.json`（history/releases）、`VERSIONING.md` 发布表（行要归位）。
4. 更新 `docs/HANDOFF.md`（当前版本、产物、待办）与本文件（新增坑/流程变化）。
5. 清理 `tools/temp`、恢复模拟器（时间/电量/旋转/unroot）。
6. 提交推送（直连失败再走中继），确认 `git status` 干净、远端 HEAD 与本地一致。
7. 在回复末尾说明：版本号、产物路径、验证结果、未完成项。

## 10. 当前状态快照（2026-11-08）

| 项 | 值 |
| --- | --- |
| 完整版正式版 | `1.1.0`（versionCode 1010001，`release/HoMiSe_1.1.0_20261104045254_5882b59c451775bf.APK`，1.91 MB） |
| HMSS7 正式版 | `0.2.0`（versionCode 20001，`s7/release/HMSS7_0.2.0_20261104045431_6a99fbe3f6c87a35.APK`，1.1 MB） |
| GitHub Release | `v1.1.0`（Latest，「HoMiSe 1.1.0 + HMSS7 0.2.0」，含两包与 `.sha256`） |
| 介绍页截图 | `docs/screenshots/clock-1.1.0-landscape.png`（1999-12-31T23:59:59、HSEG16 Classic Mono Light Italic、99%、v1.1.0） |
| 本轮新增功能 | 字体锁（锁定字体族/字重，滑动被忽略，状态持久化；ImageVector 锁图标；测试包桌面名带 (CS)） |
| 待办 | 无强制项；可选：字体子集（−4%）、dex 优化（−3%）、HMSS7 独立 Release |
