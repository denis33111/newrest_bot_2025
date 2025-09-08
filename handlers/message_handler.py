#!/usr/bin/env python3
"""
Message Handler
Handles incoming Telegram messages and routes to appropriate flows
"""

import logging
import os
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
        
        
        # Handle admin group commands first
        admin_group_id = os.getenv('ADMIN_GROUP_ID')
        if str(message.get('chat', {}).get('id')) == admin_group_id:
            # Handle admin simulation commands
            if text == '/simulate_reminders':
                await handle_simulate_reminders_command(message)
                return
            elif text == '/simulate_tomorrow':
                await handle_simulate_tomorrow_command(message)
                return
            elif text == '/simulate_today':
                await handle_simulate_today_command(message)
                return
            elif text == '/reminder_help':
                await handle_reminder_help_command(message)
                return
            
            # Handle custom date input from admin
            # Check if message is from admin group and if any admin evaluation is waiting for custom date
            for eval_user_id, admin_eval in admin_evaluation_instances.items():
                if admin_eval.waiting_for_custom_date:
                    await admin_eval.handle_custom_date_input(text, admin_evaluation_instances)
                    return
        
        # Also check if the specific user is waiting for custom date
        if user_id in admin_evaluation_instances:
            admin_eval = admin_evaluation_instances[user_id]
            if admin_eval.waiting_for_custom_date:
                await admin_eval.handle_custom_date_input(text, admin_evaluation_instances)
                return
        
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
        elif user_status == 'REJECTED':
            # User was rejected - show service unavailable
            await send_rejection_message(user_id)
        elif user_status in ['COURSE_DATE_SET', 'APPROVED_COURSE_DATE_SET']:
            # User in transition - check if they want to trigger reminder
            if text and text.lower() in ['reminder', 'test', 'start', 'begin', 'yes', 'go']:
                # User wants to trigger reminder flow - bypass waiting
                await trigger_reminder_flow(user_id, user_status)
            else:
                # Show waiting message with option to trigger reminder
                await send_waiting_message_with_reminder_option(user_id, user_status)
        elif user_status == 'OFF':
            # Disabled user - no response
            logger.info(f"Disabled user {user_id} - ignoring message")
            return
        elif user_status == 'ERROR':
            # Google Sheets error - show working console anyway
            logger.warning(f"Google Sheets error for user {user_id}, showing working console")
            await handle_working_message(user_id, message)
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
        
        if 'Check In' in text or 'Check Out' in text:
            await working_console.handle_check_in_out(text)
        elif 'Contact' in text or 'Επικοινωνία' in text:
            await working_console.handle_contact()
        elif 'Back to Menu' in text or 'Πίσω στο μενού' in text:
            # Handle back to menu button
            await working_console.show_working_console()
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
            # Handle custom date input
            logger.info(f"Custom date requested for user {user_id}")
            
            # Get admin evaluation instance
            if user_id not in admin_evaluation_instances:
                logger.error(f"Admin evaluation instance not found for user {user_id}")
                return
            
            admin_eval = admin_evaluation_instances[user_id]
            
            # Ask for custom date input
            await admin_eval.ask_custom_date()
        
        
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
        
        # Read only specific columns to avoid duplicate header issues
        user_id_col = registration_sheet.col_values(2)  # Column B (user id)
        course_date_col = registration_sheet.col_values(18)  # Column R (COURSE_DATE)
        
        # Find user's course details
        course_date = "Unknown"
        position = "Unknown"  # Position not available in registration sheet
        
        for i in range(1, len(user_id_col)):  # Skip header row
            if str(user_id_col[i]) == str(user_id):
                if i < len(course_date_col):
                    course_date = course_date_col[i] or 'Unknown'
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

async def handle_simulate_reminders_command(message):
    """Simulate the natural reminder process - both pre-day and day reminders"""
    try:
        from telegram import Bot
        from handlers.reminder_system import ReminderSystem
        from datetime import datetime, timedelta
        import pytz
        import os
        
        bot = Bot(token=os.getenv('BOT_TOKEN'))
        chat_id = message.get('chat', {}).get('id')
        
        await bot.send_message(chat_id=chat_id, text="🔄 Simulating natural reminder process...")
        
        # Get dates
        greece_tz = pytz.timezone('Europe/Athens')
        now = datetime.now(greece_tz)
        today = now.strftime('%Y-%m-%d')
        tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')
        
        reminder_system = ReminderSystem()
        
        # Simulate pre-day reminders (9:50 AM process)
        await bot.send_message(chat_id=chat_id, text=f"📅 **Pre-Day Reminders (9:50 AM Process)**")
        await bot.send_message(chat_id=chat_id, text=f"Scanning for users with PRE_COURSE_REMINDER = {tomorrow}")
        
        pre_users = await reminder_system.get_users_for_reminder(tomorrow)
        await bot.send_message(chat_id=chat_id, text=f"Found {len(pre_users)} eligible users for pre-day reminder")
        
        if pre_users:
            for user in pre_users:
                await reminder_system.send_pre_course_reminder(
                    user['user_id'], 
                    user['course_date'], 
                    user['language']
                )
            await bot.send_message(chat_id=chat_id, text=f"✅ Sent {len(pre_users)} pre-day reminders!")
        else:
            await bot.send_message(chat_id=chat_id, text="❌ No users found for pre-day reminder")
        
        # Simulate day-course reminders (10:00 AM process)
        await bot.send_message(chat_id=chat_id, text=f"📅 **Day-Course Reminders (10:00 AM Process)**")
        await bot.send_message(chat_id=chat_id, text=f"Scanning for users with COURSE_DATE = {today} who responded YES")
        
        day_users = await reminder_system.get_users_for_day_reminder(today)
        await bot.send_message(chat_id=chat_id, text=f"Found {len(day_users)} eligible users for day-course reminder")
        
        if day_users:
            for user in day_users:
                await reminder_system.send_day_course_reminder(
                    user['user_id'], 
                    user['course_date'], 
                    user['language']
                )
            await bot.send_message(chat_id=chat_id, text=f"✅ Sent {len(day_users)} day-course reminders!")
        else:
            await bot.send_message(chat_id=chat_id, text="❌ No users found for day-course reminder")
        
        await bot.send_message(chat_id=chat_id, text="🎯 **Simulation Complete!** Natural reminder process executed.")
        
    except Exception as e:
        logger.error(f"Error in simulate reminders command: {e}")
        await bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(e)}")

async def handle_simulate_tomorrow_command(message):
    """Simulate tomorrow's pre-day reminder process"""
    try:
        from telegram import Bot
        from handlers.reminder_system import ReminderSystem
        from datetime import datetime, timedelta
        import pytz
        import os
        
        bot = Bot(token=os.getenv('BOT_TOKEN'))
        chat_id = message.get('chat', {}).get('id')
        
        await bot.send_message(chat_id=chat_id, text="🔄 Simulating tomorrow's pre-day reminder process...")
        
        # Get tomorrow's date
        greece_tz = pytz.timezone('Europe/Athens')
        now = datetime.now(greece_tz)
        tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')
        
        reminder_system = ReminderSystem()
        
        await bot.send_message(chat_id=chat_id, text=f"📅 Scanning for users with PRE_COURSE_REMINDER = {tomorrow}")
        
        users = await reminder_system.get_users_for_reminder(tomorrow)
        await bot.send_message(chat_id=chat_id, text=f"Found {len(users)} eligible users for pre-day reminder")
        
        if users:
            for user in users:
                await reminder_system.send_pre_course_reminder(
                    user['user_id'], 
                    user['course_date'], 
                    user['language']
                )
            await bot.send_message(chat_id=chat_id, text=f"✅ Sent {len(users)} pre-day reminders for {tomorrow}!")
        else:
            await bot.send_message(chat_id=chat_id, text=f"❌ No users found for {tomorrow}")
        
    except Exception as e:
        logger.error(f"Error in simulate tomorrow command: {e}")
        await bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(e)}")

async def handle_simulate_today_command(message):
    """Simulate today's day-course reminder process"""
    try:
        from telegram import Bot
        from handlers.reminder_system import ReminderSystem
        from datetime import datetime
        import pytz
        import os
        
        bot = Bot(token=os.getenv('BOT_TOKEN'))
        chat_id = message.get('chat', {}).get('id')
        
        await bot.send_message(chat_id=chat_id, text="🔄 Simulating today's day-course reminder process...")
        
        # Get today's date
        greece_tz = pytz.timezone('Europe/Athens')
        now = datetime.now(greece_tz)
        today = now.strftime('%Y-%m-%d')
        
        reminder_system = ReminderSystem()
        
        await bot.send_message(chat_id=chat_id, text=f"📅 Scanning for users with COURSE_DATE = {today} who responded YES")
        
        users = await reminder_system.get_users_for_day_reminder(today)
        await bot.send_message(chat_id=chat_id, text=f"Found {len(users)} eligible users for day-course reminder")
        
        if users:
            for user in users:
                await reminder_system.send_day_course_reminder(
                    user['user_id'], 
                    user['course_date'], 
                    user['language']
                )
            await bot.send_message(chat_id=chat_id, text=f"✅ Sent {len(users)} day-course reminders for {today}!")
        else:
            await bot.send_message(chat_id=chat_id, text=f"❌ No users found for {today}")
        
    except Exception as e:
        logger.error(f"Error in simulate today command: {e}")
        await bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(e)}")

async def handle_reminder_help_command(message):
    """Show reminder simulation help"""
    try:
        from telegram import Bot
        import os
        
        bot = Bot(token=os.getenv('BOT_TOKEN'))
        chat_id = message.get('chat', {}).get('id')
        
        help_text = """🔧 **Reminder Simulation Commands**

`/simulate_reminders` - Simulate the complete natural reminder process
- Runs pre-day reminders (9:50 AM process) for tomorrow
- Runs day-course reminders (10:00 AM process) for today
- Shows exactly what the bot does naturally

`/simulate_tomorrow` - Simulate tomorrow's pre-day reminder process
- Scans for users with PRE_COURSE_REMINDER = tomorrow
- Sends pre-day reminder messages with Yes/No buttons

`/simulate_today` - Simulate today's day-course reminder process  
- Scans for users with COURSE_DATE = today who responded YES
- Sends day-course reminder messages with check-in buttons

`/reminder_help` - Show this help

**Note**: These commands trigger the actual reminder system and send real messages to users!"""
        
        await bot.send_message(chat_id=chat_id, text=help_text)
        
    except Exception as e:
        logger.error(f"Error in reminder help command: {e}")
        await bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(e)}")

async def trigger_reminder_flow(user_id, user_status):
    """Trigger reminder flow for testing - bypass waiting state"""
    try:
        from telegram import Bot
        from handlers.reminder_system import ReminderSystem
        from services.google_sheets import init_google_sheets
        from datetime import datetime, timedelta
        import pytz
        import os
        
        bot = Bot(token=os.getenv('BOT_TOKEN'))
        
        # Get user's course details
        sheets_data = init_google_sheets()
        if sheets_data['status'] != 'success':
            await send_unknown_status_message(user_id)
            return
        
        registration_sheet = sheets_data['sheets']['registration']
        
        # Read user's course date and pre-course reminder date
        user_id_col = registration_sheet.col_values(2)  # Column B (user id)
        course_date_col = registration_sheet.col_values(18)  # Column R (COURSE_DATE)
        pre_course_reminder_col = registration_sheet.col_values(19)  # Column S (PRE_COURSE_REMINDER)
        language_col = registration_sheet.col_values(4)  # Column D (LANGUAGE)
        
        # Find user's details
        course_date = None
        pre_course_reminder = None
        language = 'gr'
        
        for i in range(1, len(user_id_col)):  # Skip header row
            if str(user_id_col[i]) == str(user_id):
                if i < len(course_date_col):
                    course_date = course_date_col[i]
                if i < len(pre_course_reminder_col):
                    pre_course_reminder = pre_course_reminder_col[i]
                if i < len(language_col):
                    language = language_col[i] or 'gr'
                break
        
        if not course_date:
            await bot.send_message(chat_id=user_id, text="❌ Could not find your course details. Please contact support.")
            return
        
        # Check if user should get pre-day reminder or day-course reminder
        greece_tz = pytz.timezone('Europe/Athens')
        now = datetime.now(greece_tz)
        today = now.strftime('%Y-%m-%d')
        tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')
        
        reminder_system = ReminderSystem()
        
        # Check if user should get pre-day reminder (tomorrow's course)
        if pre_course_reminder == tomorrow:
            await bot.send_message(chat_id=user_id, text="🔄 Triggering pre-day reminder for testing...")
            await reminder_system.send_pre_course_reminder(user_id, course_date, language)
        # Check if user should get day-course reminder (today's course)
        elif course_date == today:
            await bot.send_message(chat_id=user_id, text="🔄 Triggering day-course reminder for testing...")
            await reminder_system.send_day_course_reminder(user_id, course_date, language)
        else:
            await bot.send_message(chat_id=user_id, text=f"⏰ Your course is on {course_date}. Reminders will be sent automatically at the right time.")
        
    except Exception as e:
        logger.error(f"Error triggering reminder flow: {e}")
        await send_error_message(user_id)

async def send_waiting_message_with_reminder_option(user_id, status):
    """Send waiting message with option to trigger reminder for testing"""
    try:
        from telegram import Bot
        from services.google_sheets import init_google_sheets
        import os
        
        bot = Bot(token=os.getenv('BOT_TOKEN'))
        
        # Get course details from REGISTRATION sheet
        sheets_data = init_google_sheets()
        if sheets_data['status'] != 'success':
            await send_unknown_status_message(user_id)
            return
        
        registration_sheet = sheets_data['sheets']['registration']
        
        # Read only specific columns to avoid duplicate header issues
        user_id_col = registration_sheet.col_values(2)  # Column B (user id)
        course_date_col = registration_sheet.col_values(18)  # Column R (COURSE_DATE)
        
        # Find user's course details
        course_date = "Unknown"
        position = "Unknown"  # Position not available in registration sheet
        
        for i in range(1, len(user_id_col)):  # Skip header row
            if str(user_id_col[i]) == str(user_id):
                if i < len(course_date_col):
                    course_date = course_date_col[i] or 'Unknown'
                break
        
        message = f"""⏳ We are waiting for you!

Your course is scheduled for:
📅 Date: {course_date}
🕘 Time: 9:50-15:00
💼 Position: {position}

Please wait for further instructions.

**For Testing:** Type 'reminder' to trigger reminder flow now."""
        
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='Markdown'
        )
        
        logger.info(f"Waiting message with reminder option sent to user {user_id} with status {status}")
        
    except Exception as e:
        logger.error(f"Error sending waiting message with reminder option: {e}")
