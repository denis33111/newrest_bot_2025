#!/usr/bin/env python3
"""
Registration Flow Handler
Manages the complete registration process
"""

import os
import logging
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from handlers.language_system import get_text, get_buttons, get_language_from_text
from services.google_sheets import save_registration_data, save_worker_data
from handlers.admin_evaluation import AdminEvaluation

logger = logging.getLogger(__name__)

class RegistrationFlow:
    def __init__(self, user_id, language='gr'):
        self.user_id = user_id
        self.language = language
        self.data = {}
        self.current_step = 0
        self.bot_token = os.getenv('BOT_TOKEN')
    
    async def start_registration(self):
        """Start the registration process"""
        self.current_step = 1
        await self.show_language_selection()
    
    async def show_language_selection(self):
        """Show language selection screen"""
        keyboard = [
            [InlineKeyboardButton("Ελληνικά", callback_data="lang_gr")],
            [InlineKeyboardButton("English", callback_data="lang_en")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"**1. Language Selection**\n\n{get_text('en', 'language_selection')}"
        
        bot = Bot(token=self.bot_token)
        await bot.send_message(
            chat_id=self.user_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def handle_language_selection(self, callback_data):
        """Handle language selection"""
        if callback_data == "lang_gr":
            self.language = 'gr'
        elif callback_data == "lang_en":
            self.language = 'en'
        
        self.current_step = 2
        await self.show_personal_info_questions()
    
    async def show_personal_info_questions(self):
        """Show personal information questions (text input)"""
        questions = [
            ('full_name', 'full_name'),
            ('age', 'age'),
            ('phone', 'phone'),
            ('email', 'email'),
            ('address', 'address')
        ]
        
        for field, question_key in questions:
            if field not in self.data:
                await self.ask_text_question(field, question_key)
                return
    
    async def ask_text_question(self, field, question_key):
        """Ask a text input question"""
        question = get_text(self.language, question_key)
        message = f"**{self.current_step}. {question}**"
        
        bot = Bot(token=self.bot_token)
        await bot.send_message(
            chat_id=self.user_id,
            text=message,
            parse_mode='Markdown'
        )
    
    async def handle_text_answer(self, text):
        """Handle text input answer"""
        logger.info(f"Handling text answer: '{text}' for step {self.current_step}, data: {self.data}")
        
        if self.current_step == 2:
            # Personal info questions
            if 'full_name' not in self.data:
                self.data['full_name'] = text
                logger.info(f"Set full_name: {text}, asking for age")
                await self.ask_text_question('age', 'age')
            elif 'age' not in self.data:
                self.data['age'] = text
                logger.info(f"Set age: {text}, asking for phone")
                await self.ask_text_question('phone', 'phone')
            elif 'phone' not in self.data:
                self.data['phone'] = text
                logger.info(f"Set phone: {text}, asking for email")
                await self.ask_text_question('email', 'email')
            elif 'email' not in self.data:
                self.data['email'] = text
                logger.info(f"Set email: {text}, asking for address")
                await self.ask_text_question('address', 'address')
            elif 'address' not in self.data:
                self.data['address'] = text
                logger.info(f"Set address: {text}, moving to step 3")
                self.current_step = 3
                await self.show_selection_questions()
    
    async def show_selection_questions(self):
        """Show selection questions (buttons)"""
        if 'transportation' not in self.data:
            await self.ask_selection_question('transportation', 'transportation')
        elif 'bank' not in self.data:
            await self.ask_selection_question('bank', 'bank')
        elif 'driving_license' not in self.data:
            await self.ask_selection_question('driving_license', 'driving_license')
        else:
            self.current_step = 4
            await self.show_review_screen()
    
    async def ask_selection_question(self, field, question_key):
        """Ask a selection question with buttons"""
        question = get_text(self.language, question_key)
        buttons = get_buttons(self.language, field)
        
        keyboard = []
        for button in buttons:
            keyboard.append([InlineKeyboardButton(button, callback_data=f"{field}_{button}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"**{self.current_step}. {question}**"
        
        bot = Bot(token=self.bot_token)
        await bot.send_message(
            chat_id=self.user_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def handle_selection_answer(self, callback_data):
        """Handle selection answer"""
        # Handle special case for driving_license (has underscore in field name)
        if callback_data.startswith('driving_license_'):
            field = 'driving_license'
            value = callback_data.replace('driving_license_', '')
            # Convert English to Greek for consistency
            if value == 'YES':
                value = 'ΝΑΙ'
            elif value == 'NO':
                value = 'ΟΧΙ'
        else:
            field, value = callback_data.split('_', 1)
        
        self.data[field] = value
        logger.info(f"Set {field}: {value}, current data: {self.data}")
        
        if field == 'transportation':
            logger.info("Asking for bank selection")
            await self.ask_selection_question('bank', 'bank')
        elif field == 'bank':
            logger.info("Asking for driving license selection")
            await self.ask_selection_question('driving_license', 'driving_license')
        elif field == 'driving_license':
            logger.info("All selections complete, showing review screen")
            self.current_step = 4
            await self.show_review_screen()
    
    async def show_review_screen(self):
        """Show review screen with edit options"""
        review_text = f"*4. Review & Confirmation*\n\n{get_text(self.language, 'review_title')}\n\n"
        
        # Add all collected data with edit buttons
        fields = [
            ('full_name', 'NAME'),
            ('age', 'AGE'),
            ('phone', 'PHONE'),
            ('email', 'EMAIL'),
            ('address', 'ADDRESS'),
            ('transportation', 'TRANSPORT'),
            ('bank', 'BANK'),
            ('driving_license', 'DRIVING LICENSE')
        ]
        
        for field, label in fields:
            value = self.data.get(field, 'Not set')
            # Escape special characters for Markdown
            value = str(value).replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace('`', '\\`')
            review_text += f"*{label}:* {value}\n"
        
        review_text += f"\n{get_text(self.language, 'edit_field')}"
        
        # Create edit buttons
        keyboard = []
        for field, label in fields:
            keyboard.append([InlineKeyboardButton(f"Edit {label}", callback_data=f"edit_{field}")])
        
        # Add confirmation button
        keyboard.append([InlineKeyboardButton(
            get_text(self.language, 'confirm_registration'),
            callback_data="confirm_registration"
        )])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        bot = Bot(token=self.bot_token)
        await bot.send_message(
            chat_id=self.user_id,
            text=review_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def handle_edit_request(self, callback_data):
        """Handle edit request"""
        field = callback_data.replace('edit_', '')
        
        if field in ['full_name', 'age', 'phone', 'email', 'address']:
            # Text input fields
            question_key = field
            await self.ask_text_question(field, question_key)
        else:
            # Selection fields
            question_key = field
            await self.ask_selection_question(field, question_key)
    
    async def confirm_registration(self):
        """Confirm and save registration data"""
        # Add user ID and language
        self.data['user_id'] = self.user_id
        self.data['language'] = self.language
        self.data['status'] = 'WAITING'
        
        # Save to Google Sheets
        registration_success = save_registration_data(self.data)
        worker_success = save_worker_data(self.data)
        
        success = registration_success and worker_success
        
        if success:
            # Store candidate data for admin evaluation
            from handlers.message_handler import candidate_data_storage
            candidate_data_storage[self.user_id] = self.data.copy()
            
            # Notify admin group
            admin_eval = AdminEvaluation(self.user_id, self.data)
            await admin_eval.notify_admin_group()
            
            # Send success message based on language
            if self.language == 'gr':
                message = """🎉 Συγχαρητήρια! Περάσατε με επιτυχία το πρώτο στάδιο.

Στο δεύτερο στάδιο θα περάσετε από συνέντευξη με τη Newrest.

Για την ημέρα και ώρα της συνέντευξης θα ενημερωθείτε από έναν συνάδελφό μας.

📍 Τοποθεσία Newrest: https://maps.app.goo.gl/f5ttxdDEyoU6TBi77

📋 Έγγραφα για εργασία:

• Έγχρωμη φωτογραφία ταυτότητας μπροστά και πίσω όψη.

• Αντίγραφο ποινικού μητρώου.
Πληκτρολογούμε στο Google: αντίγραφο ποινικού μητρώου, επιλέγουμε το πρώτο, ακολουθούμε τα βήματα, συνδεόμαστε με τους κωδικούς taxisnet, επιλέγουμε ΝΑΙ κάτω κάτω στις μπάρες, γίνεται η αίτηση και στέλνουμε φωτογραφία το QR code.
Ενημερώνουμε σε κάθε περίπτωση αν δεν μπορεί να βγει το αρχείο με αυτό τον τρόπο.

• Πιστοποιητικό υγείας.
Εάν δεν έχουμε κάνει ποτέ ή έχουμε κάνει και έχουν περάσει πέντε χρόνια, τότε το βγάζουμε εμείς.

• Υπεύθυνη δήλωση ποινικού μητρώου.
Το αρχείο που σας έχει αποσταλεί, το επικυρώνουμε με Ψηφιακή βεβαίωση εγγράφου στο gov.gr (υπηρεσία: "Ψηφιακή βεβαίωση εγγράφου"). Μπορείτε να πάτε απευθείας εδώ: https://www.gov.gr/ipiresies/polites-kai-kathemerinoteta/psephiaka-eggrapha-gov-gr/psephiake-bebaiose-eggraphou
Πληκτρολογούμε στο Google: Ψηφιακή βεβαίωση εγγράφου, επιλέγουμε το πρώτο, ακολουθούμε τα βήματα, συνδεόμαστε, ανεβάζουμε το αρχείο στο αντίστοιχο πεδίο, επιλέγουμε υπογραφή στα ελληνικά και ολοκληρώνουμε με τον κωδικό SMS. Βγάζουμε καλή φωτογραφία το QR code και το στέλνουμε.

• ΑΦΜ, ΑΜΑ, ΑΜΚΑ και μία διεύθυνση.

📄 Υπεύθυνη δήλωση ποινικού μητρώου: https://newrest-bot-2025.onrender.com/download/criminal_record_form.pdf

Ευχαριστούμε! Παρακαλώ προχωρήστε στο επόμενο βήμα όπως σας ενημερώσαμε."""
            else:
                message = """🎉 Congratulations! You have successfully passed the first stage.

In the second stage you will go through an interview with Newrest.

You will be informed about the day and time of the interview by one of our colleagues.

📍 Newrest Location: https://maps.app.goo.gl/f5ttxdDEyoU6TBi77

📋 Documents for work:

• Color ID photo front and back.

• Copy of criminal record.
We type in Google: copy of criminal record, select the first one, follow the steps, connect with the TAXISnet codes, select YES at the bottom of the bars; when the application is made please send a photo of the QR code. Please let us know in case you cannot get the file in this way.

• Health certificate.
If you have never done it or if you have done it but it has been five years, we will get it for you.

• Criminal record certificate.
The file that has been sent to you can be validated using the gov.gr service "Digital document certification". Direct link: https://www.gov.gr/en/ipiresies/polites-kai-kathemerinoteta/psephiaka-eggrapha-gov-gr/psephiake-bebaiose-eggraphou
Follow the steps: connect with TAXISnet, upload the file, choose signature in Greek, request SMS code, enter it and download the certified document. Then send us a clear photo of the QR code.

• AFM, AMA, AMKA and your home address.

📄 Criminal record declaration form: https://newrest-bot-2025.onrender.com/download/criminal_record_form.pdf

Thank you! Please come to the next step as instructed."""
            
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=self.user_id,
                text=message,
                parse_mode='Markdown'
            )
        else:
            message = "❌ **Registration Failed**\n\nThere was an error saving your registration. Please try again."
            bot = Bot(token=self.bot_token)
            await bot.send_message(
                chat_id=self.user_id,
                text=message,
                parse_mode='Markdown'
            )
