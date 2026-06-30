from __future__ import annotations

import logging
import os
from html import escape

import telebot
from telebot import types

logger = logging.getLogger(__name__)


def _validate_bot_settings() -> tuple[str, str]:
    token = os.getenv("TELEGRAM_API_KEY", "").strip()
    mini_app_url = os.getenv("TELEGRAM_MINI_APP_URL", "").strip()

    if not token:
        raise ValueError("TELEGRAM_API_KEY is required to run the Telegram bot")
    if not mini_app_url:
        raise ValueError("TELEGRAM_MINI_APP_URL is required to open the mini app")

    return token, mini_app_url


def _build_start_keyboard(mini_app_url: str) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)

    # Single reliable fallback button: opens Mini App URL directly.
    # This works even when WebApp launch constraints are not configured.
    keyboard.add(
        types.InlineKeyboardButton(
            text="Open Global Avicola Mini App",
            url=mini_app_url,
        )
    )

    return keyboard


def create_bot() -> telebot.TeleBot:
    token, mini_app_url = _validate_bot_settings()
    bot = telebot.TeleBot(token=token, parse_mode="HTML")

    @bot.message_handler(commands=["start"])
    def start_handler(message: types.Message) -> None:
        user_name = escape(message.from_user.first_name) if message.from_user else "there"
        greeting = (
            f"Hello, {user_name}!\n\n"
            "Welcome to Global Avicola.\n"
            "Tap the button below to open the mini app."
        )
        bot.send_message(
            chat_id=message.chat.id,
            text=greeting,
            reply_markup=_build_start_keyboard(mini_app_url),
        )

    return bot


def run_bot() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    bot = create_bot()
    logger.info("Starting Telegram bot polling")
    bot.infinity_polling(skip_pending=True, allowed_updates=["message"])


if __name__ == "__main__":
    run_bot()
