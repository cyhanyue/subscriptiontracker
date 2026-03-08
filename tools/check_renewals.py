"""
Check for subscriptions renewing in 3 days and send an email notification.
Can be run manually or is triggered daily by the scheduler in app.py.
Usage: python3 tools/check_renewals.py
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from tools.sheets_helper import get_sheet

load_dotenv()

DAYS_AHEAD = 3


def advance(d: date, frequency: str) -> date:
    if frequency == 'weekly':
        return d + relativedelta(weeks=1)
    elif frequency == 'monthly':
        return d + relativedelta(months=1)
    elif frequency == 'quarterly':
        return d + relativedelta(months=3)
    elif frequency == 'yearly':
        return d + relativedelta(years=1)
    raise ValueError(f"Unknown frequency: {frequency}")


def send_email(upcoming: list):
    gmail = os.getenv('GMAIL_ADDRESS')
    password = os.getenv('GMAIL_APP_PASSWORD')
    notify = os.getenv('NOTIFICATION_EMAIL')
    total = sum(float(r['amount']) for r in upcoming)
    renewal_date = upcoming[0]['renewal_date']

    lines = [f"  • {r['name']}  —  ${float(r['amount']):.2f} / {r['frequency']}" for r in upcoming]
    body = (
        f"Hi,\n\nThe following subscription(s) renew on {renewal_date} (in {DAYS_AHEAD} days):\n\n"
        + "\n".join(lines)
        + f"\n\nTotal due: ${total:.2f}\n\nNow's a good time to review — cancel anything you no longer need.\n"
    )

    msg = MIMEMultipart()
    msg['From'] = gmail
    msg['To'] = notify
    msg['Subject'] = f"Subscription Reminder: {len(upcoming)} renewal(s) on {renewal_date}"
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(gmail, password)
        server.send_message(msg)

    print(f"Email sent to {notify}")


def main():
    today = date.today()
    target = today + relativedelta(days=DAYS_AHEAD)
    print(f"Checking renewals for {target}...")

    sheet = get_sheet()
    rows = sheet.get_all_records()
    upcoming = []
    stale_updates = []

    for i, row in enumerate(rows, start=2):
        renewal_date = datetime.strptime(row['Next Renewal Date'], '%Y-%m-%d').date()
        frequency = row['Frequency']
        updated = False
        while renewal_date < today:
            renewal_date = advance(renewal_date, frequency)
            updated = True
        if updated:
            stale_updates.append((i, renewal_date.strftime('%Y-%m-%d')))
        if renewal_date == target:
            upcoming.append({
                'name': row['Subscription Name'],
                'amount': row['Amount'],
                'frequency': frequency,
                'renewal_date': renewal_date.strftime('%Y-%m-%d'),
            })

    for row_idx, new_date in stale_updates:
        sheet.update_cell(row_idx, 5, new_date)
        print(f"Updated row {row_idx} renewal date to {new_date}")

    if upcoming:
        send_email(upcoming)
    else:
        print(f"No renewals on {target}. Nothing to send.")


if __name__ == '__main__':
    main()
