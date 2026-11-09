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
