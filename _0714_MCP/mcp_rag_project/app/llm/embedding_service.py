"""
OpenAI 임베딩과 API 키가 필요 없는 로컬 임베딩을 제공합니다.
"""

# 미래 타입 힌트 평가 방식을 사용합니다.
from __future__ import annotations

# 해시 기반 로컬 임베딩을 만들기 위해 hashlib을 가져옵니다.
import hashlib

# 벡터 정규화와 배열 계산을 위해 NumPy를 가져옵니다.
import numpy as np

# OpenAI 임베딩 API를 호출하기 위해 OpenAI 클라이언트를 가져옵니다.
from openai import OpenAI

# 프로젝트 설정을 가져옵니다.
from app.config.settings import Settings


# 임베딩 생성 기능을 담당하는 클래스를 정의합니다.
class EmbeddingService:
    """설정에 따라 로컬 또는 OpenAI 임베딩을 생성합니다."""

    # 서비스 생성 시 설정 객체를 전달받습니다.
    def __init__(self, settings: Settings) -> None:
        # 전달받은 설정을 인스턴스 변수에 저장합니다.
        self.settings = settings

        # OpenAI API 키가 설정된 경우에만 OpenAI 클라이언트를 생성합니다.
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    # 현재 사용하는 임베딩 차원을 반환합니다.
    @property
    def dimension(self) -> int:
        """현재 임베딩 벡터의 차원을 반환합니다."""

        # OpenAI text-embedding-3-small 모델의 기본 차원을 반환합니다.
        if self.settings.embedding_backend.lower() == "openai":
            return 1536

        # 로컬 임베딩 설정에서 정의한 차원을 반환합니다.
        return self.settings.local_embedding_dimension

    # 여러 텍스트를 벡터로 변환합니다.
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """문서 목록을 임베딩 벡터 목록으로 변환합니다."""

        # OpenAI 백엔드를 선택한 경우 OpenAI 임베딩을 생성합니다.
        if self.settings.embedding_backend.lower() == "openai":
            return self._embed_openai(texts)

        # 기본값으로 API 키가 필요 없는 로컬 임베딩을 생성합니다.
        return [self._embed_local(text) for text in texts]

    # 검색 질문 하나를 벡터로 변환합니다.
    def embed_query(self, text: str) -> list[float]:
        """검색 질문을 하나의 임베딩 벡터로 변환합니다."""

        # 기존 문서 임베딩 함수를 재사용하여 첫 번째 결과를 반환합니다.
        return self.embed_documents([text])[0]

    # OpenAI 임베딩 API를 호출합니다.
    def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        """OpenAI API를 사용하여 실제 의미 기반 임베딩을 생성합니다."""

        # OpenAI 클라이언트가 없으면 명확한 오류를 발생시킵니다.
        if self.client is None:
            raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다.")

        # OpenAI Embeddings API에 모델 이름과 텍스트 목록을 전달합니다.
        response = self.client.embeddings.create(
            model=self.settings.openai_embedding_model,
            input=texts,
        )

        # API 응답에서 각 임베딩 배열만 추출하여 반환합니다.
        return [item.embedding for item in response.data]

    # 로컬에서 결정적인 해시 임베딩을 생성합니다.
    def _embed_local(self, text: str) -> list[float]:
        """실습용 로컬 임베딩을 생성합니다."""

        # 설정된 차원만큼 0으로 채운 NumPy 배열을 생성합니다.
        vector = np.zeros(self.settings.local_embedding_dimension, dtype=np.float32)

        # 공백을 기준으로 텍스트를 단어 토큰으로 나눕니다.
        tokens = text.lower().split()

        # 각 토큰을 순회하며 벡터의 특정 위치에 값을 누적합니다.
        for token in tokens:
            # 토큰의 SHA-256 해시값을 생성합니다.
            digest = hashlib.sha256(token.encode("utf-8")).digest()

            # 해시의 앞 4바이트를 정수로 바꾼 뒤 벡터 인덱스로 변환합니다.
            index = int.from_bytes(digest[:4], "little") % len(vector)

            # 해시의 다음 바이트를 이용해 양수 또는 음수 부호를 결정합니다.
            sign = 1.0 if digest[4] % 2 == 0 else -1.0

            # 계산한 위치에 부호 값을 누적합니다.
            vector[index] += sign

        # 벡터 길이를 계산합니다.
        norm = float(np.linalg.norm(vector))

        # 0으로 나누는 문제를 막기 위해 값이 있을 때만 정규화합니다.
        if norm > 0.0:
            vector = vector / norm

        # NumPy 배열을 일반 Python 리스트로 변환하여 반환합니다.
        return vector.tolist()
