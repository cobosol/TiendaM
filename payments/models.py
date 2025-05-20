from django.db import models
from django.contrib.auth import get_user_model
import uuid
import datetime
from django.contrib.auth.models import User
from ccheckout.models import Order


class Coupon(models.Model):
    code = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    discount_percent = models.PositiveIntegerField(default=10)
    expiration_date = models.DateTimeField(default=datetime.datetime.now() + datetime.timedelta(days=30))
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    applied_to_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, 
                                         related_name='applied_coupon', verbose_name="Orden a la que se le aplica el cupón")

    def is_valid(self):
        return not self.used and self.expiration_date > datetime.datetime.now()
    
    def __str__(self):
        return str(self.code)
    
class Coupon_first(Coupon):
    related_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, verbose_name="Orden que genera el cupón")

