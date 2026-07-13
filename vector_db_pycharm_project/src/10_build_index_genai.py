"""실습문제1. 멤버십정책.pdf를 청킹·임베딩하여 FAISS 인덱스를 만들고 저장합니다."""  # 이 파일은 GenAI 임베딩 기반 배치 인덱싱 단계입니다.

from langchain_community.vectorstores import FAISS  # FAISS 벡터스토어 클래스를 불러옵니다.

from common import MEMBERSHIP_FAISS_DIR, get_genai_embeddings, load_and_chunk  # 저장 경로, Google 임베딩, 문서 청킹 함수를 불러옵니다.

TARGET_FILES = ["멤버십정책.pdf"]  # 문제1에서 인덱싱할 대상 PDF 문서 목록입니다.


def build_index() -> None:  # 멤버십정책 PDF로 FAISS 인덱스를 만드는 함수입니다.
    emb = get_genai_embeddings()  # Google Gemini 임베딩 객체를 생성합니다.
    chunks = load_and_chunk(TARGET_FILES)  # PDF를 페이지 단위로 읽고 검색용 청크로 분할합니다.
    print(f"저장된 청크 개수: {len(chunks)}")  # 저장할 청크 개수를 출력해 인덱싱 규모를 확인합니다.
    vs = FAISS.from_documents(chunks, emb)  # 모든 청크를 임베딩하고 FAISS 인덱스를 생성합니다.
    MEMBERSHIP_FAISS_DIR.mkdir(parents=True, exist_ok=True)  # 저장 폴더가 없으면 먼저 생성합니다.
    vs.save_local(str(MEMBERSHIP_FAISS_DIR))  # 생성된 FAISS 인덱스를 지정 경로에 저장합니다.
    print(f"FAISS 인덱스 저장 완료: {MEMBERSHIP_FAISS_DIR}")  # 저장 위치(index.faiss, index.pkl 생성 폴더)를 안내합니다.


def main() -> None:  # main.py 메뉴에서 호출할 표준 실행 진입점입니다.
    build_index()  # 실제 인덱스 생성 함수를 호출합니다.


if __name__ == "__main__":  # 파일을 직접 실행했는지 확인합니다.
    main()  # 직접 실행과 메뉴 실행이 같은 흐름을 사용하도록 main 함수를 실행합니다.
