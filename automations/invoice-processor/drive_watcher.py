#!/usr/bin/env python3
"""
Google Drive Invoice Watcher
Monitors "Invoices - To Process" folder for new PDFs,
processes them with invoice_processor.py, then moves to "Invoices - Processed".
"""

import os
import sys
import time
import logging
import tempfile
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import io

# Import our existing invoice processor
from invoice_processor import extract_text_from_pdf, parse_invoice_data, insert_to_airtable, check_duplicate

load_dotenv()

INBOX_FOLDER_ID     = os.getenv("DRIVE_INBOX_FOLDER_ID")
PROCESSED_FOLDER_ID = os.getenv("DRIVE_PROCESSED_FOLDER_ID")
SCOPES              = ["https://www.googleapis.com/auth/drive"]
POLL_INTERVAL       = 30  # seconds between checks

# Validate config
if not INBOX_FOLDER_ID or not PROCESSED_FOLDER_ID:
    print("ERROR: DRIVE_INBOX_FOLDER_ID and DRIVE_PROCESSED_FOLDER_ID must be set in .env")
    sys.exit(1)

# Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/drive_watcher.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ── Google Drive Auth ──────────────────────────────────────────────────────────

def get_drive_service():
    """Load credentials and return authenticated Drive service."""
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)


# ── Drive Operations ───────────────────────────────────────────────────────────

def list_pdfs_in_folder(service, folder_id):
    """List all PDF files in a Drive folder."""
    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    results = service.files().list(
        q=query,
        fields="files(id, name, createdTime)"
    ).execute()
    return results.get("files", [])


def download_file(service, file_id, dest_path):
    """Download a file from Drive to a local path."""
    request = service.files().get_media(fileId=file_id)
    with open(dest_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def move_to_processed(service, file_id, filename):
    """Move a file from inbox folder to processed folder."""
    service.files().update(
        fileId=file_id,
        addParents=PROCESSED_FOLDER_ID,
        removeParents=INBOX_FOLDER_ID,
        fields="id, parents"
    ).execute()
    logger.info(f"  ✓ Moved '{filename}' to Invoices - Processed")


# ── Main Processing ────────────────────────────────────────────────────────────

def process_file(service, file):
    """Download, extract, insert to Airtable, then move to processed."""
    filename = file["name"]
    file_id  = file["id"]

    logger.info(f"Processing: {filename}")

    # Download to temp file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        download_file(service, file_id, tmp_path)

        # Extract text
        text = extract_text_from_pdf(tmp_path)
        if not text:
            logger.error(f"  ✗ Could not extract text from {filename}")
            return False

        # Parse invoice data
        invoice_data, missing_fields = parse_invoice_data(text, filename)
        invoice_data["Source File"] = filename

        # Check for duplicates
        if check_duplicate(invoice_data.get("Invoice Number")):
            logger.warning(f"  ⚠ Skipping — Invoice {invoice_data.get('Invoice Number')} already in Airtable")
            move_to_processed(service, file_id, filename)  # Still move file so it doesn't reprocess
            return True

        # Determine status
        if missing_fields:
            status = "Needs Review"
            notes  = f"Missing fields: {', '.join(missing_fields)}"
            logger.warning(f"  ⚠ Needs review — missing: {', '.join(missing_fields)}")
        else:
            status = "Processed"
            notes  = ""
            logger.info(f"  ✓ All fields extracted successfully")

        # Insert to Airtable
        success, result = insert_to_airtable(invoice_data, status, notes)
        if success:
            logger.info(f"  ✓ Inserted to Airtable (ID: {result})")
            move_to_processed(service, file_id, filename)
            return True
        else:
            logger.error(f"  ✗ Airtable insert failed: {result}")
            return False

    finally:
        # Always clean up temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def watch_drive():
    """Poll Drive folder every POLL_INTERVAL seconds for new PDFs."""
    logger.info("=" * 60)
    logger.info("Drive Watcher Started")
    logger.info(f"Watching folder ID: {INBOX_FOLDER_ID}")
    logger.info(f"Polling every {POLL_INTERVAL} seconds")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 60)

    service = get_drive_service()
    processed_ids = set()  # Track files processed this session

    while True:
        try:
            files = list_pdfs_in_folder(service, INBOX_FOLDER_ID)
            new_files = [f for f in files if f["id"] not in processed_ids]

            if new_files:
                logger.info(f"Found {len(new_files)} new file(s)")
                for file in new_files:
                    success = process_file(service, file)
                    if success:
                        processed_ids.add(file["id"])
                    logger.info("-" * 40)
            else:
                logger.info(f"No new files. Next check in {POLL_INTERVAL}s...")

        except Exception as e:
            logger.error(f"Error during watch cycle: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    watch_drive()
