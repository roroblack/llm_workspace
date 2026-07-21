# -*- coding: utf-8 -*-
"""FastAPI 비즈니스 에이전트 앱의 환경설정 모듈입니다."""

# 운영체제 환경변수를 읽기 위해 os 모듈을 가져옵니다.
import os
# 여러 경로를 안전하게 조합하기 위해 Path 클래스를 가져옵니다.
from pathlib import Path
# 환경변수 파일을 자동으로 읽기 위해 load_dotenv 함수를 가져옵니다.
from dotenv import load_dotenv

# 현재 파일을 기준으로 프로젝트 루트 경로를 계산합니다.
ROOT = Path(__file__).resolve().parents[2]
# 프로젝트 루트의 .env 파일을 읽어 환경변수에 반영합니다.
load_dotenv(ROOT / ".env")
# 원본 데이터가 저장된 data 폴더 경로를 정의합니다.
DATA_DIR = ROOT / "data"
# 정책 및 매뉴얼 PDF가 저장된 docs 폴더 경로를 정의합니다.
DOCS_DIR = DATA_DIR / "docs"
# 생성된 경영 보고서와 차트를 저장할 폴더 경로를 정의합니다.
REPORTS_DIR = ROOT / "reports"
# 벡터 검색 인덱스 등 재사용 데이터를 저장할 폴더 경로를 정의합니다.
CACHE_DIR = ROOT / "cache"
# 실행 로그 파일을 저장할 폴더 경로를 정의합니다.
LOGS_DIR = ROOT / "logs"
# FastAPI 서버의 표시 이름을 환경변수 또는 기본값으로 설정합니다.
APP_NAME = os.getenv("APP_NAME", "Business Agent FastAPI")
# FastAPI 서버의 버전을 환경변수 또는 기본값으로 설정합니다.
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
# 기본 LLM 공급자를 openai 또는 gemini 문자열로 설정합니다.
DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "openai").strip().lower()
# 기본 검색 결과 개수를 정수로 변환해 설정합니다.
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
# 서버 시작 전에 필요한 출력 폴더들을 자동 생성합니다.
for directory in (REPORTS_DIR, CACHE_DIR, LOGS_DIR):
    # 부모 폴더가 없어도 함께 만들고 이미 존재하면 오류를 내지 않습니다.
    directory.mkdir(parents=True, exist_ok=True)
