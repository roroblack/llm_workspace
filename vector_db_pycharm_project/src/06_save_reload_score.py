"""06. FAISS 인덱스 저장, 재로드, 점수 포함 검색을 확인합니다."""  # 이 파일은 save_local/load_local과 score 검색을 실습합니다.

from langchain_community.vectorstores import FAISS  # FAISS 인덱스를 생성하고 로드하기 위해 불러옵니다.

from common import FAISS_DIR, get_embeddings, load_and_chunk, print_scored_documents  # 공통 함수와 경로를 불러옵니다.

FILES = ["제품매뉴얼_로봇청소기.txt", "제품매뉴얼_스마트워치.txt"]  # 저장/재로드 실습에 사용할 문서 목록입니다.


def main() -> None:  # PyCharm에서 실행할 메인 함수입니다.
    emb = get_embeddings()  # 임베딩 객체를 생성합니다.
    chunks = load_and_chunk(FILES)  # 문서를 로드하고 청크로 분할합니다.
    vs = FAISS.from_documents(chunks, emb)  # 청크 전체를 임베딩하고 FAISS 인덱스를 생성합니다.
    vs.save_local(str(FAISS_DIR))  # 생성된 인덱스를 index.faiss와 index.pkl로 저장합니다.
    print(f"인덱스 저장 완료: {FAISS_DIR}")  # 저장 완료 메시지를 출력합니다.
    reloaded = FAISS.load_local(str(FAISS_DIR), emb, allow_dangerous_deserialization=True)  # 저장된 인덱스를 재임베딩 없이 다시 로드합니다.
    query = "배터리 충전 시간은?"  # 점수 포함 검색에 사용할 질문입니다.
    scored = reloaded.similarity_search_with_score(query, k=2)  # 검색 결과와 FAISS 거리 점수를 함께 가져옵니다.
    print_scored_documents(f"점수 포함 검색: {query}", scored)  # 거리 점수와 검색 결과를 출력합니다.
    print("FAISS 점수는 거리이므로 일반적으로 작을수록 질문과 더 가깝습니다.")  # 점수 해석 방법을 안내합니다.


if __name__ == "__main__":  # 직접 실행된 경우를 확인합니다.
    main()  # 저장/재로드/점수 검색 실습을 실행합니다.
