"""O serializer é a fronteira · the serializer is the boundary.

PT: `fields` explícitos (nunca "__all__"); `read_only_fields` para o que o servidor decide.
EN: explicit `fields` (never "__all__"); `read_only_fields` for whatever the server decides.
"""

from rest_framework import serializers

from .models import Category, Customer, Order, OrderItem, Payment, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "sku", "name", "category", "category_name", "price", "stock",
            "attributes", "is_active", "created_at",
        ]  # fmt: skip
        read_only_fields = ["created_at"]

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value


class CustomerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "user", "username", "email", "phone", "address"]
        read_only_fields = ["user"]


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "order", "product", "product_name", "quantity", "unit_price", "line_total"]
        read_only_fields = ["unit_price"]

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive.")
        return value

    def validate(self, attrs):
        # regra entre campos: quantidade ≤ stock · cross-field rule: quantity ≤ stock
        product = attrs.get("product") or getattr(self.instance, "product", None)
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", 0))
        if product is not None and quantity > product.stock:
            raise serializers.ValidationError({"quantity": f"Only {product.stock} in stock."})
        return attrs

    def create(self, validated_data):
        # o preço é copiado do produto no servidor, nunca vem do cliente
        # the price is copied from the product on the server, never from the client
        validated_data["unit_price"] = validated_data["product"].price
        return super().create(validated_data)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.user.username", read_only=True)
    # vem de annotate(total=...) no queryset · comes from annotate(total=...) in the queryset
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "customer", "customer_name", "status", "items", "total", "created_at"]
        # customer vem de request.user (perform_create); status só muda via pay/cancel;
        # total é calculado (annotate).
        read_only_fields = ["customer", "status", "total", "created_at"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "order", "amount", "method", "paid_at"]
        read_only_fields = ["amount", "paid_at"]
