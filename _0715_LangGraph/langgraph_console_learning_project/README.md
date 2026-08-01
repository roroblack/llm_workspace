# LangGraph 콘솔 학습 프로젝트

이 프로젝트는 LangGraph의 핵심 개념을 PyCharm 콘솔 메뉴에서 직접 실행하며 확인하기 위한 실습 프로젝트입니다.

## 실행 메뉴

1. State, Node, Edge 기본 선형 그래프
2. add_conditional_edges 조건부 분기
3. 반복 그래프와 종료 조건
4. Reducer를 이용한 상태 누적
5. MessagesState 메시지 누적
6. InMemorySaver와 thread_id 체크포인트
7. 노드 예외 처리와 fallback
8. Mermaid 그래프 구조 출력

## 프로젝트 구조

```text
langgraph_console_learning_project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── basic_graph.py
│   ├── conditional_graph.py
│   ├── loop_graph.py
│   ├── reducer_graph.py
│   ├── messages_graph.py
│   ├── checkpoint_graph.py
│   ├── error_graph.py
│   └── utils.py
├── tests/
│   └── test_graphs.py
├── requirements.txt
├── .gitignore
└── README.md
```

## 권장 환경

- Python 3.11
- PyCharm
- Windows 11

## 설치

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

## 실행

프로젝트 루트에서 실행합니다.

```bash
python -m app.main
```

PyCharm에서는 `app/main.py`를 실행해도 됩니다. 실행 구성의 Working directory는 프로젝트 루트로 지정합니다.

## 테스트

```bash
pytest -q
```

## 특징

- OpenAI 또는 Gemini API 키 없이 실행됩니다.
- 모든 예제는 작은 독립 모듈로 분리했습니다.
- 각 코드 구문에 상세한 한국어 설명 주석을 작성했습니다.
- 이후 Node 내부를 LLM, Vector DB, MySQL, MCP 호출로 교체할 수 있습니다.
