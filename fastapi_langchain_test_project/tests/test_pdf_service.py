from io import BytesIO

import pytest
from starlette.datastructures import Headers, UploadFile

from app.services.pdf_service import (
    PdfValidationError,
    cleanup_temp_file,
    save_upload_to_temp_pdf,
)


def make_upload(data: bytes, filename: str, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(data),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


async def test_rejects_non_pdf():
    upload = make_upload(b"hello", "notes.txt", "text/plain")
    with pytest.raises(PdfValidationError):
        await save_upload_to_temp_pdf(upload, max_size_bytes=1024)


async def test_rejects_empty_pdf():
    upload = make_upload(b"", "empty.pdf", "application/pdf")
    with pytest.raises(PdfValidationError):
        await save_upload_to_temp_pdf(upload, max_size_bytes=1024)


async def test_rejects_oversized_pdf():
    upload = make_upload(b"x" * 5000, "big.pdf", "application/pdf")
    with pytest.raises(PdfValidationError):
        await save_upload_to_temp_pdf(upload, max_size_bytes=1024)


async def test_accepts_valid_pdf_and_writes_temp_file():
    payload = b"%PDF-1.4 fake body"
    upload = make_upload(payload, "doc.pdf", "application/pdf")
    temp_path = await save_upload_to_temp_pdf(upload, max_size_bytes=1024)
    try:
        assert temp_path.exists()
        assert temp_path.read_bytes() == payload
    finally:
        cleanup_temp_file(temp_path)
    assert not temp_path.exists()


async def test_accepts_by_content_type_when_extension_missing():
    upload = make_upload(b"%PDF-1.4", "upload", "application/pdf")
    temp_path = await save_upload_to_temp_pdf(upload, max_size_bytes=1024)
    try:
        assert temp_path.exists()
    finally:
        cleanup_temp_file(temp_path)
