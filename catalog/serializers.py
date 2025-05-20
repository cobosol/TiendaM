from rest_framework import serializers
from .models import Product,Category

class CategoryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name']

class ProductsGipproSerializer(serializers.ModelSerializer):
    categories = CategoryModelSerializer(many=True)
    class Meta:
        model = Product
        fields = ['gname', 'presentation', 'sku', 'is_feedstock', 'count', 'categories']