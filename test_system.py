"""
Comprehensive automated tests for Smart Class Complaint System
Verifies:
1. Public pages: /, /complaint, /track, /success
2. Location detection from QR code query parameter
3. Anonymous submission without student personal details
4. Unique Complaint ID generation (CMP-YYYY-XXXX)
5. Tracking page status resolution
6. Admin authentication
7. Admin dashboard metrics and Chart analytics API
8. Complaint status update and admin response workflow
9. Location management and QR code image generation
10. CSV Report export (verifying zero student personal info in export)
"""
import unittest
from app import create_app
from models import db
from models.models import Admin, Complaint, Location, ComplaintStatusHistory


class SmartComplaintSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_01_public_home(self):
        """Test home page loads with required headings and status counters"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Smart Class Complaint System", response.data)
        self.assertIn(b"REPORT THE ISSUE, NOT THE STUDENT", response.data)
        self.assertIn(b"Scan QR Code", response.data)

    def test_02_complaint_page_with_qr_location(self):
        """Test /complaint?location=Classroom%20A101 auto-detects location"""
        response = self.client.get('/complaint?location=Classroom%20A101')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Complaint Location:", response.data)
        self.assertIn(b"Classroom A101", response.data)
        self.assertIn(b"Your personal details are not required", response.data)
        # Verify NO student personal input fields exist in HTML
        self.assertNotIn(b'name="student_name"', response.data)
        self.assertNotIn(b'name="roll_number"', response.data)
        self.assertNotIn(b'name="student_id"', response.data)
        self.assertNotIn(b'name="email"', response.data)
        self.assertNotIn(b'name="phone"', response.data)
        # Verify NO file input
        self.assertNotIn(b'type="file"', response.data)

    def test_03_submit_anonymous_complaint(self):
        """Test submitting a complaint in student's own words"""
        response = self.client.post('/complaint', data={
            'location': 'Classroom A101',
            'specific_location': 'Row 2 near chalkboard',
            'category': 'Classroom Issue',
            'faculty_staff_name': '',
            'description': 'The whiteboard projector has heavy flickering and shuts down after 5 minutes.',
            'priority': 'High'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Complaint Submitted Successfully", response.data)
        self.assertIn(b"Your Unique Complaint ID", response.data)
        self.assertIn(b"CMP-", response.data)

        # Check database
        with self.app.app_context():
            latest = Complaint.query.filter_by(location='Classroom A101').order_by(Complaint.id.desc()).first()
            self.assertIsNotNone(latest)
            self.assertEqual(latest.priority, 'High')
            self.assertEqual(latest.status, 'Pending')
            self.assertTrue(latest.complaint_id.startswith('CMP-'))

    def test_04_submit_faculty_complaint(self):
        """Test submitting a faculty-related complaint with optional faculty name"""
        response = self.client.post('/complaint', data={
            'location': 'Department Office',
            'category': 'Faculty Issue',
            'faculty_staff_name': 'Dr. HOD Physics',
            'description': 'Office hours are consistently missed without prior notification.',
            'priority': 'Medium'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Complaint Submitted Successfully", response.data)

        with self.app.app_context():
            c = Complaint.query.filter_by(faculty_staff_name='Dr. HOD Physics').first()
            self.assertIsNotNone(c)
            self.assertEqual(c.category, 'Faculty Issue')

    def test_05_track_complaint(self):
        """Test public tracking by Complaint ID"""
        with self.app.app_context():
            c = Complaint.query.first()
            self.assertIsNotNone(c)
            cid = c.complaint_id

        # Track via GET query
        response = self.client.get(f'/track?id={cid}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(cid.encode('utf-8'), response.data)
        self.assertIn(b"Track Complaint Status", response.data)

        # Track via POST form
        response = self.client.post('/track', data={'complaint_id': cid})
        self.assertEqual(response.status_code, 200)
        self.assertIn(cid.encode('utf-8'), response.data)

    def test_06_admin_login_and_dashboard(self):
        """Test admin login and access to protected dashboard"""
        # Login
        response = self.client.post('/admin/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"System Overview", response.data)
        self.assertIn(b"Total Complaints", response.data)

    def test_07_admin_update_status_and_response(self):
        """Test admin updating complaint status and adding admin response"""
        # Login first
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'admin123'})

        with self.app.app_context():
            c = Complaint.query.filter_by(status='Pending').first()
            self.assertIsNotNone(c)
            cid = c.id
            comp_id_code = c.complaint_id

        # Update status
        response = self.client.post(f'/admin/complaints/{cid}', data={
            'action_type': 'update_status',
            'status': 'Resolved',
            'admin_response': 'The projector bulb and HDMI cable were replaced by the AV team.',
            'status_note': 'Replaced bulb and tested resolution.'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        # Verify updated in DB
        with self.app.app_context():
            updated = db.session.get(Complaint, cid)
            self.assertEqual(updated.status, 'Resolved')
            self.assertIn("AV team", updated.admin_response)

        # Now verify student sees the updated response on public tracking page
        response = self.client.get(f'/track?id={comp_id_code}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Resolved", response.data)
        self.assertIn(b"The projector bulb and HDMI cable were replaced", response.data)

    def test_08_qr_api_and_generation(self):
        """Test QR code API endpoint generates valid PNG image"""
        with self.app.app_context():
            loc = Location.query.first()
            self.assertIsNotNone(loc)
            loc_id = loc.id

        response = self.client.get(f'/api/qr/{loc_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'image/png')
        # Check PNG signature: 89 50 4E 47 0D 0A 1A 0A
        self.assertTrue(response.data.startswith(b'\x89PNG\r\n\x1a\n'))

    def test_09_analytics_api(self):
        """Test analytics JSON API returns structured chart data"""
        response = self.client.get('/api/analytics')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('categories', data)
        self.assertIn('statuses', data)
        self.assertIn('locations', data)
        self.assertIn('timeline', data)

    def test_10_csv_export_privacy_guarantee(self):
        """Test CSV export does NOT contain student personal information"""
        # Login
        self.client.post('/admin/login', data={'username': 'admin', 'password': 'admin123'})

        response = self.client.get('/admin/reports/export-csv')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Complaint ID,Date Submitted (UTC),Category,Location", response.data)
        # Check header does NOT contain student identity fields
        header_line = response.data.splitlines()[0].decode('utf-8')
        self.assertNotIn("student_name", header_line.lower())
        self.assertNotIn("roll_number", header_line.lower())
        self.assertNotIn("email", header_line.lower())
        self.assertNotIn("phone", header_line.lower())
        self.assertNotIn("ip_address", header_line.lower())


if __name__ == '__main__':
    unittest.main()
