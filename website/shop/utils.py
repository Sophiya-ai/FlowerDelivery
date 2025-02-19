import asyncio

from celery import shared_task
from aiogram import Bot
from django.conf import settings


@shared_task
def send_telegram_message(telegram_id, message):
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        asyncio.run(bot.send_message(chat_id=telegram_id, text=message))
    except Exception as e:
        print(f"Ошибка отправки сообщения в Telegram: {e}")