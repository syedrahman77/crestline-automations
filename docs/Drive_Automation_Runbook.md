# Google Drive Invoice Watcher — Runbook

**Last Updated:** June 2026
**Owner:** Syed
**Status:** Active

---

## Overview

**What it does:** Watches a Google Drive folder ("Invoices - To Process") for new PDF invoices, runs them through the same extraction logic as the invoice processor, saves the data to Airtable, then moves the file to "Invoices - Processed."

**Why it exists:** Removes the manual step of downloading invoices and running the processor by hand — invoices dropped into Drive (e.g. by email forwarding rules or manual upload) are picked up automatically.

**Who uses it:** Finance team. Runs continuously in the background (polling), not triggered manually per file.

**Impact:** Invoices are processed within ~30 seconds of landing in Drive, with no manual download/run step.

---

## Architecture / How It Works

- Polls the inbox Drive folder every 30 seconds for PDF files.
- For each new file: downloads it to a temp file, extracts text, parses invoice fields, checks for duplicates, and inserts a record into Airtable — reusing `extract_text_from_pdf`, `parse_invoice_data`, `check_duplicate`, and `insert_to_airtable` directly from `invoice_processor.py`.
- On success (or duplicate), moves the file from the inbox folder to the processed folder in Drive so it isn't picked up again.
- Logs to both the terminal and `logs/drive_watcher.log`.

**Important dependency:** This script lives in `automations/invoice-processor/` alongside `invoice_processor.py` and imports functions from it directly (`extract_text_from_pdf`, `parse_invoice_data`, `check_duplicate`, `insert_to_airtable`) — it does not duplicate that logic. It shares the same `.env`, virtual environment, and Airtable table, so the [Invoice Processor Runbook](Invoice_Processor_Runbook.md) Airtable setup must already be done first.

---

## Setup & Prerequisites

### Requirements
- Python 3.9+
- Same pip packages as the invoice processor (see `automations/invoice-processor/requirements.txt`) — includes `google-auth`, `google-auth-oauthlib`, `google-api-python-client`
- Airtable already set up per the [Invoice Processor Runbook](Invoice_Processor_Runbook.md)
- A Google Cloud project with the Drive API enabled and OAuth credentials (`credentials.json`)
- Two Drive folders: an inbox folder and a processed folder, with their folder IDs

### One-Time Setup

1. **Navigate to the invoice-processor folder and activate its virtual environment** (`drive_watcher.py` lives here and shares its dependencies, `.env`, and Airtable setup):
   ```bash
   cd ~/workspace/crestline-automations/automations/invoice-processor
   source venv/bin/activate
   ```

2. **Create two folders in Google Drive:**
   - `Invoices - To Process` (inbox)
   - `Invoices - Processed` (destination after processing)

   Open each folder in the browser and copy the folder ID from the URL:
   `https://drive.google.com/drive/folders/<FOLDER_ID>`

3. **Add the folder IDs to `.env`** (same `.env` used by invoice_processor):
   ```
   DRIVE_INBOX_FOLDER_ID=your_inbox_folder_id_here
   DRIVE_PROCESSED_FOLDER_ID=your_processed_folder_id_here
   ```

4. **Set up Google OAuth credentials:**

   a. **Select a Google Cloud project:**
      - Go to https://console.cloud.google.com/ and use the project dropdown at the top of the page
      - If you already have any existing project, just select it — there's no need to create a new one for this
      - Only create a new project if you don't have one: https://console.cloud.google.com/projectcreate (note: Google caps how many projects an account can create; if you hit that limit, requesting an increase is free but reusing an existing project avoids the wait entirely)

   b. **Enable the Google Drive API:**
      - Go to https://console.cloud.google.com/apis/library/drive.googleapis.com
      - Make sure your project is selected at the top of the page
      - Click **Enable**

   c. **Configure the OAuth consent screen** (required before creating credentials):
      - Go to https://console.cloud.google.com/apis/credentials/consent
      - Choose **External** (unless you have a Google Workspace org, then **Internal** is fine) and click **Create**
      - Fill in the required fields (app name, your email as support/developer contact) and click **Save and Continue** through the remaining steps
      - On the "Test users" step, add the Google account you'll use to authorize the watcher (the one with access to both Drive folders)

   d. **Create the OAuth Client ID:**
      - Go to https://console.cloud.google.com/apis/credentials
      - Click **Create Credentials** → **OAuth client ID**
      - Application type: **Desktop app**
      - Give it a name (e.g. "Drive Watcher Desktop Client") and click **Create**

   e. **Download the credentials file:**
      - In the resulting dialog (or back on the credentials list), click the download icon next to the client you just created
      - This downloads a JSON file — rename it to `credentials.json` and place it in the `invoice-processor` folder (next to `drive_watcher.py` and `generate_token.py`)

   f. **Run the one-time authorization helper to generate `token.json`:**
     ```bash
     python generate_token.py
     ```
     This opens a browser window to sign in and approve access. Sign in with the same Google account added as a test user in step c — `token.json` is created automatically on approval.

---

## How to Run It

1. **Activate the virtual environment and start the watcher:**
   ```bash
   cd ~/workspace/crestline-automations/automations/invoice-processor
   source venv/bin/activate
   python drive_watcher.py
   ```

2. **What to expect:**
   - Runs continuously, checking every 30 seconds
   - Logs each cycle to the terminal and to `logs/drive_watcher.log`
   - Successful output looks like:
   ```
   2026-06-20 10:00:00 - Drive Watcher Started
   2026-06-20 10:00:00 - Watching folder ID: 1AbCxyz...
   2026-06-20 10:00:30 - Found 1 new file(s)
   2026-06-20 10:00:31 - Processing: invoice-001-acme-corp.pdf
   2026-06-20 10:00:33 -   ✓ Inserted to Airtable (ID: recXXXXX)
   2026-06-20 10:00:33 -   ✓ Moved 'invoice-001-acme-corp.pdf' to Invoices - Processed
   ```

3. **Stop it:** `Ctrl+C`

4. **Verify it worked:**
   - File disappears from "Invoices - To Process" and appears in "Invoices - Processed"
   - New record appears in Airtable with the extracted data

---

## What Could Go Wrong

**"ERROR: DRIVE_INBOX_FOLDER_ID and DRIVE_PROCESSED_FOLDER_ID must be set in .env"**
- Cause: Folder IDs missing from `.env`
- Fix: Add both IDs as shown in setup step 3

**"ModuleNotFoundError: No module named 'invoice_processor'"**
- Cause: Script run from outside the `invoice-processor/` folder
- Fix: `cd` into `automations/invoice-processor/` before running `python drive_watcher.py`

**OAuth / token errors (`RefreshError`, missing `token.json`)**
- Cause: `token.json` missing, expired, or revoked
- Fix: Run `python generate_token.py` again to regenerate `token.json`

**File stuck in "Invoices - To Process" / reprocessed repeatedly**
- Cause: Airtable insert failed (script only moves the file on success or duplicate)
- Fix: Check `logs/drive_watcher.log` for the Airtable error, fix the underlying issue (e.g. token expired), restart the watcher

**Script crashes and stops watching**
- Cause: Unhandled error during a watch cycle (network blip, Drive API quota, etc.)
- Fix: Check `logs/drive_watcher.log`, restart `python drive_watcher.py`; consider running it under a process manager (e.g. `pm2`, `systemd`, or `nohup`) so it restarts automatically

---

## Monitoring & Verification

- **Logs:** `logs/drive_watcher.log` (rotates only if you add log rotation — currently grows unbounded)
- **Drive:** "Invoices - To Process" should stay empty/near-empty during normal operation
- **Airtable:** New records should match files moved to "Invoices - Processed"

---

## Maintenance

- **Periodically:** Check that `token.json` hasn't been revoked (Google may require re-auth after long inactivity)
- **Monthly:** Check Airtable token hasn't expired (shared with invoice processor)
- **Disk:** Watch `logs/drive_watcher.log` size if running long-term unattended

---

## Emergency Procedures

**If the watcher is down and invoices are piling up in Drive:**
1. Manually download PDFs from "Invoices - To Process"
2. Run them through `invoice_processor.py` directly (see [Invoice Processor Runbook](Invoice_Processor_Runbook.md))
3. Manually move processed files to "Invoices - Processed" in Drive
4. Notify Syed to fix the watcher

**Rollback:** No rollback needed — script only inserts records and moves files, never deletes.

**Contact:** Syed
