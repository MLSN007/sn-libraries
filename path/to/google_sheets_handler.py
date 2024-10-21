from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.http import Request

class GoogleSheetsHandler:
    def authenticate(self) -> None:
        """
        Authenticates with Google Sheets API using OAuth2 credentials.

        Raises:
            RefreshError: If the token refresh fails.
        """
        try:
            self.creds.refresh(Request())
        except RefreshError:
            logger.warning("Refresh token expired or revoked. Initiating re-authentication.")
            flow = InstalledAppFlow.from_client_secrets_file(
                'path/to/credentials.json',
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            self.creds = flow.run_local_server(port=0)
            self.save_credentials()
            logger.info("Re-authentication successful and credentials updated.")
