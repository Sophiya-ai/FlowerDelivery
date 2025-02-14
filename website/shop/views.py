from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

from .models import User, Category, Product, Order, OrderItem, Review, BotUser, BotOrder
from .forms import UserFormInOrderHistory
from django.conf import settings


def index(request):
    products = Product.objects.filter(is_available=True).order_by('name')
    paginator = Paginator(products, 6)  # Показывать 6 товаров на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'shop/index.html', {'products': page_obj})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('individual_data')  # Перенаправляем на главную страницу
            else:
                # Обработка ошибки аутентификации
                return render(request, 'shop/login.html', {'form': form, 'error': 'Неверное имя пользователя или пароль'})
    else:
        form = AuthenticationForm()
    return render(request, 'shop/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматически логиним после регистрации
            return redirect('home')  # Перенаправляем на главную страницу
    else:
        form = UserCreationForm()
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
            return redirect('individual_data') # Обновляем страницу
    else:
        form = UserFormInOrderHistory(instance=request.user)

    telegram_bot_url = f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start={request.user.id}"
    # Прописываем словари для передачи информации в html-шаблон
    return render(request, 'shop/order_history.html',
                  {'form': form, 'user': request.user, 'telegram_bot_url': telegram_bot_url})
