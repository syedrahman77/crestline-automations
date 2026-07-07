# Invoice Upload Web App — Runbook

**Last Updated:** March 2026
**Owner:** Syed
**Status:** Active

---

## Overview

**What it does:** A web app where any Finance team member can upload a PDF invoice from any device, review the extracted data, and save it to Airtable with one click.

**Why it exists:** The local invoice processor requires access to a specific computer. The web app lets anyone on the team process invoices from any device — no setup required.

**Who uses it:** Entire Finance team. Anyone with the URL can use it.

**Live URL:** https://crestline-automations-kmxz9bu4w-isyedrahman77s-projects.vercel.app/

**Impact:** Self-service invoice processing — no dependency on a single machine or person.

---

## How to Use It (For Finance Team)

1. **Open the app:** https://crestline-automations-kmxz9bu4w-isyedrahman77s-projects.vercel.app/
2. **Upload a PDF:** Click "Click to upload" or drag and drop your invoice PDF
3. **Wait:** The app extracts data automatically (takes 3-10 seconds)
4. **Review:** Check the extracted fields — edit anything that looks wrong
5. **Save:** Click "Save to Airtable"
6. **Done:** Check Airtable to confirm the record appeared

---

## What Could Go Wrong (For Users)

**"Please upload a PDF file" error**
- Cause: Wrong file type selected
- Fix: Make sure you're uploading a `.pdf` file, not a Word doc or image

**Fields show as empty or wrong**
- Cause: Invoice has unusual formatting
- Fix: Edit the fields manually before clicking Save

**"Duplicate invoice" error**
- Cause: This invoice was already saved to Airtable
- Fix: Check Airtable — the record is already there. No action needed.

**App loads but nothing happens after upload**
- Cause: Temporary server issue
- Fix: Refresh the page and try again. If it persists, use the local script as backup.

---

## Deployment & Infrastructure

- **Hosted on:** Vercel (free tier)
- **GitHub repo:** https://github.com/isyedrahman77/crestline-automations (root directory: `automations/invoice-webapp`)
- **Vercel dashboard:** https://vercel.com/isyedrahman77s-projects/crestline-automations
- **Auto-deploys:** Any push to the `main` branch on GitHub triggers a redeploy

---

## Environment Variables (Vercel)

Set in Vercel dashboard → Settings → Environment Variables:

| Variable | Description |
|---|---|
| `AIRTABLE_TOKEN` | Airtable Personal Access Token |
| `AIRTABLE_BASE_ID` | Airtable base ID for Invoice Tracker |

**To update credentials:**
1. Go to Vercel dashboard → Settings → Environment Variables
2. Update the value
3. Go to Deployments → Redeploy (env vars only take effect on new deployments)

---

## Updating the App

1. Make code changes locally in:
   ```
   automations/invoice-webapp/
   ```
2. Push to GitHub:
   ```bash
   git add .
   git commit -m "describe your change"
   git push
   ```
3. Vercel auto-redeploys within 2 minutes

---

## Monitoring

- **Vercel logs:** https://vercel.com/isyedrahman77s-projects/crestline-automations → Logs
- **Error rate:** Check Vercel dashboard → Observability
- **Airtable:** Verify records are appearing after each upload

---

## Emergency Procedures

**If the web app is down:**
1. Check Vercel status at https://vercel.com/isyedrahman77s-projects/crestline-automations
2. Use the local invoice processor script as backup
3. Notify Syed

**If Airtable saves are failing:**
1. Check that `AIRTABLE_TOKEN` hasn't expired in Vercel environment variables
2. Regenerate token at https://airtable.com/create/tokens
3. Update in Vercel dashboard and redeploy

**Contact:** Syed
