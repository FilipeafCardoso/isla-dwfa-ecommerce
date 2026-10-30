# Ficha 03 - Reflexão

**1. 401, 403 e 404**
- 401 -> não se sabe quem é; pedido sem token ou com token inválido.
- 403 -> o utilizador é reconhecido mas não tem permissão para a ação (ex.: cliente a criar um produto).
- 404 -> o recurso não existe ou não pertence ao utilizador; a resposta não distingue os dois casos.

Para uma encomenda de outro cliente, um 403 confirmaria que a encomenda existe (apesar de barrar o acesso). Com o filtro no get_queryset, a encomenda não chega a ser encontrada e o 404 não revela nada. Sem o filtro, os testes passaram de 404 para 403: o acesso continuou bloqueado, mas só o 403 expõe a existência do recurso.

**2. CORS**
Aplicado pelo browser, impede que JavaScript de outra origem leia as respostas (protege o utilizador, não o servidor). Um curl ou um script não são browsers e ignoram o CORS por completo. Quem protege a API é o servidor: autenticação JWT, autorização (permissões e queryset filtrado) e throttling no login.