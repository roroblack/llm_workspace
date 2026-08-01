# path: app/core/config.py
# 환경 설정 관리

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
  '''
  각 작업별로 기본 모델을 지정함 
  (실습이므로 많이 쓰는 범용 모델들)
  '''
  # Text Classification (감성분석) 예시 모델
  # distilbert 기반의 SST-2 (영어 감성분석)로 가볍고 빠름
  CLS_MODEL: str = "distilbert-base-uncased-finetuned-sst-2-english"
  
  # Summarization(요약) 예시 모델: BART CNN 요약 모델
  # BART 는 seq2seq 모델로 요약/번역 등에 활용됨. bart-large-cnn 은 요약으로 유명함
  SUM_MODEL: str = "facebook/bart-large-cnn"
  
  # Translation(번역) 예시 모델: MarianMT (영->한)
  # 언어쌍에 따라 모델명이 달라짐 
  TRANS_MODEL: str = "facebook/nllb-200-distilled-600M"
  
  # CPU 환경이므로 device = -1 (pipeline 에서 -1은 CPU를 의미함)
  DEVICE: int = -1  # MacOS GPU 제공됨: GPU 0 (CUDA:0) -> 0, GPU 1 -> 1 로 지정함
  
  # 요약 파라미터 기본값
  SUM_MAX_LENGTH: int = 120
  SUM_MIN_LENGTH: int = 30
  
# class end -----------------

settings = Settings()  # 싱글톤 적용
  