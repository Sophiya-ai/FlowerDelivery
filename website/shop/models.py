from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth.models import User


# Используем встроенную модель пользователя AbstractUser.
# Добавляем дополнительные поля - телефон, адрес и telegram_user
class UserProfile(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Номер телефона")
    address = models.TextField(blank=True, null=True, verbose_name="Адрес")
    type_of_user = models.CharField(
        max_length=20,
        choices=[
            ('company', 'Компания'),
            ('individual', 'Частное лицо')
        ],
        default='individual',
        verbose_name='Тип пользователя')
    telegram_user = models.OneToOneField('BotUser', on_delete=models.SET_NULL, null=True, blank=True,
                                         related_name='web_user', verbose_name="Telegram пользователь")

    # Конфликты reverse accessor:**
    # Ошибки, связанные с `auth.User.groups` и `auth.User.user_permissions`, указывают на то,
    # что у вас есть конфликт имен между встроенной моделью `User` из `django.contrib.auth`
    # и вашей кастомной моделью `User` в приложении `shop`. Это происходит из-за того,
    # что обе модели определяют отношения `groups` и `user_permissions`, и Django не может определить, какой из них использовать.
    # Устанавливаем кастомные related_name для полей groups и user_permissions
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.get_full_name()


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название категории")
    description = models.TextField(blank=True, null=True, verbose_name="Описание категории")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="products", verbose_name="Категория")
    name = models.CharField(max_length=255, verbose_name="Название товара")
    description = models.TextField(verbose_name="Описание товара")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    image = models.ImageField(upload_to='products/', verbose_name="Изображение товара")
    is_available = models.BooleanField(default=True, verbose_name="В наличии")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    # чтобы таблица в админ-панели отображалась на русском, создаём вложенные классы в каждой модели
    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name


class Order(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="orders", verbose_name="Пользователь")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")
    delivery_address = models.TextField(verbose_name="Адрес доставки")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая цена")
    STATUS_CHOICES = (
        ('принят', 'Принят'),
        ('в обработке', 'В обработке'),
        ('доставлен', 'Доставлен'),
        ('отменен', 'Отменен'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='принят', verbose_name="Статус")
    notes = models.TextField(blank=True, null=True, verbose_name="Примечания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    is_from_bot = models.BooleanField(default=False, verbose_name="Заказ из Telegram бота")

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"

    def __str__(self):
        return f"Заказ №{self.id} от {self.order_date.strftime('%d.%m.%Y %H:%M')}"

    # Общее количество товаров в заказе
    def get_total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Заказ")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена за единицу")

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"

    def __str__(self):
        return f"{self.product.name} ({self.quantity} шт.)"

    # Общая стоимость позиции в заказе
    def get_total_price(self):
        return self.quantity * self.price


class Review(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="reviews", verbose_name="Пользователь")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews", verbose_name="Товар")
    rating = models.PositiveIntegerField(verbose_name="Рейтинг")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата отзыва")

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.product.name}"


class BotUser(models.Model):
    telegram_id = models.IntegerField(unique=True, verbose_name="Telegram ID")
    username = models.CharField(max_length=255, blank=True, null=True, verbose_name="Имя пользователя в Telegram")
    first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Имя")
    last_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Фамилия")

    class Meta:
        verbose_name = "Пользователь Telegram бота"
        verbose_name_plural = "Пользователи Telegram бота"

    def __str__(self):
        return f"{self.first_name} {self.last_name} (Telegram ID: {self.telegram_id})"


# Модель для связывания заказов из TГ-бота с заказами с сайта
class BotOrder(models.Model):
    bot_order_id = models.IntegerField(unique=True, verbose_name="ID заказа в Telegram боте")
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True,
                              verbose_name="Заказ в веб-приложении")
    telegram_user = models.ForeignKey(BotUser, on_delete=models.SET_NULL, null=True, blank=True,
                                      verbose_name="Пользователь Telegram")

    class Meta:
        verbose_name = "Заказ Telegram бота"
        verbose_name_plural = "Заказы Telegram бота"

    def __str__(self):
        if self.order:
            return f"Заказ Telegram бота {self.bot_order_id} связан с заказом № {self.order.id}"
        else:
            return f"Заказ Telegram бота {self.bot_order_id} (не связан)"
