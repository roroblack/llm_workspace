"""07. Chroma 메타데이터 필터링 검색을 실습합니다."""  # 이 파일은 특정 문서 안에서만 검색하는 방법을 보여 줍니다.

import shutil  # Chroma 기존 저장 폴더를 초기화하기 위해 shutil을 사용합니다.

from langchain_community.vectorstores import Chroma  # Chroma 벡터스토어를 사용하기 위해 불러옵니다.

from common import CHROMA_DIR, get_embeddings, load_and_chunk, print_documents  # 공통 경로와 유틸리티 함수를 불러옵니다.

FILES = ["환불교환정책.txt", "멤버십정책.txt", "직원핸드북.txt"]  # Chroma 필터 실습에 사용할 여러 문서 목록입니다.


def build_chroma() -> Chroma:  # Chroma 인덱스를 새로 생성하는 함수입니다.
    if CHROMA_DIR.exists():  # 이전 실습 결과가 남아 있으면 결과 혼동을 줄이기 위해 삭제합니다.
        shutil.rmtree(CHROMA_DIR)  # 기존 Chroma 저장 폴더를 삭제합니다.
    chunks = load_and_chunk(FILES)  # 여러 문서를 로드하고 청크로 분할합니다.
    emb = get_embeddings()  # Chroma에 사용할 임베딩 객체를 생성합니다.
    return Chroma.from_documents(chunks, emb, persist_directory=str(CHROMA_DIR))  # 청크를 임베딩하고 Chroma DB에 저장합니다.


def search_in_doc(vs: Chroma, query: str, source: str | None = None, k: int = 3):  # 특정 문서 필터를 적용할 수 있는 검색 함수입니다.
    metadata_filter = {"source": source} if source else None  # source가 있으면 해당 파일명만 검색하도록 필터를 만듭니다.
    return vs.similarity_search(query, k=k, filter=metadata_filter)  # 필터 조건에 맞는 청크 안에서 유사도 검색을 수행합니다.


def main() -> None:  # PyCharm 실행 진입점입니다.
    vs = build_chroma()  # Chroma 인덱스를 생성하고 저장합니다.
    query = "VIP 등급 혜택은?"  # 멤버십 문서에서 답해야 하는 질문을 준비합니다.
    all_results = search_in_doc(vs, query, source=None, k=3)  # 필터 없이 전체 문서에서 검색합니다.
    filtered_results = search_in_doc(vs, query, source="멤버십정책.txt", k=3)  # 멤버십정책 문서 안에서만 검색합니다.
    print_documents("필터 없음 - 전체 문서 검색", all_results)  # 전체 검색 결과를 출력합니다.
    print_documents("필터 적용 - 멤버십정책.txt 안에서만 검색", filtered_results)  # 필터 검색 결과를 출력합니다.
    print("필터를 사용하면 관련 없는 문서가 섞이는 노이즈를 줄일 수 있습니다.")  # 필터링의 효과를 설명합니다.


if __name__ == "__main__":  # 직접 실행 여부를 확인합니다.
    main()  # Chroma 필터 검색 실습을 실행합니다.
