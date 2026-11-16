"""Aplicação Celery do projeto (Ficha 05).

O worker arranca com `uv run celery -A config worker -l info`; as definições vêm do
Django (prefixo `CELERY_`) e as tarefas são descobertas em `<app>/tasks.py`.
"""

import os

from celery import Celery

# Ficha 05: o worker não passa pelo manage.py, por isso escolhe aqui os mesmos settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("config")
# Lê as CELERY_* do Django (CELERY_BROKER_URL → broker_url, …)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()  # procura <app>/tasks.py em cada INSTALLED_APPS
