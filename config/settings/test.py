"""Testes (pytest-django) · tests."""

from .base import *  # noqa: F403

DEBUG = False

# Hasher rápido: os testes não medem a força das passwords · fast hasher: tests do not
# benchmark password strength
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Ficha 05: sem Redis nos testes (o CI não o tem): Celery síncrono e caches em memória
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_TASK_STORE_EAGER_RESULT = True
CELERY_RESULT_BACKEND = "cache+memory://"
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
# Faz de trabalho a sério sem atrasar os testes
REPORT_ITEM_DELAY = 0
