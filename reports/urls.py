# En tu urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard_general/', views.admin_dashboard_general, name='admin_dashboard_general'),
    
    # Listas de órdenes
    path('orders/admin/', views.admin_orders_list, name='admin_orders_list'),
    path('orders/vendedor/', views.vendedor_orders_list, name='vendedor_orders_list'),
    path('orders/clientes/', views.clients_orders_list, name='clients_orders_list'),
    
    # Reportes detallados
    path('reportes/ventas/', views.sales_summary, name='sales_summary'),
    path('reportes/productos/', views.sales_products, name='sales_products'),
    path('reportes/clientes/', views.sales_client, name='venta_clientes'),
    path('reportes/oficial/', views.summary_oficial_sales, name='venta_resumen'),
    path('reportes/total/', views.sales_total_summary, name='ventas_totales_resumen'),
]