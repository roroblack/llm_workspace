# 간단한 MCP 서버 PyCharm 프로젝트

이 프로젝트는 MCP 서버 구축의 핵심인 **Tool, Resource, Prompt**를 한 파일에서 실습하는 간단한 예제입니다.

## 1. 제공 기능

### Tool

| 이름 | 설명 |
|---|---|
| `hello` | 이름을 받아 인사말을 반환합니다. |
| `add` | 두 숫자를 더합니다. |
| `get_current_time` | 서버 컴퓨터의 현재 시간을 반환합니다. |

### Resource

| URI | 설명 |
|---|---|
| `manual://guide` | `data/manual.txt` 내용을 반환합니다. |
| `profile://{name}` | 입력한 이름으로 예제 프로필을 생성합니다. |

### Prompt

| 이름 | 설명 |
|---|---|
| `summarize_document` | 주제와 설명 방식을 받아 요약용 Prompt를 생성합니다. |

## 2. 프로젝트 구조

```text
simple_mcp_server_project/
├─ data/
│  └─ manual.txt
├─ __init__.py
├─ server.py
├─ requirements.txt
├─ .gitignore
└─ README.md
```

## 3. PyCharm 설정

1. 압축을 해제합니다.
2. PyCharm에서 `Open`을 선택합니다.
3. `simple_mcp_server_project` 폴더를 엽니다.
4. `File → Settings → Project → Python Interpreter`로 이동합니다.
5. Python 3.10 이상으로 새 가상환경을 생성합니다.

권장 버전은 Python 3.11입니다.

## 4. 패키지 설치

PyCharm Terminal에서 실행합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## 5. MCP 서버 실행

```bash
python server.py
```

stdio 서버는 웹 서버처럼 일반 화면을 제공하지 않습니다. MCP Client가 표준 입력과 표준 출력을 통해 연결하므로, 직접 실행했을 때 멈춘 것처럼 보이는 것이 정상입니다.

종료:

```text
Ctrl + C
```

## 6. MCP Inspector 테스트

Node.js가 설치되어 있다면 프로젝트 루트에서 실행합니다.

```bash
npx -y @modelcontextprotocol/inspector python server.py
```

Inspector에서 다음 순서로 확인합니다.

1. `Tools` 탭에서 `hello`, `add`, `get_current_time` 실행
2. `Resources` 탭에서 `manual://guide` 읽기
3. 동적 Resource `profile://홍길동` 확인
4. `Prompts` 탭에서 `summarize_document` 실행

## 7. Claude Desktop 연결 예시

Windows 설정 예시입니다.

```json
{
  "mcpServers": {
    "simple-mcp-server": {
      "command": "C:\\전체경로\\simple_mcp_server_project\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\전체경로\\simple_mcp_server_project\\server.py"
      ]
    }
  }
}
```

`전체경로`는 실제 프로젝트 경로로 변경합니다.

## 8. 학습 순서

1. `FastMCP` 객체 생성
2. `@mcp.tool()` 함수 등록
3. `@mcp.resource()` URI 등록
4. `@mcp.prompt()` Prompt 등록
5. `mcp.run(transport="stdio")` 실행

## 9. 주의 사항

stdio 서버에서는 일반 `print()`로 stdout에 로그를 남기면 MCP 통신 메시지가 손상될 수 있습니다.

디버깅 메시지는 stderr를 사용합니다.

```python
import sys

print("디버깅 메시지", file=sys.stderr)
```
