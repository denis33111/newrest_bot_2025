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
from handlers.reminder_system import ReminderSystem

logger = logging.getLogger(__name__)

# Store active registration flows
active_registrations = {}

# Store candidate data for admin evaluation
candidate_data_storage = {}

# Store admin evaluation instances to maintain state
admin_evaluation_instances = {}

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
        logger.info(f"User {user_id} status: {user_status}")
        
        if user_status == 'WORKING':
            # Handle working console messages
            await handle_working_message(user_id, message)
        elif user_status == 'NOT_FOUND':
            # Start registration flow
            registration = RegistrationFlow(user_id)
            active_registrations[user_id] = registration
            await registration.start_registration()
        elif user_status == 'REJECTED':
            # User was rejected - show service unavailable
            await send_rejection_message(user_id)
        elif user_status in ['COURSE_DATE_SET', 'APPROVED_COURSE_DATE_SET']:
            # User in transition - show waiting message
            await send_waiting_message(user_id, user_status)
        elif user_status == 'OFF':
            # Disabled user - no response
            logger.info(f"Disabled user {user_id} - ignoring message")
            return
        else:
            await send_unknown_status_message(user_id)
            
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
        
        if 'Check In' in text or 'Check Out' in text or 'Εγγραφή' in text or 'Αποχώρηση' in text:
            await working_console.handle_check_in_out(text)
        elif 'Contact' in text or 'Επικοινωνία' in text:
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
        # Handle reminder callbacks
        elif data.startswith('reminder_'):
            await handle_reminder_callback(data)
        # Handle day check-in callbacks
        elif data.startswith('day_checkin_'):
            await handle_day_checkin_callback(data)
        
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
        
        logger.info(f"Retrieved candidate data for user {user_id}: {candidate_data}")
        
        # Get or create admin evaluation instance to maintain state
        if user_id not in admin_evaluation_instances:
            admin_evaluation_instances[user_id] = AdminEvaluation(user_id, candidate_data)
        
        admin_eval = admin_evaluation_instances[user_id]
        
        if action == 'start':
            await admin_eval.start_evaluation()
        elif action == 'continue':
            await admin_eval.ask_position()
        elif action == 'reject':
            await admin_eval.save_evaluation('', '', approved=False)
        elif action == 'position':
            position = parts[3]  # HL, Supervisor, EQ
            admin_eval.selected_position = position  # Store position in the instance
            await admin_eval.ask_course_date(position)
        elif action == 'date':
            course_date = parts[3]  # Selected date
            position = admin_eval.selected_position or 'Unknown'  # Use stored position
            await admin_eval.save_evaluation(position, course_date, approved=True)
            # Clean up after completion
            if user_id in admin_evaluation_instances:
                del admin_evaluation_instances[user_id]
        elif action == 'custom':
            # Handle custom date input (would need additional implementation)
            logger.info(f"Custom date requested for user {user_id}")
        
        logger.info(f"Admin evaluation callback handled: {action} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling admin evaluation callback: {e}")

async def handle_reminder_callback(data):
    """Handle reminder callback queries"""
    try:
        parts = data.split('_')
        
        if len(parts) < 3:
            logger.error(f"Invalid reminder callback: {data}")
            return
        
        action = parts[1]  # yes, no, reschedule, not_interested
        user_id = parts[2]
        
        reminder_system = ReminderSystem()
        
        # Get user language from candidate data
        candidate_data = candidate_data_storage.get(user_id, {})
        language = candidate_data.get('language', 'gr')
        
        if action == 'yes':
            await reminder_system.handle_attendance_confirmation(user_id, 'yes', language)
        elif action == 'no':
            await reminder_system.handle_attendance_confirmation(user_id, 'no', language)
        elif action == 'reschedule':
            await reminder_system.handle_reschedule_request(user_id, language)
        elif action == 'not_interested':
            await reminder_system.handle_not_interested(user_id, language)
        
        logger.info(f"Reminder callback handled: {action} for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling reminder callback: {e}")

async def handle_day_checkin_callback(data):
    """Handle day check-in callback queries"""
    try:
        parts = data.split('_')
        
        if len(parts) < 3:
            logger.error(f"Invalid day check-in callback: {data}")
            return
        
        user_id = parts[2]
        
        reminder_system = ReminderSystem()
        
        # Get user language from candidate data
        candidate_data = candidate_data_storage.get(user_id, {})
        language = candidate_data.get('language', 'gr')
        
        # Handle day check-in
        await reminder_system.handle_day_checkin(user_id, language)
        
        logger.info(f"Day check-in callback handled for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling day check-in callback: {e}")

async def send_rejection_message(user_id):
    """Send rejection message to user"""
    try:
        from services.telegram_bot import Bot
        import os
        
        bot = Bot(token=os.getenv('BOT_TOKEN'))
        
        message = """😔 Service Unavailable

Unfortunately, your application was not approved at this time.

Thank you for your interest."""
        
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown'
        )
        
        logger.info(f"Rejection message sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error sending rejection message: {e}")

async def send_waiting_message(user_id, status):
    """Send waiting message to user in transition"""
    try:
        from services.telegram_bot import Bot
        from services.google_sheets import init_google_sheets
        import os
        
        bot = Bot(token=os.getenv('BOT_TOKEN'))
        
        # Get course details from REGISTRATION sheet
        sheets_data = init_google_sheets()
        if sheets_data['status'] != 'success':
            await send_unknown_status_message(user_id)
            return
        
        registration_sheet = sheets_data['sheets']['registration']
        all_data = registration_sheet.get_all_records()
        
        # Find user's course details
        course_date = "Unknown"
        position = "Unknown"
        
        for row in all_data:
            if str(row.get('user id')) == str(user_id):
                course_date = row.get('COURSE_DATE', 'Unknown')
                position = row.get('POSITION', 'Unknown')
                break
        
        message = f"""⏳ We are waiting for you!

Your course is scheduled for:
📅 Date: {course_date}
🕘 Time: 9:50-15:00
💼 Position: {position}

Please wait for further instructions."""
        
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown'
        )
        
        logger.info(f"Waiting message sent to user {user_id} with status {status}")
        
    except Exception as e:
        logger.error(f"Error sending waiting message: {e}")

async def send_unknown_status_message(user_id):
    """Send unknown status message to user"""
    try:
        from services.telegram_bot import Bot
        import os
        
        bot = Bot(token=os.getenv('BOT_TOKEN'))
        
        message = """❓ Unknown Status

There seems to be an issue with your account status.

Please contact support for assistance."""
        
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown'
        )
        
        logger.info(f"Unknown status message sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"Error sending unknown status message: {e}")
