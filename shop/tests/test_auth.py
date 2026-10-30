# shop/tests/test_auth.py
import pytest
from rest_framework.test import APIClient

from accounts.factories import UserFactory

from django.contrib.auth.models import Group

from shop.factories import CategoryFactory, CustomerFactory, OrderFactory, OrderItemFactory

PASSWORD = "uma-password-bem-longa-123"


# Autenticação JWT

@pytest.mark.django_db
def test_orders_without_token_is_401():
    assert APIClient().get("/api/v1/orders/").status_code == 401


@pytest.mark.django_db
def test_login_returns_access_and_refresh():
    user = UserFactory()
    user.set_password(PASSWORD)
    user.save()
    r = APIClient().post(
        "/api/v1/auth/token/",
        {"username": user.username, "password": PASSWORD},
        format="json",
    )
    assert r.status_code == 200
    assert {"access", "refresh"} <= r.json().keys()


@pytest.fixture
def actors(db):
    gestor = UserFactory()
    gestor.groups.add(Group.objects.get(name="gestores"))  # criado pela migração de dados
    return {"anon": None, "customer": UserFactory(), "gestor": gestor}


def as_(user):
    api = APIClient()
    if user:
        api.force_authenticate(user=user)
    return api


@pytest.mark.parametrize("role,expected", [("anon", 401), ("customer", 403), ("gestor", 201)])
def test_create_product_by_role(actors, role, expected):
    body = {
        "sku": "LAMP-1",
        "name": "Lamp",
        "price": "9.90",
        "stock": 3,
        "category": CategoryFactory().id,
        "attributes": {},
    }
    r = as_(actors[role]).post("/api/v1/products/", body, format="json")
    assert r.status_code == expected


@pytest.mark.parametrize(
    "role,expected_status,expected_count",
    [("anon", 401, None), ("customer", 200, 1), ("gestor", 200, 2)],
)
def test_list_orders_by_role(actors, role, expected_status, expected_count):
    OrderFactory(customer=CustomerFactory(user=actors["customer"]))  # do cliente
    OrderFactory()  # outro cliente
    r = as_(actors[role]).get("/api/v1/orders/")
    assert r.status_code == expected_status
    if expected_count is not None:
        assert r.json()["count"] == expected_count


@pytest.mark.parametrize(
    "method,path",
    [("get", "/api/v1/orders/{id}/"), ("post", "/api/v1/orders/{id}/pay/")],
)
def test_foreign_order_is_404_for_customer(actors, method, path):
    CustomerFactory(user=actors["customer"])
    other = OrderFactory()
    OrderItemFactory(order=other)
    r = getattr(as_(actors["customer"]), method)(path.format(id=other.id))
    assert r.status_code == 404  # não 403: não se confirma que a encomenda existe


def test_owner_cannot_change_status_via_patch(actors):
    order = OrderFactory(customer=CustomerFactory(user=actors["customer"]))
    before = order.status
    r = as_(actors["customer"]).patch(
        f"/api/v1/orders/{order.id}/", {"status": "paid"}, format="json"
    )
    assert r.status_code == 200
    order.refresh_from_db()
    assert order.status == before  # status em read_only_fields: o PATCH é ignorado