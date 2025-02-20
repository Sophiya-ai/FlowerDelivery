import logging
from datetime import date, datetime
from aiogram import types

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import permission_required
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth import get_user_model  # Импортирована функция get_user_model из django.contrib.auth,
                                                # которая позволяет получить текущую модель пользователя,
                                                # указанную в AUTH_USER_MODEL
from django.db.models import Avg
from django.urls import reverse
from asgiref.sync import sync_to_async

from .models import Category, Product, Order, OrderItem, Review
from .forms import UserFormInOrderHistory, UserProfileCreationForm, ReviewForm, AdminForm
from .utils import send_telegram_message  # Импортируем функции

User = get_user_model()
logger = logging.getLogger(__name__)


def index(request):
    products = Product.objects.all().order_by('-is_available')
    paginator = Paginator(products, 6)  # Показывать 6 товаров на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    telegram_bot_url = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={request.user.id}"

    products_ratings = {}  # словарь средних рейтингов

    for product in page_obj:  # Перебираем только товары на текущей странице

        # Благодаря определению related_name="reviews" в модели Review на ForeignKey к Product,
        # получаем все отзывы, связанные с данным продуктом. вычисляет средний рейтинг для каждого товара,
        # используя связь product.reviews и агрегирующую функцию Avg('rating'). Результат сохраняется
        # в словаре products_ratings, где ключом является product.id
        average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
        if average_rating is None:  # Если у продукта нет отзывов, то рейтинг равен 0
            average_rating = 0

        products_ratings[product.id] = average_rating  # в products_ratings теперь хранится id: рейтинг
    return render(request, 'shop/index.html', {'telegram_bot_url': telegram_bot_url,
                                               'products': page_obj,
                                               'products_ratings': products_ratings})


def catalog_view(request):
    categories = Category.objects.all()
    products_by_category = {}
    products_ratings = {}  # словарь средних рейтингов

    for category in categories:
        products_by_category[category] = Product.objects.filter(category=category).order_by('-is_available')

        for product in products_by_category[category]:  # Перебираем только товары текущей категории

            # Благодаря определению related_name="reviews" в модели Review на ForeignKey к Product,
            # получаем все отзывы, связанные с данным продуктом. вычисляет средний рейтинг для каждого товара,
            # используя связь product.reviews и агрегирующую функцию Avg('rating'). Результат сохраняется
            # в словаре products_ratings, где ключом является product.id
            average_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
            if average_rating is None:  # Если у продукта нет отзывов, то рейтинг равен 0
                average_rating = 0

            products_ratings[product.id] = average_rating  # в products_ratings теперь хранится id: рейтинг

    context = {
        'categories': categories,
        'products_by_category': products_by_category,
        'products_ratings': products_ratings,
    }
    return render(request, 'shop/categories_view.html', context)


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if username == 'admin':  # Проверяем логин
                    return redirect('adminpage')  # Перенаправляем на страницу adminpage
                else:
                    return redirect('individual_data')  # иначе перенаправляем на Личную страницу
            else:
                # Обработка ошибок формы
                messages.error(request, "Неверное имя пользователя или пароль.")  # Добавлено сообщение об ошибке
        else:
            # Обработка ошибок формы
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = AuthenticationForm()
    return render(request, 'shop/login.html', {'form': form})


def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, pk=product_id)
        total_for_product = product.price * quantity
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'total': total_for_product,
        })
        total_price += total_for_product

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'today': date.today().strftime('%Y-%m-%d'),
    }
    return render(request, 'shop/cart.html', context)


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart = request.session.get('cart', {})
    quantity = 1
    if product_id in cart:
        cart[product_id] += quantity
    else:
        cart[product_id] = quantity
    request.session['cart'] = cart
    messages.success(request, f'Товар {product.name} добавлен в корзину!')

    # остаемся на той странице, с которой заказывали
    referer = request.META.get('HTTP_REFERER', '')
    if 'home' in referer:
        return redirect('home')
    elif 'catalog' in referer:
        return redirect('catalog')
    else:
        # Если реферер не определён, можно выбрать действие по умолчанию
        return redirect('home')  # или 'catalog', в зависимости от ваших требований


def update_cart(request, product_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity'))
        if quantity > 0:
            cart = request.session.get('cart', {})
            cart[str(product_id)] = quantity
            request.session['cart'] = cart
            messages.success(request, "Количество товара обновлено")
    return redirect('cart')


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id = str(product_id)  # Делаем в строкой для соответствия ключам в корзине

    if product_id in cart:
        del cart[product_id]
        request.session['cart'] = cart
        messages.success(request, "Товар удален из корзины")
    return redirect('cart')


@login_required
async def process_order(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if not cart:
            messages.error(request, "Корзина пуста.")
            return redirect('cart')

        delivery_address = request.POST.get('delivery_address')
        order_date_str = request.POST.get('order_date')
        delivery_time_str = request.POST.get('delivery_time')
        phone_number = request.POST.get('phone_number')

        try:
            order_date = datetime.strptime(order_date_str, '%Y-%m-%d').date()
            delivery_time = datetime.strptime(delivery_time_str, '%H:%M').time()
        except ValueError:
            messages.error(request, "Неверный формат даты или времени.")
            return redirect('cart')

        # Получаем Telegram ID пользователя, если он есть
        try:
            user_profile = request.user  # Получаем пользователя
            bot_user = await sync_to_async(
                lambda: user_profile.telegram_user)()  # Получаем связанный BotUser через поле telegram_user
            telegram_id = bot_user.telegram_id if bot_user else None
        except Exception as e:
            telegram_id = None
            logger.error(f"Ошибка при получении telegram_id: {e}")
        logger.info(f"Attempting to send message to telegram_id: {telegram_id}")

        total_price = 0
        order = await sync_to_async(Order.objects.create)(
            user=request.user,
            delivery_address=delivery_address,
            order_date=order_date,
            total_price=0,
            notes=f'Телефон: {phone_number}, Дата доставки: {order_date}, Время доставки: {delivery_time}'
        )

        order_items = []
        image_urls = []  # Список URL изображений

        for product_id, quantity in cart.items():
            try:
                product = await sync_to_async(Product.objects.get)(pk=product_id)
            except Product.DoesNotExist:
                logger.error(f"Product with id {product_id} not found.")
                messages.error(request, f"Товар с id {product_id} не найден.")  # Сообщаем об ошибке
                continue  # Переходим к следующему товару

            price = product.price
            total_for_product = price * quantity
            total_price += total_for_product

            await sync_to_async(OrderItem.objects.create)(
                order=order,
                product=product,
                quantity=quantity,
                price=price
            )
            order_items.append(f"- {product.name} ({quantity} шт.) - {product.price} руб.")

            if product.image:
                image_url = request.build_absolute_uri(product.image.url)
                logger.info(f"Generated image URL: {image_url}")
                image_urls.append(image_url)

        order.total_price = total_price
        await sync_to_async(order.save)()

        del request.session['cart']

        now = datetime.now().time()
        start_time = datetime.strptime('08:00', '%H:%M').time()
        end_time = datetime.strptime('18:00', '%H:%M').time()

        if telegram_id:
            message = f"Ваш заказ №{order.id} успешно размещен!\n\n"
            message += f"Информация о доставке:\n {order.notes}\n\n"
            message += f"Адрес доставки: {order.delivery_address}\n"
            message += f"Общая сумма: {order.total_price}\n"
            message += "\nСостав заказа:\n"
            message += "\n".join(order_items)  # Добавляем информацию о каждой позиции заказа
            if not start_time <= now <= end_time:
                message += (
                    "\nВаш заказ принят, но будет обработан в рабочее время (с 8:00 до 18:00). О смене статуса "
                    "будет сообщено.\n")
            message += "\n\nВизуализация содержимого вашего заказа:"

            await send_telegram_message(telegram_id, message)  # Вызываем функцию напрямую

            # Отправляем каждое изображение отдельно
            if image_urls:
                for image_url in image_urls:
                    logger.info(f"Отправка изображения: {image_url}")
                    await send_telegram_message(telegram_id, image_url)  # Отправляем каждое изображение отдельно
            else:
                logger.info("Список URL изображений пуст, изображения не отправляются.")
        else:
            logger.warning(
                f"Telegram ID не найден для пользователя {request.user.username}. Уведомление не отправлено.")

        return redirect('order_success', order_id=order.id)  # Редирект на страницу успеха
    else:
        return redirect('cart')  # Обработка GET запроса


def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, 'shop/order_success.html', {'order': order})


def register(request):
    if request.method == 'POST':
        form = UserProfileCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect('login')  # Перенаправляем на главную страницу
    else:
        form = UserProfileCreationForm()
    return render(request, 'shop/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')  # Перенаправляем на главную страницу


# Форма привязана к текущему пользователю (instance=request.user), что позволяет отображать и редактировать его данные
# Декоратор @login_required гарантирует, что только аутентифицированные пользователи могут получить доступ к странице

# request.user.id: ID пользователя на сайте, который передается боту в качестве параметра start.
# Это позволит боту идентифицировать пользователя, когда он запустит бота.

# https://t.me/{bot_username}?start={user_id} - Это стандартная схема deeplink для Telegram ботов,
# при переходе по которой бот откроется и получит user_id в качестве аргумента команды start
@login_required
def view_orders_and_individual_data(request):
    if request.method == 'POST':
        form = UserFormInOrderHistory(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('individual_data')  # Обновляем страницу
    else:
        form = UserFormInOrderHistory(instance=request.user)

    telegram_bot_url = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={request.user.id}"

    # Получаем историю заказов пользователя и сортируем по дате (сначала новые за счет order_by('-order_date'))
    order_history_data = Order.objects.filter(user=request.user).order_by('-order_date')

    # Прописываем словари для передачи информации в html-шаблон
    return render(request, 'shop/order_history.html',
                  {'form': form,
                   'user': request.user,
                   'telegram_bot_url': telegram_bot_url,
                   'order_history': order_history_data})


@login_required
def adminpage_view(request):
    if request.method == 'POST':
        form = AdminForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('adminpage')  # Обновляем страницу
    else:
        form = AdminForm(instance=request.user)

    # Получаем историю заказов и сортируем по дате (сначала новые за счет order_by('-order_date'))
    order_history_data = Order.objects.order_by('-order_date')

    # Прописываем словари для передачи информации в html-шаблон
    return render(request, 'shop/admin.html',
                  {'form': form,
                   'user': request.user,
                   'order_history': order_history_data})


# def update_order_status(request, order_id):
#     order = get_object_or_404(Order, id=order_id)
#     old_status = order.status
#
#     if request.method == 'POST':
#         new_status = request.POST.get('status')
#         order.status = new_status
#         order.save()
#
#         # Получаем Telegram ID пользователя, если он есть
#         try:
#             user = order.user
#             bot_user = user.telegram_user
#             if bot_user:
#                 telegram_id = bot_user.telegram_id
#         except Exception as e:
#             telegram_id = None
#             logger.error(f"Ошибка при получении telegram_id: {e}")
#
#         logger.info(f"Attempting to send message to telegram_id: {telegram_id}")
#
#         if telegram_id:
#             message = f"Статус вашего заказа №{order.id} изменен!\n\n"
#             message += f"Старый статус: {old_status}\n"
#             message += f"Новый статус: {order.get_status_display()}\n"
#             send_telegram_message(telegram_id, message)
#
#         return redirect('adminpage')  # обратно на страницу с историей заказов
#     return redirect('adminpage')


@permission_required('shop.change_order')
async def update_order_status(request, order_id):
    order = await sync_to_async(get_object_or_404)(Order, id=order_id)
    old_status = order.status

    if request.method == 'POST':
        new_status = request.POST.get('status')
        order.status = new_status
        await sync_to_async(order.save)()

        # Получаем Telegram ID пользователя, если он есть
        try:
            user = order.user
            bot_user = await sync_to_async(lambda: user.telegram_user)()
            telegram_id = bot_user.telegram_id if bot_user else None
        except Exception as e:
            telegram_id = None
            logger.error(f"Ошибка при получении telegram_id: {e}")

        logger.info(f"Attempting to send message to telegram_id: {telegram_id}")

        if telegram_id:
            message = (
                f"Статус вашего заказа №{order.id} изменен!\n\n"
                f"Старый статус: {old_status}\n"
                f"Новый статус: {order.get_status_display()}\n"
            )
            await send_telegram_message(telegram_id, message)  # Вызываем функцию напрямую
        else:
            logger.warning(f"Telegram ID не найден для пользователя {order.user.username}.  Уведомление не отправлено.")

        logger.info(
            f"Пользователь {request.user.username} изменил статус заказа {order.id} с {old_status} на {new_status}")  # Логируем изменение статуса

        return redirect(reverse('update_order_status', kwargs={'order_id': order_id}))  # Используем reverse для формирования URL
    return redirect(reverse('update_order_status', kwargs={'order_id': order_id}))


def add_to_cart_once_more(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    cart = request.session.get('cart', {})

    for item in order.items.all():
        product_id = str(item.product.id)
        quantity = item.quantity

        if product_id in cart:
            cart[product_id] += quantity
        else:
            cart[product_id] = quantity

    request.session['cart'] = cart
    messages.success(request, f'Товары из заказа №{order.id} добавлены в корзину!')
    return redirect('cart')


def watch_review(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    reviews = Review.objects.filter(product=product).order_by('-date')

    return render(request, 'shop/product_reviews.html', {'product': product, 'reviews': reviews})


def add_review(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product
            review.save()
            messages.success(request, "Спасибо за ваш отзыв!")
            return redirect('product_reviews', product_id=product_id)  # Обновляем страницу
    else:
        form = ReviewForm()
    return render(request, 'shop/review_form.html', {
        'form': form,
        'product': product})
