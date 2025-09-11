#!/usr/bin/env python3
"""
Working Console Handler
Manages check-in/out system for working users
"""

import os
import logging
import asyncio
from datetime import datetime
import pytz
from telegram import Bot, ReplyKeyboardMarkup, KeyboardButton
from services.google_sheets import get_user_working_status, update_working_status
from services.location_service import validate_work_location
from handlers.language_system import get_text

logger = logging.getLogger(__name__)

# Global pending actions dictionary for state management
pending_actions = {}

class WorkingConsole:
    def __init__(self, user_id):
        self.user_id = user_id
        self.bot = Bot(token=os.getenv('BOT_TOKEN'))
    
    async def show_working_console(self):
        """Show working console with permanent buttons"""
        try:
            # Get current working status
            status = await get_user_working_status(self.user_id)
            
            # Get user language from status
            user_language = status.get('language', 'gr')
            
            # Create permanent keyboard
            keyboard = self._create_working_keyboard(status, user_language)
            reply_markup = ReplyKeyboardMarkup(
                keyboard, 
                resize_keyboard=True, 
                one_time_keyboard=False,
                is_persistent=True
            )
            
            # Create status message
            message = self._create_status_message(status, user_language)
            
            await self.bot.send_message(
                chat_id=self.user_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error showing working console: {e}")
            # Show basic working console even if Google Sheets fails
            await self._show_basic_working_console()
    
    async def _show_working_console_silent(self):
        """Show working console without welcome message - just the keyboard"""
        try:
            # Get user status from Google Sheets
            status = await get_user_working_status(self.user_id)
            language = status.get('language', 'gr')
            
            # Create smart keyboard based on current status
            keyboard = self._create_working_keyboard(status, language)
            reply_markup = ReplyKeyboardMarkup(
                keyboard, 
                resize_keyboard=True, 
                one_time_keyboard=False,
                is_persistent=True
            )
            
            # Send only the keyboard without any message
            await self.bot.send_message(
                chat_id=self.user_id,
                text=" ",  # Empty message
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error showing silent working console: {e}")
            # Show basic working console even if Google Sheets fails
            await self._show_basic_working_console()
    
    async def _show_basic_working_console(self):
        """Show basic working console when Google Sheets is unavailable"""
        try:
            # Create basic keyboard with both buttons
            keyboard = [
                [KeyboardButton("🟢 Check In"), KeyboardButton("🔚 Check Out")],
                [KeyboardButton("📞 Contact")]
            ]
            reply_markup = ReplyKeyboardMarkup(
                keyboard, 
                resize_keyboard=True, 
                one_time_keyboard=False,
                is_persistent=True
            )
            
            # Basic message
            message = """✅ **Welcome to NewRest Bot!**

**System Status:** ⚠️ Limited (Google Sheets temporarily unavailable)

**Available Actions:**
• Check In/Out (location verification required)
• Contact support

**Note:** Some features may be limited due to system maintenance."""
            
            await self.bot.send_message(
                chat_id=self.user_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error showing basic working console: {e}")
            await self._send_error_message()
    
    def _create_working_keyboard(self, status, language):
        """Create smart keyboard based on current attendance status"""
        keyboard = []
        
        # Determine current status
        current_status = self._get_attendance_status(status)
        
        if current_status == 'CHECKED_IN':
            # Worker is checked in, show only check-out button
            check_out_button = KeyboardButton("🔚 Check Out")
            contact_button = KeyboardButton(f"📞 {get_text(language, 'contact')}")
            keyboard.append([check_out_button, contact_button])
            
        elif current_status == 'COMPLETE':
            # Worker completed today, show only check-in button
            check_in_button = KeyboardButton("🟢 Check In")
            contact_button = KeyboardButton(f"📞 {get_text(language, 'contact')}")
            keyboard.append([check_in_button, contact_button])
            
        else:
            # Worker not checked in today, show only check-in button
            check_in_button = KeyboardButton("🟢 Check In")
            contact_button = KeyboardButton(f"📞 {get_text(language, 'contact')}")
            keyboard.append([check_in_button, contact_button])
        
        return keyboard
    
    def _get_attendance_status(self, status):
        """Determine attendance status from Google Sheets data"""
        try:
            # Check if user has check-in time
            check_in_time = status.get('check_in_time', '')
            check_out_time = status.get('check_out_time', '')
            
            if not check_in_time:
                return 'NOT_CHECKED_IN'
            elif check_in_time and not check_out_time:
                return 'CHECKED_IN'
            elif check_in_time and check_out_time:
                return 'COMPLETE'
            else:
                return 'NOT_CHECKED_IN'
                
        except Exception as e:
            logger.error(f"Error determining attendance status: {e}")
            return 'NOT_CHECKED_IN'
    
    def _create_status_message(self, status, language):
        """Create smart status message based on current attendance state"""
        current_status = self._get_attendance_status(status)
        user_name = status.get('user_name', 'User')
        
        if current_status == 'CHECKED_IN':
            # User is checked in but not out
            check_in_time = status.get('check_in_time', 'Unknown')
            message = f"""✅ **{get_text(language, 'welcome_back')}, {user_name}!**

{get_text(language, 'already_registered')}

**{get_text(language, 'status_checked_in')}**
**{get_text(language, 'check_in_time')}** {check_in_time}

{get_text(language, 'use_buttons_below')}"""
            
        elif current_status == 'COMPLETE':
            # User completed today's work
            check_in_time = status.get('check_in_time', '')
            check_out_time = status.get('check_out_time', '')
            
            if '-' in check_in_time:
                # Format: "HH:MM-HH:MM"
                check_in, check_out = check_in_time.split('-')
                message = f"""✅ **{get_text(language, 'welcome_back')}, {user_name}!**

{get_text(language, 'already_checked_in_clear')}

**{get_text(language, 'check_in_time')}** {check_in}
**{get_text(language, 'check_out_time')}** {check_out}

{get_text(language, 'use_buttons_below')}"""
            else:
                message = f"""✅ **{get_text(language, 'welcome_back')}, {user_name}!**

{get_text(language, 'already_checked_in_clear')}

{get_text(language, 'use_buttons_below')}"""
                
        else:
            # User not checked in today
            message = f"""✅ **{get_text(language, 'welcome_back')}, {user_name}!**

{get_text(language, 'already_registered')}

{get_text(language, 'use_buttons_below')}"""
        
        return message
    
    async def handle_check_in_out(self, message_text):
        """Handle check in/out button press with smart status detection"""
        try:
            # Get user language and current status ONCE
            status = await get_user_working_status(self.user_id)
            user_language = status.get('language', 'gr')
            current_status = self._get_attendance_status(status)
            
            # Check for button text (English only as per requirements)
            if "Check In" in message_text:
                await self._handle_check_in(user_language, current_status, status)
            elif "Check Out" in message_text:
                await self._handle_check_out(user_language, current_status, status)
            else:
                await self._send_error_message(user_language)
                
        except Exception as e:
            logger.error(f"Error handling check in/out: {e}")
            await self._send_error_message('gr')
    
    async def _handle_check_in(self, language, current_status, status_data):
        """Handle check in process with smart status detection"""
        try:
            # Check if already checked in today
            if current_status == 'CHECKED_IN':
                check_in_time = status_data.get('check_in_time', 'Unknown')
                message = f"""✅ **{get_text(language, 'already_checked_in')}**

**{get_text(language, 'check_in_time')}** {check_in_time}

**{get_text(language, 'next_action')}** {get_text(language, 'check_out_when_done')}"""
                
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                return
            
            # Check if already completed today
            elif current_status == 'COMPLETE':
                check_in_time = status_data.get('check_in_time', '')
                
                if '-' in check_in_time:
                    check_in, check_out = check_in_time.split('-')
                    message = f"""✅ **{get_text(language, 'already_checked_in')}**

**{get_text(language, 'check_in_time')}** {check_in}
**{get_text(language, 'check_out_time')}** {check_out}

**{get_text(language, 'next_action')}** {get_text(language, 'check_in_tomorrow')}"""
                else:
                    message = f"""✅ **{get_text(language, 'already_checked_in')}**

**{get_text(language, 'next_action')}** {get_text(language, 'check_in_tomorrow')}"""
                
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                return
            
            # Proceed with check-in
            await self._request_location_for_check_in(language)
            
        except Exception as e:
            logger.error(f"Error in check in process: {e}")
            await self._send_error_message(language)
    
    async def _handle_check_out(self, language, current_status, status_data):
        """Handle check out process with smart status detection"""
        try:
            # Check if not checked in today
            if current_status != 'CHECKED_IN':
                message = f"""❌ **{get_text(language, 'not_checked_in')}**

**{get_text(language, 'must_check_in_first')}**

{get_text(language, 'use_buttons_below')}"""
                
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                return
            
            # Proceed with check-out
            await self._request_location_for_check_out(language)
            
        except Exception as e:
            logger.error(f"Error in check out process: {e}")
            await self._send_error_message(language)
    
    async def _request_location_for_check_in(self, language):
        """Request location for check in with pending action tracking"""
        try:
            # Get user name for pending action
            status = await get_user_working_status(self.user_id)
            user_name = status.get('user_name', 'User')
            
            # Store pending check-in action
            greece_tz = pytz.timezone('Europe/Athens')
            pending_actions[self.user_id] = {
                'worker_name': user_name,
                'action': 'checkin',
                'timestamp': datetime.now(greece_tz)
            }
            
            # Create location request keyboard with back button
            keyboard = [
                [KeyboardButton("📍 Share Location", request_location=True)],
                [KeyboardButton(f"🏠 {get_text(language, 'back_to_menu')}")]
            ]
            reply_markup = ReplyKeyboardMarkup(
                keyboard, 
                resize_keyboard=True, 
                one_time_keyboard=False,
                is_persistent=True
            )
            
            message = f"""📍 **{get_text(language, 'check_in_required')}**

**{get_text(language, 'tap_share_location')}**"""
            
            await self.bot.send_message(
                chat_id=self.user_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error requesting location for check-in: {e}")
            await self._send_error_message(language)
    
    async def _request_location_for_check_out(self, language):
        """Request location for check out with pending action tracking"""
        try:
            # Get user name for pending action
            status = await get_user_working_status(self.user_id)
            user_name = status.get('user_name', 'User')
            
            # Store pending check-out action
            greece_tz = pytz.timezone('Europe/Athens')
            pending_actions[self.user_id] = {
                'worker_name': user_name,
                'action': 'checkout',
                'timestamp': datetime.now(greece_tz)
            }
            
            # Create location request keyboard with back button
            keyboard = [
                [KeyboardButton("📍 Share Location", request_location=True)],
                [KeyboardButton(f"🏠 {get_text(language, 'back_to_menu')}")]
            ]
            reply_markup = ReplyKeyboardMarkup(
                keyboard, 
                resize_keyboard=True, 
                one_time_keyboard=False,
                is_persistent=True
            )
            
            message = f"""📍 **{get_text(language, 'check_out_required')}**

**{get_text(language, 'tap_share_location')}**"""
            
            await self.bot.send_message(
                chat_id=self.user_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error requesting location for check-out: {e}")
            await self._send_error_message(language)
    
    async def handle_location(self, location):
        """Handle location sharing for check in/out with pending action tracking"""
        try:
            # Check if user has a pending action
            pending_action = pending_actions.get(self.user_id)
            
            if not pending_action:
                # No pending action, ignore location
                return
            
            # Check if already processing to prevent double-clicks
            if pending_action.get('processing', False):
                return
            
            # Mark as processing
            pending_actions[self.user_id]['processing'] = True
            
            # Send immediate "processing" message to prevent double-clicks
            status = await get_user_working_status(self.user_id)
            language = status.get('language', 'gr')
            
            processing_message = f"""⏳ **{get_text(language, 'processing')}**

{get_text(language, 'please_wait')}"""
            
            await self.bot.send_message(
                chat_id=self.user_id,
                text=processing_message,
                parse_mode='Markdown'
            )
            
            # Small delay to show processing message and prevent rapid double-clicks
            await asyncio.sleep(1)
            
            # Validate location
            is_valid = validate_work_location(location)
            
            if not is_valid:
                # Get user language for localized error message
                status = await get_user_working_status(self.user_id)
                language = status.get('language', 'gr')
                
                error_message = f"""❌ **{get_text(language, 'location_not_valid')}**

{get_text(language, 'location_validation_message')}

**{get_text(language, 'location_validation_instructions')}**
• {get_text(language, 'make_sure_at_work')}
• {get_text(language, 'check_gps_signal')}
• {get_text(language, 'try_again')}"""
                
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text=error_message,
                    parse_mode='Markdown'
                )
                
                # Clear pending action and return to main menu
                pending_actions.pop(self.user_id, None)
                await self.show_working_console()
                return
            
            # Location verified, proceed with action
            if pending_action['action'] == 'checkin':
                await self._complete_checkin(location)
            elif pending_action['action'] == 'checkout':
                await self._complete_checkout(location)
            
            # Clear pending action
            pending_actions.pop(self.user_id, None)
                
        except Exception as e:
            logger.error(f"Error handling location: {e}")
            await self._send_error_message()
            # Clear pending action on error
            pending_actions.pop(self.user_id, None)
            # Restore working console on error
            await self.show_working_console()
    
    async def _complete_checkin(self, location):
        """Complete check-in after location verification"""
        try:
            from services.google_sheets import get_greek_time
            current_time = get_greek_time()
            
            # Update working status
            success = await update_working_status(
                self.user_id, 
                checked_in=True, 
                check_in_time=current_time,
                location=location
            )
            
            if success:
                # Get user language for localized message
                status = await get_user_working_status(self.user_id)
                language = status.get('language', 'gr')
                
                message = f"""✅ **{get_text(language, 'check_in_successful')}**

**{get_text(language, 'time')}** {current_time}
**{get_text(language, 'location')}** {get_text(language, 'verified')} ✅

{get_text(language, 'work_session_started')}"""
                
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                
                # Show updated working console with Check Out button (no welcome message)
                await self._show_working_console_silent()
                
            else:
                await self._send_error_message()
                # Restore working console on error
                await self.show_working_console()
                
        except Exception as e:
            logger.error(f"Error completing check in: {e}")
            await self._send_error_message()
            # Restore working console on error
            await self.show_working_console()
    
    async def _complete_checkout(self, location):
        """Complete check-out after location verification"""
        try:
            from services.google_sheets import get_greek_time
            current_time = get_greek_time()
            
            # Get check in time to calculate hours
            status = await get_user_working_status(self.user_id)
            check_in_time = status.get('check_in_time', '00:00')
            language = status.get('language', 'gr')
            
            # Calculate work hours
            work_hours = self._calculate_work_hours(check_in_time, current_time)
            
            # Update working status
            success = await update_working_status(
                self.user_id, 
                checked_in=False, 
                check_out_time=current_time,
                work_hours=work_hours,
                location=location
            )
            
            if success:
                message = f"""✅ **{get_text(language, 'check_out_successful')}**

**{get_text(language, 'check_in_time')}** {check_in_time}
**{get_text(language, 'check_out_time')}** {current_time}
**{get_text(language, 'location')}** {get_text(language, 'verified')} ✅

{get_text(language, 'great_work_today')}"""
                
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                
                # Show updated working console with Check In button (no welcome message)
                await self._show_working_console_silent()
                
            else:
                await self._send_error_message()
                # Restore working console on error
                await self.show_working_console()
                
        except Exception as e:
            logger.error(f"Error completing check out: {e}")
            await self._send_error_message()
            # Restore working console on error
            await self.show_working_console()
    
    def _calculate_work_hours(self, check_in_time, check_out_time):
        """Calculate work hours between check in and out"""
        try:
            # Parse times
            check_in = datetime.strptime(check_in_time, "%H:%M")
            check_out = datetime.strptime(check_out_time, "%H:%M")
            
            # Calculate difference
            diff = check_out - check_in
            
            # Convert to hours and minutes
            total_minutes = int(diff.total_seconds() / 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            
            return f"{hours}h {minutes}m"
            
        except Exception as e:
            logger.error(f"Error calculating work hours: {e}")
            return "0h 0m"
    
    async def handle_contact(self):
        """Handle contact button press"""
        # Get user language first
        status = await get_user_working_status(self.user_id)
        user_language = status.get('language', 'gr')
        
        message = f"""📞 **{get_text(user_language, 'contact')}**

**{get_text(user_language, 'contact_message')}**

{get_text(user_language, 'contact_description')}

**{get_text(user_language, 'contact_for_now')}**"""
        
        await self.bot.send_message(
            chat_id=self.user_id,
            text=message,
            parse_mode='Markdown'
        )
    
    
    async def _send_error_message(self, language='gr'):
        """Send error message"""
        message = f"""❌ **{get_text(language, 'something_went_wrong')}**

{get_text(language, 'error_message')}

**{get_text(language, 'please_try')}**
• {get_text(language, 'check_internet')}
• {get_text(language, 'try_again')}
• {get_text(language, 'contact_support')}

*{get_text(language, 'working_on_fix')}*"""
        
        await self.bot.send_message(
            chat_id=self.user_id,
            text=message,
            parse_mode='Markdown'
        )
    
    async def _show_contact_only_console(self):
        """Show console with only contact button for post-registration users"""
        try:
            from telegram import ReplyKeyboardMarkup, KeyboardButton
            from handlers.language_system import get_text
            
            # Get user language from status
            status = await get_user_working_status(self.user_id)
            user_language = status.get('language', 'gr')
            
            # Create keyboard with only contact button
            contact_button = KeyboardButton(f"📞 {get_text(user_language, 'contact')}")
            keyboard = [[contact_button]]
            reply_markup = ReplyKeyboardMarkup(
                keyboard, 
                resize_keyboard=True, 
                one_time_keyboard=False,
                is_persistent=True
            )
            
            # Create message for post-registration users
            if user_language == 'gr':
                message = """✅ **Εγγραφή Ολοκληρώθηκε**

Η εγγραφή σας έχει αποθηκευτεί με επιτυχία. Θα ενημερωθείτε για τα επόμενα βήματα.

Εάν έχετε ερωτήσεις, μπορείτε να επικοινωνήσετε μαζί μας."""
            else:
                message = """✅ **Registration Completed**

Your registration has been saved successfully. You will be notified about the next steps.

If you have any questions, you can contact us."""
            
            await self.bot.send_message(
                chat_id=self.user_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error showing contact-only console: {e}")