from django import forms
from .models import Order
import datetime
import re

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
                    'base_total', 'end_total', 'coupon_percent', 'others_discount', 'coupon'
                    )
    def clean_phone(self):
        phone = self.cleaned_data['payment_phone']
        stripped_phone = strip_non_numbers(phone)
        if len(stripped_phone) < 8:
            raise forms.ValidationError('Entre un número de teléfono válido de al menos 8 dígitos. (ejemplo: 5-555-5555)')
        return self.cleaned_data['payment_phone']

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
                     'base_total', 'end_total', 'coupon_percent', 'others_discount', 'coupon')

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
                     'base_total', 'end_total', 'coupon_percent', 'others_discount', 'coupon')

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