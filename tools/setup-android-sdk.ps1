<#
.SYNOPSIS
    Install the Android SDK command line tools and the packages this project needs.

.DESCRIPTION
    NOT USABLE ON THIS MACHINE - kept for reference only.

    sdkmanager fails here with "IO exception while downloading manifest" plus
    java.nio.file.NoSuchFileException under C:\Users\<non-ASCII>\.android\cache, even
    though plain Java can fetch the very same URLs (verified). Use
    tools\setup-android-sdk-manual.ps1 instead: it resolves package URLs from the
    official repository XML and unpacks them directly. That path is verified and
    produced the SDK this project currently builds with.

    This machine has neither Android Studio nor an SDK, so everything is installed into
    <project>/tools/android-sdk.

    Requires: tools\jdk-17 already installed (sdkmanager is a Java program).

    NOTES
      - Keep this file pure ASCII (Windows PowerShell 5.1 decodes BOM-less files as GBK here).
      - Networking required; run it with network access.

.EXAMPLE
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\setup-android-sdk-manual.ps1
#>
[CmdletBinding()]
param(
    [string]$SdkDir,
    [string]$CmdlineToolsUrl = 'https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip',
    [string[]]$Packages = @(
        'platform-tools',
        'platforms;android-35',
        'build-tools;35.0.0'
    )
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $SdkDir) { $SdkDir = Join-Path $root 'tools\android-sdk' }
$jdkHome = Join-Path $root 'tools\jdk-17'

$javaExe = Join-Path $jdkHome 'bin\java.exe'
if (-not (Test-Path $javaExe)) { throw "JDK 17 not found at $jdkHome. Run tools\install-jdk17.ps1 first." }

$sdkManagerBat = Join-Path $SdkDir 'cmdline-tools\latest\bin\sdkmanager.bat'
if (-not (Test-Path $sdkManagerBat)) {
    Write-Output "Installing Android command line tools into $SdkDir"
    $work = Join-Path $root 'tools\_sdk_setup'
    if (Test-Path $work) { Remove-Item $work -Recurse -Force }
    New-Item -ItemType Directory -Path $work -Force | Out-Null
    $archive = Join-Path $work 'cmdline-tools.zip'

    . (Join-Path $PSScriptRoot 'download-common.ps1')
    $downloaded = Start-FastDownload -Urls @($CmdlineToolsUrl) -Dest $archive -Threads 12
    if (-not $downloaded) { throw "Download failed: $CmdlineToolsUrl" }
    Write-Output "Downloaded: $([math]::Round((Get-Item $archive).Length/1MB,1)) MB"

    $expanded = Join-Path $work 'expanded'
    Expand-Archive -Path $archive -DestinationPath $expanded -Force

    # The archive contains cmdline-tools/bin/... which must become cmdline-tools/latest/bin/...
    $latestDir = Join-Path $SdkDir 'cmdline-tools\latest'
    New-Item -ItemType Directory -Path (Split-Path -Parent $latestDir) -Force | Out-Null
    if (Test-Path $latestDir) { Remove-Item $latestDir -Recurse -Force }
    Move-Item -Path (Join-Path $expanded 'cmdline-tools') -Destination $latestDir
    Remove-Item $work -Recurse -Force
    Write-Output "Command line tools installed: $latestDir"
}

if (-not (Test-Path $sdkManagerBat)) { throw "sdkmanager.bat still missing: $sdkManagerBat" }

$env:JAVA_HOME = $jdkHome
$env:ANDROID_HOME = $SdkDir
$env:ANDROID_SDK_ROOT = $SdkDir
$env:PATH = "$jdkHome\bin;$env:PATH"

Write-Output "`n== Accepting SDK licenses =="
# sdkmanager asks "Accept? (y/N)" per license; a file of many 'y' answers covers all of them.
$answerFile = Join-Path $env:TEMP 'homise_sdk_licenses.txt'
$answers = @()
for ($i = 0; $i -lt 40; $i++) { $answers += 'y' }
Set-Content -Path $answerFile -Value $answers -Encoding ascii
cmd /c "`"$sdkManagerBat`" --sdk_root=`"$SdkDir`" --licenses < `"$answerFile`""

Write-Output "`n== Installing packages: $($Packages -join ', ') =="
foreach ($pkg in $Packages) {
    Write-Output "--- $pkg ---"
    cmd /c "`"$sdkManagerBat`" --sdk_root=`"$SdkDir`" $pkg"
    if ($LASTEXITCODE -ne 0) { throw "Failed to install package: $pkg (exit $LASTEXITCODE)" }
}

Write-Output "`n== Installed SDK contents =="
Get-ChildItem $SdkDir | Select-Object -ExpandProperty Name
Write-Output "`nSDK ready at: $SdkDir"
