from rest_framework import serializers
from .models import Product, Category

class CategoryModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name']

class ProductsGipproSerializer(serializers.ModelSerializer):
    categories = CategoryModelSerializer(many=True)
    class Meta:
        model = Product
        fields = ['gname', 'presentation', 'sku', 'is_feedstock', 'count', 'categories']

class ProductsCoboChatSerializer(serializers.ModelSerializer):
    categories = CategoryModelSerializer(many=True)
    class Meta:
        model = Product
        fields = ['gname', 'name', 'presentation', 'is_feedstock', 'categories', 'price_base', 'count']

class ProductAgrupedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['gname', 'name']

    @staticmethod
    def agrupar_por_atributos(queryset, campos):
        """
        Convierte un queryset de productos en un JSON agrupado por campos específicos
        """
        resultado = {campo: [] for campo in campos}
        
        for producto in queryset:
            for campo in campos:
                # Obtener el valor del campo, manejando campos relacionados
                valor = getattr(producto, campo)
                
                # Convertir a string si es necesario o mantener el tipo original
                if hasattr(valor, 'pk'):  # Si es un objeto relacionado
                    resultado[campo].append(str(valor))
                else:
                    resultado[campo].append(valor)
        
        return resultado