#!/usr/bin/env python3
"""
Working Console Handler
Manages check-in/out system for working users
"""

import os
import logging
from datetime import datetime
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from services.google_sheets import get_user_working_status, update_working_status
from services.location_service import validate_work_location
from handlers.language_system import get_text, get_buttons

logger = logging.getLogger(__name__)

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
            await self._send_error_message()
    
    def _create_working_keyboard(self, status, language):
        """Create permanent working console keyboard"""
        keyboard = []
        
        # Check In/Out button based on status
        if status.get('checked_in', False):
            check_button_text = "🔚 Check Out"
        else:
            check_button_text = "🟢 Check In"
        
        check_button = KeyboardButton(check_button_text)
        
        # Contact button
        contact_button_text = f"📞 {get_text(language, 'contact')}"
        contact_button = KeyboardButton(contact_button_text)
        
        # Add buttons to keyboard
        keyboard.append([check_button, contact_button])
        
        return keyboard
    
    def _create_status_message(self, status, language):
        """Create status message based on current state"""
        if status.get('checked_in', False):
            # User is checked in
            check_in_time = status.get('check_in_time', 'Unknown')
            
            message = f"""✅ **{get_text(language, 'welcome_back')}, {status.get('user_name', 'User')}!**

{get_text(language, 'already_registered')}

**{get_text(language, 'status_checked_in')}**
**{get_text(language, 'check_in_time')}** {check_in_time}
**{get_text(language, 'location_verified')}**

{get_text(language, 'use_buttons_below')}"""
        else:
            # User is not checked in
            message = f"""✅ **{get_text(language, 'welcome_back')}, {status.get('user_name', 'User')}!**

{get_text(language, 'already_registered')}

**{get_text(language, 'status_not_checked_in')}**

{get_text(language, 'ready_to_start')}"""
        
        return message
    
    async def handle_check_in_out(self, message_text):
        """Handle check in/out button press"""
        try:
            # Get user language first
            status = await get_user_working_status(self.user_id)
            user_language = status.get('language', 'gr')
            
            # Check for localized button text
            if get_text(user_language, 'check_in') in message_text or "Check In" in message_text:
                await self._handle_check_in(user_language)
            elif get_text(user_language, 'check_out') in message_text or "Check Out" in message_text:
                await self._handle_check_out(user_language)
            else:
                await self._send_error_message(user_language)
                
        except Exception as e:
            logger.error(f"Error handling check in/out: {e}")
            await self._send_error_message('gr')
    
    async def _handle_check_in(self, language):
        """Handle check in process"""
        try:
            # Check if already checked in
            status = await get_user_working_status(self.user_id)
            if status.get('checked_in', False):
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text=f"✅ **{get_text(language, 'already_checked_in')}**\n\n{get_text(language, 'already_checked_in_message')}\n\n{get_text(language, 'use_check_out')}",
                    parse_mode='Markdown'
                )
                return
            
            # Request location for check in
            await self._request_location_for_check_in(language)
            
        except Exception as e:
            logger.error(f"Error in check in process: {e}")
            await self._send_error_message(language)
    
    async def _handle_check_out(self, language):
        """Handle check out process"""
        try:
            # Check if checked in
            status = await get_user_working_status(self.user_id)
            if not status.get('checked_in', False):
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text=f"ℹ️ **{get_text(language, 'not_checked_in')}**\n\n{get_text(language, 'not_checked_in_message')}\n\n{get_text(language, 'use_check_in')}",
                    parse_mode='Markdown'
                )
                return
            
            # Request location for check out
            await self._request_location_for_check_out(language)
            
        except Exception as e:
            logger.error(f"Error in check out process: {e}")
            await self._send_error_message(language)
    
    async def _request_location_for_check_in(self, language):
        """Request location for check in"""
        keyboard = [
            [KeyboardButton("📍 Share Location", request_location=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, 
            resize_keyboard=True, 
            one_time_keyboard=False,
            is_persistent=True
        )
        
        message = f"""📍 **{get_text(language, 'check_in_required')}**

{get_text(language, 'tap_share_location')}"""
        
        await self.bot.send_message(
            chat_id=self.user_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _request_location_for_check_out(self, language):
        """Request location for check out"""
        keyboard = [
            [KeyboardButton("📍 Share Location", request_location=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, 
            resize_keyboard=True, 
            one_time_keyboard=False,
            is_persistent=True
        )
        
        message = f"""📍 **{get_text(language, 'check_out_required')}**

{get_text(language, 'tap_share_location')}"""
        
        await self.bot.send_message(
            chat_id=self.user_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def handle_location(self, location):
        """Handle location sharing for check in/out"""
        try:
            logger.info(f"Handling location: {location}")
            
            # Validate location
            is_valid = validate_work_location(location)
            logger.info(f"Location validation result: {is_valid}")
            
            if not is_valid:
                # Get user language for localized error message
                status = await get_user_working_status(self.user_id)
                language = status.get('language', 'gr')
                
                error_message = f"""❌ **{get_text(language, 'location_not_valid')}**

{get_text(language, 'location_validation_message')}

**{get_text(language, 'location_validation_instructions')}**
• {get_text(language, 'make_sure_at_work')}
• {get_text(language, 'check_gps_signal')}
• {get_text(language, 'try_again')}

{get_text(language, 'location_verification_note')}"""
                
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text=error_message,
                    parse_mode='Markdown'
                )
                # Show working console again
                await self.show_working_console()
                return
            
            # Process check in/out based on current status
            logger.info(f"Getting working status for user {self.user_id}")
            status = await get_user_working_status(self.user_id)
            logger.info(f"Working status: {status}")
            
            if status.get('checked_in', False):
                # Check out
                await self._process_check_out(location)
            else:
                # Check in
                await self._process_check_in(location)
                
        except Exception as e:
            logger.error(f"Error handling location: {e}")
            await self._send_error_message()
            # Restore working console on error
            await self.show_working_console()
    
    async def _process_check_in(self, location):
        """Process successful check in"""
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
                message = f"""✅ **Checked In Successfully**

**Time:** {current_time}
**Location:** Verified ✅
**Status:** Working

Your work session has started!"""
                
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                
                # Show working console with updated status
                await self.show_working_console()
            else:
                await self._send_error_message()
                # Restore working console on error
                await self.show_working_console()
                
        except Exception as e:
            logger.error(f"Error processing check in: {e}")
            await self._send_error_message()
            # Restore working console on error
            await self.show_working_console()
    
    async def _process_check_out(self, location):
        """Process successful check out"""
        try:
            from services.google_sheets import get_greek_time
            current_time = get_greek_time()
            
            # Get check in time to calculate hours
            status = await get_user_working_status(self.user_id)
            check_in_time = status.get('check_in_time', '00:00')
            
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
                message = f"""✅ **Checked Out Successfully**

**Check-in:** {check_in_time}
**Check-out:** {current_time}
**Total Hours:** {work_hours}
**Location:** Verified ✅

Great work today!"""
                
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text=message,
                    parse_mode='Markdown'
                )
                
                # Show working console with updated status
                await self.show_working_console()
            else:
                await self._send_error_message()
                # Restore working console on error
                await self.show_working_console()
                
        except Exception as e:
            logger.error(f"Error processing check out: {e}")
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
