from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseRedirect
from .forms import * 
from django.urls import reverse
from .models import Order, OrderItem
from ccheckout.ccheckout import generate_daily_summary_pdf, process2, export_pdf, createPaymentCardsJSON, tPAccessToken, loadSecret, create_order
from cart import cart
from cart.models import DeliveryInfo
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
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
from .filtros import *
# Hacer resumen diario de punto de venta.
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .validators import CouponValidator
from django.db.models import Sum, Count, Avg, F, ExpressionWrapper, FloatField
from datetime import datetime, timedelta
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone

@require_POST
@login_required
def apply_coupon(request):
    coupon_code = request.POST.get('coupon_code')
    try:
        coupon = CouponValidator.validate(coupon_code, request.user)
        # Aplicar descuento a la orden en sesión o base de datos
        request.session['active_coupon'] = str(coupon.code)
        return JsonResponse({'success': True, 'discount': coupon.discount_percent})
    except: #forms.ValidationError as e
        return JsonResponse({'success': False, 'error': str('e')})
    

# Retorno del pago en Tropipay
@csrf_exempt
@require_http_methods(["POST"])
def payment_notification(request):
    #response = json.loads(request.__dict__()) #.raw_post_data
    #response2 = json.loads(str(request))
    #js = request.json()
    #response = json.loads(js)
    #status = json.loads(request.POST.get('status')) 
    #print(status)
    response = json.loads(request.body)
    #print(response)
    
    """ st = response["status"]
    print("response[status]")
    print(st) """

    status = response.get("status")
    
    try:
        if response.get("status") == 'OK':
            print("if")
        
        data = response["data"]
        signature = data["signaturev2"]
        bankOrderCode = data["bankOrderCode"]
        creds = loadSecret()
        clientId = creds["client_id"]
        clientSecret = creds["client_secret"]
        originalCurrencyAmount = data["originalCurrencyAmount"]
        #print("CI: " + clientId)
        #print("CS: " + clientSecret)
        chekSignature = hashlib.sha256(str(bankOrderCode + clientId + clientSecret + originalCurrencyAmount).encode('utf-8'))
        #print("checked")
        encodehash = chekSignature.hexdigest()
        #print(encodehash)
        if signature == encodehash:
            #print("Confirmed")
            paymentcard = data["paymentcard"]
            order_number = paymentcard["reasonId"]
            #print(order_number)
            if order_number:
                order = get_object_or_404(Order, id=order_number) 
                order.status = Order.PROCESSED
                order.transaction_id = data["id"]
                order.save()
            else:
                print("Error al generar orden")
        else:
            print("No coinciden las firmas")
    except OSError:
        print("OSError --- status"+status)
   
    return request

# Donde redirecciona al usuario Tropipay después de pagar
def hit(request):
    order_number = request.session.get('order_number','')
    if order_number:
        order = Order.objects.filter(id=order_number)[0]
        if order.status == Order.PROCESSED: #SUBMITTED: # PROCESSED
            order.update_status(Order.PAIDED)
            order.save()
            receipt_url = reverse('checkout_receipt')
            return HttpResponseRedirect(receipt_url)
        else:
            fail_url = reverse('checkout_fail')
            return HttpResponseRedirect(fail_url)
    else:
        print("Error en el numero de la orden")

# El view de la página de pago
@login_required
def show_checkout(request, template_name='checkout/checkout.html'):
    MND = 'USD'
    if cart.is_empty(request):
        cart_url = reverse('show_cart')
        return HttpResponseRedirect(cart_url)
    if request.method == 'POST': 
        postdata = request.POST.copy()
        if postdata['submit'] == ' ':
            form = CheckoutForm(postdata)
            if form.is_valid():
                order_number = create_order(request, 2) 
                error_message = postdata.get('message','')
                if order_number['order_number'] == -1:
                    fail = reverse('show_cart')
                    return HttpResponseRedirect(fail)
                if order_number:
                    request.session['order_number'] = order_number['order_number']
                    response = createPaymentCardsJSON(request, order_number)
                    dicto = json.loads(response.content)
                    try:
                        url_pay = dicto["shortUrl"]
                        order = Order.objects.filter(id=order_number['order_number'])[0]
                        order.pay_url = url_pay
                        order.save()
                        order.update_status(order.PROCESSED)
                        order.save()
                        return HttpResponseRedirect(url_pay)
                    except Exception as e:
                        print(f"Error en: {e}")
                        if dicto["error"]["code"] in ["EXPIRED_TOKEN", "INVALID_CREDENTIAL", "FORBIDDEN_ERROR"]:
                            response = tPAccessToken()
                            dicto = json.loads(response.content)
                            creds = loadSecret()
                            creds["token"] = dicto.get('access_token')
                            #"Guardo el token actualizado en el fichero")
                            with open('secrets.txt', 'w') as archivo:
                                json.dump(creds, archivo)
                            #("Llamo por segunda vez al pago")
                            response2 = createPaymentCardsJSON(request, order_number)
                            try:
                                dicto2 = json.loads(response2.content)
                                url_pay = dicto2["shortUrl"]
                                order = Order.objects.filter(id=order_number['order_number'])[0]
                                order.pay_url = url_pay
                                order.save()
                                order.update_status(order.PROCESSED)
                                order.save()
                                return HttpResponseRedirect(url_pay)
                            except:
                                fail_url = reverse('checkout_fail')
                                return HttpResponseRedirect(fail_url)
                        else:
                            print(f'Error en AccessToken{dicto["error"]}')
                            fail_url = reverse('checkout_fail')
                            return HttpResponseRedirect(fail_url)
            else:
                fail_url = reverse('checkout_fail')
                return HttpResponseRedirect(fail_url)
        """ else:
            form = CachForm(postdata)
            if form.is_valid():
                order_number = create_order(request, 1, True, True) # Crear la orden con tipo de transacción 1 usd en cach
                if order_number['order_number'] == -1:
                    fail = reverse('show_cart')
                    return HttpResponseRedirect(fail)
                error_message = postdata.get('message','')
                if order_number:
                    request.session['order_number'] = order_number['order_number']
                    order = Order.objects.filter(id=order_number['order_number'])[0]
                    order.transaction_id = 1 # 1 para pago en efectivo USD 
                    order.save()
                    order.update_status(Order.PAIDED)
                    order.update_status(Order.DELIVERED)
                    order.save()
                    receipt_url = reverse('checkout_receipt')
                    return HttpResponseRedirect(receipt_url) """
    else:
        form = CheckoutForm()
        form.name = request.user.first_name + request.user.last_name
    page_title = 'Checkout'
    cobra_efectivo = False
    cart_subtotal = cart.cart_subtotal(request)
    cart_delivery = cart.cart_delivery_price(request, cart_subtotal, MND)
    cart_total = cart_subtotal + cart_delivery
    st_name = cart.delivery_Store(request).name
    envio = False
    deli = cart.get_delivery(request)
    if deli == '3':
        envio = True 
    if (request.user.groups.filter(name='vendedor').exists() or request.user.is_superuser):
        cobra_efectivo = True
    return render(request, template_name, locals())

@login_required
def cach(request, template_name='checkout/cach.html'):
    MD = 'USD'
    if cart.is_empty(request):
        cart_url = reverse('show_cart')
        return HttpResponseRedirect(cart_url)
    if request.method == 'POST': 
        postdata = request.POST.copy()
        if postdata['submit'] == 'Confirmar pago':
            form = CachForm(postdata)
            if form.is_valid():
                user = request.user
                profile = get_object_or_404(Profile, user = user)
                MD = profile.MONEY_TYPE[profile.money_type][1]
                if MD == 'USD':
                    order_number = create_order(request, 1, True, True) # Crear la orden con tipo de transacción 1 usd en cach
                    if order_number['order_number'] == -1:
                        fail = reverse('show_cart')
                        return HttpResponseRedirect(fail)
                else:
                    order_number = create_order(request, 3, False, True)
                    if order_number['order_number'] == -1:
                        fail = reverse('show_cart')
                        return HttpResponseRedirect(fail)
                error_message = postdata.get('message','')
                if order_number:
                    request.session['order_number'] = order_number['order_number']
                    order = Order.objects.filter(id=order_number['order_number'])[0]
                    order.transaction_id = 1 # 1 para pago en efectivo USD 
                    order.save()
                    order.update_status(Order.PAIDED)
                    order.update_status(Order.DELIVERED)
                    order.save()
                    receipt_url = reverse('checkout_receipt')
                    return HttpResponseRedirect(receipt_url)
    else:
        form = CachForm()
    page_title = 'Cach'
    cobra_efectivo = False
    cart_subtotal = round(cart.cart_subtotal(request), 2)
    cart_delivery = cart.cart_delivery_price(request, cart_subtotal, MD)
    cart_total = cart_subtotal + cart_delivery
    st_name = cart.delivery_Store(request).name
    envio = False
    deli = cart.get_delivery(request)
    if deli == '3':
        envio = True 
    if (request.user.groups.filter(name = 'vendedores').exists() or request.user.groups.filter(name = 'comercial').exists() or request.user.is_staff):
        cobra_efectivo = True
    return render(request, template_name, locals())

@login_required
def facturar(request, template_name='checkout/facturar.html'):
    MD = 'USD'
    if cart.is_empty(request):
        cart_url = reverse('show_cart')
        return HttpResponseRedirect(cart_url)
    if request.method == 'POST': 
        postdata = request.POST.copy()
        if postdata['submit'] == 'Efectuar pago':
            form = FacturarForm(postdata)
            if form.is_valid():
                user = request.user
                profile = get_object_or_404(Profile, user = user)
                MD = profile.MONEY_TYPE[profile.money_type][1]
                if MD == 'USD':
                    order_number = create_order(request, 3, True, True) # Crear la orden con tipo de transacción 3 usd en cach
                    if order_number['order_number'] == -1:
                        fail = reverse('show_cart')
                        return HttpResponseRedirect(fail)
                elif MD == 'CUP':
                    order_number = create_order(request, 3, False, True)
                    if order_number['order_number'] == -1:
                        fail = reverse('show_cart')
                        return HttpResponseRedirect(fail)
                else:
                    order_number = create_order(request, 3, False, False)
                    if order_number['order_number'] == -1:
                        fail = reverse('show_cart')
                        return HttpResponseRedirect(fail)
                error_message = postdata.get('message','')
                if order_number:
                    request.session['order_number'] = order_number['order_number']
                    order = Order.objects.filter(id=order_number['order_number'])[0] 
                    order.save()
                    order.update_status(Order.PAIDED)
                    order.update_status(Order.DELIVERED)
                    order.save()
                    receipt_url = reverse('checkout_receipt')
                    return HttpResponseRedirect(receipt_url)
            else:
                print("Error de validacion de la form")
    else: # Si no es llamada post
        form = FacturarForm()
        #form.name = request.user.first_name + request.user.last_name
    page_title = 'Facturar'
    #cobra_efectivo = False
    cart_subtotal = round(cart.cart_subtotal(request), 2)
    cart_delivery = cart.cart_delivery_price(request, cart_subtotal, MD)
    cart_total = cart_subtotal + cart_delivery
    st_name = cart.delivery_Store(request).name
    envio = False
    #deli = cart.get_delivery(request) 
    """ if (request.user.groups.filter(name = 'vendedores').exists() or request.user.groups.filter(name = 'comercial').exists() or request.user.is_staff):
        cobra_efectivo = True """
    return render(request, template_name, locals())

# El view de la página de pago nacional
@login_required
def pagar(request, template_name='checkout/pagar.html'):
    MD = 'USD'
    if cart.is_empty(request):
        cart_url = reverse('show_cart')
        return HttpResponseRedirect(cart_url)
    if request.method == 'POST': 
        postdata = request.POST.copy()
        if postdata['submit'] == 'Efectuar pago':
            form = PagarForm(postdata)
            if form.is_valid():
                user = request.user
                profile = get_object_or_404(Profile, user = user)
                MD = profile.MONEY_TYPE[profile.money_type][1]
                order_number = create_order(request, 1, False, False) # Crear la orden con tipo de transacción 1 usd en cach
                if order_number['order_number'] == -1:
                    fail = reverse('show_cart')
                    return HttpResponseRedirect(fail)
                error_message = postdata.get('message','')
                if order_number:
                    request.session['order_number'] = order_number['order_number']
                    order = Order.objects.filter(id=order_number['order_number'])[0]
                    order.pay_url = order.get_transfer_pay_url()
                    order.update_status(Order.PROCESSED)
                    order.save()
                    pagarTransfer = order.pay_url #reverse(order.pay_url)
                    return HttpResponseRedirect(pagarTransfer)
    else:
        form = PagarForm()
        form.name = request.user.first_name + request.user.last_name
    page_title = 'Transfermovil'
    cobra_efectivo = False
    cart_subtotal = round(cart.cart_subtotal(request), 2)
    cart_delivery = cart.cart_delivery_price(request, cart_subtotal, MD)
    cart_total = cart_subtotal + cart_delivery
    st_name = cart.delivery_Store(request).name
    envio = False
    deli = cart.get_delivery(request)
    if deli == '3':
        envio = True 
    if (request.user.groups.filter(name = 'vendedores').exists() or request.user.groups.filter(name = 'comercial').exists() or request.user.is_staff):
        cobra_efectivo = True
    return render(request, template_name, locals())

@login_required
def reserve(request, template_name='checkout/reserve.html'):
    # Reservar productos sin pagar
    MD = 'USD'
    st_name = cart.delivery_Store(request).name # Nombre del tipo de entrega
    if cart.is_empty(request): #Si el carrito está vacío
        cart_url = reverse('show_cart')
        return HttpResponseRedirect(cart_url) # Vuelvo al carrito
    if request.method == 'POST': # Analizo todas las funcionalidades disponibles
        postdata = request.POST.copy()
        if postdata['submit'] == 'Reservar': # Cuando el cliente va a reservar sin pagar
            if st_name == 'Envío Habana':
                form = ReserveForm(postdata) #Guardo los datos que vienen en la form con datos de entrega
            else:
                form = ReserveEForm(postdata) #Guardo los datos que vienen en la form sin datos de entrega
            if form.is_valid(): # Si trae todos los datos necesarios
                user = request.user
                profile = get_object_or_404(Profile, user = user)
                MD = profile.MONEY_TYPE[profile.money_type][1] # Guardo el tipo de moneda con que está el cliente
                order_number = create_order(request, 2, True, True) # Crear la orden con tipo de transacción 2(Reservar) usd y cach (Aunque no es cach)
                if order_number['order_number'] == -1: # Si no se creó una orden
                    fail = reverse('show_cart')
                    return HttpResponseRedirect(fail) # Vuelvo al carrito
                if order_number: # Si se generó correctamente la orden
                    request.session['order_number'] = order_number['order_number'] #Guardo el número de orden en la sesión
                    order = Order.objects.filter(id=order_number['order_number'])[0] #Construyo la orden a partir del numero
                    order.update_status(Order.PROCESSED) # Actualizo el status a procesada.
                    order.save() 
                    notification_user_sale(request) # Envío notificación por correo a usuario
                    notification_reserve(request) # Envío notificacion por correo a la administración
                    receipt_url = order.get_paided_url() # Capturo elurl de detales de la orden
                    return HttpResponseRedirect(receipt_url) # redirijo a los detalles
    else: #Si no es llamada post. Cargar la página normal
        if st_name == 'Envío Habana':
            form = ReserveForm() # construyo la form con datos de entrega
        else:
            form = ReserveEForm() #Construyo la form sin datos de entrega  
    page_title = 'Reservar'
    #cobra_efectivo = False
    cart_subtotal = round(cart.cart_subtotal(request), 2) # Capturo suma de productos 
    cart_delivery = cart.cart_delivery_price(request, cart_subtotal, MD) # Capturo precio de entrega
    cart_total = cart_subtotal + cart_delivery # Total: Productos + entrega
    envio = False
    deli = cart.get_delivery(request) # Capturo el id del tipo de entrega
    if deli == '3': # Si es 3 (Envío habana). ##### Esto hay que hacerlo genérico  
        envio = True 
    return render(request, template_name, locals())

@login_required
def transfer(request, template_name='checkout/transfer.html', id=0):
    order = Order.objects.filter(id=id)[0]
    if request.method == 'POST': 
        postdata = request.POST.copy()
        if postdata['submit'] == 'Confirmar':
            if id == 0:
                order = Order.objects.filter(id=request.session['order_number'])[0]
            else:
                order = Order.objects.filter(id=id)[0]
            order.transaction_id = postdata['TransferId']
            order.update_status(Order.PAIDED)
            order.save()
            notification_user_sale(request)
            notification_sale(request)
            receipt_url = reverse('checkout_procesado')
            return HttpResponseRedirect(receipt_url)
    return render(request, template_name, locals())

def create_daily_summary(request):
    MD = 'USD'
    if cart.is_empty(request):
        cart_url = reverse('show_cart')
        return HttpResponseRedirect(cart_url)
    if request.method == 'POST':
        formset = PaymentMethodFormSet(request.POST, prefix='payments')
        if MD == 'USD':
            order_number = create_order(request, 4, True, True) # Crear la orden con tipo de transacción 3 usd en cach
            if order_number['order_number'] == -1:
                fail = reverse('show_cart')
                return HttpResponseRedirect(fail)
        elif MD == 'CUP':
            order_number = create_order(request, 4, False, True)
            if order_number['order_number'] == -1:
                fail = reverse('show_cart')
                return HttpResponseRedirect(fail)
        else:
            messages.info(request, "El resumen es solo en CUP o USD")  
        if order_number:
            request.session['order_number'] = order_number['order_number']
            order = Order.objects.filter(id=order_number['order_number'])[0] 
            order.save()
            order.update_status(Order.PAIDED)
            order.update_status(Order.DELIVERED)
            if formset.is_valid():
                # Crear orden especial
                formset.instance = order
                formset.save()
                order.end_total = sum([form.cleaned_data['amount'] for form in formset])
                order.save()
                app_label = order._meta.app_label
                model_name = order._meta.model_name
                messages.success(request, "Resumen creado con éxito")
                receipt_url = order.get_absolute_url()
                return HttpResponseRedirect(receipt_url)
        else:
            print("Error de validacion de la form")       
    else:
        order_form = DailySummaryForm()
        formset = PaymentMethodFormSet(prefix='payments', queryset=PaymentMethod.objects.none())
        cart_total = round(cart.cart_subtotal(request), 2)        
        st_name = cart.delivery_Store(request).name
        price = Price.objects.filter(is_active=True)[0] # Capturo la configuración de precio actual
        t_CUP_alcambio = cart_total * price.change_usd_cup
        t_CUP_Oficial = cart_total * 120
    
    return render(request, 'checkout/create_summary.html', {
        'order_form': order_form,
        'formset': formset,
        'cart_total': cart_total,
        'st_name': st_name,
        't_CUP_alcambio': t_CUP_alcambio,
        't_CUP_oficial': t_CUP_Oficial
    })
 

def download_daily_summary_pdf(request, order_id):
    return generate_daily_summary_pdf(order_id)

# El view de la página de pago completado por plataforma internacional
@login_required
def receipt(request, template_name='checkout/receipt.html'):
    order_number = request.session.get('order_number','')
    order = Order.objects.filter(id=order_number)[0]
    if order_number and order.status == order.PAIDED:    
        order_items = OrderItem.objects.filter(order=order_number)
        orderN = order_number
        user = order.user
    else:
        cart_url = reverse('show_cart')
        return HttpResponseRedirect(cart_url)
    # Capturar el POST de un botón para generar pdf
    if request.method == 'POST':
        del request.session['order_number']
        return export_pdf(request, order_number)
    return render(request, template_name, locals())

# El view de la página de pago completado por transfermovil
@login_required
def confirmado(request, order_id, template_name='checkout/confirmado.html'):
    #order_number = request.session.get('order_number','')
    order = Order.objects.filter(id=order_id)[0]
    order_number = order.id
    discounts = "False"
    if order.status == order.PROCESSED or order.status == order.PAIDED:    
        order_items = OrderItem.objects.filter(order=order_number)
        for item in order_items:
            if item.has_discount:
                discounts = "True"
                break
        orderN = order_number
        user = order.user
    else:
        cart_url = reverse('show_cart')
        return HttpResponseRedirect(cart_url)
    # Capturar el POST de un botón para generar pdf
    if request.method == 'POST':
        del request.session['order_number']
        return export_pdf(request, order_number)
    user = request.user
    profile = get_object_or_404(Profile, user = user)
    MND = profile.MONEY_TYPE[profile.money_type][1]
    cart_subtotal = round(cart.cart_subtotal(request), 2)
    cart_delivery = cart.cart_delivery_price(request, cart_subtotal, MND)
    cart_total = cart_subtotal + cart_delivery
    st_name = cart.delivery_Store(request).name
    envio = False
    deli = cart.get_delivery(request)
    if deli == '3':
        envio = True
    return render(request, template_name, locals())

# El view de la lista de órdenes (compras) realizadas por el usuario
@login_required
def orders_list(request, template_name='checkout/orders_list.html'):
    orders = Order.objects.filter(user=request.user).order_by('-date')
    
    filter = FiltroOrder

    status = request.GET.get('status')
    store_name = request.GET.get('store_name')
    currency = request.GET.get('currency')

    if status:
        if status!='':
            orders = orders.filter(status__icontains = status)

    if store_name:
        if store_name!='':
            orders = orders.filter(store_name__icontains = store_name)

    if currency:
        if currency!='':
            orders = orders.filter(currency__icontains=currency)

    if request.method == 'POST':
        postdata = request.POST.copy()
        if postdata['submit'] == 'Factura':
            order_number = postdata['order_id']
            return export_pdf(request, order_number)
    user_name = request.user.first_name + " " + request.user.last_name
    return render(request, template_name, locals())

# view de la lista de ordenes (compras) relizadas a la tienda
def admin_orders_list(request, template_name='checkout/admin_orders_list.html'):
    orders = Order.objects.all().order_by('-date')
    
    filter = FiltroOrderAdmin

    status = request.GET.get('status')
    store_name = request.GET.get('store_name')
    currency = request.GET.get('currency')
    user = request.GET.get('user')

    if user:
        if user != '':
            orders= orders.filter(user=user).order_by('-date')
            
    if status:
        if status!='':
            orders = orders.filter(status__icontains = status).order_by('-date')

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
        if postdata['submit'] == 'Detalles':
            order_id = postdata['order_id']
            template = 'checkout/details.html'
            return redirect(reverse('details'))
        return HttpResponseRedirect(receipt)
    user_name = ""
    return render(request, template_name, locals())

# view de la página que se visualiza al usuario cuando hubo algún problema en el pago desde la pasarela.
def fail(request, template_name='checkout/fail.html'):
    order_number = request.session.get('order_number','')
    order = Order.objects.filter(id=order_number)[0]
    if order:
        order.status = Order.CANCELLED
        order.save()    
    return render(request, template_name, locals())

@login_required
def details(request, order_id, template_name='checkout/details.html'):
    order = Order.objects.filter(id=order_id)[0]
    subtotal = order.total - order.delivery_price    
    order_items = OrderItem.objects.filter(order=order_id)
    discounts = "False"
    for item in order_items:
            if item.has_discount:
                discounts = "True"
                break
    orderN = order_id
    user = order.user
    amounth_discount = "False"
    mount = 0
    if abs(order.total_items - order.base_total) > 0.01:
        amounth_discount = "True"
        mount = 100 - round((order.base_total / order.total_items * 100 ), 0)
    # Capturar el POST de un botón para generar pdf
    if request.method == 'POST':
        postdata = request.POST.copy()
        if postdata['submit'] == 'Generar Factura':
            return export_pdf(request, order_id)
        elif postdata['submit'] == 'Actualizar':
            form = UpdateStatusForm(request.POST)
            status = int(postdata['status'])
            order.update_status(status)
            order.save()
    else:
        form = UpdateStatusForm()
    return render(request, template_name, locals())

@login_required
def transfer_pay(request, order_id, template_name='checkout/transfer.html'):
    order = Order.objects.filter(id=order_id)[0]
    subtotal = order.total - order.delivery_price    
    order_items = OrderItem.objects.filter(order=order_id)
    orderN = order_id
    user = order.user
    if request.method == 'POST': 
        postdata = request.POST.copy()
        if postdata['submit'] == 'Confirmar':
            if order_id == 0:
                order = Order.objects.filter(id=request.session['order_number'])[0]
            else:
                order = Order.objects.filter(id=order_id)[0]
            order.transaction_id = postdata['TransferId']
            order.update_status(Order.PAIDED)
            order.save()
            notification_user_sale(request)
            notification_sale(request)
            receipt_url = order.get_paided_url()
            return HttpResponseRedirect(receipt_url)
    return render(request, template_name, locals())

def sales_manages(request):
    context = {}
    return render(request, 'checkout/resumenes_gaficos.html', locals())

def sales_products(request):
    # Obtener fechas del request
    start_date = request.GET.get('start_date', '2023-01-01')
    end_date = request.GET.get('end_date', datetime.today().strftime('%Y-%m-%d'))
    
    # Convertir a objetos datetime
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Filtrar órdenes en el rango
    orders = Order.objects.filter(date__range=[start, end], currency='USD')
    
    # 1. Cantidad vendida por producto
    products_data = list(
        OrderItem.objects
        .filter(order__in=orders)
        .values('product__name')
        .annotate(total_quantity=Sum('quantity'))
        .order_by('-total_quantity')
    )
    # Convertir Decimal a float
    for p in products_data:
        p['total_quantity'] = float(p['total_quantity'])
    
    # 2. Monto total por producto
    revenue_by_product = list(
        OrderItem.objects
        .filter(order__in=orders)
        .values('product__name')
        .annotate(total_revenue=ExpressionWrapper(Sum(F('price') * F('quantity')),
                                                  output_field=FloatField()
                                                  ) # Utilizar totalf que incluye los descuentos
        )
        .order_by('-total_revenue')
    )
    
    # Preparar datos para gráficas
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'products': json.dumps(products_data),
        'revenue_data': json.dumps(revenue_by_product),
    }

    return render(request, 'checkout/venta_productos.html', context)

def sales_client(request):
    # Obtener fechas del request
    start_date = request.GET.get('start_date', '2023-01-01')
    end_date = request.GET.get('end_date', datetime.today().strftime('%Y-%m-%d'))
    
    # Convertir a objetos datetime
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Filtrar órdenes en el rango
    orders = Order.objects.filter(date__range=[start, end], currency='USD')
    
    # 4. Compras por usuario (top 10)
    top_customers = list(
        orders.values('user__username')
        .annotate(
            total_spent=Sum('end_total'),
            order_count=Count('id')
        )
        .order_by('-total_spent')[:10]
    )

    for c in top_customers:
        c['total_spent'] = float(c['total_spent'])

    
    # Preparar datos para gráficas
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'top_customers': json.dumps(top_customers),
    }

    return render(request, 'checkout/venta_clientes.html', context)

def sales_summary(request):
    # Obtener fechas del request
    start_date = request.GET.get('start_date', '2023-01-01')
    end_date = request.GET.get('end_date', datetime.today().strftime('%Y-%m-%d'))
    
    # Convertir a objetos datetime
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Filtrar órdenes en el rango
    orders = Order.objects.filter(date__range=[start, end], currency='USD')
    
    # 3. Estadísticas generales
    total_orders = orders.count()

    avg_order_amount = orders.aggregate(avg=Avg('end_total'))['avg'] or 0
    avg_order_amount = float(avg_order_amount)

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
        .filter(date__range=[start_date, end_date], currency='USD')
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
    }

    return render(request, 'checkout/venta_resumen.html', context)

