"""FastAPI 애플리케이션 객체를 생성합니다."""

# FastAPI 클래스를 가져옵니다.
from fastapi import FastAPI
# 정적 파일 제공을 위해 StaticFiles를 가져옵니다.
from fastapi.staticfiles import StaticFiles
# 프로젝트 API 라우터를 가져옵니다.
from app.api.routes import router
# 공통 설정 객체를 가져옵니다.
from app.core.config import settings

# 데이터 및 저장 디렉터리를 생성합니다.
settings.create_directories()
# FastAPI 애플리케이션 객체를 생성합니다.
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="프롬프트와 음성 STT를 조건부 GAN 이미지 생성으로 연결하는 애플리케이션",
)
# CSS와 JavaScript 파일을 /static URL로 제공합니다.
app.mount("/static", StaticFiles(directory=str(settings.static_dir)), name="static")
# 음성, 텍스트, 이미지 저장 파일을 /storage URL로 제공합니다.
app.mount(
    "/storage",
    StaticFiles(directory=str(settings.project_root / "storage")),
    name="storage",
)
# 모든 API와 메인 페이지 라우터를 등록합니다.
app.include_router(router)
