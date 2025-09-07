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
            
            message = f"""🔔 **New Candidate Registration**

**Candidate Details:**
👤 **Name:** {name}
🆔 **User ID:** {user_id}
📅 **Age:** {age}
📞 **Phone:** {phone}
📧 **Email:** {email}
🚗 **Transportation:** {transportation}
🏦 **Bank:** {bank}
🚙 **Driving License:** {driving_license}

Click below to start evaluation:"""

            keyboard = [[
                InlineKeyboardButton(
                    "Start Evaluation",
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
            
            message = """🔍 **Candidate Evaluation**

**Question 1:** Should we continue with this candidate?

Please review the candidate details and decide:"""
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Yes, Continue", callback_data=f"admin_eval_continue_{self.user_id}"),
                    InlineKeyboardButton("❌ No, Reject", callback_data=f"admin_eval_reject_{self.user_id}")
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
            
            message = """📋 **Position Selection**

**Question 2:** What position is this candidate for?

Select the appropriate position:"""
            
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
            
            message = f"""📅 **Course Date Selection**

**Question 3:** When should the course be scheduled?

**Position:** {position}
**Available dates:**"""
            
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
                    "📝 Custom Date",
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
            # Get current date
            today = datetime.now()
            
            # Calculate next available dates (example logic)
            dates = []
            
            # Next Monday
            next_monday = today + timedelta(days=(7 - today.weekday()) % 7)
            if next_monday.weekday() == 0:  # If today is Monday, get next Monday
                next_monday += timedelta(days=7)
            
            dates.append({
                'date': next_monday.strftime('%Y-%m-%d'),
                'day': 'Monday',
                'description': 'Next Monday'
            })
            
            # Same day next week
            same_day_next_week = today + timedelta(days=7)
            dates.append({
                'date': same_day_next_week.strftime('%Y-%m-%d'),
                'day': same_day_next_week.strftime('%A'),
                'description': 'Same day next week'
            })
            
            # Next Tuesday
            next_tuesday = today + timedelta(days=(8 - today.weekday()) % 7)
            if next_tuesday.weekday() == 1:  # If today is Tuesday, get next Tuesday
                next_tuesday += timedelta(days=7)
            
            dates.append({
                'date': next_tuesday.strftime('%Y-%m-%d'),
                'day': 'Tuesday',
                'description': 'Next Tuesday'
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
            
            for i, user_id_in_sheet in enumerate(id_column[1:], start=2):  # Skip header row
                if str(self.user_id) == str(user_id_in_sheet):
                    user_row = i
                    break
            
            if not user_row:
                logger.error(f"User {self.user_id} not found in WORKERS sheet")
                return False
            
            # Update status and add course info
            if approved:
                # Update status to COURSE_DATE_SET
                workers_sheet.update_cell(user_row, 3, 'COURSE_DATE_SET')  # Column C - STATUS
                
                # Add position and course date to additional columns if they exist
                # This would need to be adjusted based on actual sheet structure
                try:
                    workers_sheet.update_cell(user_row, 5, position)  # Column E - POSITION
                    workers_sheet.update_cell(user_row, 6, course_date)  # Column F - COURSE_DATE
                except:
                    pass  # Columns might not exist yet
            else:
                # Update status to STOP
                workers_sheet.update_cell(user_row, 3, 'STOP')  # Column C - STATUS
            
            logger.info(f"Worker status updated for user {self.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating worker status: {e}")
            return False
    
    async def notify_user_result(self, position, course_date, approved):
        """Notify user about evaluation result"""
        try:
            bot = Bot(token=self.bot_token)
            name = self.candidate_data.get('full_name', 'Candidate')
            
            if approved:
                message = f"""🎉 Συγχαρητήρια {name}!

Έχετε επιλεγεί για τη θέση **{position}**.

Η εισαγωγική εκπαίδευση θα πραγματοποιηθεί στις **{course_date}** στις 9:50-15:00.

Παρακαλούμε υποβάλετε όλα τα απαραίτητα έγγραφα όπως συζητήσαμε νωρίτερα.

Εάν χρειάζεστε βοήθεια, μη διστάσετε να επικοινωνήσετε μαζί μας."""
            else:
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
