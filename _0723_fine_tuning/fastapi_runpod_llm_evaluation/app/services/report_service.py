"""
Base와 Fine-tuned 답변을 섞어 블라인드 사람 평가 CSV를 생성합니다.
"""

# 정답표 JSON 파일을 만들기 위해 json을 가져옵니다.
import json

# 답변 순서를 무작위로 섞기 위해 random을 가져옵니다.
import random

# 파일 경로를 다루기 위해 Path를 가져옵니다.
from pathlib import Path

# CSV 파일 생성을 위해 pandas를 가져옵니다.
import pandas as pd


def load_jsonl(file_path: Path) -> list[dict]:
    """
    JSONL 파일을 파이썬 딕셔너리 목록으로 읽습니다.
    """

    # 입력 파일 존재 여부를 확인합니다.
    if not file_path.exists():
        raise FileNotFoundError(f"예측 파일이 없습니다: {file_path}")

    # 읽은 데이터를 저장할 리스트입니다.
    rows: list[dict] = []

    # UTF-8 인코딩으로 파일을 엽니다.
    with file_path.open("r", encoding="utf-8") as file:
        # 한 줄씩 읽습니다.
        for line in file:
            # 빈 줄은 건너뜁니다.
            if not line.strip():
                continue

            # JSON 문자열을 딕셔너리로 변환합니다.
            rows.append(json.loads(line))

    # 전체 데이터를 반환합니다.
    return rows


def create_blind_review(
    base_file: Path,
    fine_tuned_file: Path,
    review_file: Path,
    answer_key_file: Path,
    random_seed: int = 42,
) -> dict[str, str | int]:
    """
    두 모델의 답변을 A와 B로 무작위 배치하여 평가 파일을 생성합니다.
    """

    # 동일한 실행 결과를 재현할 수 있도록 난수 시드를 고정합니다.
    random.seed(random_seed)

    # Base 모델 예측 결과를 읽습니다.
    base_rows = load_jsonl(base_file)

    # Fine-tuned 모델 예측 결과를 읽습니다.
    fine_rows = load_jsonl(fine_tuned_file)

    # ID를 키로 사용하는 Base 모델 조회 딕셔너리를 만듭니다.
    base_map = {str(row["id"]): row for row in base_rows}

    # ID를 키로 사용하는 Fine-tuned 모델 조회 딕셔너리를 만듭니다.
    fine_map = {str(row["id"]): row for row in fine_rows}

    # 평가자가 입력할 CSV 행을 저장합니다.
    review_rows: list[dict] = []

    # A와 B에 배치된 실제 모델 정보를 저장합니다.
    answer_key: dict[str, dict[str, str]] = {}

    # 두 모델에 공통으로 존재하는 평가 ID만 정렬하여 반복합니다.
    for evaluation_id in sorted(set(base_map) & set(fine_map)):
        # 현재 Base 모델 결과를 가져옵니다.
        base_row = base_map[evaluation_id]

        # 현재 Fine-tuned 모델 결과를 가져옵니다.
        fine_row = fine_map[evaluation_id]

        # 두 답변 배치 순서를 무작위로 결정합니다.
        if random.randint(0, 1) == 0:
            answer_a = base_row["prediction"]
            answer_b = fine_row["prediction"]
            model_a = "base"
            model_b = "fine_tuned"
        else:
            answer_a = fine_row["prediction"]
            answer_b = base_row["prediction"]
            model_a = "fine_tuned"
            model_b = "base"

        # 사람이 평가할 항목을 구성합니다.
        review_rows.append(
            {
                "id": evaluation_id,
                "category": base_row.get("category", "unknown"),
                "prompt": base_row["prompt"],
                "reference": base_row["reference"],
                "answer_a": answer_a,
                "answer_b": answer_b,
                "winner_A_B_TIE": "",
                "a_accuracy_1_5": "",
                "b_accuracy_1_5": "",
                "a_relevance_1_5": "",
                "b_relevance_1_5": "",
                "a_korean_naturalness_1_5": "",
                "b_korean_naturalness_1_5": "",
                "a_safety_1_5": "",
                "b_safety_1_5": "",
                "comment": "",
            }
        )

        # 실제 모델 대응 관계를 별도 정답표에 저장합니다.
        answer_key[evaluation_id] = {
            "answer_a_model": model_a,
            "answer_b_model": model_b,
        }

    # 결과 파일의 상위 디렉터리를 생성합니다.
    review_file.parent.mkdir(parents=True, exist_ok=True)

    # 평가 행을 DataFrame으로 변환합니다.
    dataframe = pd.DataFrame(review_rows)

    # Excel에서 한글이 깨지지 않도록 UTF-8 BOM 인코딩으로 저장합니다.
    dataframe.to_csv(review_file, index=False, encoding="utf-8-sig")

    # 정답표를 JSON 파일로 저장합니다.
    with answer_key_file.open("w", encoding="utf-8") as file:
        json.dump(answer_key, file, ensure_ascii=False, indent=2)

    # 생성된 파일 정보와 평가 건수를 반환합니다.
    return {
        "review_file": str(review_file),
        "answer_key_file": str(answer_key_file),
        "sample_count": len(review_rows),
    }
