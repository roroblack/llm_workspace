# 운영체제 환경변수를 읽기 위해 os 모듈을 불러옵니다.
import os

# .env 파일의 환경변수를 자동으로 로드하기 위해 dotenv 함수를 불러옵니다.
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일을 읽어 환경변수로 등록합니다.
load_dotenv()

# OpenAI API Key를 환경변수에서 읽습니다.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# OpenAI API 사용 여부를 환경변수에서 읽습니다. 기본값은 비용 보호를 위해 비활성화입니다.
ENABLE_OPENAI = os.getenv("ENABLE_OPENAI", "false").strip().lower() in {"1", "true", "yes", "on"}

# 사용할 OpenAI 모델명을 환경변수에서 읽고, 없으면 기본 모델을 사용합니다.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# 사용자가 실제 구글 설문지를 연결할 때 사용할 기본 링크입니다.
SURVEY_LINK = os.getenv("SURVEY_LINK", "https://forms.gle/example")

# FastAPI 앱 제목입니다.
APP_TITLE = "Survey AI Chatbot"
