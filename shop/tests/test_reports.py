# shop/tests/test_reports.py — Ficha 05: relatório com 202 e estado só para o dono
# Com ALWAYS_EAGER a tarefa corre dentro do POST; o estado fica no backend em memória.
import uuid

import pytest
from django.contrib.auth.models import Group
from rest_framework.test import APIClient

from accounts.factories import UserFactory
from shop.factories import CustomerFactory, OrderFactory, OrderItemFactory
from shop.models import Order


def as_(user):
    api = APIClient()
    if user:
        api.force_authenticate(user=user)
    return api


@pytest.fixture
def shop(db):
    ana, bruno = CustomerFactory(), CustomerFactory()
    for _ in range(3):
        OrderItemFactory(order=OrderFactory(customer=ana))
    OrderItemFactory(order=OrderFactory(customer=ana, status=Order.Status.PAID))
    for _ in range(2):
        OrderItemFactory(order=OrderFactory(customer=bruno))  # encomendas de outro cliente
    return {"ana": ana, "bruno": bruno}


def test_report_is_accepted_and_counts_only_own_orders(shop):
    api = as_(shop["ana"].user)
    r = api.post("/api/v1/reports/orders/")
    assert r.status_code == 202
    body = r.json()
    assert body["status_url"] == f"/api/v1/tasks/{body['id']}/"
    assert r["Location"] == body["status_url"]

    status = api.get(body["status_url"])
    assert status.status_code == 200
    data = status.json()
    assert data["state"] == "SUCCESS"
    assert data["result"]["orders"] == 4  # só as da ana, não as do bruno
    assert data["result"]["by_status"] == {"pending": 3, "paid": 1, "cancelled": 0}
    assert isinstance(data["result"]["amount"], str)
    assert data["progress"] is None and data["error"] is None


def test_task_of_another_customer_or_unknown_is_404(shop):
    status_url = as_(shop["ana"].user).post("/api/v1/reports/orders/").json()["status_url"]
    other = as_(shop["bruno"].user)
    assert other.get(status_url).status_code == 404  # não se confirma que existe
    assert other.get(f"/api/v1/tasks/{uuid.uuid4()}/").status_code == 404
    assert other.get("/api/v1/tasks/inventado/").status_code == 404


def test_gestor_report_counts_all_orders(shop):
    gestor = UserFactory()
    gestor.groups.add(Group.objects.get(name="gestores"))
    api = as_(gestor)
    status_url = api.post("/api/v1/reports/orders/").json()["status_url"]
    assert api.get(status_url).json()["result"]["orders"] == Order.objects.count() == 6


def test_report_requires_authentication(db):
    assert as_(None).post("/api/v1/reports/orders/").status_code == 401


def test_user_without_customer_profile_is_400(db):
    r = as_(UserFactory()).post("/api/v1/reports/orders/")
    assert r.status_code == 400
    assert r.json()["status"] == 400  # Problem Details
