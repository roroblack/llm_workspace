"""
Base와 Fine-tuned 모델을 동일한 데이터로 평가하고 비교합니다.
"""

# 프로젝트 루트를 모듈 검색 경로에 추가하기 위해 sys를 가져옵니다.
import sys

# 파일 경로를 처리하기 위해 Path를 가져옵니다.
from pathlib import Path


# 프로젝트 루트 경로를 계산합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# app 패키지를 찾을 수 있도록 프로젝트 루트를 추가합니다.
sys.path.insert(0, str(PROJECT_ROOT))

# 평가 서비스 객체를 가져옵니다.
from app.services.evaluation_service import evaluation_service


def main() -> None:
    """
    두 모델 평가를 실행하고 핵심 변화량을 출력합니다.
    """

    # BERTScore를 제외한 기본 전체 비교를 실행합니다.
    result = evaluation_service.compare(
        use_bertscore=False,
        limit=None,
    )

    # 비교 결과 파일 위치를 출력합니다.
    print(f"비교 결과 저장 완료: {result['comparison_file']}")

    # 각 지표의 변화량을 반복하여 출력합니다.
    for metric_name, values in result["comparison"].items():
        print(
            f"{metric_name}: "
            f"base={values['base']}, "
            f"fine_tuned={values['fine_tuned']}, "
            f"improvement={values['improvement_delta']}"
        )


# 직접 실행할 때만 전체 평가를 수행합니다.
if __name__ == "__main__":
    main()
