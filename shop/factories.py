"""Factories para seed e testes · factories for seed and tests."""

import factory
from factory import fuzzy

from accounts.factories import UserFactory

from .models import Category, Customer, Order, OrderItem, Payment, Product


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ("slug",)

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.Sequence(lambda n: f"category-{n}")


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product
        django_get_or_create = ("sku",)

    category = factory.SubFactory(CategoryFactory)
    sku = factory.Sequence(lambda n: f"SKU-{n:05d}")
    name = factory.Faker("catch_phrase")
    price = fuzzy.FuzzyDecimal(1, 200, 2)
    stock = fuzzy.FuzzyInteger(5, 50)


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer
        django_get_or_create = ("user",)

    user = factory.SubFactory(UserFactory)
    phone = factory.Sequence(lambda n: f"+3519{n:08d}")


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    customer = factory.SubFactory(CustomerFactory)
    status = Order.Status.PENDING


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = fuzzy.FuzzyInteger(1, 3)
    unit_price = factory.LazyAttribute(lambda o: o.product.price)


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    order = factory.SubFactory(OrderFactory, status=Order.Status.PAID)
    amount = fuzzy.FuzzyDecimal(1, 200, 2)
