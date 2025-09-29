# Schedule Monthly Excel Report at 7am GMT+7 on First Day of Month
# Run this script as Administrator to set up the scheduled task

param(
    [int]$HourLocal = 7   # Default to 07:00 (7am) if your system is GMT+7
)

$TaskName = "PolymarketMonthlyExcel"
$WorkingDir = Get-Location
$PythonScript = "notification\send_reports.py"
$Arguments = "--excel-only"

Write-Host "Setting up monthly Excel task: $TaskName"
Write-Host "Schedule: First day of each month at ${HourLocal}:00 local time"
Write-Host "Working directory: $WorkingDir"
Write-Host "Command: python $PythonScript $Arguments"

# Check if task already exists and delete it
$ExistingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($ExistingTask) {
    Write-Host "Task $TaskName already exists. Removing..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the scheduled task - use daily trigger with manual monthly execution
$Action = New-ScheduledTaskAction -Execute "python" -Argument "$PythonScript $Arguments" -WorkingDirectory $WorkingDir

# Create a daily trigger at 7am but the script will check if it's the 1st of month
$Trigger = New-ScheduledTaskTrigger -Daily -At "${HourLocal}:00"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the task
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Send monthly Polymarket Excel report at 7am GMT+7 on first day of month (runs daily but only executes on 1st)"

Write-Host "Task $TaskName has been scheduled successfully!"
Write-Host ""
Write-Host "Usage examples:"
Write-Host "  Current timezone GMT+7: Run as-is"
Write-Host "  Current timezone GMT+9: powershell -ExecutionPolicy Bypass -File schedule_monthly_excel.ps1 -HourLocal 9"
Write-Host "  Current timezone GMT+0: powershell -ExecutionPolicy Bypass -File schedule_monthly_excel.ps1 -HourLocal 0"
Write-Host ""
Write-Host "To test manually: python $PythonScript $Arguments --dry-run"
Write-Host "Note: Excel is generated for the previous month when run on first day of month"
