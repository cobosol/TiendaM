from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_coupon(user, coupon):
    # Envío por email
    subject = f"Tu cupón de descuento - {settings.SITE_NAME}"
    message = render_to_string('emails/coupon_email.html', {
        'user': user,
        'coupon': coupon,
        'site_url': settings.SITE_URL
    })
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=message,
        fail_silently=False
    )
    
    # Alternativa: Generar PDF y permitir descarga
    # Implementar generación de PDF aquí y guardar en servidor/CDN
    # Enviar enlace de descarga por email o mensaje interno