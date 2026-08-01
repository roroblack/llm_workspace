"""
저장된 두 모델의 예측 결과로 블라인드 평가 CSV를 생성합니다.
"""

# 프로젝트 패키지를 찾기 위해 sys를 가져옵니다.
import sys

# 파일 경로 처리를 위해 Path를 가져옵니다.
from pathlib import Path


# 현재 프로젝트의 루트 경로를 계산합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 프로젝트 루트를 파이썬 모듈 검색 경로에 추가합니다.
sys.path.insert(0, str(PROJECT_ROOT))

# 블라인드 평가 생성 함수를 가져옵니다.
from app.services.report_service import create_blind_review


def main() -> None:
    """
    Base와 Fine-tuned 답변을 섞은 CSV와 정답표를 생성합니다.
    """

    # 출력 디렉터리를 지정합니다.
    output_dir = PROJECT_ROOT / "outputs"

    # 블라인드 평가 파일을 생성합니다.
    result = create_blind_review(
        base_file=output_dir / "base_predictions.jsonl",
        fine_tuned_file=output_dir / "fine_tuned_predictions.jsonl",
        review_file=output_dir / "human_review.csv",
        answer_key_file=output_dir / "human_review_answer_key.json",
    )

    # 생성 결과 정보를 출력합니다.
    print(result)


# 직접 실행한 경우에만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
