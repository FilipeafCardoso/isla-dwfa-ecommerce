"""Tarefas Celery da loja (Ficha 05).

As tarefas recebem ids, nunca objetos: a mensagem vai serializada para o Redis e o objeto
estaria velho quando o worker a lesse.
"""

import os
from smtplib import SMTPException

from celery import shared_task
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import Payment
from .services import order_total


class ReceiptGatewayError(Exception):
    """Falha transitória ao enviar o recibo (SMTP em baixo, timeout)."""


@shared_task(
    bind=True,
    acks_late=True,
    autoretry_for=(ReceiptGatewayError,),  # só o transitório; nunca DoesNotExist/ValidationError
    retry_backoff=2,  # 2 s, 4 s, 8 s …
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=3,
)
def send_order_receipt(self, order_id: int) -> str:
    # Só para a demonstração do retry (slide 20): a 1.ª tentativa falha de propósito
    if os.environ.get("RECEIPT_FLAKY") == "1" and self.request.retries == 0:
        raise ReceiptGatewayError("timed out")

    with transaction.atomic():
        # Encomenda/pagamento inexistente não é transitório: o DoesNotExist sobe sem retry
        payment = (
            Payment.objects.select_for_update()
            .select_related("order__customer__user")
            .get(order_id=order_id)
        )
        # Idempotência: o broker entrega *pelo menos uma vez* (acks_late); a 2.ª entrega
        # vê o campo preenchido e não reenvia
        if payment.receipt_sent_at is not None:
            return "already-sent"

        order = payment.order
        user = order.customer.user
        # Sem email não há a quem enviar; não se marca, para poder sair se o email aparecer
        if not user.email:
            return "no-email"

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
        except (SMTPException, OSError) as exc:
            raise ReceiptGatewayError(str(exc)) from exc

        payment.receipt_sent_at = timezone.now()
        payment.save(update_fields=["receipt_sent_at"])
    return "sent"
