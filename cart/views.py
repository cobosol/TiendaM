from django.shortcuts import render, redirect, get_object_or_404
from django import forms
from django.urls import reverse
from django.template import RequestContext
from cart import cart
from django.http import HttpResponseRedirect
from catalog.forms import ProductAddToCartForm
from cart.forms import DeliveryForm
from cart.models import DeliveryInfo
import requests
import json
from registration.models import Profile
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from utils.models import Price
from stores.models import Store
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from ccheckout.ccheckout import get_checkout_url
from ccheckout.models import Coupon
from ccheckout.utils import send_coupon
from ccheckout.validators import CouponValidator
import decimal


def show_cart(request, template_name="cart/cart.html"):
    # Verificar que esté autenticado
    if not (request.user.is_authenticated):
        request.session['wallet_discount'] = ''
        messages.warning(request, "Debe estar autenticado para acceder al carrito")
        url = reverse('login')
        return HttpResponseRedirect(url)
    cart.verify_mnd(request)
    form = DeliveryForm(request=request)
    price = Price.objects.filter(is_active=True)[0] # Capturo la configración de precio actual
    MND = 'USD'
    user = request.user
    profile = get_object_or_404(Profile, user = user)
    #No hay envío, solo recogida en planta
    profile.prefered_store = get_object_or_404(Store, pk=1)
    MND = profile.MONEY_TYPE[profile.money_type][1]
    try:
        if request.method == 'POST':
            postdata = request.POST.copy()
            if postdata['submit'] == 'X': # Eliminar producto del carrito
                cart.remove_from_cart(request)
            elif postdata['submit'] == '': # Actualizar cantidades del carrito (disminuir)
                print(postdata)
                cart.update_cart(request)
            elif postdata['submit'] == '>': # Actualizar cantidades del carrito (aumentar)
                print(postdata)
                cart.update_cart(request)
            elif postdata['submit'] == 'Buscar': # Buscar producto
                productSearch = postdata['producto']
                url = '/catalogo/productos/' + productSearch + '/'
                return HttpResponseRedirect(url)
            elif postdata['submit'] == 'Aplicar cupón': # Aplicar cupón de descuento
                if postdata['coupon'] == '':
                    text = "Debe introducir un código de cupón válido"
                    messages.error(request, text)
                else:
                    coupon = CouponValidator.validate(postdata['coupon'], user)
                    if coupon:
                        request.session['active_coupon'] = str(coupon.code)
                        text = "Cupón activado correctamente"
                        messages.info(request, text)
                    else:
                        messages.error(request, f"cupon falso {coupon}")
            elif postdata['submit'] == 'Usar puntos': # Aplicar puntos
                try:
                    cart_subtotal = cart.cart_subtotal(request)
                    wallet_to_apply = request.POST.get('wallet_to_apply', '')
                    wallet_to_apply = wallet_to_apply.replace(',','.')
                    if float(wallet_to_apply) > float(request.user.wallet.balance):
                        messages.info(request, 'No puede utilizar más puntos de los disponibles')
                        url = reverse('show_cart')
                        return HttpResponseRedirect(url)
                    if MND == 'CUP':
                        if float(wallet_to_apply) > cart_subtotal/2:
                            messages.info(request, 'No puede utilizar en la compra más del 50% de puntos')
                            url = reverse('show_cart')
                            return HttpResponseRedirect(url)
                    else:
                        if float(wallet_to_apply) > cart_subtotal*120/2:
                            messages.info(request, 'No puede utilizar en la compra más del 50% en puntos')
                            url = reverse('show_cart')
                            return HttpResponseRedirect(url)
                    response = cart.wallet_discount(request, cart_subtotal, wallet_to_apply)
                    resp = json.loads(response.content)
                    if not resp.get('success'):
                        text = resp['message']
                        messages.info(request, text)
                    else:
                        messages.success(request, 'Puntos aplicados con éxito')
                except Exception as e:
                    messages.error(request, f'Error. {e}')
            elif postdata['submit'] == 'Reservar': # Reservar producto sin pagar
                if request.user.is_authenticated:
                    if MND == 'USD':
                        url = reverse('reservar')
                        return HttpResponseRedirect(url)
            elif postdata['submit'] == 'Ir a pagar':
                    if MND == 'USD':
                        """if cart.cart_subtotal(request) < 2:
                            text = "El monto mínimo para la compra en línea es de 2.00 USD"
                            messages.error(request, text)
                            cart_url = reverse('show_cart')
                            return HttpResponseRedirect(cart_url) """
                        url = reverse('reservar') #reverse('checkout') Mientras no esté activa la plataforma de pagos
                        return HttpResponseRedirect(url)
                    else:
                        url = reverse('pagar')
                        return HttpResponseRedirect(url)
            elif postdata['submit'] == 'Confirmar pago':
                url = reverse('efectivo')
                return HttpResponseRedirect(url)
            elif postdata['submit'] == 'Facturar':
                url = reverse('facturar')
                return HttpResponseRedirect(url)
            elif postdata['submit'] == 'Resumen':
                url = reverse('resumen')
                return HttpResponseRedirect(url)
            elif postdata['submit'] == 'Buscar':
                productSearch = postdata['producto']
                url = '/catalogo/productos/' + productSearch + '/'
                return HttpResponseRedirect(url)
            elif postdata['submit'] == 'Actualizar entrega':
                form = DeliveryForm(request, postdata)
                form.storeDelivery = postdata['storeDelivery']
                form.deliveryZone = postdata['deliveryZone']
                delivery = postdata['storeDelivery']
                zone = postdata['deliveryZone']
                cart.set_delivery(request, delivery, zone)
                if (user.is_authenticated):
                    profile.prefered_store = get_object_or_404(Store, pk = postdata['storeDelivery'])
                    profile.save()
            else:
                messages.info(request, "Órden no identificada")
    except forms.ValidationError as e:
        messages.error(request, str(e))

    cart_items = cart.get_cart_items(request)
    if not cart_items:
        request.session['wallet_discount'] = ''
    """ for cart_i in cart_items:
        text = cart_i.discount_message()
        if text != "":
            messages.info(request, text) """
    page_title = 'Shopping Cart'
    cart_subtotal = cart.cart_subtotal(request)
    print(f'Al salir {cart_subtotal}')
    cart_delivery = cart.cart_delivery_price(request, cart_subtotal, MND)
    delivery_name = str(cart.delivery_name(request))
    envio = False
    if delivery_name == 'Envío Habana':
        envio = True 
    discount = request.session.get('wallet_discount', 0)
    discountChange = discount
    if discount:
        if MND == "CUP":
            cart_total = cart_subtotal + cart_delivery - decimal.Decimal(discount)
        else:
            discount = discount/120
            cart_total = cart_subtotal + cart_delivery - decimal.Decimal(discount)
    else:
        cart_total = cart_subtotal + cart_delivery
        discount = 0.00
    discount = round(discount,2)
    deliveryObj = get_object_or_404(DeliveryInfo, client=user)
    zone = deliveryObj.getDeliveryZone
    cart_subtotal = float(cart_subtotal)
    cart_delivery = float(cart_delivery)
    cart_total = float(cart_total)
    if MND == 'CUP':
        wallet_to_apply = round(min((cart_subtotal/2),user.wallet.balance),2)
    elif MND == 'USD':
        wallet_to_apply = round(min((cart_subtotal*120/2),user.wallet.balance),2)
    else:
        wallet_to_apply = 0.00
    context = {'cart_total':cart_total, 'envio': envio, 'wallet_to_apply': wallet_to_apply, 'discountChange':discountChange, 
               'delivery_name': delivery_name, 'cart_delivery':cart_delivery, 'discount':discount, 
               'cart_subtotal':cart_subtotal, 'zone':zone, 'cart_items':cart_items, 'MND':MND}
    return render(request, template_name, context)