<#
.SYNOPSIS
    Export a HoMiSe APK with the agreed file naming.

.DESCRIPTION
    Output file name:  HoMiSe_<version>_<yyyyMMddHHmmss>_<hash>.APK

      version : formal export  -> major.minor.patch (no iteration number)
                internal build -> major.minor.patch.iteration (-InternalBuild)
      time    : 14-digit local export time, yyyyMMddHHmmss
      hash    : SHA-256 of the APK, first 16 hex characters

    Guard rails, per VERSIONING.md:
      - A FORMAL export needs the requester's confirmation, recorded by running
        tools\version.ps1 -Action promote -Bump minor -ConfirmVersion.
        This script refuses to export unless version.json records that release.
      - An INTERNAL export (-InternalBuild) is not a formal version: the file name
        carries the iteration number and no confirmation is required. It is meant for
        testing only.
      - The APK is rebuilt first and must be signed; versionCode and versionName are
        read back and compared with version.json, and a mismatch aborts the export.

    NOTE: keep this file pure ASCII. Windows PowerShell 5.1 decodes BOM-less files as
    GBK on this machine, so non-ASCII text here would break parsing.

.EXAMPLE
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\export-apk.ps1 -ConfirmVersion
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\export-apk.ps1 -Variant debug -InternalBuild
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\export-apk.ps1 -DryRun

.NOTES
    Cleanup policy: every export removes older INTERNAL packages, keeping only the newest
    one, while all FORMAL releases are retained permanently. Pass -KeepAll to skip it.
#>
[CmdletBinding()]
param(
    [string]$SdkDir,
    [string]$OutDir,
    [ValidateSet('debug', 'release')]
    [string]$Variant = 'release',
    [switch]$SkipBuild,
    [switch]$DryRun,
    [switch]$ConfirmVersion,
    [switch]$InternalBuild,
    [switch]$KeepAll
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $SdkDir) { $SdkDir = Join-Path $root 'tools\android-sdk' }
if (-not $OutDir) { $OutDir = Join-Path $root 'release' }

# ---- 1. Read version state ----
$statePath = Join-Path $root 'version.json'
$state = [System.IO.File]::ReadAllText($statePath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
$major = [int]$state.current.major
$minor = [int]$state.current.minor
$patch = [int]$state.current.patch
$iteration = [int]$state.current.iteration
$formalVersion = "$major.$minor.$patch"
$internalVer = "$formalVersion.$iteration"
$expectedCode = $major * 1000000 + $minor * 10000 + $patch * 100 + 1 + $iteration

Write-Output "version.json : formal=$formalVersion internal=$internalVer code=$expectedCode"
Write-Output "stage        : $($state.stage)"

# Version used in the file name: formal = 3 fields, internal package = 4 fields.
if ($InternalBuild) {
    $nameVersion = $internalVer
    $exportMode = 'INTERNAL (iteration package)'
} else {
    $nameVersion = $formalVersion
    $exportMode = 'FORMAL'
}
Write-Output "export mode  : $exportMode"
Write-Output "name version : $nameVersion"

# ---- 2. A formal export must be confirmed and recorded first ----
$lastRelease = [string]$state.lastRelease
if (-not $DryRun -and -not $InternalBuild) {
    if (-not $lastRelease) {
        throw "Refused: no formal version has been confirmed yet. Run 'tools\version.ps1 -Action promote -Bump minor -ConfirmVersion' after the requester confirms the version number, then export again."
    }
    if ($lastRelease -ne $formalVersion) {
        throw "Refused: version.json records lastRelease=$lastRelease but the current formal version is $formalVersion. Confirm the version before exporting."
    }
    if (-not $ConfirmVersion) {
        throw "Refused: pass -ConfirmVersion to state that the requester confirmed this formal version."
    }
}

# ---- 3. Build the APK ----
if (-not $SkipBuild) {
    Write-Output ""
    Write-Output "== building ($Variant) =="
    $task = if ($Variant -eq 'release') { 'assembleRelease' } else { 'assembleDebug' }
    & (Join-Path $PSScriptRoot 'build.ps1') -Tasks $task -SdkDir $SdkDir
    if ($LASTEXITCODE -ne 0) { throw "build failed with exit code $LASTEXITCODE" }
}

$apkName = if ($Variant -eq 'release') { 'app-release.apk' } else { 'app-debug.apk' }
$apkPath = Join-Path $root "app\build\outputs\apk\$Variant\$apkName"
if (-not (Test-Path $apkPath)) {
    $unsigned = Join-Path $root "app\build\outputs\apk\$Variant\app-release-unsigned.apk"
    if (Test-Path $unsigned) {
        throw "Refused: only an UNSIGNED apk exists. An unsigned APK cannot be installed, so it must not be exported. Create a key with tools\create-keystore.ps1, rebuild, then export again."
    }
    throw "APK not found: $apkPath"
}

# ---- 4. The APK must actually be signed ----
$apksigner = Join-Path $SdkDir 'build-tools\35.0.0\apksigner.bat'
if (Test-Path $apksigner) {
    $env:JAVA_HOME = Join-Path $root 'tools\jdk-17'
    $env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
    $verify = cmd /c "`"$apksigner`" verify --print-certs `"$apkPath`" 2>&1"
    $signerLine = $verify | Where-Object { $_ -match 'certificate DN' } | Select-Object -First 1
    if (-not $signerLine) {
        throw "Refused: APK is not signed (apksigner verify failed). Output was: $($verify -join ' ')"
    }
    Write-Output "signer       : $($signerLine.Trim())"
} else {
    Write-Output "warning: apksigner not found, skipping signature verification"
}

# ---- 5. The built APK must carry the expected version ----
$aapt = Join-Path $SdkDir 'build-tools\35.0.0\aapt2.exe'
if (Test-Path $aapt) {
    $badging = cmd /c "`"$aapt`" dump badging `"$apkPath`" 2>&1"
    $pkgLine = $badging | Where-Object { $_ -match '^package:' } | Select-Object -First 1
    Write-Output ""
    Write-Output "APK badging  : $pkgLine"
    $codeMatch = [regex]::Match($pkgLine, "versionCode='(\d+)'")
    $nameMatch = [regex]::Match($pkgLine, "versionName='([^']*)'")
    $apkCode = if ($codeMatch.Success) { [int]$codeMatch.Groups[1].Value } else { -1 }
    $apkVerName = if ($nameMatch.Success) { $nameMatch.Groups[1].Value } else { '' }
    if ($apkCode -ne $expectedCode) {
        throw "Mismatch: APK versionCode=$apkCode but version.json implies $expectedCode"
    }
    if ($apkVerName -notlike "$formalVersion*") {
        throw "Mismatch: APK versionName='$apkVerName' does not start with $formalVersion"
    }
} else {
    Write-Output "warning: aapt2 not found, skipping APK version verification"
}

# ---- 6. Hash and name ----
$sha = (Get-FileHash -Path $apkPath -Algorithm SHA256).Hash.ToLowerInvariant()
$hash16 = $sha.Substring(0, 16)
$timestamp = Get-Date -Format 'yyyyMMddHHmmss'
$fileName = "HoMiSe_${nameVersion}_${timestamp}_${hash16}.APK"

Write-Output ""
Write-Output "APK          : $apkPath"
Write-Output "size         : $([math]::Round((Get-Item $apkPath).Length/1MB,2)) MB"
Write-Output "sha256       : $sha"
Write-Output "hash (16 hex): $hash16"
Write-Output "output name  : $fileName"

if ($DryRun) {
    Write-Output ""
    Write-Output "DRY RUN: nothing was copied."
    return
}

# ---- 7. Copy out ----
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
$target = Join-Path $OutDir $fileName
Copy-Item -Path $apkPath -Destination $target -Force

$shaFile = "$target.sha256"
"$sha  $fileName" | Set-Content -Path $shaFile -Encoding ascii

Write-Output ""
Write-Output "exported     : $target"
Write-Output "checksum file: $shaFile"
if (-not $InternalBuild) {
    Write-Output ""
    Write-Output "reminder: record this formal export in VERSIONING.md (release table) and version.json releases."
}

# ---- 8. Clean up old packages ----
# Policy: keep ONE internal package (the newest) plus every formal release.
# Formal versions carry no iteration number, so they are never removed.
if (-not $KeepAll) {
    $all = @(Get-ChildItem -Path $OutDir -Filter 'HoMiSe_*_*.APK' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -ne (Get-Item $target).FullName })
    $internal = @($all | Where-Object { $_.BaseName -match '^HoMiSe_\d+\.\d+\.\d+\.\d+_' })
    $removed = @()
    if ($internal.Count -gt 0) {
        # Sort by numeric version tuple, newest first: string comparison would order
        # "0.1.0.22" before "0.1.0.9" and keep the wrong package.
        $sorted = @($internal | Sort-Object -Descending -Property @{
            Expression = {
                $v = ($_.BaseName -split '_')[1] -split '\.'
                [double]$v[0] * 1e9 + [double]$v[1] * 1e6 + [double]$v[2] * 1e3 + [double]$v[3]
            }
        })
        # 只保留最新的一个内部包（同版本重复导出时保留最新那份），其余全部移除
        $keep = $sorted[0]
        foreach ($f in $sorted) {
            if ($f.FullName -eq $keep.FullName) { continue }
            $full = [System.IO.Path]::GetFullPath($f.FullName)
            $base = [System.IO.Path]::GetFullPath($OutDir)
            if (-not $full.StartsWith($base, [System.StringComparison]::OrdinalIgnoreCase)) {
                throw "Refused to delete outside the release directory: $full"
            }
            Remove-Item $full -Force
            Remove-Item "$full.sha256" -Force -ErrorAction SilentlyContinue
            $removed += $f.Name
        }
    }
    Write-Output ""
    if ($removed.Count -eq 0) {
        Write-Output "cleanup      : no older internal packages to remove"
    } else {
        Write-Output "cleanup      : removed $($removed.Count) older package(s)"
        $removed | ForEach-Object { Write-Output "               - $_" }
    }
    $kept = @(Get-ChildItem -Path $OutDir -Filter '*.APK' -File | Sort-Object Name)
    Write-Output "kept in $OutDir :"
    $kept | ForEach-Object { Write-Output "               $($_.Name)" }
    Write-Output "               (pass -KeepAll to skip this cleanup)"
}
