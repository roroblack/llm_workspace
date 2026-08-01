#!/usr/bin/env bash

# 명령 실행 중 오류가 발생하면 즉시 스크립트를 종료합니다.
set -e

# 현재 스크립트가 위치한 프로젝트 루트 디렉터리로 이동합니다.
cd "$(dirname "$0")"

# .env 파일이 있으면 환경변수를 현재 셸에 로드합니다.
if [ -f ".env" ]; then
  set -a
  source .env
  set +a
fi

# HOST가 없으면 외부 접속을 받을 수 있도록 0.0.0.0을 사용합니다.
HOST="${HOST:-0.0.0.0}"

# PORT가 없으면 8000번 포트를 사용합니다.
PORT="${PORT:-8000}"

# GPU 모델을 한 번만 메모리에 적재하도록 단일 worker로 실행합니다.
exec uvicorn app.main:app --host "${HOST}" --port "${PORT}" --workers 1
