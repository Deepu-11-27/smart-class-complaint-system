from datetime import datetime, timedelta
from flask import Blueprint, jsonify, Response, current_app, request
from models import db
from models.models import Complaint, Location
from utils.qr_generator import generate_location_qr_bytes

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/qr/<int:location_id>')
def get_qr_image(location_id):
    """Serve binary PNG QR code for a location (for direct download or img src)"""
    loc = db.get_or_404(Location, location_id)
    base_url = current_app.config['APP_URL']
    png_bytes = generate_location_qr_bytes(loc.name, base_url, box_size=10)
    
    download = request.args.get('download', '0') == '1'
    headers = {'Content-Type': 'image/png'}
    if download:
        filename = f"qr_{loc.name.lower().replace(' ', '_')}.png"
        headers['Content-Disposition'] = f'attachment; filename="{filename}"'

    return Response(png_bytes, headers=headers)


@api_bp.route('/analytics')
def get_analytics():
    """Returns analytics data formatted for Chart.js rendering"""
    # Categories
    cat_data = db.session.query(
        Complaint.category, db.func.count(Complaint.id)
    ).group_by(Complaint.category).order_by(db.desc(db.func.count(Complaint.id))).all()

    # Statuses
    status_data = db.session.query(
        Complaint.status, db.func.count(Complaint.id)
    ).group_by(Complaint.status).all()

    # Priorities
    priority_data = db.session.query(
        Complaint.priority, db.func.count(Complaint.id)
    ).group_by(Complaint.priority).all()

    # Locations
    loc_data = db.session.query(
        Complaint.location, db.func.count(Complaint.id)
    ).group_by(Complaint.location).order_by(db.desc(db.func.count(Complaint.id))).limit(8).all()

    # Trends over the last 14 days
    today = datetime.now().date()
    days = []
    day_counts = []
    for i in range(13, -1, -1):
        target_date = today - timedelta(days=i)
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date, datetime.max.time())
        cnt = Complaint.query.filter(Complaint.created_at >= start_dt, Complaint.created_at <= end_dt).count()
        days.append(target_date.strftime('%b %d'))
        day_counts.append(cnt)

    return jsonify({
        'categories': {
            'labels': [c[0] for c in cat_data],
            'counts': [c[1] for c in cat_data]
        },
        'statuses': {
            'labels': [s[0] for s in status_data],
            'counts': [s[1] for s in status_data]
        },
        'priorities': {
            'labels': [p[0] for p in priority_data],
            'counts': [p[1] for p in priority_data]
        },
        'locations': {
            'labels': [l[0] for l in loc_data],
            'counts': [l[1] for l in loc_data]
        },
        'timeline': {
            'labels': days,
            'counts': day_counts
        }
    })


@api_bp.route('/track/<complaint_id>')
def api_track_complaint(complaint_id):
    """JSON API to fetch public complaint tracking data"""
    complaint = Complaint.query.filter(
        db.func.upper(Complaint.complaint_id) == complaint_id.strip().upper()
    ).first()

    if not complaint:
        return jsonify({'found': False, 'message': 'Complaint ID not found'}), 404

    return jsonify({
        'found': True,
        'complaint': {
            'complaint_id': complaint.complaint_id,
            'category': complaint.category,
            'location': complaint.location,
            'specific_location': complaint.specific_location,
            'priority': complaint.priority,
            'status': complaint.status,
            'admin_response': complaint.admin_response,
            'created_at': complaint.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'history': [h.to_dict() for h in complaint.history.all()]
        }
    })
