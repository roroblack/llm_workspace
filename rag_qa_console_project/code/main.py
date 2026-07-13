# -*- coding: utf-8 -*-
"""제16강 RAG QA 실습용 콘솔 애플리케이션의 시작 파일입니다."""

# JSON과 유사한 딕셔너리를 보기 좋게 출력하기 위해 pprint를 가져옵니다.
from pprint import pprint

# 공통 설정과 경로를 확인하기 위해 common 모듈의 값을 가져옵니다.
from common import DATA, DOCS, GEMINI_MODEL, ROOT

# RAG QA의 실제 기능을 담당하는 서비스 함수들을 가져옵니다.
from rag_service import (
    answer,
    compare_k,
    create_lcel_chain,
    extract_sources,
    format_docs,
    get_retriever,
    llm_rerank,
    load_policy_documents,
    split_documents,
    torch_rerank,
)


def print_separator(title: str) -> None:
    """메뉴 실행 결과를 구분하기 위한 제목선을 출력합니다."""

    # 결과 영역의 시작을 한눈에 알아볼 수 있도록 구분선을 출력합니다.
    print("\n" + "=" * 78)

    # 전달받은 제목을 출력합니다.
    print(title)

    # 제목 아래에도 동일한 길이의 구분선을 출력합니다.
    print("=" * 78)


def select_provider() -> str:
    """사용자가 Gemini 또는 OpenAI를 선택하도록 하고 내부 제공자 이름을 반환합니다."""

    # 제공자 선택 안내를 출력합니다.
    print("\n[모델 제공자 선택]")

    # Gemini 선택 번호를 출력합니다.
    print("1. Google Gemini")

    # OpenAI 선택 번호를 출력합니다.
    print("2. OpenAI")

    # 사용자의 선택을 문자열로 입력받고 앞뒤 공백을 제거합니다.
    choice = input("선택 [기본값 1]: ").strip()

    # 2를 선택한 경우 OpenAI 내부 이름을 반환합니다.
    if choice == "2":
        return "openai"

    # 그 외 입력과 빈 입력은 기본 제공자인 Gemini로 처리합니다.
    return "gemini"


def input_question(default: str = "환불은 며칠 걸리나요?") -> str:
    """질문을 입력받고 빈 입력이면 기본 질문을 반환합니다."""

    # 기본 질문을 함께 보여 주며 사용자 입력을 받습니다.
    question = input(f"질문 [기본값: {default}]: ").strip()

    # 실제 질문이 있으면 사용하고, 없으면 기본 질문을 반환합니다.
    return question or default


def menu_project_status() -> None:
    """공통 모듈 경로와 샘플 문서 상태를 확인합니다."""

    # 현재 기능 제목을 출력합니다.
    print_separator("1. 공통 모듈과 프로젝트 데이터 확인")

    # common.py가 계산한 프로젝트 루트 경로를 출력합니다.
    print("ROOT:", ROOT)

    # 프로젝트 데이터 폴더 경로와 존재 여부를 출력합니다.
    print("DATA:", DATA, "| 존재:", DATA.exists())

    # 정책 문서 폴더 경로와 존재 여부를 출력합니다.
    print("DOCS:", DOCS, "| 존재:", DOCS.exists())

    # common.py에서 읽은 Gemini 채팅 모델명을 출력합니다.
    print("GEMINI_MODEL:", GEMINI_MODEL)

    # 정책 문서 폴더에서 PDF 파일을 찾아 이름과 크기를 출력합니다.
    for pdf_path in sorted(DOCS.glob("*.pdf")):
        print(f"- {pdf_path.name}: {pdf_path.stat().st_size:,} bytes")


def menu_load_and_chunk() -> None:
    """PDF 로드와 청킹 결과를 API 호출 없이 확인합니다."""

    # 현재 기능 제목을 출력합니다.
    print_separator("2. 정책 PDF 로드 및 청킹 확인")

    # 두 정책 PDF를 페이지 단위 Document 객체로 읽습니다.
    documents = load_policy_documents()

    # 읽은 전체 페이지 수를 출력합니다.
    print("로드한 페이지 수:", len(documents))

    # 페이지 문서를 500자, 50자 겹침 설정으로 청킹합니다.
    chunks = split_documents(documents, chunk_size=500, chunk_overlap=50)

    # 생성된 전체 청크 수를 출력합니다.
    print("생성된 청크 수:", len(chunks))

    # 앞의 최대 3개 청크를 확인합니다.
    for index, chunk in enumerate(chunks[:3], start=1):
        print(f"\n[청크 {index}]")
        print("metadata:", chunk.metadata)
        print("본문:", chunk.page_content[:250].replace("\n", " "), "...")


def menu_lcel_qa() -> None:
    """LCEL로 연결한 검색→프롬프트→LLM 체인을 실행합니다."""

    # 현재 기능 제목을 출력합니다.
    print_separator("3. LCEL RAG QA 체인 실행")

    # 사용자가 실행할 모델 제공자를 선택합니다.
    provider = select_provider()

    # 사용자 질문을 입력받습니다.
    question = input_question()

    # 선택한 제공자와 k=4 설정으로 LCEL 체인을 생성합니다.
    chain = create_lcel_chain(provider=provider, k=4)

    # 체인에 질문을 전달해 최종 문자열 답변을 생성합니다.
    response = chain.invoke(question)

    # 생성된 답변을 출력합니다.
    print("\n[답변]")
    print(response)


def menu_answer_with_sources() -> None:
    """answer 함수로 답변과 출처를 딕셔너리 형태로 확인합니다."""

    # 현재 기능 제목을 출력합니다.
    print_separator("4. 답변과 출처 함께 반환")

    # 사용자가 실행할 모델 제공자를 선택합니다.
    provider = select_provider()

    # 사용자 질문을 입력받습니다.
    question = input_question("VIP 등급 조건은 무엇인가요?")

    # 검색, 생성, 출처 추출을 하나로 감싼 answer 함수를 호출합니다.
    result = answer(question=question, provider=provider, k=4)

    # 반환된 딕셔너리를 읽기 쉬운 형태로 출력합니다.
    pprint(result, sort_dicts=False)


def menu_unknown_question() -> None:
    """문서에 없는 질문에 모른다고 답하는지 확인합니다."""

    # 현재 기능 제목을 출력합니다.
    print_separator("5. 문서에 없는 질문의 환각 억제 확인")

    # 사용자가 실행할 모델 제공자를 선택합니다.
    provider = select_provider()

    # 정책 문서에 없는 새벽배송 질문을 기본값으로 받습니다.
    question = input_question("당일 새벽배송이 가능한가요?")

    # 근거 제한 answer 함수를 실행합니다.
    result = answer(question=question, provider=provider, k=4)

    # 답변을 출력합니다.
    print("\n[답변]")
    print(result["answer"])

    # 검색 과정에서 참조한 출처도 함께 출력합니다.
    print("\n[검색된 출처]")
    pprint(result["sources"], sort_dicts=False)


def menu_compare_k() -> None:
    """k=2, 4, 6일 때 검색 결과가 어떻게 달라지는지 비교합니다."""

    # 현재 기능 제목을 출력합니다.
    print_separator("6. 검색 k값 비교")

    # 임베딩 제공자를 선택합니다.
    provider = select_provider()

    # 비교에 사용할 질문을 입력받습니다.
    question = input_question("단순 변심 환불과 배송비 기준을 알려주세요.")

    # 여러 k값으로 검색을 수행합니다.
    results = compare_k(question=question, provider=provider, values=(2, 4, 6))

    # k값별 결과를 차례로 출력합니다.
    for k, documents in results.items():
        print(f"\n[k={k} | 검색 결과 {len(documents)}개]")

        # 현재 k값에서 검색된 각 청크의 출처와 본문 일부를 출력합니다.
        for rank, document in enumerate(documents, start=1):
            sources = extract_sources([document])
            preview = document.page_content[:100].replace("\n", " ")
            print(f"{rank}. {sources} | {preview} ...")


def menu_torch_rerank() -> None:
    """넉넉히 검색한 후보를 PyTorch 코사인 유사도로 재정렬합니다."""

    # 현재 기능 제목을 출력합니다.
    print_separator("7. PyTorch 코사인 유사도 재정렬")

    # 임베딩 제공자를 선택합니다.
    provider = select_provider()

    # 재정렬에 사용할 질문을 입력받습니다.
    question = input_question("VIP 회원은 어떤 혜택을 받을 수 있나요?")

    # 누락을 줄이기 위해 먼저 k=6으로 넉넉하게 후보 청크를 검색합니다.
    documents = get_retriever(provider=provider, k=6).invoke(question)

    # PyTorch 행렬 연산으로 후보를 다시 정렬하고 상위 2개만 가져옵니다.
    reranked = torch_rerank(
        question=question,
        documents=documents,
        provider=provider,
        top_n=2,
    )

    # 재정렬된 결과를 점수와 함께 출력합니다.
    for rank, (score, document) in enumerate(reranked, start=1):
        print(f"\n{rank}. 코사인 유사도: {score:.4f}")
        print("출처:", extract_sources([document]))
        print(document.page_content[:300].replace("\n", " "), "...")


def menu_llm_rerank() -> None:
    """k=6 후보를 LLM 관련도 점수로 재정렬합니다."""

    # 현재 기능 제목을 출력합니다.
    print_separator("8. LLM 관련도 재정렬")

    # 임베딩과 채팅에 사용할 동일한 제공자를 선택합니다.
    provider = select_provider()

    # 재정렬에 사용할 질문을 입력받습니다.
    question = input_question("환불 처리 기간과 카드 취소 시점을 알려주세요.")

    # 먼저 벡터 검색으로 상위 6개 후보를 확보합니다.
    documents = get_retriever(provider=provider, k=6).invoke(question)

    # LLM이 각 후보의 질문 관련도를 0~10점으로 평가해 상위 2개를 선택합니다.
    reranked = llm_rerank(
        question=question,
        documents=documents,
        provider=provider,
        top_n=2,
    )

    # LLM 재정렬 결과를 점수와 함께 출력합니다.
    for rank, (score, document) in enumerate(reranked, start=1):
        print(f"\n{rank}. LLM 관련도 점수: {score}/10")
        print("출처:", extract_sources([document]))
        print(document.page_content[:300].replace("\n", " "), "...")


def print_menu() -> None:
    """사용 가능한 실행 메뉴를 출력합니다."""

    # 애플리케이션 제목을 출력합니다.
    print("\nRAG QA 콘솔 실습")

    # 메뉴 구분선을 출력합니다.
    print("-" * 42)

    # API 없이 실행 가능한 공통 경로 확인 메뉴를 출력합니다.
    print("1. 공통 모듈과 프로젝트 데이터 확인")

    # API 없이 실행 가능한 PDF 로드·청킹 메뉴를 출력합니다.
    print("2. 정책 PDF 로드 및 청킹 확인")

    # LCEL 기반 RAG QA 실행 메뉴를 출력합니다.
    print("3. LCEL RAG QA 체인 실행")

    # 답변과 출처를 함께 반환하는 메뉴를 출력합니다.
    print("4. 답변과 출처 함께 반환")

    # 문서에 없는 질문의 환각 억제를 확인하는 메뉴를 출력합니다.
    print("5. 문서에 없는 질문 테스트")

    # 검색 개수 k에 따른 결과 차이를 확인하는 메뉴를 출력합니다.
    print("6. 검색 k값 비교")

    # PyTorch 코사인 유사도 기반 재정렬 메뉴를 출력합니다.
    print("7. PyTorch 코사인 유사도 재정렬")

    # LLM 관련도 점수 기반 재정렬 메뉴를 출력합니다.
    print("8. LLM 관련도 재정렬")

    # 프로그램 종료 메뉴를 출력합니다.
    print("0. 프로그램 종료")


def main() -> None:
    """메뉴를 반복 출력하고 사용자가 선택한 기능을 실행합니다."""

    # 메뉴 번호와 실행 함수를 연결한 딕셔너리를 정의합니다.
    handlers = {
        "1": menu_project_status,
        "2": menu_load_and_chunk,
        "3": menu_lcel_qa,
        "4": menu_answer_with_sources,
        "5": menu_unknown_question,
        "6": menu_compare_k,
        "7": menu_torch_rerank,
        "8": menu_llm_rerank,
    }

    # 사용자가 0을 입력할 때까지 메뉴를 반복합니다.
    while True:
        # 현재 선택 가능한 메뉴를 출력합니다.
        print_menu()

        # 사용자에게 메뉴 번호를 입력받습니다.
        choice = input("메뉴 선택: ").strip()

        # 0을 입력하면 반복문을 종료합니다.
        if choice == "0":
            print("프로그램을 종료합니다.")
            break

        # 입력한 번호에 해당하는 실행 함수를 찾습니다.
        handler = handlers.get(choice)

        # 존재하지 않는 번호이면 안내 후 다음 반복으로 이동합니다.
        if handler is None:
            print("올바른 메뉴 번호를 입력하세요.")
            continue

        # 한 메뉴의 오류가 전체 프로그램 종료로 이어지지 않도록 예외를 처리합니다.
        try:
            handler()
        except KeyboardInterrupt:
            print("\n현재 작업을 취소하고 메뉴로 돌아갑니다.")
        except Exception as error:
            print(f"\n[실행 오류] {type(error).__name__}: {error}")


# 이 파일을 직접 실행했을 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
