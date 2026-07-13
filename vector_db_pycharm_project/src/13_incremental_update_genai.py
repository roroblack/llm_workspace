"""실습문제4. 저장된 인덱스를 로드해 환불교환정책.pdf를 증분(add_documents) 추가합니다."""  # 이 파일은 전체 재빌드 없이 새 문서만 추가하는 단계입니다.

from pathlib import Path  # 인덱스 파일 존재 여부를 확인하기 위해 Path를 사용합니다.

from langchain_community.vectorstores import FAISS  # FAISS 로드와 증분 추가에 사용합니다.

from common import MEMBERSHIP_FAISS_DIR, get_genai_embeddings, load_and_chunk  # 저장 경로, Google 임베딩, 청킹 함수를 불러옵니다.

NEW_FILE = ["환불교환정책.pdf"]  # 문제4에서 증분으로 추가할 새 PDF 문서입니다.


def load_index(emb) -> FAISS:  # 문제1이 저장한 멤버십 인덱스를 로드하는 함수입니다.
    index_file = Path(MEMBERSHIP_FAISS_DIR) / "index.faiss"  # FAISS 핵심 인덱스 파일 경로를 만듭니다.
    if not index_file.exists():  # 인덱스가 없으면 먼저 문제1을 실행해야 합니다.
        raise FileNotFoundError("FAISS 인덱스가 없습니다. 먼저 메뉴 10(실습문제1)을 실행하세요.")  # 실행 순서를 안내하는 오류를 발생시킵니다.
    return FAISS.load_local(str(MEMBERSHIP_FAISS_DIR), emb, allow_dangerous_deserialization=True)  # 저장된 기존 인덱스를 로드합니다.


def print_with_metadata(title: str, docs, max_chars: int = 160) -> None:  # 검색 결과를 파일명/페이지와 함께 출력하는 함수입니다.
    print(f"\n[{title}]")  # 결과 묶음의 제목을 출력합니다.
    if not docs:  # 검색 결과가 없을 때 안내합니다.
        print("검색 결과가 없습니다.")  # 빈 결과임을 알려 줍니다.
        return  # 출력할 문서가 없으므로 종료합니다.
    for index, doc in enumerate(docs, start=1):  # 결과 문서를 순회합니다.
        source = doc.metadata.get("source", "?")  # 문서파일명을 가져옵니다.
        page = doc.metadata.get("page", "?")  # 페이지 번호를 가져옵니다.
        content = doc.page_content.replace("\n", " ")[:max_chars]  # 내용 앞부분만 표시합니다.
        print(f"{index}. 문서파일명={source}, 페이지={page}")  # 출처 정보를 출력합니다.
        print(f"   내용: {content}...")  # 청크 내용 일부를 출력합니다.


def main() -> None:  # PyCharm 실행 진입점입니다.
    emb = get_genai_embeddings()  # Google 임베딩 객체를 생성합니다.
    vs = load_index(emb)  # 문제1이 만든 멤버십 인덱스를 로드합니다.
    query = "환불은 며칠 안에 가능한가요?"  # 추가된 환불 문서가 검색되는지 확인할 질문입니다.
    before = vs.similarity_search(query, k=3)  # 증분 추가 전 검색을 수행합니다.
    print_with_metadata("증분 전 검색 - 멤버십 문서만 있는 상태", before)  # 추가 전 결과를 출력합니다.
    new_chunks = load_and_chunk(NEW_FILE)  # 새로 추가할 환불교환정책 PDF를 청킹합니다.
    print(f"\n추가할 청크 개수: {len(new_chunks)}")  # 증분으로 임베딩할 청크 수를 출력합니다.
    vs.add_documents(new_chunks)  # 새 청크만 임베딩하여 기존 인덱스에 덧붙입니다.
    vs.save_local(str(MEMBERSHIP_FAISS_DIR))  # 증분 추가된 인덱스를 다시 저장합니다.
    after = vs.similarity_search(query, k=3)  # 같은 질문으로 증분 후 검색을 수행합니다.
    print_with_metadata("증분 후 검색 - 환불교환정책.pdf 추가 상태(결과에 포함되면 성공)", after)  # 추가 후 결과를 출력합니다.
    keep = vs.similarity_search("VIP 적립률", k=2)  # 기존 멤버십 지식이 유지되는지 확인합니다.
    print_with_metadata("기존 지식 유지 확인 - 멤버십 질문", keep)  # 기존 지식 검색 결과를 출력합니다.
    print("\nadd_documents는 새 청크만 임베딩하므로 전체 재빌드보다 비용과 시간이 줄어듭니다.")  # 증분 업데이트의 장점을 설명합니다.


if __name__ == "__main__":  # 직접 실행 여부를 확인합니다.
    main()  # 증분 업데이트 실습을 실행합니다.
