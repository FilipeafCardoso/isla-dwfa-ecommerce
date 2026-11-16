"""Tarefas Celery da loja (Ficha 05).

As tarefas recebem ids, nunca objetos: a mensagem vai serializada para o Redis e o objeto
estaria velho quando o worker a lesse.
"""

import os
import time
from decimal import Decimal
from smtplib import SMTPException

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import LINE_TOTAL, Order, Payment
from .services import order_total


class ReceiptGatewayError(Exception):
    """Falha transitória ao enviar o recibo (SMTP em baixo, timeout).

    Ficha 05: é a única exceção com retry; os erros permanentes falham logo.
    """


@shared_task(
    bind=True,  # dá acesso a self.request.retries (usado no RECEIPT_FLAKY)
    acks_late=True,  # Ficha 05: confirma no fim → entrega *pelo menos uma vez*
    autoretry_for=(ReceiptGatewayError,),  # só o transitório; nunca DoesNotExist/ValidationError
    retry_backoff=2,  # teto exponencial: 2 s, 4 s, 8 s …
    retry_backoff_max=60,
    retry_jitter=True,  # espera sorteada entre 0 e o teto (o log pode mostrar "Retry in 0s")
    max_retries=3,
)
def send_order_receipt(self, order_id: int) -> str:
    # Ficha 05: só para a demonstração do retry (slide 20) — a 1.ª tentativa falha de propósito
    if os.environ.get("RECEIPT_FLAKY") == "1" and self.request.retries == 0:
        raise ReceiptGatewayError("timed out")

    with transaction.atomic():
        # 1) Bloquear: um worker de cada vez neste pagamento. Inexistente não é transitório:
        # o DoesNotExist sobe sem retry
        payment = (
            Payment.objects.select_for_update()
            .select_related("order__customer__user")
            .get(order_id=order_id)
        )
        # 2) Já enviado? Ficha 05: idempotente — o broker entrega *pelo menos uma vez*
        # (acks_late); a 2.ª entrega vê o campo preenchido e não reenvia
        if payment.receipt_sent_at is not None:
            return "already-sent"

        order = payment.order
        user = order.customer.user
        # Sem email não há a quem enviar; não se marca, para poder sair se o email aparecer
        if not user.email:
            return "no-email"

        # 3) Enviar
        total = order_total(order)  # Decimal, nunca float
        try:
            send_mail(
                subject=f"Recibo da encomenda #{order.pk}",
                message=(
                    f"Olá {user.get_username()},\n\n"
                    f"Recebemos o pagamento da encomenda #{order.pk}.\n"
                    f"Total: {total:.2f} €\n\n"
                    "Obrigado pela compra."
                ),
                from_email=None,  # DEFAULT_FROM_EMAIL
                recipient_list=[user.email],
            )
        except (SMTPException, OSError) as exc:  # falhas de rede/SMTP → retry
            raise ReceiptGatewayError(str(exc)) from exc

        # 4) Marcar, na mesma transação do bloqueio
        payment.receipt_sent_at = timezone.now()
        payment.save(update_fields=["receipt_sent_at"])
    return "sent"


@shared_task(bind=True)
def export_orders_report(self, user_id: int, customer_id: int | None) -> dict:
    """Resumo das encomendas: as de um cliente, ou todas (gestor, `customer_id=None`).

    `user_id` é quem pediu; fica nos argumentos da tarefa (visível no log do worker).
    """
    # Ficha 05: uma só query — o total vem anotado, como no OrderViewSet (sem N+1)
    qs = Order.objects.annotate(total=Sum(LINE_TOTAL)).order_by("id")
    if customer_id is not None:
        qs = qs.filter(customer_id=customer_id)
    rows = list(qs.values_list("status", "total"))

    n = len(rows)
    amount = Decimal("0.00")
    by_status = {status: 0 for status in Order.Status.values}
    for i, (status, total) in enumerate(rows, start=1):
        amount += total or Decimal("0.00")  # encomenda sem linhas → total None
        by_status[status] += 1
        # Grava o progresso no result backend; o GET /tasks/<id>/ lê-o como `progress`
        self.update_state(state="PROGRESS", meta={"current": i, "total": n})
        time.sleep(settings.REPORT_ITEM_DELAY)

    # Ficha 05: amount em string — JSON não tem decimal (a mesma regra do price)
    return {"orders": n, "amount": str(amount), "by_status": by_status}
