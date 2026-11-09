# Frontend — ISLA Shop (SPA)

SPA em Vue 3 + TypeScript + Vite, cliente da API Django deste repositório

## Como correr

1. **API** (na raiz do repositório):

   ```bash
   docker compose up -d
   uv run manage.py migrate
   uv run manage.py seed
   uv run manage.py runserver        # http://localhost:8000
   ```

2. **SPA** (nesta pasta, `frontend/`):

   ```bash
   cp .env.example .env              # VITE_API_URL=http://localhost:8000
   npm install
   npm run dev                       # http://localhost:5173
   ```

   O Vite só lê o `.env` ao arrancar: depois de o alterar, reiniciar o `npm run dev`.

**Conta de demonstração** (criada pelo `seed`): `ana` / `pass1234`, com 10 encomendas.

### Depois de mudar a API

Os tipos da SPA são gerados do schema OpenAPI. Sempre que um serializer ou uma view mudar:

```bash
uv run manage.py spectacular --file schema.yaml --validate   # na raiz
npm run gen:api                                              # em frontend/
```

O `src/api/schema.d.ts` nunca se edita à mão (está no `.prettierignore`).

## Comandos

| Comando | O que faz |
|---|---|
| `npm run dev` | servidor de desenvolvimento |
| `npm run gen:api` | gera `src/api/schema.d.ts` a partir de `../schema.yaml` |
| `npm run type-check` | `vue-tsc`: zero erros de tipos |
| `npm run lint` | oxlint + ESLint |
| `npm run build` | build de produção em `dist/` |
| `npm run test:unit -- --run` | testes Vitest (sem `--run` fica em modo watch) |

## O que está cá

- `src/api/schema.d.ts` — tipos gerados do OpenAPI (`npm run gen:api`)
- `src/api/client.ts` — cliente `openapi-fetch` tipado, `unwrap()` e `ApiError` (`field()`, `detail`)
- `src/api/auth.ts` — middleware: `Bearer` em cada pedido; num 401 renova uma vez e repete
- `src/stores/auth.ts` — sessão (Pinia): `access` em memória, `refresh` em `localStorage`, `login`, `logout`, `refreshAccess` (single-flight), `bootstrap`
- `src/types.ts` — aliases dos tipos gerados (`Product`, `Order`, `OrderStatus`, `Me`…) + `Problem`
- `src/composables/useFetch.ts` — os três estados (a carregar · erro · dados) + `reload`
- `src/views/ProductsView.vue` — lista com pesquisa e paginação no URL (`?search=`, `?page=`)
- `src/views/ProductView.vue` — detalhe do produto, com os `attributes` num `<dl>`
- `src/views/LoginView.vue` — login; mensagens para 401 e 429; volta ao `?next=`
- `src/views/OrdersView.vue` — as minhas encomendas, pagamento (409 como mensagem)
- `src/views/NewOrderView.vue` — nova encomenda com várias linhas e erros da API por linha
- `src/views/NotFoundView.vue` — página do catch-all
- `src/components/ProductCard.vue` — cartão de produto, emite `select` com o id
- `src/components/OrderStatusBadge.vue` — estado da encomenda (switch exaustivo sobre o enum)

### Testes

- `src/components/__tests__/ProductCard.spec.ts` — nome como texto; clique emite `select`
- `src/components/__tests__/OrderStatusBadge.spec.ts` — texto de cada estado
- `src/stores/__tests__/auth.spec.ts` — login (access só em memória), 401, refresh com rotação
- `src/views/__tests__/LoginView.spec.ts` — 401 mostra a mensagem e não sai do login

## Rotas

| Rota | Nome | Acesso | Vista |
|---|---|---|---|
| `/` | — | pública | redireciona para `/products` |
| `/products` | `products` | pública | lista |
| `/products/:id` | `product` | pública | detalhe (só ids numéricos, lazy) |
| `/login` | `login` | pública | login (lazy) |
| `/orders` | `orders` | **privada** | as minhas encomendas (lazy) |
| `/orders/new` | `order-new` | **privada** | nova encomenda (lazy) |
| qualquer outra | `not-found` | pública | `NotFoundView` |

As rotas privadas têm `meta: { requiresAuth: true }`: sem sessão, o guard redireciona para
`/login?next=<rota>`. O guard só protege o ecrã; os dados são protegidos pela API.
