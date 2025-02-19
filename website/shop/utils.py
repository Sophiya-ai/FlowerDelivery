from celery import shared_task
from aiogram import Bot
from django.conf import settings
from aiogram import types
import asyncio
import logging
import requests

logger = logging.getLogger(__name__)

# Глобальная переменная для хранения event loop
_event_loop = None


def get_event_loop():
    """Получает существующий event loop или создает новый"""
    global _event_loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


@shared_task
def send_telegram_message(telegram_id, message):
    try:
        bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        loop = get_event_loop()  # Получаем event loop
        # Проверяем, является ли сообщение URL изображения (теперь проверяем наличие http/https)
        if message.startswith("http://") or message.startswith("https://"):
            try:
                # Используем requests для проверки URL и Content-Type
                response = requests.get(message, stream=True)
                response.raise_for_status()  # Вызываем исключение для HTTP ошибок
                content_type = response.headers.get('Content-Type')

                if content_type and content_type.startswith('image'):
                    # Отправляем изображение в Telegram
                    loop.run_until_complete(bot.send_photo(chat_id=telegram_id, photo=message))
                    logger.info(f"Successfully sent photo to telegram_id {telegram_id}")
                else:
                    logger.error(
                        f"Ошибка: URL не ведет к изображению или Content-Type не image. Content-Type: {content_type}, URL: {message}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при запросе URL: {e}")
            except Exception as e:
                logger.error(f"Ошибка при отправке фото: {e}")

        else:
            try:
                loop.run_until_complete(bot.send_message(chat_id=telegram_id, text=message))
                logger.info(f"Successfully sent text to telegram_id {telegram_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке текста: {e}")
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения в Telegram: {e}")
