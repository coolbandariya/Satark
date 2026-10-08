"""Upload and media preprocessing helpers for SATARK.

All helpers enforce bounded input sizes before expensive parsing/encoding.
They do not depend on Streamlit so they can be exercised in isolation.
"""

import base64
import hashlib
from io import BytesIO

from PIL import Image
from pypdf import PdfReader

from satark_utils import safe_text

MAX_PDF_BYTES = 25 * 1024 * 1024
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000

def _uploaded_size(uploaded_file):
    """Return an upload size for Streamlit uploads and file-like test inputs."""
    raw_size = getattr(uploaded_file, "size", None)
    try:
        if raw_size is not None:
            return int(raw_size)
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        current = uploaded_file.tell()
        uploaded_file.seek(0, 2)
        size = uploaded_file.tell()
        uploaded_file.seek(current)
        return int(size)
    except Exception:
        pass
    try:
        return len(uploaded_file.getvalue())
    except Exception:
        return None

def extract_pdf_text(uploaded_file):
    size = _uploaded_size(uploaded_file)
    if size is not None and size > MAX_PDF_BYTES:
        raise ValueError("This PDF is larger than SATARK's 25 MB processing limit.")
    try:
        reader = PdfReader(uploaded_file)
    except Exception as exc:
        raise ValueError("SATARK could not read this PDF. It may be corrupted, encrypted, or unsupported.") from exc
    pages = []
    for page in reader.pages[:30]:
        try:
            text = page.extract_text() or ""
            if text.strip(): pages.append(text)
        except Exception:
            pass
    text = "\n\n".join(pages).strip()
    if not text:
        raise ValueError("No readable text was found in this PDF. It may be scanned/image-only. Please use a screenshot/image of the relevant page for vision analysis.")
    return text[:50000]


def image_to_data_url(uploaded_file):
    """Convert one uploaded image to a compact JPEG data URL.

    Kept modest in size (max_side=900, moderate JPEG quality) so a small
    number of images stays well under Groq's on-demand tokens-per-minute
    budget for vision models — full-resolution uploads were previously
    large enough on their own to trip the TPM rate limit."""
    from io import BytesIO
    size = _uploaded_size(uploaded_file)
    if size is not None and size > MAX_IMAGE_BYTES:
        raise ValueError("This image is larger than SATARK's 10 MB processing limit.")
    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    try:
        image = Image.open(uploaded_file)
        width, height = image.size
        if width * height > MAX_IMAGE_PIXELS:
            raise ValueError("This image has too many pixels for SATARK to process safely.")
        image = image.convert("RGB")
        image.load()
    except ValueError:
        raise
    except Image.DecompressionBombError as exc:
        raise ValueError("This image is too large to process safely.") from exc
    except Exception as exc:
        raise ValueError("SATARK could not read this image. Use a valid PNG, JPG or WEBP file.") from exc
    max_side = 900
    if max(image.size) > max_side:
        scale = max_side / max(image.size)
        image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))))
    for quality in (75, 62, 50, 40):
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        if len(encoded) <= 900_000 or quality == 40:
            return f"data:image/jpeg;base64,{encoded}"
    return f"data:image/jpeg;base64,{encoded}"


def images_to_data_urls(uploaded_files, max_images=5):
    """Convert multiple uploaded images while keeping the request manageable."""
    if not uploaded_files:
        return []
    urls = []
    for uploaded_file in list(uploaded_files)[:max_images]:
        urls.append(image_to_data_url(uploaded_file))
    return urls


def uploaded_fingerprint(uploaded_files):
    """Return a content fingerprint so a new scan cannot reuse stale image state."""
    if not uploaded_files:
        return ""
    digest = hashlib.sha256()
    for uploaded_file in uploaded_files:
        try:
            data = uploaded_file.getvalue()
        except Exception:
            data = b""
        digest.update(safe_text(getattr(uploaded_file, "name", "")).encode("utf-8", errors="ignore"))
        digest.update(str(len(data)).encode("ascii"))
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def single_file_fingerprint(uploaded_file):
    """Fingerprint a single uploaded file (used for video scanning)."""
    if not uploaded_file:
        return ""
    try:
        data = uploaded_file.getvalue()
    except Exception:
        data = b""
    digest = hashlib.sha256()
    digest.update(safe_text(getattr(uploaded_file, "name", "")).encode("utf-8", errors="ignore"))
    digest.update(str(len(data)).encode("ascii"))
    digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()
