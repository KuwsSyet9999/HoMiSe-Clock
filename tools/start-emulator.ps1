# Launch the HoMiSe AVD (pure ASCII).
# Note: -no-window is NOT supported on Windows, so the emulator runs with a real window.
$ErrorActionPreference = 'Continue'
$root = 'D:\DSHin\HoMiSe'
$sdk = Join-Path $root 'tools\android-sdk'
$jdk = Join-Path $root 'tools\jdk-17'

$env:JAVA_HOME = $jdk
$env:ANDROID_HOME = $sdk
$env:ANDROID_SDK_ROOT = $sdk
$env:ANDROID_AVD_HOME = Join-Path $root 'tools\avd'
# The emulator resolves its own ".android" directory from HOME / USERPROFILE, and the
# signed-in user's home has a non-ASCII name it cannot write to
# ("Unexpected error while creating: C:\Users\<non-ASCII>\.android\...lock (error: 5)").
# Point both, plus the Android home, at ASCII paths inside the project.
$env:HOME = Join-Path $root 'tools\home'
$env:USERPROFILE = Join-Path $root 'tools\home'
$env:ANDROID_USER_HOME = Join-Path $root 'tools\home'
Remove-Item Env:\ANDROID_PREFS_ROOT -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path (Join-Path $env:HOME '.android') -Force | Out-Null

# adb writes adb.log into %TEMP%, which is denied under the non-ASCII user profile; the
# emulator also fails to register with the adb server if adb cannot start. Point TEMP at
# an ASCII path and bring the adb server up before launching the emulator.
$asciiTemp = Join-Path $root 'tools\temp'
New-Item -ItemType Directory -Path $asciiTemp -Force | Out-Null
$env:TEMP = $asciiTemp
$env:TMP = $asciiTemp

$env:PATH = "$jdk\bin;$sdk\emulator;$sdk\platform-tools;$env:PATH"

Write-Output "starting adb server..."
& (Join-Path $sdk 'platform-tools\adb.exe') start-server 2>&1 | Out-Null
& (Join-Path $sdk 'platform-tools\adb.exe') devices 2>&1

Write-Output "ANDROID_AVD_HOME = $env:ANDROID_AVD_HOME"
Get-ChildItem $env:ANDROID_AVD_HOME -Force | Select-Object -ExpandProperty Name

Write-Output ""
Write-Output "starting emulator (huge software renderer, first boot may take many minutes)..."
$emu = Join-Path $sdk 'emulator\emulator.exe'
$emuArgs = @(
    '-avd', 'HoMiSeTest',
    '-gpu', 'swiftshader_indirect',
    '-no-audio',
    '-no-boot-anim',
    '-no-snapshot',
    '-memory', '2048',
    '-cores', '4',
    '-verbose'
)
Write-Output ("cmd: `"$emu`" " + ($emuArgs -join ' '))
& $emu @emuArgs
Write-Output "emulator exited with code $LASTEXITCODE"
