# Ficha 05: carrega a app Celery quando o Django arranca, para o @shared_task a encontrar
from .celery import app as celery_app

__all__ = ("celery_app",)
