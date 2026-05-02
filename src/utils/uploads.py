import os
import uuid

from werkzeug.utils import secure_filename

from .config import ALLOWED_EXTENSIONS, UPLOAD_FOLDER


def allowed_file(filename: str) -> bool:
    """Check if a file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file) -> str | None:
    """Save an uploaded file to UPLOAD_FOLDER. Returns the filename or None on failure."""
    if file and file.filename and allowed_file(file.filename):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        # Ensure filenames are unique to prevent collisions
        unique_prefix = str(uuid.uuid4())[:8]
        filename = f"{unique_prefix}_{secure_filename(file.filename)}"
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        return filename
    return None
