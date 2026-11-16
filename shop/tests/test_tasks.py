# shop/tests/test_tasks.py — Ficha 05: recibo (Celery em modo eager, sem Redis)
import pytest
from django.core import mail
from rest_framework.test import APIClient

from accounts.factories import UserFactory
from shop.factories import CustomerFactory, OrderFactory, OrderItemFactory, PaymentFactory
from shop.models import Order, Payment
from shop.tasks import send_order_receipt


def paid_order(**user_kwargs):
    customer = CustomerFactory(user=UserFactory(**user_kwargs))
    order = OrderFactory(customer=customer, status=Order.Status.PAID)
    OrderItemFactory(order=order)
    PaymentFactory(order=order)
    return order


@pytest.mark.django_db
def test_receipt_is_idempotent():
    # Ficha 05: idempotente — 2 entregas da mesma mensagem, 1 só email
    order = paid_order()
    first = send_order_receipt.delay(order.id)
    again = send_order_receipt.delay(order.id)  # 2.ª entrega da mesma mensagem
    assert first.get() == "sent"
    assert again.get() == "already-sent"
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [order.customer.user.email]
    assert Payment.objects.get(order=order).receipt_sent_at is not None


@pytest.mark.django_db
def test_receipt_without_email_is_not_marked():
    # Sem email não se marca: o recibo ainda pode sair mais tarde
    order = paid_order(email="")
    assert send_order_receipt.delay(order.id).get() == "no-email"
    assert mail.outbox == []
    assert Payment.objects.get(order=order).receipt_sent_at is None


@pytest.mark.django_db
def test_unknown_order_fails_without_retry():
    # Retry só no transitório: o DoesNotExist sobe à primeira (com EAGER_PROPAGATES)
    with pytest.raises(Payment.DoesNotExist):
        send_order_receipt.delay(999_999)


def pay_as_owner(order):
    api = APIClient()
    api.force_authenticate(user=order.customer.user)
    return api.post(f"/api/v1/orders/{order.id}/pay/")


@pytest.mark.django_db
def test_pay_enqueues_receipt_on_commit(django_capture_on_commit_callbacks):
    # Ficha 05: on_commit — o pay deixa exatamente 1 callback, que envia o recibo
    order = OrderItemFactory().order
    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        r = pay_as_owner(order)
    assert r.status_code == 200
    assert r.json()["status"] == "paid"
    assert len(callbacks) == 1
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_receipt_is_not_sent_inside_the_transaction(django_capture_on_commit_callbacks):
    # Ficha 05: nada sai antes do commit (falharia com um .delay() solto na transação)
    order = OrderItemFactory().order
    with django_capture_on_commit_callbacks() as callbacks:  # sem execute: não há "commit"
        r = pay_as_owner(order)
    assert r.status_code == 200
    assert len(callbacks) == 1
    assert mail.outbox == []  # nada saiu antes do commit
    callbacks[0]()  # simula o commit
    assert len(mail.outbox) == 1
