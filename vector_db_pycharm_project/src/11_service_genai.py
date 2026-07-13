"""실습문제2. 저장된 FAISS 인덱스를 load_local로 불러와 검색만 수행합니다."""  # 이 파일은 재빌드 없이 로드+검색만 하는 서비스 단계입니다.

from pathlib import Path  # 인덱스 파일 존재 여부를 확인하기 위해 Path를 사용합니다.

from langchain_community.vectorstores import FAISS  # 저장된 FAISS 인덱스를 로드하기 위해 FAISS 클래스를 불러옵니다.

from common import MEMBERSHIP_FAISS_DIR, get_genai_embeddings, print_documents  # 저장 경로, Google 임베딩, 출력 함수를 불러옵니다.


def load_membership_index() -> FAISS:  # 디스크에 저장된 멤버십 FAISS 인덱스를 메모리로 로드하는 함수입니다.
    index_file = Path(MEMBERSHIP_FAISS_DIR) / "index.faiss"  # FAISS 핵심 인덱스 파일 경로를 만듭니다.
    if not index_file.exists():  # 인덱스 파일이 없으면 먼저 문제1을 실행해야 합니다.
        raise FileNotFoundError("FAISS 인덱스가 없습니다. 먼저 메뉴 10(실습문제1)을 실행하세요.")  # 실행 순서를 안내하는 오류를 발생시킵니다.
    emb = get_genai_embeddings()  # 검색 질문 임베딩에 사용할 같은 Google 임베딩 객체를 생성합니다.
    return FAISS.load_local(str(MEMBERSHIP_FAISS_DIR), emb, allow_dangerous_deserialization=True)  # 저장된 벡터를 재임베딩 없이 로드만 합니다.


def search(question: str, k: int = 3):  # 질문을 받아 Top-k 문서를 검색하는 함수입니다.
    vs = load_membership_index()  # 저장된 FAISS 인덱스를 로드합니다.
    return vs.similarity_search(question, k=k)  # 질문과 의미적으로 가까운 청크 k개를 검색합니다.


def main() -> None:  # PyCharm 실행 진입점입니다.
    question = "VIP 적립률"  # 문제2에서 요구한 검색 질문입니다.
    results = search(question, k=3)  # 로드만으로 질문과 가까운 청크 3개를 찾습니다.
    print_documents(f"검색 질문: {question} (top-1이 적립률 청크이면 성공)", results)  # 검색 결과를 출처와 함께 출력합니다.


if __name__ == "__main__":  # 이 파일을 직접 실행한 경우에만 메인 함수를 실행합니다.
    main()  # 서비스 검색 예제를 실행합니다.
