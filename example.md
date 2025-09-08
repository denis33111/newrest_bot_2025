def create_smart_keyboard(worker_name: str, current_status: str) -> ReplyKeyboardMarkup:
    """Create smart keyboard based on current attendance status"""
    
    if current_status == 'CHECKED_IN':
        # Worker is checked in, show only check-out button
        keyboard = [
            [KeyboardButton("🚪 Check Out")],
            [KeyboardButton("📅 Πρόγραμμα"), KeyboardButton("�� Contact")]
        ]
    elif current_status == 'COMPLETE':
        # Worker completed today, show only check-in button
        keyboard = [
            [KeyboardButton("✅ Check In")],
            [KeyboardButton("📅 Πρόγραμμα"), KeyboardButton("�� Contact")]
        ]
    else:
        # Worker not checked in today, show only check-in button
        keyboard = [
            [KeyboardButton("✅ Check In")],
            [KeyboardButton("📅 Πρόγραμμα"), KeyboardButton("�� Contact")]
        ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)




    async def start_command(update: Update, context):
    """Handle /start command"""
    # Get services from context
    sheets_service = context.bot_data.get('sheets_service')
    location_service = context.bot_data.get('location_service')
    
    user = update.effective_user
    
    # Check if worker already exists
    existing_worker = await sheets_service.find_worker_by_telegram_id(user.id)
    
    if existing_worker:
        # Existing worker - show smart keyboard based on current status
        worker_name = existing_worker['name']
        
        # Get current attendance status
        attendance_status = await sheets_service.get_worker_attendance_status(worker_name)
        current_status = attendance_status['status']
        
        # Create smart keyboard based on current status
        smart_keyboard = create_smart_keyboard(worker_name, current_status)
        
        # Show welcome message with smart keyboard
        welcome_msg = f"""
✅ **Καλώς ήρθατε, {worker_name}!**

Είστε ήδη εγγεγραμμένος στο σύστημα.

**Χρησιμοποιήστε τα κουμπιά κάτω από το πεδίο εισαγωγής:**
        """
        
        # Send message with smart keyboard
        await update.message.reply_text(welcome_msg, parse_mode='Markdown', reply_markup=smart_keyboard)
        
        return ConversationHandler.END
    else:
        # New worker - start registration flow
        await update.message.reply_text("Χαίρετε! ��\n\nΠαρακαλώ για να κάνετε εγγραφή γράψτε ονομα και επώνυμο:")
        
        # Store user data for registration
        context.user_data['registration'] = {'telegram_id': user.id}
        
        return ASKING_NAME



        async def handle_persistent_keyboard(update: Update, context):
    """Handle persistent keyboard button presses"""
    try:
        user = update.effective_user
        text = update.message.text
        
        logger.info(f"�� DEBUG: handle_persistent_keyboard called by user {user.id}")
        logger.info(f"�� DEBUG: Button text: '{text}'")
        logger.info(f"🔍 DEBUG: User info: {user.username} ({user.first_name} {user.last_name})")
        
        # Check if worker exists
        sheets_service = context.bot_data.get('sheets_service')
        location_service = context.bot_data.get('location_service')
        existing_worker = await sheets_service.find_worker_by_telegram_id(user.id)
        
        if not existing_worker:
            await update.message.reply_text("❌ Δεν είστε εγγεγραμμένος στο σύστημα. Παρακαλώ χρησιμοποιήστε /start για εγγραφή.")
            return
        
        worker_name = existing_worker['name']
        
        if text == "✅ Check In":
            # Handle check-in via persistent keyboard
            logger.info(f"🔍 DEBUG: Check In button pressed by user {user.id} ({worker_name})")
            await handle_persistent_checkin(update, context, worker_name)
            
        elif text == "🚪 Check Out":
            # Handle check-out via persistent keyboard
            logger.info(f"🔍 DEBUG: Check Out button pressed by user {user.id} ({worker_name})")
            await handle_persistent_checkout(update, context, worker_name)
            
        elif text == "📅 Πρόγραμμα":
            # Handle schedule request via persistent keyboard
            await handle_persistent_schedule(update, context, worker_name)
            
        elif text == "📞 Contact":
            # Handle contact request via persistent keyboard
            await handle_persistent_contact(update, context, worker_name)
            
        elif text == "🏠 Πίσω στο μενού":
            # Handle back to menu button - return to main menu
            await return_to_main_menu(update, context, user.id)
            
    except Exception as e:
        logger.error(f"Error handling persistent keyboard: {e}")
        await update.message.reply_text("❌ Σφάλμα κατά την επεξεργασία της ενέργειας.")






        async def handle_persistent_checkin(update: Update, context, worker_name: str):
    """Handle check-in from persistent keyboard"""
    try:
        # Get sheets service
        sheets_service = context.bot_data.get('sheets_service')
        if not sheets_service:
            await update.message.reply_text("❌ Σφάλμα: Δεν είναι διαθέσιμη η υπηρεσία Google Sheets.")
            return
        
        # Check current attendance status from Google Sheets (not memory)
        attendance_status = await sheets_service.get_worker_attendance_status(worker_name)
        current_status = attendance_status['status']
        
        # If already checked in today, show current status
        if current_status == 'CHECKED_IN':
            check_in_time = attendance_status['time']
            await update.message.reply_text(
                f"✅ **Έχετε ήδη κάνει check-in σήμερα!**\n\n"
                f"**Ώρα check-in:** {check_in_time}\n\n"
                f"**Επόμενη ενέργεια:** Πατήστε 🚪 Check Out όταν τελειώσετε τη βάρδια.",
                parse_mode='Markdown'
            )
            return
        
        # If already completed today, show completion status
        elif current_status == 'COMPLETE':
            check_in_time = attendance_status['time']
            if '-' in check_in_time:
                check_in, check_out = check_in_time.split('-')
                await update.message.reply_text(
                    f"�� **Η βάρδια σας ολοκληρώθηκε!**\n\n"
                    f"**Check-in:** {check_in}\n"
                    f"**Check-out:** {check_out}\n\n"
                    f"**Επόμενη ενέργεια:** Μπορείτε να κάνετε check-in αύριο.",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"�� **Η βάρδια σας ολοκληρώθηκε!**\n\n"
                    f"**Ώρα:** {check_in_time}\n\n"
                    f"**Επόμενη ενέργεια:** Μπορείτε να κάνετε check-in αύριο.",
                    parse_mode='Markdown'
                )
            return
        
        # No need to check pending_actions - we use Google Sheets data instead
        
        # Get user ID for pending actions
        user_id = update.effective_user.id
        
        # Create location request keyboard
        location_keyboard = ReplyKeyboardMarkup([
            [KeyboardButton("📍 Στείλε την τοποθεσία μου", request_location=True)],
            [KeyboardButton("�� Πίσω στο μενού")]
        ], resize_keyboard=True, one_time_keyboard=True)
        
        # Store check-in request in global pending_actions (for location verification)
        import pytz
        greece_tz = pytz.timezone('Europe/Athens')
        pending_actions[user_id] = {
            'worker_name': worker_name,
            'action': 'checkin',
            'timestamp': datetime.now(greece_tz)
        }
        logger.info(f"🔍 DEBUG: Stored check-in pending action for user {user_id}: {pending_actions[user_id]}")
        logger.info(f"�� DEBUG: All pending actions: {pending_actions}")
        
        # Show minimal location request message
        await update.message.reply_text(
            f"📍 **Check-in για {worker_name}**\n\n"
            "**Πατήστε το κουμπί τοποθεσίας παρακάτω:**\n\n"
            "⚠️ Πρέπει να είστε μέσα σε 300m από το γραφείο",
            reply_markup=location_keyboard,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error during persistent check-in: {e}")
        await update.message.reply_text("❌ Σφάλμα κατά το check-in. Παρακαλώ δοκιμάστε ξανά.")


        async def handle_location_message(update: Update, context):
    """Handle location messages for check-in/out"""
    try:
        user = update.effective_user
        user_id = user.id
        
        # Check if user has a pending action
        pending_action = pending_actions.get(user_id)
        
        logger.info(f"🔍 DEBUG: Checking pending actions for user {user_id}")
        logger.info(f"🔍 DEBUG: Current pending actions: {pending_actions}")
        logger.info(f"🔍 DEBUG: User's pending action: {pending_action}")
        
        if not pending_action:
            # No pending action, ignore location
            logger.info(f"🔍 DEBUG: No pending action for user {user_id}, ignoring location")
            return
        
        # Get location from message
        if not update.message.location:
            await update.message.reply_text("❌ Παρακαλώ στείλτε την τοποθεσία σας (location), όχι κείμενο.")
            # Clear pending action for invalid location so user can try again
            pending_actions.pop(user_id, None)
            # Return to main menu even for invalid location
            await return_to_main_menu(update, context, user_id)
            return
        
        location = update.message.location
        latitude = location.latitude
        longitude = location.longitude
        
        logger.info(f"🔍 DEBUG: Received location from user {user_id}:")
        logger.info(f"🔍 DEBUG:   Raw location object: {location}")
        logger.info(f"�� DEBUG:   Latitude: {latitude}")
        logger.info(f"�� DEBUG:   Longitude: {longitude}")
        logger.info(f"🔍 DEBUG:   Location type: {type(latitude)}, {type(longitude)}")
        
        # Get services from context
        location_service = context.bot_data.get('location_service')
        if not location_service:
            logger.error("🔍 DEBUG: Location service not available in context")
            logger.error("Location service not available in context")
            await update.message.reply_text("❌ Σφάλμα: Δεν είναι διαθέσιμη η υπηρεσία τοποθεσίας.")
            # Clear pending action when service unavailable so user can try again
            pending_actions.pop(user_id, None)
            await return_to_main_menu(update, context, user_id)
            return
        
        logger.info(f"🔍 DEBUG: Location service found, calling is_within_office_zone...")
        # Verify location is within office zone
        location_result = location_service.is_within_office_zone(latitude, longitude)
        logger.info(f"🔍 DEBUG: Location verification result: {location_result}")
        
        if not location_result['is_within']:
            # Location outside zone - show error and return to main menu
            location_msg = location_service.format_location_message(location_result)
            await update.message.reply_text(location_msg, parse_mode='Markdown')
            
            # IMPORTANT: Clear pending action when location fails so user can try again
            pending_actions.pop(user_id, None)
            
            # Return to main menu after failed location check
            await return_to_main_menu(update, context, user_id)
            return
        
        # Location verified, proceed with action
        logger.info(f"🔍 DEBUG: Location verified, proceeding with action: {pending_action['action']}")
        if pending_action['action'] == 'checkin':
            logger.info(f"🔍 DEBUG: Calling complete_checkin for user {user_id}")
            await complete_checkin(update, context, pending_action, location_result)
        elif pending_action['action'] == 'checkout':
            logger.info(f"🔍 DEBUG: Calling complete_checkout for user {user_id}")
            await complete_checkout(update, context, pending_action, location_result)
        
        # Clear pending action
        logger.info(f"🔍 DEBUG: Clearing pending action for user {user_id}")
        pending_actions.pop(user_id, None)
        logger.info(f"🔍 DEBUG: Pending actions after clearing: {pending_actions}")
        
    except Exception as e:
        logger.error(f"Error handling location message: {e}")
        await update.message.reply_text("❌ Σφάλμα κατά την επεξεργασία της τοποθεσίας.")
        # Clear pending action on error so user can try again
        pending_actions.pop(user_id, None)
        # Return to main menu even on error
        await return_to_main_menu(update, context, user_id)






        def is_within_office_zone(self, latitude: float, longitude: float) -> Dict[str, any]:
    """Check if location is within office zone"""
    logger.info(f"🔍 DEBUG: is_within_office_zone called with user coordinates: lat={latitude}, lon={longitude}")
    logger.info(f"🔍 DEBUG: Office coordinates: lat={self.office_latitude}, lon={self.office_longitude}")
    logger.info(f"🔍 DEBUG: Office radius: {self.office_radius_meters} meters")
    
    try:
        # Calculate distance to office
        logger.info(f"🔍 DEBUG: Calling calculate_distance...")
        distance = self.calculate_distance(
            self.office_latitude, 
            self.office_longitude, 
            latitude, 
            longitude
        )
        
        logger.info(f"🔍 DEBUG: Distance calculated: {distance} meters")
        
        # Check if within radius
        is_within = distance <= self.office_radius_meters
        logger.info(f"🔍 DEBUG: Within radius check: {distance} <= {self.office_radius_meters} = {is_within}")
        
        result = {
            'is_within': is_within,
            'distance_meters': round(distance, 2),
            'office_lat': self.office_latitude,
            'office_lon': self.office_longitude,
            'user_lat': latitude,
            'user_lon': longitude,
            'radius_meters': self.office_radius_meters
        }
        
        logger.info(f"🔍 DEBUG: Final result: {result}")
        
        if is_within:
            logger.info(f"✅ Location verified: {distance:.2f}m from office")
        else:
            logger.warning(f"❌ Location outside zone: {distance:.2f}m from office (limit: {self.office_radius_meters}m)")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error calculating location: {e}")
        logger.error(f"🔍 DEBUG: Exception details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
        return {
            'is_within': False,
            'error': str(e),
            'distance_meters': -1
        }




        async def complete_checkin(update: Update, context, pending_data: dict, location_result: dict):
    """Complete check-in after location verification"""
    try:
        sheets_service = context.bot_data.get('sheets_service')
        location_service = context.bot_data.get('location_service')
        worker_name = pending_data['worker_name']
        
        # Use Greece timezone for check-in time
        import pytz
        greece_tz = pytz.timezone('Europe/Athens')
        current_time = datetime.now(greece_tz).strftime("%H:%M")
        
        # Update attendance sheet
        success = await sheets_service.update_attendance_cell(
            sheets_service.get_current_month_sheet_name(),
            worker_name,
            check_in_time=current_time
        )
        
        if success:
            # Create smart keyboard for check-in status
            smart_keyboard = create_smart_keyboard(worker_name, 'CHECKED_IN')
            
            # Get current date in Greece timezone for display
            current_date = datetime.now(greece_tz).strftime("%d/%m/%Y")
            
            message = f"""
✅ **Check-in επιτυχής!**

**Ώρα:** {current_time}
**Ημερομηνία:** {current_date}

**Τώρα μπορείτε να κάνετε check-out όταν τελειώσετε τη βάρδια!**
            """
            
            # Send success message with smart keyboard
            await update.message.reply_text(message, parse_mode='Markdown', reply_markup=smart_keyboard)
        else:
            await update.message.reply_text("❌ Σφάλμα κατά το check-in. Παρακαλώ δοκιμάστε ξανά.")
            # Clear pending action on failure so user can try again
            user_id = update.effective_user.id
            pending_actions.pop(user_id, None)
            
    except Exception as e:
        logger.error(f"Error completing check-in: {e}")
        await update.message.reply_text("❌ Σφάλμα κατά το check-in. Παρακαλώ δοκιμάστε ξανά.")
        # Clear pending action on error so user can try again
        user_id = update.effective_user.id
        pending_actions.pop(user_id, None)
        async def get_worker_attendance_status(self, worker_name: str) -> Dict:
    """Get worker's current attendance status for today"""
    if not self.service:
        return {'status': 'UNKNOWN', 'time': ''}
        
    try:
        sheet_name = self.get_current_month_sheet_name()
        
        # Ensure monthly sheet exists
        await self.ensure_monthly_sheet_exists()
        
        # Find worker row
        worker_row = await self.find_worker_row_in_monthly_sheet(sheet_name, worker_name)
        
        if worker_row is None:
            return {'status': 'NOT_REGISTERED', 'time': ''}
        
        # Get today's column
        today_col = self.get_today_column_letter()
        cell_range = f"{sheet_name}!{today_col}{worker_row}"
        
        # Read cell value
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range=cell_range
        ).execute()
        
        values = result.get('values', [])
        cell_value = values[0][0] if values and values[0] else ""
        
        # Determine status
        time = ""  # Initialize time variable
        if not cell_value:
            status = 'NOT_CHECKED_IN'
        elif cell_value.endswith('-'):
            status = 'CHECKED_IN'
            time = cell_value[:-1]  # Remove trailing dash
        elif '-' in cell_value:
            status = 'COMPLETE'
            time = cell_value
        else:
            status = 'UNKNOWN'
            time = cell_value
        
        return {
            'status': status,
            'time': time
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting attendance status: {e}")
        return {'status': 'ERROR', 'time': ''}