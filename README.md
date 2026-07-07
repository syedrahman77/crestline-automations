# Crestline Manufacturing — Automation Portfolio

**Client:** mid-sized manufacturer (anonymized in this repo as "Crestline Manufacturing Co.") &nbsp;&nbsp; **Built by:** Syed Abidur Rahman &nbsp;&nbsp; **Status:** Delivered & handed off — client scoping expanded requirements before rollout

---

## Overview

A suite of automation tools built to eliminate manual data entry at a mid-sized manufacturer. The Finance team was spending 2+ hours daily manually keying invoice data, and Sales Ops were maintaining spreadsheets by hand. These automations were built to reduce that overhead to near zero.

**Four automations. One goal: eliminate repetitive manual work.**

---

## Project Status

All four automations were scoped, built, tested against sample data, and delivered with full runbooks and handoff documentation. During acceptance, the client identified additional business requirements, so rollout is on hold pending an expanded implementation phase.

This repository is published (with sample/test data only) as a reference implementation of practical workflow automation: PDF field extraction, Drive-triggered processing, a self-service upload portal, and multi-view CRM sync.

---

## Target Impact

| Metric                  | Current process       | With automation             |
| ----------------------- | --------------------- | --------------------------- |
| Invoice processing time | 2+ hrs/day (manual)   | ~0 mins (automated)         |
| Sales data sync         | 4 hrs/week (manual)   | Scheduled / on-demand       |
| Invoice errors          | Human error prone     | Consistent, validated       |
| Access                  | One person's desktop  | Any device, any team member |

---

## How It Works

### Automation 1 — Invoice Processor (Local Script)

```
📁 Local Invoices Folder
        │
        ▼
  📄 PDF Invoice
        │
        ▼
  [pdfplumber extracts text]
        │
        ▼
  [Regex parses fields]
  Vendor, Amount, Dates,
  Invoice Number
        │
        ├─── All fields found ──▶ Status: "Processed" ──▶ ✅ Airtable Record
        │
        └─── Missing fields ────▶ Status: "Needs Review" ──▶ ⚠️ Airtable Record
```

**Tech:** Python · pdfplumber · Airtable API &nbsp;&nbsp; **Location:** `automations/invoice-processor/`

---

### Automation 2 — Google Drive Watcher

```
📂 Google Drive
"Invoices - To Process"
        │
        ▼ (polls every 30s)
  [New PDF detected]
        │
        ▼
  [Downloads to temp file]
        │
        ▼
  [Same extraction pipeline
   as Invoice Processor]
        │
        ▼
  ✅ Airtable Record
        │
        ▼
  📂 Moved to
"Invoices - Processed"
```

**Tech:** Python · Google Drive API · pdfplumber · Airtable API &nbsp;&nbsp; **Location:** `automations/drive-automation/`

---

### Automation 3 — Invoice Upload Web App

```
👤 Finance Team Member
  (any device, any browser)
        │
        ▼
  [Uploads PDF via web portal]
        │
        ▼
  [FastAPI backend extracts
   and previews data]
        │
        ▼
  [User reviews & confirms]
        │
        ▼
  ✅ Saved to Airtable
```

- **Demo URL:** <https://invoice-webapp-inky.vercel.app/> — demo instance connected to a sample Airtable base; try it with the invoices in `sample-data/`
- **Tech:** FastAPI · pdfplumber · Airtable API · Vercel
- **Location:** `automations/invoice-webapp/`

---

### Automation 4 — Sales Ops Sync

```
📊 Airtable
  (Deals CRM)
        │
        ▼
  [sync.py pulls deal data]
        │
        ├──▶ Revenue Tracking Sheet  (Finance — all deals)
        ├──▶ Sales Forecast Sheet    (CEO — active pipeline only)
        └──▶ Customer Data Sheet     (Marketing — Closed Won only)
```

**Tech:** Python · Airtable API · Google Sheets API &nbsp;&nbsp; **Location:** `automations/sales-sync/`

---

## Automations Summary

| # | Automation        | Input               | Output           | Tech               |
| --- | ----------------- | ------------------- | ---------------- | ------------------ |
| 1 | Invoice Processor | PDF folder (local)  | Airtable records | Python, pdfplumber |
| 2 | Drive Watcher     | Google Drive folder | Airtable records | Python, Drive API  |
| 3 | Invoice Web App   | Browser upload      | Airtable records | FastAPI, Vercel    |
| 4 | Sales Ops Sync    | Airtable CRM        | 3 Google Sheets  | Python, Sheets API |

---

## Setup

### Prerequisites

- Python 3.9+
- Airtable account with an Invoices table
- Google Cloud credentials (for Drive automation and Sales Sync)

### Environment Variables

Each automation uses a `.env` file. See `.env.example` in each folder for required variables:

```
AIRTABLE_TOKEN=your_airtable_token
AIRTABLE_BASE_ID=your_base_id
AIRTABLE_TABLE_NAME=Invoices
```

### Install Dependencies

```
cd automations/invoice-processor
pip install -r requirements.txt
```

### Run the Invoice Processor

```
python invoice_processor.py
```

### Run the Drive Watcher

```
python drive_watcher.py
```

### Run the Web App Locally

```
cd automations/invoice-webapp
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open: <http://localhost:8000>

### Run the Sales Sync

```
cd automations/sales-sync
pip install -r requirements.txt
python sync.py
```

---

## Project Structure

```
crestline-automations/
├── automations/
│   ├── invoice-processor/     # Local PDF → Airtable script
│   ├── drive-automation/      # Google Drive watcher
│   ├── invoice-webapp/        # Self-service web portal
│   └── sales-sync/            # Airtable → Google Sheets sync
├── docs/
│   ├── Handoff_Summary.md
│   ├── Invoice_Processor_Runbook.md
│   ├── Web_App_Runbook.md
│   └── Sales_Sync_Runbook.md
├── sample-data/               # Test PDF invoices (synthetic)
└── README.md
```

---

## About This Project

This was built as a freelance/consulting engagement for a mid-sized manufacturing company whose Finance and Sales Operations teams were heavily reliant on manual data entry. The brief was to identify the highest-impact repetitive workflows and automate them with minimal disruption to the existing team.

The project involved scoping, building, testing, and documenting four automations end-to-end — including handoff documentation and runbooks so the internal team could own and maintain the tools going forward. Following delivery, the client's requirements expanded, and an enhanced implementation phase is being scoped as separate work.

---

## Sample Data

Test invoices in the `sample-data/` folder are synthetic documents created for this repo and can be used to validate the extraction pipeline end-to-end.

---

## Documentation

Full runbooks for each automation are in the `/docs` folder, covering setup, day-to-day operation, common errors, and troubleshooting steps.
