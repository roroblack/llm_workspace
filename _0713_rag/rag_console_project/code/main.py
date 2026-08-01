# 콘솔 앱의 시작점이며 숫자 메뉴를 반복 실행합니다.
from features.menu_actions import (
    run_chunk_tuning,
    run_chunking,
    run_keyword_search,
    run_llm_rag,
    run_path_check,
    run_pdf_load,
    run_torch_search,
    run_various_loaders,
)


def print_menu() -> None:
    """사용자가 실행할 수 있는 실습 기능만 메뉴로 출력합니다."""
    # 이전 실행 결과와 새 메뉴를 시각적으로 구분하기 위해 빈 줄과 구분선을 출력합니다.
    print("\n" + "=" * 64)
    # 콘솔 프로그램의 제목을 출력합니다.
    print("RAG 문서 로드·청킹·검색 콘솔 실습")
    # 제목 아래쪽 구분선을 출력합니다.
    print("=" * 64)
    # 아래 메뉴는 HTML 설명을 보여 주지 않고 실제 실행 기능만 제공합니다.
    print("1. 공통 경로 및 실습 파일 확인")
    print("2. PDF 페이지 단위 로드")
    print("3. PDF 청킹 및 metadata 확인")
    print("4. 청크 키워드 검색")
    print("5. chunk_size / chunk_overlap 비교")
    print("6. CSV · TXT · Markdown 로더 확인")
    print("7. PyTorch 로컬 벡터 검색")
    print("8. OpenAI API 근거 기반 답변")
    print("9. Gemini API 근거 기반 답변")
    print("0. 프로그램 종료")


def main() -> None:
    """메뉴 번호를 입력받아 해당 함수를 호출하고 오류를 사용자에게 안내합니다."""
    # 메뉴 문자열과 실행 함수를 딕셔너리로 연결하여 긴 조건문을 줄입니다.
    actions = {
        "1": run_path_check,
        "2": run_pdf_load,
        "3": run_chunking,
        "4": run_keyword_search,
        "5": run_chunk_tuning,
        "6": run_various_loaders,
        "7": run_torch_search,
        "8": lambda: run_llm_rag("openai"),
        "9": lambda: run_llm_rag("gemini"),
    }
    # 사용자가 종료 메뉴를 선택할 때까지 메뉴 입력을 반복합니다.
    while True:
        # 현재 선택 가능한 메뉴를 출력합니다.
        print_menu()
        # 사용자 입력 앞뒤 공백을 제거하여 메뉴 번호를 얻습니다.
        choice = input("메뉴 번호를 선택하세요: ").strip()
        # 0번을 선택하면 반복문을 종료합니다.
        if choice == "0":
            # 프로그램 종료 메시지를 출력합니다.
            print("프로그램을 종료합니다.")
            # while 반복문을 빠져나갑니다.
            break
        # 입력한 번호와 연결된 실행 함수를 찾습니다.
        action = actions.get(choice)
        # 등록되지 않은 메뉴 번호이면 안내 후 다시 입력받습니다.
        if action is None:
            print("0~9 사이의 올바른 메뉴 번호를 입력하세요.")
            continue
        try:
            # 선택한 기능을 실행합니다.
            action()
        except (FileNotFoundError, ValueError, SystemExit) as error:
            # 파일 누락, 잘못된 입력, API 키 누락처럼 예상 가능한 오류를 출력합니다.
            print(f"\n[실행 오류] {error}")
        except Exception as error:
            # 그 밖의 예외가 발생해도 앱 전체가 종료되지 않도록 오류 정보를 출력합니다.
            print(f"\n[예상하지 못한 오류] {type(error).__name__}: {error}")


# 이 파일을 직접 실행한 경우에만 main 함수를 호출합니다.
if __name__ == "__main__":
    # 콘솔 메뉴 프로그램을 시작합니다.
    main()
