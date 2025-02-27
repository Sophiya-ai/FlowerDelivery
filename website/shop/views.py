import logging
from datetime import date, datetime
from aiogram import types
import asyncio
import requests

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth import get_user_model  # Импортирована функция get_user_model из django.contrib.auth,
                                                # которая позволяет получить текущую модель пользователя,
                                                # указанную в AUTH_USER_MODEL
from django.db.models import Avg
from django.contrib.auth import update_session_auth_hash

from .models import Category, Product, Order, OrderItem, Review
from .forms import UserFormInOrderHistory, UserProfileCreationForm, ReviewForm, AdminForm


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
def process_order(request):
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
            bot_user = user_profile.telegram_user  # Получаем связанный BotUser через поле telegram_user
            telegram_id = bot_user.telegram_id if bot_user else None
        except Exception as e:
            telegram_id = None
            logger.error(f"Ошибка при получении telegram_id: {e}")
        logger.info(f"Attempting to send message to telegram_id: {telegram_id}")

        total_price = 0
        order = Order.objects.create(
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
                product = Product.objects.get(pk=product_id)
            except Product.DoesNotExist:
                logger.error(f"Product with id {product_id} not found.")
                messages.error(request, f"Товар с id {product_id} не найден.")  # Сообщаем об ошибке
                continue  # Переходим к следующему товару

            price = product.price
            total_for_product = price * quantity
            total_price += total_for_product

            OrderItem.objects.create(
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
        order.save()

        del request.session['cart']

        now = datetime.now().time()
        start_time = datetime.strptime('08:00', '%H:%M').time()
        end_time = datetime.strptime('18:00', '%H:%M').time()

        message_about_time = ''
        if not start_time <= now <= end_time:
            message_about_time = (
                "\nВаш заказ принят, но будет обработан в рабочее время (с 8:00 до 18:00). О смене статуса "
                "будет сообщено.\n")

        if not image_urls:
            logger.info("Список URL изображений пуст, изображения не отправляются.")

        if telegram_id:

            data = {
                'telegram_id': telegram_id,
                'order_id': order.id,
                'notes': order.notes,
                'address': order.delivery_address,
                'total_price': float(order.total_price),
                'order_items': order_items,
                'image_urls': image_urls,
                'message_about_time': message_about_time,
            }
            try:
                # Отправка POST-запроса к вашему боту
                response = requests.post('http://127.0.0.1:8080/ordernotify', json=data)
                response.raise_for_status()
            except requests.RequestException as e:
                # Логируем ошибки
                logger.error(f"Ошибка при отправке уведомления о заказе: {e}")

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
            form.save()
            return redirect('login')  # Перенаправляем на страницу входа
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
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password and confirm_password:
            if new_password == confirm_password:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Чтобы не выкинуть пользователя из сессии
                messages.success(request, 'Пароль успешно изменен.')
            else:
                messages.error(request, 'Пароли не совпадают.')

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
        
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password and confirm_password:
            if new_password == confirm_password:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Чтобы не выкинуть пользователя из сессии
                messages.success(request, 'Пароль успешно изменен.')
            else:
                messages.error(request, 'Пароли не совпадают.')

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



@login_required
def update_order_status(request, order_id):
    # Используем prefetch_related для асинхронной загрузки bot_user
    order = get_object_or_404(
        Order.objects.prefetch_related('user__telegram_user'),  # Асинхронно загружаем bot_user
        id=order_id)
    old_status = order.status

    if request.method == 'POST':
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()

        # Получаем Telegram ID пользователя, если он есть
        telegram_id = None  # Инициализируем telegram_id
        try:
            user_profile = order.user  # Получаем пользователя
            bot_user = user_profile.telegram_user  # Получаем связанный BotUser

            telegram_id = bot_user.telegram_id if bot_user else None
        except Exception as e:
            logger.error(f"Ошибка при получении telegram_id: {e}")

        logger.info(f"Attempting to send message to telegram_id: {telegram_id}")

        data = {
            'telegram_id': telegram_id,  # ID пользователя из Telegram
            'order_id': order.id,
            'new_status': order.status,
        }
        try:
            # Отправка POST-запроса к вашему боту
            response = requests.post('http://127.0.0.1:8080/notify', json=data)
            response.raise_for_status()
        except requests.RequestException as e:
            # Логируем ошибки
            logger.error(f"Ошибка при отправке уведомления о смене статуса: {e}")

        return redirect('adminpage')  # обратно на страницу с историей заказов
    return redirect('adminpage')




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
