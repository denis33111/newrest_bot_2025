# Technical Context - NewRest Bot 2025

## Technology Stack

### Core Framework
- **Python 3.11.0**: Runtime environment
- **Flask 2.3.3**: Web framework with async support
- **python-telegram-bot 20.7**: Telegram Bot API integration

### Data Layer
- **Google Sheets API**: Primary data storage
- **gspread 5.12.0**: Python Google Sheets client
- **google-auth 2.23.0**: Authentication library

### Supporting Libraries
- **requests 2.31.0**: HTTP client
- **python-dotenv 1.0.0**: Environment variable management
- **google-auth-oauthlib 1.1.0**: OAuth2 authentication
- **google-auth-httplib2 0.1.1**: HTTP transport for auth

## Development Environment

### Project Structure
```
newrest_bot/
├── app.py                    # Main Flask application
├── handlers/                 # Message and flow handlers
│   ├── message_handler.py    # Telegram message routing
│   ├── registration_flow.py  # Registration process
│   └── language_system.py    # Bilingual support
├── services/                 # External service integrations
│   ├── telegram_bot.py       # Telegram API operations
│   └── google_sheets.py      # Google Sheets operations
├── requirements.txt          # Python dependencies
├── Procfile                  # Render.com deployment
├── runtime.txt              # Python version specification
└── memory-bank/             # Project documentation
```

### Environment Variables
- `BOT_TOKEN`: Telegram bot authentication
- `BOT_USERNAME`: Bot username for identification
- `ADMIN_GROUP_ID`: Admin group for notifications
- `GOOGLE_SHEETS_ID`: Target spreadsheet identifier
- `GOOGLE_SERVICE_ACCOUNT_EMAIL`: Service account email
- `GOOGLE_PRIVATE_KEY`: Service account private key
- `WEBHOOK_URL`: Telegram webhook endpoint

## Deployment Configuration

### Render.com Setup
- **Runtime**: Python 3.11.0
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`
- **Environment**: Production with environment variables

### Google Sheets Configuration
- **Service Account**: Automated authentication
- **Spreadsheet Access**: Multi-sheet operations
- **API Scopes**: Spreadsheets and Drive access
- **Rate Limiting**: Respects Google API quotas

## Data Architecture

### Google Sheets Structure
1. **REGISTRATION Sheet**: Personal data and document tracking
2. **WORKERS Sheet**: Active worker management
3. **Monthly Sheets**: Daily attendance tracking (e.g., 2025/8)

### Data Flow
```
Telegram Message → Flask Webhook → Google Sheets API → Data Update
```

## Performance Considerations

### Async Processing
- **Event Loop Management**: Proper async/await usage
- **Non-blocking Operations**: Telegram and Google Sheets calls
- **Error Handling**: Graceful failure management

### Scalability
- **Webhook Architecture**: Stateless request processing
- **Database Integration**: Google Sheets as primary storage
- **Caching**: Minimal state management for performance

## Security Measures

### Authentication
- **Service Account**: Google Sheets API access
- **Environment Variables**: Secure credential storage
- **Webhook Validation**: Telegram message verification

### Data Protection
- **Input Sanitization**: User data validation
- **Error Masking**: No sensitive data exposure
- **Logging**: Comprehensive audit trail

## Monitoring and Logging

### Health Checks
- `/health`: Basic service status
- `/test/telegram`: Bot connectivity test
- `/test/sheets`: Google Sheets connectivity test
- `/test/all`: Complete system validation

### Logging Strategy
- **Level**: INFO for normal operations
- **Error Tracking**: Comprehensive exception logging
- **User Actions**: Registration and status changes
- **System Events**: Webhook and API interactions
