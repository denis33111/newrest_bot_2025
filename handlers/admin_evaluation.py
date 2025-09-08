#!/usr/bin/env python3
"""
Admin Evaluation Handler
Manages the admin evaluation process for candidate registration
"""

import os
import logging
from datetime import datetime, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from services.google_sheets import init_google_sheets, get_monthly_sheet

logger = logging.getLogger(__name__)

class AdminEvaluation:
    def __init__(self, user_id, candidate_data):
        self.user_id = user_id
        self.candidate_data = candidate_data
        self.bot_token = os.getenv('BOT_TOKEN')
        self.admin_group_id = os.getenv('ADMIN_GROUP_ID')
        self.evaluation_data = {}
        self.selected_position = None
        
    async def notify_admin_group(self):
        """Send notification to admin group about new registration"""
        try:
            logger.info(f"Attempting to send admin notification for user {self.user_id}")
            logger.info(f"Admin group ID: {self.admin_group_id}")
            
            bot = Bot(token=self.bot_token)
            
            # Prepare candidate summary
            name = self.candidate_data.get('full_name', 'Unknown')
            user_id = self.candidate_data.get('user_id', 'Unknown')
            age = self.candidate_data.get('age', 'Unknown')
            phone = self.candidate_data.get('phone', 'Unknown')
            email = self.candidate_data.get('email', 'Unknown')
            transportation = self.candidate_data.get('transportation', 'Unknown')
            bank = self.candidate_data.get('bank', 'Unknown')
            driving_license = self.candidate_data.get('driving_license', 'Unknown')
            
            message = f"""🔔 Νέα Αίτηση Εγγραφής

👤 Υποψήφιος: {name}
🆔 ID: {user_id}

Κάντε κλικ για αξιολόγηση:"""

            keyboard = [[
                InlineKeyboardButton(
                    "Ξεκινήστε Αξιολόγηση",
                    callback_data=f"admin_eval_start_{user_id}"
                )
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            logger.info(f"Sending message to admin group {self.admin_group_id}")
            await bot.send_message(
                chat_id=self.admin_group_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            logger.info(f"Admin notification sent successfully for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending admin notification: {e}")
            logger.error(f"Admin group ID: {self.admin_group_id}")
            logger.error(f"Bot token present: {bool(self.bot_token)}")
            return False
    
    async def start_evaluation(self):
        """Start the evaluation process"""
        try:
            bot = Bot(token=self.bot_token)
            
            message = """🔍 **Αξιολόγηση Υποψηφίου**

**Ερώτηση 1:** Θα συνεχίσουμε με αυτόν τον υποψήφιο;

Παρακαλώ αξιολογήστε τα στοιχεία του υποψηφίου και αποφασίστε:"""
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Ναι, Συνεχίστε", callback_data=f"admin_eval_continue_{self.user_id}"),
                    InlineKeyboardButton("❌ Όχι, Απόρριψη", callback_data=f"admin_eval_reject_{self.user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await bot.send_message(
                chat_id=self.admin_group_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            logger.info(f"Evaluation started for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting evaluation: {e}")
            return False
    
    async def ask_position(self):
        """Ask for position selection"""
        try:
            bot = Bot(token=self.bot_token)
            
            message = """📋 **Επιλογή Θέσης**

**Ερώτηση 2:** Για ποια θέση είναι αυτός ο υποψήφιος;

Επιλέξτε την κατάλληλη θέση:"""
            
            keyboard = [
                [
                    InlineKeyboardButton("HL", callback_data=f"admin_eval_position_HL_{self.user_id}"),
                    InlineKeyboardButton("Supervisor", callback_data=f"admin_eval_position_Supervisor_{self.user_id}"),
                    InlineKeyboardButton("EQ", callback_data=f"admin_eval_position_EQ_{self.user_id}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await bot.send_message(
                chat_id=self.admin_group_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            logger.info(f"Position question sent for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error asking position: {e}")
            return False
    
    async def ask_course_date(self, position):
        """Ask for course date selection"""
        try:
            # Store the selected position
            self.selected_position = position
            
            bot = Bot(token=self.bot_token)
            
            # Calculate course dates based on position
            course_dates = self.calculate_course_dates(position)
            
            message = f"""📅 **Επιλογή Ημερομηνίας Μαθήματος**

**Ερώτηση 3:** Πότε πρέπει να προγραμματιστεί το μάθημα;

**Θέση:** {position}
**Διαθέσιμες ημερομηνίες:**"""
            
            keyboard = []
            
            # Add preset dates
            for i, date_info in enumerate(course_dates[:3]):  # Show first 3 options
                keyboard.append([
                    InlineKeyboardButton(
                        f"{date_info['date']} ({date_info['day']})",
                        callback_data=f"admin_eval_date_{date_info['date']}_{self.user_id}"
                    )
                ])
            
            # Add custom option
            keyboard.append([
                InlineKeyboardButton(
                    "📝 Προσαρμοσμένη Ημερομηνία",
                    callback_data=f"admin_eval_custom_{self.user_id}"
                )
            ])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await bot.send_message(
                chat_id=self.admin_group_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            logger.info(f"Course date question sent for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error asking course date: {e}")
            return False
    
    def calculate_course_dates(self, position):
        """Calculate available course dates based on position"""
        try:
            from datetime import datetime, timedelta
            import pytz
            
            # Set timezone to Greece
            greece_tz = pytz.timezone('Europe/Athens')
            now = datetime.now(greece_tz)
            
            # Calculate next available dates based on position
            dates = []
            
            if position == 'EQ':
                # EQ Position → Next 2 Fridays (not today)
                target_weekday = 4  # Friday
                day_name = 'Friday'
            else:
                # HL and Supervisor → Next 2 Thursdays (not today)
                target_weekday = 3  # Thursday
                day_name = 'Thursday'
            
            # Calculate next target day
            days_ahead = target_weekday - now.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            
            # First target day (next week)
            first_date = now + timedelta(days=days_ahead)
            dates.append({
                'date': first_date.strftime('%Y-%m-%d'),
                'day': day_name,
                'description': f'Next {day_name}'
            })
            
            # Second target day (following week)
            second_date = first_date + timedelta(days=7)
            dates.append({
                'date': second_date.strftime('%Y-%m-%d'),
                'day': day_name,
                'description': f'Following {day_name}'
            })
            
            return dates
            
        except Exception as e:
            logger.error(f"Error calculating course dates: {e}")
            return []
    
    async def save_evaluation(self, position, course_date, approved=True):
        """Save evaluation results and notify user"""
        try:
            # Update WORKERS sheet
            success = await self.update_worker_status(position, course_date, approved)
            
            # Also update REGISTRATION sheet with course info
            if approved:
                await self.update_registration_sheet(position, course_date)
            
            if success:
                # Notify user
                await self.notify_user_result(position, course_date, approved)
                
                # Notify admin
                await self.notify_admin_result(approved)
                
                logger.info(f"Evaluation completed for user {self.user_id}: {position}, {course_date}")
                return True
            else:
                logger.error(f"Failed to save evaluation for user {self.user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving evaluation: {e}")
            return False
    
    async def update_worker_status(self, position, course_date, approved):
        """Update worker status in WORKERS sheet"""
        try:
            sheets_data = init_google_sheets()
            if sheets_data['status'] != 'success':
                return False
            
            workers_sheet = sheets_data['sheets']['workers']
            
            # Find user row
            id_column = workers_sheet.col_values(2)  # Column B - ID
            user_row = None
            
            logger.info(f"Looking for user {self.user_id} in WORKERS sheet")
            logger.info(f"ID column values: {id_column}")
            
            for i, user_id_in_sheet in enumerate(id_column[1:], start=2):  # Skip header row
                logger.info(f"Checking row {i}: {user_id_in_sheet} == {self.user_id}? {str(self.user_id) == str(user_id_in_sheet)}")
                if str(self.user_id) == str(user_id_in_sheet):
                    user_row = i
                    break
            
            if not user_row:
                logger.error(f"User {self.user_id} not found in WORKERS sheet")
                # Try to add the user to WORKERS sheet as fallback
                logger.info(f"Attempting to add user {self.user_id} to WORKERS sheet as fallback")
                try:
                    # Add user to WORKERS sheet
                    worker_row = [
                        self.candidate_data.get('full_name', 'Unknown'),  # Column A - NAME
                        str(self.user_id),  # Column B - ID
                        'WAITING',  # Column C - STATUS
                        self.candidate_data.get('language', 'gr')  # Column D - LANGUAGE
                    ]
                    workers_sheet.append_row(worker_row)
                    logger.info(f"User {self.user_id} added to WORKERS sheet as fallback")
                    
                    # Get the total number of rows to find the newly added row
                    all_values = workers_sheet.get_all_values()
                    user_row = len(all_values)  # The new row will be at the end
                    logger.info(f"New user row number: {user_row}")
                except Exception as e:
                    logger.error(f"Failed to add user to WORKERS sheet: {e}")
                    return False
            
            # Update status and add course info
            if approved:
                # Update status to COURSE_DATE_SET
                workers_sheet.update_cell(user_row, 3, 'COURSE_DATE_SET')  # Column C - STATUS
                
                # Add position only to WORKERS sheet (course date goes to REGISTRATION sheet)
                workers_sheet.update_cell(user_row, 5, position)  # Column E - POSITION
                logger.info(f"WORKERS sheet updated - Position: {position}")
                
                # Note: Pre-course and day-course reminders are not stored in WORKERS sheet
                # as it only has 5 columns (A-E). Course date goes to REGISTRATION sheet only.
                logger.info(f"Position {position} saved to WORKERS sheet. Course date goes to REGISTRATION sheet only.")
            else:
                # Update status to STOP
                workers_sheet.update_cell(user_row, 3, 'STOP')  # Column C - STATUS
            
            logger.info(f"Worker status updated for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating worker status: {e}")
            return False
    
    async def update_registration_sheet(self, position, course_date):
        """Update REGISTRATION sheet with course info"""
        try:
            from services.google_sheets import init_google_sheets
            
            sheets_data = init_google_sheets()
            if sheets_data['status'] != 'success':
                return False
            
            registration_sheet = sheets_data['sheets']['registration']
            
            # Find user row in REGISTRATION sheet
            id_column = registration_sheet.col_values(2)  # Column B - ID
            user_row = None
            for i, user_id_in_sheet in enumerate(id_column[1:], start=2):  # Skip header row
                if str(self.user_id) == str(user_id_in_sheet):
                    user_row = i
                    break
            
            if not user_row:
                logger.error(f"User {self.user_id} not found in REGISTRATION sheet")
                return False
            
            # Update course date in REGISTRATION sheet (Column R)
            # Note: REGISTRATION sheet doesn't have a POSITION column
            registration_sheet.update_cell(user_row, 18, course_date)  # Column R - COURSE_DATE
            
            # Calculate and update pre-course reminder (1 day before course date)
            try:
                from datetime import datetime, timedelta
                course_date_obj = datetime.strptime(course_date, '%Y-%m-%d')
                pre_course_date = course_date_obj - timedelta(days=1)
                pre_course_reminder = pre_course_date.strftime('%Y-%m-%d')
                registration_sheet.update_cell(user_row, 19, pre_course_reminder)  # Column S - PRE_COURSE_REMINDER
                logger.info(f"Pre-course reminder set to {pre_course_reminder} for course on {course_date}")
            except Exception as e:
                logger.error(f"Error calculating pre-course reminder: {e}")
            
            # Update day-course reminder (same day as course date)
            registration_sheet.update_cell(user_row, 20, course_date)  # Column T - DAY_COURSE_REMINDER
            logger.info(f"Day-course reminder set to {course_date}")
            
            logger.info(f"REGISTRATION sheet updated - Course Date: {course_date}")
            
            logger.info(f"Registration sheet updated for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating registration sheet: {e}")
            return False
    
    async def notify_user_result(self, position, course_date, approved):
        """Notify user about evaluation result"""
        try:
            bot = Bot(token=self.bot_token)
            logger.info(f"notify_user_result - candidate_data: {self.candidate_data}")
            name = self.candidate_data.get('full_name', 'Unknown')
            language = self.candidate_data.get('language', 'gr')
            logger.info(f"notify_user_result - extracted name: {name}, language: {language}")
            
            if approved:
                if language == 'en':
                    message = f"""🎉 Congratulations!

You have been selected for the position **{position}**.

The introductory training will take place on **{course_date}** from 9:50-15:00.

Please submit all necessary documents as we discussed earlier.

If you need help, do not hesitate to contact us."""
                else:  # Greek
                    message = f"""🎉 Συγχαρητήρια!

Έχετε επιλεγεί για τη θέση **{position}**.

Η εισαγωγική εκπαίδευση θα πραγματοποιηθεί στις **{course_date}** στις 9:50-15:00.

Παρακαλούμε υποβάλετε όλα τα απαραίτητα έγγραφα όπως συζητήσαμε νωρίτερα.

Εάν χρειάζεστε βοήθεια, μη διστάσετε να επικοινωνήσετε μαζί μας."""
            else:
                if language == 'en':
                    message = f"""😔 Unfortunately, we cannot proceed with your application at this time.

Thank you for your interest and we wish you all the best!"""
                else:  # Greek
                    message = f"""😔 Δυστυχώς, δεν μπορούμε να προχωρήσουμε με την αίτησή σας αυτή τη στιγμή.

Σας ευχαριστούμε για το ενδιαφέρον και σας ευχόμαστε καλή συνέχεια!"""
            
            await bot.send_message(
                chat_id=self.user_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"User notification sent for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error notifying user: {e}")
            return False
    
    async def notify_admin_result(self, approved):
        """Notify admin about evaluation result"""
        try:
            bot = Bot(token=self.bot_token)
            name = self.candidate_data.get('full_name', 'Unknown')
            
            if approved:
                message = f"✅ **Evaluation Complete**\n\nCandidate **{name}** has been **APPROVED** and notified."
            else:
                message = f"❌ **Evaluation Complete**\n\nCandidate **{name}** has been **REJECTED** and notified."
            
            await bot.send_message(
                chat_id=self.admin_group_id,
                text=message,
                parse_mode='Markdown'
            )
            
            logger.info(f"Admin result notification sent for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error notifying admin: {e}")
            return False
