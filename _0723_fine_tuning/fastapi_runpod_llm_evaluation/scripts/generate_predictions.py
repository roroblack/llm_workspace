"""
명령행에서 특정 모델의 평가 예측 결과를 생성합니다.
"""

# 명령행 인자를 처리하기 위해 argparse를 가져옵니다.
import argparse

# 프로젝트 루트 경로를 모듈 검색 경로에 추가하기 위해 sys를 가져옵니다.
import sys

# 파일 경로를 처리하기 위해 Path를 가져옵니다.
from pathlib import Path


# 현재 스크립트의 상위 프로젝트 경로를 계산합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# app 패키지를 가져올 수 있도록 프로젝트 루트를 모듈 검색 경로에 추가합니다.
sys.path.insert(0, str(PROJECT_ROOT))

# 경로 설정 이후 평가 서비스를 가져옵니다.
from app.services.evaluation_service import evaluation_service


def parse_args() -> argparse.Namespace:
    """
    명령행에서 모델 종류와 입출력 파일을 읽습니다.
    """

    # 명령행 파서를 생성합니다.
    parser = argparse.ArgumentParser(
        description="평가 질문에 대한 모델 예측 생성"
    )

    # base 또는 fine_tuned 모델 종류를 필수 인자로 받습니다.
    parser.add_argument(
        "--model-kind",
        choices=["base", "fine_tuned"],
        required=True,
    )

    # 평가 데이터 파일 경로를 받습니다.
    parser.add_argument(
        "--input-file",
        type=Path,
        default=PROJECT_ROOT / "data/evaluation.jsonl",
    )

    # 결과 파일 경로를 받습니다.
    parser.add_argument(
        "--output-file",
        type=Path,
        required=True,
    )

    # 평가할 최대 샘플 수를 받습니다.
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    # 완성된 인자를 반환합니다.
    return parser.parse_args()


def main() -> None:
    """
    평가 데이터를 읽고 모델 예측 결과를 JSONL로 저장합니다.
    """

    # 명령행 인자를 읽습니다.
    args = parse_args()

    # 지정한 평가 데이터를 읽습니다.
    rows = evaluation_service.load_evaluation_rows(
        file_path=args.input_file,
        limit=args.limit,
    )

    # 선택한 모델의 전체 예측을 생성합니다.
    predictions = evaluation_service.generate_predictions(
        model_kind=args.model_kind,
        rows=rows,
    )

    # 생성 결과를 지정한 JSONL 파일에 저장합니다.
    evaluation_service.save_jsonl(
        predictions,
        args.output_file,
    )

    # 생성 건수와 파일 위치를 출력합니다.
    print(f"{len(predictions)}개 예측 저장 완료: {args.output_file}")


# 이 파일을 직접 실행한 경우에만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
