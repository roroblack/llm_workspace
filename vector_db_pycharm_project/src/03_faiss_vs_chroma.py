"""03. FAISS와 Chroma의 차이를 설명합니다."""  # 이 파일은 두 벡터스토어 선택 기준을 출력합니다.


def main() -> None:  # PyCharm에서 직접 실행 가능한 메인 함수입니다.
    print("03. FAISS vs Chroma")  # 현재 예제 제목을 출력합니다.
    print("FAISS: 가볍고 빠른 벡터 검색 라이브러리입니다.")  # FAISS의 기본 특징을 출력합니다.
    print("FAISS: save_local/load_local로 파일 저장과 재로드가 명확합니다.")  # FAISS 영속화 방식을 설명합니다.
    print("FAISS: 복잡한 메타데이터 필터가 필요 없는 대부분의 RAG 실습에 적합합니다.")  # FAISS 추천 상황을 설명합니다.
    print("Chroma: 메타데이터 필터와 컬렉션 관리가 편한 임베디드 벡터DB입니다.")  # Chroma의 기본 특징을 출력합니다.
    print("Chroma: filter={\"source\": \"멤버십정책.txt\"}처럼 특정 문서만 검색할 때 적합합니다.")  # Chroma 필터 예시를 설명합니다.
    print("FAISS 점수는 거리(distance)이므로 일반적으로 작을수록 더 가까운 결과입니다.")  # FAISS 점수 해석 주의점을 설명합니다.


if __name__ == "__main__":  # 직접 실행될 때만 아래 코드를 실행합니다.
    main()  # 메인 함수를 호출합니다.
