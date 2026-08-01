"""
mock 백엔드에서 FastAPI 주요 API가 정상 작동하는지 검사합니다.
"""

# FastAPI 애플리케이션을 테스트하기 위한 TestClient를 가져옵니다.
from fastapi.testclient import TestClient

# 테스트 대상 FastAPI app 객체를 가져옵니다.
from app.main import app


# 실제 네트워크 포트 없이 API를 호출할 테스트 클라이언트를 생성합니다.
client = TestClient(app)


def test_health() -> None:
    """
    상태 확인 API가 200과 핵심 필드를 반환하는지 검사합니다.
    """

    # 상태 확인 API를 GET 방식으로 호출합니다.
    response = client.get("/api/system/health")

    # HTTP 상태가 성공인지 확인합니다.
    assert response.status_code == 200

    # 응답 JSON을 파이썬 딕셔너리로 변환합니다.
    data = response.json()

    # 서버 상태값이 ok인지 확인합니다.
    assert data["status"] == "ok"

    # 현재 백엔드 정보가 존재하는지 확인합니다.
    assert "inference_backend" in data


def test_generate_mock_answer() -> None:
    """
    단일 질문 추론 API가 구조화된 결과를 반환하는지 검사합니다.
    """

    # mock 기반 모델에 질문을 전달합니다.
    response = client.post(
        "/api/inference/generate",
        json={
            "model_kind": "base",
            "prompt": "파인튜닝 평가 방법을 설명하세요.",
            "max_new_tokens": 64,
            "do_sample": False,
            "temperature": 0.7,
            "top_p": 0.9,
        },
    )

    # 정상 응답인지 확인합니다.
    assert response.status_code == 200

    # 응답 JSON을 읽습니다.
    data = response.json()

    # 선택한 모델 종류가 유지되는지 확인합니다.
    assert data["model_kind"] == "base"

    # 답변이 빈 문자열이 아닌지 확인합니다.
    assert data["answer"]

    # 생성 속도가 0보다 큰지 확인합니다.
    assert data["tokens_per_second"] > 0


def test_run_evaluation() -> None:
    """
    평가 API가 테스트 데이터의 요약 결과를 반환하는지 검사합니다.
    """

    # Base 모델을 두 개 샘플로 평가합니다.
    response = client.post(
        "/api/evaluation/run",
        json={
            "model_kind": "base",
            "use_bertscore": False,
            "limit": 2,
        },
    )

    # 평가 API가 성공했는지 확인합니다.
    assert response.status_code == 200

    # 결과 JSON을 읽습니다.
    data = response.json()

    # 요청한 두 개의 샘플이 평가되었는지 확인합니다.
    assert data["summary"]["sample_count"] == 2

    # ROUGE-L 평가 지표가 포함되었는지 확인합니다.
    assert "rougeL_f1" in data["summary"]
