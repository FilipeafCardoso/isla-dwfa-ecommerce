"""Domínio e-commerce · e-commerce domain (Ficha 02, parte 1).

PT: seis entidades; todas as FKs com `on_delete` deliberado e `related_name`;
regras de negócio como constraints em `Meta` — a base de dados impõe-nas para
todos os caminhos de escrita, não só para o serializer.
EN: six entities; every FK with a deliberate `on_delete` and `related_name`;
business rules as `Meta` constraints — the database enforces them on every
write path, not only through the serializer.
"""

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Category(models.Model):
    name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    # PROTECT: apagar uma categoria com produtos é um erro, não uma cascata
    # PROTECT: deleting a category that still has products is an error, not a cascade
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    sku = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    # JSONB: atributos variáveis por categoria (cor, tamanho, voltagem…) — sem schema fixo
    # JSONB: per-category attributes (colour, size, voltage…) with no fixed schema
    attributes = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(condition=Q(price__gte=0), name="product_price_gte_0"),
        ]
        indexes = [models.Index(fields=["category", "is_active"], name="product_cat_active_idx")]

    def __str__(self):
        return f"{self.sku} {self.name}"


class Customer(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="customer"
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        return self.user.get_username()


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"

    # PROTECT: uma encomenda é um registo contabilístico; não desaparece com o cliente
    # PROTECT: an order is an accounting record; it does not vanish with the customer
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer", "created_at"], name="order_customer_created_idx")
        ]

    def __str__(self):
        return f"Order #{self.pk} ({self.status})"


class OrderItem(models.Model):
    # CASCADE: uma linha sem encomenda não faz sentido · a line without its order is meaningless
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField()
    # copiado do produto no momento da compra · copied from the product at purchase time
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"], name="orderitem_unique_product_per_order"
            ),
            models.CheckConstraint(condition=Q(quantity__gt=0), name="orderitem_quantity_gt_0"),
        ]

    def __str__(self):
        return f"{self.quantity} × {self.product}"


class Payment(models.Model):
    class Method(models.TextChoices):
        CARD = "card", "Card"
        MBWAY = "mbway", "MB WAY"
        TRANSFER = "transfer", "Bank transfer"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.CARD)
    paid_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_at"]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="payment_amount_gt_0"),
        ]

    def __str__(self):
        return f"Payment {self.amount} for order #{self.order_id}"


# usado em anotações · used in annotations
LINE_TOTAL = F("items__quantity") * F("items__unit_price")
