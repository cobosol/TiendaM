from rest_framework import serializers
from .models import Product

class ProductsGipproSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['gname', 'presentation', 'sku', 'is_feedstock', 'count', 'categories']