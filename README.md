# Ficha 02 — Modelos, ORM e migrações · REST com DRF · Models, ORM, migrations · REST with DRF

Aulas 02 + 03 (17 e 19/10/2026) · solução de referência · reference solution

**PT** — Os alunos entregaram o seu *fork* do esqueleto `isla-dwfa-ecommerce` com o domínio da loja (`shop`) e a API. Não é a única resposta certa: comparem com o vosso código (`git diff`, ou lado a lado). Seis entidades — `Category`, `Product`, `Customer`, `Order`, `OrderItem`, `Payment` — com `on_delete` deliberado, constraints e índices em `Meta`, JSONB em `Product.attributes`; migração lida antes de aplicada; seed idempotente com factory_boy; API em `/api/v1/` com serializers explícitos, viewsets sem N+1, filtros/pesquisa/ordenação/paginação, ação `pay` (409 ao repetir), erros em Problem Details (RFC 9457) e OpenAPI em `/api/docs/`. Autenticação e permissões ficam para a Ficha 03 — esta semana `AllowAny`, de propósito.
**EN** — Students submitted their fork of the `isla-dwfa-ecommerce` skeleton with the shop domain (`shop`) and the API. Not the only correct answer: compare it with your own code. Six entities with deliberate `on_delete`, `Meta` constraints and indexes, JSONB on `Product.attributes`; migration read before applied; idempotent seed with factory_boy; API at `/api/v1/` with explicit serializers, N+1-free viewsets, filters/search/ordering/pagination, a `pay` action (409 when repeated), Problem Details errors (RFC 9457) and OpenAPI at `/api/docs/`. Authentication and permissions come in Ficha 03 — `AllowAny` this week, on purpose.

```sh
cp .env.example .env                                # porta 5432 ocupada? · port busy? → :5433 aqui e no compose
docker compose up -d && uv sync                     # PostgreSQL 16 "healthy" · .venv
uv run python manage.py sqlmigrate shop 0001        # ler o SQL · read the SQL (constraints, indexes)
uv run python manage.py migrate
uv run python manage.py seed && uv run python manage.py seed   # idempotente · idempotent: "0 new orders" na 2.ª vez
uv run python manage.py createsuperuser
uv run python manage.py runserver                   # /api/v1/ · /api/docs/ · /admin/
uv run pytest                                       # 12 testes verdes · 12 green tests (4 esqueleto + 3 modelos + 5 API)
uv run ruff check . && uv run ruff format --check . # como no CI · as in CI
```

Python 3.13 · uv · Docker Compose v2 · Git.

## Como foi feito · How it was built

```sh
uv run python manage.py startapp shop               # + "shop" em INSTALLED_APPS
uv add djangorestframework django-filter drf-spectacular
uv run python manage.py makemigrations shop --name initial_domain
uv run python manage.py spectacular --file schema.yaml
```

`shop/models.py` · `admin.py` · `factories.py` · `management/commands/seed.py` (sábado · Saturday) — `serializers.py` · `filters.py` · `services.py` · `api.py` · `views.py` · `urls.py` + `REST_FRAMEWORK`/`SPECTACULAR_SETTINGS` em `config/settings/base.py` e `api/v1/`, `api/schema/`, `api/docs/` em `config/urls.py` (segunda · Monday) — `docs/decisions.md` · `docs/ficha-02.md` · `schema.yaml`.

## O que se verifica · What to check

1. `\d+ shop_orderitem` no `psql` mostra `orderitem_unique_product_per_order` e `orderitem_quantity_gt_0`; `\d+ shop_order` mostra `order_customer_created_idx` · constraints and index with the names given in `Meta`.
2. Todas as FKs têm `on_delete` deliberado e `related_name`; `Order.customer` e `Product.category` são `PROTECT`, só linhas e pagamento são `CASCADE` · every FK has a deliberate `on_delete`; only lines and payment cascade.
3. `seed` corrido duas vezes → "0 new orders (30 total)" · run twice → no duplicates.
4. `/api/v1/orders/` devolve o envelope `{"count","next","previous","results"}` com `items` aninhados e `total` calculado em `annotate` — **3 queries** para 20 encomendas (`test_order_list_is_paginated_without_n_plus_one`); sem o `Prefetch` são 82 · 3 queries for the list; 82 without the prefetch.
5. `POST /api/v1/orders/1/pay/` → 200 e `status: paid`; repetido → **409** com corpo Problem Details (`type`, `title`, `status`, `errors`) · repeated → 409 with a Problem Details body.
6. `GET /api/v1/products/?min_price=10&search=lamp&ordering=-price&page=1` → 200 só com os produtos esperados; `ordering_fields` e `search_fields` explícitos · explicit allowlists.
7. `POST /api/v1/order-items/` com `quantity > stock` → 400 com `errors.quantity`; o `unit_price` vem do produto, nunca do cliente · price copied on the server.
8. `/api/docs/` lista todos os endpoints e a ação `pay` com respostas 200 e 409 (`@extend_schema`); `schema.yaml` commitado · schema committed.
9. `docs/decisions.md` com seis decisões e o número de queries sem prefetch; `docs/ficha-02.md` com as duas respostas · six decisions and the two answers.

## Erros comuns · Common mistakes

- `fields = "__all__"` ou `status`/`unit_price`/`total` escrevíveis — o cliente paga a encomenda com um `PATCH` · writable server-owned fields let a client "pay" with a `PATCH`.
- `prefetch_related("items__product")` em vez de `Prefetch("items", queryset=…select_related("product"))` — uma query a mais (4 em vez de 3) · one extra query.
- `annotate()` sem `ordering = [...]` explícito no viewset — perde-se o `Meta.ordering` e a paginação fica instável · `annotate()` drops `Meta.ordering`; pagination becomes unstable.
- `throttle_scope`/`basename` esquecidos: um viewset sem atributo `queryset` precisa de `basename` no router · a viewset without `queryset` needs a `basename`.
- Lógica do `pay` dentro da vista, sem `services.py` nem `select_for_update` — dois pedidos concorrentes pagam duas vezes · two concurrent requests pay twice.
- `seed` "idempotente" que apaga e recria, ou que só corre com a tabela vazia · a seed that deletes and recreates is not idempotent.
- Tag `ficha-02-api` criada antes dos últimos commits; `docs/ficha-02.md` com outro nome · tag before the last commits; renamed docs file.
- `shop/tests.py` vazio ao lado de `shop/tests/` — o pytest falha na recolha (`import file mismatch`) · an empty `tests.py` next to `tests/` breaks collection.
