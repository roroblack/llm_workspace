# path: app/core/config.py

from pydantic_settings import BaseSettings
# BaseSettings 는 환경변수(.env 포함된 변수) --> 파이썬 객체로 설정값을 자동 로딩하거나 검증해주는 베이스 클래스임

# Settings 클래스:
#    애플리케이션에서 사용할 환경설정(환경변수)를 한 곳에 모아두는 용도임
# BaseSettings 를 상속하면, 클래스 필드 (OPENAI_API_KEY 등)를 기준으로 운영체제(OS) 환경변수와
#   .env 파일을 읽어와서 자동으로 매핑 및 검증할 수 있게 됨
class Settings(BaseSettings):
  # .env 에서 읽어옴
  OPENAI_API_KEY: str
  OPENAI_MODEL: str = "gpt-4o-mini"
  
  # 업로드시 파일 용량 제한 (바이트) - 필요시 조정
  MAX_UPLOAD_SIZE: int = 20 * 1024 * 1024  # 20MB
  # 이 값은 라우터에서 검사해서, 용량이 초과된 파일이 업로드되면 413 (Too Large) 에러 코드를 반환하게 될 것임
  
  # Config 클래스 :
  # Pydantic (설정 로더)의 동작 방식을 커스터마이징하기 위한 내부 설정 클래스임
  class Config:
    env_file = ".env"   # Settings 생성할 때 운영체제 환경변수와 현재 프로젝트 루트에 있는 .env 파일도 함께 읽도록 지정
    env_file_encoding = "utf-8"   # .env 파일을 utf-8 문자로 인코딩 처리 지정
  # class Config: ----------------
# class Settings(BaseSettings): --------------------

settings = Settings()  # Settings 생성
# Settings 객체를 전역변수로 생성하면 '전역 싱글톤' 적용함
'''
앱이 실행되는 순간:
 - .env 파일과 환경변수를 읽어 들이고
 - OPENAI_API_KEY 같은 필수값이 있는지 검사하고
 - 타입 (int, str) 에 맞게 변환한 뒤
 - Settings 인스턴스를 만듦
 
주의 : 필수값이 없거나 타입 변환이 안 되면 에러가 발생할 것임 
'''
  