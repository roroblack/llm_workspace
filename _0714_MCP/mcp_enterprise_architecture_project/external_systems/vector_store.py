"""
추가 모델 다운로드 없이 실행 가능한 TF-IDF 유사 문서 검색 어댑터입니다.
"""

# JSON 인덱스를 저장하기 위해 json을 가져옵니다.
import json

# 단어를 추출하기 위해 re를 가져옵니다.
import re

# 로그 계산과 벡터 길이 계산을 위해 math를 가져옵니다.
import math

# 파일 경로를 처리하기 위해 Path를 가져옵니다.
from pathlib import Path

# 단어 빈도를 계산하기 위해 Counter를 가져옵니다.
from collections import Counter


# Vector Search 어댑터를 정의합니다.
class VectorSearchAdapter:
    """TF-IDF 벡터와 코사인 유사도를 사용하는 교육용 검색기입니다."""

    # 문서 폴더와 인덱스 파일을 전달받습니다.
    def __init__(self, docs_dir: Path, index_file: Path) -> None:
        # 문서 폴더를 저장합니다.
        self.docs_dir = docs_dir

        # 인덱스 파일 경로를 저장합니다.
        self.index_file = index_file

        # 필요한 폴더를 생성합니다.
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    # 텍스트를 단어 토큰으로 분리합니다.
    def _tokens(self, text: str) -> list[str]:
        """한글, 영문, 숫자로 구성된 2글자 이상 토큰을 반환합니다."""

        # 정규식을 사용하여 토큰을 소문자로 추출합니다.
        return re.findall(r"[가-힣A-Za-z0-9_]{2,}", text.lower())

    # 문서 인덱스를 재구축합니다.
    def rebuild(self) -> dict:
        """문서별 TF-IDF 벡터를 계산하여 JSON으로 저장합니다."""

        # txt와 md 파일을 정렬하여 가져옵니다.
        paths = sorted([
            path for path in self.docs_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in {".txt", ".md"}
        ])

        # 각 문서 내용을 읽습니다.
        documents = [
            {
                "source": str(path.relative_to(self.docs_dir)),
                "content": path.read_text(encoding="utf-8"),
            }
            for path in paths
        ]

        # 각 문서를 토큰 목록으로 변환합니다.
        token_lists = [self._tokens(item["content"]) for item in documents]

        # 각 단어가 몇 개 문서에 등장하는지 계산합니다.
        document_frequency: Counter[str] = Counter()

        # 문서별 중복 단어를 제거하여 DF를 누적합니다.
        for tokens in token_lists:
            document_frequency.update(set(tokens))

        # 전체 문서 수를 저장합니다.
        document_count = len(documents)

        # 각 문서의 TF-IDF 벡터를 계산합니다.
        for document, tokens in zip(documents, token_lists):
            # 문서 내부 단어 빈도를 계산합니다.
            term_frequency = Counter(tokens)

            # 벡터를 저장할 딕셔너리를 생성합니다.
            vector: dict[str, float] = {}

            # 각 단어의 TF-IDF 값을 계산합니다.
            for term, count in term_frequency.items():
                # 단어 빈도를 전체 토큰 수로 나눕니다.
                tf = count / max(1, len(tokens))

                # 부드러운 IDF 공식을 사용합니다.
                idf = math.log((1 + document_count) / (1 + document_frequency[term])) + 1.0

                # TF와 IDF를 곱하여 저장합니다.
                vector[term] = tf * idf

            # 문서에 계산된 벡터를 추가합니다.
            document["vector"] = vector

        # 인덱스 전체 정보를 구성합니다.
        index = {
            "document_count": document_count,
            "document_frequency": dict(document_frequency),
            "documents": documents,
        }

        # JSON 인덱스를 UTF-8로 저장합니다.
        self.index_file.write_text(
            json.dumps(index, ensure_ascii=False),
            encoding="utf-8",
        )

        # 처리 결과를 반환합니다.
        return {"indexed_documents": document_count}

    # 희소 벡터 코사인 유사도를 계산합니다.
    def _cosine(self, left: dict[str, float], right: dict[str, float]) -> float:
        """두 희소 벡터의 코사인 유사도를 반환합니다."""

        # 공통 단어의 곱을 합산하여 내적을 계산합니다.
        dot = sum(value * right.get(term, 0.0) for term, value in left.items())

        # 왼쪽 벡터 길이를 계산합니다.
        left_norm = math.sqrt(sum(value * value for value in left.values()))

        # 오른쪽 벡터 길이를 계산합니다.
        right_norm = math.sqrt(sum(value * value for value in right.values()))

        # 어느 한쪽이라도 0 벡터이면 유사도를 0으로 반환합니다.
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0

        # 코사인 유사도를 반환합니다.
        return dot / (left_norm * right_norm)

    # 질문과 유사한 문서를 검색합니다.
    def search(self, query: str, top_k: int = 4) -> list[dict]:
        """TF-IDF 코사인 유사도로 문서를 검색합니다."""

        # 인덱스가 없으면 자동으로 재구축합니다.
        if not self.index_file.exists():
            self.rebuild()

        # 저장된 인덱스를 읽습니다.
        index = json.loads(self.index_file.read_text(encoding="utf-8"))

        # 질문 토큰의 빈도를 계산합니다.
        query_tokens = self._tokens(query)
        query_tf = Counter(query_tokens)

        # 질문 벡터를 저장할 딕셔너리를 생성합니다.
        query_vector: dict[str, float] = {}

        # 질문의 각 단어에 TF-IDF 값을 계산합니다.
        for term, count in query_tf.items():
            # 질문 내부의 단어 빈도를 계산합니다.
            tf = count / max(1, len(query_tokens))

            # 저장된 문서 빈도로 IDF를 계산합니다.
            df = index["document_frequency"].get(term, 0)
            idf = math.log((1 + index["document_count"]) / (1 + df)) + 1.0

            # 질문 벡터에 값을 저장합니다.
            query_vector[term] = tf * idf

        # 각 문서와 질문의 유사도를 계산합니다.
        results = [
            {
                "source": item["source"],
                "content": item["content"],
                "score": self._cosine(query_vector, item["vector"]),
            }
            for item in index["documents"]
        ]

        # 높은 점수 순으로 정렬합니다.
        results.sort(key=lambda item: item["score"], reverse=True)

        # 요청한 개수를 안전한 범위로 제한하여 반환합니다.
        return results[:max(1, min(top_k, 20))]
