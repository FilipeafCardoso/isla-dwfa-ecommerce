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
- **Queries na lista de encomendas: 82 sem `prefetch_related`, 4 com** (25 encomendas × 3 linhas: `COUNT` + encomendas com JOIN de cliente/utilizador + linhas com JOIN de produto + 1 do `is_gestor()` aos grupos, acrescentada na Ficha 03). O teste `test_order_list_is_paginated_without_n_plus_one` falha no dia em que alguém remover o prefetch. · 82 queries without the prefetch, 4 with it (+1 group lookup since Ficha 03); the test fails the day someone removes it.
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
| POST /auth/token/ (11.ª tentativa no mesmo minuto) | 429 | 429 | 429 |
| POST /auth/token/refresh/ | 200 (refresh válido) / 401 (inválido ou na blacklist) | 200 | 200 |
| PUT /products/{id}/ | 401 | 403 | 200 |
| PATCH / DELETE /orders/{id}/ (própria) | 401 | 200 / 204 | 200 / 204 |
| POST /orders/{id}/cancel/ (própria, pendente) | 401 | 200 | 200 |
| GET / PATCH / DELETE /order-items/{id}/ (alheio) | 401 | 404 | 200 / 204 |
| POST /order-items/ (encomenda própria) | 401 | 201 | 201 |
| GET /payments/{id}/ (alheio) | 401 | 404 | 200 |

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

## Ficha 03 — Tokens JWT

- **Tempos de vida:** access 30 min, refresh 1 dia, com `ROTATE_REFRESH_TOKENS` e
  `BLACKLIST_AFTER_ROTATION`: cada refresh devolve um par novo e invalida o anterior,
  por isso um refresh roubado só serve uma vez. O access curto limita a janela de
  abuso se for intercetado.
- **Onde a SPA guarda os tokens:** em memória, não em localStorage — o localStorage é 
  legível por qualquer script da página, logo fica exposto a XSS. 
  O custo é perder a sessão ao recarregar a página (novo login).
  *Revisto na Ficha 04: refresh em localStorage (ver "Ficha 04 — SPA (parte 2)").*
  Alternativa mais robusta para o futuro: refresh num cookie HttpOnly + Secure +
  SameSite, que o JavaScript não consegue ler (exige uma vista própria e proteção CSRF).

Conclusão: o queryset filtrado protege a listagem e esconde a existência
(404); has_object_permission funciona como segunda linha de defesa.


## Ficha 03 — Decisões

- **Leitura pública do catálogo:** `IsGestorOrReadOnly` devolve `True` em
  SAFE_METHODS. Desvio intencional ao código de exemplo do enunciado (que exigia
  login para ler), para cumprir "toda a gente lê" e manter a montra da SPA sem login.
- **check --deploy:** com `SECRET_KEY=x` o Django emite `security.W009` (chave curta
  e previsível), e com razão. Validado com uma chave gerada
  (`secrets.token_urlsafe(50)`) → 0 issues. Em produção a chave vem só do ambiente.
- **Filtro também em Customer, OrderItem e Payment:** expunham dados de outros
  clientes; aplicado o mesmo padrão (gestor vê tudo, cliente só os seus → 404).
- **MeSerializer:** documenta a resposta de `/me/` no Swagger e elimina o aviso
  `drf_spectacular.W002` do check.
- **Migrações da blacklist:** vêm do pacote `djangorestframework-simplejwt`
  (versão fixada no `uv.lock`); a migração própria commitada é a do grupo `gestores`.


## Ficha 04 — SPA (parte 1)

- **`frontend/` no mesmo repositório da API:** a SPA e o Django mudam juntos (o tipo
  é o contrato com a API) e o M2 entrega SPA, CI e Docker num só repositório.
- **CORS em vez do proxy do Vite:** a SPA chama `http://localhost:8000` diretamente e
  o Django autoriza a origem `http://localhost:5173` (Ficha 03). Com o proxy, o
  browser veria uma só origem e o CORS deixava de ser exercitado em dev — e em
  produção as origens vão ser diferentes de qualquer forma.
- **O URL como estado da lista:** `?search=` e `?page=` vivem em `route.query` (um
  `computed` com get/set), não num `ref`. Recarregar, voltar atrás ou partilhar o
  link mantém a pesquisa e a página.
- **Rota do detalhe lazy:** `component: () => import(...)` gera um chunk à parte
  (`ProductView-<hash>.js`, ~1 kB); quem só vê a lista não descarrega o código do
  detalhe.
- **`useFetch` ignora respostas antigas:** cada pedido tem um número e só o mais
  recente atualiza os dados, para que uma pesquisa rápida não mostre os resultados
  de uma pesquisa anterior.

## Ficha 04 — SPA (parte 2)

- **Tokens (revê a Ficha 03):** `access` só em memória (store Pinia); `refresh` em
  `localStorage` para sobreviver ao F5, rodado a cada uso e com blacklist (um refresh
  roubado só serve uma vez). Rejeitado o cookie HttpOnly: a API passaria a emitir cookies
  e a precisar de CSRF outra vez. Rejeitado "só memória": obrigava a novo login a cada F5.
- **Renovação:** o middleware do openapi-fetch envia `Bearer`; num 401 renova **uma vez** e
  repete o pedido (um 401 na repetição é definitivo). Uma só renovação em curso
  (single-flight), porque com rotação + blacklist uma segunda renovação com o mesmo refresh
  falharia; se a renovação falhar → `logout()` e `/login?next=`.
- **Tipos gerados do OpenAPI:** `openapi-fetch` + `src/api/schema.d.ts` (`npm run gen:api`),
  com `types.ts` só com aliases; `COMPONENT_SPLIT_REQUEST: True` na API para separar pedido
  e resposta (sem isso, campos read_only como `access` apareciam obrigatórios no body).
- **Campos da resposta obrigatórios no schema:** o hook `shop.schema.require_response_fields`
  marca todas as propriedades dos componentes de resposta como `required`; o DRF devolve-as
  sempre, mas `stock`/`is_active` (com default no modelo) e `next`/`previous` saíam
  opcionais. Rejeitado estreitar em `types.ts` (`Product & { stock: number }`): a resposta
  do `api.GET` continuava com `stock?` e cada chamada precisaria de um cast.
- **`overrides` do TypeScript para o `openapi-typescript`:** a 7.x declara
  `peer typescript@^5.x` e o projeto usa TS 6; o `overrides` em `package.json` aplica-se só
  a esse pacote (o ficheiro gerado foi verificado). Rejeitado `--legacy-peer-deps`, que
  desliga a verificação de peers em todas as dependências.
- **Guard:** protege o ecrã, não os dados — sem token, `GET /api/v1/orders/` continua a
  devolver 401; a autorização é da API (401/403/404 da Ficha 03).
- **`next` do login:** só caminhos internos — tem de começar por `/` e não por `//`
  (`//evil.com` é um URL de outro domínio para o browser).
- **Erros:** 400 ao lado do campo (`ApiError.field`), 409 como mensagem + recarregar a lista
  (não é o estado de erro do ecrã), 429 no login como frase.
- **Dinheiro:** o total do formulário é uma estimativa somada em cêntimos inteiros a partir
  das strings; o total que conta é o `Decimal` da API (`annotate(Sum(...))`).
- **Nova encomenda:** `POST /orders/` + um `POST /order-items/` por linha (o
  `OrderSerializer` não aceita `items` aninhados); ao corrigir erros reutiliza-se a mesma
  encomenda e só se reenviam as linhas pendentes.
- **Linhas aceites bloqueadas:** as linhas que já deram 201 ficam desativadas
  (`<fieldset disabled>`, "✓ Adicionada"), porque já estão gravadas na encomenda e
  editá-las no formulário não as alteraria na API.
- **Limitação — encomenda vazia:** se a encomenda for criada mas todas as linhas forem
  rejeitadas e o utilizador sair, fica uma encomenda `pending` sem linhas; a API recusa
  pagá-la (409 "has no items"). Rejeitado por agora um endpoint que crie encomenda e linhas
  numa só transação (escrita aninhada), por sair do âmbito da ficha.

## Ficha 05 — Tarefas assíncronas

- **Idempotência:** o recibo marca `Payment.receipt_sent_at` numa transação com
  `select_for_update`; uma segunda entrega (o broker garante *pelo menos uma vez*,
  `acks_late=True`) vê o campo preenchido e devolve `already-sent` sem reenviar.
  Limitação: se o worker morrer entre o `send_mail` e o commit, o email pode sair
  duas vezes.
- **Retry só no transitório:** `autoretry_for=(ReceiptGatewayError,)` com backoff
  exponencial e jitter (por isso o log mostra esperas entre 0 e 2 s na 1.ª tentativa);
  `SMTPException`/`OSError` passam a `ReceiptGatewayError`, e um `DoesNotExist` falha à
  primeira. Rejeitado `autoretry_for=(Exception,)`: repetia erros que nunca se resolvem.
- **`on_commit`:** o recibo só é enfileirado depois do commit do `pay` — sem isso o worker
  podia ler a encomenda antes de estar gravada como paga, ou receber o id de uma transação
  que fez rollback. A tarefa recebe o id, nunca o objeto (estaria velho no worker).
- **Dono da tarefa e 404:** o dono fica na cache (Redis, base `/1`, 1 h), gravado **antes**
  de enfileirar(com um id gerado à partida: se fosse depois do `.delay()`, como no slide 13, 
  a tarefa podia acabar antes de o dono existir na cache); tarefa alheia ou desconhecida → 404, 
  a mesma regra das encomendas (não se confirma que existe). O `AsyncResult` sozinho não sabe de 
  quem é a tarefa. A rota aceita `<str:task_id>` (não `<uuid:>`) para um id inválido dar o mesmo
  404 em Problem Details.
- **202 em vez de 200:** a vista só enfileira e responde com `status_url` e `Location`; o
  trabalho e o progresso (`PROGRESS` com `current`/`total`) vivem no worker e no result
  backend. Em `FAILURE` a API devolve só o nome da exceção; o traceback fica no log.
- **Redis por bases:** `/0` broker e resultados, `/1` cache do Django (inclui o throttle do
  login e o dono das tarefas).
- **Testes sem Redis:** `CELERY_TASK_ALWAYS_EAGER` + result backend e cache em memória, para
  o CI correr sem serviços extra; `REPORT_ITEM_DELAY = 0` nos testes.
- **Import local em `pay_order()`:** `tasks.py` usa `order_total()` de `services.py`; o
  import de `send_order_receipt` fica dentro da função para evitar o import circular.
- **Como correr:** `docker compose up -d` · `uv run manage.py runserver` ·
  `uv run celery -A config worker -l info` (terminal 2).
  
  ## Ficha 05 — Declaração de uso de IA

- **Planeamento:** preparei com o Claude um plano por fases a partir do
  enunciado e dos slides da Aula 07 (Parte 1 + Parte 2).
- **Implementação:** auxiliada pelo Claude e CLaude Code.
- **Verificação:** testado manualmente o recibo no worker (email na consola, `already-sent`,
  worker parado com `LLEN celery = 1` e o recibo a sair ao religar) e o relatório com `curl`
  (202, `PROGRESS` a subir, `SUCCESS`, 404 com o token do bruno); `pytest` (34 testes),
  `ruff`, `check --deploy` e os quatro comandos da SPA correm limpos. Por fim, foi passada
  uma checklist ao claude code para verificar ponto a ponto (foi também pedido ao Claude Code,
  tendo em conta o trabalho realizado, comentários objetivos sobre as novas alterações).
