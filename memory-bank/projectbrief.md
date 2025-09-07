# Project Brief - NewRest Bot 2025

## Project Overview
**NewRest Bot 2025** is a Python webhook service running 24/7 on render.com that manages worker registration, tracking, and daily attendance through Google Sheets integration.

## Core Purpose
- **Worker Registration Management**: Collect and track personal data, documents, and employment status
- **Daily Attendance Tracking**: Monitor worker presence and shifts for specific periods (e.g., August 1-10, 2025)
- **Real-time Data Synchronization**: Webhook-based updates to Google Sheets for immediate data consistency
- **Bilingual Support**: Greek/English interface for international workforce

## Key Requirements
1. **24/7 Uptime**: Deployed on render.com for continuous operation
2. **Google Sheets Integration**: Real-time read/write operations across multiple sheets
3. **Telegram Bot Interface**: User-friendly registration and status checking
4. **Multi-language Support**: Greek and English interfaces
5. **Webhook Architecture**: RESTful API for external integrations
6. **Data Validation**: Cross-reference data between sheets for consistency

## Success Criteria
- Seamless worker registration flow with admin verification
- Real-time attendance tracking and reporting
- Reliable 24/7 operation with <2 second response times
- Accurate data synchronization across all Google Sheets
- User-friendly bilingual interface

## Project Scope
- **In Scope**: Registration flow, attendance tracking, Google Sheets integration, Telegram bot interface
- **Out of Scope**: Payment processing, advanced analytics, mobile app development
- **Future Considerations**: Email notifications, SMS integration, calendar management

## Technical Constraints
- Python 3.11.0 runtime
- Flask web framework with async support
- Google Sheets API v4
- Telegram Bot API
- render.com hosting platform
- Service account authentication for Google services
