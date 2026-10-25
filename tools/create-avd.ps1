# Create the HoMiSe AVD by writing its config directly (pure ASCII).
# avdmanager refuses to create an AVD here: it needs an "emulator" package entry with
# package.xml in the SDK, which the manually unpacked emulator does not carry.
# The emulator itself only needs a valid config.ini + <name>.ini pair.
$ErrorActionPreference = 'Stop'

$root = 'D:\DSHin\HoMiSe'
$sdk = Join-Path $root 'tools\android-sdk'
$avdHome = Join-Path $root 'tools\avd'
$avdName = 'HoMiSeTest'

New-Item -ItemType Directory -Path $avdHome -Force | Out-Null
$avdDir = Join-Path $avdHome "$avdName.avd"
New-Item -ItemType Directory -Path $avdDir -Force | Out-Null

$sysImg = 'system-images/android-35/google_apis/x86_64'
$sysImgFull = Join-Path $sdk ($sysImg -replace '/', '\')
if (-not (Test-Path (Join-Path $sysImgFull 'system.img'))) {
    throw "system image not found at $sysImgFull"
}

# ---- <name>.ini : points at the AVD directory ----
$iniContent = @(
    "avd.ini.encoding=UTF-8",
    "path=$($avdDir -replace '\\', '\\')",
    "path.rel=avd/$avdName.avd",
    "target=android-35"
)
[System.IO.File]::WriteAllText((Join-Path $avdHome "$avdName.ini"), ($iniContent -join "`r`n") + "`r`n", (New-Object System.Text.UTF8Encoding($false)))

# ---- config.ini : device profile (Pixel, 1080x1920 @ 420dpi) ----
$config = [ordered]@{
    'avd.ini.encoding'                  = 'UTF-8'
    'AvdId'                             = $avdName
    'abi.type'                          = 'x86_64'
    'hw.cpu.arch'                       = 'x86_64'
    'hw.cpu.ncore'                      = '4'
    'image.sysdir.1'                    = "$sysImg/"
    'tag.id'                            = 'google_apis'
    'tag.display'                       = 'Google APIs'
    'PlayStore.enabled'                 = 'false'
    'hw.device.name'                    = 'pixel'
    'hw.device.manufacturer'            = 'Google'
    'hw.lcd.width'                      = '1080'
    'hw.lcd.height'                     = '1920'
    'hw.lcd.density'                    = '420'
    'hw.lcd.vsync'                      = '60'
    'hw.ramSize'                        = '2048'
    'vm.heapSize'                       = '256'
    'disk.dataPartition.size'           = '4096M'
    'hw.gpu.enabled'                    = 'yes'
    'hw.gpu.mode'                       = 'swiftshader_indirect'
    'hw.keyboard'                       = 'yes'
    'hw.mainKeys'                       = 'no'
    'hw.dPad'                           = 'no'
    'hw.trackBall'                      = 'no'
    'hw.sdCard'                         = 'no'
    'hw.audioInput'                     = 'no'
    'hw.audioOutput'                    = 'no'
    'hw.camera.back'                    = 'none'
    'hw.camera.front'                   = 'none'
    'hw.sensors.orientation'            = 'yes'
    'hw.sensors.proximity'              = 'no'
    'hw.sensors.magnetic_field'         = 'yes'
    'hw.sensors.accelerometer'          = 'yes'
    'hw.sensors.gyroscope'              = 'yes'
    'hw.sensors.light'                  = 'yes'
    'hw.sensors.pressure'               = 'yes'
    'hw.sensors.humidity'               = 'yes'
    'hw.sensors.temperature'            = 'yes'
    'hw.initialOrientation'             = 'Portrait'
    'skin.dynamic'                      = 'yes'
    'showDeviceFrame'                   = 'no'
    'runtime.network.latency'           = 'none'
    'runtime.network.speed'             = 'full'
    'fastboot.forceColdBoot'            = 'yes'
    'fastboot.forceFastBoot'            = 'no'
    'firstboot.bootFromDownloadedSnapshot' = 'no'
}
$lines = @()
foreach ($k in $config.Keys) { $lines += "$k=$($config[$k])" }
[System.IO.File]::WriteAllText((Join-Path $avdDir 'config.ini'), ($lines -join "`r`n") + "`r`n", (New-Object System.Text.UTF8Encoding($false)))

Write-Output "AVD created:"
Write-Output "  ini     : $(Join-Path $avdHome "$avdName.ini")"
Write-Output "  config  : $(Join-Path $avdDir 'config.ini')"
Write-Output ""
Write-Output "=== config.ini ==="
Get-Content (Join-Path $avdDir 'config.ini') | Select-Object -First 12
Write-Output "..."
Write-Output ""
Write-Output "=== image path check ==="
$imgDir = Join-Path $sdk ($sysImg -replace '/', '\')
Write-Output ("  {0} exists: {1}" -f $imgDir, (Test-Path $imgDir))
