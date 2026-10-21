import pytest
from django.db import IntegrityError
from django.db.models import Count
from store.models import Order
from store.factories import OrderFactory, ProductFactory, OrderItemFactory

# Create your tests here

@pytest.mark.django_db
def test_unique_order_item_constraint():
    """Garante que não é possível adicionar o mesmo produto duas vezes à mesma encomenda."""
    order = OrderFactory()
    product = ProductFactory()
    
    # Adiciona o produto pela primeira vez (sucesso)
    OrderItemFactory(order=order, product=product)
    
    # A segunda tentativa deve levantar um IntegrityError (bloqueado pela base de dados)
    with pytest.raises(IntegrityError):
        OrderItemFactory(order=order, product=product)

@pytest.mark.django_db
def test_order_list_has_no_n_plus_one(django_assert_num_queries):
    """Garante que a contagem de itens por encomenda corre em apenas 1 query."""
    # Cria 5 encomendas, cada uma com 4 itens (total 20 itens)
    for _ in range(5):
        order = OrderFactory()
        OrderItemFactory.create_batch(4, order=order)
        
    # Valida que a listagem com anotação só precisa de 1 query
    with django_assert_num_queries(1):
        qs = Order.objects.annotate(n_items=Count('items')).order_by('id')
        rows = list(qs)
        
    assert len(rows) == 5
    assert all(row.n_items == 4 for row in rows)