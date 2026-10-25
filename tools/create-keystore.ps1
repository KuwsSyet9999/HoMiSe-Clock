<#
.SYNOPSIS
    Create the signing key used for HoMiSe release builds.

.DESCRIPTION
    Generates a keystore used to sign release APKs so they can be installed and tested.
    The default key is the conventional "debug" identity (alias android / store password
    android), which is fine for local testing but MUST NOT be used to distribute a build:
    the password is public. Replace it with a private key before any public release.

    Override the password with -StorePassword, or read it from the environment variable
    HOMISE_KEYSTORE_PASSWORD, to keep it out of the command line and shell history.

    NOTE: keep this file pure ASCII (Windows PowerShell 5.1 decodes BOM-less files as GBK here).

.EXAMPLE
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\create-keystore.ps1
#>
[CmdletBinding()]
param(
    [string]$OutDir,
    [string]$FileName = 'homise-debug.jks',
    [string]$Alias = 'android',
    [string]$StorePassword,
    [string]$KeyPassword,
    [string]$Dname = 'CN=HoMiSe Local Test, OU=Dev, O=HoMiSe, L=Unknown, ST=Unknown, C=CN',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $OutDir) { $OutDir = Join-Path $root 'keystore' }
New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

if (-not $StorePassword) {
    $StorePassword = $env:HOMISE_KEYSTORE_PASSWORD
    if (-not $StorePassword) { $StorePassword = 'android' }
}
if (-not $KeyPassword) { $KeyPassword = $StorePassword }

$keystorePath = Join-Path $OutDir $FileName
if ((Test-Path $keystorePath) -and -not $Force) {
    Write-Output "keystore already exists: $keystorePath"
    exit 0
}

$jdkHome = Join-Path $root 'tools\jdk-17'
$keytool = Join-Path $jdkHome 'bin\keytool.exe'
if (-not (Test-Path $keytool)) { throw "keytool not found: $keytool" }

Write-Output "creating keystore: $keystorePath"
& $keytool -genkeypair `
    -keystore $keystorePath `
    -alias $Alias `
    -keyalg RSA `
    -keysize 2048 `
    -validity 10000 `
    -storepass $StorePassword `
    -keypass $KeyPassword `
    -dname $Dname
if ($LASTEXITCODE -ne 0) { throw "keytool failed with exit code $LASTEXITCODE" }

Write-Output ""
Write-Output "keystore : $keystorePath"
Write-Output "alias    : $Alias"
Write-Output "note     : this is a local-test key with the public 'android' password;"
Write-Output "           create a private keystore before distributing anything."
