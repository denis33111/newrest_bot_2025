#!/usr/bin/env python3
"""
Google Sheets Service
Handles all Google Sheets operations
"""

import os
import logging
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

# Load environment variables
GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
GOOGLE_SERVICE_ACCOUNT_EMAIL = os.getenv('GOOGLE_SERVICE_ACCOUNT_EMAIL')

def init_google_sheets():
    """Initialize Google Sheets connection"""
    try:
        # Parse private key
        private_key = os.getenv('GOOGLE_PRIVATE_KEY').replace('\\n', '\n')
        
        # Define scope
        scope = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Create credentials
        credentials = Credentials.from_service_account_info({
            "type": "service_account",
            "project_id": "newrest-465515",
            "private_key_id": "your-key-id",
            "private_key": private_key,
            "client_email": GOOGLE_SERVICE_ACCOUNT_EMAIL,
            "client_id": "your-client-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{GOOGLE_SERVICE_ACCOUNT_EMAIL}"
        }, scopes=scope)
        
        # Initialize gspread client
        gc = gspread.authorize(credentials)
        
        # Open the spreadsheet
        spreadsheet = gc.open_by_key(GOOGLE_SHEETS_ID)
        
        return {
            'status': 'success',
            'client': gc,
            'spreadsheet': spreadsheet,
            'sheets': {
                'registration': spreadsheet.worksheet('REGISTRATION'),
                'workers': spreadsheet.worksheet('WORKERS'),
                'august_2025': spreadsheet.worksheet('2025/8')
            }
        }
    except Exception as e:
        logger.error(f"Google Sheets initialization failed: {e}")
        return {'status': 'error', 'error': str(e)}

def check_user_status(user_id):
    """Check user status in WORKERS sheet"""
    try:
        sheets_data = init_google_sheets()
        if sheets_data['status'] != 'success':
            return 'ERROR'
        
        workers_sheet = sheets_data['sheets']['workers']
        workers_data = workers_sheet.get_all_values()
        
        # Check if user_id exists in the sheet
        for row in workers_data[1:]:  # Skip header row
            if len(row) >= 2 and str(user_id) == str(row[1]):  # Check ID column
                status = row[2] if len(row) > 2 else 'UNKNOWN'  # Check STATUS column
                return status
        
        return 'NOT_FOUND'
        
    except Exception as e:
        logger.error(f"Error checking user status: {e}")
        return 'ERROR'

def get_sheet_data(sheet_name):
    """Get data from specific sheet"""
    try:
        sheets_data = init_google_sheets()
        if sheets_data['status'] != 'success':
            return None
        
        sheet = sheets_data['sheets'].get(sheet_name)
        if not sheet:
            return None
        
        return sheet.get_all_values()
    except Exception as e:
        logger.error(f"Error getting sheet data for {sheet_name}: {e}")
        return None

def save_registration_data(data):
    """Save registration data to REGISTRATION sheet"""
    try:
        sheets_data = init_google_sheets()
        if sheets_data['status'] != 'success':
            return False
        
        registration_sheet = sheets_data['sheets']['registration']
        
        # Prepare data row
        row_data = [
            data.get('language', 'gr'),           # Column A - LANGUAGE
            data.get('user_id', ''),              # Column B - USER_ID
            '',                                   # Column C - WORKING
            data.get('full_name', ''),            # Column D - NAME
            data.get('age', ''),                  # Column E - AGE
            data.get('phone', ''),                # Column F - PHONE
            data.get('email', ''),                # Column G - EMAIL
            data.get('address', ''),              # Column H - ADDRESS
            data.get('transportation', ''),       # Column I - TRANSPORT
            data.get('bank', ''),                 # Column J - BANK
            data.get('driving_license', ''),      # Column K - DR_LICENCE_NO
            '',                                   # Column L - CRIMINAL_RECORD
            '',                                   # Column M - HEALTH_CERT
            '',                                   # Column N - AMKA
            '',                                   # Column O - AMA
            '',                                   # Column P - AFM
            data.get('status', 'WAITING'),        # Column Q - STATUS
            '',                                   # Column R - COURSE_DATE
            '',                                   # Column S - PRE_COURSE_REMINDER
            ''                                    # Column T - DAY_COURSE_REMINDER
        ]
        
        # Add row to sheet
        registration_sheet.append_row(row_data)
        
        logger.info(f"Registration data saved for user {data.get('user_id')}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving registration data: {e}")
        return False
