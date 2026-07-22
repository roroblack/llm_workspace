# -*- coding: utf-8 -*-
"""요약 보고서와 임원용 월간 매출 보고서를 생성·저장합니다."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Literal

import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.logging_config import setup_logging
from app.core.settings import DATA_DIR, REPORTS_DIR, get_settings
from app.services.llm_factory import create_chat_model

logger = setup_logging()
Provider = Literal["openai", "gemini"]


def _extract_text(response: object) -> str:
    """공급자별 LangChain 응답에서 일반 텍스트를 추출합니다."""
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))
        return "\n".join(parts).strip()
    return str(content).strip()


def _safe_filename(text: str, max_length: int = 70) -> str:
    """Windows와 POSIX에서 모두 안전한 파일명 조각을 만듭니다."""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", text.strip())
    cleaned = re.sub(r"\s+", "_", cleaned).strip("._")
    return (cleaned or "report")[:max_length]


def _save_markdown(prefix: str, title: str, body: str) -> Path:
    """UTF-8 마크다운 보고서를 reports 폴더에 저장합니다."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = REPORTS_DIR / f"{prefix}_{timestamp}_{_safe_filename(title)}.md"
    document = f"# {title}\n\n> 생성일: {datetime.now().isoformat(timespec='seconds')}\n\n{body.strip()}\n"
    path.write_text(document, encoding="utf-8")
    logger.info("보고서 파일 생성: path=%s", path)
    return path

def _fallback_summary(text: str) -> str:
    """LLM을 사용할 수 없을 때 원문 문장만 이용해 안전한 요약을 만듭니다."""
    sentences = [item.strip() for item in re.split(r"(?<=[.!?。다])\s+|\n+", text) if item.strip()]
    selected = sentences[:5] if sentences else [text.strip()]
    bullets = "\n".join(f"- {sentence}" for sentence in selected)
    return f"## 핵심 요약\n{selected[0]}\n\n## 주요 내용\n{bullets}"


def generate_summary_report(title: str, text: str, provider: Provider) -> dict[str, object]:
    """긴 텍스트를 map-reduce 방식으로 요약하고 마크다운 보고서로 저장합니다."""
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max(settings.rag_chunk_size * 3, 1200),
        chunk_overlap=settings.rag_chunk_overlap,
    )
    chunks = splitter.split_text(text.strip())
    used_fallback = False
    try:
        llm = create_chat_model(provider)
        partials: list[str] = []
        for chunk in chunks:
            response = llm.invoke(
                "다음 내용을 사실을 추가하지 말고 한국어로 간결하게 요약하세요. "
                "핵심 사실과 결정·후속 조치를 보존하세요.\n\n" + chunk
            )
            partials.append(_extract_text(response))
        joined = "\n".join(f"- {partial}" for partial in partials)
        response = llm.invoke(
            "다음 부분 요약들을 중복 없이 통합해 한국어 보고서를 작성하세요. "
            "반드시 '## 핵심 요약', '## 주요 내용', '## 후속 조치' 섹션을 포함하고 "
            "원문에 없는 사실을 만들지 마세요.\n\n" + joined
        )
        body = _extract_text(response)
        if not body:
            raise ValueError("LLM이 빈 요약을 반환했습니다.")
    except Exception as exc:
        used_fallback = True
        logger.warning("요약 LLM 호출 실패, 원문 기반 템플릿 사용: %s", exc)
        body = _fallback_summary(text)
        body += f"\n\n> LLM 호출 실패로 원문 추출 요약을 사용했습니다: {type(exc).__name__}"

    path = _save_markdown("summary", title, body)
    return {
        "title": title,
        "content": body,
        "report_path": path.name,
        "download_url": f"/api/v1/reports/{path.name}",
        "used_fallback": used_fallback,
        "facts": None,
    }


def _read_sales() -> pd.DataFrame:
    """monthly_sales.csv를 읽고 매출 계산용 스키마를 검증합니다."""
    path = DATA_DIR / "monthly_sales.csv"
    if not path.exists():
        raise FileNotFoundError(f"매출 파일을 찾지 못했습니다: {path}")
    frame = pd.read_csv(path, encoding="utf-8-sig")
    required = {"month", "total"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"매출 필수 컬럼이 누락되었습니다: {missing}")
    frame = frame.sort_values("month").reset_index(drop=True)
    numeric_columns = [column for column in frame.columns if column != "month"]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame.empty or frame[numeric_columns].isna().any().any():
        raise ValueError("매출 데이터가 비어 있거나 숫자가 아닌 값이 있습니다.")
    return frame


def _sales_facts(month: str | None) -> dict[str, object]:
    """대상 월과 전월을 비교한 확정 수치를 계산합니다."""
    frame = _read_sales()
    if month:
        matches = frame.index[frame["month"].astype(str) == month].tolist()
        if not matches:
            available = ", ".join(frame["month"].astype(str).tolist())
            raise ValueError(f"'{month}' 데이터가 없습니다. 사용 가능한 달: {available}")
        index = int(matches[0])
    else:
        index = len(frame) - 1
    if index <= 0:
        raise ValueError("전월 데이터가 없어 증감률을 계산할 수 없습니다.")

    current = frame.iloc[index]
    previous = frame.iloc[index - 1]
    if float(previous["total"]) == 0:
        raise ValueError("전월 총매출이 0이라 증감률을 계산할 수 없습니다.")
    category_columns = [column for column in frame.columns if column not in {"month", "total"}]
    if len(category_columns) < 2:
        raise ValueError("카테고리 매출 컬럼이 최소 2개 필요합니다.")
    categories = current[category_columns].sort_values(ascending=False)
    growth = (float(current["total"]) - float(previous["total"])) / float(previous["total"]) * 100
    return {
        "month": str(current["month"]),
        "prev_month": str(previous["month"]),
        "total": int(current["total"]),
        "prev_total": int(previous["total"]),
        "growth_pct": round(growth, 1),
        "top_category": str(categories.index[0]),
        "top_value": int(categories.iloc[0]),
        "second_category": str(categories.index[1]),
        "second_value": int(categories.iloc[1]),
        "by_category": {str(key): int(value) for key, value in categories.items()},
    }


def _format_facts(facts: dict[str, object]) -> str:
    categories = facts["by_category"]
    assert isinstance(categories, dict)
    category_lines = "\n".join(f"- {name}: {int(value):,}원" for name, value in categories.items())
    return (
        f"- 대상 월: {facts['month']}\n- 전월: {facts['prev_month']}\n"
        f"- 총매출: {int(facts['total']):,}원\n- 전월 총매출: {int(facts['prev_total']):,}원\n"
        f"- 전월 대비 증감률: {float(facts['growth_pct']):+.1f}%\n"
        f"- 최대 카테고리: {facts['top_category']} {int(facts['top_value']):,}원\n"
        f"- 2위 카테고리: {facts['second_category']} {int(facts['second_value']):,}원\n"
        f"[카테고리별 매출]\n{category_lines}"
    )


def _fallback_sales_report(facts: dict[str, object]) -> str:
    growth = float(facts["growth_pct"])
    trend = "증가" if growth > 0 else "감소" if growth < 0 else "보합"
    return (
        "## 총평\n"
        f"{facts['month']} 총매출은 {int(facts['total']):,}원으로, {facts['prev_month']}의 "
        f"{int(facts['prev_total']):,}원 대비 {abs(growth):.1f}% {trend}했습니다.\n\n"
        "## 카테고리 분석\n"
        f"매출 1위는 {facts['top_category']}({int(facts['top_value']):,}원), "
        f"2위는 {facts['second_category']}({int(facts['second_value']):,}원)입니다.\n\n"
        "## 다음 달 제언\n"
        "상위 카테고리의 판매 흐름을 유지하고 하위 카테고리의 상품 구성과 프로모션 반응을 점검합니다."
    )


def generate_sales_report(month: str | None, provider: Provider) -> dict[str, object]:
    """확정 수치를 근거로 임원용 월간 매출 보고서를 만듭니다."""
    facts = _sales_facts(month)
    used_fallback = False
    try:
        llm = create_chat_model(provider)
        response = llm.invoke(
            "너는 온라인 쇼핑몰 경영기획 담당자다. 아래 확정 수치만 근거로 임원용 한국어 "
            "월간 매출 보고서를 마크다운으로 작성하라. 숫자를 변경·재계산·추측하지 말고 "
            "반드시 '## 총평', '## 카테고리 분석', '## 다음 달 제언'을 포함하라.\n\n"
            + _format_facts(facts)
        )
        body = _extract_text(response)
        if not body:
            raise ValueError("LLM이 빈 보고서를 반환했습니다.")
    except Exception as exc:
        used_fallback = True
        logger.warning("매출 보고서 LLM 호출 실패, 확정 수치 템플릿 사용: %s", exc)
        body = _fallback_sales_report(facts)
        body += f"\n\n> LLM 호출 실패로 기본 템플릿을 사용했습니다: {type(exc).__name__}"

    title = f"{facts['month']} 임원용 월간 매출 보고서"
    path = _save_markdown("executive_sales", title, body)
    return {
        "title": title,
        "content": body,
        "report_path": path.name,
        "download_url": f"/api/v1/reports/{path.name}",
        "used_fallback": used_fallback,
        "facts": facts,
    }


def resolve_report_path(filename: str) -> Path:
    """reports 폴더 내부의 안전한 다운로드 경로만 반환합니다."""
    if Path(filename).name != filename or not filename.endswith(".md"):
        raise ValueError("잘못된 보고서 파일명입니다.")
    path = (REPORTS_DIR / filename).resolve()
    if path.parent != REPORTS_DIR.resolve():
        raise ValueError("잘못된 보고서 경로입니다.")
    return path
