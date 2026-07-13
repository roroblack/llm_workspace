# -*- coding: utf-8 -*-
"""
torch_metrics.py

역할:
    - API 호출 없이도 CoT 실습의 핵심인 '정답률 계산'을 확인합니다.
    - pandas로 CSV 데이터를 읽고 torch Tensor로 정답률을 계산합니다.
"""

# pandas는 CSV 파일을 읽고 표 형태 데이터를 다루기 위해 사용합니다.
import pandas as pd

# torch는 정답 배열과 예측 배열을 Tensor로 바꾸고 정확도를 계산하기 위해 사용합니다.
import torch

# common.py의 DATA 경로를 공통 데이터 폴더로 사용합니다.
from common import DATA


def load_math_data() -> pd.DataFrame:
    """쇼핑 계산 문제 CSV를 pandas DataFrame으로 읽어 반환합니다."""
    # math_word_problems.csv 파일 경로를 생성합니다.
    csv_path = DATA / "math_word_problems.csv"

    # 파일이 없으면 명확한 오류 메시지를 발생시킵니다.
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

    # CSV 파일을 읽어서 DataFrame으로 반환합니다.
    return pd.read_csv(csv_path, encoding="utf-8")


def calculate_accuracy_with_torch(gold_answers: list[int], predictions: list[int]) -> float:
    """정답 리스트와 예측 리스트를 torch Tensor로 변환하여 정확도를 계산합니다."""
    # 정답 값을 정수 Tensor로 변환합니다.
    gold_tensor = torch.tensor(gold_answers, dtype=torch.long)

    # 예측 값을 정수 Tensor로 변환합니다.
    pred_tensor = torch.tensor(predictions, dtype=torch.long)

    # 두 Tensor의 크기가 다르면 비교할 수 없으므로 오류를 발생시킵니다.
    if gold_tensor.shape != pred_tensor.shape:
        raise ValueError("정답 개수와 예측 개수가 서로 다릅니다.")

    # gold_tensor == pred_tensor는 각 위치가 맞았는지 True/False Tensor를 만듭니다.
    correct_tensor = gold_tensor == pred_tensor

    # float()로 True/False를 1.0/0.0으로 바꾼 뒤 평균을 구하면 정확도가 됩니다.
    accuracy = correct_tensor.float().mean().item()

    # 파이썬 float 값으로 반환합니다.
    return accuracy


def run_offline_accuracy_demo() -> None:
    """API 없이 고정 예측값으로 직접 답변과 CoT의 정답률 비교를 시연합니다."""
    # CSV 데이터를 읽습니다.
    df = load_math_data()

    # answer 컬럼을 정수 리스트로 변환합니다.
    gold = df["answer"].astype(int).tolist()

    # 직접 답변 예측 예시입니다. 일부러 몇 개는 틀리게 넣어 정답률 차이를 보여 줍니다.
    direct_pred = [213000, 89000, 44000, 107000, 80000, 160000, 168000, 135000]

    # CoT 예측 예시입니다. 단계적 풀이를 했을 때 정답이 나온 상황을 가정합니다.
    cot_pred = gold.copy()

    # torch로 직접 답변 정확도를 계산합니다.
    direct_acc = calculate_accuracy_with_torch(gold, direct_pred)

    # torch로 CoT 정확도를 계산합니다.
    cot_acc = calculate_accuracy_with_torch(gold, cot_pred)

    # 결과 표 제목을 출력합니다.
    print("\n[Torch 기반 정답률 계산]")
    print("-" * 80)

    # 각 문제의 정답과 두 방식의 예측을 출력합니다.
    for idx, row in df.iterrows():
        # 현재 문제의 정답을 가져옵니다.
        ans = int(row["answer"])

        # 직접 답변이 맞았는지 표시합니다.
        d_mark = "O" if direct_pred[idx] == ans else "X"

        # CoT 답변이 맞았는지 표시합니다.
        c_mark = "O" if cot_pred[idx] == ans else "X"

        # 한 줄 결과를 출력합니다.
        print(
            f"{row['problem_id']} 정답={ans:>7} | "
            f"직접={direct_pred[idx]:>7} {d_mark} | "
            f"CoT={cot_pred[idx]:>7} {c_mark}"
        )

    # 전체 정확도를 백분율로 출력합니다.
    print("-" * 80)
    print(f"직접 답변 정답률: {direct_acc:.0%}")
    print(f"CoT 정답률     : {cot_acc:.0%}")
