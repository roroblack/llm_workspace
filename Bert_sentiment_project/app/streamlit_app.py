"""Streamlit으로 문장을 입력받고 감성분석 결과를 출력하는 앱입니다.

영어 리뷰는 기존 BERT 모델(src 패키지)로, 한국어 리뷰는 새로 추가한
한국어 감성분석 모델(src_choi_yeonwoo 패키지)로 분석합니다.
"""

import sys
from pathlib import Path

import streamlit as st

# Streamlit을 프로젝트 루트 밖에서 실행해도 패키지를 찾을 수 있도록 프로젝트 루트를 Python 경로에 추가합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 프로젝트 루트 경로가 sys.path에 없으면 추가합니다.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.config import MODEL_DIR  # noqa: E402
from src.predict import SentimentPredictor  # noqa: E402
from src_choi_yeonwoo.config import MODEL_DIR as KO_MODEL_DIR  # noqa: E402
from src_choi_yeonwoo.predict import KoreanSentimentPredictor  # noqa: E402


@st.cache_resource
def load_predictor() -> SentimentPredictor:
    """영어 BERT 감성분석 모델을 한 번만 로드해 캐싱합니다."""
    # 저장된 모델 폴더가 있으면 해당 모델을 사용하고, 없으면 기본 BERT 분류 모델을 사용합니다.
    return SentimentPredictor(model_dir=MODEL_DIR)


@st.cache_resource
def load_korean_predictor() -> KoreanSentimentPredictor:
    """한국어 감성분석 모델을 한 번만 로드해 캐싱합니다."""
    # 직접 파인튜닝한 모델이 있으면 사용하고, 없으면 사전학습 NSMC 모델을 사용합니다.
    return KoreanSentimentPredictor(model_dir=KO_MODEL_DIR)


def render_result(result: dict) -> None:
    """예측 결과 딕셔너리를 화면에 공통 형식으로 출력합니다."""
    # 최종 분류 결과를 크게 출력합니다.
    st.subheader(f"분류 결과: {result['label']}")

    # 긍정 확률을 progress bar로 출력합니다.
    st.write(f"긍정 확률: {result['positive_probability']:.4f}")
    st.progress(result["positive_probability"])

    # 부정 확률을 progress bar로 출력합니다.
    st.write(f"부정 확률: {result['negative_probability']:.4f}")
    st.progress(result["negative_probability"])

    # 현재 어떤 모델 경로를 사용했는지 출력합니다.
    st.caption(f"사용 모델: {result['model_path']}")


def main() -> None:
    """Streamlit 화면을 구성하고 사용자 입력에 대한 예측 결과를 출력합니다."""
    # 브라우저 탭 제목과 화면 레이아웃을 설정합니다.
    st.set_page_config(page_title="BERT 감성분석", page_icon="🤖", layout="centered")

    # 앱의 큰 제목을 출력합니다.
    st.title("BERT 문장 감성분석")

    # 앱 사용 목적을 짧게 설명합니다.
    st.write("문장을 입력하면 분류 모델이 긍정 또는 부정 결과를 예측합니다.")

    # ── 영어 리뷰 감성분석 (기존 기능 유지) ──────────────────────────────
    st.header("🇺🇸 영어 리뷰 감성분석")

    # 학습된 영어 모델이 없는 경우 기본 사전 학습 모델이 사용될 수 있음을 안내합니다.
    if not MODEL_DIR.exists():
        st.warning("학습된 영어 모델 폴더가 없습니다. `python -m src.train` 으로 학습하면 더 정확한 결과를 볼 수 있습니다.")

    # 예측할 영어 문장을 입력받는 텍스트 영역을 만듭니다.
    text = st.text_area("분석할 문장 입력", value="This movie was wonderful and I loved it.", height=120, key="en_text")

    # 사용자가 버튼을 누르면 영어 예측을 실행합니다.
    if st.button("감성분석 실행", type="primary", key="en_button"):
        try:
            # 캐시된 영어 예측 객체를 불러옵니다.
            predictor = load_predictor()

            # 입력 문장에 대한 예측 결과를 계산해 화면에 출력합니다.
            render_result(predictor.predict(text))
        except Exception as error:
            # 예측 중 발생한 오류를 화면에 표시하여 원인을 빠르게 확인할 수 있게 합니다.
            st.error(f"예측 중 오류가 발생했습니다: {error}")

    # 영어/한국어 영역을 시각적으로 구분합니다.
    st.divider()

    # ── 한국어 리뷰 감성분석 (추가 기능) ────────────────────────────────
    st.header("🇰🇷 한국어 리뷰 감성분석")

    # 직접 파인튜닝한 한국어 모델이 없으면 사전학습 NSMC 모델을 사용함을 안내합니다.
    if not KO_MODEL_DIR.exists():
        st.info("직접 학습한 한국어 모델이 없어 사전학습 NSMC 모델(monologg/koelectra-base-finetuned-nsmc)을 사용합니다.")

    # 예측할 한국어 리뷰 문장을 input_text 변수로 입력받습니다.
    input_text = st.text_area("한국어 리뷰 문장", value="이 영화 정말 재미있어요. 강력 추천합니다.", height=120, key="ko_text")

    # 사용자가 '감성분석' 버튼을 누르면 한국어 예측을 실행합니다.
    if st.button("감성분석", type="primary", key="ko_button"):
        try:
            # 캐시된 한국어 예측 객체를 불러옵니다.
            korean_predictor = load_korean_predictor()

            # input_text 에 대한 예측 결과를 계산해 화면에 출력합니다.
            render_result(korean_predictor.predict(input_text))
        except Exception as error:
            # 예측 중 발생한 오류를 화면에 표시하여 원인을 빠르게 확인할 수 있게 합니다.
            st.error(f"예측 중 오류가 발생했습니다: {error}")


if __name__ == "__main__":
    # streamlit run app/streamlit_app.py로 실행할 때 main 함수를 호출합니다.
    main()
