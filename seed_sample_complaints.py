"""
Seed sample complaints to demonstrate the full workflow,
including status history, admin responses, and dashboard charts.
"""
from datetime import datetime, timedelta
from app import create_app
from models import db
from models.models import Complaint, ComplaintStatusHistory, Location

app = create_app()

with app.app_context():
    # Only seed if no complaints exist yet
    if Complaint.query.count() == 0:
        print("[*] Seeding sample complaints...")
        now = datetime.now()

        samples = [
            {
                "complaint_id": "CMP-2026-0001",
                "category": "Faculty Issue",
                "faculty_staff_name": "Prof. Advanced Mathematics",
                "description": "I am facing an issue with the way the class is being conducted. The explanation pace is extremely fast and questions during lecture are often brushed off. Please review it.",
                "location": "Classroom A101",
                "specific_location": "Row 4",
                "priority": "Medium",
                "status": "Under Review",
                "admin_response": "The Academic Dean has scheduled a discussion with the department head to review teaching methodology.",
                "days_ago": 3,
                "history": [
                    ("Pending", "Complaint submitted anonymously by student.", 3),
                    ("Under Review", "Assigned to Academic Dean for review.", 2)
                ]
            },
            {
                "complaint_id": "CMP-2026-0002",
                "category": "Classroom Issue",
                "faculty_staff_name": None,
                "description": "The fan in our classroom is not working. It makes loud grinding noises and turns off after 2 minutes.",
                "location": "Classroom A102",
                "specific_location": "Ceiling fan near back window",
                "priority": "High",
                "status": "In Progress",
                "admin_response": "Electrician team visited and ordered a replacement motor. Scheduled for installation tomorrow morning.",
                "days_ago": 2,
                "history": [
                    ("Pending", "Complaint submitted anonymously by student.", 2),
                    ("Under Review", "Sent work order to Electrical Maintenance.", 2),
                    ("In Progress", "Electrician inspected fan, replacing motor unit.", 1)
                ]
            },
            {
                "complaint_id": "CMP-2026-0003",
                "category": "Other",
                "faculty_staff_name": None,
                "description": "There is an issue in the college that I would like the administration to look into. The bicycle parking shed near the rear gate is constantly flooded after rain.",
                "location": "General Campus",
                "specific_location": "Rear parking shed B",
                "priority": "Medium",
                "status": "Pending",
                "admin_response": None,
                "days_ago": 1,
                "history": [
                    ("Pending", "Complaint submitted anonymously by student.", 1)
                ]
            },
            {
                "complaint_id": "CMP-2026-0004",
                "category": "Laboratory Issue",
                "faculty_staff_name": None,
                "description": "Five computers (terminals 11 to 15) in Computer Lab have broken Ethernet ports and outdated IDEs required for DBMS lab exercises.",
                "location": "Computer Lab",
                "specific_location": "Row 2, Systems 11-15",
                "priority": "High",
                "status": "Resolved",
                "admin_response": "System Administrator replaced network cables and updated the software environment on all machines.",
                "days_ago": 5,
                "history": [
                    ("Pending", "Complaint submitted anonymously by student.", 5),
                    ("In Progress", "IT team dispatched to re-crimp cables and patch IDEs.", 4),
                    ("Resolved", "System Administrator replaced network cables and updated software. All terminals operational.", 3)
                ]
            },
            {
                "complaint_id": "CMP-2026-0005",
                "category": "Electrical Issue",
                "faculty_staff_name": None,
                "description": "Exposed wiring near the physics experiment bench switchboard. Sparks were observed when turning on the apparatus.",
                "location": "Physics Lab",
                "specific_location": "Apparatus table 3 switchboard",
                "priority": "Emergency",
                "status": "Resolved",
                "admin_response": "Emergency maintenance dispatched within 15 minutes. Switchboard rewired and circuit breaker replaced.",
                "days_ago": 6,
                "history": [
                    ("Pending", "Urgent safety report submitted.", 6),
                    ("In Progress", "Emergency maintenance dispatched.", 6),
                    ("Resolved", "Switchboard rewired and circuit breaker replaced. Passed safety inspection.", 5)
                ]
            },
            {
                "complaint_id": "CMP-2026-0006",
                "category": "Canteen Issue",
                "faculty_staff_name": None,
                "description": "Drinking water cooler near the canteen counter is not cooling and the water filter indicator shows red.",
                "location": "Canteen",
                "specific_location": "Main dining hall cooler",
                "priority": "Medium",
                "status": "Pending",
                "admin_response": None,
                "days_ago": 0,
                "history": [
                    ("Pending", "Complaint submitted anonymously by student.", 0)
                ]
            }
        ]

        for s in samples:
            created_time = now - timedelta(days=s["days_ago"], hours=3)
            comp = Complaint(
                complaint_id=s["complaint_id"],
                category=s["category"],
                faculty_staff_name=s["faculty_staff_name"],
                description=s["description"],
                location=s["location"],
                specific_location=s["specific_location"],
                priority=s["priority"],
                status=s["status"],
                admin_response=s["admin_response"],
                created_at=created_time,
                updated_at=now - timedelta(days=s["days_ago"] // 2)
            )
            db.session.add(comp)
            db.session.flush()

            for hist_status, comment, hist_days in s["history"]:
                hist_entry = ComplaintStatusHistory(
                    complaint_id=comp.id,
                    old_status=None if hist_status == 'Pending' else 'Pending',
                    new_status=hist_status,
                    comment=comment,
                    changed_by='System' if hist_status == 'Pending' else 'admin',
                    created_at=now - timedelta(days=hist_days, hours=2)
                )
                db.session.add(hist_entry)

        db.session.commit()
        print(f"[OK] Successfully seeded {len(samples)} realistic sample complaints.")
    else:
        print("[!] Database already contains complaints, skipping sample seed.")
