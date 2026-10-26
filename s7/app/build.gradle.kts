import groovy.json.JsonSlurper
import java.io.File
import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

/**
 * 版本号规则（见根目录 VERSIONING.md）：
 *   格式 = 主.子.末.迭代序号
 *   内部迭代只递增第 4 位；正式版本不带迭代序号，由需求方确认后才导出。
 * versionName 对外只取「主.子.末」，versionCode 由四段位合成并保持单调递增。
 *
 * 注意：version.json 是嵌套 JSON，不能用 Properties 读取（点分键取不到嵌套对象）。
 */
val versionFile = rootProject.file("version.json")
require(versionFile.exists()) { "未找到版本状态文件 version.json，版本号规则要求必须存在" }

@Suppress("UNCHECKED_CAST")
val versionJson = JsonSlurper().parse(versionFile, "UTF-8") as Map<String, Any>
@Suppress("UNCHECKED_CAST")
val versionCurrent = versionJson["current"] as Map<String, Any>

fun versionField(name: String): Int =
    (versionCurrent[name] as? Number)?.toInt()
        ?: error("version.json 缺少 current.$name")

val vMajor = versionField("major")
val vMinor = versionField("minor")
val vPatch = versionField("patch")
val vIteration = versionField("iteration")

// 对外版本号：只含主.子.末三位，不含迭代序号
val versionNameText = "$vMajor.$vMinor.$vPatch"
// 构建号：Android 要求为正整数且同一应用必须单调递增。
// base = 主*1e6 + 子*1e4 + 末*100 + 1，保证「同一基线的内部迭代版」严格大于其正式版，
// 且小于下一个正式版；起始基线 0.0.0 的构建号因此从 1 开始而不是 0。
val versionCodeValue = vMajor * 1_000_000 + vMinor * 10_000 + vPatch * 100 + 1 + vIteration

/**
 * 签名配置。
 *
 * 凭据优先取自环境变量，便于在不把密码写进仓库的前提下签名：
 *   HOMISE_KEYSTORE_FILE / HOMISE_KEYSTORE_PASSWORD / HOMISE_KEY_ALIAS / HOMISE_KEY_PASSWORD
 * 未提供时读取 keystore/release.properties（分发用发布密钥的配置，不进版本库）；
 * 两者都没有时，回退到 tools/create-keystore.ps1 生成的本地测试密钥（口令是公开的 "android"）。
 *
 * 重要：本地测试密钥不可用于对外分发。发布密钥一旦丢失，已发布的应用将永远无法更新，
 * 因此 keystore/homise-release.jks 与 keystore/release.properties 必须离线备份。
 */
val releaseSigningProps = Properties().apply {
    val f = rootProject.file("keystore/release.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}

fun signingValue(envName: String, propName: String, fallback: String): String =
    System.getenv(envName) ?: releaseSigningProps.getProperty(propName) ?: fallback

// 属性文件里的 storeFile 是相对 keystore/ 的文件名，需解析成绝对路径
val signingStoreFileRaw = signingValue("HOMISE_KEYSTORE_FILE", "storeFile", "homise-debug.jks")
val signingStoreFile = if (File(signingStoreFileRaw).isAbsolute) {
    signingStoreFileRaw
} else {
    rootProject.file("keystore/$signingStoreFileRaw").absolutePath
}
val signingStorePassword = signingValue("HOMISE_KEYSTORE_PASSWORD", "storePassword", "android")
val signingKeyAlias = signingValue("HOMISE_KEY_ALIAS", "keyAlias", "android")
val signingKeyPassword = signingValue("HOMISE_KEY_PASSWORD", "keyPassword", signingStorePassword)
val hasSigningKey = file(signingStoreFile).exists()

// 明确报出签名来源，避免把测试密钥误当发布密钥（两者签名不同，无法互相覆盖安装）
val signingSource = when {
    System.getenv("HOMISE_KEYSTORE_FILE") != null -> "ENV"
    releaseSigningProps.isNotEmpty() -> "keystore/release.properties (发布密钥)"
    else -> "本地测试密钥（不可分发）"
}
logger.lifecycle("HoMiSe signing: $signingSource -> ${file(signingStoreFile).name}")

logger.lifecycle(
    "HoMiSe version: name=$versionNameText code=$versionCodeValue " +
        "(iteration=$vIteration from version.json)"
)

android {
    namespace = "com.homise.clock"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.homise.hmss7"
        minSdk = 26
        targetSdk = 35
        versionCode = versionCodeValue
        versionName = versionNameText
    }

    signingConfigs {
        if (hasSigningKey) {
            create("release") {
                storeFile = file(signingStoreFile)
                storePassword = signingStorePassword
                keyAlias = signingKeyAlias
                keyPassword = signingKeyPassword
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            // 有可用密钥时才签名；否则仍产出未签名包（gradle 会提示 unsigned）
            if (hasSigningKey) {
                signingConfig = signingConfigs.getByName("release")
            }
            // 正式版显示三位；用 -PtestBuild 构建测试包时显示迭代号。
            val displayVersion = if (project.hasProperty("testBuild")) {
                "\"$versionNameText.$vIteration\""
            } else {
                "\"$versionNameText\""
            }
            buildConfigField("String", "DISPLAY_VERSION", displayVersion)
        }
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-internal"
            // 内部包显示四位版本号，便于测试时确认装的是哪一次迭代
            buildConfigField("String", "DISPLAY_VERSION", "\"$versionNameText.$vIteration\"")
        }
    }

    compileOptions {
        // 本机默认 JDK 27 不被 AGP 支持，构建须使用 JDK 17（见 NETWORK.md）
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    packaging {
        resources.excludes += "/META-INF/{AL2.0,LGPL2.1}"
        // S7 精简：Kotlin 模块元数据与 baseline profile 都不参与运行
        resources.excludes += "kotlin/**"
        resources.excludes += "*.prof"
        resources.excludes += "*.profm"
        // 时钟只用 Compose 文本与圆角形状，不涉及 Path 解析
        jniLibs.excludes += "**/libandroidx.graphics.path.so"
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.activity.compose)

    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)

    debugImplementation(libs.androidx.ui.tooling)

    // 本地单元测试：验证布局尺寸计算（不需要设备）
    testImplementation(libs.junit)
}
