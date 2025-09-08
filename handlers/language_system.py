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
        'edit_field': 'Click on any field above to edit it',
        # Working Console
        'welcome_message': 'Welcome, {name}!',
        'already_registered': 'You are already registered in the system.',
        'use_buttons_below': 'Use the buttons below the input field:',
        'working_console': 'Working Console',
        'welcome_back': 'Welcome back',
        'already_registered': 'You are already registered in the system.',
        'status_checked_in': 'Status: ✅ Checked In',
        'status_not_checked_in': 'Status: ⏸️ Not Checked In',
        'check_in_time': 'Check-in Time:',
        'todays_hours': "Today's Hours:",
        'location_verified': 'Location: Verified ✅',
        'ready_to_start': 'Ready to start your work session!',
        'check_in_required': 'Check In - Location Required',
        'check_out_required': 'Check Out - Location Required',
        'share_location_instructions': 'To check in/out, please share your current location.',
        'how_to_share_location': 'How to share location:',
        'tap_share_location': "Tap 'Share Location' below",
        'allow_location_access': 'Allow location access when prompted',
        'select_send_location': "Select 'Send Location'",
        'location_note': 'You must be within 500m of the work location to check in/out successfully.',
        'location_not_valid': 'Location Not Valid',
        'location_validation_message': 'You need to be within 500m of the work location to check in/out.',
        'location_validation_instructions': 'Please:',
        'make_sure_at_work': 'Make sure you are at the work location',
        'check_gps_signal': 'Check your GPS signal',
        'try_sharing_again': 'Try sharing location again',
        'location_verification_note': 'Location verification ensures accurate attendance tracking.',
        'already_checked_in': 'Already Checked In',
        'already_checked_in_message': "You're already checked in and working.",
        'use_check_out': 'Use "Check Out" when you finish your work session.',
        'not_checked_in': 'Not Checked In',
        'not_checked_in_message': 'You need to check in first before you can check out.',
        'use_check_in': 'Use "Check In" to start your work session.',
        'checked_in_successfully': 'Checked In Successfully',
        'checked_out_successfully': 'Checked Out Successfully',
        'time': 'Time:',
        'check_in': 'Check In',
        'check_out': 'Check Out',
        'total_hours': 'Total Hours:',
        'great_work_today': 'Great work today!',
        'contact': 'Contact',
        'contact_message': 'Crew Assistant: Coming Soon!',
        'contact_description': 'This feature will connect you directly with the crew assistant for any questions or support.',
        'contact_for_now': 'For now, please contact your supervisor directly.',
        'something_went_wrong': 'Something went wrong',
        'error_message': 'Sorry, there was an error processing your request.',
        'please_try': 'Please try:',
        'check_internet': 'Check your internet connection',
        'try_again': 'Try again in a moment',
        'contact_support': 'Contact support if the problem continues',
        'working_on_fix': "We're working to fix this issue."
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
        'edit_field': 'Κάντε κλικ σε οποιοδήποτε πεδίο παραπάνω για να το επεξεργαστείτε',
        # Working Console
        'welcome_message': 'Καλώς ήρθατε, {name}!',
        'already_registered': 'Είστε ήδη εγγεγραμμένος στο σύστημα.',
        'use_buttons_below': 'Χρησιμοποιήστε τα κουμπιά κάτω από το πεδίο εισαγωγής:',
        'working_console': 'Κονσόλα Εργασίας',
        'welcome_back': 'Καλώς ήρθατε',
        'already_registered': 'Είστε ήδη εγγεγραμμένος στο σύστημα.',
        'status_checked_in': 'Κατάσταση: ✅ Εγγεγραμμένος',
        'status_not_checked_in': 'Κατάσταση: ⏸️ Δεν Είστε Εγγεγραμμένος',
        'check_in_time': 'Ώρα Εγγραφής:',
        'todays_hours': 'Ώρες Σήμερα:',
        'location_verified': 'Τοποθεσία: Επαληθευμένη ✅',
        'ready_to_start': 'Έτοιμοι να ξεκινήσετε τη συνεδρία εργασίας σας!',
        'check_in_required': 'Εγγραφή - Απαιτείται Τοποθεσία',
        'check_out_required': 'Αποχώρηση - Απαιτείται Τοποθεσία',
        'share_location_instructions': 'Για να εγγραφείτε/αποχωρήσετε, παρακαλώ μοιραστείτε την τρέχουσα τοποθεσία σας.',
        'how_to_share_location': 'Πώς να μοιραστείτε την τοποθεσία:',
        'tap_share_location': "Πατήστε 'Μοιραστείτε Τοποθεσία' παρακάτω",
        'allow_location_access': 'Επιτρέψτε την πρόσβαση στην τοποθεσία όταν σας ζητηθεί',
        'select_send_location': "Επιλέξτε 'Αποστολή Τοποθεσίας'",
        'location_note': 'Πρέπει να είστε μέσα σε 500μ από την τοποθεσία εργασίας για να εγγραφείτε/αποχωρήσετε επιτυχώς.',
        'location_not_valid': 'Τοποθεσία Δεν Είναι Έγκυρη',
        'location_validation_message': 'Πρέπει να είστε μέσα σε 500μ από την τοποθεσία εργασίας για να εγγραφείτε/αποχωρήσετε.',
        'location_validation_instructions': 'Παρακαλώ:',
        'make_sure_at_work': 'Βεβαιωθείτε ότι είστε στην τοποθεσία εργασίας',
        'check_gps_signal': 'Ελέγξτε το σήμα GPS σας',
        'try_sharing_again': 'Δοκιμάστε να μοιραστείτε την τοποθεσία ξανά',
        'location_verification_note': 'Η επαλήθευση τοποθεσίας διασφαλίζει ακριβή παρακολούθηση παρουσίας.',
        'already_checked_in': 'Ήδη Εγγεγραμμένος',
        'already_checked_in_message': 'Είστε ήδη εγγεγραμμένος και εργάζεστε.',
        'use_check_out': 'Χρησιμοποιήστε "Αποχώρηση" όταν τελειώσετε τη συνεδρία εργασίας σας.',
        'not_checked_in': 'Δεν Είστε Εγγεγραμμένος',
        'not_checked_in_message': 'Πρέπει να εγγραφείτε πρώτα πριν μπορέσετε να αποχωρήσετε.',
        'use_check_in': 'Χρησιμοποιήστε "Εγγραφή" για να ξεκινήσετε τη συνεδρία εργασίας σας.',
        'checked_in_successfully': 'Εγγραφή Επιτυχής',
        'checked_out_successfully': 'Αποχώρηση Επιτυχής',
        'time': 'Ώρα:',
        'check_in': 'Εγγραφή',
        'check_out': 'Αποχώρηση',
        'total_hours': 'Συνολικές Ώρες:',
        'great_work_today': 'Καλή δουλειά σήμερα!',
        'contact': 'Επικοινωνία',
        'contact_message': 'Βοηθός Ομάδας: Έρχεται σύντομα!',
        'contact_description': 'Αυτή η λειτουργία θα σας συνδέσει απευθείας με τον βοηθό ομάδας για οποιεσδήποτε ερωτήσεις ή υποστήριξη.',
        'contact_for_now': 'Προς το παρόν, παρακαλώ επικοινωνήστε απευθείας με τον επόπτη σας.',
        'something_went_wrong': 'Κάτι πήγε στραβά',
        'error_message': 'Συγγνώμη, υπήρξε σφάλμα στην επεξεργασία του αιτήματός σας.',
        'please_try': 'Παρακαλώ δοκιμάστε:',
        'check_internet': 'Ελέγξτε τη σύνδεσή σας στο internet',
        'try_again': 'Δοκιμάστε ξανά σε λίγο',
        'contact_support': 'Επικοινωνήστε με την υποστήριξη αν το πρόβλημα συνεχίζεται',
        'working_on_fix': 'Εργαζόμαστε για να διορθώσουμε αυτό το πρόβλημα.'
    }
}

# Button options in both languages
BUTTON_OPTIONS = {
    'en': {
        'transportation': ['PUBLIC TRANSPORT', 'VEHICLE', 'BOTH'],
        'bank': ['EURO_BANK', 'ALPHA_BANK', 'PIRAEUS_BANK', 'NATIONALBANK'],
        'driving_license': ['YES', 'NO'],
        'language': ['Ελληνικά', 'English'],
        # Working Console buttons
        'check_in': 'Check In',
        'check_out': 'Check Out',
        'contact': 'Contact'
    },
    'gr': {
        'transportation': ['MMM', 'ΟΧΗΜΑ', 'ΚΑΙ ΤΑ ΔΥΟ'],
        'bank': ['EURO_BANK', 'ALPHA_BANK', 'PIRAEUS_BANK', 'NATIONALBANK'],
        'driving_license': ['ΝΑΙ', 'ΟΧΙ'],
        'language': ['Ελληνικά', 'English'],
        # Working Console buttons
        'check_in': 'Εγγραφή',
        'check_out': 'Αποχώρηση',
        'contact': 'Επικοινωνία'
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
