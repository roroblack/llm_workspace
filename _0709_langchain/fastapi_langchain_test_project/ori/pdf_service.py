# path: app/services/pdf_service.py

import os   # 파이썬 표준 라이브러리임 : 운영체제 관련 기능을 제공하는 모듈임
# 파일 디스크립터 (fd) 를 닫기 위해 임포트함

import tempfile  # 파이썬 표준 라이브러리임 : 임시 파일/디렉토리를 만들기 위한 모듈임
# windows/linux 모두 사용할 수 있음

from typing import List, Tuple  # 함수 매개변수/리턴 타입에 명시하기 위한 타입 힌트 모듈임
# List : 리스트 타입 힌트, Tuple : 튜플 타입 힌트

from langchain_community.document_loaders import PyPDFLoader
# PyPDFLoader : 내부적으로 pypdf 등을 이용해 PDF 텍스트를 읽어서 LangChain Document 형태로 반환해 주는 클래스임

from langchain_core.documents import Document  # LangChain 의 문서 표준 타입
# Document 에는 page_content (문서 본문 텍스트), metadata (페이지 번호, 소스 파일 경로 등 부가정보 딕셔너리) 포함

def save_upload_to_temp(pdf_bytes: bytes, suffix: str = ".pdf") -> str:
  '''
  업로드된 pdf 바이너리를 임시 파일로 저장하고 경로를 반환함
  windows에서도 안전하게 동작하도록 tempfile 사용함
  '''
  fd, path = tempfile.mkstemp(suffix=suffix)
  # tempfile.mkstemp():
  #  - (fd, path) 형태로 반환
  #     fd : 운영체제가 열어준 파일 디스크립터 (정수)
  #     path : 생성된 임시 파일의 실제 경로 (문자열)
  # suffix=".pdf":
  #  - 임시 파일 확장자를 .pdf 로 지정
  
  os.close(fd)  # mkstemp() 가 열어둔 파일 핸들을 먼저 닫음
  # 윈도우즈에서는 열려있는 파일을 다시 open(path, "wb")하면 "사용중인 파일" 관련 오류 발생할 수 있어서 닫아줌
  
  with open(path, "wb") as f:  # with 문 : 블록이 끝나면 자동으로 파일을 close() 함 (리소스 누수 방지)
    f.write(pdf_bytes)  # 업로드된 pdf 바이트 데이터를 임시 파일에 그대로 기록함
    
  return path  # 저장한 임시 파일 경로를 반환
# def save_upload_to_temp() -------------------------


def load_pdf_documents(pdf_path: str) -> Tuple[List[Document], int]:
  '''
  pdf를 LangChain Document 리스트로 로딩함
  mode='page'로 페이지 단위로 문서로 만들고, metadata에 page 정보가 포함되게 처리함
  '''
  loader = PyPDFLoader(pdf_path)
  # PyPDFLoader(pdf_path, mode="page"):
  #  - pdf_path: 읽을 pdf 파일 경로
  #  - mode="page": pdf 를 페이지 단위로 쪼개서 Document 만듦 (pdf 가 10페이지이면 Document가 10개임)
  #           LangChain 버전에 따라 mode 인수는 없을 수도 있음
  
  docs = loader.load()   # 각 page 가 Document 로 로드됨
  # loader.load():
  #   pdf 를 실제로 읽고, 텍스트를 추출한 뒤 Document 리스트로 반환함
  
  return docs, len(docs)  # Document 리스트와 갯수 반환
# def load_pdf_documents() -------------------------------------
