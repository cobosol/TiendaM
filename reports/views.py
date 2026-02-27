from django.shortcuts import render
from django.db.models.query import QuerySet
from django.template import RequestContext
from django.http import HttpResponseRedirect
from ccheckout.forms import * 
from django.urls import reverse, reverse_lazy
from ccheckout.models import Order, OrderItem, Coupon
from ccheckout.ccheckout import generate_daily_summary_pdf, process2, export_pdf, createPaymentCardsJSON, tPAccessToken, loadSecret, create_order, generate_pdf_response, checkOrderSummary
from cart import cart
from cart.models import CartItem
from catalog.models import Product
from cart.models import DeliveryInfo
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from django.contrib.auth.models import Group
import tempfile
from io import BytesIO
from re import escape, split
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import json
#from tienda.settings import API_CLIENT, API_SECRET
import hashlib
from .views import loadSecret
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from registration.models import Profile
from contact.contact import notification_user_sale, notification_sale, notification_reserve
from ccheckout.filtros import *
# Hacer resumen diario de punto de venta.
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from ccheckout.validators import CouponValidator
from django.db.models import Case, When, Value, Sum, Count, Avg, F, ExpressionWrapper, FloatField, Max
from datetime import date, datetime, timedelta
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, ListView, DeleteView
from utils.mixins import ComercialGroupRequiredMixin
from django.contrib.auth.models import Group
from django.db.models import Q
from django.contrib import messages
import calendar


# Añade esta vista al archivo views.py
def admin_dashboard_general(request, template_name='reports/admin_dashboard_general.html'):
    """Dashboard principal para la gerencia"""
    from datetime import date, timedelta
    
    # Fechas para resúmenes
    today = date.today()
    last_7_days = today - timedelta(days=7)
    last_30_days = today - timedelta(days=30)
    
    # 1. Estadísticas generales de órdenes
    total_orders = Order.objects.all().count()
    pending_orders = Order.objects.filter(status__in=[1, 2]).count()
    delivered_orders = Order.objects.filter(status=Order.DELIVERED).count()
    paid_orders = Order.objects.filter(status=Order.PAIDED).count()
    
    # 2. Ventas recientes
    today_orders = Order.objects.filter(date__date=today).count()
    today_sales_usd = Order.objects.filter(
        date__date=today, 
        currency='USD'
    ).aggregate(total=Sum('end_total'))['total'] or 0
    
    today_sales_cup = Order.objects.filter(
        date__date=today, 
        currency='CUP'
    ).aggregate(total=Sum('cup_total'))['total'] or 0
    
    # 3. Productos más vendidos (últimos 30 días)
    top_products = OrderItem.objects.filter(
        order__date__range=[last_30_days, today]
    ).values(
        'product__name', 
        'product__sku'
    ).annotate(
        total_sold=Sum('quantity'),
        total_revenue_cup=Sum(F('price') * F('quantity'))
    ).order_by('-total_sold')[:10]

    
    
    # 4. Clientes más activos (últimos 30 días)
    top_clients = Order.objects.filter(
        date__range=[last_30_days, today],
        user__groups__isnull=True  # Solo clientes, no comerciales
    ).values(
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email'
    ).annotate(
        order_count=Count('id'),
        total_spent=Sum('cup_oficial')
    ).order_by('-total_spent')[:10]
    
    # 5. Resumen por moneda
    currency_summary = Order.objects.filter(
        date__range=[last_30_days, today]
    ).values('currency').annotate(
        count=Count('id'),
        total_amount=Sum('end_total'),
        cup_total=Sum('cup_total')
    ).order_by('-count')
    
    # 6. Inventario crítico (si tienes modelo Product con stock)
    try:
        low_stock_products = Product.objects.filter(
            stock__lte=F('min_stock')  # Ajusta según tu modelo
        )[:10]
    except:
        low_stock_products = []
    
    # 7. Órdenes recientes
    recent_orders = Order.objects.all().order_by('-date')[:10]
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'paid_orders': paid_orders,
        'today_orders': today_orders,
        'today_sales_usd': float(today_sales_usd),
        'today_sales_cup': float(today_sales_cup),
        'top_products': list(top_products),
        'top_clients': list(top_clients),
        'currency_summary': list(currency_summary),
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
        'last_30_days_start': last_30_days,
        'last_30_days_end': today,
    }
    
    return render(request, template_name, context)

# Vista dashboard con datos del mes en curso
def admin_dashboard(request, template_name='reports/admin_dashboard.html'):
    """Dashboard principal para la gerencia"""
    
    # Fechas para resúmenes
    today = date.today()
    
    # Mes en curso
    first_day_of_month = today.replace(day=1)
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    last_day_of_month = today.replace(day=days_in_month)
    
    # Para comparación con el mes anterior
    if today.month == 1:
        first_day_last_month = date(today.year - 1, 12, 1)
        last_day_last_month = date(today.year - 1, 12, 31)
    else:
        first_day_last_month = today.replace(month=today.month - 1, day=1)
        last_day_last_month = date(today.year, today.month - 1, 
                                  calendar.monthrange(today.year, today.month - 1)[1])
    
    # 1. Estadísticas generales de órdenes
    total_orders = Order.objects.filter(status__in=[0, 1, 2, 3, 5, 7]).count()
    pending_orders = Order.objects.filter(status__in=[0, 1, 2, 7]).count()
    delivered_orders = Order.objects.filter(status=Order.DELIVERED).count()
    paid_orders = Order.objects.filter(status=Order.PAIDED).count()
    
    # 2. Ventas del MES EN CURSO
    month_orders = Order.objects.filter(
        date__date__range=[first_day_of_month, today], status__in=[2, 3, 5]
    ).count()
    
    month_sales_usd = Order.objects.filter(
        date__date__range=[first_day_of_month, today],
        currency='USD', status__in=[3, 2, 5]
    ).aggregate(total=Sum('end_total'))['total'] or 0
    
    month_sales_cup = Order.objects.filter(
        date__date__range=[first_day_of_month, today],
        currency='CUP',status__in=[3, 2, 5]
    ).aggregate(total=Sum('cup_oficial'))['total'] or 0
    
    month_sales_total = Order.objects.filter(
        date__date__range=[first_day_of_month, today], status__in=[3, 2, 5]
        ).aggregate(total=Sum('cup_oficial'))['total'] or 0
    
    # Ventas del mes anterior para comparación
    last_month_sales_usd = Order.objects.filter(
        date__date__range=[first_day_last_month, last_day_last_month],
        currency='USD', status__in=[3, 2, 5]
    ).aggregate(total=Sum('end_total'))['total'] or 0
    
    last_month_sales_cup = Order.objects.filter(
        date__date__range=[first_day_last_month, last_day_last_month],
        currency='CUP', status__in=[3, 2, 5]
    ).aggregate(total=Sum('cup_oficial'))['total'] or 0
    
    # Cálculo de crecimiento/descenso
    def calculate_growth(current, previous):
        if previous == 0:
            return 100 if current > 0 else 0
        return ((current - previous) / previous) * 100
    usd_growth = calculate_growth(float(month_sales_usd), float(last_month_sales_usd))
    cup_growth = calculate_growth(float(month_sales_cup), float(last_month_sales_cup))

    # 3. Productos más vendidos en CUP (MES EN CURSO)
    top_products = OrderItem.objects.filter(
        order__date__date__range=[first_day_of_month, today],order__currency='CUP', order__status__in=[3, 2, 5]
    ).values(
        'product__name', 
        'product__sku'
    ).annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum(F('price') * F('quantity'))
    ).order_by('-total_sold')[:10]
    
    # 4. Clientes más activos (MES EN CURSO)
    top_clients = Order.objects.filter(
        date__date__range=[first_day_of_month, today], 
        status__in=[3, 2, 5], 
        user__groups__isnull=True  # Solo clientes, no comerciales
    ).values(
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email'
    ).annotate(
        order_count=Count('id'),
        total_spent=Sum('cup_oficial'),
        last_order=Max('date')
    ).order_by('-total_spent')[:10]
    
    # 5. Resumen por moneda (MES EN CURSO)
    currency_summary = Order.objects.filter(
        date__date__range=[first_day_of_month, today], status__in=[3, 2, 5]
    ).values('currency').annotate(
        count=Count('id'),
        total_amount=Sum('end_total'),
        cup_total=Sum('cup_oficial')
    ).order_by('-count')
    
    # 6. Ventas diarias del mes (para gráfico)
    daily_sales = Order.objects.filter(
        date__date__range=[first_day_of_month, today],
        status__in=[Order.DELIVERED, Order.PAIDED]
    ).annotate(
        sale_day=TruncDate('date')  # Esto da un objeto date
    ).values('sale_day').annotate(
        daily_total=Sum('end_total'),
        order_count=Count('id')
    ).order_by('sale_day')

    # Preparar datos para gráfico
    days_list = []
    sales_list = []
    orders_list = []

    # Crear lista completa de días del mes hasta hoy
    current_day = first_day_of_month
    while current_day <= today:
        days_list.append(current_day.strftime("%d/%m"))
        # Buscar ventas para este día comparando objetos date
        day_sales = next(
            (item for item in daily_sales if item['sale_day'] == current_day),
            {'daily_total': 0, 'order_count': 0}
        )
        sales_list.append(float(day_sales['daily_total']))
        orders_list.append(day_sales['order_count'])
        current_day += timedelta(days=1)
    
    # 7. Inventario crítico (si tienes modelo Product con stock)
    try:
        low_stock_products = Product.objects.filter(
            count__lte = F('min_stock') * 1.5 
        )[:10]
    except:
        low_stock_products = []
    
    # 8. Órdenes recientes (del mes)
    recent_orders = Order.objects.filter(
        date__date__range=[first_day_of_month, today]
    ).order_by('-date')[:10]
    
    # 9. Ventas por estado del mes
    month_status_summary = Order.objects.filter(
        date__date__range=[first_day_of_month, today]
    ).values('status').annotate(
        count=Count('id'),
        total_amount=Sum('cup_oficial')
    ).order_by('-count')

        
    for item in month_status_summary:
        item['status_name'] = Order.ORDER_STATUSES[item['status']][1]

    # 10. Métricas de conversión (si tienes datos de visitas/carritos)
    try:
        cart_count = CartItem.objects.filter(
            created_at__date__range=[first_day_of_month, today]
        ).count()
        conversion_rate = (month_orders / cart_count * 100) if cart_count > 0 else 0
    except:
        cart_count = 0
        conversion_rate = 0
    
    context = {
        # Totales
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivered_orders': delivered_orders,
        'paid_orders': paid_orders,
        
        # Mes actual
        'month_orders': month_orders,
        'month_sales_usd': float(month_sales_usd),
        'month_sales_cup': float(month_sales_cup),
        'month_sales_mlc': float(month_sales_total),
        
        # Crecimiento
        'usd_growth': usd_growth,
        'cup_growth': cup_growth,
        'last_month_sales_usd': float(last_month_sales_usd),
        'last_month_sales_cup': float(last_month_sales_cup),
        
        # Top lists
        'top_products': list(top_products),
        'top_clients': list(top_clients),
        'currency_summary': list(currency_summary),
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
        'month_status_summary': list(month_status_summary),
        
        # Gráficos
        'days_list': json.dumps(days_list),
        'sales_list': json.dumps(sales_list),
        'orders_list': json.dumps(orders_list),
        
        # Fechas
        'current_month': today.strftime("%B %Y"),
        'first_day_of_month': first_day_of_month,
        'today': today,
        'month_progress': (today.day / days_in_month) * 100,
        
        # Métricas adicionales
        'cart_count': cart_count,
        'conversion_rate': conversion_rate,
    }
    
    return render(request, template_name, context)

# Gestionar la lista de ordenes (compras) realizadas a la tienda
def vendedor_orders_list(request, template_name='reports/vendedor_orders_list.html'):

    #orders = Order.objects.filter(date__range=[start, end]).order_by('-date')
    orders = Order.objects.filter(status__in = [1,2]).order_by('-date')
    
    filter = FiltroOrderVendedor

    store_name = request.GET.get('store_name')
    currency = request.GET.get('currency')
    user = request.GET.get('user')


    if user:
        if user != '':
            orders= orders.filter(user=user).order_by('-date')

    if store_name:
        if store_name!='':
            orders = orders.filter(store_name__icontains = store_name).order_by('-date')

    if currency:
        if currency!='':
            orders = orders.filter(currency__icontains=currency).order_by('-date')
    
    if request.method == 'POST':
        postdata = request.POST.copy()
        if postdata['submit'] == 'Factura':
            order_number = postdata['order_id']
            return export_pdf(request, order_number)
        elif postdata['submit'] == 'Entregada':
            order_number = postdata['order_id']
            order = get_object_or_404(Order,id=order_number)
            order.vale_salida = postdata['vale']
            order.status = order.DELIVERED
            order.save()
        elif postdata['submit'] == 'Pagada':
            order_number = postdata['order_id']
            order = get_object_or_404(Order,id=order_number)
            order.transaction_id = postdata['transaccion']
            order.status = order.PAIDED
            order.save()
        """ if postdata['submit'] == 'Detalles':
            order_id = postdata['order_id']
            template = 'checkout/details.html'
            return redirect(reverse('details')) """
    user_name = ""
    return render(request, template_name, locals())

# view de la lista de ordenes (compras) relizadas a la tienda
def admin_orders_list(request, template_name='reports/admin_orders_list.html'):

    orders = Order.objects.all().order_by('-date')


    start_date = request.GET.get('start_date', '2025-01-01')
    end_date = request.GET.get('end_date', datetime.today().strftime('%Y-%m-%d'))
    
    # Convertir a objetos datetime
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    end = end + timedelta(days=1) 

    # Filtrar órdenes en el rango
    orders = Order.objects.filter(date__range=[start, end]).order_by('-date')
    
    filter = FiltroOrderAdmin

    status = request.GET.get('status')
    #store_name = request.GET.get('store_name')
    currency = request.GET.get('currency')
    user = request.GET.get('user')

    if user:
        if user != '':
            orders= orders.filter(user=user).order_by('-date')
            
    if status:
        if status!='':
            orders = orders.filter(status__icontains = status).order_by('-date')

    if currency:
        if currency!='':
            orders = orders.filter(currency__icontains=currency).order_by('-date')
    

    if request.method == 'POST':
        postdata = request.POST.copy()
        if postdata['submit'] == 'Factura':
            order_number = postdata['order_id']
            return export_pdf(request, order_number)
        if postdata['submit'] == 'Detalles':
            order_id = postdata['order_id']
            template = 'checkout/details.html'
            return redirect(reverse('details'))
        return HttpResponseRedirect(receipt)
    user_name = ""
    return render(request, template_name, locals())


def clients_orders_list(request, template_name='reports/clients_orders_list.html'):
    start_date = request.GET.get('start_date', '2025-01-01')
    end_date = request.GET.get('end_date', datetime.today().strftime('%Y-%m-%d'))
    # Convertir a objetos datetime
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    end = end + timedelta(days=1)

    sum_daily_amount = 0
    sum_client_amount = 0
    sum_comercial_amount = 0

    gcomerciales = Group.objects.filter(name='comercial').first()
    if gcomerciales:
        comerciales = gcomerciales.user_set.all()
        comercial_orders = Order.objects.filter(date__range=[start, end], status__in=[Order.DELIVERED, Order.PAIDED, Order.SHIPPED, Order.CONFIRMED], user__in=comerciales, is_daily_summary=False).order_by('-date')
        com_count = comercial_orders.count()
    

    # Filtrar órdenes válidas en el rango
    sin_g = User.objects.filter(groups__isnull=True)
    client_orders = Order.objects.filter(date__range=[start, end], status__in=[Order.DELIVERED, Order.PAIDED, Order.SHIPPED, Order.CONFIRMED], user__in=sin_g).order_by('-date')

    co_count = client_orders.count()

    summary_orders = Order.objects.filter(date__range=[start, end], status__in=[Order.DELIVERED], is_daily_summary=True).order_by('-date')
    so_count = summary_orders.count()

    sum_daily_amount = summary_orders.aggregate(sum=Sum('cup_total'))['sum'] or 0
    sum_daily_amount = float(sum_daily_amount)

    sum_client_amount = client_orders.aggregate(sum=Sum('cup_total'))['sum'] or 0
    sum_client_amount = float(sum_client_amount)
    client_orders_cup = client_orders.filter(currency='CUP')
    client_orders_usd = client_orders.filter(currency='USD')
    sum_client_amount_cup = client_orders_cup.aggregate(sum=Sum('cup_total'))['sum'] or 0
    sum_client_amount_cup = float(sum_client_amount_cup)
    sum_client_amount_usd = client_orders_usd.aggregate(sum=Sum('end_total'))['sum'] or 0
    sum_client_amount_usd = float(sum_client_amount_usd)

    if comercial_orders:
        sum_comercial_amount = comercial_orders.aggregate(sum=Sum('cup_total'))['sum'] or 0
        sum_comercial_amount = float(sum_comercial_amount)
        comercial_orders_cup = comercial_orders.filter(currency='CUP')
        comercial_orders_usd = comercial_orders.filter(currency='USD')
        sum_comercial_amount_cup = comercial_orders_cup.aggregate(sum=Sum('cup_total'))['sum'] or 0
        sum_comercial_amount_cup = float(sum_comercial_amount_cup)
        sum_comercial_amount_usd = comercial_orders_usd.aggregate(sum=Sum('end_total'))['sum'] or 0
        sum_comercial_amount_usd = float(sum_comercial_amount_usd)

    sum_total = 0

    if sum_client_amount:
        sum_total += sum_client_amount

    if sum_comercial_amount:
        sum_total = sum_total + sum_comercial_amount

    if sum_daily_amount:
        sum_total += sum_daily_amount

    orders = Order.objects.filter(date__range=[start, end], status__in=[Order.DELIVERED, Order.PAIDED, Order.SHIPPED, Order.CONFIRMED]).order_by('-date')
    
    s = request.GET.get('summary')
    if s == 'on':
        orders = orders.filter(is_daily_summary=True).order_by('-date')

    
    comercial = request.GET.get('comercial')    
    if comercial == 'on':
        orders = orders.filter(user__in=comerciales, is_daily_summary=False).order_by('-date')

    clientes = request.GET.get('clientes')    
    if clientes == 'on':
        orders = orders.filter(user__in=sin_g).order_by('-date')

    if request.method == 'POST':
        postdata = request.POST.copy()
        if postdata['submit'] == 'Factura':
            order_number = postdata['order_id']
            return export_pdf(request, order_number)
        if postdata['submit'] == 'Detalles':
            order_id = postdata['order_id']
            template = 'checkout/details.html'
            return redirect(reverse('details'))
        return HttpResponseRedirect(receipt)
    user_name = ""
    return render(request, template_name, locals())


def summary_oficial_sales(request, template_name='reports/resumen_ventas_oficial.html'):
    start_date = request.GET.get('start_date', '2025-01-01')
    end_date = request.GET.get('end_date', datetime.today().strftime('%Y-%m-%d'))
    # Convertir a objetos datetime
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    end = end + timedelta(days=1)

    sum_daily_amount = 0
    sum_client_amount = 0
    sum_comercial_amount = 0

    gcomerciales = Group.objects.filter(name='comercial').first()
    if gcomerciales:
        comerciales = gcomerciales.user_set.all()
        comercial_orders = Order.objects.filter(date__range=[start, end], status__in=[Order.DELIVERED, Order.PAIDED, Order.SHIPPED, Order.CONFIRMED], user__in=comerciales, is_daily_summary=False).order_by('-date')
        com_count = comercial_orders.count()
    

    # Filtrar órdenes válidas en el rango
    sin_g = User.objects.filter(groups__isnull=True)
    client_orders = Order.objects.filter(date__range=[start, end], status__in=[Order.DELIVERED, Order.PAIDED, Order.SHIPPED, Order.CONFIRMED], user__in=sin_g).order_by('-date')

    co_count = client_orders.count()

    summary_orders = Order.objects.filter(date__range=[start, end], status__in=[Order.DELIVERED], is_daily_summary=True).order_by('-date')
    so_count = summary_orders.count()

    sum_daily_amount = summary_orders.aggregate(sum=Sum('total_reported'))['sum'] or 0
    sum_daily_amount = float(sum_daily_amount)

    sum_client_amount = client_orders.aggregate(sum=Sum('cup_oficial'))['sum'] or 0
    sum_client_amount = float(sum_client_amount)

    sum_comercial_amount = comercial_orders.aggregate(sum=Sum('cup_oficial'))['sum'] or 0
    sum_comercial_amount = float(sum_comercial_amount)

    sum_total = 0

    if sum_client_amount:
        sum_total += sum_client_amount

    if sum_comercial_amount:
        sum_total = sum_total + sum_comercial_amount

    if sum_daily_amount:
        sum_total += sum_daily_amount

    orders = Order.objects.filter(date__range=[start, end], status__in=[Order.DELIVERED, Order.PAIDED, Order.SHIPPED, Order.CONFIRMED]).order_by('-date')
    
    s = request.GET.get('summary')
    if s == 'on':
        orders = orders.filter(is_daily_summary=True).order_by('-date')

    comercial = request.GET.get('comercial')    
    if comercial == 'on':
        orders = orders.filter(user__in=comerciales, is_daily_summary=False).order_by('-date')

    clientes = request.GET.get('clientes')    
    if clientes == 'on':
        orders = orders.filter(user__in=sin_g).order_by('-date')

    total_count = co_count + so_count + com_count


    # EXPORTAR A PDF
    export = request.GET.get('export', '')
    if export == 'pdf':
        context = {
            'start_date': start,
            'end_date': end,
            'com_count': com_count,
            'co_count': co_count,
            'so_count': so_count,
            'total_count': total_count,
            'sum_daily_amount' : sum_daily_amount,
            'sum_client_amount' : sum_client_amount,
            'sum_comercial_amount' : sum_comercial_amount,
            'sum_total': sum_total,
            'comercial_orders': comercial_orders.select_related('user'),
            'client_orders': client_orders.select_related('user'),
            'summary_orders': summary_orders.select_related('user'),
        }
        
        return generate_pdf_response(context, f"reporte_ventas_{start_date}_{end_date}")
    
    return render(request, template_name, locals())


def sales_products(request):
    # Obtener fechas del request
    start_date = request.GET.get('start_date', '2023-01-01')
    end_date = request.GET.get('end_date', datetime.today().strftime('%Y-%m-%d'))

    cant_prod = int(request.GET.get('cant_prod', '10'))
    
    # Convertir a objetos datetime
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Filtrar órdenes en el rango
    orders = Order.objects.filter(date__range=[start, end], status__in=[2,3,5])
     
    # 1. Cantidad vendida por producto (top N)
    products_data = list(
        OrderItem.objects
        .filter(order__in=orders)
        .values('product__id', 'product__name', 'product__count')  # Incluir stock
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity')[:cant_prod]  # ¡Solo los N primeros!
    )

    # 2. Obtener stock actual de cada producto
    # Creamos una lista de IDs de productos
    product_ids = [item['product__id'] for item in products_data]
    
    # Obtenemos los productos con su stock actual
    product_stocks = Product.objects.filter(id__in=product_ids).values('id', 'name', 'count')

    # Creamos un diccionario para acceso rápido por ID
    stock_dict = {p['id']: p['count'] for p in product_stocks}
    

    # 3. Agregar stock a los datos de productos
    for product in products_data:
        product_id = product['product__id']
        product['product__count'] = stock_dict.get(product_id, 0)
        # Convertir a float para JSON
        product['total_quantity'] = float(product['total_quantity'])
        product['product__count'] = float(product['product__count'])
        
        # Marcar como bestseller si aplica
        prod_obj = get_object_or_404(Product, id=product_id)
        prod_obj.is_bestseller = True
        prod_obj.save()


    # 4. Monto total por producto (top N)
    revenue_by_product = list(
    OrderItem.objects
    .filter(order__in=orders, order__status__in=[2,3,5])
    .values('product__id', 'product__name')
    .annotate(
        total_revenue_cup=Sum(
            Case(
                When(order__currency='USD', then=F('price') * F('quantity') * F('order__change_usd_cup')),
                When(order__currency='CUP', then=F('price') * F('quantity')),
                default=Value(0),
                output_field=FloatField()
            )
        )
    )
    .order_by('-total_revenue_cup')[:cant_prod]
    )

    # Convertir Decimal a float
    for r in revenue_by_product:
        r['total_revenue_cup'] = float(r['total_revenue_cup'])

    # 5. Calcular ratio ventas/stock (para indicar productos que necesitan reposición)
    for product in products_data:
        sold = product['total_quantity']
        stock = product['product__count']
        if stock > 0:
            product['sold_stock_ratio'] = (sold / stock) * 100
        else:
            product['sold_stock_ratio'] = 100 if sold > 0 else 0  # Si no hay stock pero hubo ventas


    # Preparar datos para gráficas
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'cant_prod': cant_prod,
        'products': json.dumps(products_data),
        'revenue_data': json.dumps(revenue_by_product),
    }

    return render(request, 'reports/venta_productos.html', context)

def sales_client(request):
    # Obtener fechas del request
    start_date = request.GET.get('start_date', '2025-01-01')
    end_date = request.GET.get('end_date', datetime.today().strftime('%Y-%m-%d'))
    
    # Convertir a objetos datetime
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Filtrar órdenes en el rango
    orders = Order.objects.filter(date__range=[start, end])

    users = User.objects.all().order_by('last_name')
    
    # 4. Compras por usuario (top 10)
    top_customers = list(
        orders.filter(Q(user__groups__isnull=True))
        .values('user__username')
        .annotate(
            total_spent=Sum('cup_oficial'),
            order_count=Count('id')
        )
        .order_by('-total_spent')
    )

    for c in top_customers:
        c['total_spent'] = float(c['total_spent'])

    
    # Preparar datos para gráficas
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'top_customers': json.dumps(top_customers),
        'users': users,
    }

    return render(request, 'reports/venta_clientes.html', context)

def sales_summary(request):
    # Obtener fechas del request
    start_date = request.GET.get('start_date', '2025-01-01')
    end_date = request.GET.get('end_date', datetime.today().strftime('%Y-%m-%d'))
    
    # Convertir a objetos datetime
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Tipo de moneda
    currency = request.GET.get('currency', 'USD')

    # Filtrar órdenes en el rango
    orders = Order.objects.filter(date__range=[start, end], currency=currency, status__in=[Order.DELIVERED, Order.PAIDED])
    

    # 3. Estadísticas generales
    total_orders = orders.count()

    avg_order_amount = orders.aggregate(avg=Avg('end_total'))['avg'] or 0
    avg_order_amount = float(avg_order_amount)
    sum_order_amount = orders.aggregate(sum=Sum('end_total'))['sum'] or 0
    sum_order_amount = float(sum_order_amount)

    # Gráfica temporal
    granularity = request.GET.get('granularity', 'day')

    if granularity == 'week':
        trunc_func = TruncWeek('date', tzinfo=timezone.get_current_timezone())
    elif granularity == 'month':
        trunc_func = TruncMonth('date', tzinfo=timezone.get_current_timezone())
    else:  # Incluye 'day' y cualquier otro valor
        trunc_func = TruncDate('date', tzinfo=timezone.get_current_timezone())

    # Consulta de ventas por período
    sales_by_period = (
        Order.objects
        .filter(date__range=[start_date, end_date], currency=currency)
        .annotate(period=trunc_func)
        .values('period')
        .annotate(
            total_sales=Sum('end_total'),
            order_count=Count('id')
        )
        .order_by('period')
    )
    
    # Formatear etiquetas según granularidad
    labels = []
    for item in sales_by_period:
        period = item['period']
        if granularity == 'week':
            labels.append(f"Sem {period.isocalendar()[1]} {period.year}")
        elif granularity == 'month':
            labels.append(period.strftime("%b %Y"))
        else:
            labels.append(period.strftime("%d/%m/%Y"))
    
    # Convertir datos a formato compatible con JSON
    period_totals = [float(item['total_sales']) for item in sales_by_period]

    
    # Preparar datos para gráficas
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'granularity': granularity,
        'period_labels': json.dumps(labels),
        'period_totals': json.dumps(period_totals),
        'total_orders': total_orders,
        'avg_order_amount': avg_order_amount,
        'sum_order_amount': sum_order_amount,
    }

    return render(request, 'checkout/venta_resumen.html', context)

def sales_total_summary(request):
    # Obtener fechas del request
    start_date = request.GET.get('start_date', '2025-01-01')
    end_date = request.GET.get('end_date', datetime.today().strftime('%Y-%m-%d'))
    
    # Convertir a objetos datetime
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Tipo de moneda
    currency = request.GET.get('currency', 'USD')

    # Filtrar órdenes en el rango
    orders = Order.objects.filter(date__range=[start, end], status__in=[Order.DELIVERED, Order.PAIDED, Order.SHIPPED, Order.CONFIRMED])
    
    """ for o in orders:
        o.save() """

    # 3. Estadísticas generales
    total_orders = orders.count()

    if currency == 'USD':
        atrr = 'usd_total'
    elif currency == 'CUP':
        atrr = 'cup_oficial'
    else:
        atrr = 'mlc_total'

    avg_order_amount = orders.aggregate(avg=Avg(atrr))['avg'] or 0
    avg_order_amount = float(avg_order_amount)
    sum_order_amount = orders.aggregate(sum=Sum(atrr))['sum'] or 0
    sum_order_amount = float(sum_order_amount)

    # Gráfica temporal
    granularity = request.GET.get('granularity', 'day')

    if granularity == 'week':
        trunc_func = TruncWeek('date', tzinfo=timezone.get_current_timezone())
    elif granularity == 'month':
        trunc_func = TruncMonth('date', tzinfo=timezone.get_current_timezone())
    else:  # Incluye 'day' y cualquier otro valor
        trunc_func = TruncDate('date', tzinfo=timezone.get_current_timezone())

    # Consulta de ventas por período
    sales_by_period = (
        Order.objects
        .filter(date__range=[start_date, end_date])
        .annotate(period=trunc_func)
        .values('period')
        .annotate(
            total_sales=Sum(atrr),
            order_count=Count('id')
        )
        .order_by('period')
    )
    
    # Formatear etiquetas según granularidad
    labels = []
    for item in sales_by_period:
        period = item['period']
        if granularity == 'week':
            labels.append(f"Sem {period.isocalendar()[1]} {period.year}")
        elif granularity == 'month':
            labels.append(period.strftime("%b %Y"))
        else:
            labels.append(period.strftime("%d/%m/%Y"))
    
    # Convertir datos a formato compatible con JSON
    period_totals = [float(item['total_sales']) for item in sales_by_period]

    
    # Preparar datos para gráficas
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'granularity': granularity,
        'period_labels': json.dumps(labels),
        'period_totals': json.dumps(period_totals),
        'total_orders': total_orders,
        'avg_order_amount': avg_order_amount,
        'sum_order_amount': sum_order_amount,
    }

    return render(request, 'reports/venta_resumen.html', context)


