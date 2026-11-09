# Ficha 04 — Reflexão

1. **Guard de rota vs. segurança:** sem o guard (removido nas DevTools) ou com `curl` sem sessão, 
`/api/v1/orders/` devolve `401` (Problem Details) e a vista fica em estado de erro, sem dados; 
com o token de outro cliente, as encomendas alheias dão `404`. 
Quem protege os dados é o servidor: `IsAuthenticated` por omissão, `IsOwnerOrGestor` e o queryset filtrado em `OrderViewSet.get_queryset`. 
O guard (`router.beforeEach` com `meta.requiresAuth`) é só UX: redireciona logo para `/login?next=...` em vez de mostrar um ecrã que ia falhar.

2. **Dinheiro como string:** o DRF serializa `DecimalField` como string (`COERCE_DECIMAL_TO_STRING`) 
porque o JavaScript lê qualquer número JSON como float binário (IEEE 754): `0.1 + 0.2 = 0.30000000000000004`, 
e somar preços assim acumula erros e perde cêntimos face ao total do servidor. 
A aritmética de dinheiro vive no servidor, em `Decimal` (`unit_price` copiado no servidor, 
`Sum(LINE_TOTAL)` no `OrderViewSet` e `order_total()` em `services.py`); 
na SPA, a soma do formulário (`toCents` em `NewOrderView.vue`, em cêntimos inteiros) é só uma estimativa visual.

## Ficha 04 — Declaração de uso de IA

- **Contexto:** sendo uma entrega de dimensão inferior comparativamente a um projeto e bem delimitada, 
  usei esta ficha também para experimentar pela primeira vez o Claude Code
  para perceber as suas capacidades e limites — trabalho por fases, commits, verificação automática e relatórios.
- **Parte 1 (scaffold, lista, detalhe, teste do ProductCard):** feita por mim, com apoio
  do Claude (claude.ai) — explicação de cada passo, revisão de erros e de outputs do terminal.
- **Parte 2 (cliente OpenAPI, store, login e guard, encomendas, formulário, testes):**
  implementada com o Claude Code a partir de um plano por fases que preparei com o
  Claude; revi o relatório de cada fase antes de autorizar a seguinte, e os commits
  dessa parte estão marcados como co-autoria ("Co-Authored-By: Claude").
- **Verificação:** testado manualmente no browser.
- **O que aprendi com o Claude Code:** funciona bem quando o pedido está dividido em
  fases verificáveis; apanhou falhas que me tinham escapado (o `env.d.ts` por gravar) e
  propôs melhorias (renovação única do token, proteção do `next`); mas não testa no
  browser — a verificação manual, a revisão de cada desvio e a presença humana continuam a ser 
  necessárias. Em contrapartida, acelera a implementação, a verificação de checklists e a 
  deteção de erros, e torna a aprendizagem mais rápida.
- **Reflexão (`docs/ficha-04.md`):** respostas escritas por mim, com revisão de
  coerência pelo Claude e confirmação, no código, das referências citadas.
