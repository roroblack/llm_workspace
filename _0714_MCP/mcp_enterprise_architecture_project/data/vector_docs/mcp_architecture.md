# MCP 실무 아키텍처

사용자 요청은 FastAPI로 전달됩니다.
OpenAI 모델은 필요한 Tool을 판단합니다.
MCP Client는 표준 프로토콜로 MCP Server와 연결합니다.
MCP Server는 File, DB, GitHub, Slack, Browser, Calendar, Email, Vector Search, Python Tool을 제공합니다.
각 Tool은 실제 외부 시스템 어댑터를 호출합니다.
