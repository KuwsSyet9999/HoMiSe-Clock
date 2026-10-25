<#
.SYNOPSIS
    Install the Android SDK packages manually, without sdkmanager.

.DESCRIPTION
    sdkmanager on this machine cannot fetch remote manifests (its own cache write fails
    with java.nio.file.NoSuchFileException even though plain Java can download the same
    URLs), so the required packages are fetched straight from dl.google.com and unpacked
    by hand. Package URLs are resolved from the official repository XML.

    Resulting layout:
      tools/android-sdk/platform-tools/
      tools/android-sdk/platforms/android-35/
      tools/android-sdk/build-tools/35.0.0/
      tools/android-sdk/licenses/            (so the Gradle Android plugin accepts the SDK)

    NOTE: keep this file pure ASCII (Windows PowerShell 5.1 decodes BOM-less files as GBK here).
    Networking required.

.EXAMPLE
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\setup-android-sdk-manual.ps1
#>
[CmdletBinding()]
param(
    [string]$SdkDir,
    [string]$RepoUrl = 'https://dl.google.com/android/repository/repository2-3.xml',
    [string]$BaseUrl = 'https://dl.google.com/android/repository/',
    [int]$Threads = 12,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $SdkDir) { $SdkDir = Join-Path $root 'tools\android-sdk' }
. (Join-Path $PSScriptRoot 'download-common.ps1')

$work = Join-Path $root 'tools\_sdk_setup'
New-Item -ItemType Directory -Path $work -Force | Out-Null
New-Item -ItemType Directory -Path $SdkDir -Force | Out-Null

# ---- 1. Fetch and parse the official repository manifest ----
$xmlFile = Join-Path $work 'repository.xml'
if ((Test-Path $xmlFile) -and (Get-Item $xmlFile).Length -gt 10000) {
    Write-Output "Using cached manifest: $xmlFile"
} else {
    Write-Output "Fetching repository manifest..."
    & curl.exe -s -L --fail --connect-timeout 20 --max-time 300 -o $xmlFile $RepoUrl
    if ($LASTEXITCODE -ne 0) { throw "Failed to download repository manifest: $RepoUrl" }
}
[xml]$xml = [System.Text.Encoding]::UTF8.GetString([System.IO.File]::ReadAllBytes($xmlFile))
$rootNode = $xml.DocumentElement
Write-Output "Manifest root: $($rootNode.Name), packages: $(@($rootNode.remotePackage).Count)"

function Resolve-PackageUrl {
    param([string]$Path, [string]$HostOs = 'windows')
    foreach ($p in @($rootNode.remotePackage)) {
        if ($p.path -ne $Path) { continue }
        foreach ($a in $p.archives.archive) {
            # Platform packages carry no host-os attribute: they are host independent.
            $os = [string]$a.'host-os'
            if ([string]::IsNullOrEmpty($os)) { $os = 'any' }
            if ($os -ne 'any' -and $os -ne $HostOs) { continue }
            return [pscustomobject]@{
                Path = $Path
                Url  = $BaseUrl + [string]$a.complete.url
                Size = [int64]$a.complete.size
            }
        }
        throw "Package $Path has no archive for host-os=$HostOs"
    }
    throw "Package not found in manifest: $Path"
}

# ---- 2. Download ----
$targets = @(
    @{ Path = 'platform-tools';            Dir = 'platform-tools' },
    @{ Path = 'platforms;android-35';      Dir = 'platforms\android-35' },
    @{ Path = 'build-tools;35.0.0';        Dir = 'build-tools\35.0.0' }
)

foreach ($t in $targets) {
    $info = Resolve-PackageUrl -Path $t.Path
    $destDir = Join-Path $SdkDir $t.Dir
    $marker = Join-Path $destDir '.homise-installed'
    if ((Test-Path $marker) -and -not $Force) {
        Write-Output "[skip] $($t.Path) already installed at $destDir"
        continue
    }

    $zip = Join-Path $work (($t.Path -replace '[;]', '_') + '.zip')
    Write-Output "[get ] $($t.Path)  $([math]::Round($info.Size/1MB,1)) MB"
    $ok = Start-FastDownload -Urls @($info.Url) -Dest $zip -Threads $Threads
    if (-not $ok) { throw "Download failed: $($info.Url)" }

    # ---- 3. Inspect the archive root, then strip that root when unpacking ----
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
    $entries = $archive.Entries | Where-Object { $_.FullName -notmatch '/$' } | Select-Object -First 400
    # A common single leading directory means the zip has a wrapper folder to strip.
    $tops = @{}
    foreach ($e in $entries) {
        $parts = $e.FullName.Split('/')
        if ($parts.Count -gt 1) { $tops[$parts[0]] = $true }
    }
    $strip = $null
    if ($tops.Keys.Count -eq 1) { $strip = ($tops.Keys | Select-Object -First 1) }
    Write-Output "  archive top-level: $($tops.Keys -join ', ')  -> strip: $(if ($strip) { $strip } else { '(none)' })"
    $archive.Dispose()

    # ---- 4. Extract into the SDK ----
    if (Test-Path $destDir) { Remove-Item $destDir -Recurse -Force }
    $tmp = Join-Path $work ('unpack_' + ($t.Path -replace '[;.]', '_'))
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    New-Item -ItemType Directory -Path $tmp -Force | Out-Null
    Expand-Archive -Path $zip -DestinationPath $tmp -Force

    $srcDir = $tmp
    if ($strip) {
        $inner = Join-Path $tmp $strip
        if (Test-Path $inner) { $srcDir = $inner }
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $destDir) -Force | Out-Null
    Move-Item -Path $srcDir -Destination $destDir
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $zip -Force -ErrorAction SilentlyContinue

    Set-Content -Path (Join-Path $destDir '.homise-installed') -Value $t.Path -Encoding ascii
    Write-Output "  installed -> $destDir"
}

# ---- 5. Accept licenses: the Gradle Android plugin checks this directory ----
$licDir = Join-Path $SdkDir 'licenses'
New-Item -ItemType Directory -Path $licDir -Force | Out-Null
# Hashes are the well-known license texts of the Android SDK (android-sdk-license) plus
# the platform/build-tools licenses used by recent SDK releases.
$androidSdkLicense = @(
    '8933bad161af4178b1185d1a37fbf41ea5269c55',
    'd56f5187479451eabf01fb78af6dfcb131a6481e',
    '24333f8a63b6825ea9c5514f83c2829b004d1fee'
)
Set-Content -Path (Join-Path $licDir 'android-sdk-license') -Value $androidSdkLicense -Encoding ascii
Set-Content -Path (Join-Path $licDir 'android-sdk-preview-license') -Value @('84831b9409646a918e30573bab4c9c91346d8abd') -Encoding ascii
Set-Content -Path (Join-Path $licDir 'android-googletv-license') -Value @('601085b94cd77f0b54ff86406957099ebe79c4d6') -Encoding ascii
Set-Content -Path (Join-Path $licDir 'google-gdk-license') -Value @('33b6a2b64607f11b759f320ef9dff4ae5c47d97a') -Encoding ascii
Write-Output "Licenses written to $licDir"

# ---- 6. Verify ----
Write-Output "`n== SDK verification =="
$checks = @(
    @{ Name = 'adb';                Path = 'platform-tools\adb.exe' },
    @{ Name = 'aapt2';              Path = 'build-tools\35.0.0\aapt2.exe' },
    @{ Name = 'android.jar';        Path = 'platforms\android-35\android.jar' },
    @{ Name = 'd8.bat';             Path = 'build-tools\35.0.0\d8.bat' },
    @{ Name = 'source.properties';  Path = 'platforms\android-35\source.properties' }
)
$allOk = $true
foreach ($c in $checks) {
    $full = Join-Path $SdkDir $c.Path
    $exists = Test-Path $full
    if (-not $exists) { $allOk = $false }
    Write-Output ("  {0,-18} {1}" -f $c.Name, $(if ($exists) { 'OK' } else { 'MISSING' }))
}
if (-not $allOk) { throw "SDK verification failed; see missing items above" }

Write-Output "`nSDK ready at: $SdkDir"
