# Registers the backup capture task volsurf-snapshot (kickoff Section 9, step 0.2; instruction 01b, step 1b.2).
# Monday to Friday at each [snapshot] local_task_times_utc time, runs the repo venv's Python on
# scripts/snapshot.py --runner local --out data/local_capture --upload better.
# Runs only while the user is logged on; starts when available after a missed time.
$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$python = Join-Path $repo ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "No venv Python at $python. Build it: uv venv --python 3.12; uv pip install -r requirements-lock.txt; uv pip install -e . --no-deps"
}

Push-Location $repo
try {
    $times = & $python -c "import tomllib; print('\n'.join(tomllib.load(open('config.toml', 'rb'))['snapshot']['local_task_times_utc']))"
} finally {
    Pop-Location
}
if (-not $times) { throw "Could not read [snapshot] local_task_times_utc from config.toml" }

# The trigger times are UTC instants. Each is built as a UTC DateTime and converted to local time, so
# New-ScheduledTaskTrigger stores a StartBoundary in UTC and the task fires at the same UTC instant in
# every time zone and season.
$today = [DateTime]::UtcNow.ToString("yyyy-MM-dd")
$days = "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
$triggers = @($times | ForEach-Object {
    $utc = [DateTime]::SpecifyKind(
        [DateTime]::ParseExact("$today $_", "yyyy-MM-dd HH:mm", [Globalization.CultureInfo]::InvariantCulture),
        [DateTimeKind]::Utc)
    New-ScheduledTaskTrigger -Weekly -DaysOfWeek $days -At $utc.ToLocalTime()
})
$action = New-ScheduledTaskAction -Execute "`"$python`"" `
    -Argument "scripts\snapshot.py --runner local --out data\local_capture --upload better" `
    -WorkingDirectory $repo
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive

Register-ScheduledTask -TaskName "volsurf-snapshot" -Action $action -Trigger $triggers -Settings $settings `
    -Principal $principal -Description "Backup daily option chain capture for Volatility-Surface-and-Event-Pricing" `
    -Force | Out-Null
Write-Output "Registered volsurf-snapshot at $($times -join ', ') UTC, Monday to Friday, in $repo"
foreach ($t in (Get-ScheduledTask -TaskName "volsurf-snapshot").Triggers) {
    Write-Output "StartBoundary $($t.StartBoundary)"
}
