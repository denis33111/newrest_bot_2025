# System Patterns - NewRest Bot 2025

## Architecture Overview
```
Telegram Bot API → Flask Webhook → Google Sheets API
       ↓                ↓              ↓
   User Interface → Message Handler → Data Storage
```

## Core Components

### 1. Flask Application (`app.py`)
- **Webhook Endpoints**: `/webhook` for Telegram updates
- **Health Checks**: `/health`, `/test/telegram`, `/test/sheets`, `/test/all`
- **Async Support**: Event loop management for Telegram operations
- **Error Handling**: Comprehensive logging and error responses

### 2. Message Handler (`handlers/message_handler.py`)
- **Message Routing**: Directs messages to appropriate flows
- **Registration Management**: Tracks active registration sessions
- **Status Checking**: Validates user status in Google Sheets
- **Callback Handling**: Manages button interactions

### 3. Registration Flow (`handlers/registration_flow.py`)
- **State Management**: Tracks registration progress through steps
- **Data Collection**: Handles both text input and button selections
- **Review System**: Allows editing before final submission
- **Google Sheets Integration**: Saves completed registration data

### 4. Language System (`handlers/language_system.py`)
- **Bilingual Support**: Greek/English text and button options
- **Dynamic Content**: Language-specific question sets
- **User Detection**: Automatic language preference handling

### 5. Telegram Service (`services/telegram_bot.py`)
- **Bot Operations**: Message sending and webhook setup
- **Console Messages**: Working user interface
- **Error Messaging**: User-friendly error communication

### 6. Google Sheets Service (`services/google_sheets.py`)
- **Authentication**: Service account credentials management
- **Multi-sheet Operations**: REGISTRATION, WORKERS, monthly sheets
- **Data Validation**: User status checking and data integrity
- **Real-time Updates**: Immediate data synchronization

## Design Patterns

### Registration Flow Pattern
```
Language Selection → Personal Data → Selection Questions → Review → Confirmation
```

### State Management Pattern
- **Active Registrations**: Dictionary tracking user sessions
- **Step Progression**: Sequential data collection
- **Data Persistence**: Temporary storage during registration

### Error Handling Pattern
- **Graceful Degradation**: Fallback messages for failures
- **Logging**: Comprehensive error tracking
- **User Feedback**: Clear error communication

### Data Flow Pattern
```
User Input → Validation → Google Sheets → Status Update → User Notification
```

## Integration Patterns

### Google Sheets Integration
- **Service Account**: Secure API authentication
- **Multi-sheet Access**: REGISTRATION, WORKERS, monthly sheets
- **Data Mapping**: Column-specific data placement
- **Error Recovery**: Retry mechanisms for API failures

### Telegram Integration
- **Webhook Architecture**: Real-time message processing
- **Button Interactions**: Inline keyboard callbacks
- **Message Types**: Text, buttons, and status updates
- **Async Processing**: Non-blocking message handling

## Security Patterns
- **Environment Variables**: Secure credential management
- **Input Validation**: User data sanitization
- **Error Masking**: No sensitive data in error messages
- **Rate Limiting**: Google Sheets API quota management
