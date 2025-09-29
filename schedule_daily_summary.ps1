# Schedule Daily Summary at 7am and 7pm GMT+7
# Run this script as Administrator to set up the scheduled tasks

param(
    [int]$Hour1Local = 7,   # Default to 07:00 (7am) if your system is GMT+7
    [int]$Hour2Local = 19   # Default to 19:00 (7pm) if your system is GMT+7
)

$TaskName1 = "PolymarketDailySummary_7AM"
$TaskName2 = "PolymarketDailySummary_7PM"
$WorkingDir = Get-Location
$PythonScript = "notification\send_reports.py"
$Arguments = "--summary-only"

Write-Host "Setting up TWO daily summary tasks:"
Write-Host "Task 1: $TaskName1 at ${Hour1Local}:00 local time"
Write-Host "Task 2: $TaskName2 at ${Hour2Local}:00 local time"
Write-Host "Working directory: $WorkingDir"
Write-Host "Command: python $PythonScript $Arguments"

# Remove old single task if it exists
$OldTask = Get-ScheduledTask -TaskName "PolymarketDailySummary" -ErrorAction SilentlyContinue
if ($OldTask) {
    Write-Host "Removing old single task: PolymarketDailySummary"
    Unregister-ScheduledTask -TaskName "PolymarketDailySummary" -Confirm:$false
}

# Check if new tasks already exist and delete them
$ExistingTask1 = Get-ScheduledTask -TaskName $TaskName1 -ErrorAction SilentlyContinue
if ($ExistingTask1) {
    Write-Host "Task $TaskName1 already exists. Removing..."
    Unregister-ScheduledTask -TaskName $TaskName1 -Confirm:$false
}

$ExistingTask2 = Get-ScheduledTask -TaskName $TaskName2 -ErrorAction SilentlyContinue
if ($ExistingTask2) {
    Write-Host "Task $TaskName2 already exists. Removing..."
    Unregister-ScheduledTask -TaskName $TaskName2 -Confirm:$false
}

# Create the scheduled tasks
$Action = New-ScheduledTaskAction -Execute "python" -Argument "$PythonScript $Arguments" -WorkingDirectory $WorkingDir
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Task 1: 7am GMT+7
$Trigger1 = New-ScheduledTaskTrigger -Daily -At "${Hour1Local}:00"
Register-ScheduledTask -TaskName $TaskName1 -Action $Action -Trigger $Trigger1 -Settings $Settings -Description "Send daily Polymarket summary at 7am GMT+7"

# Task 2: 7pm GMT+7  
$Trigger2 = New-ScheduledTaskTrigger -Daily -At "${Hour2Local}:00"
Register-ScheduledTask -TaskName $TaskName2 -Action $Action -Trigger $Trigger2 -Settings $Settings -Description "Send daily Polymarket summary at 7pm GMT+7"

Write-Host "Both daily summary tasks have been scheduled successfully!"
Write-Host ""
Write-Host "Usage examples:"
Write-Host "  Current timezone GMT+7: Run as-is (7am and 7pm)"
Write-Host "  Current timezone GMT+9: powershell -ExecutionPolicy Bypass -File schedule_daily_summary.ps1 -Hour1Local 9 -Hour2Local 21"
Write-Host "  Current timezone GMT+0: powershell -ExecutionPolicy Bypass -File schedule_daily_summary.ps1 -Hour1Local 0 -Hour2Local 12"
Write-Host ""
Write-Host "Scheduled tasks created:"
Write-Host "  $TaskName1 - Daily at ${Hour1Local}:00"
Write-Host "  $TaskName2 - Daily at ${Hour2Local}:00"
Write-Host ""
Write-Host "To test manually: python $PythonScript $Arguments --dry-run"
