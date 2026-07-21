# -*- coding: utf-8 -*-
"""확정 facts를 기반으로 월간 매출 차트를 PNG로 저장합니다."""

from pathlib import Path
import matplotlib
# PyCharm 콘솔이나 화면 없는 배치 환경에서도 파일 저장이 가능하도록 Agg 백엔드를 지정합니다.
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from app.core.common import ROOT

# 보고서와 차트를 같은 폴더에 저장합니다.
REPORTS_DIR = ROOT / "reports"


def _configure_korean_font() -> None:
    """koreanize_matplotlib이 설치되어 있으면 한글 폰트를 자동 적용합니다."""
    try:
        # 패키지를 import하는 것만으로 matplotlib 한글 폰트 설정이 적용됩니다.
        import koreanize_matplotlib  # noqa: F401
    except ImportError:
        # 패키지가 없더라도 차트 생성을 중단하지 않고 기본 폰트로 진행합니다.
        print("[안내] koreanize-matplotlib이 없어 환경에 따라 한글이 깨질 수 있습니다.")


def make_category_chart(facts: dict, filename: str | None = None) -> Path:
    """최신 달 카테고리별 매출 막대그래프를 PNG 파일로 저장합니다."""
    # 한글 폰트 적용을 시도합니다.
    _configure_korean_font()
    # 차트를 저장할 폴더가 없으면 생성합니다.
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    # 내림차순 facts에서 카테고리명을 순서대로 추출합니다.
    categories = list(facts["by_category"].keys())
    # 큰 원 단위 값을 읽기 쉽도록 만원 단위로 변환합니다.
    values = [value / 10000 for value in facts["by_category"].values()]
    # 독립적인 Figure와 Axes 객체를 생성합니다.
    figure, axes = plt.subplots(figsize=(10, 5.5))
    # 카테고리별 막대그래프를 그립니다.
    bars = axes.bar(categories, values)
    # 제목에 분석 대상 월을 포함합니다.
    axes.set_title(f"{facts['month']} 카테고리별 매출")
    # 세로축의 단위를 명확하게 표시합니다.
    axes.set_ylabel("매출(만원)")
    # 가로축이 카테고리임을 표시합니다.
    axes.set_xlabel("카테고리")
    # 긴 카테고리명이 겹치지 않도록 30도 회전합니다.
    plt.xticks(rotation=30, ha="right")
    # 각 막대 위에 정확한 만원 단위 값을 표시합니다.
    for bar, value in zip(bars, values):
        axes.text(
            bar.get_x() + bar.get_width() / 2,
            value,
            f"{value:,.0f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    # 제목과 축 라벨이 그림 밖으로 잘리지 않도록 배치를 조정합니다.
    plt.tight_layout()
    # 파일명이 없으면 분석 월을 포함한 표준 파일명을 만듭니다.
    chart_name = filename or f"chart_{facts['month']}.png"
    # 최종 저장 경로를 구성합니다.
    chart_path = REPORTS_DIR / chart_name
    # 화면 표시 대신 PNG 파일로 저장합니다.
    figure.savefig(chart_path, dpi=120)
    # 반복 실행 시 메모리가 쌓이지 않도록 Figure를 닫습니다.
    plt.close(figure)
    # 생성된 파일 경로를 반환합니다.
    return chart_path


def add_chart_to_report(report_body: str, chart_path: Path) -> str:
    """마크다운 보고서 본문 위에 차트 이미지 링크를 추가합니다."""
    # 보고서와 차트가 같은 reports 폴더에 있으므로 파일명만 상대경로로 사용합니다.
    image_markdown = f"![카테고리별 매출 차트]({chart_path.name})"
    # 차트 뒤에 기존 보고서 본문이 이어지도록 결합합니다.
    return f"{image_markdown}\n\n{report_body.strip()}"
