"""Price-check orchestration and change-aware alert decisions."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from decimal import Decimal

from .history import HistoryStore
from .models import PriceObservation, Product
from .notifier import TelegramNotifier
from .scraper import extract_price, fetch_page


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class CheckResult:
    product: Product
    observation: PriceObservation | None
    previous_price: Decimal | None
    error: str | None = None


class PriceTracker:
    def __init__(
        self,
        products: list[Product],
        history: HistoryStore,
        notifier: TelegramNotifier,
        request_timeout_seconds: float,
    ) -> None:
        self.products = products
        self.history = history
        self.notifier = notifier
        self.request_timeout_seconds = request_timeout_seconds

    def check_product(self, product: Product) -> CheckResult:
        if not product.url:
            return CheckResult(product, None, None, "URL is not configured")
        try:
            previous = self.history.latest(product.id)
            previous_price = Decimal(previous["price"]) if previous else None
            html = fetch_page(product.url, self.request_timeout_seconds)
            observation = PriceObservation.now(product, extract_price(html, product.price_selector))
            self.history.append(observation)
            return CheckResult(product, observation, previous_price)
        except Exception as error:  # A failure for one shop must not stop other checks.
            LOGGER.exception("Price check failed for %s", product.id)
            return CheckResult(product, None, None, str(error))

    def check_all(self) -> list[CheckResult]:
        return [self.check_product(product) for product in self.products]

    async def check_and_notify(self) -> list[CheckResult]:
        results = await asyncio.to_thread(self.check_all)
        for result in results:
            if result.observation is None:
                continue
            if self._should_alert(result):
                await self.notifier.send(self._message(result))
        return results

    @staticmethod
    def _should_alert(result: CheckResult) -> bool:
        assert result.observation is not None
        target_crossed = (
            result.product.target_price_uah is not None
            and result.previous_price is not None
            and result.previous_price > result.product.target_price_uah
            and result.observation.price <= result.product.target_price_uah
        )
        return result.previous_price is None or result.observation.price != result.previous_price or target_crossed

    @staticmethod
    def _message(result: CheckResult) -> str:
        assert result.observation is not None
        current = result.observation.price
        previous = result.previous_price
        if previous is None:
            title = "✅ Перша перевірка ціни"
            comparison = ""
        elif current < previous:
            title = "📉 Ціна знизилась"
            comparison = f"\nБуло: {previous} {result.product.currency}"
        elif current > previous:
            title = "📈 Ціна зросла"
            comparison = f"\nБуло: {previous} {result.product.currency}"
        else:
            title = "🎯 Цільова ціна досягнута"
            comparison = f"\nЦіль: {result.product.target_price_uah} UAH"
        return (
            f"{title}\n\n{result.product.name}\n"
            f"Зараз: {current} {result.product.currency}{comparison}\n"
            f"{result.product.url}"
        )
