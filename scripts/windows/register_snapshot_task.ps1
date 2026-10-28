# Registers the backup capture task volsurf-snapshot (kickoff Section 9, step 0.2).
# Monday to Friday at each [snapshot] local_task_times_london time, runs the repo venv's Python on
# scripts/snapshot.py --runner local --out data/local_capture --upload if-missing.
# Runs only while the user is logged on; starts when available after a missed time.
$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$python = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "No venv Python at $python. Build it: uv venv --python 3.12; uv pip install -r requirements-lock.txt; uv pip install -e . --no-deps"
}
# The trigger times are London wall-clock times, and Task Scheduler uses the machine's time zone.
if ((Get-TimeZone).Id -ne "GMT Standard Time") {
    throw "Machine time zone is $((Get-TimeZone).Id), not GMT Standard Time (London); the task times would be wrong."
}

Push-Location $repo
try {
    $times = & $python -c "import tomllib; print('\n'.join(tomllib.load(open('config.toml', 'rb'))['snapshot']['local_task_times_london']))"
} finally {
    Pop-Location
}
if (-not $times) { throw "Could not read [snapshot] local_task_times_london from config.toml" }

$days = "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
$triggers = @($times | ForEach-Object { New-ScheduledTaskTrigger -Weekly -DaysOfWeek $days -At $_ })
$action = New-ScheduledTaskAction -Execute "`"$python`"" `
    -Argument "scripts\snapshot.py --runner local --out data\local_capture --upload if-missing" `
    -WorkingDirectory $repo
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

Register-ScheduledTask -TaskName "volsurf-snapshot" -Action $action -Trigger $triggers -Settings $settings `
    -Principal $principal -Description "Backup daily option chain capture for Volatility-Surface-and-Event-Pricing" `
    -Force | Out-Null
Write-Output "Registered volsurf-snapshot at $($times -join ', ') London, Monday to Friday, in $repo"
