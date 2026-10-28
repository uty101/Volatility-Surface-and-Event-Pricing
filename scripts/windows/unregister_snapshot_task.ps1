# Removes the backup capture task volsurf-snapshot (kickoff Section 9, step 0.2).
$ErrorActionPreference = "Stop"

if (Get-ScheduledTask -TaskName "volsurf-snapshot" -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName "volsurf-snapshot" -Confirm:$false
    Write-Output "Unregistered volsurf-snapshot"
} else {
    Write-Output "volsurf-snapshot is not registered"
}
