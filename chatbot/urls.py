from django.urls import path
from . import views
from .views import (
    ProductoBusquedaExactaAPIView,
    ProductoBusquedaParcialAPIView,
    ProductoBusquedaFlexibleAPIView
)

urlpatterns = [
    path('chat_query', views.chat_query, name='chat_query'),
    # Búsqueda exacta (un solo producto)
    path('api/productos/busqueda-exacta/', ProductoBusquedaExactaAPIView.as_view(), name='api_producto_busqueda_exacta'),
    
    # Búsqueda parcial (múltiples productos)
    path('api/productos/busqueda-parcial/', ProductoBusquedaParcialAPIView.as_view(), name='api_producto_busqueda_parcial'),
    
    # Búsqueda flexible (combinada)
    path('api/productos/buscar/', ProductoBusquedaFlexibleAPIView.as_view(), name='api_producto_buscar'),
]