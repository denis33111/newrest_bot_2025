# System Patterns - NewRest Bot 2025

## Architecture Overview
The system follows a **webhook-based microservice architecture** with clear separation of concerns:

```
Telegram Bot API → Flask Webhook → Handler Layer → Service Layer → Google Sheets API
```

## Key Technical Decisions

### 1. **Webhook Architecture**
- **Pattern**: Event-driven webhook processing
- **Rationale**: Real-time updates, scalable, stateless
- **Implementation**: Flask webhook endpoints with async processing

### 2. **Handler-Service Separation**
- **Pattern**: Layered architecture with clear boundaries
- **Handlers**: Message routing, flow management, user interaction
- **Services**: External integrations, data persistence, business logic

### 3. **State Management**
- **Pattern**: In-memory state for active flows
- **Implementation**: `active_registrations` dictionary for ongoing registrations
- **Rationale**: Simple, fast, suitable for current scale

## Component Relationships

### Core Components
```
app.py (Flask App)
├── handlers/
│   ├── message_handler.py (Message routing)
│   ├── registration_flow.py (Registration logic)
│   └── language_system.py (I18n support)
└── services/
    ├── telegram_bot.py (Telegram integration)
    └── google_sheets.py (Sheets integration)
```

### Data Flow Patterns
1. **Registration Flow**: User → Telegram → Handler → Service → Google Sheets
2. **Status Check**: User → Telegram → Handler → Service → Google Sheets → Response
3. **Admin Operations**: External → Webhook → Service → Google Sheets

## Design Patterns in Use

### 1. **State Machine Pattern**
- **Implementation**: RegistrationFlow class with step-based progression
- **States**: Language → Personal Info → Selections → Review → Confirmation
- **Transitions**: Clear state transitions with validation

### 2. **Strategy Pattern**
- **Implementation**: Language system with different text/button strategies
- **Usage**: Dynamic content based on user language preference

### 3. **Repository Pattern**
- **Implementation**: Google Sheets service abstracts data access
- **Benefits**: Centralized data operations, easy testing, consistent interface

### 4. **Factory Pattern**
- **Implementation**: Handler creation based on message type
- **Usage**: Dynamic handler instantiation for different flows

## Error Handling Patterns

### 1. **Graceful Degradation**
- **Implementation**: Try-catch blocks with fallback responses
- **Example**: Google Sheets errors → User-friendly error messages

### 2. **Circuit Breaker**
- **Implementation**: Connection retry logic in services
- **Usage**: Prevent cascading failures from external APIs

### 3. **Logging Strategy**
- **Implementation**: Structured logging with context
- **Levels**: INFO for normal flow, ERROR for failures, DEBUG for troubleshooting

## Data Patterns

### 1. **Data Validation**
- **Pattern**: Input validation at handler level
- **Implementation**: Type checking, format validation, business rule validation

### 2. **Data Transformation**
- **Pattern**: Handler-to-Service data mapping
- **Implementation**: Convert Telegram data to Google Sheets format

### 3. **Data Consistency**
- **Pattern**: Single source of truth (Google Sheets)
- **Implementation**: All data operations go through Google Sheets service

## Integration Patterns

### 1. **Webhook Processing**
- **Pattern**: Asynchronous webhook handling
- **Implementation**: Event loop management for async operations

### 2. **External API Integration**
- **Pattern**: Service abstraction layer
- **Implementation**: Telegram and Google Sheets services with error handling

### 3. **Configuration Management**
- **Pattern**: Environment-based configuration
- **Implementation**: Environment variables for all external dependencies
