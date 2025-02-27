"""
Django settings for website project.

Generated by 'django-admin startproject' using Django 5.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-xo-2ml=dmt(e#a5mb4%%ehp$-p0-f!s1&kn5lw4#8_0i&g#p8s'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'shop',
    'widget_tweaks',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Важно: WhiteNoiseMiddleware должен быть после SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'website.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'website.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': (BASE_DIR.parent / 'db' / 'db.sqlite3').resolve(),
        'OPTIONS': {
            'timeout': 20  # Увеличение таймаута для блокировок
        }
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

# Для работы со статическим файлами
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'shop', 'static'),  # Добавьте эту строку!
    #BASE_DIR / "static",
    # 'var/www/static/', это нужно для подгрузки на сервер
]

# Настройте WhiteNoise для обслуживания медиафайлов
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Папка, в которую Django будет собирать все статические файлы при выполнении команды collectstatic
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# Media files (Uploaded files by users)
# https://docs.djangoproject.com/en/3.0/howto/media-files/

# URL, через который будут доступны медиафайлы
MEDIA_URL = '/media/'

# Папка, в которой будут храниться медиафайлы
MEDIA_ROOT = BASE_DIR / 'media'
print(MEDIA_ROOT)

AUTH_USER_MODEL = 'shop.UserProfile'



DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# пропишем абсолютный путь к проекту. При перемещении в другую папку, надо изменить
# try:
#     sys.path.append('C:/Users/Sofi/Documents/GitHub/FlowerDelivery/bot')  # Не рекомендуется, но возможно
#     from config import BOT_TOKEN
#
#     TELEGRAM_BOT_TOKEN = BOT_TOKEN
# except ImportError as e:
#     print(f"ImportError: {e}")
#     TELEGRAM_BOT_TOKEN = None

try:
    sys.path.insert(0, os.path.join(BASE_DIR.parent, 'bot'))
    print(BASE_DIR.parent)
    from config import BOT_TOKEN, BOT_USERNAME  # website - имя пакета
    TELEGRAM_BOT_TOKEN = BOT_TOKEN
    TELEGRAM_BOT_USERNAME = BOT_USERNAME
except ImportError as e:
    print(f"ImportError: {e}")
    TELEGRAM_BOT_TOKEN = None
print(sys.path)


# Настройки для корректных URL
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


