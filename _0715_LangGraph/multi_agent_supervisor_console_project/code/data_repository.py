# -*- coding: utf-8 -*-
"""상품 및 FAQ CSV 데이터를 읽고 검색하는 저장소 모듈입니다."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

# 같은 code 폴더의 common.py가 제공하는 DATA 경로를 가져옵니다.
from common import DATA


@dataclass(frozen=True)
class Product:
    """상품 CSV 한 행을 표현하는 변경 불가능한 데이터 객체입니다."""

    product_id: str
    product_name: str
    category: str
    price: int
    stock: int
    rating: float


@dataclass(frozen=True)
class FaqItem:
    """FAQ CSV 한 행을 표현하는 변경 불가능한 데이터 객체입니다."""

    question: str
    answer: str
    keywords: tuple[str, ...]


def _require_file(path: Path) -> None:
    """실습 데이터 파일이 없으면 원인을 알 수 있는 예외를 발생시킵니다."""
    # 지정된 경로가 실제 파일인지 검사합니다.
    if not path.is_file():
        # 누락된 파일의 절대 경로를 포함하여 문제 해결에 필요한 정보를 제공합니다.
        raise FileNotFoundError(f"실습 데이터 파일을 찾을 수 없습니다: {path}")


def load_products() -> list[Product]:
    """products.csv를 읽어 Product 객체 목록으로 반환합니다."""
    # common.py의 DATA 경로를 기준으로 상품 CSV 파일 경로를 구성합니다.
    path = DATA / "products.csv"

    # 파일이 실제로 존재하는지 먼저 확인합니다.
    _require_file(path)

    # 읽은 상품을 저장할 빈 리스트를 생성합니다.
    products: list[Product] = []

    # Excel에서 저장한 CSV도 읽을 수 있도록 utf-8-sig 인코딩으로 파일을 엽니다.
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        # 첫 행의 열 이름을 키로 사용하는 DictReader를 생성합니다.
        reader = csv.DictReader(file)

        # CSV의 각 행을 순서대로 읽습니다.
        for row in reader:
            # 문자열로 읽힌 숫자를 실제 int/float로 변환하여 Product 객체를 생성합니다.
            products.append(
                Product(
                    product_id=row["product_id"],
                    product_name=row["product_name"],
                    category=row["category"],
                    price=int(row["price"]),
                    stock=int(row["stock"]),
                    rating=float(row["rating"]),
                )
            )

    # 완성된 상품 목록을 호출한 쪽에 반환합니다.
    return products


def load_faq() -> list[FaqItem]:
    """faq.csv를 읽어 FaqItem 객체 목록으로 반환합니다."""
    # common.py의 DATA 경로를 기준으로 FAQ CSV 파일 경로를 구성합니다.
    path = DATA / "faq.csv"

    # 파일 존재 여부를 검사합니다.
    _require_file(path)

    # 읽은 FAQ를 저장할 빈 리스트를 생성합니다.
    faq_items: list[FaqItem] = []

    # BOM이 있는 CSV도 안전하게 처리하도록 utf-8-sig로 파일을 엽니다.
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        # 열 이름을 사용해 값을 읽는 DictReader를 생성합니다.
        reader = csv.DictReader(file)

        # 각 FAQ 행을 순서대로 처리합니다.
        for row in reader:
            # 쉼표로 저장된 키워드를 분리하고 공백을 제거한 튜플로 변환합니다.
            keywords = tuple(word.strip() for word in row["keywords"].split(",") if word.strip())

            # FAQ 데이터 객체를 만들어 목록에 추가합니다.
            faq_items.append(
                FaqItem(
                    question=row["question"],
                    answer=row["answer"],
                    keywords=keywords,
                )
            )

    # 완성된 FAQ 목록을 반환합니다.
    return faq_items


def search_products(category: str, limit: int = 3) -> str:
    """카테고리와 관련된 재고 보유 상품을 평점순으로 최대 limit개 추천합니다."""
    # 사용자가 입력한 검색어를 비교하기 쉬운 소문자 문자열로 정규화합니다.
    normalized = category.strip().lower()

    # 전체 상품 데이터를 읽습니다.
    products = load_products()

    # 카테고리나 상품명에 검색어가 포함되고 재고가 있는 상품만 선택합니다.
    matched = [
        product
        for product in products
        if product.stock > 0
        and (
            normalized in product.category.lower()
            or normalized in product.product_name.lower()
            or product.category.lower() in normalized
        )
    ]

    # 직접 일치하는 상품이 없으면 전체 재고 상품을 대상으로 추천 후보를 만듭니다.
    if not matched:
        matched = [product for product in products if product.stock > 0]

    # 평점은 높은 순서, 가격은 낮은 순서로 정렬하여 가성비 좋은 결과를 앞에 둡니다.
    ranked = sorted(matched, key=lambda product: (-product.rating, product.price))[:limit]

    # 추천 가능한 상품이 하나도 없으면 안내 문장을 반환합니다.
    if not ranked:
        return "현재 추천 가능한 재고 상품이 없습니다."

    # 사람이 읽기 쉬운 추천 결과 문자열을 만들기 위한 리스트를 생성합니다.
    lines = [f"'{category}' 관련 추천 상품입니다."]

    # 정렬된 상품 정보를 한 줄씩 추가합니다.
    for product in ranked:
        lines.append(
            f"- {product.product_name} | {product.price:,}원 | "
            f"평점 {product.rating:.1f} | 재고 {product.stock}개"
        )

    # 여러 줄을 줄바꿈 문자로 결합하여 최종 도구 결과로 반환합니다.
    return "\n".join(lines)


def search_faq(keyword: str, limit: int = 2) -> str:
    """질문·답변·키워드에서 관련 FAQ를 찾아 최대 limit개 반환합니다."""
    # 검색어 앞뒤 공백을 제거하고 소문자로 변환합니다.
    normalized = keyword.strip().lower()

    # 전체 FAQ 데이터를 읽습니다.
    faq_items = load_faq()

    # 각 FAQ의 질문, 답변, 키워드에 검색어가 포함되는지 검사합니다.
    matched = [
        item
        for item in faq_items
        if normalized in item.question.lower()
        or normalized in item.answer.lower()
        or any(normalized in tag.lower() or tag.lower() in normalized for tag in item.keywords)
    ]

    # 완전한 검색어로 찾지 못하면 질문 속 개별 단어를 사용해 한 번 더 검색합니다.
    if not matched:
        tokens = [token for token in normalized.replace("?", " ").split() if len(token) >= 2]
        matched = [
            item
            for item in faq_items
            if any(
                token in item.question.lower()
                or token in item.answer.lower()
                or any(token in tag.lower() for tag in item.keywords)
                for token in tokens
            )
        ]

    # 관련 FAQ가 없으면 근거를 찾지 못했다는 명확한 메시지를 반환합니다.
    if not matched:
        return "관련 FAQ 근거를 찾지 못했습니다. 상담원 연결이 필요합니다."

    # FAQ 결과를 사람이 읽기 쉬운 Q/A 형식으로 변환합니다.
    lines: list[str] = []

    # 최대 limit개 항목만 출력합니다.
    for item in matched[:limit]:
        lines.append(f"Q. {item.question}\nA. {item.answer}")

    # 각 FAQ 항목 사이를 빈 줄로 구분하여 반환합니다.
    return "\n\n".join(lines)
