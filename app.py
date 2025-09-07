#!/usr/bin/env python3
"""
NewRest Bot 2025 - Health Check & Connection Test
Minimal script to verify all connections are working
"""

import os
import asyncio
import logging
from flask import Flask, jsonify, request
from telegram import Bot
import gspread
from google.oauth2.service_account import Credentials

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Load environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME')
ADMIN_GROUP_ID = os.getenv('ADMIN_GROUP_ID')
GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
GOOGLE_SERVICE_ACCOUNT_EMAIL = os.getenv('GOOGLE_SERVICE_ACCOUNT_EMAIL')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Initialize bot
bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None

# Initialize Google Sheets
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

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'NewRest Bot 2025',
        'version': '1.0.0',
        'timestamp': asyncio.get_event_loop().time()
    })

# Telegram bot test endpoint
@app.route('/test/telegram', methods=['GET'])
async def test_telegram():
    """Test Telegram bot connection"""
    try:
        if not bot:
            return jsonify({'status': 'error', 'message': 'Bot not initialized'})
        
        # Get bot info
        bot_info = await bot.get_me()
        
        return jsonify({
            'status': 'success',
            'bot_info': {
                'id': bot_info.id,
                'username': bot_info.username,
                'first_name': bot_info.first_name,
                'is_bot': bot_info.is_bot
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

# Google Sheets test endpoint
@app.route('/test/sheets', methods=['GET'])
def test_sheets():
    """Test Google Sheets connection"""
    try:
        sheets_data = init_google_sheets()
        
        if sheets_data['status'] == 'error':
            return jsonify(sheets_data)
        
        # Test reading from each sheet
        registration_data = sheets_data['sheets']['registration'].get_all_values()
        workers_data = sheets_data['sheets']['workers'].get_all_values()
        august_data = sheets_data['sheets']['august_2025'].get_all_values()
        
        return jsonify({
            'status': 'success',
            'spreadsheet_id': GOOGLE_SHEETS_ID,
            'sheets': {
                'registration': {
                    'rows': len(registration_data),
                    'columns': len(registration_data[0]) if registration_data else 0
                },
                'workers': {
                    'rows': len(workers_data),
                    'columns': len(workers_data[0]) if workers_data else 0
                },
                'august_2025': {
                    'rows': len(august_data),
                    'columns': len(august_data[0]) if august_data else 0
                }
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)})

# Complete system test
@app.route('/test/all', methods=['GET'])
async def test_all():
    """Test all connections"""
    results = {
        'health': 'healthy',
        'telegram': None,
        'google_sheets': None,
        'overall_status': 'unknown'
    }
    
    # Test Telegram
    try:
        if bot:
            bot_info = await bot.get_me()
            results['telegram'] = {'status': 'success', 'username': bot_info.username}
        else:
            results['telegram'] = {'status': 'error', 'message': 'Bot not initialized'}
    except Exception as e:
        results['telegram'] = {'status': 'error', 'error': str(e)}
    
    # Test Google Sheets
    try:
        sheets_data = init_google_sheets()
        if sheets_data['status'] == 'success':
            # Test reading from each sheet
            registration_data = sheets_data['sheets']['registration'].get_all_values()
            workers_data = sheets_data['sheets']['workers'].get_all_values()
            august_data = sheets_data['sheets']['august_2025'].get_all_values()
            
            results['google_sheets'] = {
                'status': 'success',
                'spreadsheet_id': GOOGLE_SHEETS_ID,
                'sheets': {
                    'registration': {
                        'rows': len(registration_data),
                        'columns': len(registration_data[0]) if registration_data else 0
                    },
                    'workers': {
                        'rows': len(workers_data),
                        'columns': len(workers_data[0]) if workers_data else 0
                    },
                    'august_2025': {
                        'rows': len(august_data),
                        'columns': len(august_data[0]) if august_data else 0
                    }
                }
            }
        else:
            results['google_sheets'] = sheets_data
    except Exception as e:
        results['google_sheets'] = {'status': 'error', 'error': str(e)}
    
    # Determine overall status
    if (results['telegram']['status'] == 'success' and 
        results['google_sheets']['status'] == 'success'):
        results['overall_status'] = 'all_connected'
    else:
        results['overall_status'] = 'partial_failure'
    
    return jsonify(results)

# Telegram webhook endpoint
@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    data = request.get_json()
    logger.info(f"Telegram webhook received: {data}")
    
    # Process Telegram update
    if data and 'message' in data:
        asyncio.create_task(handle_telegram_message(data['message']))
    
    return jsonify({'status': 'ok'})

async def handle_telegram_message(message):
    """Handle incoming Telegram messages"""
    try:
        user_id = message['from']['id']
        username = message['from'].get('username', 'Unknown')
        text = message.get('text', '')
        
        logger.info(f"Processing message from user {user_id} ({username}): {text}")
        
        # Check if user is in WORKERS sheet
        user_status = await check_user_status(user_id)
        
        if user_status == 'WORKING':
            await send_working_console(user_id)
        elif user_status == 'NOT_FOUND':
            await send_registration_flow(user_id)
        elif user_status == 'OFF':
            # Disabled user - no response
            logger.info(f"Disabled user {user_id} - ignoring message")
            return
        else:
            await send_error_message(user_id)
            
    except Exception as e:
        logger.error(f"Error handling Telegram message: {e}")

async def check_user_status(user_id):
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

async def send_working_console(user_id):
    """Send working console message"""
    message = """
🚀 **Working Console - Coming Soon**

Welcome back! Your working console is being prepared.

**Available Soon:**
• Check-in/out system
• Daily attendance tracking
• Schedule management
• Status updates

Stay tuned! 🎯
    """
    await bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')

async def send_registration_flow(user_id):
    """Send registration flow message"""
    message = """
📝 **Registration Flow - Coming Soon**

Welcome! You need to complete registration first.

**Registration Process:**
• Step 1: Personal data input
• Step 2: Admin verification
• Step 3: Course date confirmation

**Coming Soon!** 🎯
    """
    await bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')

async def send_error_message(user_id):
    """Send error message"""
    message = """
❌ **System Error**

Sorry, there was an error processing your request.

Please try again later.
    """
    await bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')

async def setup_webhook():
    """Set up Telegram webhook"""
    try:
        webhook_url = WEBHOOK_URL  # Already includes /webhook
        await bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
        return True
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        return False

if __name__ == '__main__':
    # Test all connections on startup
    print("🚀 Starting NewRest Bot 2025...")
    print(f"📱 Bot Token: {'✅ Set' if BOT_TOKEN else '❌ Missing'}")
    print(f"📊 Sheets ID: {'✅ Set' if GOOGLE_SHEETS_ID else '❌ Missing'}")
    print(f"🔗 Webhook URL: {WEBHOOK_URL}")
    
    # Set up webhook
    if BOT_TOKEN and WEBHOOK_URL:
        asyncio.run(setup_webhook())
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
