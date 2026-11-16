"""Aplicação Celery do projeto (Ficha 05).

O worker arranca com `uv run celery -A config worker -l info`; as definições vêm do
Django (prefixo `CELERY_`) e as tarefas são descobertas em `<app>/tasks.py`.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
