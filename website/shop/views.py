from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string

from .models import User, Category, Product, Order, OrderItem, Review, BotUser, BotOrder


def index(request):
    return render(request, 'shop/index.html')
