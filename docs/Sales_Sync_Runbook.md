# Sales Operations Sync — Runbook

**Last Updated:** March 2026
**Owner:** Syed
**Status:** Active

---

## Overview

**What it does:** Pulls deal data and syncs it to 3 Google Sheets automatically — Revenue Tracking (Finance), Sales Forecast (CEO), and Customer Data (Marketing).

**Why it exists:** Sales team was spending 3.5-4 hours/week manually copying data from Airtable into 3 different Google Sheets. This script automates the entire process.

**Who uses it:** Sales Operations team runs it (or it runs on a schedule).

**Impact:** Saves ~4 hours/week across the Sales Ops team. Data is always current and consistent.

---

## Setup & Prerequisites

### Requirements
- Python 3.9+
- Google Cloud service account with Sheets API enabled
- 3 Google Sheets shared with the service account

### One-Time Setup

1. **Navigate to the script folder:**
   ```bash
   cd ~/workspace/clients/precision-manufacturing/automations/sales-sync
   ```

2. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```
   If venv doesn't exist yet:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Place your Google credentials file:**
   - Download `credentials.json` from Google Cloud Console
   - Place it in the `sales-sync` folder

4. **Create the `.env` file:**
   ```bash
   cp .env.example .env
   ```
   Fill in your Sheet IDs:
   ```
   GOOGLE_CREDENTIALS_PATH=credentials.json
   SHEET_REVENUE_TRACKING=your_sheet_id
   SHEET_SALES_FORECAST=your_sheet_id
   SHEET_CUSTOMER_DATA=your_sheet_id
   ```

5. **Share each Google Sheet** with the service account email from `credentials.json` (`client_email` field) as Editor.

---

## How to Run It

1. **Activate virtual environment:**
   ```bash
   cd ~/workspace/clients/precision-manufacturing/automations/sales-sync
   source venv/bin/activate
   ```

2. **Run the sync:**
   ```bash
   python sync.py
   ```

3. **What to expect:**
   ```
   2026-03-25 10:00:01 - === Sales Sync Starting ===
   2026-03-25 10:00:01 - Loaded 8 deals from mock data
   2026-03-25 10:00:02 - Connecting to Google Sheets...
   2026-03-25 10:00:03 - Writing to sheets...
   2026-03-25 10:00:04 -   → Sheet1: wrote 9 rows (including header)
   2026-03-25 10:00:05 -   → Sheet1: wrote 8 rows (including header)
   2026-03-25 10:00:06 -   → Sheet1: wrote 4 rows (including header)
   2026-03-25 10:00:06 - === Sync Complete ===
   ```

4. **Verify:** Open each Google Sheet and confirm data is updated

---

## What Each Sheet Contains

| Sheet | Filter | Columns |
|---|---|---|
| Revenue Tracking (Finance) | All deals | Deal Name, Company, Amount, Close Date, Stage, Owner |
| Sales Forecast (CEO) | Excludes Closed Lost | Deal Name, Amount, Close Date, Probability, Stage, Territory |
| Customer Data (Marketing) | Closed Won only | Company, Industry, Size, Owner, Close Date, Amount |

---

## What Could Go Wrong

**"google.auth.exceptions.DefaultCredentialsError"**
- Cause: `credentials.json` not found or wrong path
- Fix: Check `GOOGLE_CREDENTIALS_PATH` in `.env`, ensure file exists in the folder

**"HttpError 403: The caller does not have permission"**
- Cause: Google Sheet not shared with service account
- Fix: Open the Sheet → Share → add service account email as Editor

**"HttpError 404: Requested entity was not found"**
- Cause: Wrong Sheet ID in `.env`
- Fix: Check the Sheet URL and copy the ID correctly

**Data not updating in sheets**
- Cause: Script ran but wrote to wrong sheet
- Fix: Verify Sheet IDs in `.env` match the correct sheets

---

## Connecting to Real Airtable (When Ready)

Currently uses `mock_deals.json`. To switch to live Airtable data, replace the `get_deals()` function in `sync.py` with:

```python
def get_deals():
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Sales Pipeline"
    headers = {"Authorization": f"Bearer {AIRTABLE_TOKEN}"}
    response = requests.get(url, headers=headers)
    records = response.json().get("records", [])
    return [r["fields"] for r in records]
```

Add to `.env`:
```
AIRTABLE_TOKEN=your_token
AIRTABLE_BASE_ID=your_base_id
```

---

## Maintenance

- **Weekly:** Run on Tuesday mornings (Jennifer's schedule)
- **When new fields are added to Airtable:** Update field mappings in `sync.py`
- **Monthly:** Verify Google credentials haven't expired

---

## Emergency Procedures

**If sync fails and data is needed urgently:**
1. Jennifer exports CSV from Airtable manually (old process as backup)
2. Notify Syed to fix the script

**Contact:** Syed
