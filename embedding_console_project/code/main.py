# -*- coding: utf-8 -*-
"""제14강 임베딩 실습을 메뉴 방식으로 실행하는 콘솔 애플리케이션입니다."""

from __future__ import annotations

import csv
from pathlib import Path

from common import DATA, DOCS, get_chat, get_embeddings
from vector_utils import cosine_similarity, top_k_indices


def print_title(title: str) -> None:
    """각 실습의 시작 위치를 쉽게 구분할 수 있도록 제목을 출력합니다."""
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def choose_provider() -> str:
    """사용자가 Gemini 또는 OpenAI 제공자를 선택하도록 입력을 받습니다."""
    print("1. Gemini")
    print("2. OpenAI")
    choice = input("모델 제공자를 선택하세요: ").strip()
    return "openai" if choice == "2" else "gemini"


def load_faq_rows() -> list[dict[str, str]]:
    """data/faq.csv 파일을 읽어 FAQ 딕셔너리 목록으로 반환합니다."""
    faq_path = DATA / "faq.csv"
    if not faq_path.exists():
        raise FileNotFoundError(f"FAQ 파일을 찾을 수 없습니다: {faq_path}")
    with faq_path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def menu_environment() -> None:
    """공통 모듈이 계산한 프로젝트 경로와 데이터 파일 상태를 확인합니다."""
    print_title("1. 공통 모듈 및 데이터 경로 확인")
    print("DATA 경로:", DATA)
    print("DOCS 경로:", DOCS)
    print("FAQ 존재:", (DATA / "faq.csv").exists())
    print("긴 문서 존재:", (DOCS / "employee_handbook.txt").exists())


def menu_torch_cosine() -> None:
    """API를 사용하지 않고 PyTorch로 코사인 유사도 계산 원리를 확인합니다."""
    print_title("2. PyTorch 코사인 유사도 계산")
    vector_a = [1.0, 0.0, 1.0]
    vector_b = [0.9, 0.1, 1.0]
    vector_c = [-1.0, 0.0, -1.0]
    print("A와 B 유사도:", f"{cosine_similarity(vector_a, vector_b):.4f}")
    print("A와 C 유사도:", f"{cosine_similarity(vector_a, vector_c):.4f}")


def menu_single_embedding() -> None:
    """선택한 임베딩 API로 문장 하나를 고정 길이 벡터로 변환합니다."""
    print_title("3. 문장 하나 임베딩")
    provider = choose_provider()
    sentence = input("임베딩할 문장을 입력하세요: ").strip() or "환불은 며칠 걸려요?"
    embeddings = get_embeddings(provider)
    vector = embeddings.embed_query(sentence)
    print("제공자:", provider)
    print("벡터 차원:", len(vector))
    print("앞 10개 값:", vector[:10])


def menu_compare_sentences() -> None:
    """세 문장을 임베딩하고 PyTorch 코사인 유사도로 의미의 가까움을 비교합니다."""
    print_title("4. 문장 의미 유사도 비교")
    provider = choose_provider()
    sentences = ["환불", "돈 돌려받기", "로봇청소기 배터리"]
    embeddings = get_embeddings(provider)
    vectors = embeddings.embed_documents(sentences)
    print("환불 ↔ 돈 돌려받기:", f"{cosine_similarity(vectors[0], vectors[1]):.4f}")
    print("환불 ↔ 로봇청소기 배터리:", f"{cosine_similarity(vectors[0], vectors[2]):.4f}")


def menu_faq_search() -> None:
    """FAQ 질문을 배치 임베딩한 뒤 사용자 질문과 가장 유사한 상위 FAQ를 찾습니다."""
    print_title("5. FAQ 임베딩 및 Top-k 의미 검색")
    provider = choose_provider()
    rows = load_faq_rows()
    questions = [row["question"] for row in rows]
    user_question = input("검색 질문을 입력하세요: ").strip() or "돈 언제 돌려받아요?"
    embeddings = get_embeddings(provider)
    document_vectors = embeddings.embed_documents(questions)
    query_vector = embeddings.embed_query(user_question)
    results = top_k_indices(query_vector, document_vectors, k=3)
    for rank, (index, score) in enumerate(results, start=1):
        print(f"\n{rank}위 | 유사도 {score:.4f}")
        print("질문:", rows[index]["question"])
        print("답변:", rows[index]["answer"])


def menu_long_document_search() -> None:
    """긴 텍스트를 청킹하고 각 청크를 임베딩하여 관련 청크를 검색합니다."""
    print_title("6. 긴 문서 청킹 후 임베딩 검색")
    provider = choose_provider()
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    document_path = DOCS / "employee_handbook.txt"
    text = document_path.read_text(encoding="utf-8")
    original = Document(page_content=text, metadata={"source": str(document_path)})
    splitter = RecursiveCharacterTextSplitter(chunk_size=180, chunk_overlap=30)
    chunks = splitter.split_documents([original])
    chunk_texts = [chunk.page_content for chunk in chunks]
    question = input("긴 문서 검색 질문: ").strip() or "연차 휴가는 며칠인가요?"
    embeddings = get_embeddings(provider)
    chunk_vectors = embeddings.embed_documents(chunk_texts)
    query_vector = embeddings.embed_query(question)
    for rank, (index, score) in enumerate(top_k_indices(query_vector, chunk_vectors, 3), start=1):
        print(f"\n{rank}위 | 유사도 {score:.4f}")
        print(chunk_texts[index])


def menu_rag_answer() -> None:
    """FAQ 의미 검색 결과를 근거로 전달하고 채팅 모델이 최종 답변을 생성하게 합니다."""
    print_title("7. 임베딩 검색 + 채팅 모델 근거 답변")
    provider = choose_provider()
    rows = load_faq_rows()
    questions = [row["question"] for row in rows]
    user_question = input("질문을 입력하세요: ").strip() or "돈은 언제 돌려받을 수 있나요?"
    embeddings = get_embeddings(provider)
    document_vectors = embeddings.embed_documents(questions)
    query_vector = embeddings.embed_query(user_question)
    results = top_k_indices(query_vector, document_vectors, k=3)
    context = "\n\n".join(
        f"FAQ 질문: {rows[index]['question']}\nFAQ 답변: {rows[index]['answer']}"
        for index, _ in results
    )
    prompt = (
        "다음 FAQ 근거에 포함된 내용만 사용해 한국어로 답하세요. "
        "근거에 답이 없으면 '제공된 FAQ에서 확인할 수 없습니다.'라고 답하세요.\n\n"
        f"[FAQ 근거]\n{context}\n\n[사용자 질문]\n{user_question}"
    )
    chat = get_chat(provider, temperature=0.0)
    response = chat.invoke(prompt)
    print("\n최종 답변:")
    print(response.content)


def print_menu() -> None:
    """HTML 설명 메뉴를 제외하고 실제 실행 실습 메뉴만 출력합니다."""
    print("\n[제14강 임베딩 콘솔 실습]")
    print("1. 공통 모듈 및 데이터 경로 확인")
    print("2. PyTorch 코사인 유사도 계산")
    print("3. 문장 하나 임베딩")
    print("4. 문장 의미 유사도 비교")
    print("5. FAQ 임베딩 및 Top-k 의미 검색")
    print("6. 긴 문서 청킹 후 임베딩 검색")
    print("7. 임베딩 검색 + 채팅 모델 근거 답변")
    print("0. 종료")


def main() -> None:
    """사용자 선택에 따라 각 실습 함수를 반복 실행합니다."""
    actions = {
        "1": menu_environment,
        "2": menu_torch_cosine,
        "3": menu_single_embedding,
        "4": menu_compare_sentences,
        "5": menu_faq_search,
        "6": menu_long_document_search,
        "7": menu_rag_answer,
    }
    while True:
        print_menu()
        choice = input("메뉴 번호를 입력하세요: ").strip()
        if choice == "0":
            print("프로그램을 종료합니다.")
            break
        action = actions.get(choice)
        if action is None:
            print("올바른 메뉴 번호를 입력하세요.")
            continue
        try:
            action()
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception as error:
            print(f"[실행 오류] {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
