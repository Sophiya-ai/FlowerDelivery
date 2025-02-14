"""
URL configuration for website project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
# Главная страница будет обрабатываться с помощью приложения нашего,
# которое находится в отдельном пакете. В него нужно как-то попасть.
# Для этого существует специальная функция include

# Для работы со статическим файлами подключаем:
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('', include('shop.urls')),
              ] + static(settings.STATIC_URL,
                         document_root=settings.STATIC_ROOT)  # Для работы со статическим файлами, прописываем их подключение и использование

# Настройка URL для медиафайлов. Это позволит Django обслуживать медиафайлы во время разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
