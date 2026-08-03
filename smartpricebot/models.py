"""Domain models used by the price tracker."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    url: str
    currency: str = "UAH"
    target_price_uah: Decimal | None = None
    price_selector: str | None = None


@dataclass(frozen=True)
class PriceObservation:
    product_id: str
    product_name: str
    price: Decimal
    currency: str
    url: str
    checked_at: str

    @classmethod
    def now(cls, product: Product, price: Decimal) -> "PriceObservation":
        return cls(
            product_id=product.id,
            product_name=product.name,
            price=price,
            currency=product.currency,
            url=product.url,
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict[str, str]:
        payload = asdict(self)
        payload["price"] = str(self.price)
        return payload
