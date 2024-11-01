"""
Initial Setup Script for Google OAuth2 Credentials

This script handles the initial setup for Google OAuth2 credentials, which are necessary
for authenticating and authorizing access to Google APIs.

Purpose:
- Import required libraries for handling Google OAuth2 credentials and JSON operations.
- Set up the foundation for creating, storing, and managing OAuth2 credentials.

Usage:
This script should be run:
1. During the first-time setup of the application.
2. When refreshing or updating OAuth2 credentials.
3. If the existing credentials have expired or become invalid.

Recommendations:
- Ensure you have the necessary Google Cloud Project set up with OAuth2 configured.
- Keep this script separate from your main application code for security reasons.
- Store sensitive information (like client secrets) securely and not in version control.
- Consider implementing a check in your main application to verify if this setup
  has been completed before attempting to use Google APIs.

Note: This script only imports the necessary modules. Additional code for credential
creation and storage should be implemented as needed.

Dependencies:
- google-auth
- google-auth-oauthlib
"""

import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]


def setup_credentials(account_id):
    print(f"GOOGLE_SHEETS_CONFIG_{account_id.upper()}")
    config_path = os.getenv(f"GOOGLE_SHEETS_CONFIG_{account_id.upper()}")
    print(f"config_path: {config_path}")
    print(f"GOOGLE_CLIENT_SECRETS_{account_id.upper()}")

    client_secrets_path = os.getenv(f"GOOGLE_CLIENT_SECRETS_{account_id.upper()}")
    print(f"client_secrets_path: {client_secrets_path}")

    if not config_path or not client_secrets_path:
        raise ValueError(f"Environment variables not set for {account_id}")

    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
    creds = flow.run_local_server(port=0)

    # Save the credentials for future use
    with open(config_path, "w") as token:
        json.dump({"token": creds.to_json()}, token)

    print(f"Credentials for {account_id} have been saved to {config_path}")


if __name__ == "__main__":
    setup_credentials("JK")
    # setup_credentials("007")
    # setup_credentials("NOCA")
    # setup_credentials("M4D")
