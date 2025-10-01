import django_filters
from .models import *

class FiltroOrderAdmin(django_filters.FilterSet):
    class Meta:
        model = Order
        fields = ['status', 'user', 'currency']

class FiltroOrderVendedor(django_filters.FilterSet):
    class Meta:
        model = Order
        fields = ['user', 'currency']

class FiltroOrder(django_filters.FilterSet):
    class Meta:
        model = Order
        fields = ['status', 'store_name', 'currency']

class FiltroCoupon(django_filters.FilterSet):
    class Meta:
        model = Coupon
        fields = ['user', 'expiration_date', 'discount_percent']