"""SqlCatalog — CatalogPort의 SQLAlchemy 구현(미리보기 읽기전용, Phase 6)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.application.commerce import ProductInfo
from app.db.models import Inventory, Product


class SqlCatalog:
    """CatalogPort 구현. 요청 스코프 세션을 주입받아 상품/재고를 읽는다(쓰기 없음)."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_product(self, code: str) -> ProductInfo | None:
        p = self._db.query(Product).filter(Product.product_code == code).first()
        if p is None:
            return None
        return ProductInfo(product_id=p.id, product_code=p.product_code, name=p.name, price=p.price)

    def get_stock(self, product_id: int) -> int:
        inv = self._db.query(Inventory).filter(Inventory.product_id == product_id).first()
        return inv.stock if inv else 0
