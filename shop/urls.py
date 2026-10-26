from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    CustomerViewSet,
    OrderItemViewSet,
    OrderViewSet,
    PaymentViewSet,
    ProductViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("products", ProductViewSet)
router.register("customers", CustomerViewSet)
router.register(
    "orders", OrderViewSet, basename="order"
)  # sem atributo queryset · no queryset attr
router.register("order-items", OrderItemViewSet)
router.register("payments", PaymentViewSet)

urlpatterns = router.urls
