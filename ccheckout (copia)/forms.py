from django import forms
from django.forms import inlineformset_factory
from .models import Order, PaymentMethod, Coupon
import datetime
import re
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group, User

class DailySummaryForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['seller']  # Solo campo necesario

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Obtener el grupo de vendedores
        vendedores_group = Group.objects.filter(name='vendedores').first()
        
        if vendedores_group:
            # Filtrar usuarios que pertenecen al grupo
            self.fields['seller'].queryset = User.objects.filter(groups=vendedores_group)
        else:
            # Si el grupo no existe, mostrar usuarios vacíos
            self.fields['seller'].queryset = User.objects.none()

        # Hacer el campo requerido
        self.fields['seller'].required = True
        self.fields['seller'].empty_label = "Seleccione un vendedor"

        # Opcional: ordenar por nombre completo
        self.fields['seller'].label_from_instance = lambda obj: f"{obj.get_full_name()} ({obj.username})"

    def clean_seller(self):
        seller = self.cleaned_data.get('seller')
        if not seller:
            raise ValidationError("Debe seleccionar un vendedor")
        return seller

class PaymentMethodForm(forms.ModelForm):
    details_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': 'Ingrese una transferencia por línea:\nEjemplo: TRX-001 150.00\nO: Referencia: TRX-001, Monto: 150.00'
        }),
        required=False,
        label="Detalles de Transferencia"
    )

    class Meta:
        model = PaymentMethod
        fields = ['method', 'amount', 'transaction_count']
        widgets = {
            'method': forms.Select(attrs={'class': 'payment-method-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        
        # Si tenemos una instancia, cargamos los detalles como texto
        if instance and instance.details_json:
            details = instance.details_json
            text_lines = []
            for item in details:
                text_lines.append(f"{item.get('reference', '')}: {item.get('amount', 0)}")
            self.initial['details_text'] = '\n'.join(text_lines)
    
    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('method')
        transaction_count = cleaned_data.get('transaction_count')
        details_text = cleaned_data.get('details_text')
        amount = cleaned_data.get('amount', 0)

        # Validar que se haya seleccionado un método
        if not method:
            raise ValidationError("Debe seleccionar un método de pago")
        

        # Validar que se haya seleccionado la cantidad de transacciones
        if not transaction_count:
            raise ValidationError("Debe especificar la cantidad de transacciones")
        
        # Validar que el monto sea positivo
        if not amount or amount <= 0:
            self.add_error('amount', "El monto debe ser mayor que cero")
        
        # Solo procesar detalles si es transferencia o tarjeta
        if method == 'TRANSFER' or method == 'CARD':
            if not details_text:
                self.add_error('details_text', 'Debe ingresar los detalles de las transferencias')
            else:
                try:
                    parsed = self.instance.parse_text_details(details_text)
                    if not parsed:
                        self.add_error('details_text', "Debe ingresar al menos una transferencia válida")
                    if not self.instance.set_details(details_text, amount):
                        print('Not set_details')
                        self.add_error('details_text', 'Deben coincidir los montos de los detalles con el monto total declarado')
                except ValidationError as e:
                    self.add_error('details_text', str(e))
                # Convertir texto a estructura JSON
                
        
        return cleaned_data

from django.forms import BaseInlineFormSet

class PaymentMethodFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        
        # Verificar que haya al menos un método de pago
        if not any(form.has_changed() for form in self.forms):
            raise ValidationError("Debe agregar al menos un método de pago")
        else:
            print('No hay error en metodo de pago')
        
        # Verificar que todos los métodos tengan datos válidos
        for form in self.forms:
            if form.has_changed() and not form.cleaned_data.get('method'):
                form.add_error('method', "Este campo es obligatorio")
            else:
                print('No hay error en los metodos')

PaymentMethodFormSet = inlineformset_factory(
    Order,
    PaymentMethod,
    form=PaymentMethodForm,
    formset=PaymentMethodFormSet,
    extra=1,
    can_delete=False
)

""" def cc_expire_years():
    current_year = datetime.datetime.now().year
    years = range(current_year, current_year+12)
    return [(str(x),str(x)) for x in years]

def cc_expire_months():
    months = []
    for month in range(1,13):
        if len(str(month)) == 1:
            numeric = '0' + str(month)
        else:
            numeric = str(month)
            months.append((numeric, datetime.date(2009, month, 1).strftime('%B')))
    return months

CARD_TYPES = (('Mastercard','Mastercard'),
              ('VISA','VISA'),
              ('AMEX','AMEX'),
              ('Discover','Discover'),)

 """""" def delivery_names():
    return DeliveryType.objects.all()
    orders_types
    DELIVERY_TYPES = []
    DELIVERY_TYPES.append('MUHIA_E_Guanabacoa','MUHIA_E_Guanabacoa')
    return DELIVERY_TYPES
    for orde in orders_types:
        strs = '(' + orde.name_id() + '),('+ orde.name_id() + ')'
        DELIVERY_TYPES.__add__ = strs
    return DELIVERY_TYPES """

def strip_non_numbers(data):
    """ gets rid of all non-number characters """
    non_numbers = re.compile('\D')
    return non_numbers.sub('', data)

class CheckoutForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CheckoutForm, self).__init__(*args, **kwargs)
        # override default attributes
    """         for field in self.fields:
            self.fields[field].widget.attrs['size'] = '30' """

    class Meta:
        model = Order
        exclude = ('status','ip_address','user','transaction_id',
                   'delivery_price', 'delivery_state', 'pay_url', 'delivery', 'currency', 
                   'store_name', 'base_total', 'end_total', 'coupon_percent', 'others_discount', 'coupon')

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        stripped_phone = strip_non_numbers(phone)
        if len(stripped_phone) < 10:
            raise forms.ValidationError('Entre un número de teléfono válido con el código del área.(ejemplo.555-555-5555)')
        return self.cleaned_data['phone']
    
class FacturarForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FacturarForm, self).__init__(*args, **kwargs)
        # override default attributes
    """         for field in self.fields:
            self.fields[field].widget.attrs['size'] = '30' """

    class Meta:
        model = Order
        fields = ['payment_name', 'payment_phone', 'payment_email', 'payment_address', 'payment_details']
        widgets = {
            'payment_address': forms.Textarea(attrs={'width':'300px', 'rows':3}),
            'payment_details': forms.Textarea(attrs={'width':'600px', 'rows':4}),
        }

    def clean_phone(self):
        phone = self.cleaned_data['payment_phone']
        stripped_phone = strip_non_numbers(phone)
        if len(stripped_phone) < 10:
            raise forms.ValidationError('Entre un número de teléfono válido con el código del área.(ejemplo.555-555-5555)')
        return self.cleaned_data['payment_phone']
    
class CachForm(forms.ModelForm):

    class Meta:
        model = Order
        fields = ['payment_name', 'payment_phone', 'payment_email']

    def __init__(self, *args, **kwargs):
        super(CachForm, self).__init__(*args, **kwargs)
        # override default attributes
        for field in self.fields:
            self.fields[field].widget.attrs['size'] = '30'
        self.fields['payment_name'].required = True

    def clean_phone(self):
        phone = self.cleaned_data['payment_phone']
        stripped_phone = strip_non_numbers(phone)
        if len(stripped_phone) < 8:
            raise forms.ValidationError('Entre un número de teléfono válido de 8 dígitos.(ejemplo: 55 55 5555)')
        return self.cleaned_data['payment_phone']

class PagarForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PagarForm, self).__init__(*args, **kwargs)
        # override default attributes
        """ for field in self.fields:
            self.fields[field].widget.attrs['size'] = '30' """

    class Meta:
        model = Order
        exclude = ('status','ip_address','user','transaction_id','delivery_price', 'pay_url', 'delivery',
                    'store_name', 'payment_city', 'delivery_state', 'currency', 'payment_postCode',
                    'base_total', 'end_total', 'coupon_percent', 'others_discount', 'coupon', 'usd_total',
                      'cup_total', 'mlc_total', 'total_reported' 
                    )
    def clean_phone(self):
        phone = self.cleaned_data['payment_phone']
        stripped_phone = strip_non_numbers(phone)
        if len(stripped_phone) < 8:
            raise forms.ValidationError('Entre un número de teléfono válido de al menos 8 dígitos. (ejemplo: 5-555-5555)')
        return self.cleaned_data['payment_phone']
    
    def clean_wallet_discount(self):
        wallet_discount = self.cleaned_data['wallet_discount']
        return self.cleaned_data['wallet_discount']

class ReserveForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ReserveForm, self).__init__(*args, **kwargs)
        # override default attributes
        """ for field in self.fields:
            self.fields[field].widget.attrs['size'] = '30' """
        self.fields['payment_name'].required = True
        self.fields['payment_phone'].required = True
        self.fields['delivery_name'].required = True
        self.fields['delivery_ci'].required = True
        self.fields['delivery_phone'].required = True
        self.fields['delivery_street'].required = True
        self.fields['delivery_apto'].required = True
    
    class Meta:
        model = Order
        exclude = ('status','ip_address','user','transaction_id','delivery_price', 'pay_url', 'delivery', 'store_name', 'payment_city', 
                   'delivery_state', 'currency', 'payment_postCode',
                     'base_total', 'end_total', 'coupon_percent', 'others_discount', 'coupon', 'usd_total',
                      'cup_total', 'mlc_total', 'total_reported')

    def clean_phone(self):
        phone = self.cleaned_data['payment_phone']
        stripped_phone = strip_non_numbers(phone)
        if len(stripped_phone) < 10:
            raise forms.ValidationError('Entre un número de teléfono válido con el código del área. (ejemplo.555-555-5555)')
        return self.cleaned_data['payment_phone']

class ReserveEForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ReserveEForm, self).__init__(*args, **kwargs)
        self.fields['payment_name'].required = True
        self.fields['payment_phone'].required = True
        self.fields['delivery_name'].required = True
        self.fields['delivery_ci'].required = True
        self.fields['delivery_phone'].required = True
        self.fields['delivery_substate'].required = False
    
    class Meta:
        model = Order
        exclude = ('status','ip_address','user','transaction_id','delivery_price', 'pay_url', 'delivery', 'store_name', 'payment_city', 
                   'delivery_state', 'currency', 'payment_postCode', 'delivery_street', 'delivery_apto',
                     'base_total', 'end_total', 'coupon_percent', 'others_discount', 'coupon', 'usd_total',
                      'cup_total', 'mlc_total', 'total_reported')

    def clean_phone(self):
        phone = self.cleaned_data['payment_phone']
        stripped_phone = strip_non_numbers(phone)
        if len(stripped_phone) < 10:
            raise forms.ValidationError('Entre un número de teléfono válido con el código del área. (ejemplo.555-555-5555)')
        return self.cleaned_data['payment_phone']
    
    
class UpdateStatusForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UpdateStatusForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Order
        fields = ['status']

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = '__all__'
        """ widgets = {
            'nombre': forms.TextInput(attrs={
                'size': '50'
            }),
            'creditos': forms.NumberInput(attrs={
                'size': 2,
                'style': 'width: 80px'
            }),
        } """