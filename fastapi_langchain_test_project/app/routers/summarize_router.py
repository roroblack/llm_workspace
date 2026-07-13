from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings, get_settings
from app.services.pdf_service import (
    PdfExtractionError,
    PdfValidationError,
    cleanup_temp_file,
    extract_pdf_text,
    save_upload_to_temp_pdf,
)
from app.services.summarize_service import (
    SummaryConfigurationError,
    SummaryServiceError,
    summarize_text,
)


router = APIRouter(prefix="/api", tags=["summary"])


@router.get("/", response_class=HTMLResponse)
async def upload_form() -> str:
    return """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>PDF Summarizer</title>
        <style>
          :root {
            color-scheme: light;
            font-family: Arial, sans-serif;
            line-height: 1.5;
          }
          body {
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            background: #f4f7fb;
            color: #172033;
          }
          main {
            width: min(92vw, 520px);
            padding: 32px;
            background: #ffffff;
            border: 1px solid #d9e2ef;
            border-radius: 8px;
            box-shadow: 0 16px 40px rgba(23, 32, 51, 0.08);
          }
          h1 {
            margin: 0 0 8px;
            font-size: 28px;
          }
          p {
            margin: 0 0 24px;
            color: #4e5d73;
          }
          form {
            display: grid;
            gap: 16px;
          }
          input[type="file"] {
            width: 100%;
            padding: 12px;
            border: 1px solid #b7c4d8;
            border-radius: 6px;
            background: #fbfdff;
          }
          button {
            min-height: 44px;
            border: 0;
            border-radius: 6px;
            background: #1f6feb;
            color: #ffffff;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
          }
          button:hover {
            background: #195fc9;
          }
        </style>
      </head>
      <body>
        <main>
          <h1>PDF Summarizer</h1>
          <p>Upload a PDF file to receive a JSON summary.</p>
          <form action="/api/summarize" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept="application/pdf,.pdf" required>
            <button type="submit">Summarize PDF</button>
          </form>
        </main>
      </body>
    </html>
    """


@router.post("/summarize")
async def summarize_pdf(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    temp_path: Path | None = None

    try:
        temp_path = await save_upload_to_temp_pdf(
            file=file,
            max_size_bytes=settings.max_upload_size_mb * 1024 * 1024,
        )
        text = await run_in_threadpool(extract_pdf_text, temp_path)
        summary = await summarize_text(
            text,
            settings.openai_api_key,
            settings.openai_model,
            settings.summary_language,
        )
    except PdfValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PdfExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SummaryConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except SummaryServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        if temp_path is not None:
            cleanup_temp_file(temp_path)

    return {
        "filename": file.filename,
        "text_characters": len(text),
        "summary": summary,
    }
