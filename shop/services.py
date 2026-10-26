"""Regras de negócio fora das vistas · business rules outside the views.

PT: a vista fica fina; a transição de estado corre numa transação com
`select_for_update` — dois `pay` concorrentes não pagam a mesma encomenda duas vezes.
EN: the view stays thin; the state transition runs in a transaction with
`select_for_update` — two concurrent `pay` calls cannot pay the same order twice.
"""

from django.db import transaction
from django.db.models import F, Sum
from rest_framework import status
from rest_framework.exceptions import APIException

from .models import Order, Payment


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The operation conflicts with the current state of the resource."
    default_code = "conflict"


def order_total(order: Order):
    return order.items.aggregate(total=Sum(F("quantity") * F("unit_price")))["total"] or 0


@transaction.atomic
def pay_order(order: Order, method: str = Payment.Method.CARD) -> Order:
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != Order.Status.PENDING:
        raise Conflict(f"Order #{order.pk} is {order.status}; only pending orders can be paid.")
    total = order_total(order)
    if total <= 0:
        raise Conflict(f"Order #{order.pk} has no items.")
    Payment.objects.create(order=order, amount=total, method=method)
    order.status = Order.Status.PAID
    order.save(update_fields=["status"])
    return order


@transaction.atomic
def cancel_order(order: Order) -> Order:
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status != Order.Status.PENDING:
        raise Conflict(
            f"Order #{order.pk} is {order.status}; only pending orders can be cancelled."
        )
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status"])
    return order
