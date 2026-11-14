import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-secret-key-smart-complaint-2026')
    
    # SQLite Database location in instance folder
    INSTANCE_DIR = BASE_DIR / 'instance'
    INSTANCE_DIR.mkdir(exist_ok=True)
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f"sqlite:///{INSTANCE_DIR / 'complaints.db'}")
    if SQLALCHEMY_DATABASE_URI.startswith('sqlite:///') and not SQLALCHEMY_DATABASE_URI.startswith('sqlite:////'):
        # Normalize relative sqlite path
        rel_path = SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
        if not os.path.isabs(rel_path):
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{INSTANCE_DIR / rel_path}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # App base URL for QR code generation
    APP_URL = os.getenv('APP_URL', 'http://localhost:5000')

    # Admin seed defaults
    ADMIN_DEFAULT_USER = os.getenv('ADMIN_DEFAULT_USER', 'admin')
    ADMIN_DEFAULT_PASS = os.getenv('ADMIN_DEFAULT_PASS', 'admin123')
    ADMIN_DEFAULT_EMAIL = os.getenv('ADMIN_DEFAULT_EMAIL', 'admin@smartcampus.edu')

    # SMTP Settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'complaints@smartcampus.edu')
    ADMIN_NOTIFICATION_EMAIL = os.getenv('ADMIN_NOTIFICATION_EMAIL', 'admin@smartcampus.edu')

    # Complaint categories list
    COMPLAINT_CATEGORIES = [
        "Faculty Issue",
        "Teaching Issue",
        "Staff Issue",
        "Classroom Issue",
        "Laboratory Issue",
        "Examination Issue",
        "Academic Issue",
        "Infrastructure Issue",
        "Library Issue",
        "Hostel Issue",
        "Canteen Issue",
        "Internet/Wi-Fi Issue",
        "Electrical Issue",
        "Water/Sanitation Issue",
        "Safety/Security Issue",
        "Transportation Issue",
        "Administration Issue",
        "Other"
    ]

    # Priority levels
    PRIORITY_LEVELS = ["Low", "Medium", "High", "Emergency"]

    # Complaint Statuses
    STATUS_CHOICES = ["Pending", "Under Review", "In Progress", "Resolved", "Rejected"]
