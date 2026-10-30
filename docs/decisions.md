# Decisões · Decisions

PT: uma linha por decisão — o quê, porquê, alternativa rejeitada. Cresce ficha a ficha; o M1/M2/M3 avaliam este ficheiro.
EN: one line per decision — what, why, rejected alternative. Grows ficha by ficha; M1/M2/M3 grade this file.

## Esqueleto · Skeleton

- **`AUTH_USER_MODEL = "accounts.User"` desde o dia zero** — trocar depois da primeira migração obriga a reescrever o histórico; um `AbstractUser` vazio não custa nada. · Declared on day zero; swapping later means rewriting migration history; an empty `AbstractUser` is free.
- **Settings por ambiente (`base/dev/test/prod`) com `django-environ`** — o mesmo código em todos os ambientes, só as variáveis mudam (12-factor); segredos fora do git. · Same code everywhere, only env vars change; secrets stay out of git.
- **`/api/health/` devolve 503, não 500, com a base de dados em baixo** — é o código que um load balancer lê como "tira esta instância de rotação". · 503 is what a load balancer reads as "take this instance out of rotation".

## Ficha 02 — modelos · models

- **`Order.customer` com `on_delete=PROTECT`** (e `Product.category`, `OrderItem.product`) — uma encomenda é um registo contabilístico e não desaparece com o cliente; só `OrderItem.order` e `Payment.order` são CASCADE porque não existem sem a encomenda. Rejeitado: CASCADE em tudo, que apagaria histórico de vendas. · An order is an accounting record; only lines and payments cascade. Rejected: CASCADE everywhere, which would delete sales history.
- **`UniqueConstraint(order, product)` em `OrderItem`** — o mesmo produto duas vezes na mesma encomenda é um erro de cliente; a constraint apanha-o em todos os caminhos de escrita (admin, shell, serializer). Mais `CheckConstraint` em `quantity > 0`, `price >= 0`, `amount > 0`. · Same product twice in an order is a client error; the DB catches it on every write path.
- **JSONB sim, em `Product.attributes`** — atributos variam por categoria (cor, tamanho, voltagem) e não são filtrados nesta fase; uma tabela EAV ou colunas por categoria seriam mais caras para nenhum ganho. Sem `GinIndex` até haver uma query que o justifique (Aula 09). · Per-category attributes with no fixed schema; EAV or per-category columns rejected; no GIN index until a query needs it.
- **Índice composto `(customer, created_at)` em `Order`** — a listagem "as minhas encomendas, mais recentes primeiro" é a query mais frequente da loja. · The most frequent shop query is "my orders, newest first".

## Ficha 02 — API

- **`unit_price`, `total`, `status`, `created_at` só de leitura** — o preço é copiado do produto no servidor (`OrderItemSerializer.create`), o total vem de `annotate`, o estado só muda por `pay`/`cancel`; nada disto vem do cliente. · Price copied on the server, total annotated, status only via actions; none of it comes from the client.
- **`PageNumberPagination`, `PAGE_SIZE = 20`** — simples e suficiente para catálogos pequenos; `CursorPagination` quando a tabela de encomendas crescer e `?page=500` começar a custar (candidato a tema do trabalho de investigação). · Simple and enough for a small catalogue; cursor pagination when offset pages get expensive.
- **Versionamento por URL (`/api/v1/`)** — visível, cacheável, fácil de rotear no Nginx; rejeitado o versionamento por cabeçalho `Accept`, mais "correto" mas invisível no browser e no Swagger. · URL versioning is visible and routable; header versioning rejected as invisible in the browser and Swagger.
- **Queries na lista de encomendas: 82 sem `prefetch_related`, 3 com** (25 encomendas × 3 linhas: `COUNT` + encomendas com JOIN de cliente/utilizador + linhas com JOIN de produto). O teste `test_order_list_is_paginated_without_n_plus_one` falha no dia em que alguém remover o prefetch. · 82 queries without the prefetch, 3 with it; the test fails the day someone removes it.
- **Erros no formato Problem Details (RFC 9457)** via `EXCEPTION_HANDLER` — um só envelope (`type`, `title`, `status`, `errors`) para 400/404/409/429; o que não é exceção DRF continua a ser 500, um bug a registar. · One error envelope for every DRF error; non-DRF exceptions stay 500.
- **`pay` e `cancel` em `services.py` com `select_for_update`** — a transição de estado corre numa transação com bloqueio de linha; dois `POST /pay/` concorrentes não pagam duas vezes. A vista só traduz a exceção `Conflict` em 409. · State transitions lock the row; the view only maps `Conflict` to 409.

## Ficha 03 — Matriz de autorização (endpoint × papel)

| Endpoint | Anónimo | Cliente | Gestor |
|---|---|---|---|
| POST /auth/token/ | 200 (credenciais válidas) / 401 | 200 | 200 |
| GET /me/ | 401 | 200 | 200 |
| GET /categories/, /categories/{id}/ | 200 | 200 | 200 |
| GET /products/, /products/{id}/ | 200 | 200 | 200 |
| POST /products/ | 401 | 403 | 201 |
| PATCH /products/{id}/ | 401 | 403 | 200 |
| DELETE /products/{id}/ | 401 | 403 | 204 |
| GET /customers/ | 401 | 200 (só o seu) | 200 (todos) |
| GET /customers/{id}/ (alheio) | 401 | 404 | 200 |
| GET /orders/ | 401 | 200 (só as suas) | 200 (todas) |
| GET /orders/{id}/ (própria) | 401 | 200 | 200 |
| GET /orders/{id}/ (alheia) | 401 | 404 | 200 |
| POST /orders/ | 401 | 201 (customer = request.user) | 400 (sem perfil de cliente) |
| PATCH / DELETE /orders/{id}/ (alheia) | 401 | 404 | 200 / 204 |
| POST /orders/{id}/pay/ (própria, pendente) | 401 | 200 | 200 |
| POST /orders/{id}/pay/ (alheia) | 401 | 404 | 200 |
| POST /orders/{id}/cancel/ (alheia) | 401 | 404 | 200 |
| GET /order-items/ | 401 | 200 (só das suas encomendas) | 200 (todas) |
| POST /order-items/ (encomenda alheia) | 401 | 404 | 201 |
| GET /payments/ | 401 | 200 (só das suas encomendas) | 200 (todos) |

Decisões:
- Catálogo (categorias e produtos) com leitura pública ("toda a gente lê").
- Recurso alheio → 404 e não 403: não se confirma que existe.
- `customer`, `status` e `total` são só de leitura no OrderSerializer.
- **check --deploy:** corrido com uma SECRET_KEY gerada (`secrets.token_urlsafe(50)`); 
em produção a chave vem do ambiente.

## Ficha 03 — Sem o filtro do get_queryset

Com `return qs.filter(customer__user=...)` comentado, falharam 3 testes:
- `test_list_orders_by_role[customer-200-1]`: o cliente viu 2 encomendas em vez de 1;
a listagem não passa pelo has_object_permission, só o queryset a protege.
- `test_foreign_order_is_404_for_customer[get]` e `[pay]`: 403 em vez de 404 — o
  IsOwnerOrGestor ainda bloqueou o acesso, mas o 403 revela que a encomenda existe.

Conclusão: o queryset filtrado protege a listagem e esconde a existência
(404); has_object_permission funciona como segunda linha de defesa.
