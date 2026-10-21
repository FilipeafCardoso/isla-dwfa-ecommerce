from rest_framework.exceptions import APIException
from rest_framework import status
from .models import Order

class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Operação não permitida.'

def pay_order(order: Order):
    # Regra de negócio: se já tem total_amount > 0 => já paga
    if order.total_amount > 0:
        raise ConflictError("A encomenda já foi paga e não pode ser processada novamente.")
    
    # Calcula o total e guarda
    total = sum(item.product.price * item.quantity for item in order.items.all())
    order.total_amount = total if total else 0
    order.save()
    
    return order