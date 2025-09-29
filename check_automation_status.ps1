# Simple Polymarket Automation Status Check
Write-Host "=== POLYMARKET AUTOMATION STATUS ===" -ForegroundColor Green

# Check tasks
$DailyTask1 = Get-ScheduledTask -TaskName "PolymarketDailySummary_7AM" -ErrorAction SilentlyContinue
$DailyTask2 = Get-ScheduledTask -TaskName "PolymarketDailySummary_7PM" -ErrorAction SilentlyContinue
$OldDailyTask = Get-ScheduledTask -TaskName "PolymarketDailySummary" -ErrorAction SilentlyContinue
$MonthlyTask = Get-ScheduledTask -TaskName "PolymarketMonthlyExcel" -ErrorAction SilentlyContinue

# Function to interpret task result codes
function Get-TaskResultStatus($ResultCode) {
    switch ($ResultCode) {
        0 { return @{ Status = "SUCCESS"; Color = "Green"; Description = "Task completed successfully" } }
        267011 { return @{ Status = "NEVER RUN"; Color = "Yellow"; Description = "Task has not yet run" } }
        2147942402 { return @{ Status = "TERMINATED"; Color = "Yellow"; Description = "Task was running or terminated by user/error" } }
        2147943645 { return @{ Status = "DISABLED"; Color = "Red"; Description = "Task is disabled" } }
        2147944300 { return @{ Status = "NOT FOUND"; Color = "Red"; Description = "Task not found" } }
        default { return @{ Status = "ERROR"; Color = "Red"; Description = "Task failed with code $ResultCode" } }
    }
}

# Daily Task Status - Check for new dual tasks first, then old single task
if ($DailyTask1 -and $DailyTask2) {
    # New dual task setup
    $DailyInfo1 = Get-ScheduledTaskInfo -TaskName "PolymarketDailySummary_7AM"
    $DailyInfo2 = Get-ScheduledTaskInfo -TaskName "PolymarketDailySummary_7PM"
    
    $DailyStatus1 = if ($DailyTask1.State -eq "Ready") { "RUNNING" } else { "NOT RUNNING" }
    $DailyColor1 = if ($DailyTask1.State -eq "Ready") { "Green" } else { "Red" }
    $ResultInfo1 = Get-TaskResultStatus $DailyInfo1.LastTaskResult
    
    $DailyStatus2 = if ($DailyTask2.State -eq "Ready") { "RUNNING" } else { "NOT RUNNING" }
    $DailyColor2 = if ($DailyTask2.State -eq "Ready") { "Green" } else { "Red" }
    $ResultInfo2 = Get-TaskResultStatus $DailyInfo2.LastTaskResult
    
    Write-Host "Daily Summary (7am GMT+7): $DailyStatus1" -ForegroundColor $DailyColor1
    Write-Host "Last run: $($DailyInfo1.LastRunTime)" -ForegroundColor White
    Write-Host "Last result: $($ResultInfo1.Status) ($($DailyInfo1.LastTaskResult)) - $($ResultInfo1.Description)" -ForegroundColor $ResultInfo1.Color
    Write-Host "Next run: $($DailyInfo1.NextRunTime)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Daily Summary (7pm GMT+7): $DailyStatus2" -ForegroundColor $DailyColor2
    Write-Host "Last run: $($DailyInfo2.LastRunTime)" -ForegroundColor White
    Write-Host "Last result: $($ResultInfo2.Status) ($($DailyInfo2.LastTaskResult)) - $($ResultInfo2.Description)" -ForegroundColor $ResultInfo2.Color
    Write-Host "Next run: $($DailyInfo2.NextRunTime)" -ForegroundColor Cyan
} elseif ($OldDailyTask) {
    # Old single task setup
    $DailyInfo = Get-ScheduledTaskInfo -TaskName "PolymarketDailySummary"
    $DailyStatus = if ($OldDailyTask.State -eq "Ready") { "RUNNING" } else { "NOT RUNNING" }
    $DailyColor = if ($OldDailyTask.State -eq "Ready") { "Green" } else { "Red" }
    $ResultInfo = Get-TaskResultStatus $DailyInfo.LastTaskResult
    
    Write-Host "Daily Summary (OLD - 9pm GMT+7): $DailyStatus" -ForegroundColor $DailyColor
    Write-Host "Last run: $($DailyInfo.LastRunTime)" -ForegroundColor White
    Write-Host "Last result: $($ResultInfo.Status) ($($DailyInfo.LastTaskResult)) - $($ResultInfo.Description)" -ForegroundColor $ResultInfo.Color
    Write-Host "Next run: $($DailyInfo.NextRunTime)" -ForegroundColor Cyan
    Write-Host "NOTE: Run schedule_daily_summary.ps1 to upgrade to dual 7am/7pm tasks" -ForegroundColor Yellow
} else {
    Write-Host "Daily Summary Tasks: NOT SETUP" -ForegroundColor Red
    Write-Host "Run: powershell -ExecutionPolicy Bypass -File schedule_daily_summary.ps1" -ForegroundColor Yellow
}

Write-Host ""

# Monthly Task Status
if ($MonthlyTask) {
    $MonthlyInfo = Get-ScheduledTaskInfo -TaskName "PolymarketMonthlyExcel"
    $MonthlyStatus = if ($MonthlyTask.State -eq "Ready") { "RUNNING" } else { "NOT RUNNING" }
    $MonthlyColor = if ($MonthlyTask.State -eq "Ready") { "Green" } else { "Red" }
    $MonthlyResultInfo = Get-TaskResultStatus $MonthlyInfo.LastTaskResult
    
    Write-Host "Monthly Excel (7am GMT+7, 1st): $MonthlyStatus" -ForegroundColor $MonthlyColor
    Write-Host "Last run: $($MonthlyInfo.LastRunTime)" -ForegroundColor White
    Write-Host "Last result: $($MonthlyResultInfo.Status) ($($MonthlyInfo.LastTaskResult)) - $($MonthlyResultInfo.Description)" -ForegroundColor $MonthlyResultInfo.Color
    
    # Check if NextRunTime is valid
    if ($MonthlyInfo.NextRunTime -and $MonthlyInfo.NextRunTime -gt (Get-Date)) {
        Write-Host "Next monthly run: $($MonthlyInfo.NextRunTime)" -ForegroundColor Cyan
    } else {
        Write-Host "Next monthly run: Checking trigger..." -ForegroundColor Yellow
        # Get trigger details
        $MonthlyTriggers = (Get-ScheduledTask -TaskName "PolymarketMonthlyExcel").Triggers
        if ($MonthlyTriggers) {
            Write-Host "Task is scheduled but may need trigger refresh" -ForegroundColor Yellow
        } else {
            Write-Host "Next monthly run: Not properly scheduled" -ForegroundColor Red
        }
    }
} else {
    Write-Host "Monthly Excel (7am GMT+7, 1st): NOT SETUP" -ForegroundColor Red
    Write-Host "Next monthly run: Not scheduled" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== TASK RESULT CODES REFERENCE ===" -ForegroundColor Green
Write-Host "0 = SUCCESS (Task completed successfully)" -ForegroundColor Green
Write-Host "267011 = NEVER RUN (Task has not yet run)" -ForegroundColor Yellow  
Write-Host "2147942402 = TERMINATED (Task was running or terminated by user/error)" -ForegroundColor Yellow
Write-Host "2147943645 = DISABLED (Task is disabled)" -ForegroundColor Red
Write-Host "2147944300 = NOT FOUND (Task not found)" -ForegroundColor Red
