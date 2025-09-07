#!/usr/bin/env python3
"""
Telegram Bot Service
Handles all Telegram bot operations
"""

import os
import logging
from telegram import Bot

logger = logging.getLogger(__name__)

# Load environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

async def send_working_console(user_id):
    """Send working console message"""
    message = """
🚀 **Working Console - Coming Soon**

Welcome back! Your working console is being prepared.

**Available Soon:**
• Check-in/out system
• Daily attendance tracking
• Schedule management
• Status updates

Stay tuned! 🎯
    """
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')

async def send_registration_flow(user_id):
    """Send registration flow message"""
    message = """
📝 **Registration Flow - Coming Soon**

Welcome! You need to complete registration first.

**Registration Process:**
• Step 1: Personal data input
• Step 2: Admin verification
• Step 3: Course date confirmation

**Coming Soon!** 🎯
    """
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')

async def send_error_message(user_id):
    """Send error message"""
    message = """
❌ **System Error**

Sorry, there was an error processing your request.

Please try again later.
    """
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=user_id, text=message, parse_mode='Markdown')

async def setup_webhook():
    """Set up Telegram webhook"""
    try:
        webhook_url = WEBHOOK_URL  # Already includes /webhook
        bot = Bot(token=BOT_TOKEN)
        await bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
        return True
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")
        return False
