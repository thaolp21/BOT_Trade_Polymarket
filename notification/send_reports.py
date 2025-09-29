import os
import sys
import json
from datetime import datetime, timedelta
import calendar
import argparse
from zoneinfo import ZoneInfo
import requests
from dotenv import load_dotenv

# Ensure project root (parent of this directory) is on sys.path for 'utils' and other modules
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from notification.fetch_notification_data import generate_summary  # noqa: E402

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
EXPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'export_data')
FILL_TEMPLATE_SCRIPT = os.path.join(EXPORT_DIR, 'fill_template.py')
LAST_REPORT_META = os.path.join(EXPORT_DIR, 'last_report.json')
DEFAULT_EPOCH_START_LOCAL = datetime(2025, 9, 24, 0, 0, 0, tzinfo=ZoneInfo('Asia/Bangkok'))  # 24/09/2025 00:00:00 GMT+7


def send_telegram_message(text: str, parse_mode: str | None = None) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print('Telegram credentials missing.')
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        r = requests.post(url, data=payload, timeout=30)
        if r.status_code == 200:
            print('Sent message.')
            return True
        print(f'Failed to send message: {r.status_code} {r.text}')
    except Exception as e:
        print(f'Error sending message: {e}')
    return False


def send_telegram_document(file_path: str, caption: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print('Telegram credentials missing.')
        return False
    if not os.path.isfile(file_path):
        print(f'File not found: {file_path}')
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(file_path, 'rb') as f:
            files = {'document': (os.path.basename(file_path), f)}
            data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': caption}
            r = requests.post(url, data=data, files=files, timeout=60)
            if r.status_code == 200:
                print('Sent document.')
                return True
            print(f'Failed to send document: {r.status_code} {r.text}')
    except Exception as e:
        print(f'Error sending document: {e}')
    return False


def build_summary_text(summary: dict) -> tuple[str, str]:
    # Handle profit possibly being a tuple (timestamp, value)
    raw_profit = summary.get('profit')
    if isinstance(raw_profit, (list, tuple)) and raw_profit:
        profit_val = raw_profit[-1]
    else:
        profit_val = raw_profit
    pending_claimable = summary.get('pending_claimable')
    if isinstance(pending_claimable, (list, tuple)) and pending_claimable:
        pending_claimable_val = pending_claimable[-1]
    else:
        pending_claimable_val = pending_claimable
    balance_val = summary.get('balance')
    arrow = ''
    if isinstance(profit_val, (int, float)):
        arrow = '🟢' if profit_val > 0 else ('🔻' if profit_val < 0 else '⚖️')
    profit_str = profit_val
    balance_str = balance_val
    pending_str = pending_claimable_val
    retrieved = summary.get('retrieved_at')
    # HTML formatted message
    html = (
        f"<i>{retrieved}</i>\n"
        f"<b>Balance:</b> <code>{balance_str}</code>\n"
        f"<b>Profit:</b> <code>{profit_str}</code> {arrow}\n"
        f"<b>Pending Claimable:</b> <code>{pending_str}</code>\n"
    )
    # Plain fallback text
    plain = (
        f"Time: {retrieved}\n"
        f"Balance: {balance_str}\n"
        f"Profit: {profit_str} {arrow}\n"
        f"Pending Claimable: {pending_str}\n"
    )
    return html, plain


def is_last_day_of_month(dt: datetime) -> bool:
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    return dt.day == last_day


def generate_excel_with_range(from_ts: int, to_ts: int):
    """Generate Excel by temporarily modifying FROM_TIME and TO_TIME in fill_template.py"""
    if not os.path.isfile(FILL_TEMPLATE_SCRIPT):
        print('fill_template.py not found, skipping excel generation.')
        return False
    
    # Read the current file
    try:
        with open(FILL_TEMPLATE_SCRIPT, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Store original values
        import re
        from_match = re.search(r"FROM_TIME='(\d+)'", content)
        to_match = re.search(r"TO_TIME='(\d+)'", content)
        original_from = from_match.group(1) if from_match else None
        original_to = to_match.group(1) if to_match else None
        
        # Replace with new values
        new_content = re.sub(r"FROM_TIME='(\d+)'", f"FROM_TIME='{from_ts}'", content)
        new_content = re.sub(r"TO_TIME='(\d+)'", f"TO_TIME='{to_ts}'", new_content)
        
        # Write modified file
        with open(FILL_TEMPLATE_SCRIPT, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Run the script
        cmd = f"python {FILL_TEMPLATE_SCRIPT}"
        print(f'Running: {cmd}')
        code = os.system(cmd)
        
        # Restore original values
        if original_from and original_to:
            restored_content = re.sub(r"FROM_TIME='(\d+)'", f"FROM_TIME='{original_from}'", new_content)
            restored_content = re.sub(r"TO_TIME='(\d+)'", f"TO_TIME='{original_to}'", restored_content)
            with open(FILL_TEMPLATE_SCRIPT, 'w', encoding='utf-8') as f:
                f.write(restored_content)
        
        if code != 0:
            print(f'Excel generation exited with code {code}')
            return False
        else:
            print('Excel generation complete.')
            return True
            
    except Exception as e:
        print(f'Error generating Excel: {e}')
        return False


def _start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _end_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=23, minute=59, second=59, microsecond=0)


def _to_unix(dt: datetime) -> int:
    return int(dt.timestamp())


def compute_range(args, now_local: datetime) -> tuple[int,int,str]:
    tz = ZoneInfo('Asia/Bangkok')
    # --custom-date FROM_DATE TO_DATE (format: YYYY-MM-DD)
    if args.custom_date:
        try:
            from_date = datetime.strptime(args.custom_date[0], '%Y-%m-%d').replace(tzinfo=tz)
            to_date = datetime.strptime(args.custom_date[1], '%Y-%m-%d').replace(tzinfo=tz)
        except ValueError:
            raise SystemExit('Invalid --custom-date values, use YYYY-MM-DD YYYY-MM-DD')
        from_dt = _start_of_day(from_date)
        to_dt = _end_of_day(to_date) + timedelta(seconds=1)  # exclusive end
        label = f"custom {from_dt.strftime('%d.%m.%Y')}-{to_date.strftime('%d.%m.%Y')}"
        return _to_unix(from_dt), _to_unix(to_dt), label
    # --from-last-report
    if args.from_last_report and os.path.isfile(LAST_REPORT_META):
        try:
            with open(LAST_REPORT_META,'r',encoding='utf-8') as f:
                meta = json.load(f)
            last_to = int(meta.get('to_time'))  # exclusive
            from_dt = datetime.fromtimestamp(last_to, tz)
            from_dt = _start_of_day(from_dt)  # ensure start-of-day
        except Exception:
            from_dt = DEFAULT_EPOCH_START_LOCAL
        to_dt = _end_of_day(now_local) + timedelta(seconds=1)
        label = f"since_last_report_to_{now_local.strftime('%d.%m.%Y')}"
        return _to_unix(from_dt), _to_unix(to_dt), label
    # --all-time
    if args.all_time:
        from_dt = DEFAULT_EPOCH_START_LOCAL
        to_dt = _end_of_day(now_local) + timedelta(seconds=1)
        label = f"all_time_to_{now_local.strftime('%d.%m.%Y')}"
        return _to_unix(from_dt), _to_unix(to_dt), label
    # default monthly (first day of month -> first day of current month exclusive) executed on first day current month
    # We want previous calendar month
    first_day_this_month = _start_of_day(now_local).replace(day=1)
    last_day_prev_month = first_day_this_month - timedelta(days=1)
    first_day_prev_month = last_day_prev_month.replace(day=1)
    from_dt = _start_of_day(first_day_prev_month)
    to_dt = _end_of_day(last_day_prev_month) + timedelta(seconds=1)
    label = f"monthly_{from_dt.strftime('%m-%Y')}"
    return _to_unix(from_dt), _to_unix(to_dt), label


def main():
    parser = argparse.ArgumentParser(description='Send daily summary and monthly Excel via Telegram.')
    parser.add_argument('--summary-only', action='store_true', help='Send only daily summary (for 9pm GMT+7 schedule)')
    parser.add_argument('--excel-only', action='store_true', help='Send only monthly Excel (for 7am GMT+7 first day schedule)')
    parser.add_argument('--force-excel', action='store_true', help='Force sending excel regardless of date')
    parser.add_argument('--skip-summary', action='store_true', help='Skip sending summary message')
    parser.add_argument('--dry-run', action='store_true', help='Print actions without sending')
    parser.add_argument('--from-last-report', action='store_true', help='Excel: from last report end date to now')
    parser.add_argument('--all-time', action='store_true', help='Excel: from default epoch (24/09/2025) to now')
    parser.add_argument('--custom-date', nargs=2, metavar=('FROM_DATE','TO_DATE'), help='Excel: custom inclusive date range YYYY-MM-DD YYYY-MM-DD')
    args = parser.parse_args()

    tz = ZoneInfo('Asia/Bangkok')
    now_local = datetime.now(tz)

    # Handle scheduled operations
    if args.summary_only:
        # Daily summary at 9pm GMT+7
        print(f"Daily summary scheduled run at {now_local.strftime('%Y-%m-%d %H:%M:%S')} GMT+7")
        summary = generate_summary()
        summary_html, summary_plain = build_summary_text(summary)
        if args.dry_run:
            print('[DRY] Would send daily summary (HTML):\n' + summary_html)
        else:
            if not send_telegram_message(summary_html, parse_mode='HTML'):
                print('Falling back to plain text summary...')
                send_telegram_message(summary_plain)
        return

    if args.excel_only:
        # Monthly Excel at 7am GMT+7 on first day of month
        if now_local.day != 1:
            print(f"Excel scheduled run skipped - not first day of month (today is {now_local.day})")
            return
        
        print(f"Monthly Excel scheduled run at {now_local.strftime('%Y-%m-%d %H:%M:%S')} GMT+7")
        # Generate previous month's report
        from_ts, to_ts, label = compute_range(args, now_local)
        if args.dry_run:
            print(f"[DRY] Would generate monthly Excel: {label} -> {from_ts} .. {to_ts}")
        else:
            print(f"Running monthly excel generation: {label}")
            generate_excel_with_range(from_ts, to_ts)
            
            # Load and send the generated report
            report_path = None
            if os.path.isfile(LAST_REPORT_META):
                try:
                    with open(LAST_REPORT_META,'r',encoding='utf-8') as f:
                        meta = json.load(f)
                    report_path = meta.get('path')
                except Exception as e:
                    print(f'Warning: could not load metadata: {e}')

            if report_path and os.path.isfile(report_path):
                caption = f"Monthly Report {label}"
                send_telegram_document(report_path, caption)
            else:
                print('Report file not found after generation attempt.')
        return

    # Manual/interactive mode (original logic)
    summary = generate_summary()
    summary_html, summary_plain = build_summary_text(summary)
    if not args.skip_summary:
        if args.dry_run:
            print('[DRY] Would send summary (HTML):\n' + summary_html)
        else:
            if not send_telegram_message(summary_html, parse_mode='HTML'):
                print('Falling back to plain text summary...')
                send_telegram_message(summary_plain)

    need_excel = False
    if args.force_excel or args.from_last_report or args.all_time or args.custom_date:
        need_excel = True
    else:
        # monthly: only first day of month at 07:00 (scheduler ensures time); allow run if first day
        if now_local.day == 1:
            need_excel = True

    if not need_excel:
        print('Excel generation not required today.')
        return

    # compute range
    from_ts, to_ts, label = compute_range(args, now_local)
    if args.dry_run:
        print(f"[DRY] Would generate Excel: {label} -> {from_ts} .. {to_ts}")
    else:
        print(f"Running excel generation: {label} -> {from_ts} .. {to_ts}")
        generate_excel_with_range(from_ts, to_ts)
    # Load metadata
    report_path = None
    if os.path.isfile(LAST_REPORT_META):
        try:
            with open(LAST_REPORT_META,'r',encoding='utf-8') as f:
                meta = json.load(f)
            report_path = meta.get('path')
        except Exception as e:
            print(f'Warning: could not load metadata: {e}')

    if not report_path or not os.path.isfile(report_path):
        print('Report file not found after generation attempt.')
        return

    caption = f"Report {label}"
    if args.dry_run:
        print(f"[DRY] Would send excel: {report_path} caption='{caption}'")
    else:
        send_telegram_document(report_path, caption)


if __name__ == '__main__':
    main()
