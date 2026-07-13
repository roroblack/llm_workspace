# Implementation Plan

## Goal
Make the project match the README: a FastAPI + LangChain service that accepts a PDF upload, reads the PDF content, summarizes it with OpenAI, and returns a JSON response.

## Planned Work
1. Create the README-described package structure under `app/`.
2. Add settings loading for `.env`, including `OPENAI_API_KEY`.
3. Add a FastAPI application entry point in `app/main.py`.
4. Add an `/api/` router with a browser upload form.
5. Add a `/api/summarize` endpoint for PDF uploads.
6. Add a PDF service using `langchain-community` and `pypdf`.
7. Add a summary service using `langchain-openai`.
8. Add validation for file type, empty uploads, file size, missing API key, and extraction failures.
9. Verify the app can import and start.
10. Update the checklist and write a final report.

## File Plan
- `app/main.py`: FastAPI app creation and router registration.
- `app/core/config.py`: Settings and `.env` loading.
- `app/routers/summarize_router.py`: API form and upload endpoint.
- `app/services/pdf_service.py`: PDF validation, temporary file handling, and text extraction.
- `app/services/summarize_service.py`: LangChain/OpenAI summary logic.
- `reports/project_checklist.md`: Progress checklist.
- `reports/final_report.md`: Final result after implementation and verification.
