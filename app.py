import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from tools.sheets_helper import get_sheet, ensure_headers

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'change-me-in-production')

FREQUENCIES = ['weekly', 'monthly', 'quarterly', 'bi-annual', 'yearly']
DAYS_AHEAD = 3


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.before_request
def require_login():
    if request.endpoint in ('login', 'static'):
        return
    if not session.get('authenticated'):
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['password'] == os.getenv('SITE_PASSWORD'):
            session['authenticated'] = True
            return redirect(url_for('index'))
        error = 'Incorrect password.'
    return render_template('login.html', error=error)


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── Helpers ──────────────────────────────────────────────────────────────────

def compute_next_renewal(start: date, frequency: str) -> date:
    today = date.today()
    d = start
    while d <= today:
        d = advance(d, frequency)
    return d


def advance(d: date, frequency: str) -> date:
    if frequency == 'weekly':
        return d + relativedelta(weeks=1)
    elif frequency == 'monthly':
        return d + relativedelta(months=1)
    elif frequency == 'quarterly':
        return d + relativedelta(months=3)
    elif frequency == 'bi-annual':
        return d + relativedelta(months=6)
    elif frequency == 'yearly':
        return d + relativedelta(years=1)
    raise ValueError(f"Unknown frequency: {frequency}")


def monthly_equivalent(amount: float, frequency: str) -> float:
    return {
        'weekly': amount * 52 / 12,
        'monthly': amount,
        'quarterly': amount / 3,
        'bi-annual': amount / 6,
        'yearly': amount / 12,
    }[frequency]


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    sheet = get_sheet()
    rows = sheet.get_all_records()
    today = date.today()

    subscriptions = []
    for i, row in enumerate(rows, start=2):
        try:
            renewal = datetime.strptime(row['Next Renewal Date'], '%Y-%m-%d').date()
            days_left = (renewal - today).days
        except Exception:
            renewal = None
            days_left = None

        try:
            start = datetime.strptime(row['Start Date'], '%Y-%m-%d').date()
            months_subscribed = (today.year - start.year) * 12 + (today.month - start.month)
        except Exception:
            months_subscribed = None

        subscriptions.append({
            'row': i,
            'name': row['Subscription Name'],
            'amount': float(row['Amount']),
            'frequency': row['Frequency'],
            'start_date': row['Start Date'],
            'renewal_date': row['Next Renewal Date'],
            'days_left': days_left,
            'months_subscribed': months_subscribed,
        })

    total_monthly = sum(monthly_equivalent(s['amount'], s['frequency']) for s in subscriptions)

    upcoming_payments = sorted(
        [s for s in subscriptions if s['days_left'] is not None and s['days_left'] >= 0],
        key=lambda s: s['days_left']
    )[:3]

    return render_template(
        'index.html',
        subscriptions=subscriptions,
        upcoming_payments=upcoming_payments,
        total_monthly=total_monthly,
        frequencies=FREQUENCIES,
        today=today.strftime('%Y-%m-%d'),
    )


@app.route('/add', methods=['POST'])
def add():
    name = request.form['name'].strip()
    amount = float(request.form['amount'])
    frequency = request.form['frequency']
    start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
    next_renewal = compute_next_renewal(start_date, frequency)

    sheet = get_sheet()
    ensure_headers(sheet)
    sheet.append_row([
        name,
        amount,
        frequency,
        start_date.strftime('%Y-%m-%d'),
        next_renewal.strftime('%Y-%m-%d'),
    ])

    flash(f"Added '{name}' — next renewal {next_renewal}", 'success')
    return redirect(url_for('index'))


@app.route('/delete/<int:row>', methods=['POST'])
def delete(row):
    sheet = get_sheet()
    name = sheet.cell(row, 1).value
    sheet.delete_rows(row)
    flash(f"Deleted '{name}'", 'info')
    return redirect(url_for('index'))


# ── Email notification (also used by scheduler) ───────────────────────────────

def send_renewal_email(upcoming: list):
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

    print(f"[scheduler] Email sent to {notify}")


def check_renewals_job():
    print("[scheduler] Running renewal check...")
    today = date.today()
    target = today + relativedelta(days=DAYS_AHEAD)

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

    if upcoming:
        send_renewal_email(upcoming)
    else:
        print(f"[scheduler] No renewals on {target}.")


# ── Scheduler ─────────────────────────────────────────────────────────────────

scheduler = BackgroundScheduler()
scheduler.add_job(check_renewals_job, 'cron', hour=9, minute=0)
scheduler.start()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
