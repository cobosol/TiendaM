from ccheckout.models import Order
from django.db.models import Q

# Actualizar registros existentes con valor None o 0
objetos_actualizar = Order.objects.filter(
    Q(end_total__isnull=True) | 
    Q(end_total=0)
)

for obj in objetos_actualizar:
    obj.save()  # Esto activará la lógica de save()