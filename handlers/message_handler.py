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
        
        # Handle admin test commands first
        if text.startswith('/test_reminder'):
            await handle_reminder_test_command(text, user_id)
            return
        
        # Handle custom date input from admin
        # Check if message is from admin group and if any admin evaluation is waiting for custom date
        admin_group_id = os.getenv('ADMIN_GROUP_ID')
        if str(message.get('chat', {}).get('id')) == admin_group_id:
            # Message is from admin group, check if any evaluation is waiting for custom date
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
            # User in transition - show waiting message
            await send_waiting_message(user_id, user_status)
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

async def handle_reminder_test_command(text, user_id):
    """Handle admin reminder test commands"""
    try:
        from handlers.reminder_system import ReminderSystem
        from services.telegram_bot import send_message
        import os
        
        # Check if user is admin (you can modify this check as needed)
        admin_group_id = os.getenv('ADMIN_GROUP_ID')
        if str(user_id) != admin_group_id:
            await send_message(user_id, "❌ This command is only available for admins.")
            return
        
        reminder_system = ReminderSystem()
        
        if text == '/test_reminder_first':
            # Test first reminder (pre-course)
            await send_message(user_id, "🔄 Testing first reminder (pre-course)...")
            result = await reminder_system.send_daily_reminders()
            if result:
                await send_message(user_id, "✅ First reminder test completed successfully!")
            else:
                await send_message(user_id, "❌ First reminder test failed. Check logs.")
                
        elif text == '/test_reminder_second':
            # Test second reminder (day course)
            await send_message(user_id, "🔄 Testing second reminder (day course)...")
            result = await reminder_system.send_day_course_reminders()
            if result:
                await send_message(user_id, "✅ Second reminder test completed successfully!")
            else:
                await send_message(user_id, "❌ Second reminder test failed. Check logs.")
                
        elif text == '/test_reminder_both':
            # Test both reminders
            await send_message(user_id, "🔄 Testing both reminders...")
            
            # Test first reminder
            first_result = await reminder_system.send_daily_reminders()
            await send_message(user_id, f"First reminder: {'✅ Success' if first_result else '❌ Failed'}")
            
            # Test second reminder
            second_result = await reminder_system.send_day_course_reminders()
            await send_message(user_id, f"Second reminder: {'✅ Success' if second_result else '❌ Failed'}")
            
            if first_result and second_result:
                await send_message(user_id, "✅ Both reminder tests completed successfully!")
            else:
                await send_message(user_id, "⚠️ Some reminder tests failed. Check logs.")
                
        elif text == '/test_reminder_status':
            # Check reminder status
            await send_message(user_id, "🔄 Checking reminder status...")
            
            from datetime import datetime
            import pytz
            
            greece_tz = pytz.timezone('Europe/Athens')
            now = datetime.now(greece_tz)
            today = now.strftime('%Y-%m-%d')
            
            # Get users for first reminder
            first_users = await reminder_system.get_users_for_reminder(today)
            second_users = await reminder_system.get_users_for_day_reminder(today)
            
            status_text = f"""📊 **Reminder Status for {today}**

**First Reminder (Pre-Course):**
- Eligible users: {len(first_users)}
- Users: {[user['user_id'] for user in first_users]}

**Second Reminder (Day Course):**
- Eligible users: {len(second_users)}
- Users: {[user['user_id'] for user in second_users]}

**Current Time:** {now.strftime('%H:%M:%S')} (Greece)"""
            
            await send_message(user_id, status_text)
            
        elif text == '/test_reminder_help':
            # Show help
            help_text = """🔧 **Reminder Test Commands**

`/test_reminder_first` - Test first reminder (pre-course)
`/test_reminder_second` - Test second reminder (day course)  
`/test_reminder_both` - Test both reminders
`/test_reminder_status` - Check reminder status for today
`/test_reminder_help` - Show this help

**Note**: These commands will send actual reminders to users who are eligible today."""
            
            await send_message(user_id, help_text)
            
        else:
            await send_message(user_id, "❌ Unknown test command. Use `/test_reminder_help` for available commands.")
            
    except Exception as e:
        logger.error(f"Error handling reminder test command: {e}")
        await send_message(user_id, f"❌ Error: {str(e)}")

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
