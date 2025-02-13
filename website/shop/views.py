from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.paginator import Paginator

from .models import User, Category, Product, Order, OrderItem, Review, BotUser, BotOrder
from .forms import UserFormInOrderHistory


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
                return redirect('order_history')  # Перенаправляем на главную страницу
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
            return redirect('index')  # Перенаправляем на главную страницу
    else:
        form = UserCreationForm()
    return render(request, 'shop/register.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('index')  # Перенаправляем на главную страницу


def view_orders_and_individual_data(request):
    form = UserFormInOrderHistory()
    return render(request, 'shop/order_history.html', {'form': form})
