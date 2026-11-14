import io
import csv
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, session, current_app, Response, jsonify
)
from models import db
from models.models import Admin, Complaint, Location, ComplaintStatusHistory
from utils.qr_generator import generate_location_qr_base64, get_complaint_url

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Please log in to access the administrator panel.', 'warning')
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_id'):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username_or_email = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        admin = Admin.query.filter(
            (Admin.username == username_or_email) | (Admin.email == username_or_email)
        ).first()

        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash(f"Welcome back, {admin.username}!", "success")
            next_url = request.args.get('next') or url_for('admin.dashboard')
            return redirect(next_url)
        else:
            flash("Invalid username/email or password. Please try again.", "danger")

    return render_template('admin/login.html')


@admin_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('admin.login'))


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin Dashboard with summary statistics, charts, and recent complaints"""
    # Summary Counters
    total_complaints = Complaint.query.count()
    pending_count = Complaint.query.filter_by(status='Pending').count()
    under_review_count = Complaint.query.filter_by(status='Under Review').count()
    in_progress_count = Complaint.query.filter_by(status='In Progress').count()
    resolved_count = Complaint.query.filter_by(status='Resolved').count()
    rejected_count = Complaint.query.filter_by(status='Rejected').count()
    
    high_priority_count = Complaint.query.filter_by(priority='High').count()
    emergency_count = Complaint.query.filter_by(priority='Emergency').count()

    faculty_complaints_count = Complaint.query.filter(
        (Complaint.category == 'Faculty Issue') | (Complaint.faculty_staff_name.isnot(None))
    ).count()
    teaching_complaints_count = Complaint.query.filter_by(category='Teaching Issue').count()

    total_locations = Location.query.count()

    # Recent complaints
    recent_complaints = Complaint.query.order_by(Complaint.created_at.desc()).limit(8).all()

    # Top complaint locations
    location_stats = db.session.query(
        Complaint.location, db.func.count(Complaint.id).label('count')
    ).group_by(Complaint.location).order_by(db.desc('count')).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        total_complaints=total_complaints,
        pending_count=pending_count,
        under_review_count=under_review_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        rejected_count=rejected_count,
        high_priority_count=high_priority_count,
        emergency_count=emergency_count,
        faculty_complaints_count=faculty_complaints_count,
        teaching_complaints_count=teaching_complaints_count,
        total_locations=total_locations,
        recent_complaints=recent_complaints,
        location_stats=location_stats
    )


@admin_bp.route('/complaints')
@admin_required
def complaints():
    """All complaints list with search, filter, and sorting"""
    query = Complaint.query

    # Search parameters
    search_q = request.args.get('q', '').strip()
    category_filter = request.args.get('category', '').strip()
    location_filter = request.args.get('location', '').strip()
    priority_filter = request.args.get('priority', '').strip()
    status_filter = request.args.get('status', '').strip()
    sort_by = request.args.get('sort', 'newest').strip()

    if search_q:
        search_pattern = f"%{search_q}%"
        query = query.filter(
            (Complaint.complaint_id.ilike(search_pattern)) |
            (Complaint.description.ilike(search_pattern)) |
            (Complaint.faculty_staff_name.ilike(search_pattern)) |
            (Complaint.location.ilike(search_pattern))
        )

    if category_filter:
        query = query.filter(Complaint.category == category_filter)

    if location_filter:
        query = query.filter(Complaint.location == location_filter)

    if priority_filter:
        query = query.filter(Complaint.priority == priority_filter)

    if status_filter:
        query = query.filter(Complaint.status == status_filter)

    # Sorting
    if sort_by == 'oldest':
        query = query.order_by(Complaint.created_at.asc())
    elif sort_by == 'priority':
        # Custom priority sorting: Emergency -> High -> Medium -> Low
        priority_order = db.case(
            (Complaint.priority == 'Emergency', 1),
            (Complaint.priority == 'High', 2),
            (Complaint.priority == 'Medium', 3),
            (Complaint.priority == 'Low', 4),
            else_=5
        )
        query = query.order_by(priority_order, Complaint.created_at.desc())
    else:  # newest default
        query = query.order_by(Complaint.created_at.desc())

    complaints_list = query.all()
    all_locations = Location.query.order_by(Location.name).all()
    categories = current_app.config['COMPLAINT_CATEGORIES']
    priorities = current_app.config['PRIORITY_LEVELS']
    statuses = current_app.config['STATUS_CHOICES']

    return render_template(
        'admin/complaints.html',
        complaints=complaints_list,
        categories=categories,
        locations=all_locations,
        priorities=priorities,
        statuses=statuses,
        search_q=search_q,
        category_filter=category_filter,
        location_filter=location_filter,
        priority_filter=priority_filter,
        status_filter=status_filter,
        sort_by=sort_by,
        total_matched=len(complaints_list)
    )


@admin_bp.route('/complaints/<int:id>', methods=['GET', 'POST'])
@admin_required
def complaint_detail(id):
    """View complaint detail, update status, and add administrator response"""
    complaint_obj = db.get_or_404(Complaint, id)
    statuses = current_app.config['STATUS_CHOICES']

    if request.method == 'POST':
        action_type = request.form.get('action_type', 'update_status')

        if action_type == 'update_status':
            new_status = request.form.get('status', '').strip()
            admin_response = request.form.get('admin_response', '').strip()
            status_note = request.form.get('status_note', '').strip()

            if new_status in statuses:
                old_status = complaint_obj.status
                complaint_obj.status = new_status
                complaint_obj.admin_response = admin_response if admin_response else complaint_obj.admin_response
                complaint_obj.updated_at = datetime.now()

                # Add history entry
                history_comment = status_note or (f"Status changed from {old_status} to {new_status}." + (f" Response: {admin_response}" if admin_response else ""))
                history_entry = ComplaintStatusHistory(
                    complaint_id=complaint_obj.id,
                    old_status=old_status,
                    new_status=new_status,
                    comment=history_comment,
                    changed_by=session.get('admin_username', 'Admin')
                )
                db.session.add(history_entry)
                db.session.commit()
                flash(f"Complaint {complaint_obj.complaint_id} updated successfully.", "success")
            else:
                flash("Invalid status selected.", "danger")

        return redirect(url_for('admin.complaint_detail', id=complaint_obj.id))

    history_list = complaint_obj.history.all()
    return render_template(
        'admin/complaint_detail.html',
        complaint=complaint_obj,
        statuses=statuses,
        history=history_list
    )


@admin_bp.route('/locations', methods=['GET', 'POST'])
@admin_required
def locations():
    """List, add, and manage locations"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        building = request.form.get('building', '').strip()
        floor = request.form.get('floor', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash("Location name is required.", "danger")
        elif Location.query.filter_by(name=name).first():
            flash(f"A location with the name '{name}' already exists.", "warning")
        else:
            new_loc = Location(
                name=name,
                building=building if building else None,
                floor=floor if floor else None,
                description=description if description else None,
                is_active=True
            )
            db.session.add(new_loc)
            db.session.commit()
            flash(f"Location '{name}' created successfully!", "success")
            return redirect(url_for('admin.locations'))

    all_locations = Location.query.order_by(Location.name).all()
    base_url = current_app.config['APP_URL']
    
    # Attach base64 QR preview to each location
    location_data = []
    for loc in all_locations:
        loc_dict = loc.to_dict()
        loc_dict['qr_base64'] = generate_location_qr_base64(loc.name, base_url, box_size=4)
        loc_dict['complaint_url'] = get_complaint_url(loc.name, base_url)
        loc_dict['complaint_count'] = Complaint.query.filter_by(location=loc.name).count()
        location_data.append(loc_dict)

    return render_template('admin/locations.html', locations=location_data)


@admin_bp.route('/locations/create', methods=['GET', 'POST'])
@admin_required
def create_location():
    """Dedicated location creation page"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        building = request.form.get('building', '').strip()
        floor = request.form.get('floor', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash("Location name is required.", "danger")
            return render_template('admin/locations_create.html')

        if Location.query.filter_by(name=name).first():
            flash(f"A location with the name '{name}' already exists.", "warning")
            return render_template('admin/locations_create.html')

        new_loc = Location(
            name=name,
            building=building if building else None,
            floor=floor if floor else None,
            description=description if description else None,
            is_active=True
        )
        db.session.add(new_loc)
        db.session.commit()
        flash(f"Location '{name}' created successfully!", "success")
        return redirect(url_for('admin.locations'))

    return render_template('admin/locations_create.html')


@admin_bp.route('/locations/<int:id>/edit', methods=['POST'])
@admin_required
def edit_location(id):
    loc = db.get_or_404(Location, id)
    name = request.form.get('name', '').strip()
    building = request.form.get('building', '').strip()
    floor = request.form.get('floor', '').strip()
    description = request.form.get('description', '').strip()
    is_active = request.form.get('is_active') == 'on'

    if not name:
        flash("Location name cannot be empty.", "danger")
        return redirect(url_for('admin.locations'))

    existing = Location.query.filter(Location.name == name, Location.id != id).first()
    if existing:
        flash(f"Another location with the name '{name}' already exists.", "warning")
        return redirect(url_for('admin.locations'))

    # If location name changed, update existing complaints under this location
    old_name = loc.name
    if old_name != name:
        Complaint.query.filter_by(location=old_name).update({'location': name})

    loc.name = name
    loc.building = building if building else None
    loc.floor = floor if floor else None
    loc.description = description if description else None
    loc.is_active = is_active
    db.session.commit()

    flash(f"Location '{name}' updated successfully.", "success")
    return redirect(url_for('admin.locations'))


@admin_bp.route('/locations/<int:id>/delete', methods=['POST'])
@admin_required
def delete_location(id):
    loc = db.get_or_404(Location, id)
    name = loc.name
    complaint_count = Complaint.query.filter_by(location=name).count()
    
    if complaint_count > 0:
        # Soft delete by deactivating to preserve historical complaint records
        loc.is_active = False
        db.session.commit()
        flash(f"Location '{name}' has existing complaints ({complaint_count}), so it was marked inactive instead of permanently deleted.", "warning")
    else:
        db.session.delete(loc)
        db.session.commit()
        flash(f"Location '{name}' deleted successfully.", "success")

    return redirect(url_for('admin.locations'))


@admin_bp.route('/qr-codes')
@admin_required
def qr_codes():
    """Visual gallery of all QR codes with download and print options"""
    all_locations = Location.query.filter_by(is_active=True).order_by(Location.name).all()
    base_url = current_app.config['APP_URL']

    items = []
    for loc in all_locations:
        items.append({
            'id': loc.id,
            'name': loc.name,
            'building': loc.building or '',
            'floor': loc.floor or '',
            'complaint_url': get_complaint_url(loc.name, base_url),
            'qr_base64': generate_location_qr_base64(loc.name, base_url, box_size=8)
        })

    return render_template('admin/qr_codes.html', qr_items=items)


@admin_bp.route('/locations/<int:id>/print')
@admin_required
def print_location_qr(id):
    """Clean printable poster/card for a specific location"""
    loc = db.get_or_404(Location, id)
    base_url = current_app.config['APP_URL']
    qr_base64 = generate_location_qr_base64(loc.name, base_url, box_size=10)
    complaint_url = get_complaint_url(loc.name, base_url)

    return render_template(
        'admin/qr_print.html',
        items=[{
            'name': loc.name,
            'building': loc.building,
            'floor': loc.floor,
            'description': loc.description,
            'complaint_url': complaint_url,
            'qr_base64': qr_base64
        }],
        bulk=False
    )


@admin_bp.route('/qr-codes/print-all')
@admin_required
def print_all_qr():
    """Printable sheet containing QR code cards for all active locations"""
    all_locations = Location.query.filter_by(is_active=True).order_by(Location.name).all()
    base_url = current_app.config['APP_URL']

    items = []
    for loc in all_locations:
        items.append({
            'name': loc.name,
            'building': loc.building,
            'floor': loc.floor,
            'description': loc.description,
            'complaint_url': get_complaint_url(loc.name, base_url),
            'qr_base64': generate_location_qr_base64(loc.name, base_url, box_size=8)
        })

    return render_template('admin/qr_print.html', items=items, bulk=True)


@admin_bp.route('/reports')
@admin_required
def reports():
    """Analytics and reporting dashboard with date ranges and trends"""
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # Time period counts
    daily_count = Complaint.query.filter(Complaint.created_at >= today_start).count()
    weekly_count = Complaint.query.filter(Complaint.created_at >= week_start).count()
    monthly_count = Complaint.query.filter(Complaint.created_at >= month_start).count()
    total_count = Complaint.query.count()

    # Faculty & Teaching metrics
    faculty_count = Complaint.query.filter(
        (Complaint.category == 'Faculty Issue') | (Complaint.faculty_staff_name.isnot(None))
    ).count()
    teaching_count = Complaint.query.filter_by(category='Teaching Issue').count()

    # Breakdown queries
    category_breakdown = db.session.query(
        Complaint.category, db.func.count(Complaint.id)
    ).group_by(Complaint.category).order_by(db.desc(db.func.count(Complaint.id))).all()

    location_breakdown = db.session.query(
        Complaint.location, db.func.count(Complaint.id)
    ).group_by(Complaint.location).order_by(db.desc(db.func.count(Complaint.id))).limit(10).all()

    status_breakdown = db.session.query(
        Complaint.status, db.func.count(Complaint.id)
    ).group_by(Complaint.status).all()

    priority_breakdown = db.session.query(
        Complaint.priority, db.func.count(Complaint.id)
    ).group_by(Complaint.priority).all()

    return render_template(
        'admin/reports.html',
        daily_count=daily_count,
        weekly_count=weekly_count,
        monthly_count=monthly_count,
        total_count=total_count,
        faculty_count=faculty_count,
        teaching_count=teaching_count,
        category_breakdown=category_breakdown,
        location_breakdown=location_breakdown,
        status_breakdown=status_breakdown,
        priority_breakdown=priority_breakdown
    )


@admin_bp.route('/reports/export-csv')
@admin_required
def export_csv():
    """
    Export all complaints to CSV.
    STRICT PRIVACY POLICY:
    The CSV contains strictly NO student personal identification details.
    """
    complaints_list = Complaint.query.order_by(Complaint.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header without any student personal information
    writer.writerow([
        'Complaint ID',
        'Date Submitted (UTC)',
        'Category',
        'Location',
        'Specific Location',
        'Priority',
        'Status',
        'Faculty or Staff Mentioned',
        'Complaint Description',
        'Admin Response',
        'Last Updated'
    ])

    for c in complaints_list:
        writer.writerow([
            c.complaint_id,
            c.created_at.strftime('%Y-%m-%d %H:%M:%S') if c.created_at else '',
            c.category,
            c.location,
            c.specific_location or '',
            c.priority,
            c.status,
            c.faculty_staff_name or '',
            c.description,
            c.admin_response or '',
            c.updated_at.strftime('%Y-%m-%d %H:%M:%S') if c.updated_at else ''
        ])

    csv_data = output.getvalue()
    filename = f"complaints_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename={filename}'}
    )


@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """Admin settings page: Change password and view system settings"""
    admin_id = session.get('admin_id')
    admin_user = db.session.get(Admin, admin_id)

    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not admin_user.check_password(current_password):
            flash("Incorrect current password.", "danger")
        elif len(new_password) < 6:
            flash("New password must be at least 6 characters long.", "danger")
        elif new_password != confirm_password:
            flash("New passwords do not match.", "danger")
        else:
            admin_user.set_password(new_password)
            db.session.commit()
            flash("Password updated successfully!", "success")

    return render_template('admin/settings.html', admin=admin_user)
