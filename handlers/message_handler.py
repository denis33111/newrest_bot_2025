#!/usr/bin/env python3
"""
Message Handler
Handles incoming Telegram messages and routes to appropriate flows
"""

import logging
from services.google_sheets import check_user_status
from services.telegram_bot import send_working_console, send_error_message
from handlers.registration_flow import RegistrationFlow

logger = logging.getLogger(__name__)

# Store active registration flows
active_registrations = {}

async def handle_telegram_message(message):
    """Handle incoming Telegram messages"""
    try:
        user_id = message['from']['id']
        username = message['from'].get('username', 'Unknown')
        text = message.get('text', '')
        
        logger.info(f"Processing message from user {user_id} ({username}): {text}")
        
        # Check if user is in active registration
        if user_id in active_registrations:
            await handle_registration_message(user_id, text)
            return
        
        # Check if user is in WORKERS sheet
        user_status = check_user_status(user_id)
        
        if user_status == 'WORKING':
            await send_working_console(user_id)
        elif user_status == 'NOT_FOUND':
            # Start registration flow
            registration = RegistrationFlow(user_id)
            active_registrations[user_id] = registration
            await registration.start_registration()
        elif user_status == 'OFF':
            # Disabled user - no response
            logger.info(f"Disabled user {user_id} - ignoring message")
            return
        else:
            await send_error_message(user_id)
            
    except Exception as e:
        logger.error(f"Error handling Telegram message: {e}")

async def handle_registration_message(user_id, text):
    """Handle message during registration flow"""
    try:
        registration = active_registrations.get(user_id)
        if not registration:
            return
        
        # Handle text input
        if registration.current_step == 2:
            await registration.handle_text_answer(text)
        elif registration.current_step == 3:
            await registration.handle_text_answer(text)
            
    except Exception as e:
        logger.error(f"Error handling registration message: {e}")

async def handle_callback_query(callback_query):
    """Handle callback queries (button presses)"""
    try:
        user_id = callback_query.from_user.id
        data = callback_query.data
        
        # Handle registration callbacks
        if user_id in active_registrations:
            registration = active_registrations[user_id]
            
            if data.startswith('lang_'):
                await registration.handle_language_selection(data)
            elif data.startswith('edit_'):
                await registration.handle_edit_request(data)
            elif data == 'confirm_registration':
                await registration.confirm_registration()
                # Remove from active registrations
                del active_registrations[user_id]
            else:
                # Handle selection answers
                await registration.handle_selection_answer(data)
        
        # Answer the callback query
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")
