# Google API Authentication Guide

This document explains how to set up and use Google Sheets and Drive authentication in our project.

## For Non-Experts

### Two Types of Authentication

1. **Development Authentication**: Used when you're actively developing and need to interact with the API.
2. **Automatic Authentication**: Used for automated scripts or production environments.

### Initial Setup (Run Once)

1. Ensure you have the necessary environment variables set:
   - `GOOGLE_SHEETS_CONFIG_ACCOUNT1`: Path to the config file for account 1
   - `GOOGLE_CLIENT_SECRETS_ACCOUNT1`: Path to the client secrets file for account 1
   (Repeat for ACCOUNT2 if needed)

2. Run the initial setup script:
   ```python
   python initial_setup.py
   ```
   This will:
   - Open a browser window for you to log in to your Google account
   - Ask for permissions to access Sheets and Drive
   - Create a config file with your authentication tokens

### Using Authentication in Scripts

After the initial setup, you can use the `GoogleSheetsHandler` class in your scripts:


python
from google_sheets_handler import GoogleSheetsHandler
Create a handler for account 1
handler = GoogleSheetsHandler('account1')
handler.authenticate()
Now you can use handler to interact with Sheets and Drive
For example:
spreadsheet_id = 'your_spreadsheet_id_here'
range_name = 'Sheet1!A1:D5'
values = handler.read_spreadsheet(spreadsheet_id, range_name)
print(values)


### Troubleshooting

- If you get authentication errors, try running `initial_setup.py` again to refresh your tokens.
- Make sure your environment variables are correctly set before running any scripts.
- Never share or commit your config files or client secrets files.

## For Experienced Programmers

Our project sn-libraries uses a custom `GoogleSheetsHandler` class for Google Sheets and Drive API authentication. Key points:

- Authentication is handled via OAuth 2.0 flow.
- Credentials are stored in config files, paths set via environment variables.
- Two modes: interactive (for development) and service account (for automation).

### Usage


python
from google_sheets_handler import GoogleSheetsHandler
handler = GoogleSheetsHandler('account1')
handler.authenticate()
Use handler.sheets_service for Sheets API
Use handler.drive_service for Drive API



### Environment Variables

- `GOOGLE_SHEETS_CONFIG_ACCOUNT1`: Path to config file
- `GOOGLE_CLIENT_SECRETS_ACCOUNT1`: Path to client secrets file
- `GOOGLE_SERVICE_ACCOUNT_ACCOUNT1`: Path to service account key (for automation)

### Notes

- Run `initial_setup.py` to generate/refresh tokens for interactive mode.
- Use service account for automated scripts (no browser auth required).
- All config and secret files are in `.gitignore`.

Refer to `google_sheets_handler.py` for full implementation details.