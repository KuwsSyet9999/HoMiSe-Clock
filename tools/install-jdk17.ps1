<#
.SYNOPSIS
    Download and install JDK 17 (Adoptium Temurin LTS) into <project>/tools/jdk-17.

.DESCRIPTION
    The Android build chain (AGP 8.x) supports JDK 17; the machine's JDK 27 is too new.
    The JDK is installed inside the project and the system PATH is left untouched, so
    other JDKs on the machine are unaffected.

    This script needs network access and a build command that can reach the network.

    NOTE: keep this file pure ASCII. Windows PowerShell 5.1 decodes BOM-less files as
    GBK on this machine, so non-ASCII text here would break parsing.

.EXAMPLE
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\install-jdk17.ps1
#>
[CmdletBinding()]
param(
    [string]$InstallDir,
    [string[]]$Urls = @(
        'https://mirrors.huaweicloud.com/openjdk/17.0.2/openjdk-17.0.2_windows-x64_bin.zip',
        'https://mirrors.tuna.tsinghua.edu.cn/Adoptium/17/jdk/x64/windows/OpenJDK17U-jdk_x64_windows_hotspot_17.0.20.1_1.zip',
        'https://api.adoptium.net/v3/binary/latest/17/ga/windows/x64/jdk/hotspot/normal/eclipse'
    ),
    [int]$Threads = 12,
    [switch]$KeepArchive
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $InstallDir) { $InstallDir = Join-Path $root 'tools\jdk-17' }

$javaExe = Join-Path $InstallDir 'bin\java.exe'
if (Test-Path $javaExe) {
    Write-Output "Already installed, skipping download: $javaExe"
    # java -version writes to stderr; cmd /c keeps powershell from treating it as an error.
    cmd /c "`"$javaExe`" -version 2>&1" | Select-Object -First 3
    exit 0
}

$work = Join-Path $root 'tools\_jdk17_setup'
if (Test-Path $work) { Remove-Item $work -Recurse -Force }
New-Item -ItemType Directory -Path $work -Force | Out-Null
$archive = Join-Path $work 'jdk17.zip'

Write-Output "Downloading JDK 17 (Temurin LTS, windows x64), about 182 MB..."
Write-Output "Parallel segments: $Threads"

# Shared download helper; it keeps parallel range requests inside ONE curl process
# because child PowerShell jobs cannot exchange data in this sandbox.
. (Join-Path $PSScriptRoot 'download-common.ps1')

$downloaded = Start-FastDownload -Urls $Urls -Dest $archive -Threads $Threads
if (-not $downloaded) { throw "Download failed from all sources" }

if (-not (Test-Path $archive)) { throw "Download failed: no file produced" }
$size = (Get-Item $archive).Length
if ($size -lt 50MB) { throw "Downloaded file is too small ($([math]::Round($size/1MB,1)) MB); not a JDK archive" }
Write-Output "Downloaded: $([math]::Round($size/1MB,1)) MB"

Write-Output "Extracting..."
$expanded = Join-Path $work 'expanded'
Expand-Archive -Path $archive -DestinationPath $expanded -Force

$inner = Get-ChildItem $expanded -Directory | Select-Object -First 1
if (-not $inner) { throw "No JDK directory found after extraction" }
Write-Output "Extracted: $($inner.FullName)"

if (Test-Path $InstallDir) { Remove-Item $InstallDir -Recurse -Force }
Move-Item -Path $inner.FullName -Destination $InstallDir
if (-not $KeepArchive) { Remove-Item $work -Recurse -Force }

if (-not (Test-Path $javaExe)) { throw "java.exe missing after install: $javaExe" }
Write-Output ""
Write-Output "Installed to: $InstallDir"
cmd /c "`"$javaExe`" -version 2>&1" | Select-Object -First 3
Write-Output ""
Write-Output "Project builds should use: -Dorg.gradle.java.home=$InstallDir"