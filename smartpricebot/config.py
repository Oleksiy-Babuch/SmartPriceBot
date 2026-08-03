"""Loading for environment variables and product definitions."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dotenv import load_dotenv

from .models import Product


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str | None
    telegram_chat_ids: tuple[int, ...]
    request_timeout_seconds: float
    products_file: Path
    history_file: Path


def load_settings() -> Settings:
    load_dotenv(PROJECT_ROOT / ".env")
    raw_ids = os.getenv("TELEGRAM_CHAT_IDS", "")
    chat_ids: list[int] = []
    for value in raw_ids.split(","):
        value = value.strip()
        if value:
            try:
                chat_ids.append(int(value))
            except ValueError as error:
                raise ValueError("TELEGRAM_CHAT_IDS must contain comma-separated numeric IDs.") from error
    timeout = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN") or None,
        telegram_chat_ids=tuple(chat_ids),
        request_timeout_seconds=timeout,
        products_file=PROJECT_ROOT / "config" / "products.toml",
        history_file=PROJECT_ROOT / "data" / "price_history.json",
    )


def load_products(products_file: Path) -> list[Product]:
    with products_file.open("rb") as handle:
        config = tomllib.load(handle)
    products: list[Product] = []
    identifiers: set[str] = set()
    for row in config.get("products", []):
        product_id = str(row["id"]).strip()
        if not product_id or product_id in identifiers:
            raise ValueError(f"Product id must be unique and non-empty: {product_id!r}")
        identifiers.add(product_id)
        target = str(row.get("target_price_uah", "")).strip()
        try:
            target_price = Decimal(target) if target else None
        except InvalidOperation as error:
            raise ValueError(f"Invalid target_price_uah for {product_id}.") from error
        products.append(
            Product(
                id=product_id,
                name=str(row["name"]).strip(),
                url=str(row.get("url", "")).strip(),
                currency=str(row.get("currency", "UAH")).upper(),
                target_price_uah=target_price,
                price_selector=str(row.get("price_selector", "")).strip() or None,
            )
        )
    return products
