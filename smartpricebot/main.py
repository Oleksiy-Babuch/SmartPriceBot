"""CLI entry point: run a one-off check or the Telegram polling bot."""

from __future__ import annotations

import argparse
import asyncio
import logging

from .config import load_products, load_settings
from .history import HistoryStore
from .notifier import TelegramNotifier
from .telegram_bot import build_application
from .tracker import PriceTracker


def make_tracker() -> tuple[PriceTracker, object]:
    settings = load_settings()
    tracker = PriceTracker(
        products=load_products(settings.products_file),
        history=HistoryStore(settings.history_file),
        notifier=TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_ids),
        request_timeout_seconds=settings.request_timeout_seconds,
    )
    return tracker, settings


def main() -> None:
    parser = argparse.ArgumentParser(description="SmartPriceBot")
    parser.add_argument("command", choices=("check", "bot"), help="Run one check or start Telegram polling")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    tracker, settings = make_tracker()
    if args.command == "check":
        results = asyncio.run(tracker.check_and_notify())
        for result in results:
            if result.observation:
                print(f"OK {result.product.name}: {result.observation.price} {result.product.currency}")
            else:
                print(f"ERROR {result.product.name}: {result.error}")
        return
    if not settings.telegram_bot_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is required to run the bot.")
    if not settings.telegram_chat_ids:
        raise SystemExit("TELEGRAM_CHAT_IDS is required to protect bot commands.")
    build_application(settings.telegram_bot_token, settings.telegram_chat_ids, tracker).run_polling()


if __name__ == "__main__":
    main()
