# -*- coding: utf-8 -*-
"""config.yaml 로드와 구조적 로깅을 담당하는 운영 공통 모듈입니다."""

# 파이썬 표준 로깅 기능을 사용하기 위해 logging 모듈을 가져옵니다.
import logging
# YAML 설정 파일을 읽기 위해 PyYAML의 yaml 모듈을 가져옵니다.
import yaml
# 공통 모듈에 정의된 프로젝트 루트와 데이터 경로를 가져옵니다.
from common import DATA, ROOT


def load_config() -> dict:
    """data/config.yaml을 읽고 누락된 30강 기본 설정을 안전하게 보완합니다."""
    # data 폴더 안의 config.yaml 경로를 구성합니다.
    config_path = DATA / "config.yaml"
    # UTF-8 인코딩으로 YAML 파일을 읽기 모드로 엽니다.
    with config_path.open("r", encoding="utf-8") as file:
        # 안전한 YAML 파서를 사용해 내용을 파이썬 딕셔너리로 변환합니다.
        config = yaml.safe_load(file) or {}
    # app 설정 그룹이 없으면 빈 딕셔너리를 생성합니다.
    config.setdefault("app", {})
    # 앱 이름이 없으면 30강 통합 에이전트 기본 이름을 설정합니다.
    config["app"].setdefault("name", "Final CS Agent")
    # 앱 버전이 없으면 교육용 기본 버전을 설정합니다.
    config["app"].setdefault("version", "1.0.0")
    # llm 설정 그룹이 없으면 빈 딕셔너리를 생성합니다.
    config.setdefault("llm", {})
    # temperature가 없으면 사실 기반 상담에 적합한 0.0을 사용합니다.
    config["llm"].setdefault("temperature", 0.0)
    # 최대 재시도 횟수가 없으면 3회를 사용합니다.
    config["llm"].setdefault("max_retries", 3)
    # rag 설정 그룹이 없으면 빈 딕셔너리를 생성합니다.
    config.setdefault("rag", {})
    # 문서 청크 크기가 없으면 700자를 기본값으로 사용합니다.
    config["rag"].setdefault("chunk_size", 700)
    # 청크 중첩 크기가 없으면 문맥 보존을 위해 100자를 사용합니다.
    config["rag"].setdefault("chunk_overlap", 100)
    # 검색 결과 개수가 없으면 상위 4개 문서를 사용합니다.
    config["rag"].setdefault("top_k", 4)
    # logging 설정 그룹이 없으면 빈 딕셔너리를 생성합니다.
    config.setdefault("logging", {})
    # 로그 레벨이 없으면 일반 운영 정보가 보이는 INFO를 사용합니다.
    config["logging"].setdefault("level", "INFO")
    # 로그 파일 경로가 없으면 프로젝트 logs 폴더의 agent.log를 사용합니다.
    config["logging"].setdefault("file", "logs/agent.log")
    # 보완된 최종 설정 딕셔너리를 호출한 곳에 반환합니다.
    return config


def setup_logging(config: dict) -> logging.Logger:
    """설정값을 이용해 콘솔과 파일에 동시에 기록되는 로거를 생성합니다."""
    # 문자열 로그 레벨을 logging 상수로 변환하고 잘못된 값이면 INFO를 사용합니다.
    level = getattr(logging, str(config["logging"]["level"]).upper(), logging.INFO)
    # 설정에 지정된 상대 경로를 프로젝트 루트 기준 절대 경로로 변환합니다.
    log_path = ROOT / str(config["logging"]["file"])
    # 로그 파일의 상위 폴더가 없으면 자동 생성합니다.
    log_path.parent.mkdir(parents=True, exist_ok=True)
    # final_cs_agent라는 이름의 전용 로거를 가져옵니다.
    logger = logging.getLogger("final_cs_agent")
    # 로거가 처리할 최소 심각도 수준을 설정합니다.
    logger.setLevel(level)
    # 메뉴를 반복 실행할 때 동일 핸들러가 중복 등록되지 않도록 기존 핸들러를 제거합니다.
    logger.handlers.clear()
    # 로그 시각, 수준, 모듈 이름, 메시지를 포함하는 출력 형식을 정의합니다.
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    # 터미널에 로그를 출력하는 스트림 핸들러를 생성합니다.
    console_handler = logging.StreamHandler()
    # 콘솔 핸들러에 앞에서 만든 출력 형식을 적용합니다.
    console_handler.setFormatter(formatter)
    # UTF-8 로그 파일에 기록하는 파일 핸들러를 생성합니다.
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    # 파일 핸들러에도 동일한 출력 형식을 적용합니다.
    file_handler.setFormatter(formatter)
    # 완성된 콘솔 핸들러를 로거에 연결합니다.
    logger.addHandler(console_handler)
    # 완성된 파일 핸들러를 로거에 연결합니다.
    logger.addHandler(file_handler)
    # 다른 루트 로거로 메시지가 중복 전달되지 않도록 전파를 막습니다.
    logger.propagate = False
    # 설정이 완료된 로거 객체를 반환합니다.
    return logger
