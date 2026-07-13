# 검색된 문서 근거를 OpenAI 또는 Gemini에 전달하는 RAG 응답 서비스입니다.
# LangChain의 표준 Document 타입을 타입 힌트에 사용하기 위해 가져옵니다.
from langchain_core.documents import Document
# 제공된 common.py의 공통 채팅 모델 생성 함수를 가져옵니다.
from common import get_chat


def format_context(results: list[tuple[Document, float]]) -> str:
    """검색 결과를 LLM 프롬프트에 넣기 쉬운 문자열로 변환합니다."""
    # 문서별 근거 문자열을 저장할 빈 리스트를 생성합니다.
    sections: list[str] = []
    # 검색 순위 번호와 Document, 유사도 점수를 순서대로 처리합니다.
    for number, (doc, score) in enumerate(results, start=1):
        # metadata에서 원본 파일 경로를 읽고 없으면 대체 문구를 사용합니다.
        source = doc.metadata.get("source", "알 수 없는 출처")
        # PDF 문서일 때 존재할 수 있는 0부터 시작하는 페이지 번호를 읽습니다.
        page = doc.metadata.get("page")
        # 정수 페이지 번호가 있으면 사용자가 읽는 1부터 시작하는 번호로 변환합니다.
        page_text = f", page={page + 1}" if isinstance(page, int) else ""
        # 근거 번호, 출처, 점수, 본문을 하나의 문자열로 묶어 리스트에 추가합니다.
        sections.append(
            f"[근거 {number}] source={source}{page_text}, score={score:.4f}\n"
            f"{doc.page_content}"
        )
    # 각 근거 사이를 빈 줄 두 개로 구분하여 하나의 프롬프트 문자열로 반환합니다.
    return "\n\n".join(sections)


def answer_with_context(
    provider: str,
    question: str,
    results: list[tuple[Document, float]],
) -> str:
    """선택한 LLM에 근거 제한 프롬프트를 전달하고 텍스트 답변을 반환합니다."""
    # 검색 결과가 없으면 API를 호출하지 않고 안내 문장을 즉시 반환합니다.
    if not results:
        return "검색된 근거가 없어 답변을 생성할 수 없습니다."
    # 검색 결과를 모델 입력용 근거 문자열로 변환합니다.
    context = format_context(results)
    # 환각을 줄이기 위해 제공된 근거만 사용하도록 명시한 프롬프트를 작성합니다.
    prompt = f"""당신은 사내 문서 기반 질의응답 도우미입니다.
아래 [검색 근거]에 포함된 사실만 사용하여 한국어로 답하세요.
근거에 없는 내용은 추측하지 말고 '제공된 문서에서 확인할 수 없습니다'라고 답하세요.
답변 마지막에는 사용한 근거 번호를 표시하세요.

[사용자 질문]
{question}

[검색 근거]
{context}
"""
    # common.py를 통해 OpenAI 또는 Gemini LangChain 채팅 모델을 생성합니다.
    model = get_chat(provider=provider, temperature=0.0)
    # 완성한 프롬프트를 모델에 전달하여 응답 객체를 받습니다.
    response = model.invoke(prompt)
    # LangChain 메시지 객체라면 content를 읽고, 아니면 응답 자체를 사용합니다.
    content = getattr(response, "content", response)
    # 콘솔에서 안전하게 출력할 수 있도록 최종 결과를 문자열로 변환해 반환합니다.
    return str(content)
