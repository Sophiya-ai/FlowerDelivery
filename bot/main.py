import asyncio
import logging
import sqlite3  # Импортируем sqlite3

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import BOT_TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

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


@dp.message(CommandStart())
async def start(message: Message):
    # Получаем список аргументов из текста сообщения (message.text содержит полный текст сообщения, включая команду /start)
    args = message.text.split()[1:]
    user_id_txt = args[0] if args else None # Берем первый аргумент, если он есть
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

            if user_id:
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
                """, (message.from_user.id, message.from_user.username, message.from_user.first_name,
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

        else:
                # ID пользователя отсутствует, пользователь запустил бота без подключения к сайту
                await message.reply(
                    "Привет! Чтобы получать информацию о ваших заказах, подключитесь к боту на нашем сайте.")

        except sqlite3.Error as e:
            logging.error(f"Ошибка при работе с БД: {e}")  # Логируем ошибки БД
            await message.reply("Произошла ошибка при подключении к вашему аккаунту. Попробуйте позже.")

        finally:
            conn.close()

    else:
        await message.reply("Произошла ошибка при подключении к базе данных. Попробуйте позже.")



async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())