"""
One-time setup script: runs the Google OAuth consent flow and saves
the resulting token.json, which drive_watcher.py expects to find.

Run this once, in a browser-accessible environment, before starting
drive_watcher.py for the first time (or whenever token.json is lost/revoked).
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]


def main():
    if not os.path.exists("credentials.json"):
        raise FileNotFoundError(
            "credentials.json not found. Download it from Google Cloud Console "
            "(OAuth Client ID, Desktop app type) and place it in this folder."
        )

    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)

    with open("token.json", "w") as f:
        f.write(creds.to_json())

    print("token.json created successfully. You can now run drive_watcher.py.")


if __name__ == "__main__":
    main()
