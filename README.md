# Smart Class Complaint System

> **A confidential, anonymous QR-code-driven grievance reporting and resolution platform for schools, colleges, and universities.**

---

## 📌 1. Project Introduction

The **Smart Class Complaint System** is an institutional web platform engineered to empower students to report campus issues securely and confidentially. By placing location-specific QR codes across lecture halls, laboratory benches, libraries, hostels, and canteens, students can scan a code with any standard smartphone camera, describe their problem freely in their own words, submit the report immediately, and monitor its real-time resolution status using a generated **Complaint ID**—all without creating an account or revealing their identity.

---

## 🎯 2. Problem Statement

In conventional educational setups, students often hesitate or decline to report grievances (such as classroom maintenance failures, harassment, faculty teaching pace, erratic grading, lab defects, or sanitation issues) because:
1. **Fear of Reprisal / Victimization:** Requiring student name, roll number, or department exposes the student to potential bias.
2. **Cumbersome Portals:** Traditional ERP systems force login with credentials, CAPTCHA, and tedious multi-step menus.
3. **Rigid Predefined Options:** Pre-set issue dropdowns rarely match the student's actual circumstances.
4. **Lack of Transparency:** Once a complaint is filed, students are left in the dark with no easy way to track resolution progress.

---

## 💡 3. Proposed Solution

The Smart Class Complaint System adopts the golden operational principle:

> ### **"REPORT THE ISSUE, NOT THE STUDENT."**

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  SCAN QR CODE   │  ───> │ WRITE YOUR ISSUE │  ───> │ SUBMIT ISSUE    │
│  In Room / Lab  │       │ In Your Own Words│      │ 100% Anonymous  │
└─────────────────┘       └─────────────────┘       └─────────────────┘
                                                             │
                                                             ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ TRACK STATUS    │  <─── │ ADMIN RESOLVES  │  <─── │ GET COMPLAINT ID│
│ View Admin Note │       │ & Adds Response │       │ e.g. CMP-2026-..│
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

1. **Scan QR Code:** Placed in classrooms, labs, libraries, hostels, canteens. Opens `/complaint?location=Classroom%20A101` automatically identifying the physical room.
2. **Describe Issue in Own Words:** Large free-form text box with live character counter. No rigid forced categories.
3. **Submit Anonymously:** No student login, no roll number, no phone, no email, no IP tracking, no media files.
4. **Unique Complaint ID:** Instantly issues a tracking ID (e.g. `CMP-2026-0001`).
5. **Track Resolution:** Public tracking page `/track` allows students to view progress (Pending &rarr; Under Review &rarr; In Progress &rarr; Resolved/Rejected) and read official admin responses.

---

## ✨ 4. Key Features

- **Strict Anonymous Grievance Submission:** No account creation or personal identification.
- **Physical QR Code Generator:** Admin creates campus spaces and generates high-resolution printable QR placards.
- **Auto-Location Detection:** Scanning a room placard automatically locks in the room name on the submission form.
- **Support for Faculty & Academic Issues:** Dedicated optional field to mention faculty/staff members without requiring the student's name.
- **Flexible Categorization:** 18 predefined educational grievance categories plus a free-form "Other" option.
- **Text-Only Privacy Guarantee:** Strictly forbids photo/video/file uploads to prevent inadvertent metadata and identity leakage.
- **Real-Time Interactive Tracking:** Visual progress stepper, admin reply box, and timestamped event timeline.
- **Asynchronous SMTP Notification:** Instant automated alerts dispatched to administrator email when a new complaint is filed (with fallback to local simulation mode).
- **Executive Admin Dashboard:** 8 KPI metric cards, Chart.js trend charts (14-day submissions, status distribution, top incident locations, categorical distribution).
- **Search, Filter & Sort:** Instant complaint search by ID, keywords, faculty names, locations, and priority levels.
- **One-Click CSV Export:** Generates standardized spreadsheets of all grievances stripped of any personal data.

---

## 🛡️ 5. Privacy & Confidentiality Guarantee

| Property | Policy |
| :--- | :--- |
| **Student Name** | ❌ Never asked, never stored |
| **Roll / Registration Number** | ❌ Never asked, never stored |
| **Email Address** | ❌ Never asked, never stored |
| **Phone / Mobile Number** | ❌ Never asked, never stored |
| **Student Accounts / Login** | ❌ No student authentication portal |
| **IP Address Logging** | ❌ Disabled; no IP column exists in database schema |
| **Device / Browser Fingerprinting** | ❌ Zero telemetry or user-agent tracking |
| **Photo / File Uploads** | ❌ Prohibited; complaints are strictly text-only |
| **Client-Side Privacy Filter** | ✅ Automatically warns student if accidental phone or email patterns are typed |

---

## 🏛️ 6. System Architecture

```
smart_class_complaint_system/
├── app.py                      # Application factory, context processors, auto-seeding
├── config.py                   # Centralized configuration & environment loader
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment variables
├── .env                        # Active local environment settings
├── README.md                   # Comprehensive technical documentation
├── test_system.py              # Automated test suite (10 unit & integration tests)
├── seed_sample_complaints.py   # Database seeder with realistic sample cases
│
├── models/
│   ├── __init__.py             # SQLAlchemy instance initialization
│   └── models.py               # Admin, Location, Complaint, ComplaintStatusHistory
│
├── routes/
│   ├── __init__.py
│   ├── public.py               # Student routes (/, /complaint, /track, /success)
│   ├── admin.py                # Admin dashboard, complaints management, locations, reports
│   └── api.py                  # QR binary endpoints & Chart.js JSON analytics
│
├── utils/
│   ├── __init__.py
│   ├── email_service.py        # Asynchronous multi-threaded SMTP notification system
│   └── qr_generator.py         # Pillow & qrcode engine for PNG and base64 rendering
│
├── templates/
│   ├── base.html               # Public base template with navbar and privacy footer
│   ├── index.html              # Public landing page with workflow illustration
│   ├── complaint.html          # Student complaint submission form
│   ├── success.html            # Submission confirmation & Complaint ID copy card
│   ├── track.html              # Public complaint tracking & timeline view
│   ├── 404.html & 500.html     # Custom error pages
│   └── admin/
│       ├── base_admin.html     # Admin layout with sidebar navigation
│       ├── login.html          # Admin secure authentication form
│       ├── dashboard.html      # KPI counter cards & Chart.js visual charts
│       ├── complaints.html     # Complaint management table with search & filters
│       ├── complaint_detail.html# Detail inspector, status updater & response editor
│       ├── locations.html      # Locations list, edit/delete modals, and QR tools
│       ├── locations_create.html# Dedicated new location creation page
│       ├── qr_codes.html       # Visual QR gallery with batch print options
│       ├── qr_print.html       # Print-ready placards with institutional branding
│       ├── reports.html        # Periodic metrics (daily, weekly, monthly) & CSV export
│       └── settings.html       # Admin password update & system diagnostics
│
└── static/
    ├── css/
    │   └── style.css           # Modern styles, print styles, and status timeline
    └── js/
        └── script.js           # Character counters, clipboard copy, and privacy scanner
```

---

## 🛠️ 7. Technologies Used

- **Backend:** Python 3.10+ / Python 3.14, Flask 3.1+
- **Database:** SQLite via SQLAlchemy ORM (stored in `instance/complaints.db`)
- **Authentication:** Werkzeug secure password hashing (`generate_password_hash`, `check_password_hash`) and Flask sessions
- **QR Code Engine:** `qrcode` library with `Pillow` (PIL) image generation
- **Email Service:** Python `smtplib` with asynchronous daemon background threads
- **Frontend:** HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons 1.11, Chart.js 4.4, Vanilla JavaScript

---

## 🚀 8. Installation & Setup

### Step 1: Clone or Navigate to the Workspace
```bash
cd "c:\Users\DELL\OneDrive\Desktop\smart class room\code\smartt"
```

### Step 2: Install Python Dependencies
```bash
python -m pip install -r requirements.txt
```

### Step 3: Environment Setup
Review `.env` (or copy from `.env.example`):
```ini
SECRET_KEY=smart_class_complaint_secret_key_2026_super_secure
FLASK_ENV=development
APP_URL=http://localhost:5000

# Database
DATABASE_URL=sqlite:///complaints.db

# Default Admin Account (Auto-created on launch)
ADMIN_DEFAULT_USER=admin
ADMIN_DEFAULT_PASS=admin123
ADMIN_DEFAULT_EMAIL=admin@smartcampus.edu

# Optional SMTP Settings (Leave MAIL_USERNAME blank for console simulation mode)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=complaints@smartcampus.edu
ADMIN_NOTIFICATION_EMAIL=admin@smartcampus.edu
```

---

## 🏃 9. Running the Application

### Start the Flask Development Server:
```bash
python app.py
```
*The server will start on `http://127.0.0.1:5000` (or `http://localhost:5000`).*

### (Optional) Populate Sample Complaints:
To seed the database with realistic sample grievances across categories, locations, and priorities:
```bash
python seed_sample_complaints.py
```

### Run the Automated Test Suite:
```bash
python -m unittest test_system.py
```

---

## 👥 10. User Workflows

### A. Student Workflow: "SCAN &rarr; DESCRIBE &rarr; SUBMIT &rarr; TRACK"
1. **Scan QR Code:**
   The student points their smartphone camera at any QR code placard in the classroom (e.g., Classroom A101).
   The URL opens:
   `http://localhost:5000/complaint?location=Classroom%20A101`
2. **Location Automatically Loaded:**
   The form prominently displays: `Complaint Location: Classroom A101`.
3. **Optional Details:**
   - Specific spot (e.g., *"Row 3 near projector"*).
   - Category (e.g., *Classroom Issue*, *Faculty Issue*, *Wi-Fi Issue*, or *Other*).
   - Faculty/Staff name (only if relevant, completely optional).
4. **Describe the Problem in Their Own Words:**
   A large text area allows free-form writing. Minimum 10 characters, maximum 3,000 characters with a live counter and automated privacy reminder.
5. **Select Priority (Optional):**
   Low, Medium (Default), High, or Emergency.
6. **Submit:**
   The system issues a unique tracking ID:
   `Complaint ID: CMP-2026-0001`
7. **Track Progress:**
   The student visits `/track` at any time, enters `CMP-2026-0001`, and views real-time status transitions and official administrative replies.

---

### B. Administrator Workflow:
1. **Login:**
   Visit `/admin/login` using `admin` / `admin123`.
2. **Dashboard Overview:**
   Review counts for *Total Complaints, Pending, Under Review, In Progress, Resolved, Rejected, High Priority, and Emergency*, alongside Chart.js analytics.
3. **Complaint Review & Status Update:**
   - Navigate to `/admin/complaints`.
   - Filter by location, category, priority, or status, or search by text keywords.
   - Click **Manage** on any complaint.
   - Update the status (e.g. *In Progress* &rarr; *Resolved*).
   - Add an **Admin Response** (e.g. *"The maintenance team replaced the faulty motor in ceiling fan #2."*).
4. **Campus Location & QR Management:**
   - Navigate to `/admin/locations` or `/admin/qr-codes`.
   - Add new classrooms, labs, hostels, or offices.
   - Download individual high-resolution PNG QR codes.
   - Click **Print Poster** to render clean institutional placards for physical wall mounting.
5. **Periodic Reports & CSV Export:**
   - Navigate to `/admin/reports` to inspect daily, weekly, and monthly trends.
   - Click **Export Full CSV Report** to download records (guaranteed free of student personal information).

---

## 📋 11. Supported Complaint Categories

1. Faculty Issue
2. Teaching Issue
3. Staff Issue
4. Classroom Issue
5. Laboratory Issue
6. Examination Issue
7. Academic Issue
8. Infrastructure Issue
9. Library Issue
10. Hostel Issue
11. Canteen Issue
12. Internet / Wi-Fi Issue
13. Electrical Issue
14. Water / Sanitation Issue
15. Safety / Security Issue
16. Transportation Issue
17. Administration Issue
18. Other (Unrestricted free-form)

---

## 🔐 12. Security & Compliance Highlights

- **Werkzeug 3.0+ Password Hashing:** Admin passwords are encrypted using secure PBKDF2/SHA256 salted hashes.
- **Zero Student Database Footprint:** The `complaints` table strictly contains no columns for `student_name`, `student_id`, `roll_number`, `email`, `phone`, `ip_address`, or `user_agent`.
- **Soft Deletion with Historical Integrity:** Deleting locations with existing complaints automatically transitions them to inactive status rather than orphaning or destroying past audit logs.
- **SQL Injection Prevention:** 100% parameterized queries via SQLAlchemy ORM.
- **XSS & CSRF Safe:** Jinja2 contextual escaping enabled by default across all forms and templates.

---

## 📄 13. License
This project is open-source educational software distributed under the **MIT License**.
