from django.db import models
from django import forms
from django.contrib.auth.models import User
from catalog.models import Product
from stores.models import Store, Product_Sales
import decimal
from utils.models import Price
import json
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import uuid
import datetime

# Crear una clase delivery que incluya todas las definiciones de los envios.
# El municipio con los precios (diccionario), descuentos por monto...

class Order(models.Model):
    # each individual status
    SUBMITTED = 0
    PROCESSED = 1
    PAIDED = 2
    SHIPPED = 3
    CANCELLED = 4
    DELIVERED = 5
    RETURNED = 6
    CONFIRMED = 7
    # set of possible order statuses
    ORDER_STATUSES = ((SUBMITTED,'Solicitada'),
                      (PROCESSED,'Procesada'),
                      (PAIDED,'Pagada'),
                      (SHIPPED,'Transportando'),
                      (CANCELLED,'Cancelada'),
                      (DELIVERED,'Entregada'),
                      (RETURNED, 'Devuelta'),
                      (CONFIRMED, 'Confirmada'),
                      )
    
    # each individual substate
    GUANABACOA = 0
    HABANADELESTE = 1
    CERRO = 2
    COTORRO = 3
    DIEZDEOCTUBRE = 4
    HABANAVIEJA = 5
    CENTROHABANA = 6
    SANMIGUEL = 7
    BOYEROS = 8
    MARIANAO = 9
    LALISA = 10
    PLAZA = 11
    PLAYA = 12
    REGLA = 13
    ARROYO = 14

    # set of possible order statuses
    SUBSTATE = ((GUANABACOA,'Guanabacoa'),
                      (HABANADELESTE,'La Habana del Este'),
                      (CERRO,'Cerro'),
                      (COTORRO,'Cotorro'),
                      (DIEZDEOCTUBRE,'Diez de Octubre'),
                      (HABANAVIEJA,'La Habana Vieja'),
                      (CENTROHABANA, 'Centro Habana'),
                      (SANMIGUEL, 'San Miguel del Padrón'),
                      (BOYEROS,'Boyeros'),
                      (MARIANAO,'Marianao'),
                      (LALISA,'La Lisa'),
                      (PLAZA,'Plaza de la Revolución'),
                      (PLAYA, 'Playa'),
                      (REGLA, 'Regla'),
                      (ARROYO, 'Arroyo Naranjo'),
                      )
    

    # order info
    date = models.DateTimeField(auto_now_add=True, verbose_name = "Fecha de facturación")
    status = models.IntegerField(choices=ORDER_STATUSES, default=SUBMITTED, verbose_name = "Estado")
    ip_address = models.GenericIPAddressField(verbose_name = "Dirección ip")
    last_updated = models.DateTimeField(auto_now=True, verbose_name = "Última actualización")
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE, verbose_name = "Usuario")
    transaction_id = models.CharField(max_length=20, help_text="No. de transacción", verbose_name = "Nro. Transacción")
    vale_salida = models.CharField(max_length=20, null=True, blank=True, help_text="Vale salida almacén", verbose_name = "Vale almacén")
    delivery_price = models.IntegerField(verbose_name="Precio de envío", default=0)
    base_total = models.DecimalField(max_digits=10, decimal_places=2, default = 0.00, verbose_name="Total base")
    end_total = models.DecimalField(max_digits=10, decimal_places=2, default = 0.00, verbose_name="Total final con descuento y envío")
    usd_total = models.DecimalField(max_digits=10, decimal_places=2, default = 0.00, verbose_name="Total en USD")
    cup_total = models.DecimalField(max_digits=10, decimal_places=2, default = 0.00, verbose_name="Total en CUP")
    mlc_total = models.DecimalField(max_digits=10, decimal_places=2, default = 0.00, verbose_name="Total en MLC")
    total_reported = models.DecimalField(max_digits=10, decimal_places=2, default = 0.00, verbose_name="Total reportado")
    store_name = models.CharField(max_length=200, default="Envío Habana", verbose_name = "Nombre del tipo de entrega")
    coupon_percent = models.PositiveIntegerField(default=0, verbose_name="Porciento de descuento de cupón")
    others_discount = models.PositiveIntegerField(default=0, verbose_name="Porciento de otros descuentos")
    wallet_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pay_url = models.URLField(verbose_name="URL de pago", blank = True, null=True, default="")
    currency = models.CharField(max_length=3, default="USD", verbose_name = "Tipo de moneda")
    price = models.ForeignKey(Price, on_delete = models.PROTECT, blank = True, null=True, verbose_name="Valores para el cálculo del Precio de la compra")
    coupon = models.ForeignKey('Coupon', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name="Cupón de descuento")
    is_daily_summary = models.BooleanField(default=False, verbose_name="Es resumen diario")
    seller = models.ForeignKey(User, related_name="order_sumary", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Vendedor")

    # payment info
    payment_name = models.CharField(max_length=50, verbose_name = "Nombre del titular", null = True, blank = True)
    payment_phone = models.CharField(max_length=20, blank = True, null=True, verbose_name = "Teléfono móvil")
    payment_city = models.CharField(max_length=20, null=True, blank = True, default=None, verbose_name = "Ciudad del banco", help_text="Ciudad del banco de la tarjeta")
    payment_email = models.EmailField(max_length=50, null=True, blank = True, default=None, verbose_name = "Correo electrónico")
    payment_address = models.CharField(max_length=200, blank = True, null=True, verbose_name = "Dirección")
    payment_postCode = models.CharField(max_length=20, blank = True, null=True, verbose_name = "Código Postal")
    payment_details = models.CharField(max_length=200, blank = True, null=True, verbose_name = "Detalles de la compra")
    
    # delivery information
    delivery_name = models.CharField(max_length=50, verbose_name = "Nombre del beneficiario", null = True, blank = True)
    delivery_ci = models.CharField(max_length=25, verbose_name="Número de identidad", null=True, blank=True)
    delivery_phone = models.CharField(max_length=20, verbose_name = "Teléfono", null=True, blank=True)
    delivery_ws = models.CharField(max_length=20, verbose_name = "Teléfono WhatsApp", null=True, blank=True)
    delivery_street = models.CharField(default = " ", max_length=100, verbose_name = "Calle", null = True, blank = True)
    delivery_apto = models.CharField(default = " ", max_length=100, verbose_name = "Número/Apartamento", null = True, blank = True)
    delivery_between = models.CharField(default = " ", max_length=100, verbose_name = "Entre calles", null = True, blank = True)
    delivery_state = models.CharField(max_length=50, verbose_name = "Provincia", default="La Habana")
    delivery_substate = models.IntegerField(choices=SUBSTATE, default=GUANABACOA, verbose_name = "Municipio")
    #delivery_substate = models.CharField(max_length=50, verbose_name = "Municipio", null = True, blank = True)
    #delivery_address_1 = models.CharField(max_length=250, verbose_name = "Dirección", null = True, blank = True)
    delivery_address_2 = models.CharField(max_length=500, verbose_name = "Dirección alternativa", null = True, blank = True)
    
    delivery = models.ForeignKey('stores.Store', unique=False, null = True, verbose_name = "Tipo de entrega", blank = True, on_delete=models.SET_NULL)
    
    class Meta:
        verbose_name = "Orden de compra"

    def __unicode__(self):
        return 'Orden #' + str(self.id)

    def save(self, *args, **kwargs):
        if self.end_total is None or self.end_total == 0:
            self.end_total = self.total_items + decimal.Decimal(self.delivery_price)
        if self.base_total is None or self.base_total == 0:
            self.base_total = self.total_items 
        if self.total_reported == 0.00:
            self.total_reported = self.end_total
        if self.price:
            if self.currency == 'USD':
                self.usd_total = self.base_total
                self.cup_total = self.base_total * self.price.change_usd_cup
                self.mlc_total = self.base_total * self.price.change_usd_mlc
            elif self.currency == 'CUP':
                self.usd_total = self.base_total / self.price.change_usd_cup
                self.cup_total = self.base_total
                self.mlc_total = self.base_total / self.price.change_usd_cup * self.price.change_usd_mlc
            else:
                self.usd_total = self.base_total / self.price.change_usd_mlc
                self.cup_total = self.base_total / self.price.change_usd_mlc * self.price.change_usd_cup
                self.mlc_total = self.base_total
        super().save(*args, **kwargs)

    @property
    def total_items(self):
        total = decimal.Decimal('0.00')
        order_items = OrderItem.objects.filter(order=self)
        for item in order_items:
            t = item.total
            total = total + decimal.Decimal(t)
        return total
    
    #Revisar esto
    @property
    def total_CUP(self):
        if self.currency == 'USD':
            total = decimal.Decimal('0.00')
            order_items = OrderItem.objects.filter(order=self)
            for item in order_items:
                t = item.total
                total = total + decimal.Decimal(t)
            return total * self.price.change_usd_cup
        else:
            return self.end_total
    
    @property
    def total(self):
        if self.end_total != 0:
            return self.end_total
        else:
            return self.total_items + decimal.Decimal(self.delivery_price) 

    @property
    def statusS(self):
        return self.ORDER_STATUSES[self.status][1]
    
    @property
    def first_name(self):
        return self.user.first_name
    
    def get_absolute_url(self):
        return f"/compra/compras/{self.id}/"
    
    def get_transfer_pay_url(self):
        return f"/compra/transfer/{self.id}/"
    
    def get_paided_url(self):
        return f"/compra/procesado/{self.id}/"
    
    @property
    def paid(self):
        if self.status == self.PAIDED:
            return True
        return False
    
    @property
    def products_list(self):
        order_items = OrderItem.objects.filter(order=self)
        products = []
        for item in order_items:
            product = item.product.name
            count = item.quantity
            count_produc = str(count) + " " + str(product)
            products.append(count_produc)
        return products
    
    @property
    def total_cash(self):
        cash = self.payment_methods.filter(method='CASH').first()
        return cash.amount if cash else 0
    
    #Revisar este método
    @property
    def cash_transactions(self):
        cash = self.payment_methods.filter(method='CASH').first()
        return cash.transaction_count if cash else 0
    
    @property
    def transfer_details(self):
        transfers = self.payment_methods.filter(method='TRANSFER')
        return [{
            'amount': t.amount,
            'details': t.transaction_details
        } for t in transfers]

    # Al crear la orden de compra:
    # Disminuye los disponibles en Productos por Almacen
    # Incrementar la cantidad de reservados en Productos por Almacen
    # Devuelve Falso si en ese almacen algún producto no tiene disponible la cantidad solicitada. 
    def products_reserved(self):
        order_items = OrderItem.objects.filter(order=self)
        st = self.delivery
        all_available = True
        products_Sales = st.products
        if not products_Sales:
            return False
        for item in order_items:
            for prod in products_Sales:
                if item.product == prod.product:
                    prod.reserved = prod.reserved + item.quantity
                    prod.available = prod.available - item.quantity
                    if prod.available < 0:
                        all_available = False
                        break
                    prod.save()               
        return all_available
               
    # Al pagar:
    # Incrementar la cantidad de vendidos sin entregar
    # Disminuye la cantidad de reservados
    # Devuelve falso si los reservados son menos de 0
    def products_sold(self):
        order_items = OrderItem.objects.filter(order=self)
        st = self.delivery
        products_Sales = st.products
        if not products_Sales:
            return False
        all_available = True
        for item in order_items:
           for prod in products_Sales:
               if item.product == prod.product:
                   prod.sold = prod.sold + item.quantity
                   prod.reserved = prod.reserved - item.quantity
                   prod.save()
                   if prod.reserved < 0:
                       all_available = False
                   break
        return all_available

    # Al entregar producto: 
    # Decrementar la cantidad de cantidad de vendidos sin entregar en el almacen.
    # Decreentar la cantidad en Producto
    # Decrementar los reservados en el Producto
    # Devuelve falso si alguno de los valores se hace negativo 
    def products_delivered(self):
        order_items = OrderItem.objects.filter(order=self)
        st = self.delivery
        products_Sales = st.products
        if not products_Sales:
            return False
        all_available = True
        for item in order_items:
            for prod_s in products_Sales:
                if item.product == prod_s.product:
                    prod_s.sold = prod_s.sold - item.quantity
                    prod_s.count = prod_s.count - item.quantity
                    if prod_s.count < 0 or prod_s.sold < 0:
                        all_available = False
                    prod_s.save()
                    break
            prod = item.product
            st.update_prod_count2(prod)
            prod.reserved = prod.reserved - item.quantity
            if prod.reserved < 0:
                all_available = False
            prod.save()
        return all_available
    
    # Al cancelar una orden: 
    # Decrementar la cantidad de reservados en el almacen.
    # Aumenta la cantidad de disponibles en el almacen.
    # Decrementar los reservados en el Producto
    # Devuelve falso si alguno de los valores se hace negativo 
    def order_cancelled(self, preview):
        order_items = OrderItem.objects.filter(order=self)
        st = self.delivery
        products_Sales = st.products
        if not products_Sales:
            return False
        all_available = True
        for item in order_items:
            for prod in products_Sales:
                if item.product == prod.product:
                    if preview == self.PROCESSED or preview == self.SUBMITTED:
                        prod.reserved = prod.reserved - item.quantity
                        prod.available = prod.available + item.quantity
                    elif preview == self.PAIDED:
                        prod.sold = prod.sold - item.quantity
                    elif preview == self.DELIVERED:
                        prod.count = prod.count + item.quantity
                        prod.available = prod.available + item.quantity
                    prod.save()
        return all_available
    
    # Al hacer una devolución de la orden: 
    # Decrementar la cantidad de reservados en el almacen.
    # Aumenta la cantidad de disponibles en el almacen.
    # Decrementar los reservados en el Producto
    # Devuelve falso si alguno de los valores se hace negativo 
    """def order_returned(self):
        self.order_cancelled(self.DELIVERED)
        self.status = self.RETURNED
         order_items = OrderItem.objects.filter(order=self)
        st = self.delivery
        products_Sales = st.products
        all_available = True
        for item in order_items:
            for prod in products_Sales:
                if item.product == prod.product:
                    prod.count = prod.count + item.quantity
                    prod.available = prod.available + item.quantity
                    prod.save()
                    break
            prod = item.product
            st.update_prod_count2(prod)
            prod.save() 
        return all_available"""

    def verify_order_items(self):
        order_items = OrderItem.objects.filter(order=self)
        for item in order_items:
            disp = item.product.count - item.product.reserved
            if item.quantity >= disp:
                return False
        for item in order_items:
            item.product.reserved = item.product.reserved + item.quantity
            item.product.save()
        return True

    def update_status(self, new_status):   
        preview = self.status
        self.status = new_status     
        if new_status == self.SUBMITTED:
            self.products_reserved() 
        elif new_status == self.PROCESSED:
            if not self.verify_order_items():
                self.order_cancelled(preview)
        elif new_status == self.PAIDED:
            self.products_sold()
        elif new_status == self.DELIVERED:
            self.products_delivered()
        elif new_status == self.CANCELLED:
            self.order_cancelled(preview)
        else: 
            return False
        return True

class OrderItem(models.Model):
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL, verbose_name = "Producto")
    quantity = models.DecimalField(max_digits=9, decimal_places=2,default=1.00, verbose_name = "Cantidad")
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name = "Precio")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name = "Orden")
    is_summary_item = models.BooleanField(default=False, verbose_name="Elemento especial de resumen diario ")  # Identificar items especiales
    store_name = models.CharField(max_length=250, default="Envío Habana", verbose_name = "Forma de entrega")
    totalf = models.DecimalField(max_digits=9,decimal_places=2, default=-1.00, verbose_name = "Precio total del producto")

    @property
    def has_discount(self):
        bool = abs((self.price * self.quantity) - self.total) > 0.01
        return abs((self.price * self.quantity) - self.total) > 0.01

    #Revisar...    
    @property
    def total(self):
        #MND = self.order.currency
        try:
            if self.totalf > 0:
                return self.totalf
            if self.quantity >= self.product.min_quantity_whole:
                porciento = decimal.Decimal('0.00')
                porciento = 1-self.product.whole_discount/100
                precio = decimal.Decimal('0.00')
                precio = self.price * decimal.Decimal(porciento)
                return self.quantity * precio
            else:
                return self.quantity * self.price
        except:
            print(self.order.pk)
            return 0

    @property
    def total_base_CUP(self):
        return self.quantity * self.price_CUP

    @property
    def name(self):
        if self.product:
            return self.product.name
        else:
            return ''

    @property
    def price_CUP(self):
        cup_price = 0
        if self.order.currency == 'USD':
            cup_price = self.price * self.order.price.change_usd_cup
        elif self.order.currency == 'MLC':
            cup_price = (self.price / self.order.price.change_usd_mlc) * self.order.price.change_usd_cup
        else:
            cup_price = self.price

        return (cup_price) + 10 - (cup_price % 10) if (cup_price % 10) > 0 else cup_price

    @property
    def sku(self):
        return self.product.sku

    def __unicode__(self):
        return self.product.name + ' (' + self.product.sku + ')'
    
    def get_absolute_url(self):
        return self.product.get_absolute_url()
    
    def update_status(self, status):
        return True
    
class PaymentMethod(models.Model):
    METHOD_CHOICES = [
        ('CASH', 'Efectivo'),
        ('TRANSFER', 'Transferencia'),
        ('CARD', 'Tarjeta'),
    ]
    
    order = models.ForeignKey(Order, related_name='payment_methods', on_delete=models.CASCADE)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, verbose_name="Métodos de pago")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto")
    transaction_count = models.PositiveIntegerField(default=1, verbose_name="Cantidad de transacciones")  # Para contar operaciones
    transaction_details = models.TextField(blank=True, null=True, verbose_name="Detalles")  # Para almacenar múltiples transacciones

    class Meta:
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"

    @property
    def details_json(self):
        try:
            return json.loads(self.transaction_details) if self.transaction_details else {}
        except json.JSONDecodeError:
            return {}
    
    #Validar que coincidan los detalles con el monto
    def validate_amount(self, details, amount):
        sum = 0
        line = details.split('\n')
        for l in line:
            monto = l.split()
            sum = sum + float(monto[1])
        if sum != amount:
            return False
        return True

    def parse_text_details(self, text):
        result = []
        lines = text.strip().split('\n')
        
        if not lines or not any(line.strip() for line in lines):
            raise ValidationError("Debe ingresar al menos una transferencia")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Intentar diferentes formatos
            if ':' in line:
                parts = [p.strip() for p in line.split(':', 1)]
                if len(parts) >= 2:
                    reference = parts[0]
                    # Extraer el monto del segundo segmento
                    amount_str = ''.join(filter(lambda x: x.isdigit() or x in ['.', ','], parts[1]))
                    try:
                        amount = float(amount_str.replace(',', '.'))
                        result.append({'reference': reference, 'amount': amount})
                        continue
                    except ValueError:
                        pass
            
            # Formato: referencia monto
            parts = line.split()
            if len(parts) >= 2:
                try:
                    # El último elemento debería ser el monto
                    amount_str = parts[-1].replace(',', '.')
                    amount = float(amount_str)
                    reference = ' '.join(parts[:-1])
                    result.append({'reference': reference, 'amount': amount})
                    continue
                except ValueError:
                    pass
            
            # Si no coincide con ningún formato
            raise ValidationError(f"Formato inválido en línea: '{line}'")
        
        # Validar que haya al menos una transferencia válida
        if not result:
            raise ValidationError("No se encontraron transferencias válidas")
        
        return result
        
    # Método para guardar datos estructurados
    def set_details(self, details, amount):
        print(f'monto: {amount}')
        if self.validate_amount(details, amount):
            if isinstance(details, dict):
                self.transaction_details = json.dumps(details, ensure_ascii=False)
            elif isinstance(details, str):
                # Intentamos convertir texto a JSON
                try:
                    # Validamos que sea convertible
                    parsed = self.parse_text_details(details)
                    det = json.dumps(parsed, ensure_ascii=False)
                    self.transaction_details = det
                except ValueError as e:
                    raise ValidationError(str(e))
        else:
            print('No coincide el monto con los detalles especificados')
            return False
        return True
        
    
    # Convertir texto plano a estructura JSON
    """ def parse_text_details(self, text):
        result = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Diferentes formatos de entrada
            if ':' in line:
                parts = [p.strip() for p in line.split(':', 1)]
                if len(parts) == 2:
                    result.append({
                        'reference': parts[0],
                        'amount': float(parts[1].replace(',', '.'))
                    })
                    continue
                    
            # Formato: referencia monto
            parts = line.split()
            if len(parts) >= 2:
                try:
                    amount = float(parts[-1].replace(',', '.'))
                    reference = ' '.join(parts[:-1])
                    result.append({
                        'reference': reference,
                        'amount': amount
                    })
                    continue
                except ValueError:
                    pass
                    
            # Si no coincide con ningún formato
            result.append({
                'reference': line,
                'amount': 0.0
            })
        
        return result """

    """ def clean(self):
        if self.method == 'TRANSFER' or self.method == 'CARD':
            if not self.transaction_details:
                raise ValidationError('Debe ingresar detalles para transferencias')
            
            # Validar que haya al menos una transferencia
            details = self.details_json
            if not details or not isinstance(details, list) or len(details) == 0:
                raise ValidationError('Formato de transferencias inválido')
                
            # Validar montos
            for item in details:
                if 'amount' not in item or not isinstance(item['amount'], (int, float)):
                    raise ValidationError('Cada transferencia debe tener un monto numérico') """
                
class Coupon(models.Model):
    code = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Usuario")
    discount_percent = models.PositiveIntegerField(default=10, verbose_name="Descuento (%)")
    expiration_date = models.DateTimeField(default=datetime.datetime.now() + datetime.timedelta(days=30), verbose_name="Expira")
    used = models.BooleanField(default=False, verbose_name="Usado")
    created_at = models.DateTimeField(auto_now_add=True)
    applied_to_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, 
                                         related_name='applied_coupon', verbose_name="Orden a la que se le aplica el cupón")

    def is_valid(self):
        return not self.used and self.expiration_date > datetime.datetime.now()
    
    def __str__(self):
        return str(self.code)
    
class Coupon_first(Coupon):
    related_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, verbose_name="Orden que genera el cupón")
