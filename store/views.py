from django.db.models import Sum, F, Prefetch
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Category, Customer, Product, Order, OrderItem
from .serializers import CategorySerializer, CustomerSerializer, ProductSerializer, OrderSerializer
from drf_spectacular.utils import extend_schema

#Create your views here.

from .services import pay_order

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    # Apenas de leitura: os clientes não podem criar ou apagar categorias pela API
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.select_related('user').all()
    serializer_class = CustomerSerializer

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    ordering_fields = ['created_at', 'total']
    ordering = ['-created_at']

    def get_queryset(self):
        items_qs = OrderItem.objects.select_related('product')
        # Calcular o total (quantidade * preço do produto)
        line = F('items__quantity') * F('items__product__price')
        
        return (
            Order.objects
            .select_related('customer__user')
            .prefetch_related(Prefetch('items', queryset=items_qs))
            .annotate(total=Sum(line))
        )

    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        order = self.get_object()
        order = pay_order(order)
        return Response(OrderSerializer(order).data)

    @extend_schema(request=None, responses={200: OrderSerializer, 409: None})
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        order = self.get_object()
        order = pay_order(order)
        return Response(OrderSerializer(order).data)