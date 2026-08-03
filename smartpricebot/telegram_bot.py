"""Interactive Telegram interface."""

from __future__ import annotations

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from .tracker import PriceTracker


def _allowed(update: Update, allowed_chat_ids: tuple[int, ...]) -> bool:
    return bool(update.effective_chat and update.effective_chat.id in allowed_chat_ids)


def build_application(token: str, allowed_chat_ids: tuple[int, ...], tracker: PriceTracker) -> Application:
    app = Application.builder().token(token).build()

    async def reject_unconfigured(update: Update) -> bool:
        if _allowed(update, allowed_chat_ids):
            return False
        if update.effective_message:
            await update.effective_message.reply_text("Доступ до цього бота не налаштований.")
        return True

    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await reject_unconfigured(update):
            return
        await update.effective_message.reply_text(
            "Команди:\n/check — перевірити ціни\n/status — останні збережені ціни\n"
            "/products — список товарів\n/id — ID цього чату"
        )

    async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_chat:
            await update.effective_message.reply_text(f"Chat ID: {update.effective_chat.id}")

    async def products_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await reject_unconfigured(update):
            return
        lines = [f"• {p.name}: {'налаштовано' if p.url else 'потрібне посилання'}" for p in tracker.products]
        await update.effective_message.reply_text("\n".join(lines) or "Товари не налаштовані.")

    async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await reject_unconfigured(update):
            return
        lines: list[str] = []
        for product in tracker.products:
            latest = tracker.history.latest(product.id)
            lines.append(f"• {product.name}: {latest['price']} {latest['currency']}" if latest else f"• {product.name}: ще не перевірено")
        await update.effective_message.reply_text("\n".join(lines) or "Немає товарів.")

    async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await reject_unconfigured(update):
            return
        await update.effective_message.reply_text("Перевіряю ціни…")
        results = await tracker.check_and_notify()
        successful = sum(item.observation is not None for item in results)
        failures = [f"{item.product.name}: {item.error}" for item in results if item.error]
        text = f"Готово: {successful}/{len(results)} перевірок успішні."
        if failures:
            text += "\n\nПомилки:\n" + "\n".join(failures)
        await update.effective_message.reply_text(text)

    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start", help_command))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("products", products_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("check", check_command))
    return app
