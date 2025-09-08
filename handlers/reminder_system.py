#!/usr/bin/env python3
"""
Reminder System Handler
Manages pre-course and day-course reminders with attendance confirmation
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
import pytz
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from services.google_sheets import init_google_sheets

logger = logging.getLogger(__name__)

class ReminderSystem:
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.admin_group_id = os.getenv('ADMIN_GROUP_ID')
        
    async def send_pre_course_reminder(self, user_id, course_date, language='gr'):
        """Send reminder at 10am the day before the course"""
        try:
            bot = Bot(token=self.bot_token)
            
            if language == 'en':
                message = """🔔 Reminder: Your training is tomorrow from 9:50-15:00.

Will you attend?"""
            else:  # Greek
                message = """🔔 Υπενθύμιση: Η εκπαίδευσή σας είναι αύριο στις 9:50-15:00.

Θα παρευρεθείτε;"""
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Ναι / Yes", callback_data=f"reminder_yes_{user_id}"),
                    InlineKeyboardButton("❌ Όχι / No", callback_data=f"reminder_no_{user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            # Mark first reminder as sent
            await self._mark_reminder_sent(user_id, 'FIRST_REMINDER_SENT')
            
            logger.info(f"Pre-course reminder sent to user {user_id} for course on {course_date}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending pre-course reminder: {e}")
            return False
    
    async def handle_attendance_confirmation(self, user_id, response, language='gr'):
        """Handle user's attendance confirmation (yes/no)"""
        try:
            bot = Bot(token=self.bot_token)
            
            if response == 'yes':
                # User will attend
                await self._handle_attendance_yes(user_id, language)
            else:
                # User won't attend - ask for reschedule or not interested
                await self._handle_attendance_no(user_id, language)
                
        except Exception as e:
            logger.error(f"Error handling attendance confirmation: {e}")
            return False
    
    async def _handle_attendance_yes(self, user_id, language):
        """Handle when user confirms attendance"""
        try:
            bot = Bot(token=self.bot_token)
            
            if language == 'en':
                message = """✅ Great! See you tomorrow at 9:50-15:00.

We look forward to meeting you!"""
            else:  # Greek
                message = """✅ Τέλεια! Θα σας δούμε αύριο στις 9:50-15:00.

Ανυπομονούμε να σας γνωρίσουμε!"""
            
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
            # Update WORKERS sheet status
            await self._update_worker_status(user_id, 'APPROVED_COURSE_DATE_SET')
            
            # Mark first reminder response
            await self._mark_reminder_response(user_id, 'YES')
            
            # Notify admin group
            await self._notify_admin_attendance(user_id, True, language)
            
            logger.info(f"User {user_id} confirmed attendance")
            return True
            
        except Exception as e:
            logger.error(f"Error handling attendance yes: {e}")
            return False
    
    async def _handle_attendance_no(self, user_id, language):
        """Handle when user says they won't attend"""
        try:
            bot = Bot(token=self.bot_token)
            
            if language == 'en':
                message = """❌ We understand you can't attend tomorrow.

What would you like to do?"""
            else:  # Greek
                message = """❌ Καταλαβαίνουμε ότι δεν μπορείτε να παρευρεθείτε αύριο.

Τι θα θέλατε να κάνετε;"""
            
            keyboard = [
                [
                    InlineKeyboardButton("📅 Επαναπρογραμματισμός / Reschedule", callback_data=f"reminder_reschedule_{user_id}"),
                    InlineKeyboardButton("👋 Δεν ενδιαφέρομαι πλέον / Not interested", callback_data=f"reminder_not_interested_{user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            logger.info(f"User {user_id} declined attendance, asking for next step")
            return True
            
        except Exception as e:
            logger.error(f"Error handling attendance no: {e}")
            return False
    
    async def handle_reschedule_request(self, user_id, language='gr'):
        """Handle reschedule request"""
        try:
            bot = Bot(token=self.bot_token)
            
            if language == 'en':
                message = """📅 We will notify you about a new date soon.

Thank you for your patience!"""
            else:  # Greek
                message = """📅 Θα σας ενημερώσουμε για νέα ημερομηνία σύντομα.

Σας ευχαριστούμε για την υπομονή!"""
            
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
            # Notify admin group
            await self._notify_admin_reschedule(user_id, language)
            
            logger.info(f"User {user_id} requested reschedule")
            return True
            
        except Exception as e:
            logger.error(f"Error handling reschedule request: {e}")
            return False
    
    async def handle_not_interested(self, user_id, language='gr'):
        """Handle when user is no longer interested"""
        try:
            bot = Bot(token=self.bot_token)
            
            if language == 'en':
                message = """👋 Thank you for your time and interest.

We wish you all the best in your future endeavors!"""
            else:  # Greek
                message = """👋 Σας ευχαριστούμε για τον χρόνο και το ενδιαφέρον.

Σας ευχόμαστε καλή επιτυχία στις μελλοντικές σας προσπάθειες!"""
            
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
            # Mark first reminder response
            await self._mark_reminder_response(user_id, 'NO')
            
            # Notify admin group
            await self._notify_admin_not_interested(user_id, language)
            
            # Update WORKERS sheet status
            await self._update_worker_status(user_id, 'REJECTED')
            
            logger.info(f"User {user_id} is no longer interested")
            return True
            
        except Exception as e:
            logger.error(f"Error handling not interested: {e}")
            return False
    
    async def _update_worker_status(self, user_id, new_status):
        """Update worker status in WORKERS sheet"""
        try:
            sheets_data = init_google_sheets()
            if sheets_data['status'] != 'success':
                return False
            
            workers_sheet = sheets_data['sheets']['workers']
            
            # Find user row
            id_column = workers_sheet.col_values(2)  # Column B - ID
            user_row = None
            
            for i, user_id_in_sheet in enumerate(id_column[1:], start=2):  # Skip header row
                if str(user_id) == str(user_id_in_sheet):
                    user_row = i
                    break
            
            if user_row:
                workers_sheet.update_cell(user_row, 3, new_status)  # Column C - STATUS
                logger.info(f"Updated worker status for user {user_id} to {new_status}")
                return True
            else:
                logger.error(f"User {user_id} not found in WORKERS sheet")
                return False
                
        except Exception as e:
            logger.error(f"Error updating worker status: {e}")
            return False
    
    async def _notify_admin_attendance(self, user_id, will_attend, language='gr'):
        """Notify admin group about attendance confirmation"""
        try:
            bot = Bot(token=self.bot_token)
            
            if will_attend:
                if language == 'en':
                    message = f"✅ **Attendance Confirmed**\n\nUser **{user_id}** will attend tomorrow's training."
                else:  # Greek
                    message = f"✅ **Επιβεβαίωση Παρακολούθησης**\n\nΟ χρήστης **{user_id}** θα παρευρεθεί στην εκπαίδευση αύριο."
            else:
                if language == 'en':
                    message = f"❌ **Attendance Declined**\n\nUser **{user_id}** will not attend tomorrow's training."
                else:  # Greek
                    message = f"❌ **Απόρριψη Παρακολούθησης**\n\nΟ χρήστης **{user_id}** δεν θα παρευρεθεί στην εκπαίδευση αύριο."
            
            await bot.send_message(
                chat_id=self.admin_group_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"Admin notified about attendance for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error notifying admin about attendance: {e}")
            return False
    
    async def _notify_admin_reschedule(self, user_id, language='gr'):
        """Notify admin group about reschedule request"""
        try:
            bot = Bot(token=self.bot_token)
            
            if language == 'en':
                message = f"📅 **Reschedule Request**\n\nUser **{user_id}** requested a new training date."
            else:  # Greek
                message = f"📅 **Αίτημα Επαναπρογραμματισμού**\n\nΟ χρήστης **{user_id}** ζήτησε νέα ημερομηνία εκπαίδευσης."
            
            await bot.send_message(
                chat_id=self.admin_group_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"Admin notified about reschedule request for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error notifying admin about reschedule: {e}")
            return False
    
    async def _notify_admin_not_interested(self, user_id, language='gr'):
        """Notify admin group about not interested response"""
        try:
            bot = Bot(token=self.bot_token)
            
            if language == 'en':
                message = f"👋 **No Longer Interested**\n\nUser **{user_id}** is no longer interested in the position."
            else:  # Greek
                message = f"👋 **Δεν Ενδιαφέρεται Πλέον**\n\nΟ χρήστης **{user_id}** δεν ενδιαφέρεται πλέον για τη θέση."
            
            await bot.send_message(
                chat_id=self.admin_group_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"Admin notified about not interested for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error notifying admin about not interested: {e}")
            return False
    
    async def get_users_for_reminder(self, target_date):
        """Get users who need reminders for a specific date"""
        try:
            sheets_data = init_google_sheets()
            if sheets_data['status'] != 'success':
                return []
            
            registration_sheet = sheets_data['sheets']['registration']
            workers_sheet = sheets_data['sheets']['workers']
            
            # Get specific columns to avoid duplicate header issues
            # Read only the columns we need from each sheet
            # Read specific columns from registration sheet
            user_id_col = registration_sheet.col_values(2)  # Column B (user id)
            pre_course_reminder_col = registration_sheet.col_values(19)  # Column S (PRE_COURSE_REMINDER)
            first_reminder_sent_col = registration_sheet.col_values(21)  # Column U (FIRST_REMINDER_SENT)
            course_date_col = registration_sheet.col_values(18)  # Column R (COURSE_DATE)
            language_col = registration_sheet.col_values(1)  # Column A (LANGUAGE)
            
            # Read only specific columns from workers sheet to avoid conflicts
            workers_id_col = workers_sheet.col_values(2)  # Column B (ID)
            workers_status_col = workers_sheet.col_values(3)  # Column C (STATUS)
            
            # Create a mapping of user_id to status
            user_status_map = {}
            for i in range(1, len(workers_id_col)):  # Skip header row
                if i < len(workers_status_col):
                    user_id = workers_id_col[i]
                    status = workers_status_col[i]
                    if user_id and status:
                        user_status_map[user_id] = status
            
            # Find users with PRE_COURSE_REMINDER matching target_date
            # AND who haven't been sent a reminder yet
            # AND who have valid status (not REJECTED)
            users_to_remind = []
            for i in range(1, len(user_id_col)):  # Skip header row
                if (i < len(pre_course_reminder_col) and 
                    i < len(first_reminder_sent_col) and
                    i < len(course_date_col) and
                    i < len(language_col)):
                    
                    user_id = user_id_col[i]
                    pre_course_reminder = pre_course_reminder_col[i]
                    first_reminder_sent = first_reminder_sent_col[i]
                    course_date = course_date_col[i]
                    language = language_col[i]
                    user_status = user_status_map.get(user_id)
                    
                    if (pre_course_reminder == target_date and
                        not first_reminder_sent and
                        user_status not in ['REJECTED', 'CANCELLED']):
                        users_to_remind.append({
                            'user_id': user_id,
                            'course_date': course_date,
                            'language': language or 'gr'
                        })
            
            logger.info(f"Found {len(users_to_remind)} users to remind for {target_date}")
            logger.info(f"Looking for users with PRE_COURSE_REMINDER = {target_date}")
            
            # Debug: Log what we found in the data
            logger.info(f"Total users in registration: {len(user_id_col) - 1}")
            for i in range(1, min(6, len(user_id_col))):  # Log first 5 users for debugging
                if i < len(pre_course_reminder_col):
                    logger.info(f"User {i}: ID={user_id_col[i]}, PRE_COURSE_REMINDER={pre_course_reminder_col[i]}, FIRST_REMINDER_SENT={first_reminder_sent_col[i] if i < len(first_reminder_sent_col) else 'N/A'}")
            
            return users_to_remind
            
        except Exception as e:
            logger.error(f"Error getting users for reminder: {e}")
            return []
    
    async def get_users_for_day_reminder(self, target_date):
        """Get users who need day course reminders for a specific date"""
        try:
            sheets_data = init_google_sheets()
            if sheets_data['status'] != 'success':
                return []
            
            registration_sheet = sheets_data['sheets']['registration']
            workers_sheet = sheets_data['sheets']['workers']
            
            # Get specific columns to avoid duplicate header issues
            # Read only the columns we need from each sheet
            # Read specific columns from registration sheet
            user_id_col = registration_sheet.col_values(2)  # Column B (user id)
            day_course_reminder_col = registration_sheet.col_values(20)  # Column T (DAY_COURSE_REMINDER)
            course_date_col = registration_sheet.col_values(18)  # Column R (COURSE_DATE)
            first_reminder_response_col = registration_sheet.col_values(23)  # Column W (FIRST_REMINDER_RESPONSE)
            second_reminder_sent_col = registration_sheet.col_values(22)  # Column V (SECOND_REMINDER_SENT)
            language_col = registration_sheet.col_values(1)  # Column A (LANGUAGE)
            
            # Read only specific columns from workers sheet to avoid conflicts
            workers_id_col = workers_sheet.col_values(2)  # Column B (ID)
            workers_status_col = workers_sheet.col_values(3)  # Column C (STATUS)
            
            # Create a mapping of user_id to status
            user_status_map = {}
            for i in range(1, len(workers_id_col)):  # Skip header row
                if i < len(workers_status_col):
                    user_id = workers_id_col[i]
                    status = workers_status_col[i]
                    if user_id and status:
                        user_status_map[user_id] = status
            
            # Find users with DAY_COURSE_REMINDER matching target_date 
            # AND status APPROVED_COURSE_DATE_SET
            # AND who responded YES to first reminder
            # AND who haven't been sent second reminder yet
            users_to_remind = []
            for i in range(1, len(user_id_col)):  # Skip header row
                if (i < len(day_course_reminder_col) and 
                    i < len(course_date_col) and
                    i < len(first_reminder_response_col) and
                    i < len(second_reminder_sent_col) and
                    i < len(language_col)):
                    
                    user_id = user_id_col[i]
                    day_course_reminder = day_course_reminder_col[i]
                    course_date = course_date_col[i]
                    first_reminder_response = first_reminder_response_col[i]
                    second_reminder_sent = second_reminder_sent_col[i]
                    language = language_col[i]
                    user_status = user_status_map.get(user_id)
                    
                    if (day_course_reminder == target_date and 
                        user_status == 'APPROVED_COURSE_DATE_SET' and
                        first_reminder_response == 'YES' and
                        not second_reminder_sent):
                        users_to_remind.append({
                            'user_id': user_id,
                            'course_date': course_date,
                            'language': language or 'gr'
                        })
            
            logger.info(f"Found {len(users_to_remind)} users for day course reminder on {target_date}")
            return users_to_remind
            
        except Exception as e:
            logger.error(f"Error getting users for day reminder: {e}")
            return []
    
    async def send_day_course_reminder(self, user_id, course_date, language='gr'):
        """Send day course reminder with check-in button"""
        try:
            bot = Bot(token=self.bot_token)
            
            if language == 'en':
                message = """🎯 Good morning! Today is your training day.

Please check in when you arrive at 9:50-15:00."""
            else:  # Greek
                message = """🎯 Καλημέρα! Σήμερα είναι η ημέρα της εκπαίδευσής σας.

Παρακαλούμε κάντε check-in όταν φτάσετε στις 9:50-15:00."""
            
            keyboard = [
                [InlineKeyboardButton("✅ Check-In / Check-In", callback_data=f"day_checkin_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            # Mark reminder as sent in Google Sheets
            await self._mark_reminder_sent(user_id, 'SECOND_REMINDER_SENT')
            
            logger.info(f"Day course reminder sent to user {user_id} for course on {course_date}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending day course reminder: {e}")
            return False
    
    async def handle_day_checkin(self, user_id, language='gr'):
        """Handle day course check-in with location validation"""
        try:
            bot = Bot(token=self.bot_token)
            
            # Add location validation
            from services.location_service import LocationService
            location_service = LocationService()
            
            # Check if user has already tried location validation
            retry_count = await self._get_retry_count(user_id)
            
            if retry_count < 2:  # Allow 2 retries
                if not await location_service.validate_location(user_id):
                    # Location validation failed - send retry message
                    await self._send_location_retry_message(user_id, language, retry_count + 1)
                    await self._increment_retry_count(user_id)
                    return False
            
            # If retry count exceeded, send contact message
            if retry_count >= 2:
                await self._send_contact_message(user_id, language)
                return False
            
            # Location validation passed - proceed with check-in
            if language == 'en':
                message = """✅ Check-in successful!

Welcome to your training day. You are now in the working console.

You can check in/out as needed throughout the day."""
            else:  # Greek
                message = """✅ Check-in επιτυχής!

Καλώς ήρθατε στην ημέρα εκπαίδευσής σας. Είστε τώρα στην κονσόλα εργασίας.

Μπορείτε να κάνετε check-in/out όποτε χρειάζεται κατά τη διάρκεια της ημέρας."""
            
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
            # Save check-in data to monthly sheet
            await self._save_checkin_data(user_id)
            
            # Update status to WORKING
            await self._update_worker_status(user_id, 'WORKING')
            
            # Send working console
            await self._send_working_console(user_id)
            
            # Reset retry count on successful check-in
            await self._reset_retry_count(user_id)
            
            logger.info(f"Day check-in completed for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error handling day check-in: {e}")
            return False
    
    async def _save_checkin_data(self, user_id):
        """Save check-in data to monthly sheet"""
        try:
            from services.google_sheets import get_monthly_sheet
            from datetime import datetime
            import pytz
            
            # Get current date and time
            greece_tz = pytz.timezone('Europe/Athens')
            now = datetime.now(greece_tz)
            current_date = now.strftime('%Y-%m-%d')
            current_time = now.strftime('%H:%M')
            
            # Get monthly sheet
            monthly_sheet = get_monthly_sheet()
            if not monthly_sheet:
                logger.error("Could not get monthly sheet for check-in data")
                return False
            
            # Get user data from WORKERS sheet
            sheets_data = init_google_sheets()
            if sheets_data['status'] != 'success':
                return False
            
            workers_sheet = sheets_data['sheets']['workers']
            
            # Read only specific columns to avoid duplicate header issues
            workers_id_col = workers_sheet.col_values(2)  # Column B (ID)
            workers_name_col = workers_sheet.col_values(1)  # Column A (NAME)
            
            # Find user name
            user_name = "Unknown"
            for i in range(1, len(workers_id_col)):  # Skip header row
                if i < len(workers_name_col):
                    if str(workers_id_col[i]) == str(user_id):
                        user_name = workers_name_col[i] or 'Unknown'
                        break
            
            # Find the correct date column
            all_values = monthly_sheet.get_all_values()
            if not all_values:
                logger.error("Monthly sheet is empty")
                return False
            
            header_row = all_values[0]
            date_column = None
            
            for i, header in enumerate(header_row):
                if header == current_date:
                    date_column = i + 1  # 1-based indexing
                    break
            
            if not date_column:
                logger.error(f"Date column not found for {current_date}")
                return False
            
            # Find user row or add new user
            user_row = None
            for i, row in enumerate(all_values[1:], start=2):  # Skip header
                if len(row) > 0 and row[0] == user_name:
                    user_row = i
                    break
            
            if not user_row:
                # Add new user row
                monthly_sheet.append_row([user_name] + [''] * (len(header_row) - 1))
                user_row = len(all_values) + 1
            
            # Update check-in time
            monthly_sheet.update_cell(user_row, date_column, current_time)
            
            logger.info(f"Check-in data saved for user {user_id} at {current_time}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving check-in data: {e}")
            return False
    
    async def _send_working_console(self, user_id):
        """Send working console to user"""
        try:
            from handlers.working_console import WorkingConsole
            
            working_console = WorkingConsole(user_id)
            await working_console.show_working_console()
            
            logger.info(f"Working console sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending working console: {e}")
            return False
    
    async def send_daily_reminders(self):
        """Send reminders for today's courses (run this at 10am daily)"""
        try:
            # Calculate today's date
            greece_tz = pytz.timezone('Europe/Athens')
            now = datetime.now(greece_tz)
            today = now.strftime('%Y-%m-%d')
            
            # Get users for today's courses (PRE_COURSE_REMINDER = today)
            users = await self.get_users_for_reminder(today)
            
            if not users:
                logger.info(f"No users found for reminders on {today}")
                return False
            
            # Send reminders to each user
            for user in users:
                await self.send_pre_course_reminder(
                    user['user_id'], 
                    user['course_date'], 
                    user['language']
                )
                # Small delay between messages to avoid rate limiting
                await asyncio.sleep(1)
            
            logger.info(f"Sent reminders to {len(users)} users for {today}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending daily reminders: {e}")
            return False
    
    async def send_day_course_reminders(self):
        """Send day course reminders at 9:50am for approved users"""
        try:
            # Calculate today's date
            greece_tz = pytz.timezone('Europe/Athens')
            now = datetime.now(greece_tz)
            today = now.strftime('%Y-%m-%d')
            
            # Get users for today's day course reminders
            users = await self.get_users_for_day_reminder(today)
            
            if not users:
                logger.info(f"No users found for day course reminders on {today}")
                return False
            
            # Send reminders to each user in order (1 read → 1 send)
            for user in users:
                await self.send_day_course_reminder(
                    user['user_id'], 
                    user['course_date'], 
                    user['language']
                )
                # Small delay between messages to avoid rate limiting
                await asyncio.sleep(1)
            
            logger.info(f"Sent day course reminders to {len(users)} users for {today}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending day course reminders: {e}")
            return False
    
    async def _mark_reminder_sent(self, user_id, reminder_type):
        """Mark reminder as sent in Google Sheets"""
        try:
            sheets_data = init_google_sheets()
            if sheets_data['status'] != 'success':
                return False
            
            registration_sheet = sheets_data['sheets']['registration']
            
            # Read only specific columns to avoid duplicate header issues
            user_id_col = registration_sheet.col_values(2)  # Column B (user id)
            
            # Find user row
            user_row = None
            for i in range(1, len(user_id_col)):  # Skip header row
                if str(user_id_col[i]) == str(user_id):
                    user_row = i + 1  # +1 because col_values is 0-indexed but sheet rows are 1-indexed
                    break
            
            if user_row:
                # Mark reminder as sent
                if reminder_type == 'FIRST_REMINDER_SENT':
                    registration_sheet.update_cell(user_row, 21, 'SENT')  # Column U
                elif reminder_type == 'SECOND_REMINDER_SENT':
                    registration_sheet.update_cell(user_row, 22, 'SENT')  # Column V
                
                logger.info(f"Marked {reminder_type} as sent for user {user_id}")
                return True
            else:
                logger.error(f"User {user_id} not found in REGISTRATION sheet")
                return False
                
        except Exception as e:
            logger.error(f"Error marking reminder as sent: {e}")
            return False
    
    async def _mark_reminder_response(self, user_id, response):
        """Mark reminder response in Google Sheets"""
        try:
            sheets_data = init_google_sheets()
            if sheets_data['status'] != 'success':
                return False
            
            registration_sheet = sheets_data['sheets']['registration']
            
            # Read only specific columns to avoid duplicate header issues
            user_id_col = registration_sheet.col_values(2)  # Column B (user id)
            
            # Find user row
            user_row = None
            for i in range(1, len(user_id_col)):  # Skip header row
                if str(user_id_col[i]) == str(user_id):
                    user_row = i + 1  # +1 because col_values is 0-indexed but sheet rows are 1-indexed
                    break
            
            if user_row:
                # Mark reminder response (Column W for FIRST_REMINDER_RESPONSE)
                registration_sheet.update_cell(user_row, 23, response)  # Column W
                
                logger.info(f"Marked first reminder response as {response} for user {user_id}")
                return True
            else:
                logger.error(f"User {user_id} not found in REGISTRATION sheet")
                return False
                
        except Exception as e:
            logger.error(f"Error marking reminder response: {e}")
            return False
    
    async def _get_retry_count(self, user_id):
        """Get retry count for user"""
        try:
            sheets_data = init_google_sheets()
            if sheets_data['status'] != 'success':
                return 0
            
            registration_sheet = sheets_data['sheets']['registration']
            
            # Read only specific columns to avoid duplicate header issues
            user_id_col = registration_sheet.col_values(2)  # Column B (user id)
            retry_count_col = registration_sheet.col_values(24)  # Column X (RETRY_COUNT)
            
            for i in range(1, len(user_id_col)):  # Skip header row
                if i < len(retry_count_col):
                    if str(user_id_col[i]) == str(user_id):
                        return int(retry_count_col[i] or 0)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error getting retry count: {e}")
            return 0
    
    async def _increment_retry_count(self, user_id):
        """Increment retry count for user"""
        try:
            sheets_data = init_google_sheets()
            if sheets_data['status'] != 'success':
                return False
            
            registration_sheet = sheets_data['sheets']['registration']
            
            # Read only specific columns to avoid duplicate header issues
            user_id_col = registration_sheet.col_values(2)  # Column B (user id)
            retry_count_col = registration_sheet.col_values(24)  # Column X (RETRY_COUNT)
            
            for i in range(1, len(user_id_col)):  # Skip header row
                if i < len(retry_count_col):
                    if str(user_id_col[i]) == str(user_id):
                        current_count = int(retry_count_col[i] or 0)
                        registration_sheet.update_cell(i + 1, 24, current_count + 1)  # Column X (+1 for 1-indexed)
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error incrementing retry count: {e}")
            return False
    
    async def _reset_retry_count(self, user_id):
        """Reset retry count for user"""
        try:
            sheets_data = init_google_sheets()
            if sheets_data['status'] != 'success':
                return False
            
            registration_sheet = sheets_data['sheets']['registration']
            
            # Read only specific columns to avoid duplicate header issues
            user_id_col = registration_sheet.col_values(2)  # Column B (user id)
            
            for i in range(1, len(user_id_col)):  # Skip header row
                if str(user_id_col[i]) == str(user_id):
                    registration_sheet.update_cell(i + 1, 24, 0)  # Column X (+1 for 1-indexed)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error resetting retry count: {e}")
            return False
    
    async def _send_location_retry_message(self, user_id, language, retry_count):
        """Send location retry message"""
        try:
            bot = Bot(token=self.bot_token)
            
            if language == 'en':
                message = f"""❌ Location validation failed (Attempt {retry_count}/2)

Please make sure you are at the work location and try again."""
            else:  # Greek
                message = f"""❌ Η επαλήθευση τοποθεσίας απέτυχε (Προσπάθεια {retry_count}/2)

Παρακαλούμε βεβαιωθείτε ότι βρίσκεστε στην τοποθεσία εργασίας και δοκιμάστε ξανά."""
            
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again / Δοκιμάστε Ξανά", callback_data=f"day_checkin_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            logger.info(f"Location retry message sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending location retry message: {e}")
            return False
    
    async def _send_contact_message(self, user_id, language):
        """Send contact message for help"""
        try:
            bot = Bot(token=self.bot_token)
            
            if language == 'en':
                message = """❌ Location validation failed multiple times.

Please contact support for assistance."""
            else:  # Greek
                message = """❌ Η επαλήθευση τοποθεσίας απέτυχε πολλές φορές.

Παρακαλούμε επικοινωνήστε με την υποστήριξη για βοήθεια."""
            
            keyboard = [
                [InlineKeyboardButton("📞 Contact Support / Επικοινωνία", callback_data=f"contact_support_{user_id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            logger.info(f"Contact message sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending contact message: {e}")
            return False
