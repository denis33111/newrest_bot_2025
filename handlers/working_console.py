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
            
            # Create permanent keyboard
            keyboard = self._create_working_keyboard(status)
            reply_markup = ReplyKeyboardMarkup(
                keyboard, 
                resize_keyboard=True, 
                one_time_keyboard=False,
                is_persistent=True
            )
            
            # Create status message
            message = self._create_status_message(status)
            
            await self.bot.send_message(
                chat_id=self.user_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error showing working console: {e}")
            await self._send_error_message()
    
    def _create_working_keyboard(self, status):
        """Create permanent working console keyboard"""
        keyboard = []
        
        # Check In/Out button based on status
        if status.get('checked_in', False):
            check_button = KeyboardButton("🔚 Check Out")
        else:
            check_button = KeyboardButton("🟢 Check In")
        
        # Contact button
        contact_button = KeyboardButton("📞 Contact")
        
        # Add buttons to keyboard
        keyboard.append([check_button, contact_button])
        
        return keyboard
    
    def _create_status_message(self, status):
        """Create status message based on current state"""
        if status.get('checked_in', False):
            # User is checked in
            check_in_time = status.get('check_in_time', 'Unknown')
            today_hours = status.get('today_hours', '0h 0m')
            
            message = f"""🚀 **Working Console**

**Status:** ✅ Checked In
**Check-in Time:** {check_in_time}
**Today's Hours:** {today_hours}
**Location:** Verified ✅

Use the buttons below to manage your work session."""
        else:
            # User is not checked in
            message = f"""🚀 **Working Console**

**Status:** ⏸️ Not Checked In
**Today's Hours:** 0h 0m

Ready to start your work session! Use the buttons below."""
        
        return message
    
    async def handle_check_in_out(self, message_text):
        """Handle check in/out button press"""
        try:
            if "Check In" in message_text:
                await self._handle_check_in()
            elif "Check Out" in message_text:
                await self._handle_check_out()
            else:
                await self._send_error_message()
                
        except Exception as e:
            logger.error(f"Error handling check in/out: {e}")
            await self._send_error_message()
    
    async def _handle_check_in(self):
        """Handle check in process"""
        try:
            # Check if already checked in
            status = await get_user_working_status(self.user_id)
            if status.get('checked_in', False):
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text="✅ **Already Checked In**\n\nYou're already checked in and working.\n\nUse 'Check Out' when you finish your work session.",
                    parse_mode='Markdown'
                )
                return
            
            # Request location for check in
            await self._request_location_for_check_in()
            
        except Exception as e:
            logger.error(f"Error in check in process: {e}")
            await self._send_error_message()
    
    async def _handle_check_out(self):
        """Handle check out process"""
        try:
            # Check if checked in
            status = await get_user_working_status(self.user_id)
            if not status.get('checked_in', False):
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text="ℹ️ **Not Checked In**\n\nYou need to check in first before you can check out.\n\nUse 'Check In' to start your work session.",
                    parse_mode='Markdown'
                )
                return
            
            # Request location for check out
            await self._request_location_for_check_out()
            
        except Exception as e:
            logger.error(f"Error in check out process: {e}")
            await self._send_error_message()
    
    async def _request_location_for_check_in(self):
        """Request location for check in"""
        keyboard = [
            [KeyboardButton("📍 Share Location", request_location=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, 
            resize_keyboard=True, 
            one_time_keyboard=True
        )
        
        message = """🟢 **Check In - Location Required**

To check in, please share your current location.

**How to share location:**
1. Tap 'Share Location' below
2. Allow location access when prompted
3. Select 'Send Location'

**Note:** You must be within 500m of the work location to check in successfully."""
        
        await self.bot.send_message(
            chat_id=self.user_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def _request_location_for_check_out(self):
        """Request location for check out"""
        keyboard = [
            [KeyboardButton("📍 Share Location", request_location=True)]
        ]
        reply_markup = ReplyKeyboardMarkup(
            keyboard, 
            resize_keyboard=True, 
            one_time_keyboard=True
        )
        
        message = """🔚 **Check Out - Location Required**

To check out, please share your current location.

**How to share location:**
1. Tap 'Share Location' below
2. Allow location access when prompted
3. Select 'Send Location'

**Note:** You must be within 500m of the work location to check out successfully."""
        
        await self.bot.send_message(
            chat_id=self.user_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def handle_location(self, location):
        """Handle location sharing for check in/out"""
        try:
            # Validate location
            is_valid = await validate_work_location(location)
            
            if not is_valid:
                await self.bot.send_message(
                    chat_id=self.user_id,
                    text="📍 **Location Not Valid**\n\nYou need to be within 500m of the work location to check in/out.\n\n**Please:**\n• Make sure you're at the work location\n• Check your GPS signal\n• Try sharing location again\n\n*Location verification ensures accurate attendance tracking.*",
                    parse_mode='Markdown'
                )
                # Show working console again
                await self.show_working_console()
                return
            
            # Process check in/out based on current status
            status = await get_user_working_status(self.user_id)
            
            if status.get('checked_in', False):
                # Check out
                await self._process_check_out(location)
            else:
                # Check in
                await self._process_check_in(location)
                
        except Exception as e:
            logger.error(f"Error handling location: {e}")
            await self._send_error_message()
    
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
                
        except Exception as e:
            logger.error(f"Error processing check in: {e}")
            await self._send_error_message()
    
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
                
        except Exception as e:
            logger.error(f"Error processing check out: {e}")
            await self._send_error_message()
    
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
        message = """📞 **Contact**

**Crew Assistant:** Coming Soon!

This feature will connect you directly with the crew assistant for any questions or support.

**For now, please contact your supervisor directly.**"""
        
        await self.bot.send_message(
            chat_id=self.user_id,
            text=message,
            parse_mode='Markdown'
        )
    
    async def _send_error_message(self):
        """Send error message"""
        message = """❌ **Something went wrong**

Sorry, there was an error processing your request.

**Please try:**
• Check your internet connection
• Try again in a moment
• Contact support if the problem continues

*We're working to fix this issue.*"""
        
        await self.bot.send_message(
            chat_id=self.user_id,
            text=message,
            parse_mode='Markdown'
        )
