"""
Sales Ops Sync
Pulls deal data from Airtable and pushes formatted records to three
separate Google Sheets — one each for Finance, the CEO, and Marketing.
Built for Crestline Manufacturing Co. — replaces a weekly manual export.
"""

import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ── Setup ────────────────────────────────────────────────────────────────────

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("sync.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ── Google Sheets Config ─────────────────────────────────────────────────────
# Replace these with your actual Google Sheet IDs after creating them

SHEET_IDS = {
    "revenue_tracking": os.getenv("SHEET_REVENUE_TRACKING"),
    "sales_forecast":   os.getenv("SHEET_SALES_FORECAST"),
    "customer_data":    os.getenv("SHEET_CUSTOMER_DATA"),
}

# ── Data Source ──────────────────────────────────────────────────────────────

def get_deals():
    """
    Load deals from mock JSON file.
    To switch to real Airtable: replace this function with Airtable API call.
    """
    with open("mock_deals.json") as f:
        deals = json.load(f)
    logger.info(f"Loaded {len(deals)} deals from mock data")
    return deals


# ── Data Formatting ──────────────────────────────────────────────────────────

def format_date(date_str):
    """Convert YYYY-MM-DD to MM/DD/YYYY for Finance/CEO sheets."""
    if not date_str:
        return ""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%m/%d/%Y")
    except ValueError:
        return date_str


def format_currency(amount):
    """Format number as $X,XXX.XX string."""
    if amount is None:
        return "$0.00"
    return f"${amount:,.2f}"


# ── Sheet Transformations ────────────────────────────────────────────────────

def build_revenue_tracking(deals):
    """Finance sheet: all deals, specific columns."""
    headers = ["Deal Name", "Company", "Amount", "Close Date", "Stage", "Owner"]
    rows = [headers]
    for d in deals:
        rows.append([
            d.get("Deal Name", ""),
            d.get("Company", ""),
            format_currency(d.get("Amount")),
            format_date(d.get("Close Date")),
            d.get("Stage", ""),
            d.get("Owner", ""),
        ])
    return rows


def build_sales_forecast(deals):
    """CEO sheet: active pipeline only (exclude Closed Lost)."""
    headers = ["Deal Name", "Amount", "Close Date", "Probability", "Stage", "Territory"]
    active = [d for d in deals if d.get("Stage") != "Closed Lost"]
    rows = [headers]
    for d in active:
        rows.append([
            d.get("Deal Name", ""),
            format_currency(d.get("Amount")),
            format_date(d.get("Close Date")),
            f"{d.get('Probability', 0)}%",
            d.get("Stage", ""),
            d.get("Territory", ""),
        ])
    return rows


def build_customer_data(deals):
    """Marketing sheet: Closed Won only, different column order."""
    headers = ["Company", "Industry", "Company Size", "Deal Owner", "Close Date", "Amount"]
    closed_won = [d for d in deals if d.get("Stage") == "Closed Won"]
    rows = [headers]
    for d in closed_won:
        rows.append([
            d.get("Company", ""),
            d.get("Industry", ""),
            d.get("Company Size", ""),
            d.get("Owner", ""),
            format_date(d.get("Close Date")),
            format_currency(d.get("Amount")),
        ])
    return rows


# ── Google Sheets Writer ─────────────────────────────────────────────────────

def get_sheets_service():
    """Authenticate and return Google Sheets API service."""
    creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH, scopes=SCOPES)
    return build("sheets", "v4", credentials=creds)


def write_to_sheet(service, sheet_id, sheet_name, rows):
    """Write rows to a Google Sheet, starting from A1."""
    range_name = f"{sheet_name}!A1"
    body = {"values": rows}

    service.spreadsheets().values().clear(
        spreadsheetId=sheet_id,
        range=f"{sheet_name}!A:Z"
    ).execute()

    result = service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption="RAW",
        body=body
    ).execute()

    updated = result.get("updatedRows", 0)
    logger.info(f"  → {sheet_name}: wrote {updated} rows (including header)")
    return updated


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    logger.info("=== Sales Sync Starting ===")

    # Load data
    deals = get_deals()

    # Build sheet data
    revenue_rows  = build_revenue_tracking(deals)
    forecast_rows = build_sales_forecast(deals)
    customer_rows = build_customer_data(deals)

    logger.info(f"Revenue Tracking: {len(revenue_rows)-1} deals")
    logger.info(f"Sales Forecast:   {len(forecast_rows)-1} active deals")
    logger.info(f"Customer Data:    {len(customer_rows)-1} closed won deals")

    # Connect to Google Sheets
    logger.info("Connecting to Google Sheets...")
    service = get_sheets_service()

    # Write to each sheet
    logger.info("Writing to sheets...")
    write_to_sheet(service, SHEET_IDS["revenue_tracking"], "Sheet1", revenue_rows)
    write_to_sheet(service, SHEET_IDS["sales_forecast"],   "Sheet1", forecast_rows)
    write_to_sheet(service, SHEET_IDS["customer_data"],    "Sheet1", customer_rows)

    logger.info("=== Sync Complete ===")


if __name__ == "__main__":
    main()
