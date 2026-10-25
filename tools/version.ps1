<#
.SYNOPSIS
    HoMiSe version manager - the single authority for version numbers.

.DESCRIPTION
    Implements VERSIONING.md exactly:
      - during internal iterations only the 4th field (iteration) changes;
      - a formal version is exported ONLY when -ConfirmVersion is passed;
      - a formal version never carries an iteration number, and after export the
        iteration counter restarts at 0.

    Fields: major.minor.patch.iteration
      major     : requested by the requester, or a huge change to core features
      minor     : a new module or new feature, while major stays
      patch     : a bug fix or a change of look/behavior, while major and minor stay
      iteration : every internal iteration (dropped from formal versions)

    NOTE: keep this file pure ASCII. Windows PowerShell 5.1 decodes BOM-less files as
    GBK on this machine, so non-ASCII text here would break parsing.

.EXAMPLE
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\version.ps1 -Action show
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\version.ps1 -Action bump -Summary "did something"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\version.ps1 -Action promote -Bump minor -ConfirmVersion -Summary "first release"
#>
[CmdletBinding()]
param(
    [ValidateSet('show', 'bump', 'promote')]
    [string]$Action = 'show',

    [ValidateSet('major', 'minor', 'patch', 'none')]
    [string]$Bump = 'minor',

    [switch]$ConfirmVersion,

    [string]$Summary = ''
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$statePath = Join-Path $root 'version.json'
$docPath = Join-Path $root 'VERSIONING.md'

if (-not (Test-Path $statePath)) { throw "version.json not found: $statePath" }

$state = [System.IO.File]::ReadAllText($statePath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json

function Format-Version([int]$ma, [int]$mi, [int]$pa, [int]$it, [bool]$formal) {
    if ($formal) { return "$ma.$mi.$pa" }
    return "$ma.$mi.$pa.$it"
}

function Get-VersionCode([int]$ma, [int]$mi, [int]$pa, [int]$it) {
    # Must stay in sync with app/build.gradle.kts: Android requires a positive,
    # monotonically increasing versionCode, so the base carries a +1.
    return $ma * 1000000 + $mi * 10000 + $pa * 100 + 1 + $it
}

function Insert-ArrayEntry {
    # Append an entry to a JSON array, keeping the file's existing layout.
    # $st is unused for now but keeps the call sites uniform with Save-State.
    param([string]$Text, $st, [string]$ArrayKey, [string]$EntryJson, [string]$Indent)
    $m = [regex]::Match($Text, '"' + $ArrayKey + '"\s*:\s*\[', 'Singleline')
    if (-not $m.Success) { throw "array '$ArrayKey' not found" }
    $open = $Text.IndexOf('[', $m.Index)
    $close = $Text.IndexOf(']', $open)
    if ($close -lt 0) { throw "array '$ArrayKey' is not terminated" }
    $hasItems = $Text.Substring($open + 1, $close - $open - 1).Trim().Length -gt 0
    $insert = if ($hasItems) { ',' + "`r`n" + $Indent + $EntryJson } else { "`r`n" + $Indent + $EntryJson + "`r`n" }
    return $Text.Substring(0, $close) + $insert + $Text.Substring($close)
}

function ConvertTo-EntryJson($obj, [string]$Indent) {
    # Multi-line entry that matches the file's existing indentation, so appended
    # records stay readable instead of collapsing onto one long line.
    $flat = $obj | ConvertTo-Json -Compress
    $pretty = $flat -replace ',"', ("," + "`r`n" + $Indent + '  "')
    $pretty = $pretty -replace '^\{', ('{' + "`r`n" + $Indent + '  ')
    return $pretty + "`r`n" + $Indent
}

function Save-State($st, [string]$path, [hashtable]$ArrayEntry) {
    # Rewrite only the values, never the whole file with ConvertTo-Json: that tool
    # reformats indentation (2 -> 4 spaces), which the app/build.gradle.kts parser
    # depends on. Keeping the layout stable keeps version parsing safe.
    $st.updated = (Get-Date -Format 'yyyy-MM-dd')
    $text = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)

    # Only the top-level internalVersion may be rewritten. It sits right after
    # "lastRelease" (see version.json's field order), so anchor there: a plain global
    # replace would hit the "internalVersion" fields inside the history array and
    # corrupt every past record.
    $text = [regex]::Replace($text, '("lastRelease"\s*:\s*(?:null|"[^"]*")\s*,\s*"internalVersion"\s*:\s*)(null|"[^"]*")',
        '${1}"' + $st.internalVersion + '"', 1)
    $text = [regex]::Replace($text, '"stage"\s*:\s*"[^"]*"',
        '"stage": "' + $st.stage + '"', 1)
    $releaseText = if ($st.releaseVersion) { '"' + $st.releaseVersion + '"' } else { 'null' }
    $text = [regex]::Replace($text, '"releaseVersion"\s*:\s*(null|"[^"]*")',
        '"releaseVersion": ' + $releaseText, 1)
    $lastText = if ($st.lastRelease) { '"' + $st.lastRelease + '"' } else { 'null' }
    $text = [regex]::Replace($text, '"lastRelease"\s*:\s*(null|"[^"]*")',
        '"lastRelease": ' + $lastText, 1)

    $cm = [regex]::Match($text, '"current"\s*:\s*\{[^}]*\}', 'Singleline')
    if (-not $cm.Success) { throw "cannot locate the current block in $path" }
    $block = $cm.Value
    $block = [regex]::Replace($block, '"major"\s*:\s*\d+', '"major": ' + $st.current.major)
    $block = [regex]::Replace($block, '"minor"\s*:\s*\d+', '"minor": ' + $st.current.minor)
    $block = [regex]::Replace($block, '"patch"\s*:\s*\d+', '"patch": ' + $st.current.patch)
    $block = [regex]::Replace($block, '"iteration"\s*:\s*\d+', '"iteration": ' + $st.current.iteration)
    $text = $text.Substring(0, $cm.Index) + $block + $text.Substring($cm.Index + $cm.Length)

    $text = [regex]::Replace($text, '"updated"\s*:\s*"[^"]*"',
        '"updated": "' + $st.updated + '"', 1)

    if ($ArrayEntry) {
        if (-not $text.Contains($ArrayEntry.Json)) {
            $text = Insert-ArrayEntry -Text $text -st $st -ArrayKey $ArrayEntry.Key -EntryJson $ArrayEntry.Json -Indent $ArrayEntry.Indent
        }
    }

    [System.IO.File]::WriteAllText($path, $text, (New-Object System.Text.UTF8Encoding($false)))
}

$ma = [int]$state.current.major
$mi = [int]$state.current.minor
$pa = [int]$state.current.patch
$it = [int]$state.current.iteration

switch ($Action) {

    'show' {
        Write-Output "project      : $($state.project)"
        Write-Output "stage        : $($state.stage)"
        Write-Output "internal ver : $(Format-Version $ma $mi $pa $it $false)"
        Write-Output "release base : $(Format-Version $ma $mi $pa 0 $true)"
        if ($state.lastRelease) { Write-Output "last release : $($state.lastRelease)" }
        else { Write-Output "last release : (none yet)" }
        if ($state.nextRelease) { Write-Output "next release : $($state.nextRelease.plannedVersion) (bump=$($state.nextRelease.bump))" }
        Write-Output "iteration    : $it"
        Write-Output "versionCode  : $(Get-VersionCode $ma $mi $pa $it)"
    }

    'bump' {
        if ($state.stage -ne 'internal') { throw "stage is $($state.stage); iteration bump is only valid while internal" }
        $it = $it + 1
        $state.current.iteration = $it
        $state.stage = 'internal'
        $state.internalVersion = Format-Version $ma $mi $pa $it $false
        # releaseVersion deliberately keeps pointing at the most recent formal version;
        # an internal iteration must not erase the record of what was released.
        $entry = [pscustomobject]@{
            internalVersion = $state.internalVersion
            date            = (Get-Date -Format 'yyyy-MM-dd')
            summary         = $Summary
        }
        $state.history = @($state.history) + @($entry)
        Save-State $state $statePath -ArrayEntry @{
            Key    = 'history'
            Json   = (ConvertTo-EntryJson $entry '                    ')
            Indent = '                    '
        }
        Write-Output "internal iteration -> $($state.internalVersion)"
        Write-Output "versionCode        : $(Get-VersionCode $ma $mi $pa $it)"
        if ($Summary) { Write-Output "summary            : $Summary" }
        Write-Output "reminder: append this row to the iteration table in $docPath"
    }

    'promote' {
        if (-not $ConfirmVersion) {
            throw "Export refused: a formal version needs the requester's confirmation. Pass -ConfirmVersion together with -Bump once it is confirmed."
        }
        switch ($Bump) {
            'major' { $ma = $ma + 1; $mi = 0; $pa = 0 }
            'minor' { $mi = $mi + 1; $pa = 0 }
            'patch' { $pa = $pa + 1 }
            'none' { }
        }
        $formal = Format-Version $ma $mi $pa 0 $true
        $baselineIteration = $it

        $state.current.major = $ma
        $state.current.minor = $mi
        $state.current.patch = $pa
        $state.current.iteration = 0
        $state.stage = 'internal'
        $state.internalVersion = Format-Version $ma $mi $pa 0 $false
        $state.releaseVersion = $formal
        $state.lastRelease = $formal

        $release = [pscustomobject]@{
            version      = $formal
            date         = (Get-Date -Format 'yyyy-MM-dd')
            bump         = $Bump
            fromInternal = Format-Version $ma $mi $pa $baselineIteration $false
            summary      = $Summary
            versionCode  = (Get-VersionCode $ma $mi $pa 0)
        }
        $state.releases = @($state.releases) + @($release)
        Save-State $state $statePath -ArrayEntry @{
            Key    = 'releases'
            Json   = (ConvertTo-EntryJson $release '                     ')
            Indent = '                     '
        }

        Write-Output "formal version exported : $formal"
        Write-Output "bump type               : $Bump"
        Write-Output "versionCode             : $(Get-VersionCode $ma $mi $pa 0)"
        Write-Output "iteration restarted at  : $($state.internalVersion)"
        Write-Output "reminder: append this row to the release table in $docPath"
    }
}
