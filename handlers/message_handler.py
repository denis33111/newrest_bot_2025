#!/usr/bin/env python3
"""
Message Handler
Handles incoming Telegram messages and routes to appropriate flows
"""

import logging
from services.google_sheets import check_user_status
from services.telegram_bot import send_working_console, send_error_message
from handlers.registration_flow import RegistrationFlow
from handlers.working_console import WorkingConsole
from handlers.admin_evaluation import AdminEvaluation

logger = logging.getLogger(__name__)

# Store active registration flows
active_registrations = {}

# Store candidate data for admin evaluation
candidate_data_storage = {}

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
            # Handle working console messages
            await handle_working_message(user_id, message)
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

async def handle_working_message(user_id, message):
    """Handle messages from working users"""
    try:
        working_console = WorkingConsole(user_id)
        
        # Check if it's a location message
        if message.get('location'):
            await working_console.handle_location(message['location'])
            return
        
        # Check if it's a text message with working console commands
        text = message.get('text', '')
        
        if 'Check In' in text or 'Check Out' in text:
            await working_console.handle_check_in_out(text)
        elif 'Contact' in text:
            await working_console.handle_contact()
        else:
            # Show working console for any other message
            await working_console.show_working_console()
            
    except Exception as e:
        logger.error(f"Error handling working message: {e}")
        await send_error_message(user_id)

async def handle_callback_query(callback_query):
    """Handle callback queries (button presses)"""
    try:
        # Handle both dict and Telegram object
        if isinstance(callback_query, dict):
            user_id = callback_query['from']['id']
            data = callback_query['data']
        else:
            user_id = callback_query.from_user.id
            data = callback_query.data
        
        # Handle admin evaluation callbacks
        if data.startswith('admin_eval_'):
            await handle_admin_evaluation_callback(data)
        
        # Handle registration callbacks
        elif user_id in active_registrations:
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
        
        # Answer the callback query (only if it's a Telegram object)
        if not isinstance(callback_query, dict):
            await callback_query.answer()
        
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")

async def handle_admin_evaluation_callback(data):
    """Handle admin evaluation callback queries"""
    try:
        parts = data.split('_')
        
        if len(parts) < 4:
            logger.error(f"Invalid admin evaluation callback: {data}")
            return
        
        action = parts[2]  # start, continue, reject, position, date, custom
        user_id = parts[-1]  # Last part is always user_id
        
        # Get candidate data from storage
        candidate_data = candidate_data_storage.get(user_id, {
            'user_id': user_id,
            'full_name': 'Unknown',
            'age': 'Unknown',
            'phone': 'Unknown',
            'email': 'Unknown',
            'transportation': 'Unknown',
            'bank': 'Unknown',
            'driving_license': 'Unknown'
        })
        
        admin_eval = AdminEvaluation(user_id, candidate_data)
        
        if action == 'start':
            await admin_eval.start_evaluation()
        elif action == 'continue':
            await admin_eval.ask_position()
        elif action == 'reject':
            await admin_eval.save_evaluation('', '', approved=False)
        elif action == 'position':
            position = parts[3]  # HL, Supervisor, EQ
            await admin_eval.ask_course_date(position)
        elif action == 'date':
            course_date = parts[3]  # Selected date
            position = admin_eval.selected_position or 'Unknown'  # Use stored position
            await admin_eval.save_evaluation(position, course_date, approved=True)
        elif action == 'custom':
            # Handle custom date input (would need additional implementation)
            logger.info(f"Custom date requested for user {user_id}")
        
        logger.info(f"Admin evaluation callback handled: {action} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling admin evaluation callback: {e}")
