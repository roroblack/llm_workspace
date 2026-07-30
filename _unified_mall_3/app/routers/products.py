"""상품 조회 라우터."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.errors import NotFoundErr
from app.db.database import get_db
from app.db.models import Product
from app.schemas.commerce import ProductResponse

router = APIRouter(prefix="/api/products", tags=["products"])


def _to_response(p: Product) -> ProductResponse:
    return ProductResponse(
        product_code=p.product_code,
        name=p.name,
        category=p.category,
        price=p.price,
        stock=p.inventory.stock if p.inventory else None,
    )


@router.get("", response_model=list[ProductResponse])
def list_products(db: Session = Depends(get_db)) -> list[ProductResponse]:
    # 질의는 MCP 리소스와 공용 1벌(catalog_query). 세션 수명은 요청 스코프가 소유하고,
    # 공용 질의가 세션 독립 DTO를 주므로 직렬화 시점에 지연 로딩이 일어나지 않는다.
    from app.services.catalog_query import list_products as query_products

    return [
        ProductResponse(
            product_code=v.product_code,
            name=v.name,
            category=v.category,
            price=v.price,
            stock=v.stock,
        )
        for v in query_products(db)
    ]


@router.get("/{product_code}", response_model=ProductResponse)
def get_product(product_code: str, db: Session = Depends(get_db)) -> ProductResponse:
    p = db.query(Product).filter(Product.product_code == product_code).first()
    if p is None:
        raise NotFoundErr(f"상품을 찾을 수 없습니다: {product_code}")
    return _to_response(p)
