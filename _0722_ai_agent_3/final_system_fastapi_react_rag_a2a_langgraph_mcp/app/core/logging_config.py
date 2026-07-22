# -*- coding: utf-8 -*-
"""콘솔과 파일에 동시에 기록하는 구조적 로깅 설정 모듈입니다."""

# json은 로그 레코드를 JSON 문자열로 직렬화합니다.
import json
# logging은 파이썬 표준 로깅 기능을 제공합니다.
import logging
# datetime은 로그 발생 시각을 ISO 형식으로 만듭니다.
from datetime import datetime, timezone

# 프로젝트 로그 경로를 가져옵니다.
from app.core.settings import LOG_DIR


# JsonFormatter는 각 로그를 한 줄 JSON으로 변환합니다.
class JsonFormatter(logging.Formatter):
    """운영 환경에서 검색하기 쉬운 JSON 로그 형식을 생성합니다."""

    # format 메서드는 logging이 각 레코드를 출력할 때 호출합니다.
    def format(self, record: logging.LogRecord) -> str:
        """로그 레코드를 JSON 문자열로 변환합니다."""
        # payload는 로그에서 공통으로 사용할 핵심 필드를 담습니다.
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # record에 request_id가 있으면 요청 추적을 위해 함께 기록합니다.
        if hasattr(record, "request_id"):
            # getattr은 선택적 속성을 안전하게 읽습니다.
            payload["request_id"] = getattr(record, "request_id")
        # ensure_ascii=False는 한국어를 유니코드 이스케이프 없이 기록합니다.
        return json.dumps(payload, ensure_ascii=False)


# setup_logging 함수는 중복 핸들러 없이 로깅을 초기화합니다.
def setup_logging() -> logging.Logger:
    """애플리케이션 공용 로거를 생성하고 반환합니다."""
    # 로그 디렉터리가 없으면 자동으로 생성합니다.
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    # 동일 이름의 로거를 가져옵니다.
    logger = logging.getLogger("final_system")
    # INFO 이상 수준을 기록하도록 지정합니다.
    logger.setLevel(logging.INFO)
    # 상위 root 로거로 중복 전파되지 않도록 막습니다.
    logger.propagate = False
    # 이미 핸들러가 있으면 기존 설정을 그대로 재사용합니다.
    if logger.handlers:
        # 초기화된 로거를 즉시 반환합니다.
        return logger
    # JSON 포매터 객체를 생성합니다.
    formatter = JsonFormatter()
    # 콘솔 핸들러는 PyCharm 실행창에 로그를 표시합니다.
    console_handler = logging.StreamHandler()
    # 콘솔에도 JSON 포맷을 적용합니다.
    console_handler.setFormatter(formatter)
    # 파일 핸들러는 logs/app.log 파일에 로그를 누적합니다.
    file_handler = logging.FileHandler(LOG_DIR / "app.log", encoding="utf-8")
    # 파일 로그에도 동일한 JSON 포맷을 적용합니다.
    file_handler.setFormatter(formatter)
    # 두 핸들러를 공용 로거에 등록합니다.
    logger.addHandler(console_handler)
    # 파일 핸들러도 등록합니다.
    logger.addHandler(file_handler)
    # 완성된 로거를 반환합니다.
    return logger
