#from celery import shared_task
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Coupon, User, Coupon_first
from tienda import settings

#@shared_task(bind=True, max_retries=3)
def send_coupon_task(user_id, coupon_id):
    user = User.objects.get(id=user_id)
    coupon = Coupon_first.objects.get(pk=coupon_id)
    context = {
        'user': user,
        'coupon': coupon,
        'site_url': settings.SITE_URL,
        'support_email': settings.SUPPORT_EMAIL 
    }

    html_context = render_to_string('emails/first_purchase_coupon.html', context)

    text_context = strip_tags(html_context)

    
    send_mail(
            subject=f'Cupón generado: Gracias por entrar a la familia MUHIA',
            message=text_context, #f'Tienes un nuevo cupón: {coupon.code} con descuento de {coupon.discount_percent}%. Es válido hasta {coupon.expiration_date}',
            from_email='muhia@produccionesmuhia.ca',
            recipient_list=[user.email],
            fail_silently=False
        )
