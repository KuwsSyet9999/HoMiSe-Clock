# 网络环境与获取策略

本文件记录本项目开发机（Windows 10/11 + PowerShell 5.1）在创建 Android 时钟软件时的**实测**网络环境，以及由此确定的依赖获取与资料检索策略。
实测时间：2026-02-14。网络环境会变，重大变更前应重新实测并更新本文件。

## 1. 最重要的一条：沙箱受限模式会完全阻断 HTTPS

同一台机器、同一条 `curl` 命令，两种模式的实测结果：

| 模式 | mirrors.aliyun.com | dl.google.com | repo1.maven.org |
| --- | --- | --- | --- |
| DSH 沙箱受限模式 | `000`（0.03s 失败） | `000`（0.23s 失败） | `000`（0.39s 失败） |
| 不受限模式 | `301` 正常 | `200`，875 KB/s | `200`，86 KB/s |

失败原因（`curl -v` 原文）：

```
curl: (35) schannel: AcquireCredentialsHandle failed: SEC_E_NO_CREDENTIALS (0x8009030E)
```

即 TLS 凭证获取被受限令牌拦下。DNS 解析与 TCP 连接均正常，**只有 HTTPS 握手失败**。

**结论：一切下载依赖、拉取官方文档、检索资料的操作，都必须在不受限（完全访问）模式下执行；受限模式只能做本地文件读写与代码编辑。** 若在受限模式下看到 `000`、`SEC_E_NO_CREDENTIALS`、连接超时，那是沙箱所致，不是网络本身的问题。

## 2. 站点分级实测

### 2.1 完全可用（推荐作为主力源）

| 站点 | 结果 | 速率 | 用途 |
| --- | --- | --- | --- |
| `maven.aliyun.com/repository/google` | 200 / 0.13s | 92 KB/s | **AndroidX、AGP 等 Google 系依赖首选** |
| `maven.aliyun.com/repository/public` | 200 / 0.05s | 57 KB/s | Maven Central 聚合，首选 |
| `maven.aliyun.com/repository/central` | 200 / 0.09s | 31 KB/s | Maven Central |
| `mirrors.aliyun.com` | 200 | 235 KB/s | 通用镜像、Gradle 发行包 |
| `dl.google.com/android/repository` | 200 / 0.43s | 875 KB/s | Android SDK、命令行工具、系统镜像 |
| `services.gradle.org` | 200 / 5.4s | 405 KB/s | Gradle 发行包（官方） |
| `repo1.maven.org` / `repo.maven.apache.org` | 200 | 55–87 KB/s | Maven Central 官方 |
| `plugins.gradle.org` | 200 / 1.0s | 11 KB/s | Gradle 插件门户 |
| `repo.huaweicloud.com/repository/maven` | 200 / 0.19s | 15 KB/s | 华为云 Maven 备用源 |
| `mirrors.cloud.tencent.com` | 200 / 0.36s | 5.7 KB/s | 腾讯云 Maven 备用源 |
| `codeload.github.com` | 200 / 3.9s | 147 KB/s | **GitHub 仓库打包下载可用** |
| `registry.npmmirror.com` | 200 / 1.9s | 慢 | npm 镜像备用 |
| `services.nvd.nist.gov` | 200 | — | CVE 漏洞库查询 |

### 2.2 不可用（被阻断，必须绕开）

| 站点 | 现象 | 影响 |
| --- | --- | --- |
| `github.com`（网页） | TCP 通，HTTPS 无响应，7s 超时 | 无法浏览仓库页面；改用 `codeload.github.com` 下载源码包 |
| `developer.android.com` | TCP 超时 | 无法直接读官方文档；改用本地 SDK 文档或镜像/检索摘要 |
| `maven.google.com` | TCP 超时 | 无法直接用 Google 官方 Maven；改用阿里云 google 镜像 |
| `raw.githubusercontent.com` | 301 后无响应 | 单文件 raw 拉取不可靠；改用 codeload 下载 |

## 3. 由此确定的获取策略

1. **Maven / Android 依赖**：Gradle 仓库一律走阿里云镜像，不直连 `maven.google.com`。
2. **Gradle 发行包**：优先 `services.gradle.org` 官方（405 KB/s 实测可用），失败再退到阿里云镜像。
3. **Android SDK / 构建工具 / 系统镜像**：直连 `dl.google.com`（速率最好）。
4. **GitHub 上的第三方库**：用 `codeload.github.com` 下载 zip/tar 包，不去 clone github.com 主站。
5. **官方文档与技术资料**：直接抓取 `developer.android.com` 不可行，改走资料检索（web 检索获取摘要）+ 本地已安装的 SDK 源码与文档。
6. **所有联网操作**：必须在不受限模式下发起。

### 3.1 本会话的审批约定（2026-02-14 需求方确认）

需求方选择**保持最小权限**：沙箱维持受限模式，每次需要联网时由助手逐条提出不受限运行请求，并说明该命令的用途，由需求方批准后执行。
因此联网类命令应**合并批量执行**（一次批准完成一批下载/检索），避免频繁打扰。

## 4. 建议写入工程的仓库配置（待创建 Gradle 工程时采用）

```kotlin
// settings.gradle.kts
dependencyResolutionManagement {
    repositories {
        maven { url = uri("https://maven.aliyun.com/repository/google") }
        maven { url = uri("https://maven.aliyun.com/repository/public") }
        maven { url = uri("https://maven.aliyun.com/repository/central") }
        maven { url = uri("https://repo.huaweicloud.com/repository/maven") }
        google(); mavenCentral(); gradlePluginPortal()
    }
}
```

`gradle-wrapper.properties` 的 `distributionUrl` 可选：

- 官方：`https://services.gradle.org/distributions/gradle-X.Y-bin.zip`（实测 405 KB/s）
- 阿里云：`https://mirrors.aliyun.com/macports/distfiles/gradle/gradle-X.Y-bin.zip`（实测 284 KB/s）

## 5. 本机环境事实

| 项目 | 值 |
| --- | --- |
| 工作目录 | `D:\DSHin\HoMiSe` |
| PowerShell | Windows PowerShell 5.1（**无 `pwsh`**，脚本只能用 `powershell.exe -ExecutionPolicy Bypass` 调用） |
| 脚本编码 | PS 5.1 读无 BOM 的 UTF-8 会按 GBK 解码，含中文的 `.ps1` **必须保存为 UTF-8 with BOM**；本项目所有 `tools\*.ps1` 已统一写成纯 ASCII，从根上避开此坑 |
| 版本管理工具 | `tools/version.ps1`（详见 `VERSIONING.md`） |

### 5.1 受沙箱影响的三个能力（实测）

| 能力 | 结果 | 说明 |
| --- | --- | --- |
| 受限模式 HTTPS | 全面被阻断 | `SEC_E_NO_CREDENTIALS`，所有联网命令必须不受限运行 |
| 子进程 `Start-Job` | 收不到任何数据 | 沙箱拦截其命名管道；多线程下载改用**单进程 `curl --parallel`**（见 `tools/download-common.ps1`） |
| 受限模式 `SetNamedSecurityInfo` | 失败（Win32 5） | 工作区首次授权需一次不受限运行，之后恢复正常 |
| 工作区外建目录 | 拒绝访问 | 工具链必须放在项目内 |

### 5.1.1 中文用户名带来的连环坑（已全部绕过）

当前登录用户名为 `古成学`，其家目录路径含非 ASCII 字符，触发了两个独立故障：

| 故障 | 现象 | 解决 |
| --- | --- | --- |
| Gradle 无法初始化本地服务 | `Could not initialize native services` / `Failed to load native library 'native-platform.dll'` | 把 `GRADLE_USER_HOME` 设为项目内纯 ASCII 路径 `tools\gradle-home`（已在 `tools/build.ps1` 中固化） |
| sdkmanager 无法拉取远程清单 | `IO exception while downloading manifest`、`java.nio.file.NoSuchFileException: C:\Users\古成学\.android\cache\...` | 放弃 sdkmanager，改用 `tools/setup-android-sdk-manual.ps1` 从官方 XML 解析地址后直接下载解压 |

**规则：本项目所有工具链的缓存/家目录一律放在项目内的纯 ASCII 路径下**，不要依赖 `%USERPROFILE%`。

### 5.1.1.1 AGP 的环境变量冲突（已解决）

把 Android 偏好目录改到项目内时踩到一个坑：**同时设置 `ANDROID_PREFS_ROOT` 与 `ANDROID_USER_HOME` 会让 AGP 直接拒绝构建**，即使两者指向同一目录：

```
com.android.prefs.AndroidLocationsException: Several environment variables and/or
system properties contain different paths to the Android Preferences folder.
- ANDROID_PREFS_ROOT(environment variable): ...\tools\android-home
- ANDROID_USER_HOME(environment variable): ...\tools\android-home
```

**只设置 `ANDROID_USER_HOME`**，并用 `Remove-Item Env:\ANDROID_PREFS_ROOT` 主动清理可能继承来的值（`tools/build.ps1` 已如此处理）。本机用户级/机器级未持久化设置任何 `ANDROID*` 变量。

### 5.1.2 sdkmanager 的替代方案

`tools/setup-android-sdk-manual.ps1` 的做法（已验证可用）：

1. 下载 `https://dl.google.com/android/repository/repository2-3.xml` 官方清单；
2. 解析出 `platform-tools`、`platforms;android-35`、`build-tools;35.0.0` 的 `complete.url`；
3. 12 线程分段下载并解压到 `tools/android-sdk/`；
4. 自动剥离压缩包内的包装目录（`platform-tools/`、`android-35/`、build-tools 的 `android-15/`）；
5. 写入 `licenses/` 授权文件，使 Gradle 的 Android 插件认可该 SDK。

注意：`platforms;*` 这类包的 archive 节点**没有 `host-os` 属性**（主机无关），解析时不能按 Windows 过滤。

### 5.1.3 分段下载的两个隐蔽陷阱（均已踩过并修复）

`tools/download-common.ps1` 的并行分段下载最终实现如下，中途两个坑值得记录：

**坑一：`Start-Job` 在本沙箱收不到任何数据。** 子 PowerShell 作业需要命名管道，被沙箱拦截，`Receive-Job` 永远返回空。因此并行下载改用 `System.Diagnostics.Process` 直接并发启动多个 `curl.exe` 进程，只以退出码判定成败。

**坑二：`curl --parallel` 会去重相同 URL。** 用一份 curl config 写 4 个相同 URL、不同 `range`，curl 只真正请求 **1 次**，却把同一份字节写进了全部 4 个输出文件——结果是**文件大小恰好正确、内容完全错误**（合并后首字节为 `34 F3`，而 ZIP 应为 `50 4B`）。这种错误极难从大小上发现，必须校验内容。

**踩过的附带坑：** 在 curl config 里用 Windows 反斜杠路径（如 `tools\_x\y.zip.part0`）会被 curl 当作转义符，路径被压扁成 `tools_xy.zip.part0` 并**落在工作目录旁边**，一次下载就散落了 442 MB 垃圾文件。config 中的路径必须用正斜杠。

**验证方式（必须做）：** 除比对文件大小外，还要比对首部魔数与远端 `content-length`；`tools/tmp` 内不得残留 `*.part*`，工作区根目录不得出现压扁命名的文件。

### 5.2 JDK 镜像实测（各下载 3 MB 样本）

| 镜像 | 结果 | 速率 |
| --- | --- | --- |
| `mirrors.huaweicloud.com/openjdk` | 206 | **5152 KB/s（最快，已采用）** |
| `mirrors.tuna.tsinghua.edu.cn/Adoptium` | 206 | 2128 KB/s |
| `api.adoptium.net`（官方） | 206 | 32 KB/s（极慢） |
| `mirrors.cloud.tencent.com/Adoptium`、`mirrors.aliyun.com/adoptium` | 404 | 无该路径 |

Gradle 发行包镜像：`mirrors.cloud.tencent.com/gradle`（130 MB，实测下载顺畅，支持 Range）。

### 5.3 最终采用的工具链

| 组件 | 版本 | 来源 |
| --- | --- | --- |
| JDK | OpenJDK 17.0.2 | 华为云 openjdk 镜像 |
| Gradle | 8.9 | 腾讯云 gradle 镜像 |
| Android SDK | cmdline-tools 13114758 + platform-tools / android-35 / build-tools 35.0.0 | `dl.google.com` |
| 模拟器 | 37.3.4（emulator-windows_x64-16555280） | `dl.google.com` |
| 系统镜像 | system-images;android-35;google_apis;x86_64（x86_64-35_r09.zip，1.66 GB） | `dl.google.com` |

### 5.4 模拟器与实机验证（已跑通）

模拟器与系统镜像同样用「解析仓库 XML + 分段下载」的方式安装（`tools/install-emulator.ps1`），因为 sdkmanager 在本机不可用。三个要点：

1. **不需要 `avdmanager` 也能建 AVD。** `avdmanager` 要求 SDK 中存在带 `package.xml` 的 `emulator` 包记录，而手动解压的包只有 `source.properties`，于是它报 `"emulator" package must be installed!`。AVD 本质只是两个配置文件，`tools/create-avd.ps1` 直接写出 `<name>.ini` 与 `<name>.avd\config.ini` 即可。
2. **Windows 上 `-no-window` 不被支持**，模拟器只能用真实窗口模式启动。
3. **本机没有硬件加速**（`emulator-check accel` 返回 6：AEHD/WHPX 均未安装），只能纯软件渲染运行。仿真环境下能正常启动并渲染，只是慢。

**截图的两个坑：**

- PowerShell 的 `>` 重定向会写成 UTF-16，把 PNG 弄坏（魔数变成 `FF FE FD FF`）。必须用 `adb shell screencap -p /sdcard/x.png` 再 `adb pull`。
- 界面文本用 `uiautomator dump` 读取，可绕过截图判读，直接确认 Compose 渲染出的字符串（实测读到 `17`、`:`、`51`、`31`、`2026-10-14 周三`，与设备时间一致）。

### 5.5 PowerShell 脚本的四个坑（本轮全部踩过）

`tools/*.ps1` 已统一为纯 ASCII 以规避编码问题，但本轮仍在脚本编写上踩了四个坑，记录如下：

| 坑 | 现象 | 规则 |
| --- | --- | --- |
| 中文注释致脚本崩溃 | 脚本语法检查报 `意外的标记 }`，且变量读出空值（如版本号变成空串，生成 `HoMiSe__时间_哈希.APK`） | PS 5.1 按 GBK 解码无 BOM 的 UTF-8，中文注释会被误读而破坏解析。**工具脚本一律纯 ASCII**；确需中文就必须存为 UTF-8 with BOM |
| 变量名不区分大小写 | 参数 `-Internal` 把脚本内 `$internalVersion` 覆盖成布尔值，导致版本号为空 | PowerShell 变量名大小写不敏感，**参数名不要与内部变量仅靠大小写区分**（已改为 `-InternalBuild`） |
| `param()` 块内不能写注释 | 参数列表报 `Missing expression after ','` | 注释放在 `param()` 之外 |
| `-Tasks a b` 传参错误 | `build.ps1` 把第二个任务当成参数值，报 `Android SDK not found at assembleDebug` | 多任务要写成数组：`-Tasks a,b` |

### 5.6 布局尺寸的循环依赖（设计教训）

「四周留白 = 一个数码管字符宽度」与「字号自适应」互相依赖：留白由字号决定，而字号又需要先知道留白。第一版把边距写成「字号 × 系数」，结果可用空间被反复折算压到下限，数字缩得极小；修正为**先按屏幕尺寸定留白比例，再反推字号，最后让留白精确等于一个字符宽**。

另有一个隐蔽后果：字号由宽度算出后，我额外加了一条宽度兜底约束，但它的分母把边距当成 2 个字符宽（实际是 `2 × 0.62 = 1.24` 个），导致内容加留白恰好超出屏宽 —— **横屏最右侧的秒数被裁掉**。两处公式必须同源，并已用 `ClockLayoutTest` 的"内容不溢出"断言守住。

**② 字符宽度必须区分「内框」与「笔迹」。** 从 `glyf` 轮廓实测（unitsPerEm 1000）：

| 字形 | advance（内框） | 笔迹 x 范围 | 笔迹宽 |
| --- | --- | --- | --- |
| 数字 0/2/8 | 816 → 0.816em | [99, 717] | **618 → 0.618em** |
| 数字 1 | 816 → 0.816em | [624, 717] | **93 → 0.093em** |
| 冒号 `:` | 200 → 0.200em | [38, 162] | **124 → 0.124em** |

**排版占位看 advance，留白与视觉间距看 ink。** 我最初按观感取 0.62，与实际内框差 32%，导致横屏内容超屏、秒的两位被压扁重叠。

**③ 留白要锚在「可见笔迹」而不是字形框上。** 字形框两侧各有 0.099em 内空白，若把 padding 直接设为 0.124em，眼睛看到的留白会变成 0.124 + 0.099×2 ≈ 0.223em。正确做法：`padding = COLON_INK_RATIO − DIGIT_SIDE_INK_RATIO`，使**可见留白**恰为一个冒号笔迹宽。

**④ 高度公式也要算上上下留白。** 早先只除以行高因子，乘上边距后总高必然超屏；横屏被宽度问题掩盖，竖屏就暴露了。

**⑤ 不要用负间距。** 为把冒号两侧可见间隙精调到 0.124em，我曾取 `gap = −0.013em`；Compose 对负间距处理不可靠，实测把 Row 子项压在一起、秒的两位数字重叠。间距取 0 或正值。

## 5.7 离线构建约定（免提权）

受限沙箱**阻断全部 HTTPS**（见 5.1），但依赖一旦缓存就不需要网络。实测：

| 操作 | 受限模式（workspace-write） | 是否需要提权 |
| --- | --- | --- |
| `build.ps1`（默认 `--offline`） | **成功，9 秒** | 否 |
| `testDebugUnitTest`（`--offline`） | **成功，22 秒** | 否 |
| `gradle.bat` **不带** `--offline`（缓存已满时） | **成功，34 秒** | 否 |
| 解析/更新依赖（`--online`、新增依赖） | 全部 `000` 失败 | **是** |

因此**约定**：

- `tools/build.ps1` **默认离线**（自动追加 `--offline`），日常「改代码 → 构建 → 测试 → 导出」全程无需联网、无需批准；
- 确实要拉取或更新依赖时，显式加 `-Online`，并在提权下运行；
- 依赖缓存位置：`tools/gradle-home/caches/modules-2`（约 357 MB），换机器时需重新预热。

`tools/export-apk.ps1` 内部调用的就是 `build.ps1`，故同样默认离线。

### 5.7.1 教训：不得习惯性提权

依赖缓存预热**完成之后**，Gradle 即便不加 `--offline` 也不再联网，受限模式足以完成编译、测试与打包。

曾因早期（缓存未预热、首次拉取工具链）确实需要提权，形成「构建 = 提权」的惯性，之后未重新评估，导致在缓存已满的情况下仍多次申请 `danger-full-access` —— 其中至少 4 次（编译、单元测试、复验）经实测**根本不需要**。

**正确顺序**：先以默认受限模式执行 → 仅在确实报出网络解析失败（`Could not resolve` / `schannel` / `000`）时，才对**那一条**命令提权重试。

**判断标准**：只有下列情况才需要提权 ——
1. 拉取或更新 Gradle 依赖（新增库、改版本号依赖）；
2. 首次搭建工具链（JDK / Gradle / Android SDK / 模拟器镜像）；
3. 联网检索资料。

其余一律先在受限模式下尝试。

## 6. 工具缺陷记录（避免误判）

- `Test-NetConnection` 在本机长时间无输出，勿用于超时探测。
- `.NET` 的 `HttpWebRequest` / `SslStream` 在本机报 `No credentials are available in the security package`，**不可用于判断站点可用性**；判定网络一律以 `curl.exe` 的 `http_code` 为准。
- `maven.aliyun.com` 等仓库根路径返回 404 属正常，必须用具体构件路径测试。

## 7. 项目资产

| 文件 | 说明 |
| --- | --- |
| `all_DSEG_list.png` | DSEG 数码管字体样式清单（选型参考） |
| `fonts-DSEG_v046.zip` | DSEG 字体包 v0.46，用于时钟数字显示 |

## 8. 变更记录

| 日期 | 变更 |
| --- | --- |
| 2026-02-14 | 首次实测并确立策略；确认本会话采用「每次联网前逐条批准」的最小权限方式 |
