"""ViewSets · sem N+1 nos endpoints de lista · no N+1 on list endpoints."""

from uuid import uuid4

from celery.result import AsyncResult
from django.core.cache import cache
from django.db.models import F, Prefetch, Sum
from django.urls import reverse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import OrderFilter, ProductFilter
from .models import LINE_TOTAL, Category, Customer, Order, OrderItem, Payment, Product
from .permissions import IsGestorOrReadOnly, IsOwnerOrGestor, is_gestor
from .serializers import (
    CategorySerializer,
    CustomerSerializer,
    OrderItemSerializer,
    OrderSerializer,
    PaymentSerializer,
    ProductSerializer,
    TaskAcceptedSerializer,
    TaskStatusSerializer,
)
from .services import cancel_order, pay_order
from .tasks import export_orders_report

# Nota: em todos os get_queryset filtrados, "swagger_fake_view" é verdadeiro
# quando o drf-spectacular gera o schema; aí o request.user é anónimo e o filtro
# por utilizador rebentaria, por isso devolve-se um queryset vazio.


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    search_fields = ["name"]
    ordering_fields = ["name"]
    # Exceção à omissão IsAuthenticated: as categorias são catálogo público,
    # a montra da SPA mostra-as sem login.
    permission_classes = [AllowAny]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category")
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    search_fields = ["name", "sku"]
    ordering_fields = ["price", "name", "created_at"]
    ordering = ["name"]
    # Toda a gente lê o catálogo; só o grupo "gestores" cria, altera ou apaga.
    permission_classes = [IsGestorOrReadOnly]


class CustomerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Customer.objects.select_related("user")
    serializer_class = CustomerSerializer
    search_fields = ["user__username", "user__email"]

    def get_queryset(self):
        qs = super().get_queryset()
        if getattr(self, "swagger_fake_view", False):
            return qs.none()
        if is_gestor(self.request.user):
            return qs
        # User só vê o seu próprio perfil.
        return qs.filter(user=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    filterset_class = OrderFilter
    ordering_fields = ["created_at", "total"]
    ordering = [
        "-created_at"
    ]  # explícito: annotate() perde o Meta.ordering · annotate() drops Meta.ordering
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    # Camada 2: has_object_permission em retrieve, update, destroy
    # e ações detail=True (pay, cancel).
    permission_classes = [IsAuthenticated, IsOwnerOrGestor]

    def get_queryset(self):
        items = OrderItem.objects.select_related("product").annotate(
            line_total=F("quantity") * F("unit_price")
        )
        qs = (
            Order.objects.select_related("customer__user")
            .prefetch_related(Prefetch("items", queryset=items))
            .annotate(total=Sum(LINE_TOTAL))
        )
        if getattr(self, "swagger_fake_view", False):
            return qs.none()
        if is_gestor(self.request.user):
            return qs
        # Camada 1: o cliente só "vê" as suas encomendas. Uma encomenda alheia
        # retorna 404 ao invés de 403.
        return qs.filter(customer__user=self.request.user)

    def perform_create(self, serializer):
        customer = Customer.objects.filter(user=self.request.user).first()
        if customer is None:
            raise ValidationError(
                {"customer": ["O utilizador autenticado não tem perfil de cliente."]}
            )
        serializer.save(customer=customer)

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

    def get_queryset(self):
        qs = super().get_queryset()
        if getattr(self, "swagger_fake_view", False):
            return qs.none()
        if is_gestor(self.request.user):
            return qs
        return qs.filter(order__customer__user=self.request.user)

    def _check_order_owner(self, order):
        # Não se pode acrescentar/mover linhas para a encomenda de outro cliente.
        if not is_gestor(self.request.user) and order.customer.user_id != self.request.user.id:
            raise NotFound()

    def perform_create(self, serializer):
        self._check_order_owner(serializer.validated_data["order"])
        serializer.save()

    def perform_update(self, serializer):
        self._check_order_owner(serializer.validated_data.get("order", serializer.instance.order))
        serializer.save()


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.select_related("order")
    serializer_class = PaymentSerializer
    filterset_fields = ["order", "method"]

    def get_queryset(self):
        qs = super().get_queryset()
        if getattr(self, "swagger_fake_view", False):
            return qs.none()
        if is_gestor(self.request.user):
            return qs
        return qs.filter(order__customer__user=self.request.user)


# Ficha 05: relatório assíncrono — a vista só enfileira (202 Accepted); o trabalho é do worker

TASK_OWNER_TTL = 3600  # 1 h: depois disso a tarefa é "desconhecida" (404)


def task_owner_key(task_id):
    return f"task:{task_id}:owner"


class OrdersReportView(APIView):
    @extend_schema(
        request=None,
        responses={
            202: TaskAcceptedSerializer,
            400: OpenApiResponse(description="Utilizador sem perfil de cliente"),
        },
    )
    def post(self, request):
        if is_gestor(request.user):
            customer_id = None  # o gestor vê todas as encomendas
        else:
            customer = Customer.objects.filter(user=request.user).first()
            if customer is None:
                raise ValidationError(
                    {"customer": ["O utilizador autenticado não tem perfil de cliente."]}
                )
            customer_id = customer.id

        # Ficha 05: id gerado antes de enfileirar, para o dono ficar gravado primeiro — o
        # worker pode acabar antes de esta vista responder, e o GET já tem de saber de quem é
        task_id = str(uuid4())
        cache.set(task_owner_key(task_id), request.user.id, TASK_OWNER_TTL)
        export_orders_report.apply_async(args=(request.user.id, customer_id), task_id=task_id)

        # 202 Accepted: aceite, ainda não feito; o Location diz onde perguntar pelo estado
        status_url = reverse("task-status", args=[task_id])
        return Response(
            {"id": task_id, "status_url": status_url},
            status=status.HTTP_202_ACCEPTED,
            headers={"Location": status_url},
        )


class TaskStatusView(APIView):
    @extend_schema(
        responses={
            200: TaskStatusSerializer,
            404: OpenApiResponse(description="Tarefa desconhecida, expirada ou de outro"),
        },
    )
    def get(self, request, task_id):
        owner = cache.get(task_owner_key(task_id))
        # Ficha 05: o AsyncResult não sabe de quem é a tarefa — a regra vem da cache. Alheia
        # ou desconhecida → 404, como as encomendas (não se confirma que existe)
        if owner is None or (owner != request.user.id and not is_gestor(request.user)):
            raise NotFound()

        # Lê o estado no result backend (/0): PENDING, PROGRESS, SUCCESS, FAILURE…
        result = AsyncResult(task_id)
        state = result.state
        return Response(
            {
                "id": task_id,
                "state": state,
                "progress": result.info if state == "PROGRESS" else None,
                "result": result.result if state == "SUCCESS" else None,
                # Só o tipo da exceção: o traceback fica no log do worker
                "error": type(result.result).__name__ if state == "FAILURE" else None,
            }
        )
