# 커피 주문 챗봇에서 사용할 메뉴 데이터를 정의합니다.
# 실제 서비스에서는 이 파일 대신 MySQL, SQLite, CSV, 크롤링 데이터 등을 사용할 수 있습니다.

# 메뉴 목록을 리스트 안의 딕셔너리 구조로 저장합니다.
COFFEE_MENU = [
    {
        "id": 1,  # 메뉴를 구분하기 위한 고유 번호입니다.
        "name": "아메리카노",  # 사용자에게 보여줄 메뉴 이름입니다.
        "category": "coffee",  # 메뉴 종류를 구분하기 위한 카테고리입니다.
        "temperature": ["hot", "ice"],  # 선택 가능한 온도 옵션입니다.
        "taste_tags": ["깔끔한", "고소한", "쌉싸름한"],  # 추천에 사용할 맛 태그입니다.
        "description": "진한 에스프레소에 물을 더한 기본 커피입니다.",  # 메뉴 설명입니다.
        "price": 2500,  # 기본 가격입니다.
    },
    {
        "id": 2,
        "name": "카페라떼",
        "category": "coffee",
        "temperature": ["hot", "ice"],
        "taste_tags": ["부드러운", "고소한", "담백한"],
        "description": "에스프레소와 우유가 어우러진 부드러운 커피입니다.",
        "price": 3500,
    },
    {
        "id": 3,
        "name": "카푸치노",
        "category": "coffee",
        "temperature": ["hot"],
        "taste_tags": ["부드러운", "고소한", "풍성한"],
        "description": "우유 거품이 풍성한 클래식 커피입니다.",
        "price": 3800,
    },
    {
        "id": 4,
        "name": "카라멜 마키아토",
        "category": "coffee",
        "temperature": ["hot", "ice"],
        "taste_tags": ["달달한", "부드러운", "향긋한"],
        "description": "카라멜의 달콤함이 더해진 인기 커피입니다.",
        "price": 4300,
    },
    {
        "id": 5,
        "name": "바닐라 라떼",
        "category": "coffee",
        "temperature": ["hot", "ice"],
        "taste_tags": ["달달한", "부드러운", "향긋한"],
        "description": "바닐라 향과 우유가 잘 어울리는 달콤한 라떼입니다.",
        "price": 4200,
    },
    {
        "id": 6,
        "name": "아포가토",
        "category": "dessert",
        "temperature": ["ice"],
        "taste_tags": ["달달한", "진한", "디저트"],
        "description": "아이스크림 위에 에스프레소를 부어 먹는 디저트 메뉴입니다.",
        "price": 4800,
    },
    {
        "id": 7,
        "name": "콜드브루",
        "category": "coffee",
        "temperature": ["ice"],
        "taste_tags": ["깔끔한", "고소한", "부드러운"],
        "description": "차갑게 우려 산미와 향이 깔끔한 커피입니다.",
        "price": 4000,
    },
    {
        "id": 8,
        "name": "복숭아 아이스티",
        "category": "non_coffee",
        "temperature": ["ice"],
        "taste_tags": ["달달한", "상큼한", "시원한"],
        "description": "커피가 부담스러울 때 좋은 달콤한 아이스티입니다.",
        "price": 3200,
    },
]

# 사용자가 맛으로 메뉴를 고를 수 있도록 대표 맛 키워드를 정의합니다.
TASTE_KEYWORDS = ["부드러운", "고소한", "달달한", "상큼한", "진한", "깔끔한", "시원한"]
