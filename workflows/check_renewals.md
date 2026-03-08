# Workflow: Check Renewals & Notify

## Objective
Run daily. Find subscriptions renewing in 3 days and send an email summary.

## Inputs
None — reads all data from Google Sheet automatically.

## Steps
1. Cron triggers `tools/check_renewals.py` every morning
2. Script reads all rows from Google Sheet
3. For each subscription, it checks if `Next Renewal Date` == today + 3 days
4. Any stale renewal dates (already past) are advanced to the next upcoming cycle and updated in the sheet
5. If any renewals are found, an email is sent listing them with amounts and total cost

## Expected Output
- **Email** to `NOTIFICATION_EMAIL` with subject: `Subscription Reminder: N renewal(s) on YYYY-MM-DD`
- Stale `Next Renewal Date` cells in the sheet updated to their next upcoming date
- Log output written to `.tmp/renewals.log`

## Cron Setup (macOS)
Add this line to your crontab (`crontab -e`) to run daily at 9:00 AM:

```
0 9 * * * cd /Users/hanyueyin/Desktop/vibecodes && python3 tools/check_renewals.py >> .tmp/renewals.log 2>&1
```

## Edge Cases
- **No renewals in 3 days**: Script exits cleanly, nothing sent
- **Stale renewal dates**: Automatically corrected in the sheet each run — safe to miss days
- **Gmail auth failure**: Check that `GMAIL_APP_PASSWORD` in `.env` is a valid App Password (not your account password). Generate at: Google Account → Security → 2-Step Verification → App passwords
- **Sheet API quota**: Google Sheets free tier allows 300 read/write requests per minute — well within daily usage

## Setup Requirements (one-time)
1. Add Gmail credentials to `.env` (see `.env` for keys)
2. Enable Gmail 2FA and generate an **App Password** for "Mail"
3. Set up cron (see above)

## Running Manually
```bash
cd ~/Desktop/vibecodes
python3 tools/check_renewals.py
```
