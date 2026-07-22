# -*- coding: utf-8 -*-
"""pytest가 프로젝트 루트의 app 패키지를 찾도록 경로를 설정합니다."""

# sys는 파이썬 모듈 검색 경로를 수정할 때 사용합니다.
import sys
# pathlib.Path는 테스트 파일 위치에서 프로젝트 루트를 계산합니다.
from pathlib import Path

# tests 폴더의 상위 경로를 프로젝트 루트로 계산합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# 프로젝트 루트가 모듈 검색 경로에 없으면 맨 앞에 추가합니다.
if str(PROJECT_ROOT) not in sys.path:
    # app 패키지를 우선적으로 찾도록 검색 경로 앞에 삽입합니다.
    sys.path.insert(0, str(PROJECT_ROOT))
