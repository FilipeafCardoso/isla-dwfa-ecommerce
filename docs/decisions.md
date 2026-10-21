# Decisões · Decisions

## Esqueleto · Skeleton

- **`AUTH_USER_MODEL = "accounts.User"` desde o dia zero** — trocar depois da primeira migração obriga a reescrever o histórico; um `AbstractUser` vazio não custa nada. · Declared on day zero; swapping later means rewriting migration history; an empty `AbstractUser` is free.
- **Settings por ambiente (`base/dev/test/prod`) com `django-environ`** — o mesmo código em todos os ambientes, só as variáveis mudam (12-factor); segredos fora do git. · Same code everywhere, only env vars change; secrets stay out of git.
- **`/api/health/` devolve 503, não 500, com a base de dados em baixo** — é o código que um load balancer lê como "tira esta instância de rotação". · 503 is what a load balancer reads as "take this instance out of rotation".

## Ficha 02 — modelos · models

1. **Uso de JSONField (Produto):** Utilizou-se o `JSONField` no modelo `Product` (`attributes`) porque, num e-commerce, os produtos variam drasticamente nas suas características (ex: roupa precisa de tamanho/cor, tecnologia precisa de RAM/Voltagem). O JSON evita a criação de inúmeras colunas nulas na base de dados para atributos que só pertencem a certas categorias.

2. **Decisão de `on_delete` (OrderItem -> Product):** Utilizou-se o `models.RESTRICT` na chave estrangeira que liga a linha de encomenda ao produto. Isto garante o histórico financeiro, impedindo que um administrador apague acidentalmente do sistema um produto que já foi faturado numa encomenda.

3. **Decisão de Constraint (OrderItem):** Criou-se uma `UniqueConstraint` nos campos `order` e `product`. O objetivo é impedir que o mesmo produto seja registado duas vezes em linhas diferentes da mesma encomenda; a nível de lógica de negócio, deve-se antes incrementar a quantidade (`quantity`) na linha já existente.


## Ficha 02 — API

1. **Campo só de leitura:** O campo `unit_price` no `OrderItemSerializer` foi definido como *read_only* para garantir que o cliente não manipula o preço cobrado no momento da compra.
2. **Classe de paginação:** Optámos pela `PageNumberPagination` (configurada no base.py) porque é suficiente para navegação padrão em interfaces web, permitindo saltar diretamente para páginas específicas.
3. **Estratégia de versionamento:** O versionamento foi incluído diretamente no path do URL (`/api/v1/`) através do router, garantindo clareza e retrocompatibilidade em futuras versões.
4. **Queries sem N+1 (Teste):** Com o `prefetch_related` e o `select_related`, o endpoint de lista das encomendas necessita apenas de 3 queries.
