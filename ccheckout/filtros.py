import django_filters
from .models import *

class FiltroOrderAdmin(django_filters.FilterSet):
    
    class Meta:
        model = Order
        fields = ['status', 'user', 'store_name', 'currency']

class FiltroOrder(django_filters.FilterSet):
    class Meta:
        model = Order
        fields = ['status', 'store_name', 'currency']