# -*- coding: utf-8 -*-
"""PyTorch로 프로젝트 작업 상태를 간단히 집계하는 실습 모듈입니다."""

# pathlib는 프로젝트 데이터 파일 경로를 안전하게 만들기 위해 사용합니다.
from pathlib import Path

# pandas는 CSV 데이터를 읽고 표 형태로 다루기 위해 사용합니다.
import pandas as pd

# torch는 텐서 기반 집계와 비율 계산을 보여 주기 위해 사용합니다.
import torch


# 프로젝트 루트 경로를 계산합니다.
ROOT = Path(__file__).resolve().parent.parent

# 데이터 폴더 경로를 계산합니다.
DATA = ROOT / "data"

# 프로젝트 작업 상태를 숫자로 바꾸기 위한 매핑입니다.
STATUS_TO_ID = {"완료": 0, "진행중": 1, "대기": 2}

# 숫자 ID를 다시 상태명으로 출력하기 위한 역매핑입니다.
ID_TO_STATUS = {v: k for k, v in STATUS_TO_ID.items()}


def run_torch_status_demo() -> None:
    """project_tasks.csv를 읽어 상태별 개수와 비율을 torch 텐서로 계산합니다."""
    # 프로젝트 작업 CSV 파일을 읽습니다.
    df = pd.read_csv(DATA / "project_tasks.csv")

    # status 컬럼의 문자열 값을 숫자 ID로 변환합니다.
    status_ids = [STATUS_TO_ID[status] for status in df["status"].tolist()]

    # 상태 ID 리스트를 PyTorch LongTensor로 변환합니다.
    status_tensor = torch.tensor(status_ids, dtype=torch.long)

    # bincount는 0, 1, 2 상태 ID가 각각 몇 번 나왔는지 계산합니다.
    counts = torch.bincount(status_tensor, minlength=len(STATUS_TO_ID))

    # 전체 작업 수를 텐서 연산에 사용할 실수형 값으로 변환합니다.
    total = counts.sum().to(torch.float32)

    # 상태별 비율을 계산합니다.
    ratios = counts.to(torch.float32) / total

    # 원본 데이터를 먼저 출력합니다.
    print("\n[프로젝트 작업 목록]")
    print(df.to_string(index=False))

    # 상태별 개수와 비율을 출력합니다.
    print("\n[PyTorch 상태 집계]")
    for status_id in range(len(STATUS_TO_ID)):
        print(
            f"{ID_TO_STATUS[status_id]}: "
            f"{int(counts[status_id].item())}건, "
            f"{ratios[status_id].item() * 100:.1f}%"
        )

    # 완료율을 별도로 계산합니다.
    done_rate = ratios[STATUS_TO_ID["완료"]].item() * 100

    # 완료율 해석 메시지를 출력합니다.
    print(f"\n전체 완료율: {done_rate:.1f}%")
