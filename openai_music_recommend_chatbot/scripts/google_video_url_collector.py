"""
구글 검색 영상 URL 수집 스크립트입니다.

이 파일은 제공된 Jupyter Notebook의 Selenium 기반 수집 코드를
현재 Selenium 문법에 맞게 정리한 선택 실행용 예제입니다.

주의:
1. 구글 검색 결과 HTML 구조는 자주 변경될 수 있습니다.
2. 자동 수집은 검색 서비스 약관과 robots 정책을 확인한 뒤 사용해야 합니다.
3. 수집한 영상 URL을 챗봇에 사용할 때는 영상 저작권과 출처를 표시해야 합니다.
"""

from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


def collect_google_video_urls(keyword: str, chrome_driver_path: str) -> list[dict]:
    """
    구글에서 특정 키워드의 동영상 검색 결과 URL을 수집합니다.

    keyword:
        예: "그리울 때 듣는 노래"

    chrome_driver_path:
        Windows 예: "C:/chromedriver/chromedriver.exe"
    """

    # 한글 검색어를 URL에 넣을 수 있도록 인코딩합니다.
    encoded_keyword = quote_plus(keyword)

    # 구글 검색 URL을 생성합니다.
    search_url = f"https://www.google.com/search?q={encoded_keyword}"

    # ChromeDriver 실행 서비스를 생성합니다.
    service = Service(chrome_driver_path)

    # Selenium Chrome 브라우저 객체를 생성합니다.
    driver = webdriver.Chrome(service=service)

    try:
        # 구글 검색 페이지로 이동합니다.
        driver.get(search_url)

        # 동영상 탭을 찾고 클릭합니다.
        # 구글 화면 구조가 바뀌면 이 selector는 수정이 필요합니다.
        video_tab = driver.find_element(By.LINK_TEXT, "동영상")
        video_tab.click()

        # 동영상 탭 전환 후 현재 페이지 HTML을 가져옵니다.
        html = driver.page_source

        # BeautifulSoup으로 HTML을 파싱합니다.
        soup = BeautifulSoup(html, "html.parser")

        # 검색 결과 제목 후보를 찾습니다.
        title_elements = soup.find_all("h3")

        # 검색 결과 링크 후보를 찾습니다.
        link_elements = soup.find_all("a")

        # 결과를 저장할 리스트입니다.
        results = []

        # 링크 요소를 반복하면서 제목과 URL을 수집합니다.
        for link in link_elements:
            # href 속성이 없는 링크는 건너뜁니다.
            href = link.get("href")
            if not href:
                continue

            # YouTube 링크 또는 동영상 검색 결과 링크만 필터링합니다.
            if "youtube.com" not in href and "youtu.be" not in href:
                continue

            # 링크 안의 텍스트를 제목으로 사용합니다.
            title = link.get_text(strip=True)

            # 제목이 너무 짧으면 건너뜁니다.
            if len(title) < 2:
                continue

            # 결과에 추가합니다.
            results.append({"title": title, "url": href})

        # 중복 제거를 위해 URL 기준으로 정리합니다.
        unique_results = []
        seen_urls = set()

        for item in results:
            if item["url"] not in seen_urls:
                unique_results.append(item)
                seen_urls.add(item["url"])

        # 정리된 결과를 반환합니다.
        return unique_results

    finally:
        # 브라우저를 종료합니다.
        driver.quit()


if __name__ == "__main__":
    # 사용자에게 검색어를 입력받습니다.
    keyword = input("당신의 마음과 함께 음악을 넣어 검색해 보세요: ")

    # 사용자에게 ChromeDriver 경로를 입력받습니다.
    driver_path = input("ChromeDriver 경로를 입력하세요: ")

    # 검색 결과를 수집합니다.
    items = collect_google_video_urls(keyword, driver_path)

    # 수집 결과를 화면에 출력합니다.
    for index, item in enumerate(items, start=1):
        print(f"{index}. {item['title']}")
        print(f"   {item['url']}")
