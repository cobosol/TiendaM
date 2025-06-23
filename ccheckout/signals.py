from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Coupon, Coupon_first
from ccheckout.models import Order
from django.conf import settings
from .utils import send_coupon
import datetime

@receiver(post_save, sender=Order)
def generate_first_purchase_coupon(sender, instance, created, **kwargs):
    print("En el signals")
    print(instance.id)
    print(instance.status)
    print(instance.PAIDED)
    if instance.status == instance.PROCESSED:
        print("En procesada")
        user = instance.user
        # Verificar si es la primera compra exitosa
        if Order.objects.filter(user=user, status__in = [instance.PAIDED, instance.PROCESSED]).count() == 1:
            print("Primera orden")
            # Crear cupón
            coupon = Coupon_first.objects.create(
                user=user,
                discount_percent=settings.FIRST_PURCHASE_DISCOUNT,  # Agregar a settings: FIRST_PURCHASE_DISCOUNT = 10
                expiration_date=datetime.datetime.now() + datetime.timedelta(days=settings.COUPON_EXPIRATION_DAYS),  # COUPON_EXPIRATION_DAYS = 30
                related_order=instance
            )
            
            # Enviar cupón de forma asincrónica
            from .tasks import send_coupon_task
            send_coupon_task(user.id, coupon.pk)