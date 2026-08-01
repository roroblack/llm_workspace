"""
docs 폴더의 문서를 읽고 검색용 청크로 분할합니다.
"""

# 미래 타입 힌트 평가 방식을 사용합니다.
from __future__ import annotations

# 프로젝트 설정을 가져옵니다.
from app.config.settings import Settings


# 문서 파일 처리 서비스를 정의합니다.
class DocumentService:
    """텍스트 계열 문서를 읽고 중첩 청크로 분할합니다."""

    # 설정 객체를 전달받습니다.
    def __init__(self, settings: Settings) -> None:
        # 설정을 저장합니다.
        self.settings = settings

        # 문서 디렉터리가 없으면 생성합니다.
        self.settings.docs_dir.mkdir(parents=True, exist_ok=True)

    # docs 폴더에 있는 파일 목록을 반환합니다.
    def list_files(self) -> list[str]:
        """지원하는 문서 파일명을 반환합니다."""

        # 지원 확장자를 정의합니다.
        supported = {".txt", ".md"}

        # 지원 확장자를 가진 파일만 정렬하여 반환합니다.
        return [
            path.name
            for path in sorted(self.settings.docs_dir.iterdir())
            if path.is_file() and path.suffix.lower() in supported
        ]

    # 모든 문서를 읽어 청크 목록으로 변환합니다.
    def load_chunks(self) -> list[dict]:
        """docs 폴더의 전체 문서를 검색용 청크로 반환합니다."""

        # 모든 청크를 저장할 목록을 생성합니다.
        chunks: list[dict] = []

        # 지원 문서 파일명을 순회합니다.
        for filename in self.list_files():
            # 문서의 전체 경로를 만듭니다.
            path = self.settings.docs_dir / filename

            # UTF-8 인코딩으로 문서를 읽습니다.
            text = path.read_text(encoding="utf-8")

            # 문서를 중첩 청크로 분할합니다.
            split_texts = self._split_text(text)

            # 각 청크에 출처와 순번 메타데이터를 붙입니다.
            for chunk_index, chunk_text in enumerate(split_texts):
                chunks.append(
                    {
                        "content": chunk_text,
                        "source": filename,
                        "chunk_index": chunk_index,
                    }
                )

        # 전체 문서 청크를 반환합니다.
        return chunks

    # 긴 텍스트를 일정 크기의 중첩 청크로 분할합니다.
    def _split_text(self, text: str) -> list[str]:
        """문자 수 기준으로 문서를 분할합니다."""

        # 빈 문자열이면 빈 목록을 반환합니다.
        if not text.strip():
            return []

        # 다음 청크 시작 위치의 이동 크기를 계산합니다.
        step = max(1, self.settings.chunk_size - self.settings.chunk_overlap)

        # 분할 결과를 저장할 목록을 생성합니다.
        chunks: list[str] = []

        # step 간격으로 문서 시작 위치를 이동합니다.
        for start in range(0, len(text), step):
            # 현재 청크의 끝 위치를 계산합니다.
            end = start + self.settings.chunk_size

            # 현재 범위의 문자열을 잘라 앞뒤 공백을 제거합니다.
            chunk = text[start:end].strip()

            # 비어 있지 않은 청크만 결과에 추가합니다.
            if chunk:
                chunks.append(chunk)

            # 문서 마지막까지 읽었다면 반복을 종료합니다.
            if end >= len(text):
                break

        # 분할된 청크 목록을 반환합니다.
        return chunks
