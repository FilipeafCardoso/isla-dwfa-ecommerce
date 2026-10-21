from django.db import models
from django.conf import settings
from django.db.models import CheckConstraint, UniqueConstraint, Q, Index

# Create your models here

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Customer(models.Model):
    # Requisito: TextChoices
    class CustomerLevel(models.TextChoices):
        REGULAR = 'REG', 'Regular'
        PREMIUM = 'PRM', 'Premium'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )
    level = models.CharField(
        max_length=3,
        choices=CustomerLevel.choices,
        default=CustomerLevel.REGULAR
    )

    def __str__(self):
        return self.user.username

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT, # PROTECT impede que sejam apagadas categorias com produtos
        related_name='products'
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Requisito: JSONField
    attributes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Especificações variáveis como cor, tamanho ou voltagem."
    )

    def __str__(self):
        return self.name

class Order(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        constraints = [
            # Requisito: CheckConstraint
            CheckConstraint(
                condition=Q(total_amount__gte=0),
                name='check_order_total_positive'
            )
        ]
        indexes = [
            # Requisito: Index composto
            Index(fields=['customer', '-created_at'], name='idx_customer_created_at')
        ]

    def __str__(self):
        return f"Order {self.id} - {self.customer}"

class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE, # Se a encomenda for apagada, apaga as linhas
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.RESTRICT, # Impede que seja apagado um produto que já foi vendido
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [
            # Requisito: UniqueConstraint
            UniqueConstraint(
                fields=['order', 'product'],
                name='unique_order_product'
            )
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"