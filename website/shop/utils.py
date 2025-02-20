from aiogram import Bot, types
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
import logging
import aiohttp
from aiohttp import FormData

from django.conf import settings

logger = logging.getLogger(__name__)

# Создаем экземпляр бота один раз при запуске приложения
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)


# Отправляет текстовое или медиа-сообщение в Telegram
async def send_telegram_message(telegram_id, message):
    try:
        if message.startswith("http://") or message.startswith("https://"):
            # Отправка изображения
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(message) as resp:
                        resp.raise_for_status()
                        content_type = resp.headers.get('Content-Type')

                        if content_type and content_type.startswith('image/'):  # Проверяем Content-Type
                            # Отправляем изображение с помощью aiohttp
                            try:
                                async with session.get(message) as resp:
                                    resp.raise_for_status()
                                    image_data = await resp.read()

                                    form = FormData()  # Данные для отправки изображения формируются с использованием FormData.
                                    # Это позволяет правильно указать chat_id, имя файла и content_type
                                    form.add_field('chat_id', str(telegram_id))
                                    form.add_field('photo',
                                                   image_data,
                                                   filename='image.jpg',
                                                   content_type=content_type)

                                    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendPhoto"

                                    async with session.post(url, data=form) as photo_resp:
                                        photo_resp.raise_for_status()
                                        result = await photo_resp.json()
                                        if result['ok']:
                                            logger.info(f"Successfully sent photo to telegram_id {telegram_id}")
                                        else:
                                            logger.error(f"Failed to send photo to telegram_id {telegram_id}: {result}")

                            except Exception as e:
                                logger.error(f"Error sending photo via aiohttp: {e}")

                        else:
                            logger.error(
                                f"URL не ведет к изображению или Content-Type не image. Content-Type: {content_type}, URL: {message}")

            except aiohttp.ClientError as e:
                logger.error(f"Ошибка при запросе URL: {e}")
            except TelegramForbiddenError:
                logger.error(f"Telegram user {telegram_id} blocked the bot.")
            except TelegramBadRequest as e:
                logger.error(f"Telegram Bad Request for {telegram_id}: {e}")
            except Exception as e:
                logger.error(f"Error sending photo to telegram_id {telegram_id}: {e}")

        else:
            # Отправка текстового сообщения
            try:
                await bot.send_message(chat_id=telegram_id, text=message)
                logger.info(f"Successfully sent text to telegram_id {telegram_id}")
            except TelegramForbiddenError:
                logger.error(f"Telegram user {telegram_id} blocked the bot.")
            except TelegramBadRequest as e:
                logger.error(f"Telegram Bad Request for {telegram_id}: {e}")
            except Exception as e:
                logger.error(f"Error sending text to telegram_id {telegram_id}: {e}")

    except Exception as e:
        logger.error(f"Error sending message to telegram_id {telegram_id}: {e}")
