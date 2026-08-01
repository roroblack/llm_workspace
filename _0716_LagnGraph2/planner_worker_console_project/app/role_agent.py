# -*- coding: utf-8 -*-
"""Planner, Worker, 오케스트레이터의 핵심 실행 코드입니다."""

# 표 형식 CSV 데이터를 읽기 위해 pandas를 가져옵니다.
import pandas as pd
# 구조화 출력 스키마를 정의하기 위해 Pydantic 구성요소를 가져옵니다.
from pydantic import BaseModel, Field
# 공통 데이터 경로와 채팅 모델 생성 함수를 가져옵니다.
from app.common import DATA, get_chat

# Planner가 계획만 수행하도록 역할과 출력 범위를 고정합니다.
PLANNER_SYSTEM = (
    "너는 마케팅 캠페인 기획 설계자(Planner)다. "
    "브리프를 보고 실행에 필요한 하위 작업을 3~4개로 쪼개라. "
    "작업은 겹치지 않는 한 문장 명령형으로 작성하고 직접 실행하지 마라."
)
# Worker가 한 번에 하나의 작업만 수행하도록 역할과 출력 범위를 고정합니다.
WORKER_SYSTEM = (
    "너는 마케팅 실무 작업자(Worker)다. "
    "브리프 맥락에서 지정된 하나의 작업만 구체적으로 수행하라. "
    "결과는 5줄 이내의 실무용 내용으로 작성하라."
)

class Plan(BaseModel):
    """Planner의 응답을 문자열 목록으로 고정하는 구조화 출력 스키마입니다."""
    # LLM이 3~4개의 하위 작업을 문자열 리스트에 채우도록 필드를 선언합니다.
    subtasks: list[str] = Field(description="캠페인 실행에 필요한 하위 작업 3~4개")

def load_campaign_table() -> pd.DataFrame:
    """marketing_brief.csv 전체를 DataFrame으로 읽습니다."""
    # 캠페인 CSV 파일의 전체 경로를 구성합니다.
    csv_path = DATA / "marketing_brief.csv"
    # 파일이 없으면 사용자가 원인을 바로 알 수 있도록 오류를 발생시킵니다.
    if not csv_path.exists():
        raise FileNotFoundError(f"캠페인 데이터가 없습니다: {csv_path}")
    # UTF-8 CSV를 DataFrame으로 읽어 반환합니다.
    return pd.read_csv(csv_path)

def list_campaigns() -> None:
    """선택 가능한 캠페인 목록을 콘솔에 출력합니다."""
    # 전체 캠페인 표를 읽습니다.
    table = load_campaign_table()
    # 각 행을 순서대로 반복합니다.
    for row in table.itertuples(index=False):
        # 캠페인 ID와 제목을 한 줄로 출력합니다.
        print(f"- {row.campaign_id}: {row.title}")

def load_brief_text(campaign_id: str = "CMP02") -> str:
    """캠페인 ID에 해당하는 행을 LLM 입력용 한 줄 텍스트로 변환합니다."""
    # 전체 캠페인 표를 읽습니다.
    table = load_campaign_table()
    # campaign_id가 일치하는 행만 필터링합니다.
    matched = table[table["campaign_id"] == campaign_id]
    # 일치하는 캠페인이 없으면 사용 가능한 ID를 포함한 오류를 발생시킵니다.
    if matched.empty:
        available = ", ".join(table["campaign_id"].astype(str).tolist())
        raise ValueError(f"캠페인 ID를 찾을 수 없습니다: {campaign_id} / 사용 가능: {available}")
    # 첫 번째 일치 행을 Series로 꺼냅니다.
    campaign = matched.iloc[0]
    # 각 컬럼을 설명형 한 줄 텍스트로 조합해 반환합니다.
    return (
        f"캠페인명: {campaign['title']} / 카테고리: {campaign['category']} / "
        f"타깃: {campaign['target']} / 예산: {int(campaign['budget']):,}원 / "
        f"핵심혜택: {campaign['key_offer']}"
    )

def plan(llm, brief_text: str, planner_prompt: str = PLANNER_SYSTEM) -> list[str]:
    """브리프를 구조화된 하위 작업 목록으로 분해합니다."""
    # 메시지 클래스를 실제 LLM 호출 시점에만 가져옵니다.
    from langchain_core.messages import HumanMessage, SystemMessage
    # 일반 채팅 모델을 Plan 스키마의 구조화 출력 모델로 감쌉니다.
    planner = llm.with_structured_output(Plan)
    # Planner 역할 지시와 캠페인 브리프를 모델에 전달합니다.
    result = planner.invoke([SystemMessage(planner_prompt), HumanMessage(f"[캠페인 브리프]\n{brief_text}")])
    # Pydantic 객체에서 하위 작업 문자열 리스트를 꺼내 반환합니다.
    return result.subtasks

def work(llm, brief_text: str, subtask: str, worker_prompt: str = WORKER_SYSTEM) -> str:
    """브리프 맥락에서 지정된 하위 작업 하나만 수행합니다."""
    # 메시지 클래스를 실제 LLM 호출 시점에만 가져옵니다.
    from langchain_core.messages import HumanMessage, SystemMessage
    # Worker 역할과 전체 맥락 및 단일 작업을 모델에 전달합니다.
    result = llm.invoke([
        SystemMessage(worker_prompt),
        HumanMessage(f"[캠페인 브리프]\n{brief_text}\n\n[수행할 작업]\n{subtask}"),
    ])
    # 모델 응답 객체의 본문을 문자열로 변환해 반환합니다.
    return str(result.content)

def combine_report(brief_text: str, outputs: list[tuple[str, str]]) -> str:
    """Worker 산출물을 Markdown 형식의 실행안으로 취합합니다."""
    # 문서 제목과 원본 브리프를 첫 번째 섹션으로 생성합니다.
    sections = [f"# 캠페인 실행안\n\n> {brief_text}\n"]
    # 작업명과 산출물을 순서 번호와 함께 반복합니다.
    for index, (task, output) in enumerate(outputs, start=1):
        # 각 작업을 별도의 Markdown 섹션으로 추가합니다.
        sections.append(f"## {index}. {task}\n{output}\n")
    # 섹션 사이에 줄바꿈을 넣어 하나의 문자열로 반환합니다.
    return "\n".join(sections)

def run_campaign(provider: str, brief_text: str) -> str:
    """선택 provider로 계획, 실행, 취합 전체 과정을 수행합니다."""
    # 계획은 일관성이 중요하므로 temperature를 0으로 설정합니다.
    llm_plan = get_chat(provider=provider, temperature=0.0)
    # 실행은 표현 다양성이 필요할 수 있으므로 temperature를 0.5로 설정합니다.
    llm_work = get_chat(provider=provider, temperature=0.5)
    # Planner로 하위 작업 목록을 생성합니다.
    subtasks = plan(llm_plan, brief_text)
    # 작업별 산출물을 저장할 빈 리스트를 준비합니다.
    outputs: list[tuple[str, str]] = []
    # Planner가 만든 작업을 하나씩 순회합니다.
    for index, subtask in enumerate(subtasks, start=1):
        # 현재 수행 중인 작업을 콘솔에 표시합니다.
        print(f"[{index}/{len(subtasks)}] Worker 수행: {subtask}")
        # 한 작업의 결과를 작업명과 함께 리스트에 저장합니다.
        outputs.append((subtask, work(llm_work, brief_text, subtask)))
    # 모든 산출물을 하나의 실행안으로 취합해 반환합니다.
    return combine_report(brief_text, outputs)
