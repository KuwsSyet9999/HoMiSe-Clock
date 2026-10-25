<#
.SYNOPSIS
    Shared download helpers for the HoMiSe tool chain.

.DESCRIPTION
    Everything here stays inside one process on purpose. Starting child PowerShell
    jobs to download in parallel does NOT work in this environment: the sandbox
    blocks the named pipes those jobs need, so their output never arrives.

    Parallelism therefore uses a single curl process with --parallel and a generated
    config file of range requests, falling back to a plain download when the server
    does not support ranges.

    NOTE: keep this file pure ASCII. Windows PowerShell 5.1 decodes BOM-less files as
    GBK on this machine, so non-ASCII text here would break parsing.
#>

function Get-UrlInfo {
    param([string]$Url)
    $head = & curl.exe -s -L -I --connect-timeout 20 --max-time 60 $Url 2>$null
    $size = 0
    $ranges = $false
    foreach ($line in $head) {
        if ($line -match '(?i)^content-length:\s*(\d+)') { $size = [int64]$Matches[1] }
        if ($line -match '(?i)^accept-ranges:\s*bytes') { $ranges = $true }
    }
    return [pscustomobject]@{ Size = $size; AcceptRanges = $ranges; Headers = $head }
}

function Invoke-CurlDownload {
    param([string]$Url, [string]$Dest)
    & curl.exe -s -L --fail --connect-timeout 20 --max-time 1800 -o $Dest $Url
    return $LASTEXITCODE
}

<#
    Downloads $PrimaryUrl into $Dest.
    Uses $Threads parallel range requests through one curl process when possible;
    if the response is incomplete or ranges are unsupported, every source is retried
    as a plain sequential download before giving up.
#>
function Start-FastDownload {
    param(
        [string[]]$Urls,
        [string]$Dest,
        [int]$Threads = 8,
        [int64]$MinSizeForSegments = 20MB
    )

    foreach ($url in $Urls) {
        if (-not $url) { continue }
        Write-Output "Source: $url"
        $info = Get-UrlInfo -Url $url
        if ($info.Size -le 0) { Write-Output "  no content-length reported; trying plain download"; }
        else { Write-Output "  size: $([math]::Round($info.Size/1MB,1)) MB, ranges: $($info.AcceptRanges)" }

        if ($info.Size -gt $MinSizeForSegments -and $info.AcceptRanges) {
            if (Test-Path "$Dest.part*") { Remove-Item "$Dest.part*" -Force -ErrorAction SilentlyContinue }
            $chunk = [int64][math]::Ceiling($info.Size / $Threads)

            # One curl process per range, started concurrently through System.Diagnostics
            # rather than curl's own --parallel: with --parallel, curl de-duplicates
            # identical URLs and writes the SAME bytes into every output file (measured),
            # which yields a file of the right size with wrong content.
            # Child PowerShell jobs are not an option either (sandbox blocks their pipes),
            # so curl writes each part directly and reports its exit code through a file.
            $procs = @()
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            for ($i = 0; $i -lt $Threads; $i++) {
                $from = $i * $chunk
                if ($from -ge $info.Size) { continue }
                $to = [math]::Min($from + $chunk - 1, $info.Size - 1)
                $part = "$Dest.part$i"
                $psi = New-Object System.Diagnostics.ProcessStartInfo
                $psi.FileName = 'curl.exe'
                $psi.Arguments = "-s -L --fail --connect-timeout 20 --max-time 1800 -r $from-$to -o `"$part`" `"$url`""
                $psi.UseShellExecute = $false
                $psi.CreateNoWindow = $true
                $procs += [System.Diagnostics.Process]::Start($psi)
            }
            foreach ($p in $procs) { $p.WaitForExit() }
            $sw.Stop()

            $codes = $procs | ForEach-Object { $_.ExitCode }

            $parts = Get-ChildItem "$Dest.part*" -ErrorAction SilentlyContinue |
                Where-Object { $_.Name -notlike '*.exit' } |
                Sort-Object { [int]($_.Name -replace '^.*\.part(\d+)$', '$1') }
            $got = 0
            if ($parts) { $got = ($parts | Measure-Object -Property Length -Sum).Sum }

            $allZero = $true
            foreach ($c in $codes) { if ($c -ne 0) { $allZero = $false } }

            if ($allZero -and $got -eq $info.Size -and (($parts | Measure-Object).Count) -eq $procs.Count) {
                $out = [System.IO.File]::Create($Dest)
                try {
                    foreach ($p in $parts) {
                        $in = [System.IO.File]::OpenRead($p.FullName)
                        try { $in.CopyTo($out) } finally { $in.Dispose() }
                    }
                } finally { $out.Dispose() }
                Remove-Item "$Dest.part*" -Force -ErrorAction SilentlyContinue
                $seconds = [math]::Max($sw.Elapsed.TotalSeconds, 0.001)
                Write-Output ("  done (parallel): {0} MB in {1:N1}s = {2:N0} KB/s" -f [math]::Round($got/1MB,1), $seconds, ($got/1KB/$seconds))
                return $true
            }
            Write-Output "  parallel attempt incomplete ($got / $($info.Size) bytes, exits: $($codes -join ',')); falling back"
            Remove-Item "$Dest.part*" -Force -ErrorAction SilentlyContinue
        }

        Write-Output "  downloading sequentially..."
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        $code = Invoke-CurlDownload -Url $url -Dest $Dest
        $sw.Stop()
        if ($code -eq 0 -and (Test-Path $Dest)) {
            $got = (Get-Item $Dest).Length
            if ($info.Size -gt 0 -and $got -ne $info.Size) {
                Write-Output "  size mismatch ($got / $($info.Size)); trying next source"
                continue
            }
            $seconds = [math]::Max($sw.Elapsed.TotalSeconds, 0.001)
            Write-Output ("  done: {0} MB in {1:N1}s = {2:N0} KB/s" -f [math]::Round($got/1MB,1), $seconds, ($got/1KB/$seconds))
            return $true
        }
        Write-Output "  failed (curl exit $code); trying next source"
    }
    return $false
}
