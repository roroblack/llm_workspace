# -*- coding: utf-8 -*-
"""수정하지 않은 code/common.py를 안전하게 가져오는 연결 모듈입니다."""

# 파일 경로를 다루기 위해 pathlib을 가져옵니다.
import pathlib
# 동적 모듈 로딩을 위해 importlib.util을 가져옵니다.
import importlib.util

# 현재 프로젝트의 루트 디렉터리 경로를 계산합니다.
ROOT = pathlib.Path(__file__).resolve().parent.parent
# 원본 공통 모듈 파일의 정확한 경로를 지정합니다.
COMMON_PATH = ROOT / "code" / "common.py"
# 원본 파일로부터 모듈 명세를 생성합니다.
SPEC = importlib.util.spec_from_file_location("ch28_original_common", COMMON_PATH)
# 모듈 명세를 사용해 빈 모듈 객체를 생성합니다.
COMMON = importlib.util.module_from_spec(SPEC)
# 로더가 존재하는지 명시적으로 확인합니다.
if SPEC is None or SPEC.loader is None:
    # 로더 생성에 실패하면 원인을 알 수 있는 예외를 발생시킵니다.
    raise ImportError(f"공통 모듈을 불러올 수 없습니다: {COMMON_PATH}")
# 원본 common.py 코드를 생성한 모듈 객체 안에서 실행합니다.
SPEC.loader.exec_module(COMMON)

# 다른 모듈이 원본 common.py의 ROOT를 그대로 사용할 수 있게 공개합니다.
PROJECT_ROOT = COMMON.ROOT
# 다른 모듈이 원본 common.py의 DATA를 그대로 사용할 수 있게 공개합니다.
DATA = COMMON.DATA
# 다른 모듈이 원본 common.py의 DOCS를 그대로 사용할 수 있게 공개합니다.
DOCS = COMMON.DOCS
# 다른 모듈이 provider별 ChatModel 생성 함수를 사용할 수 있게 공개합니다.
get_chat = COMMON.get_chat
