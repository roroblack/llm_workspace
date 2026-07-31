"""브라우저 렌더링 수집기 — API 직접 호출이 막힌 사이트용 공통 엔진.

★왜 필요한가

    지금까지 4개사(삼성화재·DB손보·NH농협생명·동양생명)는 **데이터 엔드포인트를 직접 호출**해
    뚫었다. 그게 빠르고 화면 개편에 강하다. 그러나 그 방법이 안 통하는 곳이 있다.

      삼성생명   요청 본문이 **암호화**되어 있다(`g=…&b=…`). 페이로드를 만들 수 없다.
      NH농협손보  선택 UI 가 커스텀이라 AJAX 를 잡지 못했다.

    이런 곳은 **브라우저가 알아서 암호화·선택을 처리하게 하고** 결과만 받는다.
    우회가 아니라 **사이트가 의도한 경로(브라우저)를 그대로 쓰는 것**이다.

★이 방식의 대가 (정직 기록)

    - 화면 구조(셀렉터)에 의존하므로 **개편에 약하다.** 그래서 셀렉터가 0건을 내면
      조용히 넘어가지 않고 `InfraError` 로 실패시킨다 — '없음'과 '못 찾음'은 다르다.
    - 느리다. 한 건당 수 초가 걸린다.
    - 그래서 **API 가 되는 곳에는 쓰지 않는다.** 마지막 수단이다.

★설정만 추가하면 사이트가 늘어난다
    `SITES` 에 `SiteConfig` 를 하나 넣으면 된다. 엔진은 공통이다.

실행:
    python -m scripts.crawl.browser_collector --site samsunglife --probe
    python -m scripts.crawl.browser_collector --site samsunglife --limit 5
"""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.robotparser import RobotFileParser

from playwright.sync_api import Error as PWError
from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

from app.core.errors import ConfigError, InfraError, ValidationErr

_ROOT = Path(__file__).resolve().parents[2]
_RAW = _ROOT / "data" / "raw" / "insurance_terms"
_MANIFESTS = _ROOT / "data" / "raw" / "manifests"
_CATALOG = _ROOT / "data" / "catalog"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36 BarobomResearchBot/0.1 "
    "(+contact: set-before-deploy; purpose: insurance-terms-research)"
)
NAV_TIMEOUT_MS = 45_000
MAX_BYTES = 60 * 1024 * 1024
#: 남의 서버에 부하를 주지 않기 위한 행 간 대기.
ROW_DELAY_MS = 1_200
#: 이미지·폰트는 받지 않는다.
_BLOCK = {"image", "font", "media"}


@dataclass(frozen=True)
class SiteConfig:
    """사이트 하나를 뚫는 데 필요한 최소 정보."""

    insurer: str
    slug: str
    host: str
    entry_url: str
    #: 결과 표. 한 페이지에 표가 여러 개면 이걸로 먼저 고른다(삼성생명은 3개다).
    table_selector: str
    #: 표 **안에서** 행. 이 셀렉터가 0건이면 실패시킨다.
    row_selector: str
    #: 행 안에서 **보험약관** 링크. 문구로 고르는 것이 안전하다
    #: (열 순서는 회사마다 다르다 — 삼성화재 file1=약관, NH농협생명은 3번째였다).
    terms_link_selector: str
    #: 상품명이 들어 있는 셀.
    name_cell_selector: str
    #: 검색이 필요한 경우.
    search_input_selector: str | None = None
    search_terms: tuple[str, ...] = ()
    submit_selector: str | None = None
    #: 판매중지 탭 등 추가로 눌러야 하는 것.
    pre_click_selectors: tuple[str, ...] = ()
    settle_ms: int = 4_000
    #: '다음 페이지' 버튼. 없으면 1페이지만 받는다.
    next_page_selector: str | None = None
    #: 페이지 상한. 무한 루프를 막는 안전장치이지 '여기까지만 받자'가 아니다.
    max_pages: int = 200


SITES: dict[str, SiteConfig] = {
    "samsunglife": SiteConfig(
        insurer="삼성생명",
        slug="samsunglife",
        host="www.samsunglife.com",
        entry_url="https://www.samsunglife.com/individual/products/disclosure/sales/PDO-PRPRI010110M",
        # ★페이지에 표가 3개 있다(전체/판매/판매중지). 첫 번째가 목록이다.
        #   `table tbody tr` 로 잡으면 다른 표의 1행짜리 껍데기를 문다(실측: 3행만 나왔다).
        table_selector="table",   # 첫 번째 표가 목록이다
        row_selector="tbody tr",
        next_page_selector="button.btn-paging-next",
        # 약관 링크는 문구가 없고 **title 속성**에 '보험약관'이 있다.
        #   `a:has-text('약관')` 은 0건이었다 — 링크 텍스트가 상품명이기 때문이다.
        terms_link_selector="a.btn-file[title*='보험약관']",
        name_cell_selector="td:nth-child(3)",
        # ★검색을 쓰지 않는다. 이 화면은 검색 없이도 전체(6,557건)를 보여주고,
        #   보이는 검색창 셀렉터가 숨김 요소를 잡아 fill 이 실패했다(실측).
        #   전체를 받아 로컬에서 거르는 편이 "무엇을 놓쳤나"를 걱정하지 않아도 된다.
        settle_ms=9_000,
    ),
    "nhfire": SiteConfig(
        insurer="NH농협손해보험",
        slug="nhfire",
        host="www.nhfire.co.kr",
        entry_url="https://www.nhfire.co.kr/announce/productAnnounce/retrieveInsuranceProductsAnnounce.nhfire",
        # ★이 화면은 `상품군 → 상품구분 → 보험상품` 3단계를 고른 뒤에야 표가 채워진다.
        #   실손은 장기보험에 있으므로 먼저 그것을 누른다.
        pre_click_selectors=("text=장기보험",),
        # 상품명 검색으로 좁힌다(3단계를 전부 순회하지 않기 위해).
        search_input_selector="input[name='searchWord'], input#searchWord",
        search_terms=("실손",),
        # 상품 목록 표는 '판매개시일 … 약관 …' 헤더를 가진 표다.
        table_selector="table:has(th:text-is('약관'))",
        row_selector="tbody tr",
        terms_link_selector="td:nth-child(3) a, td:nth-child(3) button",
        name_cell_selector="td:nth-child(1)",
        settle_ms=6_000,
    ),
}


@dataclass
class Collected:
    insurer: str
    url: str
    http_status: int
    content_type: str
    bytes: int
    sha256: str
    fetched_at: str
    saved_as: str
    product_code: str = ""
    product_name: str = ""
    sale_start: str = ""
    sale_end: str = ""
    filename_kind_hint: str = "policy_terms"
    identification: str = "unidentified"
    #: 브라우저로 받았다는 사실을 남긴다 — 나중에 방식별 성공률을 볼 수 있다.
    collector: str = "browser"


def _robots_allows(host: str, url: str) -> tuple[bool, str]:
    req = urllib.request.Request(f"https://{host}/robots.txt", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read(512_000).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return True, "robots 없음(규칙 부재)"
        return False, f"robots HTTP {e.code}"
    except (urllib.error.URLError, socket.timeout, TimeoutError) as e:
        return False, f"robots 확인 불가({type(e).__name__})"
    rp = RobotFileParser()
    rp.parse(body.splitlines())
    ok = rp.can_fetch(USER_AGENT, url)
    return ok, f"200 → {'allow' if ok else 'disallow'}"


def _fetched_urls() -> set[str]:
    if not _MANIFESTS.exists():
        return set()
    out: set[str] = set()
    for p in _MANIFESTS.glob("*.jsonl"):
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.add(json.loads(line)["url"])
    return out


def _save(cfg: SiteConfig, blob: bytes, url: str, name: str, ctype: str) -> Collected:
    if not blob.startswith(b"%PDF"):
        raise InfraError(f"PDF가 아닙니다(앞 8바이트={blob[:8]!r}): {name}")
    if len(blob) > MAX_BYTES:
        raise ValidationErr(f"상한 초과: {name}")
    digest = hashlib.sha256(blob).hexdigest()
    safe = "".join(c for c in name if c not in '\\/:*?"<>|')[:70] or "unnamed"
    out_dir = _RAW / cfg.slug
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = out_dir / f"{digest[:12]}_{safe}.pdf"
    saved.write_bytes(blob)
    return Collected(
        insurer=cfg.insurer,
        url=url,
        http_status=200,
        content_type=ctype or "application/pdf",
        bytes=len(blob),
        sha256=digest,
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        saved_as=str(saved.relative_to(_ROOT)).replace("\\", "/"),
        product_name=name,
    )


def run(cfg: SiteConfig, *, limit: int, probe: bool) -> list[Collected]:
    allowed, verdict = _robots_allows(cfg.host, cfg.entry_url)
    if not allowed:
        raise InfraError(f"robots가 허용하지 않습니다: {cfg.host} ({verdict})")
    print(f"robots: {verdict}")

    done = _fetched_urls()
    out: list[Collected] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1366, "height": 950},
                                  locale="ko-KR", accept_downloads=True)
        ctx.set_default_navigation_timeout(NAV_TIMEOUT_MS)
        ctx.route("**/*", lambda r: r.abort() if r.request.resource_type in _BLOCK else r.continue_())

        #: ★PDF 는 클릭 결과로 **네트워크 응답**에 실려 온다. DOM 링크만 보면 놓친다.
        pdf_hits: list[tuple[str, bytes, str]] = []

        def _on_response(resp):
            try:
                ct = resp.headers.get("content-type", "")
                if "pdf" in ct.lower():
                    pdf_hits.append((resp.url, resp.body(), ct))
            except Exception:  # noqa: BLE001
                pass

        ctx.on("response", _on_response)
        page = ctx.new_page()

        try:
            page.goto(cfg.entry_url, wait_until="domcontentloaded")
            page.wait_for_timeout(cfg.settle_ms)

            for sel in cfg.pre_click_selectors:
                try:
                    page.click(sel, timeout=8_000)
                    page.wait_for_timeout(cfg.settle_ms)
                except (PWTimeout, PWError) as e:
                    raise InfraError(f"사전 클릭 실패({sel}): {type(e).__name__}") from e

            if cfg.search_input_selector and cfg.search_terms:
                box = page.locator(cfg.search_input_selector).first
                box.fill(cfg.search_terms[0], timeout=10_000)
                if cfg.submit_selector:
                    page.click(cfg.submit_selector, timeout=10_000)
                else:
                    box.press("Enter")
                page.wait_for_timeout(cfg.settle_ms)

            # ★표를 먼저 고른 뒤 그 안에서 행을 찾는다.
            #   `table tbody tr` 로 한 번에 잡으면 다른 표의 껍데기 행을 문다(실측).
            table = page.locator(cfg.table_selector).first
            if table.count() == 0:
                raise InfraError(f"표 셀렉터가 0건입니다: {cfg.table_selector!r}")
            page_no = 0
            seen_first_cell = ""
            while page_no < cfg.max_pages:
                page_no += 1
                table = page.locator(cfg.table_selector).first
                rows = table.locator(cfg.row_selector)
                # ★행이 늦게 그려진다. 6초에서는 1행만 잡혔고 9초에서 10행이 나왔다(실측).
                try:
                    rows.nth(1).wait_for(timeout=15_000)
                except (PWTimeout, PWError):
                    pass
                n = rows.count()
                if n == 0:
                    if page_no == 1:
                        # ★'결과 없음'과 '셀렉터가 안 맞음'을 구분한다.
                        raise InfraError(
                            f"행 셀렉터가 0건입니다: {cfg.row_selector!r}. "
                            "화면 구조가 바뀌었거나 셀렉터가 틀렸습니다."
                        )
                    break

                # ★페이지가 실제로 넘어갔는지 확인한다. '다음' 버튼이 먹지 않아도
                #   같은 페이지를 계속 긁으면 조용히 중복만 쌓인다.
                try:
                    first = rows.nth(0).inner_text(timeout=3_000)[:60]
                except (PWTimeout, PWError):
                    first = ""
                if page_no > 1 and first == seen_first_cell:
                    print(f"  [중단] p{page_no}: 페이지가 넘어가지 않았다(첫 행이 동일).")
                    break
                seen_first_cell = first

                print(f"  p{page_no}: 행 {n}개")
                if probe:
                    for i in range(min(n, 5)):
                        row = rows.nth(i)
                        try:
                            nm = row.locator(cfg.name_cell_selector).first.inner_text(timeout=3_000)
                        except (PWTimeout, PWError):
                            nm = "(상품명 셀 못 읽음)"
                        links = row.locator(cfg.terms_link_selector).count()
                        print(f"    [{i + 1}] {nm.strip()[:40]!r} / 약관링크 {links}개")
                    return []

                for i in range(n):
                    if limit and len(out) >= limit:
                        return out
                    row = rows.nth(i)
                    try:
                        nm = row.locator(cfg.name_cell_selector).first.inner_text(timeout=3_000).strip()
                    except (PWTimeout, PWError):
                        nm = f"p{page_no}r{i + 1}"
                    link = row.locator(cfg.terms_link_selector).first
                    if link.count() == 0:
                        continue
                    before = len(pdf_hits)
                    try:
                        link.click(timeout=10_000)
                        page.wait_for_timeout(2_500)
                    except (PWTimeout, PWError) as e:
                        print(f"    [SKIP] {nm[:28]}: 클릭 실패 {type(e).__name__}")
                        continue
                    for url, blob, ct in pdf_hits[before:]:
                        if url in done:
                            continue
                        try:
                            rec = _save(cfg, blob, url, nm, ct)
                            out.append(rec)
                            done.add(url)
                            print(f"    [OK] {nm[:28]} {rec.bytes:,}B")
                        except (InfraError, ValidationErr) as e:
                            print(f"    [FAIL] {nm[:28]}: {e}")
                    page.wait_for_timeout(ROW_DELAY_MS)

                if not cfg.next_page_selector:
                    break
                nxt = page.locator(cfg.next_page_selector).first
                if nxt.count() == 0 or not nxt.is_enabled():
                    break
                try:
                    nxt.click(timeout=8_000)
                    page.wait_for_timeout(cfg.settle_ms)
                except (PWTimeout, PWError):
                    break
        finally:
            ctx.close()
            browser.close()

    if out:
        _MANIFESTS.mkdir(parents=True, exist_ok=True)
        path = _MANIFESTS / f"{cfg.slug}.jsonl"
        with path.open("a", encoding="utf-8") as f:
            for r in out:
                f.write(json.dumps(asdict(r), ensure_ascii=False) + "\n")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True, help=f"대상: {', '.join(SITES)}")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--probe", action="store_true", help="받지 않고 셀렉터가 맞는지만 확인")
    args = ap.parse_args()

    cfg = SITES.get(args.site)
    if not cfg:
        raise ConfigError(f"등록되지 않은 사이트입니다: {args.site} (가능: {', '.join(SITES)})")

    got = run(cfg, limit=args.limit, probe=args.probe)
    print(f"\n수집 {len(got)}건")
    if got:
        print(f"→ data/raw/insurance_terms/{cfg.slug}/  ·  기록: data/raw/manifests/{cfg.slug}.jsonl")
    print("※ 받은 문서가 '무엇인지'는 판정하지 않았다(identification=unidentified).")


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(_ROOT))
    main()
