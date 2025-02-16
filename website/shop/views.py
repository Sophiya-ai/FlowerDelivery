import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth import get_user_model  # Импортирована функция get_user_model из django.contrib.auth,
# которая позволяет получить текущую модель пользователя,
# указанную в AUTH_USER_MODEL

from .models import UserProfile, Category, Product, Order, OrderItem, Review, BotUser, BotOrder
from .forms import UserFormInOrderHistory, UserProfileCreationForm


User = get_user_model()
logger = logging.getLogger(__name__)


def index(request):
    products = Product.objects.all().order_by('-is_available')
    paginator = Paginator(products, 6)  # Показывать 6 товаров на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    telegram_bot_url = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={request.user.id}"
    return render(request, 'shop/index.html', {'telegram_bot_url': telegram_bot_url, 'products': page_obj})


def login_view(request):
    if request.method == 'POST':
        # ниже надо передавать request в качестве первого аргумента.
        # Это необходимо для правильной работы аутентификации с пользовательской моделью
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('individual_data')  # Перенаправляем на Личную страницу
            else:
                # Обработка ошибки аутентификации
                logger.warning(f"Authentication failed for username: {username}")
                return render(request, 'shop/login.html',
                              {'form': form, 'error': 'Неверное имя пользователя или пароль'})
    else:
        form = AuthenticationForm()
    return render(request, 'shop/login.html', {'form': form})


from django.shortcuts import render, redirect, get_object_or_404
from .models import Product
from django.contrib import messages


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
    return redirect('home')


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    if product_id in cart:
        del cart[product_id]
        request.session['cart'] = cart
        messages.success(request, "Товар удален из корзины")
    return redirect('cart')


def register(request):
    if request.method == 'POST':
        form = UserProfileCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматически логиним после регистрации
            return redirect('individual_data')  # Перенаправляем на главную страницу
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
