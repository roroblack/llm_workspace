# -*- coding: utf-8 -*-
"""HTML 강의 파일에서 제목, 요약, 코드 블록을 추출하는 공통 유틸리티입니다."""

# pathlib는 운영체제별 경로 구분자 차이를 자동으로 처리하기 위해 사용합니다.
from pathlib import Path

# BeautifulSoup는 HTML 태그를 파싱해서 필요한 텍스트만 뽑기 위해 사용합니다.
from bs4 import BeautifulSoup


# HtmlLessonReader 클래스는 여러 HTML 파일을 읽는 기능을 한 곳에 모읍니다.
class HtmlLessonReader:
    """data/docs/source_html 폴더의 HTML 강의 파일을 읽는 클래스입니다."""

    # __init__은 객체가 만들어질 때 HTML 파일 폴더 경로를 저장합니다.
    def __init__(self, html_dir: Path) -> None:
        # html_dir 값을 Path 객체로 변환하여 이후 경로 연산을 안전하게 수행합니다.
        self.html_dir = Path(html_dir)

    # list_html_files는 폴더 안의 HTML 파일 목록을 이름순으로 반환합니다.
    def list_html_files(self) -> list[Path]:
        # glob("*.html")은 지정 폴더에서 확장자가 html인 파일만 찾습니다.
        return sorted(self.html_dir.glob("*.html"))

    # parse_file은 HTML 파일 하나에서 제목, 본문 요약, 코드 블록을 추출합니다.
    def parse_file(self, html_path: Path) -> dict:
        # HTML 파일 내용을 UTF-8 인코딩으로 읽습니다.
        html_text = html_path.read_text(encoding="utf-8")
        # BeautifulSoup 객체를 만들어 HTML 태그 구조를 탐색할 수 있게 합니다.
        soup = BeautifulSoup(html_text, "html.parser")
        # title 태그가 있으면 문서 제목을 가져오고, 없으면 파일명을 제목으로 사용합니다.
        title = soup.find("title").get_text(strip=True) if soup.find("title") else html_path.name
        # h1 태그가 있으면 강의 주제명을 가져오고, 없으면 빈 문자열을 사용합니다.
        heading = soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else ""
        # p 태그 중 앞의 3개 문단만 요약 후보로 사용합니다.
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")[:3]]
        # pre code 태그 안에 들어 있는 코드 예제를 모두 추출합니다.
        code_blocks = [code.get_text() for code in soup.select("pre code")]
        # 추출한 정보를 dict로 묶어 호출한 쪽에서 쉽게 사용할 수 있게 반환합니다.
        return {"file": html_path.name, "title": title, "heading": heading, "paragraphs": paragraphs, "code_blocks": code_blocks}

    # parse_all은 폴더 안의 모든 HTML 파일을 한 번에 파싱합니다.
    def parse_all(self) -> list[dict]:
        # list_html_files로 가져온 각 파일에 parse_file을 적용해 리스트로 반환합니다.
        return [self.parse_file(path) for path in self.list_html_files()]
