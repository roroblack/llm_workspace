"""실습문제3. 문제2 검색에 문서파일명과 페이지 정보(메타데이터)를 함께 출력합니다."""  # 이 파일은 검색 결과의 출처 추적을 강화한 단계입니다.

from pathlib import Path  # 인덱스 파일 존재 여부를 확인하기 위해 Path를 사용합니다.

from langchain_community.vectorstores import FAISS  # 저장된 FAISS 인덱스를 로드하기 위해 FAISS 클래스를 불러옵니다.

from common import MEMBERSHIP_FAISS_DIR, get_genai_embeddings  # 저장 경로와 Google 임베딩 함수를 불러옵니다.


def load_membership_index() -> FAISS:  # 저장된 멤버십 FAISS 인덱스를 로드하는 함수입니다. (문제2에서 복사)
    index_file = Path(MEMBERSHIP_FAISS_DIR) / "index.faiss"  # FAISS 핵심 인덱스 파일 경로를 만듭니다.
    if not index_file.exists():  # 인덱스 파일이 없으면 먼저 문제1을 실행해야 합니다.
        raise FileNotFoundError("FAISS 인덱스가 없습니다. 먼저 메뉴 10(실습문제1)을 실행하세요.")  # 실행 순서를 안내하는 오류를 발생시킵니다.
    emb = get_genai_embeddings()  # 검색 질문 임베딩에 사용할 Google 임베딩 객체를 생성합니다.
    return FAISS.load_local(str(MEMBERSHIP_FAISS_DIR), emb, allow_dangerous_deserialization=True)  # 재임베딩 없이 로드만 합니다.


def print_with_metadata(title: str, docs, max_chars: int = 160) -> None:  # 검색 결과에 파일명과 페이지를 명시적으로 출력하는 함수입니다.
    print(f"\n[{title}]")  # 결과 묶음의 제목을 출력합니다.
    if not docs:  # 검색 결과가 없을 때 안내합니다.
        print("검색 결과가 없습니다.")  # 빈 결과임을 알려 줍니다.
        return  # 출력할 문서가 없으므로 종료합니다.
    for index, doc in enumerate(docs, start=1):  # 결과 문서를 1번부터 번호를 붙여 순회합니다.
        source = doc.metadata.get("source", "?")  # 메타데이터에서 문서파일명을 가져옵니다.
        page = doc.metadata.get("page", "?")  # 메타데이터에서 페이지 번호를 가져옵니다.
        content = doc.page_content.replace("\n", " ")[:max_chars]  # 줄바꿈을 공백으로 바꾸고 앞부분만 표시합니다.
        print(f"{index}. 문서파일명={source}, 페이지={page}")  # 출처 파일명과 페이지 정보를 함께 출력합니다.
        print(f"   내용: {content}...")  # 검색된 청크 내용 일부를 출력합니다.


def main() -> None:  # PyCharm 실행 진입점입니다.
    vs = load_membership_index()  # 저장된 인덱스를 로드합니다.
    question = "VIP 적립률"  # 문제2와 동일한 검색 질문입니다.
    results = vs.similarity_search(question, k=3)  # 질문과 가까운 청크 3개를 검색합니다.
    print_with_metadata(f"검색 질문: {question} (출처 파일명+페이지 포함)", results)  # 메타데이터를 포함해 결과를 출력합니다.


if __name__ == "__main__":  # 이 파일을 직접 실행한 경우에만 메인 함수를 실행합니다.
    main()  # 메타데이터 출력 예제를 실행합니다.
