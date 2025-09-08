#!/usr/bin/env python3
"""
NewRest Bot 2025 - Main Flask Application
"""

import os
import asyncio
import logging
from flask import Flask, jsonify, request, send_file
from telegram import Bot
from services.google_sheets import init_google_sheets
from services.telegram_bot import setup_webhook
from handlers.message_handler import handle_telegram_message, handle_callback_query
from scheduler import start_reminder_scheduler

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
def test_telegram():
    """Test Telegram bot connection"""
    try:
        if not bot:
            return jsonify({'status': 'error', 'message': 'Bot not initialized'})
        
        # Get bot info
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot_info = loop.run_until_complete(bot.get_me())
        
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
@app.route('/test/pdf', methods=['GET'])
def test_pdf():
    """Test PDF file availability"""
    try:
        filename = 'ΥΠ_ΔΗΛΩΣΗ_ΠΟΙΝΙΚΟΥ (2).pdf'
        file_path = os.path.join(os.getcwd(), filename)
        
        result = {
            'filename': filename,
            'file_path': file_path,
            'file_exists': os.path.exists(file_path),
            'current_directory': os.getcwd(),
            'all_pdf_files': [f for f in os.listdir(os.getcwd()) if f.endswith('.pdf')]
        }
        
        if os.path.exists(file_path):
            result['file_size'] = os.path.getsize(file_path)
            result['status'] = 'success'
        else:
            result['status'] = 'file_not_found'
            
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test/all', methods=['GET'])
def test_all():
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
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            bot_info = loop.run_until_complete(bot.get_me())
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
@app.route('/download/<path:filename>')
def download_file(filename):
    """Download files like PDFs"""
    try:
        file_path = os.path.join(os.getcwd(), filename)
        logger.info(f"Download request for: {filename}")
        logger.info(f"Looking for file at: {file_path}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"File exists: {os.path.exists(file_path)}")
        
        if os.path.exists(file_path):
            logger.info(f"File found, sending: {file_path}")
            return send_file(
                file_path, 
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
        else:
            logger.error(f"File not found: {file_path}")
            # List files in current directory for debugging
            files = os.listdir(os.getcwd())
            pdf_files = [f for f in files if f.endswith('.pdf')]
            logger.error(f"Available PDF files: {pdf_files}")
            return jsonify({'error': 'File not found', 'available_files': pdf_files}), 404
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {e}")
        return jsonify({'error': 'Download failed'}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Telegram webhook endpoint"""
    data = request.get_json()
    logger.info(f"Telegram webhook received: {data}")
    
    # Process Telegram update
    if data and 'message' in data:
        # Run async function in existing event loop or create new one
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(handle_telegram_message(data['message']))
        except Exception as e:
            logger.error(f"Error in event loop: {e}")
    
    # Process callback queries (button presses)
    elif data and 'callback_query' in data:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(handle_callback_query(data['callback_query']))
        except Exception as e:
            logger.error(f"Error in callback query event loop: {e}")
    
    return jsonify({'status': 'ok'})

async def start_background_tasks():
    """Start background tasks like reminder scheduler"""
    # Start reminder scheduler
    asyncio.create_task(start_reminder_scheduler())
    logger.info("Background tasks started")

if __name__ == '__main__':
    # Test all connections on startup
    print("🚀 Starting NewRest Bot 2025...")
    print(f"📱 Bot Token: {'✅ Set' if BOT_TOKEN else '❌ Missing'}")
    print(f"📊 Sheets ID: {'✅ Set' if GOOGLE_SHEETS_ID else '❌ Missing'}")
    print(f"🔗 Webhook URL: {WEBHOOK_URL}")
    
    # Set up webhook
    if BOT_TOKEN and WEBHOOK_URL:
        asyncio.run(setup_webhook())
    
    # Start background tasks
    asyncio.run(start_background_tasks())
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
