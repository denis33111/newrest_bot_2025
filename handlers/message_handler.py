#!/usr/bin/env python3
"""
Message Handler
Handles incoming Telegram messages and routes to appropriate flows
"""

import logging
from services.google_sheets import check_user_status
from services.telegram_bot import send_working_console, send_registration_flow, send_error_message

logger = logging.getLogger(__name__)

async def handle_telegram_message(message):
    """Handle incoming Telegram messages"""
    try:
        user_id = message['from']['id']
        username = message['from'].get('username', 'Unknown')
        text = message.get('text', '')
        
        logger.info(f"Processing message from user {user_id} ({username}): {text}")
        
        # Check if user is in WORKERS sheet
        user_status = check_user_status(user_id)
        
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
