# 콘솔 메뉴에서 호출할 각 실행 기능을 정의합니다.
# 공통 모듈에서 계산한 데이터 폴더 경로를 가져옵니다.
from common import DATA, DOCS
# 문서 로드와 청킹에 필요한 서비스 함수를 가져옵니다.
from features.document_service import (
    load_all_sources,
    load_csv,
    load_markdown,
    load_pdf,
    load_text,
    split_documents,
)
# 검색 근거를 LLM에 전달하는 함수를 가져옵니다.
from features.llm_service import answer_with_context
# PyTorch 기반 로컬 검색 함수를 가져옵니다.
from features.local_vector_service import search_documents


def pause() -> None:
    """결과를 읽은 뒤 Enter를 누르면 메뉴로 돌아가게 합니다."""
    # 콘솔 결과가 바로 사라지지 않도록 사용자의 Enter 입력을 기다립니다.
    input("\nEnter 키를 누르면 메뉴로 돌아갑니다...")


def print_documents(title: str, docs, limit: int = 3) -> None:
    """Document의 본문과 metadata를 일정 개수만 보기 좋게 출력합니다."""
    # 출력 결과의 제목을 표시합니다.
    print(f"\n=== {title} ===")
    # 전체 Document 개수를 출력합니다.
    print(f"Document 개수: {len(docs)}")
    # 지정한 최대 개수만큼 Document를 순서대로 출력합니다.
    for index, doc in enumerate(docs[:limit], start=1):
        # 여러 줄 본문을 한 줄로 바꾸고 최대 250자까지만 미리보기로 만듭니다.
        preview = doc.page_content.replace("\n", " ")[:250]
        # 현재 문서의 번호와 본문 일부를 출력합니다.
        print(f"\n[{index}] page_content: {preview}")
        # 현재 문서의 출처와 페이지 등의 metadata를 출력합니다.
        print(f"    metadata: {doc.metadata}")


def run_pdf_load() -> None:
    """PDF 페이지별 로드 결과를 확인합니다."""
    # 기본 PDF를 페이지 단위 Document 목록으로 읽습니다.
    docs = load_pdf()
    # 페이지 본문 일부와 metadata를 출력합니다.
    print_documents("PDF 페이지 로드 결과", docs)
    # 사용자가 결과를 확인할 시간을 제공합니다.
    pause()


def run_chunking() -> None:
    """PDF를 기본 설정으로 청킹하고 metadata 보존을 확인합니다."""
    # 원본 PDF를 먼저 로드합니다.
    docs = load_pdf()
    # HTML 예제의 기본값인 500자와 50자 겹침으로 문서를 나눕니다.
    chunks = split_documents(docs, chunk_size=500, chunk_overlap=50)
    # 최대 5개 청크의 본문과 metadata를 출력합니다.
    print_documents("PDF 청킹 결과", chunks, limit=5)
    # 사용자가 결과를 확인할 시간을 제공합니다.
    pause()


def run_keyword_search() -> None:
    """동일 단어 포함 여부만 검사하는 단순 키워드 검색을 실행합니다."""
    # 빈 입력이면 HTML 예제와 같은 '환불'을 기본 키워드로 사용합니다.
    keyword = input("검색할 키워드 [기본값: 환불]: ").strip() or "환불"
    # PDF를 로드한 뒤 기본 설정으로 청킹합니다.
    chunks = split_documents(load_pdf())
    # 사용자가 입력한 문자열이 본문에 그대로 포함된 청크만 선택합니다.
    hits = [chunk for chunk in chunks if keyword in chunk.page_content]
    # 검색된 청크를 최대 10개까지 출력합니다.
    print_documents(f"'{keyword}' 키워드 검색 결과", hits, limit=10)
    # 사용자가 결과를 확인할 시간을 제공합니다.
    pause()


def run_chunk_tuning() -> None:
    """여러 chunk_size와 overlap 조합을 비교 표로 출력합니다."""
    # 비교 대상이 되는 원본 PDF를 로드합니다.
    docs = load_pdf()
    # 키워드 포함 청크 수를 비교할 기준 단어를 입력받습니다.
    keyword = input("비교 기준 키워드 [기본값: 환불]: ").strip() or "환불"
    # HTML 예제에 제시된 세 가지 청킹 설정을 정의합니다.
    configs = [(300, 0), (500, 50), (1000, 100)]
    # 비교 표의 헤더를 정렬하여 출력합니다.
    print(f"\n{'설정(size, overlap)':<24}{'청크 수':>10}{'평균 길이':>12}{'키워드 포함':>14}")
    # 표 헤더와 데이터 행을 구분하는 선을 출력합니다.
    print("-" * 60)
    # 각 설정을 차례대로 적용해 결과를 계산합니다.
    for size, overlap in configs:
        # 현재 설정으로 원본 문서를 청킹합니다.
        chunks = split_documents(docs, chunk_size=size, chunk_overlap=overlap)
        # 생성된 전체 청크 수를 계산합니다.
        count = len(chunks)
        # 청크가 있을 때 각 본문 길이의 평균을 계산합니다.
        average = sum(len(chunk.page_content) for chunk in chunks) / count if count else 0.0
        # 기준 키워드를 포함한 청크의 수를 계산합니다.
        hits = sum(1 for chunk in chunks if keyword in chunk.page_content)
        # 현재 설정과 계산 결과를 한 행으로 정렬해 출력합니다.
        print(f"({size}, {overlap}){count:>20}{average:>12.1f}{hits:>14}")
    # 사용자가 결과를 확인할 시간을 제공합니다.
    pause()


def run_various_loaders() -> None:
    """CSV, TXT, Markdown가 같은 Document 구조로 변환되는지 확인합니다."""
    # CSV의 한 행이 하나의 Document로 변환된 결과를 출력합니다.
    print_documents("CSVLoader 결과", load_csv())
    # 텍스트 파일 전체가 Document로 변환된 결과를 출력합니다.
    print_documents("TextLoader 결과", load_text())
    # 마크다운 헤더별로 분리된 Document 결과를 출력합니다.
    print_documents("MarkdownHeaderTextSplitter 결과", load_markdown())
    # 사용자가 결과를 확인할 시간을 제공합니다.
    pause()


def ask_question() -> tuple[str, list]:
    """전체 문서를 청킹하고 PyTorch 검색을 수행해 질문과 검색 결과를 반환합니다."""
    # 사용자에게 문서 기반 질문을 입력받습니다.
    question = input("문서에 질문할 내용을 입력하세요: ").strip()
    # 빈 질문은 검색할 수 없으므로 ValueError를 발생시킵니다.
    if not question:
        raise ValueError("질문은 비워 둘 수 없습니다.")
    # PDF, CSV, TXT, Markdown 문서를 하나의 목록으로 합칩니다.
    all_docs = load_all_sources()
    # 모든 문서를 동일한 청킹 파이프라인으로 나눕니다.
    chunks = split_documents(all_docs, chunk_size=500, chunk_overlap=50)
    # PyTorch 코사인 유사도를 이용해 상위 3개 근거를 검색합니다.
    results = search_documents(question, chunks, top_k=3)
    # 질문과 검색 결과를 호출한 메뉴 함수에 반환합니다.
    return question, results


def run_torch_search() -> None:
    """API 없이 PyTorch 코사인 유사도 검색 결과만 출력합니다."""
    # 질문을 입력받고 로컬 벡터 검색을 수행합니다.
    _question, results = ask_question()
    # 검색 결과 영역의 제목을 출력합니다.
    print("\n=== PyTorch 로컬 벡터 검색 결과 ===")
    # 유사도가 높은 순서대로 검색 결과를 출력합니다.
    for index, (doc, score) in enumerate(results, start=1):
        # 현재 문서의 순위와 유사도 점수를 출력합니다.
        print(f"\n[{index}] 유사도: {score:.4f}")
        # 현재 문서의 출처 metadata를 출력합니다.
        print("출처:", doc.metadata)
        # 현재 문서 본문을 최대 500자까지 출력합니다.
        print(doc.page_content[:500])
    # 사용자가 결과를 확인할 시간을 제공합니다.
    pause()


def run_llm_rag(provider: str) -> None:
    """PyTorch 검색 결과를 선택한 LLM에 전달하여 근거 기반 답변을 생성합니다."""
    # 질문을 입력받고 상위 문서 근거를 검색합니다.
    question, results = ask_question()
    # LLM 호출 전에 실제 전달될 검색 근거를 출력합니다.
    print("\n=== 검색된 근거 ===")
    # 검색 순위에 따라 각 근거를 출력합니다.
    for index, (doc, score) in enumerate(results, start=1):
        # 근거 번호, 유사도, metadata를 출력합니다.
        print(f"[{index}] score={score:.4f}, metadata={doc.metadata}")
        # 근거 본문 일부를 출력합니다.
        print(doc.page_content[:250], "\n")
    # 선택한 공급자의 LLM에 질문과 검색 근거를 전달합니다.
    answer = answer_with_context(provider, question, results)
    # 어떤 모델 공급자의 결과인지 제목으로 표시합니다.
    print(f"\n=== {provider.upper()} 근거 기반 답변 ===")
    # 최종 생성 답변을 출력합니다.
    print(answer)
    # 사용자가 결과를 확인할 시간을 제공합니다.
    pause()


def run_path_check() -> None:
    """공통 모듈이 계산한 데이터 경로와 실습 파일 존재 여부를 점검합니다."""
    # common.py가 계산한 data 폴더의 절대 경로를 출력합니다.
    print("\nDATA 경로:", DATA)
    # common.py가 계산한 docs 폴더의 절대 경로를 출력합니다.
    print("DOCS 경로:", DOCS)
    # 반드시 필요한 네 개의 실습 파일 경로를 순서대로 검사합니다.
    for path in [
        DOCS / "환불교환정책.pdf",
        DATA / "faq.csv",
        DATA / "notice.txt",
        DATA / "policy.md",
    ]:
        # 각 파일이 존재하는지 사람이 읽기 쉬운 문자열로 출력합니다.
        print(f"- {path.name}: {'존재' if path.exists() else '없음'}")
    # 사용자가 결과를 확인할 시간을 제공합니다.
    pause()
