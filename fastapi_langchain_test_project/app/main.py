from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.routers.summarize_router import router as summarize_router


app = FastAPI(
    title="PDF Summarizer",
    description="Upload a PDF and receive a JSON summary.",
    version="1.0.0",
)

app.include_router(summarize_router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/api/")


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
