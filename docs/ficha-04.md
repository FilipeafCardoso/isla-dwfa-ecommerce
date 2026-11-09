# Ficha 04 - Reflexão

<!-- TODO: resposta do aluno, ≤ 10 linhas no total -->
<!-- Copiar o texto exato das duas perguntas do enunciado da Ficha 04 para os títulos abaixo. -->

**1. (pergunta 1 do enunciado: o guard de rota e a segurança dos dados)**

<!-- TODO: resposta do aluno -->

Notas para a resposta (factos verificados neste repositório; apagar antes de entregar):
- `curl -s localhost:8000/api/v1/orders/` sem token → `HTTP 401` com
  `{"type":"about:blank","title":"Unauthorized","status":401,"errors":{"detail":"Authentication credentials were not provided."}}`.
- O guard está em `frontend/src/router/index.ts` (`router.beforeEach`, `meta.requiresAuth`):
  corre no browser e decide só que ecrã mostrar.
- Quem protege os dados é a API: `IsAuthenticated` por omissão, `OrderViewSet.get_queryset`
  filtra ao cliente (alheia → 404), `IsOwnerOrGestor` (`shop/views.py`, `shop/permissions.py`).

**2. (pergunta 2 do enunciado: dinheiro como string / Decimal)**

<!-- TODO: resposta do aluno -->

Notas para a resposta (factos verificados neste repositório; apagar antes de entregar):
- Os valores são `DecimalField` no modelo (`shop/models.py`: `Product.price`,
  `OrderItem.unit_price`, `Payment.amount`) e no serializer (`shop/serializers.py`:
  `line_total`, `total`).
- O DRF serializa `Decimal` como string porque `COERCE_DECIMAL_TO_STRING` é `True` por
  omissão (não é alterado em `config/settings`); no schema aparecem como
  `type: string, format: decimal` e no TypeScript como `string` (ex.: `"268.17"`). Um
  `number` de JSON seria um float binário e perderia cêntimos.
- O total da encomenda é calculado na base de dados: `annotate(total=Sum(LINE_TOTAL))` em
  `OrderViewSet.get_queryset` (`LINE_TOTAL = F("items__quantity") * F("items__unit_price")`
  em `shop/models.py`); no pagamento, `order_total()` em `shop/services.py`.
- O `unit_price` é copiado do produto no servidor (`OrderItemSerializer.create`), nunca vem
  do cliente.
- Na SPA, a estimativa do formulário soma em cêntimos inteiros (`toCents` em
  `NewOrderView.vue`); a lista mostra o `total` da API tal como vem.
