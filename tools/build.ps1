<#
.SYNOPSIS
    Build the HoMiSe Android project with the correct JDK, Gradle and Android SDK.

.DESCRIPTION
    This machine has no Android Studio and its default JDK 27 is too new for AGP 8.x,
    so JDK 17 lives inside tools\jdk-17 and Gradle inside tools\gradle-8.9.
    This script wires all three together and then runs the requested Gradle tasks.

    NOTES
      - Keep this file pure ASCII: Windows PowerShell 5.1 decodes BOM-less files as GBK
        on this machine, so non-ASCII text here would break parsing.
      - OFFLINE BY DEFAULT. Dependencies are already cached under tools\gradle-home
        (about 357 MB), so Gradle is invoked with --offline. This matters because the
        restricted DSH sandbox blocks ALL HTTPS (schannel SEC_E_NO_CREDENTIALS), so an
        online build would fail without an approval. With --offline the whole
        edit -> build -> test -> export loop runs with no network and no approval.
      - Pass -Online only when a dependency actually needs to be fetched or updated.

.EXAMPLE
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\build.ps1
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\build.ps1 -Tasks assembleDebug -Clean
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\build.ps1 -Tasks lint
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\build.ps1 -Online
#>
[CmdletBinding()]
param(
    [string[]]$Tasks = @('assembleDebug'),
    [switch]$Clean,
    [switch]$Stacktrace,
    [string]$SdkDir,
    # 需要联网拉取/更新依赖时使用；默认离线，可在受限沙箱内直接构建
    [switch]$Online
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$jdkHome = Join-Path $root 'tools\jdk-17'
$gradleHome = Join-Path $root 'tools\gradle-8.9'
if (-not $SdkDir) { $SdkDir = Join-Path $root 'tools\android-sdk' }

Write-Output "== HoMiSe build =="
Write-Output "project : $root"
Write-Output "JDK     : $jdkHome"
Write-Output "Gradle  : $gradleHome"
Write-Output "SDK     : $SdkDir"
Write-Output "tasks   : $($Tasks -join ', ')"
Write-Output "mode    : $(if ($Online) { 'ONLINE (may need network approval)' } else { 'OFFLINE (no network, no approval needed)' })"

if (-not (Test-Path (Join-Path $jdkHome 'bin\java.exe'))) {
    throw "JDK 17 not found at $jdkHome. Run tools\install-jdk17.ps1 first."
}
if (-not (Test-Path $SdkDir)) {
    throw "Android SDK not found at $SdkDir. Run tools\setup-android-sdk.ps1 first."
}

$env:JAVA_HOME = $jdkHome
$env:ANDROID_HOME = $SdkDir
$env:ANDROID_SDK_ROOT = $SdkDir
# Keep the Android tooling's own preferences inside the project too: the real home
# directory has a non-ASCII name, which the tooling cannot write to.
# Set ANDROID_USER_HOME only: AGP rejects builds when ANDROID_PREFS_ROOT and
# ANDROID_USER_HOME are both present, even pointing at the same folder.
$env:ANDROID_USER_HOME = Join-Path $root 'tools\android-home'
Remove-Item Env:\ANDROID_PREFS_ROOT -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $env:ANDROID_USER_HOME -Force | Out-Null

# The Android plugin's analytics still writes to %USERPROFILE%\.android, whose name is
# non-ASCII here, producing an "Unable to initialize metrics" warning on every build.
# Pointing HOME at an ASCII folder inside the project silences it (analytics is off by
# default in this setup anyway).
$asciiHome = Join-Path $root 'tools\home'
New-Item -ItemType Directory -Path $asciiHome -Force | Out-Null
$env:HOME = $asciiHome
$env:USERPROFILE = $asciiHome

# adb (started by Gradle for connected tests) writes adb.log into %TEMP%, and the real
# temp directory sits under the non-ASCII user profile where that write is denied
# ("cannot open C:\Users\<non-ASCII>\AppData\Local\Temp\adb.log: Permission denied").
$asciiTemp = Join-Path $root 'tools\temp'
New-Item -ItemType Directory -Path $asciiTemp -Force | Out-Null
$env:TEMP = $asciiTemp
$env:TMP = $asciiTemp
$env:PATH = "$jdkHome\bin;$SdkDir\platform-tools;$env:PATH"

# Critical on this machine: the signed-in user's home directory contains non-ASCII
# characters, and Gradle fails to load native-platform.dll from such a path
# ("Could not initialize native services"). Keeping Gradle's home inside the project
# (a pure ASCII path) avoids it, and also keeps the cache off the system drive.
$env:GRADLE_USER_HOME = Join-Path $root 'tools\gradle-home'
New-Item -ItemType Directory -Path $env:GRADLE_USER_HOME -Force | Out-Null

# local.properties tells Gradle where the SDK is; written with forward slashes so that
# the Java properties parser never treats a backslash as an escape character.
$localProps = Join-Path $root 'local.properties'
$sdkForProps = $SdkDir -replace '\\', '/'
[System.IO.File]::WriteAllText($localProps, "sdk.dir=$sdkForProps`n", (New-Object System.Text.UTF8Encoding($false)))

$gradleBat = Join-Path $gradleHome 'bin\gradle.bat'
$gradleArgs = @()
if ($Clean) { $gradleArgs += 'clean' }
$gradleArgs += $Tasks
if ($Stacktrace) { $gradleArgs += '--stacktrace' }
# 默认离线：依赖已全部缓存，加 --offline 后 Gradle 不联网，
# 因而受限沙箱（阻断全部 HTTPS）下也能直接构建，无需提权。
if (-not $Online) { $gradleArgs += '--offline' }

if (Test-Path $gradleBat) {
    Write-Output "`nRunning: gradle $($gradleArgs -join ' ')`n"
    & $gradleBat @gradleArgs
    $code = $LASTEXITCODE
} else {
    $gradlew = Join-Path $root 'gradlew.bat'
    if (-not (Test-Path $gradlew)) { throw "Neither $gradleBat nor $gradlew exists. Run tools\setup-gradle.ps1 first." }
    Write-Output "`nRunning: gradlew $($gradleArgs -join ' ')`n"
    & $gradlew @gradleArgs
    $code = $LASTEXITCODE
}

Write-Output "`nGradle exit code: $code"
if ($code -eq 0) {
    $apkDir = Join-Path $root 'app\build\outputs\apk'
    if (Test-Path $apkDir) {
        Write-Output "APK output:"
        Get-ChildItem $apkDir -Recurse -Filter *.apk | Select-Object -ExpandProperty FullName
    }
}
exit $code
