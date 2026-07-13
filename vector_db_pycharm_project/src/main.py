"""PyCharm에서 하나의 메뉴로 15강 벡터DB 실습 파일들을 실행합니다."""  # 이 파일은 프로젝트 전체 실행용 메뉴입니다.

from importlib import import_module  # 파일명을 문자열로 선택해 모듈을 동적으로 불러오기 위해 사용합니다.
from typing import Callable, Dict  # 메뉴 함수 타입을 명확하게 표시하기 위해 사용합니다.

MENU: Dict[str, tuple[str, str]] = {  # 사용자가 선택할 메뉴 번호와 모듈 정보를 저장합니다.
    "1": ("01. 대량 검색과 인덱스 저장 개념", "01_numpy_limit_demo"),  # 1번 메뉴는 NumPy 한계 설명입니다.
    "2": ("02. 벡터DB의 역할", "02_vector_db_role"),  # 2번 메뉴는 벡터DB 역할 설명입니다.
    "3": ("03. FAISS vs Chroma", "03_faiss_vs_chroma"),  # 3번 메뉴는 FAISS/Chroma 비교입니다.
    "4": ("04. FAISS 인덱스 생성/저장", "04_build_index"),  # 4번 메뉴는 FAISS 인덱스 빌드입니다.
    "5": ("05. 저장된 FAISS 인덱스 서비스 검색", "05_service_search"),  # 5번 메뉴는 FAISS 검색 서비스입니다.
    "6": ("06. 저장/재로드/점수 검색", "06_save_reload_score"),  # 6번 메뉴는 저장과 점수 검색입니다.
    "7": ("07. Chroma 메타데이터 필터 검색", "07_chroma_filter_search"),  # 7번 메뉴는 Chroma 필터 검색입니다.
    "8": ("08. FAISS 증분 업데이트", "08_incremental_update"),  # 8번 메뉴는 증분 업데이트입니다.
    "9": ("09. 정리 체크리스트", "09_checklist_summary"),  # 9번 메뉴는 체크리스트입니다.
    "10": ("10. 실습문제1 - FAISS 인덱스 생성/저장 (GenAI)", "10_build_index_genai"),  # 10번 메뉴는 실습문제1입니다.
    "11": ("11. 실습문제2 - load 후 검색 검증 (GenAI)", "11_service_genai"),  # 11번 메뉴는 실습문제2입니다.
    "12": ("12. 실습문제3 - 메타데이터 출력 (GenAI)", "12_print_metadata_genai"),  # 12번 메뉴는 실습문제3입니다.
    "13": ("13. 실습문제4 - 인덱스 증분 업데이트 (GenAI)", "13_incremental_update_genai"),  # 13번 메뉴는 실습문제4입니다.
    "14": ("14. 실습문제5 - 메타데이터 필터링 검색 (GenAI)", "14_filter_search_genai"),  # 14번 메뉴는 실습문제5입니다.
}  # 메뉴 딕셔너리 정의를 끝냅니다.


def print_menu() -> None:  # 콘솔에 메뉴를 출력하는 함수입니다.
    print("\n===  Vector DB PyCharm 실습 프로젝트 ===")  # 프로젝트 제목을 출력합니다.
    for key, (title, _) in MENU.items():  # 메뉴 번호와 제목을 순서대로 순회합니다.
        print(f"{key}. {title}")  # 번호와 제목을 한 줄로 출력합니다.
    print("0. 종료")  # 종료 메뉴를 출력합니다.


def run_module(module_name: str) -> None:  # 선택된 실습 모듈을 실행하는 함수입니다.
    module = import_module(module_name)  # src 폴더가 실행 경로일 때 모듈명을 이용해 파일을 불러옵니다.
    main_func: Callable[[], None] = getattr(module, "main")  # 모듈에서 main 함수를 가져옵니다.
    main_func()  # 가져온 main 함수를 실행합니다.


def main() -> None:  # 전체 메뉴 프로그램의 시작 함수입니다.
    while True:  # 사용자가 종료를 선택할 때까지 메뉴를 반복합니다.
        print_menu()  # 현재 실행 가능한 메뉴를 출력합니다.
        choice = input("실행할 번호를 입력하세요: ").strip()  # 사용자 입력을 받아 앞뒤 공백을 제거합니다.
        if choice == "0":  # 사용자가 종료를 선택했는지 확인합니다.
            print("프로그램을 종료합니다.")  # 종료 메시지를 출력합니다.
            break  # 반복문을 종료합니다.
        if choice not in MENU:  # 존재하지 않는 메뉴 번호인지 확인합니다.
            print("잘못된 번호입니다. 다시 입력하세요.")  # 잘못된 입력 안내를 출력합니다.
            continue  # 메뉴를 다시 보여 주기 위해 반복문 처음으로 돌아갑니다.
        title, module_name = MENU[choice]  # 선택된 메뉴의 제목과 모듈명을 가져옵니다.
        print(f"\n--- 실행: {title} ---")  # 실행할 예제 제목을 출력합니다.
        try:  # 예제 실행 중 오류가 발생해도 메뉴 프로그램이 바로 종료되지 않게 합니다.
            run_module(module_name)  # 선택된 모듈의 main 함수를 실행합니다.
        except Exception as exc:  # 모든 예외를 잡아 사용자에게 원인을 보여 줍니다.
            print(f"실행 중 오류가 발생했습니다: {exc}")  # 오류 메시지를 출력합니다.


if __name__ == "__main__":  # 이 파일을 직접 실행했는지 확인합니다.
    main()  # 메뉴 프로그램을 시작합니다.
