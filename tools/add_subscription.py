"""
Add a new subscription to Google Sheets (CLI).
Usage: python3 tools/add_subscription.py
"""

import sys
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from tools.sheets_helper import get_sheet, ensure_headers

FREQUENCIES = ['weekly', 'monthly', 'quarterly', 'bi-annual', 'yearly']


def compute_next_renewal(start: date, frequency: str) -> date:
    today = date.today()
    d = start
    while d <= today:
        if frequency == 'weekly':
            d += relativedelta(weeks=1)
        elif frequency == 'monthly':
            d += relativedelta(months=1)
        elif frequency == 'quarterly':
            d += relativedelta(months=3)
        elif frequency == 'bi-annual':
            d += relativedelta(months=6)
        elif frequency == 'yearly':
            d += relativedelta(years=1)
    return d


def main():
    print("=== Add Subscription ===\n")

    name = input("Subscription name: ").strip()
    if not name:
        print("Name cannot be empty.")
        sys.exit(1)

    amount_str = input("Amount (e.g. 9.99): ").strip()
    try:
        amount = float(amount_str)
    except ValueError:
        print("Invalid amount.")
        sys.exit(1)

    print(f"Frequency options: {', '.join(FREQUENCIES)}")
    frequency = input("Frequency: ").strip().lower()
    if frequency not in FREQUENCIES:
        print(f"Invalid frequency. Choose from: {', '.join(FREQUENCIES)}")
        sys.exit(1)

    start_str = input("Start date (YYYY-MM-DD): ").strip()
    try:
        start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
    except ValueError:
        print("Invalid date format. Use YYYY-MM-DD.")
        sys.exit(1)

    next_renewal = compute_next_renewal(start_date, frequency)

    print("\nConnecting to Google Sheets...")
    sheet = get_sheet()
    ensure_headers(sheet)
    sheet.append_row([
        name,
        amount,
        frequency,
        start_date.strftime('%Y-%m-%d'),
        next_renewal.strftime('%Y-%m-%d'),
    ])

    print(f"\nAdded '{name}' (${amount:.2f} {frequency})")
    print(f"Next renewal: {next_renewal}")


if __name__ == '__main__':
    main()
