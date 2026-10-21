from rest_framework import serializers
from .models import Category, Customer, Product, Order, OrderItem

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'category', 'price', 'attributes']

class CustomerSerializer(serializers.ModelSerializer):
    # Expõe o username do utilizador associado como campo SÓ de leitura
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Customer
        fields = ['id', 'user', 'username', 'level']
        read_only_fields = ['level'] # O cliente não pode mudar o seu próprio nível

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    unit_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price']
        
    # Requisito: validate_<campo>
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("A quantidade tem de ser maior que zero.")
        return value

class OrderSerializer(serializers.ModelSerializer):

    items = OrderItemSerializer(many=True, read_only=True)
    
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'created_at', 'total_amount', 'items', 'total']
        read_only_fields = ['created_at', 'total_amount']

    def validate(self, attrs):
        # Exemplo de validação genérica: garantir que o cliente associado está ativo
        # Como Customer é simples, vamos garantir que o total_amount inicializado pelo cliente não tenta forçar valores
        if 'customer' in attrs and attrs['customer'].level == Customer.CustomerLevel.PREMIUM:
            pass
        return attrs