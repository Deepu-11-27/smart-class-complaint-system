from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class Admin(db.Model):
    __tablename__ = 'admins'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<Admin {self.username}>"


class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False, index=True)
    building = db.Column(db.String(100), nullable=True)
    floor = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'building': self.building or '',
            'floor': self.floor or '',
            'description': self.description or '',
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }

    def __repr__(self):
        return f"<Location {self.name}>"


class Complaint(db.Model):
    """
    ANONYMOUS COMPLAINT MODEL
    STRICT PRIVACY POLICY:
    This table explicitly DOES NOT contain any student personal identification fields
    such as student_name, student_id, roll_number, email, phone, ip_address, device_id.
    """
    __tablename__ = 'complaints'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.String(32), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, default='Other')
    faculty_staff_name = db.Column(db.String(150), nullable=True)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(150), nullable=False, index=True)
    specific_location = db.Column(db.String(150), nullable=True)
    priority = db.Column(db.String(20), nullable=False, default='Medium')
    status = db.Column(db.String(50), nullable=False, default='Pending', index=True)
    admin_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    history = db.relationship('ComplaintStatusHistory', backref='complaint', lazy='dynamic', cascade='all, delete-orphan', order_by='ComplaintStatusHistory.created_at.desc()')

    @property
    def status_badge_class(self):
        mapping = {
            'Pending': 'bg-secondary',
            'Under Review': 'bg-info text-dark',
            'In Progress': 'bg-primary',
            'Resolved': 'bg-success',
            'Rejected': 'bg-danger'
        }
        return mapping.get(self.status, 'bg-secondary')

    @property
    def priority_badge_class(self):
        mapping = {
            'Low': 'bg-light text-dark border',
            'Medium': 'bg-primary',
            'High': 'bg-warning text-dark',
            'Emergency': 'bg-danger'
        }
        return mapping.get(self.priority, 'bg-secondary')

    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'category': self.category,
            'faculty_staff_name': self.faculty_staff_name or '',
            'description': self.description,
            'location': self.location,
            'specific_location': self.specific_location or '',
            'priority': self.priority,
            'status': self.status,
            'admin_response': self.admin_response or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'created_date': self.created_at.strftime('%b %d, %Y') if self.created_at else '',
            'created_time': self.created_at.strftime('%I:%M %p') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else ''
        }

    def __repr__(self):
        return f"<Complaint {self.complaint_id} - {self.category} - {self.status}>"


class ComplaintStatusHistory(db.Model):
    __tablename__ = 'complaint_status_history'

    id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.id'), nullable=False)
    old_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=False)
    comment = db.Column(db.Text, nullable=True)
    changed_by = db.Column(db.String(80), nullable=True, default='Admin')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'comment': self.comment or '',
            'changed_by': self.changed_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'formatted_time': self.created_at.strftime('%b %d, %Y, %I:%M %p') if self.created_at else ''
        }

    def __repr__(self):
        return f"<ComplaintStatusHistory {self.complaint_id}: {self.old_status} -> {self.new_status}>"


def generate_unique_complaint_id():
    """
    Generate unique Complaint ID formatted as: CMP-YYYY-XXXX
    e.g., CMP-2026-0001
    """
    current_year = datetime.now().year
    prefix = f"CMP-{current_year}-"

    # Find highest sequence number for this year
    latest_complaint = Complaint.query.filter(
        Complaint.complaint_id.like(f"{prefix}%")
    ).order_by(Complaint.id.desc()).first()

    if latest_complaint and latest_complaint.complaint_id:
        try:
            last_seq = int(latest_complaint.complaint_id.split('-')[-1])
            next_seq = last_seq + 1
        except (ValueError, IndexError):
            next_seq = Complaint.query.count() + 1
    else:
        next_seq = 1

    candidate_id = f"{prefix}{next_seq:04d}"

    # Ensure uniqueness in case of concurrent requests or collisions
    while Complaint.query.filter_by(complaint_id=candidate_id).first() is not None:
        next_seq += 1
        candidate_id = f"{prefix}{next_seq:04d}"

    return candidate_id
