#!/usr/bin/env python3
"""
Google Sheets Service
Handles all Google Sheets operations
"""

import os
import logging
import gspread
from datetime import datetime
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
                'workers': spreadsheet.worksheet('WORKERS')
            }
        }
    except Exception as e:
        logger.error(f"Google Sheets initialization failed: {e}")
        return {'status': 'error', 'error': str(e)}

def get_monthly_sheet(sheet_name):
    """Get monthly sheet by name - only called when needed"""
    try:
        sheets_data = init_google_sheets()
        if sheets_data['status'] != 'success':
            return None
        
        return sheets_data['spreadsheet'].worksheet(sheet_name)
    except Exception as e:
        logger.error(f"Error getting monthly sheet {sheet_name}: {e}")
        return None

def check_user_status(user_id):
    """Check user status in WORKERS sheet - only ID and STATUS columns"""
    try:
        sheets_data = init_google_sheets()
        if sheets_data['status'] != 'success':
            return 'ERROR'
        
        workers_sheet = sheets_data['sheets']['workers']
        
        # Get only ID column (B) and STATUS column (C) - more efficient
        id_column = workers_sheet.col_values(2)  # Column B - ID
        status_column = workers_sheet.col_values(3)  # Column C - STATUS
        
        # Check if user_id exists in ID column
        for i, user_id_in_sheet in enumerate(id_column[1:], start=2):  # Skip header row
            if str(user_id) == str(user_id_in_sheet):
                # Get corresponding status
                status = status_column[i-1] if i-1 < len(status_column) else 'UNKNOWN'
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

def save_worker_data(data):
    """Save worker data to WORKERS sheet"""
    try:
        logger.info(f"Starting save_worker_data for user {data.get('user_id')}")
        logger.info(f"Data being saved: {data}")
        
        sheets_data = init_google_sheets()
        if sheets_data['status'] != 'success':
            logger.error(f"Google Sheets initialization failed: {sheets_data}")
            return False
        
        workers_sheet = sheets_data['sheets']['workers']
        logger.info(f"Got workers sheet: {workers_sheet}")
        
        # Prepare worker data row
        worker_row = [
            data.get('full_name', ''),            # Column A - NAME
            data.get('user_id', ''),              # Column B - ID
            'WAITING',                            # Column C - STATUS
            data.get('language', 'gr')            # Column D - LANGUAGE
        ]
        
        logger.info(f"Worker row to append: {worker_row}")
        
        # Add row to WORKERS sheet using specific range to ensure correct columns
        try:
            # Get the next available row
            all_values = workers_sheet.get_all_values()
            next_row = len(all_values) + 1
            
            # Update specific cells in the correct columns (A, B, C, D)
            workers_sheet.update(f'A{next_row}', worker_row[0])  # NAME
            workers_sheet.update(f'B{next_row}', worker_row[1])  # ID
            workers_sheet.update(f'C{next_row}', worker_row[2])  # STATUS
            workers_sheet.update(f'D{next_row}', worker_row[3])  # LANGUAGE
            
            logger.info(f"Worker data updated in row {next_row} for user {data.get('user_id')}")
            
            # Verify the data was actually added
            all_values = workers_sheet.get_all_values()
            logger.info(f"Total rows in WORKERS sheet after update: {len(all_values)}")
            logger.info(f"Last row in WORKERS sheet: {all_values[-1] if all_values else 'EMPTY'}")
            
        except Exception as update_error:
            logger.error(f"Worker data update failed for user {data.get('user_id')}: {update_error}")
            return False
        
        logger.info(f"Worker data saved for user {data.get('user_id')}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving worker data: {e}")
        return False

# Working status and time tracking functions
async def get_user_working_status(user_id):
    """Get user's current working status and today's data"""
    try:
        sheets_data = init_google_sheets()
        if sheets_data['status'] != 'success':
            return {'checked_in': False, 'error': 'Sheets connection failed'}
        
        # Get current date for today's tracking
        today = datetime.now().strftime("%m/%d/%Y")
        
        # Check if user is in WORKERS sheet
        workers_sheet = sheets_data['sheets']['workers']
        workers_data = workers_sheet.get_all_values()
        
        user_name = None
        for row in workers_data[1:]:  # Skip header row
            if len(row) >= 2 and str(user_id) == str(row[1]):  # Check ID column
                user_name = row[0]  # Get name from column A
                break
        
        if not user_name:
            return {'checked_in': False, 'error': 'User not found in workers sheet'}
        
        # Get current month sheet
        current_month_sheet_name = get_current_month_sheet()
        if not current_month_sheet_name:
            return {'checked_in': False, 'error': 'Could not determine current month'}
        
        # Check if current month sheet exists, create if not
        monthly_sheet = get_monthly_sheet(current_month_sheet_name)
        if not monthly_sheet:
            # Create new monthly sheet
            monthly_sheet = create_monthly_sheet(sheets_data['spreadsheet'], current_month_sheet_name)
            if not monthly_sheet:
                return {'checked_in': False, 'error': 'Could not create monthly sheet'}
        
        monthly_data = monthly_sheet.get_all_values()
        
        # Find user's row in monthly sheet
        user_row = None
        for i, row in enumerate(monthly_data[2:], start=3):  # Skip header rows, start from row 3
            if len(row) > 0 and row[0] == user_name:  # Check name column
                user_row = i
                break
        
        if not user_row:
            # Create new row for user
            user_row = create_user_row_in_monthly_sheet(monthly_sheet, user_name)
            if not user_row:
                return {'checked_in': False, 'user_name': user_name, 'today_hours': '0h 0m'}
        
        # Get today's data from monthly sheet
        today_column = get_today_column()
        if today_column is None:
            return {'checked_in': False, 'user_name': user_name, 'today_hours': '0h 0m'}
        
        # Get today's attendance data
        today_data = monthly_sheet.cell(user_row, today_column).value
        
        if not today_data:
            return {'checked_in': False, 'user_name': user_name, 'today_hours': '0h 0m'}
        
        # Parse today's data to determine status
        if '-' in today_data and not today_data.endswith('-'):
            # Has both check-in and check-out times
            return {
                'checked_in': False,
                'user_name': user_name,
                'today_hours': calculate_hours_from_data(today_data),
                'check_in_time': today_data.split('-')[0].strip(),
                'check_out_time': today_data.split('-')[1].strip()
            }
        elif today_data.endswith('-'):
            # Only check-in time (checked in)
            check_in_time = today_data.replace('-', '').strip()
            return {
                'checked_in': True,
                'user_name': user_name,
                'today_hours': '0h 0m',
                'check_in_time': check_in_time
            }
        else:
            # Only check-in time without dash
            return {
                'checked_in': True,
                'user_name': user_name,
                'today_hours': '0h 0m',
                'check_in_time': today_data
            }
            
    except Exception as e:
        logger.error(f"Error getting user working status: {e}")
        return {'checked_in': False, 'error': str(e)}

async def update_working_status(user_id, checked_in, check_in_time=None, check_out_time=None, work_hours=None, location=None):
    """Update user's working status in Google Sheets"""
    try:
        sheets_data = init_google_sheets()
        if sheets_data['status'] != 'success':
            return False
        
        # Get user name from WORKERS sheet
        workers_sheet = sheets_data['sheets']['workers']
        workers_data = workers_sheet.get_all_values()
        
        user_name = None
        for row in workers_data[1:]:  # Skip header row
            if len(row) >= 2 and str(user_id) == str(row[1]):  # Check ID column
                user_name = row[0]  # Get name from column A
                break
        
        if not user_name:
            logger.error(f"User {user_id} not found in workers sheet")
            return False
        
        # Get today's column in monthly sheet
        today_column = get_today_column()
        if today_column is None:
            logger.error("Could not determine today's column")
            return False
        
        # Get current month sheet
        current_month_sheet_name = get_current_month_sheet()
        if not current_month_sheet_name:
            logger.error("Could not determine current month")
            return False
        
        # Check if current month sheet exists, create if not
        monthly_sheet = get_monthly_sheet(current_month_sheet_name)
        if not monthly_sheet:
            # Create new monthly sheet
            monthly_sheet = create_monthly_sheet(sheets_data['spreadsheet'], current_month_sheet_name)
            if not monthly_sheet:
                logger.error("Could not create monthly sheet")
                return False
        
        monthly_data = monthly_sheet.get_all_values()
        
        # Find user's row in monthly sheet
        user_row = None
        for i, row in enumerate(monthly_data[2:], start=3):  # Skip header rows, start from row 3
            if len(row) > 0 and row[0] == user_name:  # Check name column
                user_row = i
                break
        
        if not user_row:
            # Create new row for user
            user_row = create_user_row_in_monthly_sheet(monthly_sheet, user_name)
            if not user_row:
                logger.error(f"Could not create row for user {user_name}")
                return False
        
        # Prepare today's data
        if checked_in:
            # Check in - store time with dash
            today_data = f"{check_in_time}-"
        else:
            # Check out - get existing check-in time and add check-out
            existing_data = monthly_sheet.cell(user_row, today_column).value or ""
            if existing_data.endswith('-'):
                # Has check-in time, add check-out
                check_in_time = existing_data.replace('-', '').strip()
                today_data = f"{check_in_time}-{check_out_time}"
            elif '-' in existing_data and not existing_data.endswith('-'):
                # Already has both check-in and check-out, don't overwrite
                logger.warning(f"User {user_name} already has complete data for today: {existing_data}")
                return False
            else:
                # No existing check-in time, just store check-out
                today_data = check_out_time
        
        # Update the cell
        monthly_sheet.update_cell(user_row, today_column, today_data)
        
        logger.info(f"Updated working status for user {user_id}: {today_data}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating working status: {e}")
        return False

def get_today_column():
    """Get today's column number in the monthly sheet"""
    try:
        # Get Greek timezone
        import pytz
        greek_tz = pytz.timezone('Europe/Athens')
        today = datetime.now(greek_tz)
        
        # Get current month and year
        current_month = today.month
        current_year = today.year
        current_day = today.day
        
        # Create sheet name based on current month/year
        sheet_name = f"{current_year}/{current_month}"
        
        # For monthly sheets, columns are:
        # A: NAME, B: 1st, C: 2nd, D: 3rd, etc.
        
        if 1 <= current_day <= 31:  # All days of month are tracked
            return current_day + 1  # Column B = 2, C = 3, etc.
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting today's column: {e}")
        return None

def get_current_month_sheet():
    """Get the current month's sheet name"""
    try:
        import pytz
        greek_tz = pytz.timezone('Europe/Athens')
        today = datetime.now(greek_tz)
        
        return f"{today.year}/{today.month}"
        
    except Exception as e:
        logger.error(f"Error getting current month sheet: {e}")
        return None

def calculate_hours_from_data(time_data):
    """Calculate work hours from time data string"""
    try:
        if '-' not in time_data or time_data.endswith('-'):
            return '0h 0m'
        
        # Parse times
        check_in_str, check_out_str = time_data.split('-', 1)
        check_in_str = check_in_str.strip()
        check_out_str = check_out_str.strip()
        
        if not check_in_str or not check_out_str:
            return '0h 0m'
        
        # Parse times
        check_in = datetime.strptime(check_in_str, "%H:%M")
        check_out = datetime.strptime(check_out_str, "%H:%M")
        
        # Calculate difference
        diff = check_out - check_in
        
        # Convert to hours and minutes
        total_minutes = int(diff.total_seconds() / 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        return f"{hours}h {minutes}m"
        
    except Exception as e:
        logger.error(f"Error calculating hours from data: {e}")
        return '0h 0m'

def create_monthly_sheet(spreadsheet, sheet_name):
    """Create a new monthly sheet with proper structure"""
    try:
        # Create new worksheet
        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=32)
        
        # Set up headers
        headers = ['NAME']
        
        # Add day columns (1-31)
        for day in range(1, 32):
            headers.append(f"{day}")
        
        # Update headers
        worksheet.update('A1:AF1', [headers])
        
        # Format headers
        worksheet.format('A1:AF1', {
            'backgroundColor': {'red': 0.8, 'green': 0.8, 'blue': 1.0},
            'textFormat': {'bold': True}
        })
        
        logger.info(f"Created monthly sheet: {sheet_name}")
        return worksheet
        
    except Exception as e:
        logger.error(f"Error creating monthly sheet {sheet_name}: {e}")
        return None

def create_user_row_in_monthly_sheet(monthly_sheet, user_name):
    """Create a new row for user in monthly sheet"""
    try:
        # Get all values to find next empty row
        all_values = monthly_sheet.get_all_values()
        
        # Find next empty row (start from row 2, after headers)
        next_row = len(all_values) + 1
        
        # Add user name in column A
        monthly_sheet.update_cell(next_row, 1, user_name)
        
        logger.info(f"Created row for user {user_name} at row {next_row}")
        return next_row
        
    except Exception as e:
        logger.error(f"Error creating row for user {user_name}: {e}")
        return None

def get_greek_time():
    """Get current time in Greek timezone"""
    try:
        import pytz
        greek_tz = pytz.timezone('Europe/Athens')
        greek_time = datetime.now(greek_tz)
        return greek_time.strftime("%H:%M")
    except Exception as e:
        logger.error(f"Error getting Greek time: {e}")
        return datetime.now().strftime("%H:%M")
