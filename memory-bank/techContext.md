# Technical Context - NewRest Bot 2025

## Technology Stack

### Core Technologies
- **Python 3.11.0**: Primary runtime environment
- **Flask 2.3.3**: Web framework with async support
- **python-telegram-bot 20.7**: Telegram Bot API integration
- **gspread 5.12.0**: Google Sheets API wrapper
- **google-auth 2.23.0**: Google authentication services

### Supporting Libraries
- **requests 2.31.0**: HTTP client for external API calls
- **python-dotenv 1.0.0**: Environment variable management
- **google-auth-oauthlib 1.1.0**: OAuth2 authentication
- **google-auth-httplib2 0.1.1**: HTTP transport for Google APIs

## Development Setup

### Environment Requirements
```bash
# Python version
python-3.11.0

# Dependencies
pip install -r requirements.txt

# Environment variables (see .env template)
BOT_TOKEN=your_telegram_bot_token
BOT_USERNAME=your_bot_username
ADMIN_GROUP_ID=your_admin_group_id
GOOGLE_SHEETS_ID=your_sheets_id
GOOGLE_SERVICE_ACCOUNT_EMAIL=your_service_account_email
GOOGLE_PRIVATE_KEY=your_private_key
WEBHOOK_URL=your_webhook_url
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run the application
python app.py
```

### Production Deployment
- **Platform**: render.com
- **Runtime**: Python 3.11.0
- **Process**: `web: python app.py`
- **Port**: Dynamic (render.com assigns)
- **Uptime**: 24/7 with automatic restarts

## Technical Constraints

### 1. **Runtime Limitations**
- **Memory**: Limited by render.com free tier
- **CPU**: Single-threaded with async support
- **Storage**: No persistent storage (stateless design)

### 2. **API Rate Limits**
- **Telegram Bot API**: 30 messages per second
- **Google Sheets API**: 100 requests per 100 seconds per user
- **Mitigation**: Request queuing and error handling

### 3. **Network Constraints**
- **Webhook Timeout**: 60 seconds maximum
- **External API Timeouts**: 30 seconds default
- **Retry Logic**: Exponential backoff for failed requests

## Dependencies

### External Services
1. **Telegram Bot API**
   - **Purpose**: User interaction and messaging
   - **Authentication**: Bot token
   - **Endpoints**: Send messages, handle webhooks

2. **Google Sheets API**
   - **Purpose**: Data persistence and retrieval
   - **Authentication**: Service account with JSON key
   - **Scopes**: Spreadsheets and Drive access

3. **render.com Platform**
   - **Purpose**: Hosting and deployment
   - **Features**: Auto-deploy, health checks, logging
   - **Limitations**: Free tier resource constraints

### Internal Dependencies
- **Flask**: Web framework and routing
- **asyncio**: Asynchronous processing
- **logging**: Application monitoring
- **os**: Environment variable access

## Configuration Management

### Environment Variables
```python
# Required for operation
BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_USERNAME = os.getenv('BOT_USERNAME')
ADMIN_GROUP_ID = os.getenv('ADMIN_GROUP_ID')
GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID')
GOOGLE_SERVICE_ACCOUNT_EMAIL = os.getenv('GOOGLE_SERVICE_ACCOUNT_EMAIL')
GOOGLE_PRIVATE_KEY = os.getenv('GOOGLE_PRIVATE_KEY')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
```

### Google Sheets Configuration
- **Spreadsheet Structure**: 3 sheets (REGISTRATION, WORKERS, 2025/8)
- **Authentication**: Service account with JSON credentials
- **Permissions**: Read/write access to specific spreadsheet
- **Rate Limiting**: Built-in retry logic for API limits

## Security Considerations

### 1. **Authentication**
- **Telegram**: Bot token authentication
- **Google Sheets**: Service account with limited scope
- **Webhooks**: No authentication (public endpoints)

### 2. **Data Protection**
- **Environment Variables**: Sensitive data in environment
- **Google Sheets**: Data encrypted in transit and at rest
- **Logging**: No sensitive data in logs

### 3. **Access Control**
- **Bot Access**: Public (anyone can message)
- **Admin Functions**: Group-based access control
- **Data Access**: Service account permissions only

## Performance Characteristics

### Response Times
- **Health Check**: <100ms
- **Message Processing**: <2 seconds
- **Google Sheets Operations**: <5 seconds
- **Webhook Processing**: <10 seconds

### Scalability
- **Current Design**: Single instance, in-memory state
- **Bottlenecks**: Google Sheets API rate limits
- **Scaling Strategy**: Horizontal scaling with external state store

### Monitoring
- **Health Endpoints**: `/health`, `/test/telegram`, `/test/sheets`
- **Logging**: Structured logging with levels
- **Error Tracking**: Exception handling with context
