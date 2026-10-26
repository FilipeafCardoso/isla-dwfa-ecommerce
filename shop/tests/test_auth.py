# shop/tests/test_auth.py
import pytest
from rest_framework.test import APIClient

from accounts.factories import UserFactory

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