# 문자열 검색과 정규화를 위해 typing 모듈을 불러옵니다.
from typing import Dict, List
# 커피 메뉴 데이터를 불러옵니다.
from app.menu_data import COFFEE_MENU, TASTE_KEYWORDS

# 메모리 기반 장바구니를 생성합니다.
CART: List[Dict] = []


# 사용자의 메시지에서 온도 옵션을 추출하는 함수입니다.
def extract_temperature(message: str) -> str:
    # 메시지에 차가운 음료 관련 표현이 있으면 ice를 반환합니다.
    if any(word in message.lower() for word in ["아이스", "ice", "차가운", "시원한"]):
        return "ice"
    # 메시지에 따뜻한 음료 관련 표현이 있으면 hot을 반환합니다.
    if any(word in message.lower() for word in ["핫", "hot", "따뜻한", "뜨거운"]):
        return "hot"
    # 별도 표현이 없으면 기본값으로 ice를 반환합니다.
    return "ice"


# 사용자의 메시지에서 수량을 추출하는 함수입니다.
def extract_quantity(message: str) -> int:
    # 한국어 수량 표현을 숫자로 바꾸기 위한 딕셔너리입니다.
    korean_numbers = {"한": 1, "두": 2, "세": 3, "네": 4, "다섯": 5}
    # 한국어 수량 표현을 순회합니다.
    for word, number in korean_numbers.items():
        # 메시지에 해당 표현이 포함되어 있으면 숫자를 반환합니다.
        if f"{word} 잔" in message or f"{word}잔" in message or f"{word} 개" in message or f"{word}개" in message:
            return number
    # 아라비아 숫자 수량을 찾기 위해 1~9를 순회합니다.
    for number in range(1, 10):
        # 메시지에 숫자와 잔/개 표현이 포함되어 있으면 해당 숫자를 반환합니다.
        if f"{number}잔" in message or f"{number} 잔" in message or f"{number}개" in message or f"{number} 개" in message:
            return number
    # 수량 표현이 없으면 기본값 1을 반환합니다.
    return 1


# 메뉴 이름 또는 맛 태그를 기준으로 메뉴를 검색하는 함수입니다.
def find_menus(message: str, top_k: int = 3) -> List[Dict]:
    # 검색 결과를 저장할 리스트를 만듭니다.
    results = []
    # 사용자의 메시지를 소문자로 변환합니다.
    normalized = message.lower()
    # 메뉴 전체를 순회합니다.
    for menu in COFFEE_MENU:
        # 메뉴별 점수를 0으로 시작합니다.
        score = 0
        # 메뉴 이름이 사용자 메시지에 포함되면 높은 점수를 부여합니다.
        if menu["name"].lower().replace(" ", "") in normalized.replace(" ", ""):
            score += 5
        # 맛 태그가 사용자 메시지에 포함되면 점수를 부여합니다.
        for tag in menu["taste_tags"]:
            if tag in message:
                score += 2
        # 커피라는 단어가 있고 커피 카테고리이면 점수를 약간 부여합니다.
        if "커피" in message and menu["category"] == "coffee":
            score += 1
        # 계산된 점수가 있으면 결과 후보에 추가합니다.
        if score > 0:
            enriched = dict(menu)
            enriched["score"] = score
            results.append(enriched)
    # 결과가 없으면 기본 추천 메뉴를 사용합니다.
    if not results:
        results = [dict(menu, score=1) for menu in COFFEE_MENU[:top_k]]
    # 점수가 높은 순서대로 정렬합니다.
    results.sort(key=lambda item: item["score"], reverse=True)
    # 요청된 개수만큼 잘라 반환합니다.
    return results[:top_k]


# 장바구니에 메뉴를 추가하는 함수입니다.
def add_to_cart(menu_id: int, temperature: str, quantity: int, option_note: str = "") -> Dict:
    # 메뉴 ID와 일치하는 메뉴를 찾습니다.
    menu = next((item for item in COFFEE_MENU if item["id"] == menu_id), None)
    # 메뉴가 없으면 오류 메시지를 반환합니다.
    if menu is None:
        return {"ok": False, "message": "해당 메뉴를 찾을 수 없습니다."}
    # 선택한 온도가 메뉴 옵션에 없으면 가능한 첫 번째 온도로 변경합니다.
    if temperature not in menu["temperature"]:
        temperature = menu["temperature"][0]
    # 장바구니 항목을 구성합니다.
    cart_item = {
        "menu_id": menu["id"],
        "name": menu["name"],
        "temperature": temperature,
        "quantity": quantity,
        "price": menu["price"],
        "subtotal": menu["price"] * quantity,
        "option_note": option_note,
    }
    # 장바구니에 항목을 추가합니다.
    CART.append(cart_item)
    # 성공 결과를 반환합니다.
    return {"ok": True, "item": cart_item, "cart": CART, "total": cart_total()}


# 장바구니 총액을 계산하는 함수입니다.
def cart_total() -> int:
    # 모든 항목의 소계를 합산하여 반환합니다.
    return sum(item["subtotal"] for item in CART)


# 장바구니를 비우는 함수입니다.
def clear_cart() -> None:
    # 리스트 내부 항목을 모두 삭제합니다.
    CART.clear()
