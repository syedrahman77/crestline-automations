# Invoice Processing Automation — Runbook

**Last Updated:** March 2026
**Owner:** Syed
**Status:** Active

---

## Overview

**What it does:** Reads PDF invoices from a local folder, extracts key data (vendor, invoice number, amount, dates), and saves structured records to Airtable automatically.

**Why it exists:** Finance was spending 2+ hours daily manually typing invoice data into Airtable. This automation reduces that to near zero.

**Who uses it:** Finance team. Triggered manually or on a schedule.

**Impact:** Saves ~2 hours/day, eliminates data entry errors, creates audit trail in Airtable.

---

## Setup & Prerequisites

### Requirements
- Python 3.9+
- pip packages (see `requirements.txt`)
- Airtable Personal Access Token
- Airtable Base ID

### One-Time Setup

1. **Navigate to the script folder:**
   ```bash
   cd ~/workspace/crestline-automations/automations/invoice-processor
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create the `.env` file:**
   ```bash
   cp .env.example .env
   ```
   Then open `.env` and fill in:
   ```
   AIRTABLE_TOKEN=your_token_here
   AIRTABLE_BASE_ID=your_base_id_here
   AIRTABLE_TABLE_NAME=Invoices
   ```

5. **Get your Airtable token:**
   - Go to https://airtable.com/create/tokens
   - Create a token with `data.records:read` and `data.records:write` scopes
   - Select your Invoice Tracker base

6. **Get your Base ID:**
   - Go to https://airtable.com/api
   - Click the base you want to use
   - The Base ID is shown in the docs (and in the URL: `https://airtable.com/appXXXXXXXXXXXXXX/api/docs`)
   - It starts with `app` — copy it into `AIRTABLE_BASE_ID` in `.env`

### Creating the Airtable Table (Manual)

The script does not create its own table — it must already exist before the first run. In your Airtable base, create a table named `Invoices` (or set `AIRTABLE_TABLE_NAME` in `.env` to match a different name) with these fields:

| Field Name | Field Type | Notes |
|---|---|---|
| Invoice Number | Single line text | Used for duplicate detection |
| Vendor Name | Single line text | |
| Amount | Number (decimal) | |
| Status | Single select | Add options: `Processed`, `Needs Review` |
| Notes | Long text | Stores error/skip reasons |
| Invoice Date | Date | Only written if extracted successfully |
| Due Date | Date | Only written if extracted successfully |

Field names are case-sensitive and must match exactly — a typo here will cause inserts to fail or land in the wrong field.

---

## How to Run It

1. **Activate the virtual environment:**
   ```bash
   cd ~/workspace/crestline-automations/automations/invoice-processor
   source venv/bin/activate
   ```

2. **Place invoice PDFs** in the invoices folder:
   ```
   ~/workspace/crestline-automations/automations/invoice-processor/invoices/
   ```

3. **Run the script:**
   ```bash
   python invoice_processor.py
   ```

4. **What to expect:**
   - Script logs each file it processes
   - Takes ~2-5 seconds per invoice
   - Successful output looks like:
   ```
   2026-03-25 10:00:01 - Starting automation...
   2026-03-25 10:00:02 - Processing: invoice-001-acme-corp.pdf
   2026-03-25 10:00:04 - Saved to Airtable: recXXXXX
   2026-03-25 10:00:04 - Done.
   ```

5. **Verify it worked:**
   - Open Airtable Invoice Tracker base
   - New records should appear with extracted data
   - Check Status field — "Processed" = complete, "Needs Review" = some fields missing

---

## What Could Go Wrong

**401 Unauthorized (Airtable)**
- Cause: Token expired or incorrect
- Fix: Go to https://airtable.com/create/tokens, regenerate token, update `.env`

**No records appearing in Airtable**
- Cause: Wrong Base ID or Table Name in `.env`
- Fix: Check `.env` values match your actual Airtable base

**"ModuleNotFoundError"**
- Cause: Virtual environment not activated or dependencies not installed
- Fix: Run `source venv/bin/activate` then `pip install -r requirements.txt`

**PDF processed but all fields show "UNKNOWN"**
- Cause: PDF is a scanned image (not text-based)
- Fix: Manually enter the data in Airtable and mark status as "Needs Review"

**Script crashes mid-run**
- Cause: Corrupted PDF file
- Fix: Check logs, identify which file caused the crash, remove it from the folder and process separately

---

## Monitoring & Verification

- **Logs:** Check terminal output after each run
- **Airtable:** Verify new records appear with correct data
- **Status field:** Any "Needs Review" records need manual attention
- **Expected records:** Should match number of PDFs in the folder

---

## Maintenance

- **Monthly:** Check that Airtable token hasn't expired
- **When adding new vendors:** Test a sample invoice — extraction may need tuning if format is unusual
- **Quarterly:** Run `pip install -r requirements.txt --upgrade` to update dependencies

---

## Emergency Procedures

**If script is broken and invoices need processing urgently:**
1. Open each PDF manually
2. Enter data directly into Airtable Invoice Tracker
3. Notify Syed to fix the script

**Rollback:** No rollback needed — script only adds records, never deletes

**Contact:** Syed
