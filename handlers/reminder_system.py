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
            
            # Get all data
            all_data = registration_sheet.get_all_records()
            
            # Find users with course date matching target_date
            users_to_remind = []
            for row in all_data:
                if row.get('COURSE_DATE') == target_date:
                    users_to_remind.append({
                        'user_id': row.get('user id'),
                        'course_date': row.get('COURSE_DATE'),
                        'language': row.get('LANGUAGE', 'gr')
                    })
            
            logger.info(f"Found {len(users_to_remind)} users to remind for {target_date}")
            return users_to_remind
            
        except Exception as e:
            logger.error(f"Error getting users for reminder: {e}")
            return []
    
    async def send_daily_reminders(self):
        """Send reminders for tomorrow's courses (run this at 10am daily)"""
        try:
            # Calculate tomorrow's date
            greece_tz = pytz.timezone('Europe/Athens')
            now = datetime.now(greece_tz)
            tomorrow = (now + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Get users for tomorrow's courses
            users = await self.get_users_for_reminder(tomorrow)
            
            # Send reminders to each user
            for user in users:
                await self.send_pre_course_reminder(
                    user['user_id'], 
                    user['course_date'], 
                    user['language']
                )
                # Small delay between messages to avoid rate limiting
                await asyncio.sleep(1)
            
            logger.info(f"Sent reminders to {len(users)} users for {tomorrow}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending daily reminders: {e}")
            return False
