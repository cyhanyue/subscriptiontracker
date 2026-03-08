# Workflow: Add Subscription

## Objective
Add a new subscription entry to the Google Sheet tracker.

## Inputs
- Subscription name (e.g. "Netflix")
- Amount (e.g. 15.99)
- Frequency: `weekly`, `monthly`, `quarterly`, or `yearly`
- Start date (YYYY-MM-DD) — the date the subscription first charged

## Steps
1. Run `tools/add_subscription.py` — it will prompt for all inputs interactively
2. The script computes the next renewal date automatically from start date + frequency
3. A new row is appended to the Google Sheet

## Expected Output
- New row in Google Sheet with columns:
  `Subscription Name | Amount | Frequency | Start Date | Next Renewal Date`
- Confirmation printed in the terminal

## Edge Cases
- **Invalid frequency**: Script exits with a clear error — only `weekly`, `monthly`, `quarterly`, `yearly` are accepted
- **Missing headers**: Script auto-creates header row if sheet is empty
- **Past start date**: `Next Renewal Date` is always set to the next upcoming renewal, never a past date

## Setup Requirements (one-time)
1. Create a Google Cloud project and enable the **Google Sheets API**
2. Create a **Service Account**, download `credentials.json` to the project root
3. Create a new Google Sheet and share it with the service account email (Editor access)
4. Copy the Sheet ID from the URL (`https://docs.google.com/spreadsheets/d/<SHEET_ID>/edit`) into `.env`

## Running
```bash
cd ~/Desktop/vibecodes
python3 tools/add_subscription.py
```
