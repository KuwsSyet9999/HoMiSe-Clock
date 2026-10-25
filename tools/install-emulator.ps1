<#
.SYNOPSIS
    Install the Android emulator and a system image so the app can actually be run.

.DESCRIPTION
    Everything goes through the same manual path as setup-android-sdk-manual.ps1,
    because sdkmanager cannot fetch remote manifests on this machine.

    Sizeable download (about 2 GB total): emulator ~439 MB + system image ~1.66 GB.
    Measured throughput from dl.google.com here is ~6 MB/s.

    Resulting layout:
      tools/android-sdk/emulator/
      tools/android-sdk/system-images/android-35/google_apis/x86_64/

    NOTE: keep this file pure ASCII (Windows PowerShell 5.1 decodes BOM-less files as GBK here).
    Networking required.

.EXAMPLE
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\install-emulator.ps1
#>
[CmdletBinding()]
param(
    [string]$SdkDir,
    [string]$RepoUrl = 'https://dl.google.com/android/repository/repository2-3.xml',
    [string]$BaseUrl = 'https://dl.google.com/android/repository/',
    [string]$SysImgUrl = 'https://dl.google.com/android/repository/sys-img/google_apis/x86_64-35_r09.zip',
    [int]$Threads = 12,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $SdkDir) { $SdkDir = Join-Path $root 'tools\android-sdk' }
. (Join-Path $PSScriptRoot 'download-common.ps1')

$work = Join-Path $root 'tools\_emu_setup'
New-Item -ItemType Directory -Path $work -Force | Out-Null

function Install-PackageZip {
    param(
        [string]$Url,
        [string]$DestDir,
        [string]$Label,
        [string]$ExpectedTop
    )
    $marker = Join-Path $DestDir '.homise-installed'
    if ((Test-Path $marker) -and -not $Force) {
        Write-Output "[skip] $Label already installed at $DestDir"
        return
    }

    $zip = Join-Path $work (($Label -replace '[^A-Za-z0-9._-]', '_') + '.zip')
    Write-Output "[get ] $Label"
    $ok = Start-FastDownload -Urls @($Url) -Dest $zip -Threads $Threads
    if (-not $ok) { throw "Download failed: $Url" }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
    $entries = $archive.Entries | Where-Object { $_.FullName -notmatch '/$' } | Select-Object -First 400
    $tops = @{}
    foreach ($e in $entries) {
        $parts = $e.FullName.Split('/')
        if ($parts.Count -gt 1) { $tops[$parts[0]] = $true }
    }
    $strip = $null
    if ($tops.Keys.Count -eq 1) { $strip = ($tops.Keys | Select-Object -First 1) }
    Write-Output "  archive top-level: $($tops.Keys -join ', ')  -> strip: $(if ($strip) { $strip } else { '(none)' })"
    $archive.Dispose()

    $tmp = Join-Path $work ('unpack_' + ($Label -replace '[^A-Za-z0-9]', '_'))
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    New-Item -ItemType Directory -Path $tmp -Force | Out-Null
    Expand-Archive -Path $zip -DestinationPath $tmp -Force

    $srcDir = $tmp
    if ($strip) {
        $inner = Join-Path $tmp $strip
        if (Test-Path $inner) { $srcDir = $inner }
    }
    if (Test-Path $DestDir) { Remove-Item $DestDir -Recurse -Force }
    New-Item -ItemType Directory -Path (Split-Path -Parent $DestDir) -Force | Out-Null
    Move-Item -Path $srcDir -Destination $DestDir
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $zip -Force -ErrorAction SilentlyContinue
    Set-Content -Path (Join-Path $DestDir '.homise-installed') -Value $Label -Encoding ascii
    Write-Output "  installed -> $DestDir"
}

# ---- Resolve the emulator URL from the manifest (its name carries a build id) ----
$xmlFile = Join-Path $work 'repository.xml'
if (-not (Test-Path $xmlFile) -or (Get-Item $xmlFile).Length -lt 10000) {
    & curl.exe -s -L --fail --connect-timeout 20 --max-time 300 -o $xmlFile $RepoUrl
    if ($LASTEXITCODE -ne 0) { throw "Failed to download manifest: $RepoUrl" }
}
[xml]$xml = [System.Text.Encoding]::UTF8.GetString([System.IO.File]::ReadAllBytes($xmlFile))
$rootNode = $xml.DocumentElement

$emulatorUrl = $null
$emulatorSize = 0
foreach ($p in @($rootNode.remotePackage)) {
    if ($p.path -ne 'emulator') { continue }
    foreach ($a in $p.archives.archive) {
        $os = [string]$a.'host-os'
        if ($os -ne 'windows') { continue }
        $candidate = $BaseUrl + [string]$a.complete.url
        $size = [int64]$a.complete.size
        if ($size -gt $emulatorSize) { $emulatorUrl = $candidate; $emulatorSize = $size }
    }
}
if (-not $emulatorUrl) { throw "emulator package not found in manifest" }
Write-Output ("emulator: {0} ({1} MB)" -f $emulatorUrl, [math]::Round($emulatorSize/1MB,1))

Install-PackageZip -Url $emulatorUrl -DestDir (Join-Path $SdkDir 'emulator') -Label 'emulator-windows_x64'
Install-PackageZip -Url $SysImgUrl -DestDir (Join-Path $SdkDir 'system-images\android-35\google_apis\x86_64') -Label 'system-images;android-35;google_apis;x86_64'

Write-Output ""
Write-Output "== verification =="
$checks = @(
    @{ Name = 'emulator.exe';      Path = 'emulator\emulator.exe' },
    @{ Name = 'qemu-system';       Path = 'emulator\qemu\windows-x86_64\qemu-system-x86_64.exe' },
    @{ Name = 'system.img';        Path = 'system-images\android-35\google_apis\x86_64\system.img' },
    # source.properties is the package identity file; there is no package.xml in sys-img zips.
    @{ Name = 'source.properties'; Path = 'system-images\android-35\google_apis\x86_64\source.properties' }
)
$allOk = $true
foreach ($c in $checks) {
    $full = Join-Path $SdkDir $c.Path
    $exists = Test-Path $full
    if (-not $exists) { $allOk = $false }
    $extra = ''
    if ($exists) { $extra = "$([math]::Round((Get-Item $full).Length/1MB,1)) MB" }
    Write-Output ("  {0,-16} {1,-8} {2}" -f $c.Name, $(if ($exists) { 'OK' } else { 'MISSING' }), $extra)
}
if (-not $allOk) { throw "emulator installation incomplete" }
Write-Output "`nEmulator ready under: $SdkDir"
