import asyncio
import logging
import io
import sqlite3  # Импортируем sqlite3
import aiohttp
from aiohttp import web
from aiogram.client.session.aiohttp import AiohttpSession

from aiogram.filters import Command
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message

from config import BOT_TOKEN


# Используем асинхронную функцию `main` для инициализации и запуска бота
async def main():
    # Create an aiohttp session
    session = AiohttpSession()

    # Initialize bot and dispatcher with context
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()

    # Настройка логирования
    logging.basicConfig(level=logging.INFO)

    DATABASE_URL = "../db/db.sqlite3"

    def create_db_connection():
        conn = None
        try:
            conn = sqlite3.connect(DATABASE_URL)
            logging.info("Подключение к БД успешно")  # Логируем успешное подключение
        except sqlite3.Error as e:
            logging.error(f"Ошибка при подключении к БД: {e}")
            print(e)
        return conn

    @dp.message(Command(commands=['start']))
    async def start(message: Message):
        # Получаем список аргументов из текста сообщения (message.text содержит полный текст сообщения,
        # включая команду /start)
        args = message.text.split()[1:]
        user_id_txt = args[0] if args else None  # Берем первый аргумент, если он есть

        if not user_id_txt or not user_id_txt.isdigit():
            await message.reply("Неверный формат ID пользователя. Пожалуйста, "
                                "используйте ссылку на нашем сайте в Личном кабинете.")
            return

        user_id = int(user_id_txt)

        conn = create_db_connection()  # соединение с БД

        if conn is not None:
            cursor = conn.cursor()
            try:
                # Проверяем, существует ли пользователь с таким ID среди пользователей
                cursor.execute("SELECT id FROM shop_UserProfile WHERE id = ?", (user_id,))
                user_exists = cursor.fetchone()

                if not user_exists:
                    await message.reply("Пользователь с таким ID не найден.")
                    return

                # Проверяем, есть ли уже пользователь с таким telegram_id
                cursor.execute("SELECT telegram_id FROM shop_BotUser WHERE telegram_id = ?", (message.from_user.id,))
                existing_user = cursor.fetchone()
                if existing_user:
                    await message.reply(
                        f"Привет! Вы уже подключены к вашему аккаунту на сайте. "
                        f"Теперь вы будете получать уведомления о ваших заказах.")
                    return

                # Если ID пользователя с сайта получено, сохраняем данные в таблицу BotUser
                cursor.execute("""
                                            INSERT INTO shop_BotUser (telegram_id, username, first_name, last_name)
                                            VALUES (?, ?, ?, ?)
                                        """,
                               (message.from_user.id, message.from_user.username, message.from_user.first_name,
                                message.from_user.last_name))

                # Обновляем UserProfile
                cursor.execute(""" UPDATE shop_UserProfile SET telegram_user_id = ? WHERE id = ?
                                                            """, (message.from_user.id, user_id,))
                conn.commit()

                # Получаем имя пользователя для приветствия
                cursor.execute("SELECT first_name FROM shop_UserProfile WHERE id = ?", (user_id,))
                user_data = cursor.fetchone()
                user_first_name = user_data[0] if user_data else "Пользователь"

                # Логируем создание ботюзера и связку IDs
                logging.info(f"Пользователь с ID {user_id} успешно связан с Telegram ID {message.from_user.id}")
                await message.reply(
                    f"Привет, {user_first_name}! Вы успешно подключили свой аккаунт. Теперь вы будете получать уведомления.")

            except sqlite3.Error as e:
                logging.error(f"Ошибка при работе с БД: {e}")  # Логируем ошибки БД
                await message.reply("Произошла ошибка при подключении к вашему аккаунту. Попробуйте позже.")

            finally:
                conn.close()

        else:
            await message.reply("Произошла ошибка при подключении к базе данных. Попробуйте позже.")


    async def notify(request):
        try:
            data = await request.json()
            telegram_id = data.get('telegram_id')
            order_id = data.get('order_id')
            new_status = data.get('new_status')

            if not telegram_id or not order_id or not new_status:
                return web.json_response({'error': 'Missing required fields'}, status=400)

            message = f'Ваш заказ № {order_id} изменил статус на: "{new_status}" '
            await bot.send_message(chat_id=telegram_id, text=message)
            return web.json_response({'status': 'success'})
        except Exception as e:
            logging.error(f'Ошибка при отправке сообщения: {e}')
            return web.json_response({'error': str(e)}, status=500)


    async def order_notify(request):
        try:
            data = await request.json()
            telegram_id = data.get('telegram_id')
            order_id = data.get('order_id')
            notes = data.get('notes')
            delivery_address = data.get('address')
            total_price = data.get('total_price')
            order_items = data.get('order_items')
            image_urls = data.get('image_urls')
            message_about_time = data.get('message_about_time')

            if not telegram_id or not order_id:
                return web.json_response({'error': 'Missing required fields'}, status=400)

            message = f"Ваш заказ №{order_id} успешно размещен!\n\n"
            message += f"Информация о доставке:\n {notes}\n\n"
            message += f"Адрес доставки: {delivery_address}\n"
            message += f"Общая сумма: {total_price}\n"
            message += "\nСостав заказа:\n"
            message += "\n".join(order_items)  # Добавляем информацию о каждой позиции заказа
            message += f'\n{message_about_time}'
            message += "\nВизуализация содержимого вашего заказа:"

            await bot.send_message(chat_id=telegram_id, text=message)
            # for url in image_urls:
            #     try:
            #         await bot.send_photo(chat_id=telegram_id, photo=url)
            #     except Exception as e:
            #         logging.error(f"Error sending photo {url}: {e}")
            async with aiohttp.ClientSession() as session_order:  # Используем aiohttp для асинхронных запросов
                for url in image_urls:
                    try:
                        # обходим проверку Content-Type. Экземпляр абстрактного класса InputFile напрямую не создается,
                        # InputFile - это абстрактный класс, и надо использовать его подклассы для отправки файлов.
                        # В aiogram есть разные подклассы InputFile для разных типов источников данных.
                        # Здесь, когда есть данные изображения в памяти (в переменной image_data),
                        # следует использовать types.BufferedInputFile
                        async with session_order.get(url) as response:
                            if response.status == 200:
                                image_data = await response.read()  # Читаем данные изображения
                                photo = types.BufferedInputFile(image_data,
                                                                filename='image.jpg')  # Используем BufferedInputFile
                                await bot.send_photo(chat_id=telegram_id, photo=photo)  # Отправляем InputFile
                                logging.info(f"Successfully sent photo {url} to telegram_id {telegram_id}")
                            else:
                                logging.error(
                                    f"Failed to fetch image from URL: {url} with status {response.status}")
                    except Exception as e:
                        logging.error(f"Error sending photo {url}: {e}")

            return web.json_response({'status': 'success'})
        except Exception as e:
            logging.error(f'Ошибка при отправке сообщения: {e}')
            return web.json_response({'error': str(e)}, status=500)

    # Set up aiohttp app
    app = web.Application()
    app.router.add_post('/notify', notify)
    app.add_routes([web.post('/ordernotify', order_notify)])

    # Run both the aiohttp app and the polling
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()

    # Start polling for Telegram bot
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())