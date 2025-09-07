# Project Brief - NewRest Bot 2025

## Project Overview
**NewRest Bot 2025** is a Python-based Telegram bot system designed to manage worker registration, tracking, and daily attendance for a restaurant/retail operation. The system integrates with Google Sheets for data persistence and runs as a 24/7 webhook service on render.com.

## Core Purpose
- **Worker Registration Management**: Streamlined onboarding process with bilingual support (Greek/English)
- **Daily Attendance Tracking**: Real-time monitoring of worker presence and shifts
- **Document Management**: Track essential documents (AMKA, AFM, health certificates)
- **Status Workflow**: Manage worker status transitions (WAITING → APPROVED → ACTIVE)

## Key Requirements
1. **Bilingual Interface**: Full Greek/English language support
2. **Google Sheets Integration**: Real-time data synchronization across multiple sheets
3. **Telegram Bot Interface**: Interactive registration flow with buttons and text input
4. **24/7 Availability**: Webhook-based service running continuously
5. **Data Validation**: Cross-reference data between registration and worker sheets
6. **Admin Workflow**: Status management and approval processes

## Success Criteria
- Seamless worker registration experience
- Accurate daily attendance tracking
- Reliable Google Sheets data synchronization
- 99.9% uptime on render.com
- < 2 second response time for webhook processing

## Technical Constraints
- Python 3.11.0 runtime
- Flask web framework with async support
- Google Sheets API integration
- Telegram Bot API webhook architecture
- Render.com hosting platform
