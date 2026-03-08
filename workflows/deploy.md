# Workflow: Deploy to Railway

## Objective
Deploy the subscription tracker web app to Railway so it's accessible from anywhere.

## Prerequisites
- `credentials.json` from Google Cloud service account (in project root, gitignored)
- `.env` fully filled in
- A GitHub account
- A Railway account (railway.app — free tier available)

## Steps

### 1. Init a Git repo and push to GitHub
```bash
cd ~/Desktop/vibecodes
git init
git add -A
git commit -m "Initial commit"
# Create a new repo on GitHub (do NOT initialize with README)
git remote add origin https://github.com/<your-username>/vibecodes.git
git push -u origin main
```

### 2. Set GOOGLE_CREDENTIALS_JSON env var
On Railway, credentials.json can't be uploaded as a file. Instead, paste its contents as an env var.

```bash
# Print the contents of credentials.json as a single line:
cat credentials.json | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)))"
```
Copy the output — you'll paste it into Railway as `GOOGLE_CREDENTIALS_JSON`.

### 3. Deploy on Railway
1. Go to railway.app → New Project → Deploy from GitHub repo → select `vibecodes`
2. Railway auto-detects Python + Procfile
3. Go to **Variables** tab and add all of the following:
   - `GOOGLE_SHEET_ID` — from your `.env`
   - `GOOGLE_CREDENTIALS_JSON` — the JSON string from step 2
   - `GMAIL_ADDRESS` — from your `.env`
   - `GMAIL_APP_PASSWORD` — from your `.env`
   - `NOTIFICATION_EMAIL` — from your `.env`
   - `SECRET_KEY` — any random string (e.g. run `python3 -c "import secrets; print(secrets.token_hex(32))"`)
4. Click **Deploy** — Railway builds and launches the app
5. Go to **Settings → Networking → Generate Domain** to get your public URL

## Expected Output
- Public URL like `https://vibecodes-production.up.railway.app`
- App shows subscription table and stats
- Email notifications sent daily at 9:00 AM (scheduler runs inside the web process)

## Edge Cases
- **Build fails**: Check that `requirements.txt` is present and all packages are spelled correctly
- **App crashes on start**: Check Railway logs — usually a missing env var; verify all 6 are set
- **Email not sending**: Confirm `GMAIL_APP_PASSWORD` has no extra spaces; App Passwords are 16 chars with spaces (e.g. `xxxx xxxx xxxx xxxx`)
- **Sheets auth fails**: Confirm `GOOGLE_CREDENTIALS_JSON` is valid JSON; re-run the `cat | python3` command to regenerate

## Redeployment
Push to GitHub → Railway auto-redeploys:
```bash
git add -A && git commit -m "update" && git push
```
