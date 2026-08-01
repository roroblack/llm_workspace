"""
허용된 data/files 폴더 안에서만 파일을 읽고 쓰는 어댑터입니다.
"""

# 경로를 운영체제와 무관하게 처리하기 위해 Path를 가져옵니다.
from pathlib import Path


# 안전한 파일 시스템 어댑터를 정의합니다.
class FileSystemAdapter:
    """기준 디렉터리 밖으로 나가지 못하도록 제한한 파일 접근 기능입니다."""

    # 파일 접근 기준 디렉터리를 전달받습니다.
    def __init__(self, base_dir: Path) -> None:
        # 절대 경로로 변환한 기준 디렉터리를 저장합니다.
        self.base_dir = base_dir.resolve()

        # 기준 디렉터리가 없으면 생성합니다.
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # 사용자 입력 파일명을 안전한 절대 경로로 변환합니다.
    def _resolve(self, filename: str) -> Path:
        """경로 탈출을 차단한 파일 경로를 반환합니다."""

        # 기준 디렉터리와 사용자 파일명을 결합한 뒤 절대 경로로 변환합니다.
        target = (self.base_dir / filename).resolve()

        # 계산한 경로가 기준 디렉터리 내부인지 검사합니다.
        if target != self.base_dir and self.base_dir not in target.parents:
            raise ValueError("허용된 파일 디렉터리 밖에는 접근할 수 없습니다.")

        # 검증된 경로를 반환합니다.
        return target

    # 파일 목록을 반환합니다.
    def list_files(self) -> list[dict]:
        """허용된 디렉터리의 파일 정보를 반환합니다."""

        # 하위 폴더를 포함한 실제 파일만 순회합니다.
        return [
            {
                "name": str(path.relative_to(self.base_dir)),
                "size": path.stat().st_size,
            }
            for path in sorted(self.base_dir.rglob("*"))
            if path.is_file()
        ]

    # UTF-8 텍스트 파일을 읽습니다.
    def read_text(self, filename: str) -> str:
        """지정한 텍스트 파일의 전체 내용을 반환합니다."""

        # 안전한 경로를 계산합니다.
        target = self._resolve(filename)

        # 파일이 존재하지 않으면 오류를 발생시킵니다.
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filename}")

        # UTF-8 인코딩으로 내용을 읽어 반환합니다.
        return target.read_text(encoding="utf-8")

    # UTF-8 텍스트 파일을 저장합니다.
    def write_text(self, filename: str, content: str) -> dict:
        """지정한 파일에 텍스트를 저장합니다."""

        # 안전한 경로를 계산합니다.
        target = self._resolve(filename)

        # 필요한 상위 폴더가 없으면 생성합니다.
        target.parent.mkdir(parents=True, exist_ok=True)

        # UTF-8 인코딩으로 내용을 저장합니다.
        target.write_text(content, encoding="utf-8")

        # 저장 결과를 반환합니다.
        return {"filename": str(target.relative_to(self.base_dir)), "characters": len(content)}
