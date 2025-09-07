# NewRest Bot 2025

A Python webhook service running 24/7 on render.com that manages worker registration, tracking, and daily attendance through Google Sheets integration.

## Features

- **Worker Registration**: Manage personal data and document tracking
- **Daily Attendance**: Track worker presence and shifts
- **Google Sheets Integration**: Real-time data synchronization
- **Webhook API**: RESTful endpoints for external integrations

## Architecture

- **Platform**: Python Flask/FastAPI webhook service
- **Hosting**: render.com (24/7 uptime)
- **Integration**: Google Sheets API via webhooks
- **Method**: Webhook-based real-time updates

## Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables in `.env`
4. Run the service: `python app.py`

## Documentation

- [Google Sheets Structure](google-sheets-structure.md)
- [Bot Functionality](bot-functionality.md)
