"""인덱싱 (사전 1회) — PDF4 핵심: 인덱싱과 서비스 분리.

data/docs/*.txt → 청킹 → FAISS 인덱스 → save_local. 요청마다 재인덱싱하는
안티패턴을 피하기 위해 서비스(service.py)와 분리한다.
"""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings
from app.core.errors import InfraError
from app.rag.embeddings import get_embeddings


def _load_txt_docs(docs_dir: Path) -> list[Document]:
    if not docs_dir.exists():
        raise InfraError(f"문서 폴더가 없습니다: {docs_dir}")
    docs: list[Document] = []
    for path in sorted(docs_dir.glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            docs.append(Document(page_content=text, metadata={"source": path.name}))
    if not docs:
        raise InfraError(f"인덱싱할 txt 문서가 없습니다: {docs_dir}")
    return docs


def build_index(docs_dir: Path | None = None, out_dir: Path | None = None) -> dict:
    """txt 문서를 청킹·임베딩해 FAISS 인덱스를 out_dir에 저장한다."""
    from langchain_community.vectorstores import FAISS

    settings = get_settings()
    docs_dir = docs_dir or settings.DOCS_DIR
    out_dir = out_dir or settings.VECTOR_DIR

    docs = _load_txt_docs(docs_dir)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(docs)

    store = FAISS.from_documents(chunks, get_embeddings())
    out_dir.mkdir(parents=True, exist_ok=True)
    store.save_local(str(out_dir))
    # 인덱스가 어떤 임베딩 모델로 만들어졌는지 기록(모델 변경 시 재빌드 판단용)
    (out_dir / ".embedding_model").write_text(settings.ST_EMBEDDING_MODEL, encoding="utf-8")
    return {"docs": len(docs), "chunks": len(chunks), "out_dir": str(out_dir)}


def index_is_current(out_dir: Path | None = None) -> bool:
    """디스크 인덱스가 현재 임베딩 모델과 일치하고 완전한지 확인한다."""
    settings = get_settings()
    out_dir = out_dir or settings.VECTOR_DIR
    if not ((out_dir / "index.faiss").exists() and (out_dir / "index.pkl").exists()):
        return False
    marker = out_dir / ".embedding_model"
    return marker.exists() and marker.read_text(encoding="utf-8").strip() == settings.ST_EMBEDDING_MODEL


if __name__ == "__main__":
    print(build_index())
