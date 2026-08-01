"""MCP Resource가 반환할 읽기 전용 데이터를 정의합니다."""

import json

from app.services.container import get_container
from app.tools.file_tools import list_doc_files


def runtime_config() -> str:
    """비밀값을 제외한 현재 실행 설정을 JSON으로 반환합니다."""

    container = get_container()
    settings = container.settings
    data = {
        "app_name": settings.app_name,
        "embedding_backend": settings.embedding_backend,
        "vector_backend": settings.vector_backend,
        "qdrant_mode": settings.qdrant_mode,
        "mysql_enabled": settings.mysql_enabled,
        "openai_configured": bool(settings.openai_api_key),
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def document_catalog() -> str:
    """docs 폴더에 있는 문서 목록을 JSON으로 반환합니다."""

    docs_dir = get_container().settings.docs_dir
    files = list_doc_files(docs_dir)
    return json.dumps({"files": files}, ensure_ascii=False, indent=2)

