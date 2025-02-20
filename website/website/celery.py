# celery.py
import os
from celery import Celery

# Установите модуль настроек Django по умолчанию для Celery.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')  # Замените website на имя вашего проекта

app = Celery('website')  # Замените website на имя вашего проекта

# Используйте настройки Django для конфигурации Celery.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически загружайте задачи из всех приложений Django.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')