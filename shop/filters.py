import django_filters

from .models import Order, Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    in_stock = django_filters.BooleanFilter(field_name="stock", lookup_expr="gt", exclude=False)

    class Meta:
        model = Product
        fields = ["category", "is_active", "min_price", "max_price"]


class OrderFilter(django_filters.FilterSet):
    created_from = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_to = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = Order
        fields = ["status", "customer", "created_from", "created_to"]
