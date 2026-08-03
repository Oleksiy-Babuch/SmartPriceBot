"""Telegram message delivery used by scheduled checks."""

from __future__ import annotations

import logging

from telegram import Bot


LOGGER = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, token: str | None, chat_ids: tuple[int, ...]) -> None:
        self.token = token
        self.chat_ids = chat_ids

    async def send(self, message: str) -> None:
        if not self.token or not self.chat_ids:
            LOGGER.warning("Telegram credentials are missing; message not sent: %s", message)
            return
        async with Bot(self.token) as bot:
            for chat_id in self.chat_ids:
                await bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True)
