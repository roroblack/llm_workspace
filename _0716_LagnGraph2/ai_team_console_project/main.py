# -*- coding: utf-8 -*-
"""PyCharm에서 직접 실행하는 제27강 AI Team 콘솔 프로젝트 시작 파일입니다."""

# code 폴더 안의 콘솔 메뉴 함수를 가져옵니다.
from code_app.console_menu import run_console


# 이 파일을 직접 실행했을 때만 콘솔 메뉴를 시작합니다.
if __name__ == "__main__":
    # 사용자가 OpenAI 또는 Gemini를 선택하고 실습 메뉴를 실행하도록 합니다.
    run_console()
