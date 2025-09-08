# Google Sheets Structure

## Overview
This document describes the structure and organization of the Google Sheets used by the newrest_bot - a Python webhook service running 24/7 on render.com.

## Exact Sheet Structure

### Sheet 1: REGISTRATION
**Purpose**: Personal data collection and document tracking

#### Detailed Row Structure:
- **Row 1**: 
  - A1:K1 = Merged cell with "PERSONAL DATA"
  - N2:P2 = Merged cell with "DOCUMENTS"
  - S1:T1 = Merged cell with "PROCESS EVENTS"

- **Row 2**: All column headers

#### Complete Column Structure (Row 2):
| Column | Header | Type | Description | Color |
|--------|--------|------|-------------|-------|
| A | LANGUAGE | Text | User language preference | Light Blue |
| B | user id | Number | Unique user identifier | Light Blue |
| C | WORKING | Text | Employment status | Light Green |
| D | NAME | Text | Full name | Light Green |
| E | AGE | Number | Age in years | Light Green |
| F | PHONE | Text | Phone number | Light Green |
| G | EMAIL | Text | Email address | Light Green |
| H | ADRESS | Text | Physical address (typo) | Light Green |
| I | TRANSPORT | Text | Transportation method | Light Green |
| J | BANK | Text | Banking information | Light Green |
| K | DR LICENCE NO | Text | Driver's license number | Light Green |
| L | CRIM | Text | Criminal record status | Light Yellow |
| M | HEALTH CERT. | Text | Health certificate status | Light Yellow |
| N | AMKA | Text | Greek social security number | Light Yellow |
| O | AMA | Text | Medical association number | Light Yellow |
| P | AFM | Text | Tax identification number | Light Yellow |
| Q | STATUS | Text | Registration status (WAITING, etc.) | Light Orange |
| R | COURSE_DATE | Date | Course enrollment date | Light Orange |
| S | PRE_COURSE_REMINDER | Text | Pre-course notification status | Light Orange |
| T | DAY_COURSE_REMINDER | Text | Day-of-course reminder status | Light Orange |
| U | FIRST_REMINDER_SENT | Text | First reminder sent status | Light Orange |
| V | SECOND_REMINDER_SENT | Text | Second reminder sent status | Light Orange |
| W | FIRST_REMINDER_RESPONSE | Text | First reminder response (YES/NO) | Light Orange |
| X | RETRY_COUNT | Number | Location validation retry count | Light Yellow |

#### Section Headers:
- **A1:K1**: "PERSONAL DATA" (merged)
- **N2:P2**: "DOCUMENTS" (merged)
- **S1:T1**: "PROCESS EVENTS" (merged)

#### Data Rows:
- **Row 3+**: Actual data entries
- **Sample Row 3**: 
  - A3: "gr" (Greek language)
  - B3: "5711220944" (user ID)
  - E3: "2" (age)
  - F3: "2" (phone)
  - G3: "2" (email)
  - H3: "2" (address)
  - I3: "BOTH" (transport)
  - J3: "NATIONALBANK" (bank)
  - Q3: "WAITING" (status)

#### Color Coding Details:
- **Light Blue (A-B)**: Primary identifiers
- **Light Green (C-K)**: Personal data section
- **Light Yellow (L-P)**: Documents section
- **Light Orange (Q-T)**: Process events section

### Sheet 2: WORKERS
**Purpose**: Worker management and tracking

#### Row Structure:
- **Row 1**: Column headers

#### Column Structure (Row 1):
| Column | Header | Type | Description |
|--------|--------|------|-------------|
| A | NAME | Text | Worker's full name |
| B | ID | Number | Worker ID number |
| C | STATUS | Text | Employment status |
| D | LANGUAGE | Text | Worker's language |

#### Data Rows:
- **Row 2+**: Worker data entries
- **Range**: A1:D29 (highlighted area)

### Sheet 3: 2025/8 (August 2025)
**Purpose**: Daily attendance/shift tracking

#### Row Structure:
- **Row 1**: Merged cells B1:K1 = "Αυγούστου 2025" (August 2025)
- **Row 2**: Date headers

#### Column Structure:
| Column | Header | Type | Description |
|--------|--------|------|-------------|
| A | NAME | Text | Worker/participant name |
| B | 8/1/2025 | Text/Number | August 1st tracking |
| C | 8/2/2025 | Text/Number | August 2nd tracking |
| D | 8/3/2025 | Text/Number | August 3rd tracking |
| E | 8/4/2025 | Text/Number | August 4th tracking |
| F | 8/5/2025 | Text/Number | August 5th tracking |
| G | 8/6/2025 | Text/Number | August 6th tracking |
| H | 8/7/2025 | Text/Number | August 7th tracking |
| I | 8/8/2025 | Text/Number | August 8th tracking |
| J | 8/9/2025 | Text/Number | August 9th tracking |
| K | 8/10/2025 | Text/Number | August 10th tracking |

#### Data Rows:
- **Row 3+**: Daily attendance data
- **Range**: A1:K29 (visible area)

## Color Coding System
- **Light Blue**: Primary identifiers (USER_ID, NAME columns)
- **Light Green**: Personal data and documents section
- **Light Orange**: Process events and status tracking
- **Light Yellow**: Additional data fields

## Bot Integration Points
- **Webhook Endpoints**: Handle real-time updates
- **24/7 Monitoring**: Continuous data synchronization
- **Multi-sheet Operations**: Cross-reference data between sheets
- **Date-based Processing**: Handle monthly tracking sheets
