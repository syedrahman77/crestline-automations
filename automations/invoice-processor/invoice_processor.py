#!/usr/bin/env python3
"""
Invoice PDF Processor
Extracts invoice data from PDFs and uploads to Airtable.
Built for Crestline Manufacturing Co. — replaces manual data entry by Sarah.
"""

import os
import re
import sys
import logging
import requests
import pdfplumber
from datetime import datetime
from dotenv import load_dotenv

# ── Setup ──────────────────────────────────────────────────────────────────────

load_dotenv()

AIRTABLE_TOKEN    = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID  = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE    = os.getenv("AIRTABLE_TABLE_NAME", "Invoices")

# Validate credentials on startup
if not AIRTABLE_TOKEN or not AIRTABLE_BASE_ID:
    print("ERROR: AIRTABLE_TOKEN and AIRTABLE_BASE_ID must be set in .env")
    sys.exit(1)

AIRTABLE_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

# Logging — writes to both console and log file
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/processing.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ── PDF Extraction ─────────────────────────────────────────────────────────────

def extract_text_from_pdf(pdf_path):
    """Extract all text from a PDF file."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"Failed to read PDF {pdf_path}: {e}")
        return None


def strip_html_tags(text):
    """Remove HTML/XML tags and stray angle brackets from PDF text."""
    text = re.sub(r'<[^>]+>', ' ', text)   # remove proper tags
    text = re.sub(r'[<>]', ' ', text)       # remove stray < > characters
    return text


def parse_invoice_data(text, filename):
    """
    Extract structured invoice fields from raw PDF text.
    Returns a dict with extracted fields and a list of missing fields.
    """
    data = {
        "Invoice Number": None,
        "Vendor Name":    None,
        "Invoice Date":   None,
        "Due Date":       None,
        "Amount":         None,
    }

    # Clean HTML tags before parsing (some PDFs embed markup)
    clean_text = strip_html_tags(text)

    # ── Vendor Name ──
    # The vendor name is always the first non-empty line of the PDF
    lines = [l.strip() for l in clean_text.splitlines() if l.strip()]
    if lines:
        first_line = lines[0]
        # Exclude lines that are just "INVOICE" or start with invoice number patterns
        if not re.match(r'^invoice$', first_line, re.IGNORECASE) and \
           not re.match(r'^(inv|invoice)\s*#', first_line, re.IGNORECASE):
            data["Vendor Name"] = first_line

    # ── Invoice Number ──
    # Matches: Invoice Number: INV-2024-0342 | Invoice #: WS-789456
    match = re.search(
        r'invoice\s*(?:number|no|#)[:\s#]*([A-Z]{1,5}[-\s]?[\w\-]+)',
        clean_text, re.IGNORECASE
    )
    if match:
        data["Invoice Number"] = match.group(1).strip()

    # ── Amount ──
    # Matches: TOTAL DUE: $1,242.00 | AMOUNT DUE: $3,499.74 | TOTAL: $945.00
    # Explicitly excludes "Subtotal" using negative lookbehind
    match = re.search(
        r'(?<!sub)(?:total\s*due|amount\s*due|grand\s*total|total\s*amount)[:\s$]*\$?\s*([0-9,]+\.[0-9]{2})',
        clean_text, re.IGNORECASE
    )
    # Fallback: plain "TOTAL" that isn't preceded by "sub"
    if not match:
        match = re.search(
            r'(?<![a-zA-Z])total[:\s$]*\$?\s*([0-9,]+\.[0-9]{2})',
            clean_text, re.IGNORECASE
        )
    if match:
        amount_str = match.group(1).replace(",", "")
        try:
            data["Amount"] = float(amount_str)
        except ValueError:
            pass

    # ── Invoice Date ──
    # Matches: Invoice Date: 01/15/2024 | Date: 01/18/2024
    match = re.search(
        r'(?:invoice\s*date|date\s*issued|date)[:\s]+(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        clean_text, re.IGNORECASE
    )
    if match:
        data["Invoice Date"] = normalise_date(match.group(1).strip())

    # ── Due Date ──
    match = re.search(
        r'(?:due\s*date|payment\s*due|pay\s*by)[:\s]+(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}|[A-Za-z]+\s+\d{1,2},?\s+\d{4})',
        clean_text, re.IGNORECASE
    )
    if match:
        data["Due Date"] = normalise_date(match.group(1).strip())

    # ── Identify missing fields ──
    missing = [field for field, value in data.items() if value is None]

    return data, missing


def normalise_date(date_str):
    """Convert various date formats to YYYY-MM-DD for Airtable."""
    formats = [
        "%B %d, %Y",    # January 15, 2025
        "%B %d %Y",     # January 15 2025
        "%b %d, %Y",    # Jan 15, 2025
        "%b %d %Y",     # Jan 15 2025
        "%Y-%m-%d",     # 2025-01-15
        "%m/%d/%Y",     # 01/15/2025
        "%d/%m/%Y",     # 15/01/2025
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    logger.warning(f"Could not parse date: {date_str}")
    return None


# ── Airtable Integration ───────────────────────────────────────────────────────

def check_duplicate(invoice_number):
    """Check if invoice number already exists in Airtable. Returns True if duplicate."""
    if not invoice_number or invoice_number == "UNKNOWN":
        return False
    try:
        formula = f'{{Invoice Number}}="{invoice_number}"'
        response = requests.get(
            AIRTABLE_URL,
            headers=HEADERS,
            params={"filterByFormula": formula},
            timeout=10
        )
        if response.status_code == 200:
            records = response.json().get("records", [])
            return len(records) > 0
    except Exception as e:
        logger.warning(f"Duplicate check failed: {e} — proceeding without check")
    return False


def insert_to_airtable(invoice_data, status, notes=""):
    """Insert a single invoice record into Airtable."""
    fields = {
        "Invoice Number": invoice_data.get("Invoice Number") or "UNKNOWN",
        "Vendor Name":    invoice_data.get("Vendor Name") or "UNKNOWN",
        "Amount":         invoice_data.get("Amount") or 0,
        "Status":         status,
        "Notes":          notes,
    }

    # Only include dates if they were successfully extracted
    if invoice_data.get("Invoice Date"):
        fields["Invoice Date"] = invoice_data["Invoice Date"]
    if invoice_data.get("Due Date"):
        fields["Due Date"] = invoice_data["Due Date"]

    response = requests.post(AIRTABLE_URL, headers=HEADERS, json={"fields": fields})

    if response.status_code in (200, 201):
        return True, response.json().get("id")
    else:
        return False, response.text


# ── Main Processing Loop ───────────────────────────────────────────────────────

def process_invoices(folder_path):
    """Process all PDFs in a folder and insert results into Airtable."""

    # Find all PDFs
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]

    if not pdf_files:
        logger.warning(f"No PDF files found in {folder_path}")
        return

    logger.info(f"Found {len(pdf_files)} invoice(s) to process")
    logger.info("=" * 60)

    # Counters
    processed = 0
    needs_review = 0
    failed = 0

    for filename in sorted(pdf_files):
        pdf_path = os.path.join(folder_path, filename)
        logger.info(f"Processing: {filename}")

        # Step 1: Extract text
        text = extract_text_from_pdf(pdf_path)
        if not text:
            logger.error(f"  ✗ Could not extract text — skipping")
            failed += 1
            continue

        # Step 2: Parse invoice data
        invoice_data, missing_fields = parse_invoice_data(text, filename)
        invoice_data["Source File"] = filename

        # Step 3: Check for duplicates
        if check_duplicate(invoice_data.get("Invoice Number")):
            logger.warning(f"  ⚠ Skipping — Invoice {invoice_data.get('Invoice Number')} already in Airtable")
            logger.info("-" * 40)
            continue

        # Step 5: Determine status
        if missing_fields:
            status = "Needs Review"
            notes  = f"Missing fields: {', '.join(missing_fields)}"
            logger.warning(f"  ⚠ Needs review — missing: {', '.join(missing_fields)}")
        else:
            status = "Processed"
            notes  = ""
            logger.info(f"  ✓ All fields extracted successfully")

        # Step 6: Insert to Airtable
        success, result = insert_to_airtable(invoice_data, status, notes)

        if success:
            logger.info(f"  ✓ Inserted to Airtable (ID: {result})")
            if status == "Processed":
                processed += 1
            else:
                needs_review += 1
        else:
            logger.error(f"  ✗ Airtable insert failed: {result}")
            failed += 1

        logger.info("-" * 40)

    # Summary
    logger.info("=" * 60)
    logger.info("PROCESSING COMPLETE")
    logger.info(f"  ✓ Processed:    {processed}")
    logger.info(f"  ⚠ Needs Review: {needs_review}")
    logger.info(f"  ✗ Failed:       {failed}")
    logger.info(f"  Total:          {len(pdf_files)}")
    logger.info("=" * 60)


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    invoices_folder = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "invoices")

    if not os.path.exists(invoices_folder):
        print(f"ERROR: Folder not found: {invoices_folder}")
        sys.exit(1)

    logger.info(f"Starting invoice processor")
    logger.info(f"Folder: {invoices_folder}")
    process_invoices(invoices_folder)
