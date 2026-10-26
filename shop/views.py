"""ViewSets · sem N+1 nos endpoints de lista · no N+1 on list endpoints."""

from django.db.models import F, Prefetch, Sum
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .filters import OrderFilter, ProductFilter
from .models import LINE_TOTAL, Category, Customer, Order, OrderItem, Payment, Product
from .serializers import (
    CategorySerializer,
    CustomerSerializer,
    OrderItemSerializer,
    OrderSerializer,
    PaymentSerializer,
    ProductSerializer,
)
from .services import cancel_order, pay_order


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    search_fields = ["name"]
    ordering_fields = ["name"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category")
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    search_fields = ["name", "sku"]
    ordering_fields = ["price", "name", "created_at"]
    ordering = ["name"]


class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Customer.objects.select_related("user")
    serializer_class = CustomerSerializer
    search_fields = ["user__username", "user__email"]


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    filterset_class = OrderFilter
    ordering_fields = ["created_at", "total"]
    ordering = [
        "-created_at"
    ]  # explícito: annotate() perde o Meta.ordering · annotate() drops Meta.ordering
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        items = OrderItem.objects.select_related("product").annotate(
            line_total=F("quantity") * F("unit_price")
        )
        return (
            Order.objects.select_related("customer__user")
            .prefetch_related(Prefetch("items", queryset=items))
            .annotate(total=Sum(LINE_TOTAL))
        )

    @extend_schema(
        request=None,
        responses={200: OrderSerializer, 409: OpenApiResponse(description="Order is not pending")},
    )
    @action(detail=True, methods=["post"])
    def pay(self, request, pk=None):
        pay_order(self.get_object())
        return Response(self.get_serializer(self.get_object()).data)

    @extend_schema(
        request=None,
        responses={200: OrderSerializer, 409: OpenApiResponse(description="Order is not pending")},
    )
    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        cancel_order(self.get_object())
        return Response(self.get_serializer(self.get_object()).data)


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.select_related("product", "order").annotate(
        line_total=F("quantity") * F("unit_price")
    )
    serializer_class = OrderItemSerializer
    filterset_fields = ["order", "product"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.select_related("order")
    serializer_class = PaymentSerializer
    filterset_fields = ["order", "method"]
