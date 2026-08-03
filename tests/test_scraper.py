from decimal import Decimal

import pytest

from smartpricebot.scraper import PriceNotFoundError, extract_price, parse_price


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("1 299,50 грн", Decimal("1299.50")), ("899 грн", Decimal("899")), ("0", None)],
)
def test_parse_price(raw, expected):
    assert parse_price(raw) == expected


def test_extracts_json_ld_offer_price():
    page = '<script type="application/ld+json">{"@type":"Product","offers":{"price":"1234.50"}}</script>'
    assert extract_price(page) == Decimal("1234.50")


def test_custom_selector_takes_priority():
    page = '<span class="current">777 грн</span><meta itemprop="price" content="888">'
    assert extract_price(page, ".current") == Decimal("777")


def test_missing_price_raises_helpful_error():
    with pytest.raises(PriceNotFoundError):
        extract_price("<html><body>none</body></html>")
