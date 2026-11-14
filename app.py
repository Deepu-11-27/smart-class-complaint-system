import os
from datetime import datetime
from flask import Flask, render_template
from config import Config
from models import db
from models.models import Admin, Location, Complaint, ComplaintStatusHistory
from routes.public import public_bp
from routes.admin import admin_bp
from routes.api import api_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Context processors
    @app.context_processor
    def inject_global_data():
        return {
            'app_title': 'Smart Class Complaint System',
            'current_year': datetime.now().year,
            'app_url': app.config.get('APP_URL', 'http://localhost:5000')
        }

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    # Auto-seed initial database tables and default admin/locations
    with app.app_context():
        db.create_all()
        seed_default_data(app)

    return app


def seed_default_data(app):
    """Seed initial administrator and default campus locations if they don't exist"""
    # 1. Seed Admin
    default_user = app.config.get('ADMIN_DEFAULT_USER', 'admin')
    default_pass = app.config.get('ADMIN_DEFAULT_PASS', 'admin123')
    default_email = app.config.get('ADMIN_DEFAULT_EMAIL', 'admin@smartcampus.edu')

    existing_admin = Admin.query.filter_by(username=default_user).first()
    if not existing_admin:
        admin = Admin(
            username=default_user,
            email=default_email
        )
        admin.set_password(default_pass)
        db.session.add(admin)
        db.session.commit()
        print(f"[*] Initial admin created: username='{default_user}', password='{default_pass}'")

    # 2. Seed Default Locations
    default_locations = [
        {"name": "Classroom A101", "building": "Academic Block A", "floor": "Ground Floor", "description": "Standard Lecture Room with Projector"},
        {"name": "Classroom A102", "building": "Academic Block A", "floor": "Ground Floor", "description": "Lecture Room near Department Office"},
        {"name": "Classroom B201", "building": "Academic Block B", "floor": "2nd Floor", "description": "Smart Classroom with Interactive Display"},
        {"name": "Computer Lab", "building": "IT Block", "floor": "1st Floor", "description": "High-Performance Computing & Software Lab"},
        {"name": "Physics Lab", "building": "Science Block", "floor": "1st Floor", "description": "General Physics Experimental Lab"},
        {"name": "Chemistry Lab", "building": "Science Block", "floor": "2nd Floor", "description": "Organic & Inorganic Chemistry Lab"},
        {"name": "Central Library", "building": "Library Wing", "floor": "Ground & 1st Floor", "description": "Reading Halls and Digital Library Section"},
        {"name": "Hostel", "building": "Student Residence Block", "floor": "All Floors", "description": "Student Residential Rooms & Common Rooms"},
        {"name": "Canteen", "building": "Student Activity Center", "floor": "Ground Floor", "description": "College Dining and Refreshment Area"},
        {"name": "Department Office", "building": "Administrative Block", "floor": "1st Floor", "description": "Faculty and HOD Administrative Offices"},
        {"name": "Campus Grounds & Sports", "building": "Campus Grounds", "floor": "Outdoor", "description": "Sports Field, Courts and Walkways"},
        {"name": "General Campus", "building": "Main Campus", "floor": "Outdoor", "description": "Main Entrance, Corridors and Common Areas"}
    ]

    for loc_info in default_locations:
        if not Location.query.filter_by(name=loc_info['name']).first():
            new_loc = Location(
                name=loc_info['name'],
                building=loc_info['building'],
                floor=loc_info['floor'],
                description=loc_info['description'],
                is_active=True
            )
            db.session.add(new_loc)
    
    db.session.commit()


app = create_app()

if __name__ == '__main__':
    # Listen on all interfaces or localhost
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
