# -*- coding: utf-8 -*-
"""
로컬 Vector DB 서비스입니다.

이 프로젝트는 외부 DB 서버 없이도 PyCharm에서 바로 실행되도록,
문서 임베딩을 JSON 파일에 저장하는 '미니 Vector DB'를 구현합니다.

특징:
  1) OPENAI_API_KEY가 있으면 OpenAI 임베딩을 사용합니다.
  2) 키가 없으면 Torch 기반 해시 임베딩을 사용하여 로컬 실습이 가능합니다.
  3) 검색은 torch.nn.functional.cosine_similarity로 수행합니다.
"""

# json은 벡터 저장 파일을 읽고 쓰기 위해 사용합니다.
import json

# hashlib는 API 키가 없을 때 문자열을 고정 길이 벡터로 바꾸기 위해 사용합니다.
import hashlib

# pathlib.Path는 문서 경로와 저장 경로를 안전하게 다루기 위해 사용합니다.
from pathlib import Path

# typing.Any는 검색 결과 dict 타입을 표현하기 위해 사용합니다.
from typing import Any

# torch는 벡터 계산과 코사인 유사도 계산에 사용합니다.
import torch

# torch.nn.functional은 cosine_similarity 함수를 사용하기 위해 import합니다.
import torch.nn.functional as F

# common 모듈에서 공통 경로와 API 설정을 가져옵니다.
from common import DOCS, VECTOR_STORE, OPENAI_EMBEDDING_MODEL, get_openai_client, has_key


# VECTOR_FILE은 Vector DB가 저장될 JSON 파일 경로입니다.
VECTOR_FILE = VECTOR_STORE / "vectors.json"

# LOCAL_DIM은 API 키가 없을 때 사용할 로컬 해시 임베딩 차원입니다.
LOCAL_DIM = 128


def _ensure_dirs() -> None:
    """Vector DB 저장 폴더와 문서 폴더가 없으면 생성합니다."""
    # vector_store 폴더를 생성합니다.
    VECTOR_STORE.mkdir(parents=True, exist_ok=True)

    # docs 폴더를 생성합니다.
    DOCS.mkdir(parents=True, exist_ok=True)


def _read_documents() -> list[dict[str, str]]:
    """data/docs 폴더의 txt 문서를 읽어 Vector DB 입력 문서 목록으로 변환합니다."""
    # 폴더가 반드시 존재하도록 보장합니다.
    _ensure_dirs()

    # 문서 목록을 담을 리스트를 생성합니다.
    docs: list[dict[str, str]] = []

    # docs 폴더의 모든 txt 파일을 이름순으로 반복합니다.
    for path in sorted(DOCS.glob("*.txt")):
        # 각 파일의 텍스트 내용을 UTF-8로 읽습니다.
        text = path.read_text(encoding="utf-8").strip()

        # 빈 파일은 검색 품질을 떨어뜨리므로 건너뜁니다.
        if not text:
            continue

        # 문서 ID, 출처, 텍스트를 dict로 저장합니다.
        docs.append({"doc_id": path.stem, "source": path.name, "text": text})

    # 읽어온 문서 목록을 반환합니다.
    return docs


def _local_hash_embedding(text: str, dim: int = LOCAL_DIM) -> list[float]:
    """OpenAI 키가 없을 때 사용하는 Torch 실습용 해시 임베딩입니다."""
    # 0으로 채운 벡터 텐서를 생성합니다.
    vec = torch.zeros(dim, dtype=torch.float32)

    # 텍스트를 공백 기준으로 나누어 간단한 토큰 목록을 만듭니다.
    tokens = text.lower().split()

    # 토큰이 하나도 없으면 0벡터를 그대로 반환합니다.
    if not tokens:
        return vec.tolist()

    # 각 토큰을 해시값으로 바꾼 뒤 벡터 위치에 누적합니다.
    for token in tokens:
        # md5는 동일한 문자열에 항상 같은 해시를 만듭니다.
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()

        # 해시 앞 8자리를 정수로 바꾼 뒤 dim 범위로 나눕니다.
        idx = int(digest[:8], 16) % dim

        # 해당 위치 값을 1 증가시킵니다.
        vec[idx] += 1.0

    # 벡터 크기가 커지는 것을 막기 위해 L2 정규화합니다.
    vec = F.normalize(vec, dim=0)

    # JSON 저장이 가능하도록 리스트로 변환합니다.
    return vec.tolist()


def _openai_embedding(text: str) -> list[float]:
    """OpenAI Embedding API로 텍스트 임베딩을 생성합니다."""
    # OpenAI 클라이언트를 생성합니다.
    client = get_openai_client()

    # 임베딩 API를 호출합니다.
    response = client.embeddings.create(model=OPENAI_EMBEDDING_MODEL, input=text)

    # 첫 번째 임베딩 벡터를 반환합니다.
    return response.data[0].embedding


def embed_text(text: str) -> list[float]:
    """환경에 따라 OpenAI 또는 로컬 해시 임베딩을 선택합니다."""
    # OpenAI 키가 있으면 실제 OpenAI 임베딩을 사용합니다.
    if has_key("OPENAI_API_KEY"):
        return _openai_embedding(text)

    # 키가 없으면 로컬 해시 임베딩을 사용합니다.
    return _local_hash_embedding(text)


def rebuild_vector_db() -> dict[str, Any]:
    """문서 폴더를 다시 읽어 Vector DB JSON 파일을 재생성합니다."""
    # 저장 폴더와 문서 폴더를 보장합니다.
    _ensure_dirs()

    # 원본 문서를 읽습니다.
    docs = _read_documents()

    # 저장할 레코드 리스트를 생성합니다.
    records: list[dict[str, Any]] = []

    # 각 문서를 하나씩 벡터화합니다.
    for doc in docs:
        # 문서 텍스트를 임베딩 벡터로 변환합니다.
        vector = embed_text(doc["text"])

        # 문서 정보와 벡터를 하나의 레코드로 저장합니다.
        records.append({**doc, "vector": vector})

    # JSON 파일에 저장할 전체 구조를 만듭니다.
    payload = {"count": len(records), "records": records}

    # 벡터 파일을 UTF-8 JSON으로 저장합니다.
    VECTOR_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # 처리 결과를 반환합니다.
    return {"saved": str(VECTOR_FILE), "count": len(records), "using_openai_embedding": has_key("OPENAI_API_KEY")}


def load_vector_db() -> list[dict[str, Any]]:
    """저장된 Vector DB를 읽고, 없으면 자동으로 생성합니다."""
    # 벡터 파일이 없으면 rebuild_vector_db를 실행합니다.
    if not VECTOR_FILE.exists():
        rebuild_vector_db()

    # JSON 파일 내용을 읽습니다.
    payload = json.loads(VECTOR_FILE.read_text(encoding="utf-8"))

    # records 목록을 반환합니다.
    return payload.get("records", [])


def search_vector_db(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    """질문과 가장 유사한 문서를 Vector DB에서 검색합니다."""
    # 저장된 벡터 레코드를 읽습니다.
    records = load_vector_db()

    # 레코드가 없으면 빈 리스트를 반환합니다.
    if not records:
        return []

    # 검색 질문을 임베딩 벡터로 변환합니다.
    query_vector = torch.tensor(embed_text(query), dtype=torch.float32)

    # 검색 결과 후보를 담을 리스트입니다.
    scored: list[dict[str, Any]] = []

    # 모든 문서 레코드를 순회합니다.
    for record in records:
        # 저장된 문서 벡터를 torch 텐서로 변환합니다.
        doc_vector = torch.tensor(record["vector"], dtype=torch.float32)

        # 두 벡터 차원이 다른 경우는 임베딩 방식이 바뀐 것이므로 DB 재생성이 필요합니다.
        if query_vector.numel() != doc_vector.numel():
            raise RuntimeError("임베딩 차원이 다릅니다. /api/vector/rebuild 를 먼저 실행하세요.")

        # 코사인 유사도를 계산합니다.
        score = F.cosine_similarity(query_vector.unsqueeze(0), doc_vector.unsqueeze(0)).item()

        # 결과 후보를 저장합니다.
        scored.append(
            {
                "doc_id": record["doc_id"],
                "source": record["source"],
                "score": round(float(score), 4),
                "text": record["text"],
            }
        )

    # 점수가 높은 순서로 정렬한 뒤 top_k개만 반환합니다.
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]
