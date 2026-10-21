import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from store.models import Category, Customer, Product, Order, OrderItem

User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")

class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = Customer
    user = factory.SubFactory(UserFactory)
    level = Customer.CustomerLevel.REGULAR

class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
    name = factory.Sequence(lambda n: f"Categoria {n}")

class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product
    name = factory.Sequence(lambda n: f"Produto {n}")
    category = factory.SubFactory(CategoryFactory)
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)

class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order
    customer = factory.SubFactory(CustomerFactory)
    total_amount = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)

class OrderItemFactory(DjangoModelFactory):
    class Meta:
        model = OrderItem
    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker('random_int', min=1, max=5)