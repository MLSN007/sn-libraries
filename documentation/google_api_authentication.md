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

