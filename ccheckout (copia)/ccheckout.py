import urllib
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template, render_to_string
from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils.html import strip_tags
from xhtml2pdf import pisa
from io import BytesIO
from re import escape, split
import os, sys 
import requests
import json
import decimal

from cart import cart
from .models import Order, OrderItem
from .forms import CheckoutForm, PagarForm, CachForm, FacturarForm, DailySummaryForm
from stores.models import Store, Product_Sales
from utils.models import Price
from registration.models import Profile
from cart.models import DeliveryInfo
from .validators import CouponValidator


def loadSecret():
    try:
        credsFile=open('secrets.txt')
        creds = json.load(credsFile)
        return creds
    except Exception as e:
            print("Error Leyendo el fichero secrets")
            sys.exit("System error: " + str(e) )

def createPaymentCardsJSON(request, order_number):
    creds = loadSecret()
    print(creds)
    url = creds['URL_Payment'] 

    payloadDic = {
        "reference": "Tienda Virtual MUHIA",
        "concept": "Compra de productos",
        "favorite": True,
        "description": "Productos MUHIA",
        "amount": 4000,
        "currency": "USD",
        "singleUse": True,
        "reasonId": 4,
        "expirationDays": 1,
        "lang": "es",
        "urlSuccess": "exito",
        "urlFailed": "fallo",
        "urlNotification": "notificacion",
        "serviceDate": "2024-04-30",
        "client": {
            "name": "Nombre",
            "lastName": "Apellido",
            "address": "Direccion",
            "phone": "+5555555555",
            "email": "correo@servidor.com",
            "countryId": 1,
            "termsAndConditions": "true",
            "city":"Barcelona",
            "postCode": "78622"
        },
        "directPayment": True,
        "paymentMethods": ["EXT","TPP"]
        }
    
    ordern = order_number['order_number']
    order = Order.objects.filter(id=ordern)[0]
    total = order.total * 100
    payloadDic['amount'] = int(total)
    payloadDic['urlSuccess'] = creds['urlSuccess']
    payloadDic['urlFailed'] = creds['urlFailed']
    payloadDic['urlNotification'] = creds['urlNotification']
    user = request.user
    client = payloadDic.get('client')
    client['name'] = order.payment_name 
    client['phone'] = order.payment_phone
    client['email'] = order.payment_email
    client['city'] = order.payment_city
    client['postCode'] = order.payment_postCode
    payloadDic['reasonId'] = ordern
    payloadDic['client'] = client

    payload = json.dumps(payloadDic)
    
    headers = {
        'Prefer': 'code=200, example=Example with client data',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwYXJlbnQiOm51bGwsImNyZWRlbnRpYWxJZCI6MTI5ODM3LCJjcmVkZW50aWFsTmFtZSI6ImM2YTk5NWI5ZTFkYjI0MmYzMDdmZWE2ODI4NmMyMGY4IiwiaWQiOiI3YmY0NTE1MC02NTU4LTExZWQtYmQzMy1mYjc2MWRhNjQ5ODgiLCJpYXQiOjE3MTQ2NTM5NTEsImV4cCI6MTcxNDY2MTE1MX0.EuEI_QCBAAt7U1_NdKxdbiRp_hJHYLqyItBAB4m7kco'
        } 
    
    headers['Authorization'] = 'Bearer ' + creds["token"]   
    print(headers)
    print(payload)

    response = requests.request("POST", url, headers=headers, data=payload)
    return response
      
def tPAccessToken():
    try:
        headers = {
              "Accept": "application/json",
              "Content-Type": "application/json"
              }
        data1 = {
              "grant_type": "client_credentials",
              "client_id": "0d94edaf6b147f37453a239f8b7a9451",
              "client_secret": "e303cdd52ec325ff7c88577cfdef63c4"
              }
        
        creds = loadSecret()
        URL = creds['URL_AccessToken']
        data1["client_id"] = creds["client_id"]
        data1["client_secret"] = creds["client_secret"]

        payload = json.dumps(data1)
        
        response = requests.request("POST", URL, headers = headers, data = payload)
        return response
    except Exception as e:
        print( 'La Exception >> ' + type(e).__name__ )
        raise e
      
def get_checkout_url(request):
    url = reverse('checkout')
    return HttpResponseRedirect(url)

def process2(request, usd=True):
    postdata = request.POST.copy()
    amount = cart.cart_subtotal(request)
    results = {}
    transaction_id = 1
    order = create_order(request, transaction_id, usd)
    results = {'order_number':order.id,'message':'Creo la orden'}
    return results

def create_order(request, transaction_id, usd = True, cach = False):
    if not cart.verify_cart_items(request):
        results = {'order_number':-1,'message':'No se pudo crear la orden'}
        return results
    order = Order() # Creo la nueva orden vacía
    store = cart.delivery_Store(request) # Capturo el almacen
    price2 = Price.objects.filter(is_active=True)[0] # Capturo la configuración de precio actual
    user = request.user # capturo el usuario registrado
    profile = get_object_or_404(Profile, user = user) # Accedo a su perfil
    MND = profile.MONEY_TYPE[profile.money_type][1] # Saco el tipo de moneda del usuario
    results = {} # Crear variable para la respuesta
    if transaction_id == 2: # Reservar
        checkout_form = PagarForm(request.POST, instance=order)
        order = checkout_form.save(commit=False)
        order.currency = 'USD'
        deliveryInfo = get_object_or_404(DeliveryInfo, client=request.user)
        cart_subtotal = cart.cart_subtotal(request)
        order.delivery_price = cart.cart_delivery_price(request, cart_subtotal, MND)
    elif transaction_id == 3: # Facturar por contrato
        checkout_form = FacturarForm(request.POST, instance=order)
        order = checkout_form.save(commit=False)
        if usd: # Guardo el tipo de moneda en efectivo
            order.currency = 'USD'
        elif cach:
            order.currency = 'CUP'
        else:
            order.currency = 'MLC'
    elif transaction_id == 4: # Resumen diario
        checkout_form = DailySummaryForm(request.POST, instance=order)
        if checkout_form.is_valid():
            order = checkout_form.save(commit=False)
            order.is_daily_summary = True
            if usd: # Guardo el tipo de moneda en efectivo
                order.currency = 'USD'
            elif cach:
                order.currency = 'CUP'
    else:
        if cach: # Si se va a pagar en efectivo guardo la información de la Form para efectivo
            checkout_form = CachForm(request.POST, instance=order)
            order = checkout_form.save(commit=False)
            if usd: # Guardo el tipo de moneda en efectivo
                order.currency = 'USD'
            else:
                order.currency = 'CUP'
                order.delivery_price = store.price_cup
        else: # Si es pago por tarjeta
            if usd: # Tarjetas internacionales
                checkout_form = CheckoutForm(request.POST, instance=order)
                order = checkout_form.save(commit=False)
                order.currency = 'USD'
                deliveryInfo = get_object_or_404(DeliveryInfo, client=request.user)
                order.delivery_price = deliveryInfo.calculate_deliveryHabana()
            else: # tarjetas nacionales
                request.POST = request.POST.copy()
                request.POST['wallet_discount'] = request.session.get('wallet_discount', 0)
                pagar_form = PagarForm(request.POST, instance=order)
                if pagar_form.is_valid():
                    order = pagar_form.save(commit=False)
                    request.session['wallet_discount'] = ''
                else:
                    print(f'Errores: {pagar_form.errors}')
                    raise Http404("Error en el formulario de pago")
                if MND == 'CUP': # Si el usuario tiene en su perfil moneda CUP
                    order.delivery_price = store.price_cup
                    order.currency = 'CUP'
                else: # Si tiene en su perfil MLC
                    order.delivery_price = store.price_mlc
                    order.currency = 'MLC'
    #Lleno datos iguales para todo tipo de pago
    order.user = user
    order.transaction_id = transaction_id # Esto viene por parámetro
    order.ip_address = request.META.get('REMOTE_ADDR')
    order.delivery = store
    order.store_name = store.name
    order.price = price2    
    order.save()
    if order.pk:
        cart_items = cart.get_cart_items(request)
        for ci in cart_items:
            oi = OrderItem()
            oi.order = order
            oi.product = ci.product
            oi.store_name = cart.delivery_name(request) # Sobra
            oi.quantity = ci.quantity
            #actualizar la cantidad de reservado del producto en ese almacen
            prod = ci.product
            if MND == 'USD':
                oi.price = ci.price_USD()
                oi.totalf = ci.total_USD(order.is_daily_summary) #Si va valor True no hace descuentos
            elif MND == 'CUP':
                oi.price = ci.price_CUP()
                oi.totalf = ci.total_CUP(order.is_daily_summary)
            else:
                oi.price = ci.price_MLC()
                oi.totalf = ci.total_MLC(order.is_daily_summary)
            oi.save()
        order.update_status(Order.SUBMITTED)
        order.base_total = cart.cart_subtotal(request, not order.is_daily_summary) #order.total_items
        amounth_discount = "False"
        mount = 0
        if not order.is_daily_summary:
            if abs(order.total_items - order.base_total) > 0.01:
                amounth_discount = "True"
                mount = 100 - round((order.base_total / order.total_items * 100 ), 0)
                order.others_discount = mount
            order.end_total = order.base_total + decimal.Decimal(order.delivery_price)
            try:
                if request.session['active_coupon']:
                    coupon = CouponValidator.validate(request.session['active_coupon'],request.user)
                    order.coupon_percent = coupon.discount_percent
                    order.coupon = coupon
                    coupon.used = True
                    coupon.applied_to_order = order
                    coupon.save()
            except:
                pass                
        order.save()
        # all set, empty cart
        cart.empty_cart(request)
    # return the new order object
    results = {'order_number':order.id,'message':'Creo la orden'}
    return results

# Generar el pdf
# Para visualizar las imagenes en el pdf
def link_callback(uri, rel):
            result = finders.find(uri)
            if result:
                    if not isinstance(result, (list, tuple)):
                            result = [result]
                    result = list(os.path.realpath(path) for path in result)
                    path=result[0]
            else:
                    sUrl = settings.STATIC_URL       
                    sRoot = settings.STATIC_ROOT     
                    mUrl = settings.MEDIA_URL        
                    mRoot = settings.MEDIA_ROOT   

                    if uri.startswith(mUrl):
                            path = os.path.join(mRoot, uri.replace(mUrl, ""))
                    elif uri.startswith(sUrl):
                            path = os.path.join(sRoot, uri.replace(sUrl, ""))
                    else:
                            return uri

            # make sure that file exists
            if not os.path.isfile(path):
                    raise RuntimeError(
                            'media URI must start with %s or %s' % (sUrl, mUrl)
                    )
            return path


def generate_daily_summary_pdf(order_id):
    try:
        # Obtener la orden y procesar datos
        order = Order.objects.get(id=order_id, is_daily_summary=True)
        
        # Procesar métodos de pago con detalles
        payment_methods = []
        for payment in order.payment_methods.all():
            payment_data = {
                'method': payment.get_method_display(),
                'amount': payment.amount,
                'transaction_count': payment.transaction_count,
                'details': []
            }
            
            # Procesar detalles para transferencias
            if (payment.method == 'TRANSFER' or payment.method == 'CARD') and payment.transaction_details:
                try:
                    # Convertir JSON a lista de diccionarios
                    details = json.loads(payment.transaction_details)
                    if isinstance(details, list):
                        payment_data['details'] = details
                except json.JSONDecodeError:
                    pass
            payment_methods.append(payment_data)
        
        # Contexto para la plantilla
        context = {
            'order': order,
            'payment_methods': payment_methods,
            'total_general': sum(p.amount for p in order.payment_methods.all()),
            'date': order.date.strftime('%d/%m/%Y')
        }
        
        # Renderizar HTML
        html = render_to_string('checkout/resumen_diario_pdf.html', context)
        
        # Crear respuesta PDF
        response = HttpResponse(content_type='application/pdf')
        filename = f"resumen_diario_{order.date.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Generar PDF
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('Error al generar PDF', status=500)
        return response
        
    except Order.DoesNotExist:
        return HttpResponse("Orden no encontrada", status=404)


def checkOrderSummary(id_order):
    order = Order.objects.filter(id=id_order)[0]
    transfer_amount = decimal.Decimal('0.00')
    cards_amount = decimal.Decimal('0.00')
    if order.is_daily_summary and order.currency == 'USD':
        payment_methods = order.payment_methods.all()
        for payment in payment_methods:
            if payment.method == "TRANSFER":
                transfer_amount = transfer_amount + payment.amount
            elif payment.method == "CARD":
                cards_amount = cards_amount + payment.amount
        efectivo = (order.total_items * 120) - transfer_amount - cards_amount
        return (order.total_items * 120) - transfer_amount - cards_amount

def export_pdf(request, id_orden):
    data = {}
    #Diccionario de factura
    current_factura = {}        
    #QR datos de transaccion
    qr_generado = '{"id_orden": ' + str(id_orden)
    order = Order.objects.filter(id=id_orden)[0] 
    #Generando reporte PDF
    if order.is_daily_summary:
        check = checkOrderSummary(id_order=id_orden)
        # Procesar métodos de pago con detalles
        payment_methods = []
        transfer_sum = 0
        for payment in order.payment_methods.all():
            payment_data = {
                'method': payment.get_method_display(),
                'amount': payment.amount,
                'transaction_count': payment.transaction_count,
                'details': []
            }

            # Procesar detalles para transferencias
            if (payment.method == 'TRANSFER' or payment.method == 'CARD'):
                transfer_sum = transfer_sum + payment.amount
            if (payment.method == 'TRANSFER' or payment.method == 'CARD') and payment.transaction_details:
                try:
                    # Convertir JSON a lista de diccionarios
                    details = json.loads(payment.transaction_details)
                    if isinstance(details, list):
                        payment_data['details'] = details
                except json.JSONDecodeError:
                    pass
            payment_methods.append(payment_data)
        data['payment_methods'] = payment_methods
        p_methods = order.payment_methods.all()
        total_general = sum(p.amount for p in order.payment_methods.all())
        data['total_general'] = total_general
        if check > 0:
            data['importe'] = decimal.Decimal(round(order.total_items, 2))
            data['importeCUP'] = decimal.Decimal(round(order.total_items, 2))*120
            data['efectivo'] = data['importeCUP'] - transfer_sum
            data['seller'] = order.seller.first_name + ' ' + order.seller.last_name
            template_src = 'checkout/factura_resumen_diario_USD.html'
        else:
            data['importe'] = decimal.Decimal(round(order.total_items, 2))
            data['importeCUP'] = decimal.Decimal(round(order.total_reported, 2))
            data['seller'] = order.seller.first_name + ' ' + order.seller.last_name
            template_src = 'checkout/factura_resumen_diario.html' 
    elif order.transaction_id == '3': # Factura por contrato order.user.groups.filter(name__in=['comercial']):
        template_src = 'checkout/factura_por_contrato.html'
        data['first_name'] = order.payment_name
        data['email'] = order.payment_email
        data['phone'] = order.payment_phone
        data['address'] = order.payment_address
        data['details'] = order.payment_details
        data['importe'] = decimal.Decimal(round(order.total, 2))
    elif order.user.groups.filter(name__in=['vendedores']):
        template_src = 'checkout/factura_punto_de_venta.html'
        data['first_name'] = order.payment_name
        data['last_name'] = order.user.first_name + ' ' + order.user.last_name
        data['email'] = order.payment_email
        data['phone'] = order.payment_phone 
        data['importe'] = decimal.Decimal(round(order.total, 2))
        data['puntos'] = order.wallet_discount
    else:
        template_src = 'checkout/factura_venta_online.html'
        data['first_name'] = order.payment_name
        data['last_name'] = order.user.username + ': ' + order.user.first_name + ' ' + order.user.last_name
        data['email'] = order.payment_email
        data['phone'] = order.payment_phone
        data['importe'] = decimal.Decimal(round(order.total, 2))
        data['status'] = order.statusS
    template = get_template(template_src)
    data['id_order'] = str(id_orden).zfill(6)
    orders = OrderItem.objects.filter(order=id_orden).order_by('product')
    discount = False
    for item in orders:
         if item.has_discount:
              discount = True
              break
    if discount:
        data['discount_item'] = "True"
    else:
         data['discount_item'] = "False"
    data['order'] = order
    # Cargar el perfil del usuario
    user_profile = Profile.objects.get(user=order.user)
    if order.user.groups.filter(name__in=['comercial']):
        data['date'] = ''
    else:
         data['date'] = order.date
    data['delivery_name'] = order.delivery_name
    try:
        if order.store_name == "Envío Habana":
            delivery_add1 = order.delivery_street + " " + order.delivery_apto
            if order.delivery_between:
                delivery_add1 = delivery_add1 + " entre " + order.delivery_between 
            delivery_add1 = delivery_add1 + ". " + order.SUBSTATE[order.delivery_substate][1] + ", " + order.delivery_state
            data['delivery_add1'] = delivery_add1
        else:
            data['delivery_add1'] = order.store_name
    except:
        data['delivery_add1'] = ''
    if order.delivery_address_2:
        data['delivery_add2'] = order.delivery_address_2
    data['state'] = order._state
    data['delivery_phone'] = order.delivery_phone
    data['delivery_ws'] = order.delivery_ws
    data['CI'] = order.delivery_ci
    data['delivery_price'] = decimal.Decimal(order.delivery_price)
    data['currency'] = order.currency
    data['coupon'] = '0'
    if order.coupon:
        data['coupon'] = order.coupon_percent 
    data['discount'] = '0'
    if order.others_discount:
        data['discount'] = order.others_discount 
    data['puntos'] = order.wallet_discount
    data['monto_final'] = data['importe'] - data['puntos']
    context = {'data': data, 'orders': orders, 'request': request,'qr':qr_generado}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="factura.pdf"'
    html = template.render(context)
    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response, link_callback=link_callback)
    # if error then show some funny view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response
