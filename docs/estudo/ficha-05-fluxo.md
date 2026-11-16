# Ficha 05 — O fluxo das tarefas assíncronas (notas de estudo)

Âmbito: Parte 1 (recibo) + Parte 2 (relatório). Encontras os comentários no código com
`grep -rn "Ficha 05:"`.

## 1. O fluxo do recibo

1. **SPA "Pagar"** → `POST /api/v1/orders/<id>/pay/` (`frontend/src/views/OrdersView.vue:39`).
2. **Vista** `OrderViewSet.pay` (`shop/views.py:116`) chama `pay_order()`. Continua síncrona e
   responde logo com `paid`.
3. **`pay_order()`** (`shop/services.py:28`) corre dentro de `@transaction.atomic`. O
   `select_for_update` bloqueia a encomenda, depois cria o `Payment` e muda o estado para `paid`.
4. **`transaction.on_commit(...)`** (`shop/services.py:43`) regista o `.delay()`, mas **ainda não
   o envia**.
5. **COMMIT.** Só agora o callback corre e põe a mensagem (só o **id**) na fila `celery` do
   Redis, base `/0`.
6. **Worker** (`celery -A config worker`): lê a mensagem e corre
   `send_order_receipt(order_id)` (`shop/tasks.py:39`):
   1. **bloqueia** o `Payment` com `select_for_update` (`:48`); se não existir →
      `DoesNotExist`, sem retry;
   2. **já enviado?** se `receipt_sent_at` está preenchido → `already-sent` (`:55`);
   3. **envia** com `send_mail` (`:66`); `SMTPException`/`OSError` → `ReceiptGatewayError` → retry;
   4. **marca** `receipt_sent_at` (`:81`) na mesma transação.
7. **`acks_late`**: o worker só confirma a mensagem depois de a tarefa acabar. No log aparece
   `Task shop.tasks.send_order_receipt[…] succeeded … 'sent'`.

## 2. O fluxo do relatório

1. **`POST /api/v1/reports/orders/`** → `OrdersReportView.post` (`shop/views.py:183`). O gestor
   tem `customer_id=None`; o cliente usa o seu `Customer`; quem não tem nenhum dos dois → 400.
2. **Id gerado** antes de tudo: `task_id = str(uuid4())` (`:204`).
3. **Dono na cache** (Redis `/1`): `task:<id>:owner` com o TTL de 1 h (`:205`).
4. **`apply_async(..., task_id=task_id)`** (`:206`) põe a mensagem em `/0`.
5. **202 Accepted** com `{"id", "status_url"}` e `Location` (`:212`), em milissegundos.
6. **Worker:** `export_orders_report` (`shop/tasks.py:87`) faz 1 query com o total anotado e,
   por cada encomenda, `update_state("PROGRESS", {"current", "total"})` (`:105`) e uma pausa.
   No fim devolve `{"orders", "amount" (string), "by_status"}`.
7. **`GET /api/v1/tasks/<id>/`** → `TaskStatusView.get` (`shop/views.py:217`):
   1. **dono?** `cache.get` (`:225`); se não houver ou for de outro (e quem pede não é gestor)
      → **404** (`:229`);
   2. **`AsyncResult(id)`** (`:232`) → `state`, `progress` (em PROGRESS), `result` (em
      SUCCESS), `error` (o nome da exceção, em FAILURE).

## 3. Mapa de ficheiros

| Ficheiro | O que foi acrescentado | Conceito |
|---|---|---|
| `pyproject.toml`, `uv.lock` | `celery[redis]`, `redis` | dependências (CI com `--frozen`) |
| `compose.yaml`, `.env.example` | serviço `redis` com healthcheck; `REDIS_URL` | broker |
| `config/celery.py`, `config/__init__.py` | app Celery, `autodiscover_tasks`, `celery_app` | ligar Celery ao Django |
| `config/settings/base.py` | broker e resultados `/0`, `acks_late`, limites, `CACHES` `/1`, `REPORT_ITEM_DELAY` | Redis por bases |
| `config/settings/test.py` | eager, `cache+memory://`, LocMem, pausa 0 | testes sem Redis |
| `shop/models.py` + `0003_payment_receipt_sent_at` | `Payment.receipt_sent_at` | idempotência |
| `shop/services.py` | `on_commit` em `pay_order()` | depois do commit |
| `shop/tasks.py` | `send_order_receipt`, `export_orders_report` | retry, idempotência, progresso |
| `shop/views.py`, `shop/urls.py`, `shop/serializers.py` | `OrdersReportView`, `TaskStatusView`, rotas, serializers do schema | 202 + estado só para o dono |
| `schema.yaml`, `frontend/src/api/schema.d.ts` | os 2 endpoints novos | contrato da SPA |
| `shop/tests/test_tasks.py`, `test_reports.py` | 10 testes | provas |
| `docs/decisions.md` | secção "Ficha 05 — Tarefas assíncronas" | decisões |

## 4. As regras da aula, onde estão no código

| Regra | Onde | Prova |
|---|---|---|
| Ids, não objetos | `send_order_receipt.delay(order.pk)` (`services.py:43`); `args=(user_id, customer_id)` (`views.py:206`) | — |
| Idempotente (*pelo menos uma vez*) | `receipt_sent_at` + `select_for_update` (`tasks.py:48–55`) | `test_receipt_is_idempotent` |
| Depois do commit | `transaction.on_commit` (`services.py:43`) | `test_pay_enqueues_receipt_on_commit`, `test_receipt_is_not_sent_inside_the_transaction` |
| Retry só no transitório | `autoretry_for=(ReceiptGatewayError,)` (`tasks.py:33`) | `test_unknown_order_fails_without_retry` |
| 202 Accepted | `OrdersReportView` (`views.py:212`) | `test_report_is_accepted_and_counts_only_own_orders` |
| 404 para o que não é teu | dono na cache (`views.py:225–229`) | `test_task_of_another_customer_or_unknown_is_404` |
| Testes sem Redis (eager) | `config/settings/test.py:15–21` | o CI só tem Postgres |

## 5. Comandos

```bash
docker compose up -d                                   # Postgres + Redis
uv run manage.py runserver                             # T1
uv run celery -A config worker -l info                 # T2 (emails aparecem aqui)
RECEIPT_FLAKY=1 uv run celery -A config worker -l info # provoca 1 retry por recibo
docker compose exec redis redis-cli LLEN celery        # mensagens por consumir (worker parado)
docker compose exec redis redis-cli monitor            # ver os comandos do Celery e da cache
docker compose exec redis redis-cli -n 1 --scan --pattern '*task*'   # donos na cache
uv run pytest -q                                       # 34 testes, sem Redis
```

Nota: com o `uv` em snap, um `--logfile` em `/tmp` fica vazio (o snap tem um `/tmp` privado).

## 6. Limitações conhecidas

- **Janela email enviado / commit falhado:** se o worker morrer entre o `send_mail` e o commit
  de `receipt_sent_at`, a nova entrega reenvia o email (duplicado possível, perda não).
- **O dono expira ao fim de 1 h** (`TASK_OWNER_TTL`): depois disso o `GET /tasks/<id>/` dá 404,
  mesmo que o resultado ainda exista no backend.
- **Limite de tempo do relatório:** com 0,2 s por encomenda e `SOFT_TIME_LIMIT = 60`, um
  relatório de gestor com mais de ~300 encomendas excede o limite e acaba em `FAILURE`.
