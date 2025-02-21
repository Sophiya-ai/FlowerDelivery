import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import web
from .main import main  # Импортируйте ваши функции
from aiogram import types


# Фикстура для мокирования Bot
@pytest.fixture
def mock_bot():
    bot = AsyncMock()  # Использовать AsyncMock для асинхронных методов
    return bot


# Фикстура для мокирования Message
@pytest.fixture
def mock_message():
    message = AsyncMock()
    message.from_user = MagicMock(id=123, username='testuser', first_name='Test', last_name='User')
    message.chat.id = 456
    return message


# Фикстура для мокирования create_db_connection
@pytest.fixture
def mock_create_db_connection():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    return conn, cursor


# Тест для команды /start
@pytest.mark.asyncio
async def test_start_valid_user(mock_bot, mock_message, mock_create_db_connection):
    # Arrange
    mock_message.text = "/start 1"  # Симулируем команду с user_id = 1
    mock_create_db_connection_return, mock_cursor = mock_create_db_connection
    with patch('bot.create_db_connection', return_value=mock_create_db_connection_return):
        mock_cursor.fetchone.side_effect = [  # Симулируем ответы БД
            (1,),  # user_exists
            None,  # existing_user
            ('TestName',),  # user_data
        ]
        # Act
        await main.start(mock_message)

        # Assert
        mock_bot.send_message.assert_called_with(chat_id=456,
                                                 text="Привет, TestName! Вы успешно подключили свой аккаунт. Теперь вы будете получать уведомления.")


@pytest.mark.asyncio
async def test_start_invalid_user_id(mock_bot, mock_message):
    mock_message.text = "/start invalid_id"
    await main.start(mock_message)
    mock_bot.send_message.assert_called_with(chat_id=456,
                                             text="Неверный формат ID пользователя. Пожалуйста, используйте ссылку на нашем сайте в Личном кабинете.")


# Тест для обработчика notify
@pytest.mark.asyncio
async def test_notify_success(mock_bot):
    # Arrange
    mock_request = AsyncMock()
    mock_request.json.return_value = {'telegram_id': 789, 'order_id': '12345', 'new_status': 'Shipped'}

    # Act
    response = await main.notify(mock_request)

    # Assert
    assert response.status == 200
    await mock_bot.send_message.assert_called_with(chat_id=789, text='Ваш заказ № 12345 изменил статус на: "Shipped"')


# Тест для обработчика order_notify (неполный, требует доработки под вашу логику)
@pytest.mark.asyncio
async def test_order_notify_success(mock_bot):
    # Arrange
    mock_request = AsyncMock()
    mock_request.json.return_value = {
        'telegram_id': 789,
        'order_id': '67890',
        'notes': 'Some notes',
        'address': 'Test Address',
        'total_price': '100.00',
        'order_items': ['Item 1', 'Item 2'],
        'image_urls': [],
        'message_about_time': 'Delivery in 2 hours'
    }

    # Act
    response = await main.order_notify(mock_request)

    # Assert
    assert response.status == 200
    # Добавьте более конкретные проверки для send_message и send_photo
