"""
Parser & validation service for PDF and DOCX resume uploads.
Uses PyMuPDF (fitz) for PDF files and python-docx for DOCX files.
"""

import io
import fitz  # PyMuPDF
import docx

from app.core.config import settings
from app.core.exceptions import AppException

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",  # Browser fallback for binary
}


def validate_file_metadata(
    filename: str, content_type: str, file_size: int, content: bytes | None = None
) -> str:
    """Validate filename extension, MIME type, size, and magic byte signatures.

    Returns normalized file extension ('pdf' or 'docx').
    """
    if file_size == 0:
        raise AppException(
            message="Uploaded file is empty (0 bytes).",
            status_code=400,
        )

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        max_mb = settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)
        raise AppException(
            message=f"File size exceeds maximum allowed limit of {max_mb}MB.",
            status_code=400,
        )

    # Extension check
    dot_idx = filename.rfind(".")
    if dot_idx == -1:
        raise AppException(
            message="File must have an extension (.pdf or .docx).",
            status_code=400,
        )

    ext = filename[dot_idx:].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AppException(
            message=f"Unsupported file extension '{ext}'. Only .pdf and .docx files are allowed.",
            status_code=400,
        )

    # MIME type check
    if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
        raise AppException(
            message=f"Unsupported MIME type '{content_type}'. Only PDF and DOCX files are allowed.",
            status_code=400,
        )

    # Magic byte signature check
    if content:
        if ext == ".pdf":
            if not (content.startswith(b"%PDF-") or b"%PDF-" in content[:1024]):
                raise AppException(
                    message="Invalid file content: Missing %PDF- signature for PDF document.",
                    status_code=400,
                )
        elif ext == ".docx":
            if not content.startswith(b"PK\x03\x04"):
                raise AppException(
                    message="Invalid file content: Missing standard ZIP signature for DOCX document.",
                    status_code=400,
                )

    return ext.lstrip(".")


def extract_text_from_pdf(content: bytes) -> str:
    """Extract readable text from PDF bytes using PyMuPDF (fitz).

    Raises AppException if the PDF is corrupt, encrypted, or empty.
    """
    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise AppException(
            message="Corrupted or invalid PDF file. Unable to parse document structure.",
            status_code=400,
        ) from exc

    if doc.is_encrypted:
        raise AppException(
            message="PDF file is password-protected or encrypted.",
            status_code=400,
        )

    if len(doc) > 50:
        doc.close()
        raise AppException(
            message="PDF exceeds maximum allowed page count (50 pages).",
            status_code=400,
        )

    extracted_pages: list[str] = []
    for page_num in range(len(doc)):
        try:
            page = doc[page_num]
            text = page.get_text()
            if text:
                extracted_pages.append(text)
        except Exception:
            continue

    doc.close()
    full_text = "\n".join(extracted_pages).strip()

    if not full_text:
        raise AppException(
            message="PDF file contains no readable text or is empty.",
            status_code=400,
        )

    return full_text[:500000]


def extract_text_from_docx(content: bytes) -> str:
    """Extract readable text from DOCX bytes using python-docx.

    Raises AppException if the DOCX is corrupt or empty.
    """
    try:
        doc_file = io.BytesIO(content)
        document = docx.Document(doc_file)
    except Exception as exc:
        raise AppException(
            message="Corrupted or invalid DOCX file. Unable to parse document package.",
            status_code=400,
        ) from exc

    paragraphs: list[str] = []
    for p in document.paragraphs:
        if p.text.strip():
            paragraphs.append(p.text.strip())

    for table in document.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                paragraphs.append(row_text)

    full_text = "\n".join(paragraphs).strip()

    if not full_text:
        raise AppException(
            message="DOCX file contains no readable text or is empty.",
            status_code=400,
        )

    return full_text[:500000]


def process_and_extract_resume(filename: str, content_type: str, content: bytes) -> tuple[str, str]:
    """Validate file metadata, perform integrity parsing, and return (file_type, extracted_text)."""
    file_type = validate_file_metadata(filename, content_type, len(content), content=content)

    if file_type == "pdf":
        extracted_text = extract_text_from_pdf(content)
    elif file_type == "docx":
        extracted_text = extract_text_from_docx(content)
    else:
        raise AppException(
            message="Unsupported file type.",
            status_code=400,
        )

    return file_type, extracted_text
