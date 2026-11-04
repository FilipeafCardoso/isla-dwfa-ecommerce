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

## Comandos

| Comando | O que faz |
|---|---|
| `npm run dev` | servidor de desenvolvimento |
| `npm run type-check` | `vue-tsc`: zero erros de tipos |
| `npm run lint` | oxlint + ESLint |
| `npm run build` | build de produção em `dist/` |
| `npm run test:unit -- --run` | testes Vitest (sem `--run` fica em modo watch) |

## O que está cá

- `src/types.ts` — tipos da API: `Category`, `Product` (`price` é string), `Paginated<T>`, `Problem`
- `src/api/client.ts` — `get<T>(path, query?)` sobre `fetch`, com `ApiError` (Problem Details)
- `src/composables/useFetch.ts` — os três estados (a carregar · erro · dados) + `reload`
- `src/views/ProductsView.vue` — lista com pesquisa e paginação no URL (`?search=`, `?page=`)
- `src/views/ProductView.vue` — detalhe do produto (rota lazy), com os `attributes` num `<dl>`
- `src/views/NotFoundView.vue` — página do catch-all
- `src/components/ProductCard.vue` — cartão de produto, emite `select` com o id
- `src/components/__tests__/` — testes Vitest

## Rotas

| Rota | Vista |
|---|---|
| `/` | redireciona para `/products` |
| `/products` | lista |
| `/products/:id` | detalhe (só ids numéricos) |
| qualquer outra | `NotFoundView` |