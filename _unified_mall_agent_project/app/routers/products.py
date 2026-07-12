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
    return [_to_response(p) for p in db.query(Product).all()]


@router.get("/{product_code}", response_model=ProductResponse)
def get_product(product_code: str, db: Session = Depends(get_db)) -> ProductResponse:
    p = db.query(Product).filter(Product.product_code == product_code).first()
    if p is None:
        raise NotFoundErr(f"상품을 찾을 수 없습니다: {product_code}")
    return _to_response(p)
