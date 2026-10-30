"""Parte 2 — três testes de API · three API tests (segunda · Monday)."""

from decimal import Decimal

import pytest
from django.conf import settings
from rest_framework.test import APIClient

from shop.factories import (
    CategoryFactory,
    CustomerFactory,
    OrderFactory,
    OrderItemFactory,
    ProductFactory,
)

PAGE_SIZE = settings.REST_FRAMEWORK["PAGE_SIZE"]


@pytest.mark.django_db
def test_product_list_is_paginated_and_filtered():
    cheap = ProductFactory.create_batch(PAGE_SIZE + 5, price=Decimal("5.00"))
    ProductFactory(price=Decimal("50.00"), name="Expensive lamp")
    r = APIClient().get("/api/v1/products/")
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"count", "next", "previous", "results"}
    assert body["count"] == len(cheap) + 1 and len(body["results"]) == PAGE_SIZE
    r = APIClient().get("/api/v1/products/?min_price=10&search=lamp&ordering=-price")
    assert r.status_code == 200 and r.json()["count"] == 1


@pytest.mark.django_db
def test_create_and_validate_order_item():
    product = ProductFactory(stock=3, price=Decimal("9.90"))
    order = OrderFactory()
    api = APIClient()
    api.force_authenticate(user=order.customer.user)  # Autenticação

    r = api.post("/api/v1/order-items/", {"order": order.id, "product": product.id, "quantity": 2})
    assert r.status_code == 201

    assert r.json()["unit_price"] == "9.90"  # copied by the server · copiado pelo servidor
    r = api.post(
        "/api/v1/order-items/", {"order": OrderFactory().id, "product": product.id, "quantity": 5}
    )
    assert r.status_code == 400
    assert "quantity" in r.json()["errors"]  # Problem Details envelope
    assert r.json()["status"] == 400


@pytest.mark.django_db
def test_order_list_is_paginated_without_n_plus_one(django_assert_max_num_queries):

    customer = CustomerFactory()
    for order in OrderFactory.create_batch(25, customer=customer):
        OrderItemFactory.create_batch(3, order=order)
    api = APIClient()
    api.force_authenticate(user=customer.user)  # Dono das 25 encomendas
    with django_assert_max_num_queries(
        4
    ):  # is_gestor (grupos) + count + orders (JOIN customer/user) + items (JOIN product)
        response = api.get("/api/v1/orders/")
    assert response.status_code == 200

    body = response.json()
    assert body["count"] == 25 and len(body["results"]) == PAGE_SIZE
    first = body["results"][0]
    assert len(first["items"]) == 3 and Decimal(first["total"]) > 0


@pytest.mark.django_db
def test_pay_then_pay_again_is_409():

    order = OrderFactory()
    OrderItemFactory(order=order, product=ProductFactory(price=Decimal("10.00")), quantity=2)
    api = APIClient()
    api.force_authenticate(user=order.customer.user)  # Só o dono paga
    r = api.post(f"/api/v1/orders/{order.id}/pay/")
    assert r.status_code == 200 and r.json()["status"] == "paid"

    r = api.post(f"/api/v1/orders/{order.id}/pay/")
    assert r.status_code == 409 and r.json()["title"] == "Conflict"


@pytest.mark.django_db
def test_openapi_schema_lists_the_action():
    r = APIClient().get("/api/schema/")
    assert r.status_code == 200
    assert "/api/v1/orders/{id}/pay/" in r.content.decode()
    CategoryFactory()
    assert APIClient().get("/api/docs/").status_code == 200
