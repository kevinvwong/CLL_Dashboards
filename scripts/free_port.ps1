<#
Free a TCP port before the dashboard starts.

Called by run-dashboard.cmd. If something is already listening on the port, it
is stopped - but ONLY when it looks like this app's own server (its command line
names uvicorn AND app.main). Anything else holding the port is reported and left
alone, and the script exits non-zero, so the launcher does not start a server
that cannot bind and the user is told why.

Why this exists: a previous run of the dashboard, or another uvicorn, can still
hold the port. On Windows the new server then dies with
`[Errno 10048] only one usage of each socket address`. Stopping the stale server is
the fix, but killing an arbitrary process on that port would be reckless, hence
the ownership check.

Exit codes:
  0  the port is free (it was already, or a stale dashboard server was stopped)
  2  the port is held by a process that is not this app; nothing was killed
#>
param(
    [int]$Port = 8000,
    [switch]$Quiet
)

function Say($msg) { if (-not $Quiet) { Write-Host "[run-dashboard] $msg" } }

$listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
             Select-Object -ExpandProperty OwningProcess -Unique

if (-not $listeners) {
    Say "Port $Port is free."
    exit 0
}

$stopped = @()
$foreign = @()
foreach ($procId in $listeners) {
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$procId" -ErrorAction SilentlyContinue
    if (-not $proc) { continue }

    $cmd = [string]$proc.CommandLine
    $isOurs = ($cmd -match 'uvicorn') -and ($cmd -match 'app\.main')

    if ($isOurs) {
        Say "Stopping the existing dashboard server on port $Port (PID $procId)."
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        $stopped += $procId
    }
    else {
        $foreign += $proc
    }
}

if ($foreign.Count -gt 0) {
    Say "Port $Port is held by another program; not killing it."
    foreach ($f in $foreign) {
        Say "  PID $($f.ProcessId): $($f.CommandLine)"
    }
    Say "Stop it yourself, or pick another port: run-dashboard.cmd 8010"
    exit 2
}

# Give Windows a moment to release the socket after the stop.
if ($stopped.Count -gt 0) {
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 150
        $still = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if (-not $still) { break }
    }
    $still = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($still) {
        Say "The port is still held after stopping PID $($stopped -join ', ')."
        exit 2
    }
}

Say "Port $Port is free."
exit 0
