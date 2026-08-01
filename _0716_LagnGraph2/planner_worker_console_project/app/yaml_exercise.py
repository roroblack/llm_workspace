# -*- coding: utf-8 -*-
"""실습문제 2: 역할 프롬프트를 YAML 파일로 외부화합니다."""

# YAML 파일을 안전하게 읽기 위해 yaml 모듈을 가져옵니다.
import yaml
# provider별 모델과 데이터 경로를 가져옵니다.
from app.common import DATA, get_chat
# 기존 스키마, 취합, 작업 실행 함수를 재사용합니다.
from app.role_agent import Plan, combine_report
# Reviewer 함수도 재사용하되 YAML 프롬프트를 전달합니다.
from app.reviewer_exercise import review

def load_prompts() -> dict[str, str]:
    """data/role_prompts.yaml의 역할별 프롬프트를 읽습니다."""
    # YAML 파일 경로를 구성합니다.
    prompt_path = DATA / "role_prompts.yaml"
    # UTF-8 텍스트 모드로 YAML 파일을 엽니다.
    with prompt_path.open(mode="r", encoding="utf-8") as file:
        # 임의 객체 생성을 막는 safe_load로 딕셔너리를 읽습니다.
        loaded = yaml.safe_load(file)
    # 필수 역할 키가 모두 있는지 검사합니다.
    required = {"planner", "worker", "reviewer"}
    # 누락 키의 집합을 계산합니다.
    missing = required - set(loaded or {})
    # 하나라도 빠졌으면 설정 오류를 발생시킵니다.
    if missing:
        raise ValueError(f"YAML에 역할 프롬프트가 누락되었습니다: {sorted(missing)}")
    # 타입 검사기가 값을 문자열로 인식하도록 새 딕셔너리로 변환합니다.
    return {key: str(value) for key, value in loaded.items()}

def run_yaml_campaign(provider: str, brief_text: str) -> str:
    """YAML에서 읽은 프롬프트로 계획, 실행, 검토를 수행합니다."""
    # 메시지 클래스를 실제 LLM 호출 시점에만 가져옵니다.
    from langchain_core.messages import HumanMessage, SystemMessage
    # 실행할 때마다 YAML을 다시 읽어 파일 수정 내용이 즉시 반영되게 합니다.
    prompts = load_prompts()
    # 역할별로 필요한 세 모델 객체를 생성합니다.
    llm_plan = get_chat(provider=provider, temperature=0.0)
    llm_work = get_chat(provider=provider, temperature=0.5)
    llm_review = get_chat(provider=provider, temperature=0.0)
    # Planner 출력을 Plan 스키마로 강제합니다.
    planner = llm_plan.with_structured_output(Plan)
    # YAML의 planner 프롬프트로 하위 작업을 생성합니다.
    plan_result = planner.invoke([SystemMessage(prompts["planner"]), HumanMessage(f"[캠페인 브리프]\n{brief_text}")])
    # Worker 결과를 저장할 리스트를 준비합니다.
    outputs: list[tuple[str, str]] = []
    # 생성된 각 하위 작업을 순회합니다.
    for subtask in plan_result.subtasks:
        # YAML의 worker 프롬프트로 한 작업을 실행합니다.
        result = llm_work.invoke([
            SystemMessage(prompts["worker"]),
            HumanMessage(f"[브리프]\n{brief_text}\n\n[작업]\n{subtask}"),
        ])
        # 작업명과 결과 본문을 튜플로 저장합니다.
        outputs.append((subtask, str(result.content)))
    # Worker 결과를 실행안으로 취합합니다.
    report = combine_report(brief_text, outputs)
    # YAML의 reviewer 프롬프트로 전체 실행안을 검토합니다.
    opinion = review(llm_review, report, prompts["reviewer"])
    # 실행안과 검토 의견을 합쳐 반환합니다.
    return report + f"\n## 검토 의견\n{opinion}\n"
