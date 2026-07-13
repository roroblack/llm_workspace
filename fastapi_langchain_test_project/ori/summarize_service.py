# path : app/services/summarize_service.py

from typing import List

from langchain.chains.summarize import load_summarize_chain  # 요약 체인 생성 함수
# load_summarize_chain() 은 LLM + 요약 전략(map_reduce, refine 등)을 조합한 체인을 만들어 주는 함수임

from langchain_openai import ChatOpenAI   
# OpenAI Chat 모델을 LandChain 에서 사용하기 위한 래퍼 클래스임
# 내부적으로 OpenAI API 호출하고, LangChain 의 체인 / 에이전트 / 툴과 연결함
 
from langchain_text_splitters import RecursiveCharacterTextSplitter
# 긴 텍스트를 의미를 최대한 보존하면서 잘게 나누기 위한 텍스트 분할기
# 문단 --> 문장 --> 문자 순으로 재귀적으로 쪼개어 가능한 자연스러운 단위로 분할함

from langchain_core.documents import Document
from langchain.prompts import PromptTemplate # 한국어 처리 프롬프트 생성을 위해 임포트함

from app.core.config import settings

def summarize_documents(docs: List[Document]) -> str:
  '''
  긴 문서를 안전하게 요약하기 위해:
  1) 문서를 chunk로 분할
  2) map_reduce 체인으로 부분 요약 -> 최종 요약
  '''
  # 1) chunking : 가장 무난한 방법임 (chunk 로 분할함)
  # LLM(OpenAI 모델)은 한번에 처리할 수 있는 토큰 수에 제한이 있다.
  # PDF 전체를 그대로 넣으면 에러가 나거나, 요약 품질이 떨어지게 됨
  splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,  # 한 덩어리(chunk)의 최대 문자수
    chunk_overlap=150,  # 인접 chunk 간에 겹쳐서 포함할 문자수
  )
  split_docs = splitter.split_documents(docs)
  
  # 2) LLM 준비 (OpenAI) : OpenAI Chat 모델 쓰기 위한 클래스 객체 생성
  llm = ChatOpenAI(
    model=settings.OPENAI_MODEL,  # 사용할 모델 이름
    api_key=settings.OPENAI_API_KEY, # OpenAI API 키 (.env 에서 로드됨)
    temperature=0.2, # 출력의 창의성/랜덤성 조절값 (0에 가까울수록 사실 중심, 일관된 요약 처리됨)
  )
  
  # 한국어 pdf 파일 요약에 한국어 출력 처리 ====================================
  MAP_PROMPT = PromptTemplate(
        template="""
다음 문서는 PDF의 일부 내용이다.
이 내용을 한국어로 간결하게 요약하시오.

문서 내용:
{text}

한국어 요약:
""",
        input_variables=["text"],
    )

  REDUCE_PROMPT = PromptTemplate(
        template="""
다음은 문서의 부분 요약들이다.
이 요약들을 종합하여 전체 문서를 한국어로 정리하시오.

부분 요약들:
{text}

최종 한국어 요약:
""",
        input_variables=["text"],
    )  
  # ============================================================================
  
  # 3) 요약 체인 : map_reduce
  # 요약 전용 체인을 만들어 주는 펙토리 함수 실행
  chain = load_summarize_chain(
    llm=llm,
    chain_type="map_reduce",
    # map_prompt, combine_prompt 는 한국어 요약 출력을 위해 추가함
    map_prompt=MAP_PROMPT,
    combine_prompt=REDUCE_PROMPT,
  )
  # chain_type="map_reduce":
  '''
  1. map 단계: 각 chunk(Document)를 개별적으로 요약함
  2. reduce 단계: 부분 요약들을 다시 모아서 최종 요약을 생성함
  '''
  
  result = chain.invoke({"input_documents": split_docs})  # 체인 실행
  # 입력은 딕셔너리 형태로 전달
  
  return result.get("output_text", "").strip()  # 반환된 결과값 앞뒤 공백 제거
# def summarize_documents() ------------------------------
