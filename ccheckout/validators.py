from django import forms
from .models import Coupon
from django.utils import timezone
from django.contrib import messages

class CouponValidator:
    @staticmethod
    def validate(coupon_code, user):
        print("En el validate coupon")
        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.user != user:
                raise forms.ValidationError("Cupón no válido para este usuario")
            if coupon.used:
                raise forms.ValidationError("Este cupón ya fue utilizado")
            if coupon.expiration_date < timezone.now():
                raise forms.ValidationError("Cupón expirado")
            return coupon
        except Coupon.DoesNotExist:
            raise forms.ValidationError("Cupón no válido")