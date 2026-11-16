# Carrega a app Celery com o Django, para o @shared_task a usar
from .celery import app as celery_app

__all__ = ("celery_app",)
