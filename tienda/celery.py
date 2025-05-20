import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tienda.settings')

app = Celery('tienda')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()