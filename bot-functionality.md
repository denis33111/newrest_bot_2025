# Bot Functionality

## Overview
The newrest_bot is a **Python webhook service** running **24/7 on render.com** that manages worker registration, tracking, and daily attendance through Google Sheets integration.

## Architecture
- **Platform**: Python Flask/FastAPI webhook service
- **Hosting**: render.com (24/7 uptime)
- **Integration**: Google Sheets API via webhooks
- **Method**: Webhook-based real-time updates

## Core Features

### 🔄 **Registration Management**
- **New Worker Registration**: Add workers to REGISTRATION sheet
- **Document Tracking**: Monitor AMKA, AFM, health certificates
- **Status Updates**: Track WAITING → APPROVED → ACTIVE status
- **Reminder System**: Pre-course and day-of-course notifications

### 👥 **Worker Database**
- **Worker Profiles**: Maintain NAME, ID, STATUS, LANGUAGE
- **Cross-sheet Sync**: Link REGISTRATION data to WORKERS sheet
- **Status Monitoring**: Track employment status changes

### 📅 **Daily Tracking**
- **Attendance Logging**: Record daily presence (Aug 1-10, 2025)
- **Monthly Sheets**: Auto-create new monthly tracking sheets
- **Data Validation**: Ensure consistent name matching across sheets

## Webhook Endpoints

### Registration Webhooks
```
POST /webhook/register
POST /webhook/update-status
POST /webhook/update-documents
```

### Worker Management
```
POST /webhook/add-worker
POST /webhook/update-worker
POST /webhook/worker-status
```

### Daily Tracking
```
POST /webhook/attendance
POST /webhook/daily-log
POST /webhook/monthly-summary
```

## Data Flow
```
Webhook Request → Python Service → Google Sheets API → Response
     ↓
Status Update → Logging → Notification
```

## Integration Points

### Google Sheets API
- **Authentication**: Service account with sheet access
- **Multi-sheet Operations**: REGISTRATION, WORKERS, monthly sheets
- **Real-time Updates**: Webhook-triggered modifications
- **Data Validation**: Cross-reference between sheets

### External Services
- **Email Notifications**: Course reminders and status updates
- **SMS Integration**: Critical status changes
- **Calendar Integration**: Course date management

## Error Handling
- **Webhook Validation**: Verify incoming data format
- **Sheet Access Errors**: Handle API rate limits
- **Data Conflicts**: Resolve duplicate entries
- **24/7 Monitoring**: Automatic retry and recovery

## Performance Metrics
- **Response Time**: < 2 seconds for webhook processing
- **Uptime**: 99.9% (render.com SLA)
- **Data Accuracy**: Real-time validation and sync
- **Scalability**: Handle multiple concurrent webhooks
