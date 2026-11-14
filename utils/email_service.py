import os
import smtplib
import threading
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)


def send_complaint_notification(complaint, app_config):
    """
    Sends email notification to the administrator asynchronously.
    Guaranteed not to raise an unhandled exception or block the main thread.
    """
    thread = threading.Thread(
        target=_send_email_worker,
        args=(complaint.to_dict(), app_config),
        daemon=True
    )
    thread.start()


def _send_email_worker(complaint_dict: dict, app_config):
    """Worker function executed in background thread"""
    mail_server = app_config.get('MAIL_SERVER')
    mail_port = app_config.get('MAIL_PORT', 587)
    mail_use_tls = app_config.get('MAIL_USE_TLS', True)
    mail_username = app_config.get('MAIL_USERNAME', '')
    mail_password = app_config.get('MAIL_PASSWORD', '')
    sender = app_config.get('MAIL_DEFAULT_SENDER', 'complaints@smartcampus.edu')
    recipient = app_config.get('ADMIN_NOTIFICATION_EMAIL', 'admin@smartcampus.edu')

    complaint_id = complaint_dict.get('complaint_id')
    category = complaint_dict.get('category')
    description = complaint_dict.get('description')
    location = complaint_dict.get('location')
    specific_loc = complaint_dict.get('specific_location')
    priority = complaint_dict.get('priority')
    faculty_staff = complaint_dict.get('faculty_staff_name')
    date_str = complaint_dict.get('created_date')
    time_str = complaint_dict.get('created_time')

    subject = f"New Complaint Received - {complaint_id}"

    # Build plain text body
    lines = [
        "================================================",
        "SMART CLASS COMPLAINT SYSTEM - NEW NOTIFICATION",
        "================================================",
        "",
        f"Complaint ID   : {complaint_id}",
        f"Category       : {category}",
        f"Location       : {location}" + (f" ({specific_loc})" if specific_loc else ""),
        f"Priority       : {priority}",
        f"Date Submitted : {date_str} at {time_str}",
    ]

    if faculty_staff:
        lines.append(f"Faculty/Staff  : {faculty_staff}")

    lines.extend([
        "",
        "--- Issue Description ---",
        description,
        "",
        "------------------------------------------------",
        "Notice: This is an anonymous complaint. No student identity",
        "information was collected or attached to this report.",
        "------------------------------------------------",
    ])
    text_content = "\n".join(lines)

    # Build HTML body
    faculty_row = f"<tr><td style='padding:8px;font-weight:bold;'>Faculty/Staff Mentioned:</td><td style='padding:8px;'>{faculty_staff}</td></tr>" if faculty_staff else ""
    priority_color = {
        'Emergency': '#dc3545',
        'High': '#fd7e14',
        'Medium': '#0d6efd',
        'Low': '#6c757d'
    }.get(priority, '#0d6efd')

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>{subject}</title>
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; color: #1e293b;">
      <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
        <div style="background: #1e293b; color: #ffffff; padding: 20px; text-align: center;">
          <h2 style="margin: 0; font-size: 20px; letter-spacing: 0.5px;">Smart Class Complaint System</h2>
          <p style="margin: 5px 0 0 0; font-size: 13px; color: #94a3b8;">Confidential Incident Notification</p>
        </div>
        <div style="padding: 24px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 2px solid #f1f5f9; padding-bottom: 15px;">
            <h3 style="margin: 0; color: #0f172a; font-size: 18px;">Complaint #{complaint_id}</h3>
            <span style="background-color: {priority_color}; color: white; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: bold; text-transform: uppercase;">
              {priority} Priority
            </span>
          </div>

          <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
            <tr style="border-bottom: 1px solid #f1f5f9;">
              <td style="padding: 8px 0; font-weight: bold; color: #475569; width: 35%;">Category:</td>
              <td style="padding: 8px 0; color: #0f172a;">{category}</td>
            </tr>
            <tr style="border-bottom: 1px solid #f1f5f9;">
              <td style="padding: 8px 0; font-weight: bold; color: #475569;">Location:</td>
              <td style="padding: 8px 0; color: #0f172a;">{location} {f'— <em>{specific_loc}</em>' if specific_loc else ''}</td>
            </tr>
            {faculty_row}
            <tr style="border-bottom: 1px solid #f1f5f9;">
              <td style="padding: 8px 0; font-weight: bold; color: #475569;">Submission Date:</td>
              <td style="padding: 8px 0; color: #0f172a;">{date_str} at {time_str}</td>
            </tr>
          </table>

          <div style="background-color: #f8fafc; border-left: 4px solid #3b82f6; padding: 16px; border-radius: 4px; margin-bottom: 20px;">
            <h4 style="margin: 0 0 8px 0; font-size: 13px; text-transform: uppercase; color: #64748b;">Issue Description:</h4>
            <p style="margin: 0; font-size: 15px; line-height: 1.6; color: #1e293b; white-space: pre-wrap;">{description}</p>
          </div>

          <div style="background-color: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 6px; padding: 12px; font-size: 12px; color: #065f46;">
            <strong>Confidentiality Notice:</strong> This complaint was submitted anonymously. In accordance with student privacy protection principles, no student name, roll number, or personal details were recorded.
          </div>
        </div>
        <div style="background: #f8fafc; padding: 16px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0;">
          Smart Class Anonymous Complaint System &copy; {datetime.now().year}
        </div>
      </div>
    </body>
    </html>
    """

    # If mail_username is not provided, simulate sending by logging
    if not mail_username or not mail_password:
        print("\n" + "="*60)
        print(f"[SMTP SIMULATION] Email Notification for {complaint_id}")
        print(f"To: {recipient}")
        print(f"Subject: {subject}")
        print("-"*60)
        print(text_content)
        print("="*60 + "\n")
        logger.info(f"[Email Service] Simulated notification for {complaint_id} to {recipient} (SMTP credentials not configured)")
        return

    # Real SMTP delivery
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(mail_server, mail_port, timeout=15) as server:
            if mail_use_tls:
                server.starttls()
            server.login(mail_username, mail_password)
            server.sendmail(sender, [recipient], msg.as_string())

        logger.info(f"[Email Service] Successfully delivered notification email for {complaint_id} to {recipient}")
    except Exception as e:
        logger.warning(f"[Email Service] Failed to send email for {complaint_id}: {str(e)}")
