import re
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from models import db
from models.models import Complaint, Location, ComplaintStatusHistory, generate_unique_complaint_id
from utils.email_service import send_complaint_notification

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def index():
    """Home / Landing page explaining the anonymous QR complaint process"""
    locations = Location.query.filter_by(is_active=True).order_by(Location.name).all()
    recent_resolved_count = Complaint.query.filter_by(status='Resolved').count()
    total_complaints_count = Complaint.query.count()
    return render_template(
        'index.html',
        locations=locations,
        resolved_count=recent_resolved_count,
        total_count=total_complaints_count
    )


@public_bp.route('/complaint', methods=['GET', 'POST'])
def complaint():
    """
    Student Complaint Submission Page
    Supports QR code scanning via ?location=Classroom%20A101
    STRICT PRIVACY: Does NOT collect or store student name, roll number, email, phone, IP.
    """
    categories = current_app.config['COMPLAINT_CATEGORIES']
    priorities = current_app.config['PRIORITY_LEVELS']
    all_locations = Location.query.filter_by(is_active=True).order_by(Location.name).all()

    # Pre-filled location from query parameter (e.g., /complaint?location=Classroom%20A101)
    prefilled_location = request.args.get('location', '').strip()

    if request.method == 'POST':
        selected_location = request.form.get('location', '').strip()
        custom_location = request.form.get('custom_location', '').strip()
        specific_location = request.form.get('specific_location', '').strip()
        category = request.form.get('category', '').strip() or 'Other'
        faculty_staff_name = request.form.get('faculty_staff_name', '').strip()
        description = request.form.get('description', '').strip()
        priority = request.form.get('priority', '').strip() or 'Medium'

        # Resolve location
        final_location = custom_location if selected_location == '__custom__' and custom_location else selected_location
        if not final_location:
            final_location = prefilled_location or 'General Campus'

        # Validation
        errors = []
        if not description:
            errors.append("Please describe your issue. This field cannot be left blank.")
        elif len(description) < 10:
            errors.append("Please provide a little more detail about the issue (minimum 10 characters).")
        elif len(description) > 3000:
            errors.append("Description is too long (maximum 3000 characters). Please summarize your issue.")

        if category not in categories and category != 'Other':
            category = 'Other'

        if priority not in priorities:
            priority = 'Medium'

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template(
                'complaint.html',
                categories=categories,
                priorities=priorities,
                locations=all_locations,
                prefilled_location=final_location,
                form_data=request.form
            )

        # Generate unique Complaint ID (e.g. CMP-2026-0001)
        new_complaint_id = generate_unique_complaint_id()

        new_complaint = Complaint(
            complaint_id=new_complaint_id,
            category=category,
            faculty_staff_name=faculty_staff_name if faculty_staff_name else None,
            description=description,
            location=final_location,
            specific_location=specific_location if specific_location else None,
            priority=priority,
            status='Pending',
            created_at=datetime.now()
        )

        db.session.add(new_complaint)
        db.session.flush()  # To get new_complaint.id

        # Add initial history entry
        initial_history = ComplaintStatusHistory(
            complaint_id=new_complaint.id,
            old_status=None,
            new_status='Pending',
            comment='Complaint submitted anonymously by student.',
            changed_by='System'
        )
        db.session.add(initial_history)
        db.session.commit()

        # Send asynchronous email notification to administrator
        send_complaint_notification(new_complaint, current_app.config)

        # Redirect to success page
        return redirect(url_for('public.success', id=new_complaint_id))

    return render_template(
        'complaint.html',
        categories=categories,
        priorities=priorities,
        locations=all_locations,
        prefilled_location=prefilled_location,
        form_data={}
    )


@public_bp.route('/success')
def success():
    """Submission confirmation page with Complaint ID & instructions"""
    complaint_id = request.args.get('id', '').strip()
    if not complaint_id:
        return redirect(url_for('public.index'))

    complaint_obj = Complaint.query.filter_by(complaint_id=complaint_id).first()
    return render_template('success.html', complaint_id=complaint_id, complaint=complaint_obj)


@public_bp.route('/track', methods=['GET', 'POST'])
def track():
    """Public complaint tracking page by Complaint ID"""
    searched_id = request.args.get('id', '').strip()
    if request.method == 'POST':
        searched_id = request.form.get('complaint_id', '').strip()

    complaint_data = None
    not_found = False

    if searched_id:
        # Standardize search (case insensitive uppercase e.g. cmp-2026-0001 -> CMP-2026-0001)
        normalized_id = searched_id.upper()
        complaint_data = Complaint.query.filter(
            db.func.upper(Complaint.complaint_id) == normalized_id
        ).first()

        if not complaint_data:
            not_found = True

    return render_template(
        'track.html',
        searched_id=searched_id,
        complaint=complaint_data,
        not_found=not_found
    )
