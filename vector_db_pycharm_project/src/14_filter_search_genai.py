"""실습문제5. 두 PDF 중 하나를 선택하고, 선택한 문서에서만 메타데이터 필터링 검색합니다."""  # 이 파일은 문제4가 저장한 인덱스를 로드해 필터 검색하는 단계입니다.

from pathlib import Path  # 인덱스 파일 존재 여부를 확인하기 위해 Path를 사용합니다.

from langchain_community.vectorstores import FAISS  # 저장된 FAISS 인덱스를 로드하기 위해 FAISS 클래스를 불러옵니다.

from common import MEMBERSHIP_FAISS_DIR, get_genai_embeddings  # 저장 경로와 Google 임베딩 함수를 불러옵니다.

CHOICES = {  # 사용자가 선택할 수 있는 PDF 파일명 목록입니다.
    "1": "멤버십정책.pdf",  # 1번은 멤버십정책 문서입니다.
    "2": "환불교환정책.pdf",  # 2번은 환불교환정책 문서입니다.
}  # 선택지 딕셔너리 정의를 끝냅니다.


def load_index() -> FAISS:  # 문제4가 저장한(두 문서 포함) 인덱스를 로드하는 함수입니다.
    index_file = Path(MEMBERSHIP_FAISS_DIR) / "index.faiss"  # FAISS 핵심 인덱스 파일 경로를 만듭니다.
    if not index_file.exists():  # 인덱스가 없으면 먼저 문제1, 문제4를 실행해야 합니다.
        raise FileNotFoundError("FAISS 인덱스가 없습니다. 먼저 메뉴 10, 13을 실행하세요.")  # 실행 순서를 안내하는 오류를 발생시킵니다.
    emb = get_genai_embeddings()  # 검색 질문 임베딩에 사용할 Google 임베딩 객체를 생성합니다.
    return FAISS.load_local(str(MEMBERSHIP_FAISS_DIR), emb, allow_dangerous_deserialization=True)  # 재임베딩 없이 로드만 합니다.


def choose_source() -> str:  # 검색 대상 PDF 파일명을 사용자에게 선택받는 함수입니다.
    print("\n검색할 문서를 선택하세요.")  # 선택 안내 문구를 출력합니다.
    for key, name in CHOICES.items():  # 선택지를 순서대로 순회합니다.
        print(f"{key}. {name}")  # 번호와 파일명을 한 줄로 출력합니다.
    choice = input("번호를 입력하세요: ").strip()  # 사용자 입력을 받아 앞뒤 공백을 제거합니다.
    if choice not in CHOICES:  # 잘못된 번호이면 기본값으로 안내합니다.
        print("잘못된 번호입니다. 1(멤버십정책.pdf)로 진행합니다.")  # 잘못된 입력 시 기본 선택을 알립니다.
        return CHOICES["1"]  # 기본값으로 멤버십정책 파일명을 반환합니다.
    return CHOICES[choice]  # 선택된 파일명을 반환합니다.


def print_with_metadata(title: str, docs, max_chars: int = 160) -> None:  # 결과를 파일명/페이지와 함께 출력하는 함수입니다.
    print(f"\n[{title}]")  # 결과 묶음의 제목을 출력합니다.
    if not docs:  # 검색 결과가 없을 때 안내합니다.
        print("검색 결과가 없습니다.")  # 빈 결과임을 알려 줍니다.
        return  # 출력할 문서가 없으므로 종료합니다.
    for index, doc in enumerate(docs, start=1):  # 결과 문서를 순회합니다.
        source = doc.metadata.get("source", "?")  # 문서파일명을 가져옵니다.
        page = doc.metadata.get("page", "?")  # 페이지 번호를 가져옵니다.
        content = doc.page_content.replace("\n", " ")[:max_chars]  # 내용 앞부분만 표시합니다.
        print(f"{index}. 문서파일명={source}, 페이지={page}")  # 선택 문서의 출처 정보를 출력합니다.
        print(f"   내용: {content}...")  # 청크 내용 일부를 출력합니다.


def main() -> None:  # PyCharm 실행 진입점입니다.
    vs = load_index()  # 두 문서가 담긴 인덱스를 로드합니다.
    source = choose_source()  # 검색할 PDF 파일명을 선택받습니다.
    question = "환불 규정과 적립률을 알려주세요"  # 두 문서 모두와 관련될 수 있는 질문입니다.
    results = vs.similarity_search(question, k=3, filter={"source": source})  # source 메타데이터로 선택 문서에서만 검색합니다.
    print_with_metadata(f"필터 검색: [{source}] 문서에서만 검색 (질문: {question})", results)  # 필터 검색 결과를 출력합니다.
    if results and any(doc.metadata.get("source") != source for doc in results):  # 필터가 새지 않았는지 확인합니다.
        print("경고: 선택한 문서 외의 결과가 섞여 있습니다.")  # 예상과 다른 결과가 나오면 경고합니다.


if __name__ == "__main__":  # 직접 실행 여부를 확인합니다.
    main()  # 메타데이터 필터 검색 실습을 실행합니다.
