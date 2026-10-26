"""Parte 1 — três testes de modelo · three model tests (sábado · Saturday)."""

from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from shop.factories import OrderFactory, OrderItemFactory, ProductFactory
from shop.models import LINE_TOTAL, Order
from shop.services import Conflict, pay_order


@pytest.mark.django_db
def test_constraint_rejects_duplicate_product_in_order():
    item = OrderItemFactory()
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            OrderItemFactory(order=item.order, product=item.product)


@pytest.mark.django_db
def test_order_totals_in_two_queries(django_assert_max_num_queries):
    from django.db.models import F, Prefetch, Sum

    from shop.models import OrderItem

    for order in OrderFactory.create_batch(5):
        OrderItemFactory.create_batch(3, order=order)
    with django_assert_max_num_queries(2):  # orders+totals (1) · items prefetch (1)
        # Prefetch + select_related: 2 queries; prefetch_related("items__product") would be 3
        items = OrderItem.objects.select_related("product").annotate(
            line_total=F("quantity") * F("unit_price")
        )
        orders = list(
            Order.objects.annotate(total=Sum(LINE_TOTAL)).prefetch_related(
                Prefetch("items", queryset=items)
            )
        )
        totals = [o.total for o in orders]
        lines = [sum(i.line_total for i in o.items.all()) for o in orders]
    assert len(orders) == 5
    assert all(isinstance(t, Decimal) and t > 0 for t in totals)
    assert totals == lines


@pytest.mark.django_db
def test_failed_payment_leaves_no_row():
    order = OrderFactory(status=Order.Status.CANCELLED)
    OrderItemFactory(order=order, product=ProductFactory(price=Decimal("10.00")))
    with pytest.raises(Conflict):
        pay_order(order)
    order.refresh_from_db()
    assert order.status == Order.Status.CANCELLED
    assert not hasattr(order, "payment") or Order.objects.filter(payment__isnull=False).count() == 0
