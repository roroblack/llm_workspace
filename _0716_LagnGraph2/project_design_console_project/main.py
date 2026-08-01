# -*- coding: utf-8 -*-
"""PyCharm에서 직접 실행하는 제28강 콘솔 프로젝트의 시작 파일입니다."""

# app.console_menu 모듈의 main 함수를 가져옵니다.
from app.console_menu import main


# 현재 파일을 직접 실행한 경우에만 콘솔 메뉴를 시작합니다.
if __name__ == "__main__":
    # 프로그램의 최상위 메뉴 함수를 호출합니다.
    main()
