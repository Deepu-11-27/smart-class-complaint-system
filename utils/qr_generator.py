import io
import base64
import urllib.parse
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask


def get_complaint_url(location_name: str, base_url: str) -> str:
    """Build URL pointing to /complaint?location=<encoded>"""
    encoded_loc = urllib.parse.quote(location_name.strip())
    clean_base = base_url.rstrip('/')
    return f"{clean_base}/complaint?location={encoded_loc}"


def generate_qr_image(data_text: str, box_size: int = 10, border: int = 2):
    """
    Generate clean, high-contrast QR code image.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data_text)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1a202c", back_color="#ffffff")
    return img


def generate_location_qr_bytes(location_name: str, base_url: str, box_size: int = 10) -> bytes:
    """Generate raw PNG bytes for a given location"""
    url = get_complaint_url(location_name, base_url)
    img = generate_qr_image(url, box_size=box_size)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def generate_location_qr_base64(location_name: str, base_url: str, box_size: int = 10) -> str:
    """Generate base64 encoded data URI string for embedding in templates"""
    png_bytes = generate_location_qr_bytes(location_name, base_url, box_size)
    b64_str = base64.b64encode(png_bytes).decode('ascii')
    return f"data:image/png;base64,{b64_str}"
