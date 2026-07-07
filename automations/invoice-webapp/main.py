#!/usr/bin/env python3
"""
Invoice Upload Web App — FastAPI Backend
Accepts PDF uploads, extracts invoice data, saves to Airtable.
"""

import os
import re
import sys
import logging
import tempfile
import requests
import pdfplumber
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

load_dotenv()

AIRTABLE_TOKEN   = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE   = os.getenv("AIRTABLE_TABLE_NAME", "Invoices")
AIRTABLE_URL     = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}"
AIRTABLE_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Invoice Processor", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Data Models ────────────────────────────────────────────────────────────────

class InvoiceData(BaseModel):
    invoice_number: Optional[str] = None
    vendor_name:    Optional[str] = None
    invoice_date:   Optional[str] = None
    due_date:       Optional[str] = None
    amount:         Optional[float] = None
    source_file:    Optional[str] = None
    status:         Optional[str] = None
    missing_fields: Optional[list] = []

class SaveRequest(BaseModel):
    invoice_number: Optional[str] = None
    vendor_name:    Optional[str] = None
    invoice_date:   Optional[str] = None
    due_date:       Optional[str] = None
    amount:         Optional[float] = None
    source_file:    Optional[str] = None


# ── PDF Extraction (reused from invoice_processor.py) ─────────────────────────

def strip_html_tags(text):
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[<>]', ' ', text)
    return text

def normalise_date(date_str):
    formats = [
        "%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y",
        "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def extract_invoice_data(pdf_path: str, filename: str) -> InvoiceData:
    """Extract text from PDF and parse invoice fields."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read PDF: {e}")

    clean = strip_html_tags(text)
    data  = InvoiceData(source_file=filename)

    # Vendor Name — first meaningful line
    lines = [l.strip() for l in clean.splitlines() if l.strip()]
    if lines:
        first = lines[0]
        if not re.match(r'^invoice$', first, re.IGNORECASE) and \
           not re.match(r'^(inv|invoice)\s*#', first, re.IGNORECASE):
            data.vendor_name = first

    # Invoice Number
    m = re.search(r'invoice\s*(?:number|no|#)[:\s#]*([A-Z]{1,5}[-\s]?[\w\-]+)', clean, re.IGNORECASE)
    if m:
        data.invoice_number = m.group(1).strip()

    # Amount
    m = re.search(
        r'(?<!sub)(?:total\s*due|amount\s*due|grand\s*total|total\s*amount)[:\s$]*\$?\s*([0-9,]+\.[0-9]{2})',
        clean, re.IGNORECASE
    )
    if not m:
        m = re.search(r'(?<![a-zA-Z])total[:\s$]*\$?\s*([0-9,]+\.[0-9]{2})', clean, re.IGNORECASE)
    if m:
        try:
            data.amount = float(m.group(1).replace(",", ""))
        except ValueError:
            pass

    # Invoice Date
    m = re.search(
        r'(?:invoice\s*date|date\s*issued|date)[:\s]+(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        clean, re.IGNORECASE
    )
    if m:
        data.invoice_date = normalise_date(m.group(1).strip())

    # Due Date
    m = re.search(
        r'(?:due\s*date|payment\s*due|pay\s*by)[:\s]+(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        clean, re.IGNORECASE
    )
    if m:
        data.due_date = normalise_date(m.group(1).strip())

    # Missing fields
    fields = ["invoice_number", "vendor_name", "invoice_date", "due_date", "amount"]
    data.missing_fields = [f for f in fields if not getattr(data, f)]
    data.status = "Needs Review" if data.missing_fields else "Processed"

    return data


# ── API Routes ─────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html") as f:
        return f.read()

@app.post("/upload", response_model=InvoiceData)
async def upload_invoice(file: UploadFile = File(...)):
    """Accept PDF upload, extract and return invoice data for review."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        data = extract_invoice_data(tmp_path, file.filename)
        logger.info(f"Extracted: {file.filename} → {data.status}")
        return data
    finally:
        os.remove(tmp_path)

def check_duplicate(invoice_number: str) -> Optional[str]:
    """Check if invoice number already exists in Airtable. Returns record ID if found."""
    if not invoice_number or invoice_number == "UNKNOWN":
        return None
    try:
        formula = f'{{Invoice Number}}="{invoice_number}"'
        response = requests.get(
            AIRTABLE_URL,
            headers=AIRTABLE_HEADERS,
            params={"filterByFormula": formula},
            timeout=10
        )
        logger.info(f"Duplicate check status: {response.status_code}")
        if response.status_code == 200:
            records = response.json().get("records", [])
            if records:
                return records[0]["id"]
    except requests.exceptions.Timeout:
        logger.warning("Duplicate check timed out — proceeding without check")
    except Exception as e:
        logger.warning(f"Duplicate check failed: {e} — proceeding without check")
    return None


@app.post("/save")
async def save_to_airtable(invoice: SaveRequest):
    """Save reviewed invoice data to Airtable. Rejects duplicates."""

    # Duplicate check
    existing_id = check_duplicate(invoice.invoice_number)
    if existing_id:
        raise HTTPException(
            status_code=409,
            detail=f"Invoice {invoice.invoice_number} already exists in Airtable (record: {existing_id}). Duplicate not saved."
        )

    fields = {
        "Invoice Number": invoice.invoice_number or "UNKNOWN",
        "Vendor Name":    invoice.vendor_name    or "UNKNOWN",
        "Amount":         invoice.amount          or 0,
        "Status":         "Processed",
        "Notes":          "Uploaded via web app",
    }
    if invoice.invoice_date:
        fields["Invoice Date"] = invoice.invoice_date
    if invoice.due_date:
        fields["Due Date"] = invoice.due_date

    response = requests.post(AIRTABLE_URL, headers=AIRTABLE_HEADERS, json={"fields": fields})

    if response.status_code in (200, 201):
        record_id = response.json().get("id")
        logger.info(f"Saved to Airtable: {record_id}")
        return {"success": True, "record_id": record_id}
    else:
        logger.error(f"Airtable error: {response.text}")
        raise HTTPException(status_code=500, detail=f"Airtable error: {response.text}")
