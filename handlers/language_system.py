#!/usr/bin/env python3
"""
Language System
Handles bilingual interface (Greek/English)
"""

# Language constants
LANGUAGES = {
    'en': 'English',
    'gr': 'Ελληνικά'
}

# Registration questions in both languages
REGISTRATION_QUESTIONS = {
    'en': {
        'language_selection': 'Please select language',
        'full_name': 'What is your full name?',
        'age': 'What is your age?',
        'phone': 'What is your phone number?',
        'email': 'What is your email?',
        'address': 'In which area do you live?',
        'transportation': 'How will you go to work?',
        'bank': 'Select bank:',
        'driving_license': 'Do you have a driving license?',
        'review_title': 'Information Review:',
        'confirm_registration': 'Confirm Registration',
        'edit_field': 'Click on any field above to edit it'
    },
    'gr': {
        'language_selection': 'Παρακαλώ επιλέξτε γλώσσα',
        'full_name': 'Ποιο είναι το πλήρες όνομά σας;',
        'age': 'Ποια είναι η ηλικία σας;',
        'phone': 'Ποιος είναι ο αριθμός τηλεφώνου σας;',
        'email': 'Ποιο είναι το email σας;',
        'address': 'Σε ποια περιοχή μένετε;',
        'transportation': 'Πώς θα πηγαίνετε στη δουλειά;',
        'bank': 'Επιλέξτε τράπεζα:',
        'driving_license': 'Έχετε δίπλωμα οδήγησης;',
        'review_title': 'Επιθεώρηση Πληροφοριών:',
        'confirm_registration': 'Επιβεβαίωση Εγγραφής',
        'edit_field': 'Κάντε κλικ σε οποιοδήποτε πεδίο παραπάνω για να το επεξεργαστείτε'
    }
}

# Button options in both languages
BUTTON_OPTIONS = {
    'en': {
        'transportation': ['PUBLIC TRANSPORT', 'VEHICLE', 'BOTH'],
        'bank': ['EURO_BANK', 'ALPHA_BANK', 'PIRAEUS_BANK', 'NATIONALBANK'],
        'driving_license': ['YES', 'NO'],
        'language': ['Ελληνικά', 'English']
    },
    'gr': {
        'transportation': ['MMM', 'ΟΧΗΜΑ', 'ΚΑΙ ΤΑ ΔΥΟ'],
        'bank': ['EURO_BANK', 'ALPHA_BANK', 'PIRAEUS_BANK', 'NATIONALBANK'],
        'driving_license': ['ΝΑΙ', 'ΟΧΙ'],
        'language': ['Ελληνικά', 'English']
    }
}

def get_text(language, key):
    """Get text in specified language"""
    return REGISTRATION_QUESTIONS.get(language, {}).get(key, key)

def get_buttons(language, category):
    """Get button options in specified language"""
    return BUTTON_OPTIONS.get(language, {}).get(category, [])

def get_language_from_text(text):
    """Detect language from user input"""
    if text in ['Ελληνικά', 'gr', 'greek']:
        return 'gr'
    elif text in ['English', 'en', 'english']:
        return 'en'
    return 'gr'  # Default to Greek
