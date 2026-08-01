from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile
from langchain_community.document_loaders import PyPDFLoader


class PdfValidationError(ValueError):
    """Raised when an uploaded file is not a usable PDF."""


class PdfExtractionError(RuntimeError):
    """Raised when PDF text cannot be extracted."""


PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
CHUNK_SIZE = 1024 * 1024


async def save_upload_to_temp_pdf(file: UploadFile, max_size_bytes: int) -> Path:
    filename = file.filename or ""
    content_type = file.content_type or ""

    if not filename.lower().endswith(".pdf") and content_type not in PDF_CONTENT_TYPES:
        raise PdfValidationError("Only PDF uploads are supported.")

    temp_file = NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_path = Path(temp_file.name)
    total_size = 0

    try:
        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break

            total_size += len(chunk)
            if total_size > max_size_bytes:
                raise PdfValidationError(
                    f"PDF is too large. Maximum size is {max_size_bytes // (1024 * 1024)} MB."
                )

            temp_file.write(chunk)
    except Exception:
        temp_file.close()
        cleanup_temp_file(temp_path)
        raise
    finally:
        if not temp_file.closed:
            temp_file.close()

    if total_size == 0:
        cleanup_temp_file(temp_path)
        raise PdfValidationError("Uploaded PDF is empty.")

    return temp_path


def extract_pdf_text(pdf_path: Path) -> str:
    try:
        documents = PyPDFLoader(str(pdf_path)).load()
    except Exception as exc:
        raise PdfExtractionError("Failed to read the uploaded PDF.") from exc

    text = "\n\n".join(
        document.page_content.strip()
        for document in documents
        if document.page_content and document.page_content.strip()
    ).strip()

    if not text:
        raise PdfExtractionError("No readable text was found in the PDF.")

    return text


def cleanup_temp_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
