"""04. build_index.py 역할: 문서를 임베딩하여 FAISS 인덱스를 생성하고 저장합니다."""  # 이 파일은 배치 인덱싱 단계입니다.

from langchain_community.vectorstores import FAISS  # FAISS 벡터스토어 클래스를 불러옵니다.

from common import FAISS_DIR, get_embeddings, load_and_chunk  # 공통 경로, 임베딩 생성, 문서 청킹 함수를 불러옵니다.

BASE_FILES = ["제품매뉴얼_로봇청소기.txt", "제품매뉴얼_스마트워치.txt"]  # 최초 FAISS 인덱스에 넣을 샘플 문서 목록입니다.


def build_index() -> None:  # FAISS 인덱스를 만드는 배치 함수입니다.
    emb = get_embeddings()  # 설정된 임베딩 객체를 생성합니다.
    chunks = load_and_chunk(BASE_FILES)  # 샘플 문서를 읽고 검색 가능한 청크로 분할합니다.
    print(f"청크 개수: {len(chunks)}")  # 생성된 청크 수를 출력해 인덱싱 규모를 확인합니다.
    vs = FAISS.from_documents(chunks, emb)  # 모든 청크를 임베딩하고 FAISS 인덱스를 생성합니다.
    vs.save_local(str(FAISS_DIR))  # 생성된 FAISS 인덱스를 디스크에 저장합니다.
    print(f"FAISS 인덱스 저장 완료: {FAISS_DIR}")  # 저장 위치를 사용자에게 안내합니다.


def main() -> None:  # main.py 메뉴에서 공통으로 호출할 표준 실행 진입점입니다.
    build_index()  # 실제 인덱스 생성 함수인 build_index를 호출합니다.


if __name__ == "__main__":  # 파일을 직접 실행했는지 확인합니다.
    main()  # 직접 실행과 메뉴 실행이 같은 흐름을 사용하도록 main 함수를 실행합니다.
