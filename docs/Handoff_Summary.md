# Crestline Manufacturing — Automation Handoff Summary

**Prepared by:** Syed
**Date:** March 2026
**Status:** Pre-Production

---

## What Was Built

Three automations that together save 100+ hours per month across Finance and Sales Operations.

| Automation | What It Does | Time Saved | Status |
|---|---|---|---|
| Invoice Processor | Extracts PDF invoice data → Airtable | 2 hrs/day | 🔵 UAT |
| Invoice Web App | Self-service invoice upload portal | On-demand | 🔵 UAT |
| Sales Ops Sync | Airtable deals → 3 Google Sheets | 4 hrs/week | 🔵 UAT |

---

## Where Everything Lives

| Item | Location |
|---|---|
| All code | GitHub repo |
| Invoice Web App | https://crestline-automations-kmxz9bu4w-isyedrahman77s-projects.vercel.app/ |
| Invoice Tracker | Airtable — Invoice Tracker base |
| Runbooks | `/docs/` folder in GitHub repo |

---


## If Something Breaks

1. **Check the runbook first** — most issues are covered there
2. **Common fixes:**
   - API errors → regenerate the Airtable token at https://airtable.com/create/tokens
   - Web app down → check https://vercel.com dashboard
   - Google Sheets not updating → re-share sheet with service account
3. **If still stuck** → contact Syed

---

## Credentials & Security

- All API keys stored in `.env` files — never committed to GitHub
- Airtable tokens: regenerate at https://airtable.com/create/tokens
- Google credentials: stored as `credentials.json` in each automation folder
- Vercel env vars: managed at https://vercel.com dashboard → Settings → Environment Variables

---

## What's NOT Automated Yet (Future Opportunities)

| Department | Opportunity | Effort |
|---|---|---|
| Sales Ops | Connect live Airtable → Google Sheets sync | Low (1 day) |
| Customer Service | Email auto-classification and routing | Medium |
| Inventory | Excel monitoring with Slack alerts | Medium |
| HR | Onboarding document generation | Medium |

---

*All documentation, code, and runbooks are in the GitHub repository.*
*The automations are designed to run reliably without manual intervention.*
