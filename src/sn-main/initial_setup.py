from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import json
import os

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']

def setup_credentials(account_id):
    config_path = os.getenv(f'GOOGLE_SHEETS_CONFIG_{account_id.upper()}')
    client_secrets_path = os.getenv(f'GOOGLE_CLIENT_SECRETS_{account_id.upper()}')

    if not config_path or not client_secrets_path:
        raise ValueError(f"Environment variables not set for {account_id}")

    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
    creds = flow.run_local_server(port=0)

    # Save the credentials for future use
    with open(config_path, 'w') as token:
        json.dump({'token': creds.to_json()}, token)

    print(f"Credentials for {account_id} have been saved to {config_path}")

if __name__ == '__main__':
    setup_credentials('JK')
    # setup_credentials('007')
