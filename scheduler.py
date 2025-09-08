#!/usr/bin/env python3
"""
Scheduler for sending daily reminders
Runs at 10am Greece time to send pre-course reminders
"""

import asyncio
import logging
from datetime import datetime, time
import pytz
from handlers.reminder_system import ReminderSystem

logger = logging.getLogger(__name__)

class ReminderScheduler:
    def __init__(self):
        self.reminder_system = ReminderSystem()
        self.greece_tz = pytz.timezone('Europe/Athens')
        self.running = False
    
    async def start_scheduler(self):
        """Start the reminder scheduler"""
        self.running = True
        logger.info("Reminder scheduler started")
        
        while self.running:
            try:
                # Check if it's 10am Greece time
                now = datetime.now(self.greece_tz)
                current_time = now.time()
                target_time = time(10, 0)  # 10:00 AM
                
                # If it's 10am, send reminders
                if current_time.hour == target_time.hour and current_time.minute == target_time.minute:
                    logger.info("It's 10am - sending daily reminders")
                    await self.reminder_system.send_daily_reminders()
                
                # Wait 1 minute before checking again
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in reminder scheduler: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def stop_scheduler(self):
        """Stop the reminder scheduler"""
        self.running = False
        logger.info("Reminder scheduler stopped")

# Global scheduler instance
scheduler = ReminderScheduler()

async def start_reminder_scheduler():
    """Start the reminder scheduler (call this from app.py)"""
    await scheduler.start_scheduler()

def stop_reminder_scheduler():
    """Stop the reminder scheduler (call this on app shutdown)"""
    scheduler.stop_scheduler()
