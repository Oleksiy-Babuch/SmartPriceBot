"""HTTP fetching and conservative generic price extraction."""

from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; SmartPriceBot/1.0; "
        "+https://github.com/your-account/SmartPriceBot)"
    ),
    "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
}


class PriceNotFoundError(RuntimeError):
    pass


@retry(
    retry=retry_if_exception_type(httpx.HTTPError),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    stop=stop_after_attempt(3),
    reraise=True,
)
def fetch_page(url: str, timeout_seconds: float) -> str:
    response = httpx.get(url, headers=HEADERS, timeout=timeout_seconds, follow_redirects=True)
    response.raise_for_status()
    return response.text


def parse_price(value: str | int | float | Decimal) -> Decimal | None:
    text = str(value).replace("\u00a0", " ").strip()
    # Keep numerical characters only; Ukrainian pages commonly use both 1 299,00 and 1299.00.
    candidate = re.sub(r"[^0-9,.-]", "", text).replace("-", "")
    if not candidate:
        return None
    if candidate.count(",") == 1 and candidate.count(".") >= 1:
        candidate = candidate.replace(".", "").replace(",", ".")
    elif candidate.count(",") == 1:
        candidate = candidate.replace(",", ".")
    elif candidate.count(".") > 1:
        candidate = candidate.replace(".", "")
    try:
        price = Decimal(candidate)
    except InvalidOperation:
        return None
    return price if Decimal("0") < price < Decimal("10000000") else None


def _walk_json(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        rows = [value]
        for child in value.values():
            rows.extend(_walk_json(child))
        return rows
    if isinstance(value, list):
        rows: list[dict[str, Any]] = []
        for child in value:
            rows.extend(_walk_json(child))
        return rows
    return []


def _json_ld_price(soup: BeautifulSoup) -> Decimal | None:
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            payload = json.loads(tag.get_text(strip=True))
        except json.JSONDecodeError:
            continue
        for row in _walk_json(payload):
            offers = row.get("offers", row)
            candidates = offers if isinstance(offers, list) else [offers]
            for offer in candidates:
                if isinstance(offer, dict):
                    for field in ("price", "lowPrice"):
                        price = parse_price(offer.get(field, ""))
                        if price is not None:
                            return price
    return None


def extract_price(html: str, selector: str | None = None) -> Decimal:
    soup = BeautifulSoup(html, "html.parser")
    if selector:
        node = soup.select_one(selector)
        if node:
            for value in (node.get("content"), node.get_text(" ", strip=True)):
                price = parse_price(value or "")
                if price is not None:
                    return price
        raise PriceNotFoundError(f"No valid price found for configured selector: {selector}")

    price = _json_ld_price(soup)
    if price is not None:
        return price
    for selector in (
        'meta[itemprop="price"]',
        'meta[property="product:price:amount"]',
        '[itemprop="price"]',
        '[data-price]',
        '.price',
        '.product-price',
    ):
        node = soup.select_one(selector)
        if node:
            price = parse_price(node.get("content") or node.get("data-price") or node.get_text(" ", strip=True))
            if price is not None:
                return price
    raise PriceNotFoundError("No price detected. Configure price_selector for this store.")
