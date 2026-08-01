# -*- coding: utf-8 -*-
"""제공된 code/common.py를 수정하지 않고 불러오기 위한 연결 모듈입니다."""

# pathlib는 프로젝트의 절대 경로를 안전하게 계산할 때 사용합니다.
import pathlib
# sys는 제공된 common.py가 있는 code 폴더를 import 검색 경로에 넣을 때 사용합니다.
import sys

# 현재 파일(code_app/common_bridge.py)의 부모의 부모가 프로젝트 루트입니다.
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
# 사용자가 제공한 common.py를 그대로 둔 폴더의 경로입니다.
COMMON_DIR = PROJECT_ROOT / "code"

# 같은 경로가 중복 등록되지 않도록 확인한 다음 Python 모듈 검색 경로에 추가합니다.
if str(COMMON_DIR) not in sys.path:
    # 목록 앞쪽에 넣어 프로젝트의 common.py가 우선 검색되게 합니다.
    sys.path.insert(0, str(COMMON_DIR))

# 제공된 공통 모듈의 경로 상수와 모델 생성 함수를 그대로 가져옵니다.
from common import DATA, ROOT, get_chat  # noqa: E402

# 다른 모듈이 명시적으로 사용할 공개 이름을 정의합니다.
__all__ = ["DATA", "ROOT", "get_chat", "PROJECT_ROOT"]
