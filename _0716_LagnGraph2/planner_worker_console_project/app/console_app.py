# -*- coding: utf-8 -*-
"""OpenAI와 Gemini를 선택해 각 실습을 실행하는 콘솔 메뉴입니다."""

# 예외 발생 시 상세 원인을 출력하기 위해 traceback을 가져옵니다.
import traceback
# 환경 상태 출력 함수를 가져옵니다.
from app.common import print_environment_status
# 기본 Planner/Worker 기능을 가져옵니다.
from app.role_agent import list_campaigns, load_brief_text, plan, run_campaign, work
# 재시도 실습 함수를 가져옵니다.
from app.retry_agent import run_campaign_robust
# Reviewer 실습문제 완성 함수를 가져옵니다.
from app.reviewer_exercise import run_campaign_with_review
# YAML 프롬프트 실습문제 완성 함수를 가져옵니다.
from app.yaml_exercise import run_yaml_campaign
# provider별 채팅 모델 생성을 위해 공통 함수를 가져옵니다.
from app.common import get_chat

def select_provider() -> str | None:
    """OpenAI 또는 Gemini를 선택하고 종료 요청이면 None을 반환합니다."""
    # 공급자 선택 메뉴를 출력합니다.
    print("\n[LLM 선택] 1. OpenAI  2. Gemini  0. 종료")
    # 사용자 입력의 앞뒤 공백을 제거합니다.
    choice = input("선택: " ).strip()
    # 메뉴 번호를 내부 provider 문자열로 변환합니다.
    providers = {"1": "openai", "2": "gemini"}
    # 0을 입력하면 상위 반복문을 종료하도록 None을 반환합니다.
    if choice == "0":
        return None
    # 존재하지 않는 번호이면 None과 구분되는 빈 문자열을 반환합니다.
    return providers.get(choice, "")

def select_campaign() -> str:
    """캠페인 목록을 보여주고 선택한 브리프 문자열을 반환합니다."""
    # 데이터에 들어 있는 캠페인 목록을 출력합니다.
    list_campaigns()
    # 기본값 CMP02를 안내하며 캠페인 ID를 입력받습니다.
    campaign_id = input("캠페인 ID(Enter=CMP02): " ).strip() or "CMP02"
    # 선택한 ID의 브리프를 문자열로 변환해 반환합니다.
    return load_brief_text(campaign_id)

def run_provider_menu(provider: str) -> None:
    """선택한 provider를 유지하면서 하위 실습 메뉴를 반복 실행합니다."""
    # 뒤로 가기를 선택할 때까지 하위 메뉴를 계속 표시합니다.
    while True:
        # HTML 요약 기능을 제외한 실행 확인 메뉴만 출력합니다.
        print(f"\n[{provider.upper()} 실습 메뉴]")
        print("1. 환경·데이터 설정 확인")
        print("2. Planner 작업 분해")
        print("3. Worker 단일 작업 실행")
        print("4. Planner → Worker → 취합 전체 실행")
        print("5. Worker 실패 재시도·스킵 실습")
        print("6. 실습문제 1: Reviewer 단계 추가")
        print("7. 실습문제 2: YAML 프롬프트 외부화")
        print("0. LLM 다시 선택")
        # 실행할 메뉴 번호를 입력받습니다.
        choice = input("선택: " ).strip()
        # 0이면 현재 provider의 하위 메뉴를 종료합니다.
        if choice == "0":
            return
        try:
            # 환경 및 데이터 경로 확인 메뉴를 처리합니다.
            if choice == "1":
                print_environment_status()
                list_campaigns()
            # Planner만 단독으로 실행합니다.
            elif choice == "2":
                brief = select_campaign()
                llm = get_chat(provider=provider, temperature=0.0)
                for index, subtask in enumerate(plan(llm, brief), start=1):
                    print(f"{index}. {subtask}")
            # Worker에 사용자가 직접 입력한 작업 하나를 전달합니다.
            elif choice == "3":
                brief = select_campaign()
                subtask = input("Worker가 수행할 한 작업: " ).strip() or "타깃 고객의 핵심 니즈를 분석하라"
                llm = get_chat(provider=provider, temperature=0.5)
                print(work(llm, brief, subtask))
            # 전체 기본 오케스트레이션을 실행합니다.
            elif choice == "4":
                print(run_campaign(provider, select_campaign()))
            # 두 번째 작업을 고의로 실패시켜 재시도와 부분 실패를 확인합니다.
            elif choice == "5":
                print(run_campaign_robust(provider, select_campaign(), fail_indices={2}))
            # Reviewer 추가 실습문제 완성 코드를 실행합니다.
            elif choice == "6":
                print(run_campaign_with_review(provider, select_campaign()))
            # YAML 프롬프트 외부화 실습문제 완성 코드를 실행합니다.
            elif choice == "7":
                print(run_yaml_campaign(provider, select_campaign()))
            # 정의되지 않은 메뉴 번호를 안내합니다.
            else:
                print("메뉴 번호를 다시 입력하세요.")
        except Exception as error:
            # 사용자가 수정할 수 있도록 오류 종류와 메시지를 출력합니다.
            print(f"[실행 오류] {type(error).__name__}: {error}")
            # 개발 단계에서 상세 호출 위치까지 확인할 수 있게 traceback을 출력합니다.
            traceback.print_exc()

def main() -> None:
    """프로그램 시작점에서 LLM 선택 메뉴를 반복 실행합니다."""
    # 프로그램의 목적을 한 번 출력합니다.
    print("Planner/Worker Role Agent 콘솔 실습 프로젝트")
    # 사용자가 종료할 때까지 공급자 선택을 반복합니다.
    while True:
        # OpenAI 또는 Gemini 선택 결과를 받습니다.
        provider = select_provider()
        # None은 명시적인 종료 요청입니다.
        if provider is None:
            print("프로그램을 종료합니다.")
            return
        # 빈 문자열은 잘못된 메뉴 번호입니다.
        if not provider:
            print("1, 2, 0 중에서 선택하세요.")
            continue
        # 선택한 공급자의 하위 실습 메뉴를 실행합니다.
        run_provider_menu(provider)

# 이 파일을 직접 실행했을 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
