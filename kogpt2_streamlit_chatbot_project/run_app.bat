@echo off
REM ------------------------------------------------------------
REM KoGPT2 Streamlit 챗봇 앱을 Windows에서 실행하기 위한 배치 파일입니다.
REM 프로젝트 루트 폴더에서 이 파일을 더블클릭하거나 터미널에서 실행할 수 있습니다.
REM ------------------------------------------------------------

REM 현재 배치 파일이 있는 폴더로 작업 위치를 이동합니다.
cd /d %~dp0

REM 가상환경이 있으면 활성화합니다.
IF EXIST ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Streamlit 앱을 실행합니다.
streamlit run app/streamlit_app.py

REM 실행이 종료되었을 때 터미널 창이 바로 닫히지 않도록 대기합니다.
pause
