# Invoice Upload Tool — User Guide

**Last Updated:** March 2026
**Owner:** Syed
**Status:** Active

## What This Does

Automatically extracts invoice data from PDFs and saves it to Airtable — no manual data entry required.

## How to Use

1. Open: https://invoice-webapp-inky.vercel.app/
2. Click **"Click to upload"** and select your invoice PDF (or drag and drop)
3. Wait a few seconds while it extracts the data
4. Review the extracted fields — edit anything that looks wrong
5. Click **"Save to Airtable"**
6. Done! Check Airtable to see your invoice record

## Troubleshooting

**Extraction not accurate?**
Edit the fields manually before clicking Save. The tool does its best but some invoices have unusual formatting.

**Upload failing?**
Make sure the file is a PDF and under 10MB. Other file types are not supported.

**Duplicate invoice warning?**
The tool automatically detects if you've already uploaded the same invoice and will block the duplicate save.

**Questions or issues?**
Contact Syed.

## Supported Invoice Formats

Works best with:
- Standard invoices with clear invoice numbers
- Dates in common formats (MM/DD/YYYY, Month DD YYYY, etc.)
- Dollar amounts clearly labelled as "Total", "Amount Due", etc.

May need manual review for:
- Handwritten invoices
- Scanned images (low quality or low resolution)
- Invoices in foreign languages
- Non-standard layouts
