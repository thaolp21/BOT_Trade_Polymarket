# Polymarket Trading Bot - Automated Reporting System

This system provides automated daily summaries and monthly Excel reports for your Polymarket trading activity.

## Quick Setup

### 1. Install Dependencies
```powershell
pip install requests openpyxl python-dotenv
```

### 2. Configure Environment
Create `.env` file with:
```
API_KEY=your_polymarket_api_key
PRIVATE_KEY=your_wallet_private_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
POLYGON_RPC_URL=https://polygon-rpc.com
```

### 3. Set Up Automated Scheduling
Run PowerShell as Administrator:

**Daily Summary (9pm GMT+7):**
```powershell
powershell -ExecutionPolicy Bypass -File schedule_daily_summary.ps1
```

**Monthly Excel (7am GMT+7, first day of month):**
```powershell
powershell -ExecutionPolicy Bypass -File schedule_monthly_excel.ps1
```

## Manual Usage

### Generate Reports Manually
```powershell
# Send daily summary only
python notification\send_reports.py --summary-only

# Send monthly Excel only  
python notification\send_reports.py --excel-only

# Interactive mode (choose options)
python notification\send_reports.py

# Test without sending
python notification\send_reports.py --dry-run
```

### Generate Excel File Only
```powershell
# All-time data
python export_data\fill_template.py

# Monthly data (December 2024)
python export_data\fill_template.py --time-range monthly --date 2024-12-01

# Custom date range
python export_data\fill_template.py --time-range custom --start-date 2024-11-01 --end-date 2024-11-30
```

## File Structure

```
BOT_Trade_Polymarket/
├── 📊 AUTOMATION CORE
│   ├── export_data/
│   │   ├── fill_template.py           # Excel generation engine
│   │   ├── template.xlsx              # Excel template
│   │   └── filled_template.xlsx       # Generated reports (gitignored)
│   ├── notification/
│   │   ├── send_reports.py            # Telegram orchestrator  
│   │   ├── fetch_notification_data.py # API data aggregation
│   │   ├── last_report.json           # Report tracking (gitignored)
│   │   └── combined_notification_data.json # Data cache (gitignored)
│   └── utils/
│       └── common.py                  # Shared utilities (datetime, rounding)
├── 🔧 SCHEDULING
│   ├── schedule_daily_summary.ps1     # Dual daily tasks (7am & 7pm GMT+7)
│   ├── schedule_monthly_excel.ps1     # Monthly Excel task (7am GMT+7, 1st day)
│   └── check_automation_status.ps1    # Status monitoring tool
├── 🤖 TRADING BOTS (Optional)
│   ├── order.py                       # Individual order placement
│   ├── order_all_markets.py           # Bulk market orders
│   ├── order_all_markets_repeat.py    # Continuous trading loop
│   ├── order_specs_generator.py       # Order specification generator
│   ├── cancel_orders.py               # Order cancellation
│   ├── find_market_by_slug.py         # Market lookup utility
│   ├── fetch_redeemable_positions.py  # Position checking
│   ├── test_clob_client.py            # Client testing
│   └── redeem_all.py                  # Position redemption
├── 📁 DATA STORAGE
│   ├── order_ids/                     # Tracking placed orders
│   ├── market_condition_ids/          # Market condition tracking
│   └── note/                          # Documentation and notes
├── 🌐 DASHBOARD (WIP)
│   ├── dashboard/frontend/            # Vue.js frontend
│   └── dashboard/backend/             # FastAPI backend
├── 📋 CONFIGURATION
│   ├── .env                           # Environment variables (gitignored)
│   ├── .gitignore                     # Git ignore rules
│   ├── requirements.txt               # Python dependencies
│   └── README.md                      # This file
```

## Scheduled Operations

### Daily Summary (9pm GMT+7)
- **Frequency:** Every day at 21:00 local time
- **Content:** Balance, profit, recent activity summary
- **Format:** HTML-formatted Telegram message
- **Task Name:** `PolymarketDailySummary`

### Monthly Excel (7am GMT+7, first day of month)
- **Frequency:** First day of each month at 07:00 local time  
- **Content:** Previous month's complete trading data
- **Format:** Excel file sent to Telegram
- **Task Name:** `PolymarketMonthlyExcel`

## Timezone Configuration

If your system timezone is not GMT+7, adjust the hour parameter:

**For GMT+0 timezone:**
```powershell
# Daily summary at 14:00 local (9pm GMT+7)
powershell -ExecutionPolicy Bypass -File schedule_daily_summary.ps1 -HourLocal 14

# Monthly Excel at 00:00 local (7am GMT+7)  
powershell -ExecutionPolicy Bypass -File schedule_monthly_excel.ps1 -HourLocal 0
```

**For GMT+9 timezone:**
```powershell
# Daily summary at 23:00 local (9pm GMT+7)
powershell -ExecutionPolicy Bypass -File schedule_daily_summary.ps1 -HourLocal 23

# Monthly Excel at 09:00 local (7am GMT+7)
powershell -ExecutionPolicy Bypass -File schedule_monthly_excel.ps1 -HourLocal 9
```

## Task Management

### View Scheduled Tasks
```powershell
Get-ScheduledTask -TaskName "Polymarket*"
```

### Remove Tasks
```powershell
Unregister-ScheduledTask -TaskName "PolymarketDailySummary" -Confirm:$false
Unregister-ScheduledTask -TaskName "PolymarketMonthlyExcel" -Confirm:$false
```

### Test Tasks Manually
```powershell
Start-ScheduledTask -TaskName "PolymarketDailySummary"
Start-ScheduledTask -TaskName "PolymarketMonthlyExcel"
```

## Troubleshooting

### Check Task History
```powershell
Get-WinEvent -FilterHashtable @{LogName="Microsoft-Windows-TaskScheduler/Operational"} | Where-Object {$_.Message -like "*Polymarket*"} | Select-Object -First 10
```

### Python Path Issues
If tasks fail, ensure Python is in system PATH or modify scripts to use full Python path:
```powershell
# Find Python location
Get-Command python

# Update scripts with full path if needed
$Action = New-ScheduledTaskAction -Execute "C:\Users\YourUser\AppData\Local\Programs\Python\Python313\python.exe" -Argument "$PythonScript $Arguments" -WorkingDirectory $WorkingDir
```

### Permission Issues
- Run PowerShell as Administrator when setting up tasks
- Ensure the user account has necessary permissions
- Check that Python can access the working directory

## Configuration Options

### Excel Analysis Parameters
Edit `export_data/fill_template.py`:
```python
TIME_FRAMES = [1, 3, 7, 30]  # Days for analysis
PRICE_RANGE = [0.1, 0.9]     # Price range for filtering
ANALYSIS_COLUMNS = {          # Column mapping
    'time_frame_1': 'C', 'time_frame_3': 'D', 
    'time_frame_7': 'E', 'time_frame_30': 'F'
}
```

### Telegram Message Format
Edit `notification/send_reports.py` `build_summary_text()` function to customize message format.

## API Dependencies

- **Polymarket API:** Trading data, positions, PnL
- **Polygon RPC:** On-chain USDC balance  
- **Telegram Bot API:** Message delivery

## File Outputs

- **Excel Reports:** `export_data/dd.MM.yyyy-dd.MM.yyyy.xlsx`
- **Metadata:** `notification/last_report.json`
- **Logs:** Windows Event Viewer (Task Scheduler logs)
