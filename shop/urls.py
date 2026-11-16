from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    CustomerViewSet,
    OrderItemViewSet,
    OrdersReportView,
    OrderViewSet,
    PaymentViewSet,
    ProductViewSet,
    TaskStatusView,
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

urlpatterns = router.urls + [
    # Ficha 05: relatório assíncrono (202) e estado da tarefa (só o dono ou o gestor)
    path("reports/orders/", OrdersReportView.as_view(), name="report-orders"),
    # <str:> e não <uuid:>: um id inválido dá o mesmo 404 em Problem Details (não o HTML)
    path("tasks/<str:task_id>/", TaskStatusView.as_view(), name="task-status"),
]
