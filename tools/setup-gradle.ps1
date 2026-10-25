<#
.SYNOPSIS
    Download a Gradle distribution into <project>/tools/gradle-<version> and create
    the project's gradlew wrapper files from it.

.DESCRIPTION
    Needed because this machine has no Gradle installed and no Android Studio.
    The official distribution is preferred; a mirror can be selected with -Mirror.

    NOTE: keep this file pure ASCII. Windows PowerShell 5.1 decodes BOM-less files as
    GBK on this machine, so non-ASCII text here would break parsing.

.EXAMPLE
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\setup-gradle.ps1
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\setup-gradle.ps1 -Mirror aliyun
#>
[CmdletBinding()]
param(
    [string]$Version = '8.9',
    [ValidateSet('official', 'aliyun', 'tencent', 'tuna')]
    [string]$Mirror = 'official',
    [int]$Threads = 8,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$installDir = Join-Path $root "tools\gradle-$Version"
$gradleBat = Join-Path $installDir 'bin\gradle.bat'

if ((Test-Path $gradleBat) -and -not $Force) {
    Write-Output "Gradle $Version already installed: $installDir"
} else {
    $url = switch ($Mirror) {
        'aliyun'  { "https://mirrors.aliyun.com/macports/distfiles/gradle/gradle-$Version-bin.zip" }
        'tencent' { "https://mirrors.cloud.tencent.com/gradle/gradle-$Version-bin.zip" }
        'tuna'    { "https://mirrors.tuna.tsinghua.edu.cn/gradle/gradle-$Version-bin.zip" }
        default   { "https://services.gradle.org/distributions/gradle-$Version-bin.zip" }
    }
    $backupUrl = if ($Mirror -eq 'official') {
        "https://mirrors.cloud.tencent.com/gradle/gradle-$Version-bin.zip"
    } else {
        "https://services.gradle.org/distributions/gradle-$Version-bin.zip"
    }

    $work = Join-Path $root 'tools\_gradle_setup'
    if (Test-Path $work) { Remove-Item $work -Recurse -Force }
    New-Item -ItemType Directory -Path $work -Force | Out-Null
    $archive = Join-Path $work "gradle-$Version-bin.zip"

    Write-Output "Downloading Gradle $Version with $Threads threads"

    # Multi-threaded segmented download; mirrors measured far faster than the official host.
    function Start-SegmentedDownload {
        param([string]$PrimaryUrl, [string]$BackupUrl, [string]$Dest, [int]$Segments)
        foreach ($u in @($PrimaryUrl, $BackupUrl)) {
            if (-not $u) { continue }
            Write-Output "Source: $u"
            $head = & curl.exe -s -L -I --connect-timeout 20 --max-time 60 $u 2>$null
            $lenLine = $head | Where-Object { $_ -match '(?i)^content-length:' } | Select-Object -Last 1
            $total = 0
            if ($lenLine) { $total = [int64](($lenLine -split ':')[1].Trim()) }
            if ($total -le 0) { Write-Output "  no content-length; skipping"; continue }
            Write-Output "  size: $([math]::Round($total/1MB,1)) MB"

            $chunk = [int64][math]::Ceiling($total / $Segments)
            $jobs = @()
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            for ($i = 0; $i -lt $Segments; $i++) {
                $from = $i * $chunk
                if ($from -ge $total) { continue }
                $to = [math]::Min($from + $chunk - 1, $total - 1)
                $part = "$Dest.part$i"
                $curlArgs = @('-s', '-L', '--fail', '--connect-timeout', '20', '--max-time', '1800',
                              '-r', "$from-$to", '-o', $part, $u)
                $jobs += Start-Job -ScriptBlock {
                    param($exe, $a)
                    & $exe @a 2>$null
                    $LASTEXITCODE
                } -ArgumentList 'curl.exe', $curlArgs
            }
            $jobs | Wait-Job | Out-Null
            $codes = $jobs | ForEach-Object { Receive-Job -Job $_ }
            $jobs | Remove-Job -Force
            $sw.Stop()

            $ok = $true
            foreach ($c in $codes) { if ($c -ne 0) { $ok = $false } }
            $parts = Get-ChildItem "$Dest.part*" -ErrorAction SilentlyContinue | Sort-Object { [int]($_.Name -replace '.*\.part', '') }
            $got = ($parts | Measure-Object -Property Length -Sum).Sum
            if (-not $ok -or $got -ne $total) {
                Write-Output "  incomplete ($got / $total bytes); trying next source"
                Remove-Item "$Dest.part*" -Force -ErrorAction SilentlyContinue
                continue
            }

            $out = [System.IO.File]::Create($Dest)
            try {
                foreach ($p in $parts) {
                    $in = [System.IO.File]::OpenRead($p.FullName)
                    try { $in.CopyTo($out) } finally { $in.Dispose() }
                }
            } finally { $out.Dispose() }
            Remove-Item "$Dest.part*" -Force -ErrorAction SilentlyContinue
            $seconds = [math]::Max($sw.Elapsed.TotalSeconds, 0.001)
            Write-Output ("  done: {0} MB in {1:N1}s = {2:N0} KB/s" -f [math]::Round($got/1MB,1), $seconds, ($got/1KB/$seconds))
            return $true
        }
        return $false
    }

    $downloaded = Start-SegmentedDownload -PrimaryUrl $url -BackupUrl $backupUrl -Dest $archive -Segments $Threads
    if (-not $downloaded) { throw "Download failed from all sources" }

    $size = (Get-Item $archive).Length
    if ($size -lt 50MB) { throw "Downloaded file is too small ($([math]::Round($size/1MB,1)) MB)" }
    Write-Output "Downloaded: $([math]::Round($size/1MB,1)) MB"

    Write-Output "Extracting..."
    $expanded = Join-Path $work 'expanded'
    Expand-Archive -Path $archive -DestinationPath $expanded -Force

    $inner = Get-ChildItem $expanded -Directory | Select-Object -First 1
    if (-not $inner) { throw "No Gradle directory found after extraction" }

    $toolsDir = Join-Path $root 'tools'
    if (Test-Path $installDir) { Remove-Item $installDir -Recurse -Force }
    Move-Item -Path $inner.FullName -Destination $installDir
    Remove-Item $work -Recurse -Force
    Write-Output "Installed: $installDir"
}

& $gradleBat --version | Select-Object -First 12

# ---- 生成项目内的 gradlew wrapper（Android 项目惯例）----
$wrapperJarSrc = Get-ChildItem (Join-Path $installDir 'lib\plugins') -Filter 'gradle-wrapper-main-*.jar' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $wrapperJarSrc) {
    $wrapperJarSrc = Get-ChildItem (Join-Path $installDir 'lib') -Recurse -Filter 'gradle-wrapper*.jar' -ErrorAction SilentlyContinue | Select-Object -First 1
}
if ($wrapperJarSrc) {
    $wrapperDir = Join-Path $root 'gradle\wrapper'
    New-Item -ItemType Directory -Path $wrapperDir -Force | Out-Null
    Copy-Item $wrapperJarSrc.FullName (Join-Path $wrapperDir 'gradle-wrapper.jar') -Force
    Write-Output ""
    Write-Output "Wrapper jar copied from $($wrapperJarSrc.Name)"
} else {
    Write-Output ""
    Write-Output "WARNING: gradle-wrapper jar not found in the distribution; gradlew will not work."
}

$gradlewBat = Join-Path $root 'gradlew.bat'
if (-not (Test-Path $gradlewBat)) {
    $batContent = @'
@rem HoMiSe: minimal Gradle wrapper launcher (pure ASCII)
@echo off
setlocal
set DIRNAME=%~dp0
set APP_HOME=%DIRNAME%
set CLASSPATH=%APP_HOME%\gradle\wrapper\gradle-wrapper.jar
if defined JAVA_HOME (
  set JAVACMD=%JAVA_HOME%\bin\java.exe
) else (
  set JAVACMD=java.exe
)
"%JAVACMD%" -Xmx64m -Xms64m -Dorg.gradle.appname=gradlew -classpath "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %*
endlocal
'@
    [System.IO.File]::WriteAllText($gradlewBat, $batContent, (New-Object System.Text.UTF8Encoding($false)))
    Write-Output "Created $gradlewBat"
}

Write-Output ""
Write-Output "Done. Build with: tools\build.ps1   (or tools\gradle-$Version\bin\gradle.bat)"
