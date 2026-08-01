"""프로젝트개요와구조.txt 의 테스트 케이스를 전부 실제 호출해서 검증한다.

사용법:
    # 1) 다른 터미널에서 서버 실행
    uvicorn app.main:app
    # 2) 검증
    python scripts/verify_endpoints.py
    python scripts/verify_endpoints.py --out reports/verification.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:8000"

CLASSIFY_CASES = [
    ("기본 긍정", {
        "text": "The lecture was clear, well structured, and very helpful for "
                "understanding AI fundamentals."}),
    ("명확한 부정", {
        "text": "This service is extremely slow, unreliable, and the support team "
                "never responds."}),
    ("문맥 반전(sarcasm)", {
        "text": "I thought this course would be great, but it turned out to be a "
                "complete waste of time."}),
    ("약한 부정(경계)", {
        "text": "The product works, but it feels outdated and lacks important "
                "features.", "top_k": 2}),
    ("배치 처리", {
        "texts": [
            "Absolutely fantastic experience from start to finish.",
            "It was okay, nothing special.",
            "Worst purchase I have ever made.",
        ]}),
]

SUMMARIZE_CASES = [
    ("실전 기사형", {
        "text": "Artificial intelligence has rapidly transformed various industries "
                "over the past decade. In healthcare, AI is being used to assist "
                "doctors in diagnosing diseases more accurately and efficiently. In "
                "finance, machine learning models analyze vast amounts of data to "
                "detect fraud and optimize investment strategies. However, despite "
                "these advancements, concerns remain regarding data privacy, "
                "algorithmic bias, and job displacement. Experts emphasize that "
                "responsible AI development, combined with proper regulation and "
                "ethical guidelines, is essential to ensure that the benefits of AI "
                "outweigh its potential risks.",
        "max_length": 120, "min_length": 40}),
    ("더 긴 문서", {
        "text": "Large language models have become a central topic in artificial "
                "intelligence research. These models are trained on massive datasets "
                "and are capable of performing tasks such as translation, "
                "summarization, and question answering. Despite their impressive "
                "capabilities, they require significant computational resources and "
                "raise concerns related to environmental impact. Researchers are now "
                "focusing on model efficiency, parameter reduction, and knowledge "
                "distillation techniques to address these challenges. As AI systems "
                "become more integrated into daily life, transparency and "
                "explainability are increasingly important.",
        "max_length": 100, "min_length": 30}),
]

# 개요 문서의 두 케이스는 모두 1024 토큰 이하라 단일 요약 경로만 탄다.
# 분할 요약(map-reduce)이 실제로 동작하는지 보려면 한계를 넘는 입력이 필요하다.
_LONG_PARAGRAPHS = [
    "Artificial intelligence has rapidly transformed various industries over the "
    "past decade. In healthcare, AI is being used to assist doctors in diagnosing "
    "diseases more accurately and efficiently. In finance, machine learning models "
    "analyze vast amounts of data to detect fraud and optimize investment strategies.",
    "Large language models have become a central topic in artificial intelligence "
    "research. These models are trained on massive datasets and are capable of "
    "performing tasks such as translation, summarization, and question answering. "
    "They require significant computational resources and raise concerns related to "
    "environmental impact.",
    "Autonomous vehicles rely on computer vision and sensor fusion to perceive their "
    "surroundings. Regulatory frameworks differ widely between countries, which slows "
    "down large scale deployment. Safety validation remains the single largest "
    "obstacle for the industry.",
    "In manufacturing, predictive maintenance models estimate when equipment is "
    "likely to fail so that repairs can be scheduled before a breakdown occurs. This "
    "reduces downtime and lowers operating costs, but it requires reliable sensor "
    "data collected over long periods.",
    "Education technology has adopted adaptive learning systems that adjust the "
    "difficulty of exercises to each student. Critics argue that such systems can "
    "narrow the curriculum and that human teachers remain essential for motivation "
    "and mentorship.",
    "Climate researchers use machine learning to downscale global climate models to "
    "regional resolution. These techniques help local governments plan for flooding "
    "and heat waves, although uncertainty in the underlying physical models remains "
    "substantial.",
]
SUMMARIZE_CASES.append(
    ("긴 문서 → map-reduce 분할 요약 강제", {
        "text": " ".join(_LONG_PARAGRAPHS * 3),
        "max_length": 130, "min_length": 40}),
)

TRANSLATE_CASES = [
    ("일상 문장", {"text": "Hello, how are you doing today?"}),
    ("복문", {"text": "Although the project was challenging, the team successfully "
                    "completed it on time."}),
    ("기술 문장", {"text": "Large language models require careful fine-tuning and "
                       "evaluation to ensure reliable performance in real-world "
                       "applications."}),
    ("질문형", {"text": "What are the ethical challenges associated with deploying AI "
                     "systems in healthcare?"}),
]


def call(path: str, payload: dict | None = None, timeout: int = 600) -> tuple[int, dict]:
    url = f"{BASE}{path}"
    if payload is None:
        req = urllib.request.Request(url)
    else:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")


def run_group(title: str, path: str, cases: list[tuple[str, dict]]) -> list[dict]:
    print(f"\n{'=' * 78}\n{title}  ({path})\n{'=' * 78}")
    records = []
    for name, payload in cases:
        started = time.perf_counter()
        code, body = call(path, payload)
        wall = (time.perf_counter() - started) * 1000
        ok = code == 200
        print(f"\n[{'PASS' if ok else 'FAIL'}] {name}  (HTTP {code}, {wall:.0f}ms)")
        print(f"  요청: {json.dumps(payload, ensure_ascii=False)[:160]}")
        print(f"  응답: {json.dumps(body, ensure_ascii=False, indent=2)[:900]}")
        records.append({
            "group": title, "case": name, "request": payload,
            "status": code, "ok": ok, "response": body,
            "wall_ms": round(wall, 1),
        })
    return records


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="결과 JSON 저장 경로")
    ap.add_argument(
        "--groups",
        default="classify,summarize,translate",
        help="실행할 그룹(쉼표 구분). 메모리/디스크가 빠듯할 때 나눠서 돌린다.",
    )
    args = ap.parse_args()
    selected = {g.strip() for g in args.groups.split(",") if g.strip()}

    code, health = call("/health", None, timeout=30)
    if code != 200:
        print(f"서버에 연결할 수 없습니다 (HTTP {code}). uvicorn 이 떠 있는지 확인하세요.")
        return 1
    print("헬스체크:", json.dumps(health, ensure_ascii=False, indent=2))

    records: list[dict] = []
    if "classify" in selected:
        records += run_group("1. 감성분석", "/nlp/classify", CLASSIFY_CASES)
    if "summarize" in selected:
        records += run_group("2. 요약", "/nlp/summarize", SUMMARIZE_CASES)
    if "translate" in selected:
        records += run_group("3. 번역", "/nlp/translate", TRANSLATE_CASES)

    _, health_after = call("/health", None, timeout=30)

    passed = sum(1 for r in records if r["ok"])
    print(f"\n{'=' * 78}\n결과: {passed}/{len(records)} 통과\n{'=' * 78}")

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(
                {"health_before": health, "health_after": health_after,
                 "passed": passed, "total": len(records), "records": records},
                ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"저장: {out}")

    return 0 if passed == len(records) else 1


if __name__ == "__main__":
    sys.exit(main())
