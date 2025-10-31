from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Coupon, Coupon_first
from django.conf import settings
from .utils import send_coupon
import datetime

from django.contrib.auth.models import Group
from notification.models import Notification
from .models import Order, OrderItem
#from utils.tasks import send_notification_email

from django.db.models import Sum
from django.utils import timezone
from notification.models import Incentivo, ClienteIncentivo
from django.contrib import messages

@receiver(post_save, sender=Order)
def actualizar_incentivos_cliente(sender, instance, **kwargs):
    gcomerciales = Group.objects.filter(name='comercial').first()
    comerciales = []
    if gcomerciales:
        comerciales = gcomerciales.user_set.all()
    if not instance.user in comerciales:
        if instance.status == 2 or instance.status == 5:  # Solo procesar órdenes pagadas o entregadas
            # Obtener el primer día del mes actual
            primer_dia_mes = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
            # Calcular el monto gastado por el cliente en el mes actual
            monto_mensual = Order.objects.filter(
                user=instance.user,
                date__gte=primer_dia_mes,
                status__in=[2,5]
            ).aggregate(total=Sum('cup_oficial'))['total'] or 0

        
            # Obtener todos los incentivos activos
            incentivos_activos = Incentivo.objects.filter(activo=True).order_by('-monto_objetivo')

            incentivado = False
        
            for incentivo in incentivos_activos:
                # Crear u obtener el registro de incentivo del cliente
                if monto_mensual >= incentivo.umbral_notificacion and not incentivado:
                    cliente_incentivo, created = ClienteIncentivo.objects.get_or_create(
                        cliente=instance.user,
                        incentivo=incentivo
                    )
                    Notification.objects.create(
                        user=instance.user.profile,
                        message=f"Ha recibido una oferta especial. No deje de consultarla",
                        link=f'/notification/mis-incentivos/'  # Ir a página para realizar la entrada al almacén.  
                    )
                    # Actualizar el progreso del incentivo
                    cliente_incentivo.actualizar_progreso(monto_mensual)
                    if cliente_incentivo.estado == 'completado':
                        oi = OrderItem()
                        oi.order = instance
                        oi.product = incentivo.producto_incentivo
                        oi.quantity = 1
                        oi.price = 0.00
                        oi.save()
                        cliente_incentivo.estado = 'entregado'
                        cliente_incentivo.save()
                    incentivado = True
    
""" @receiver(post_save, sender=Order)
def notify_stars(sender, instance, created, **kwargs):
    if instance.:  
        target_groups = Group.objects.filter(name__in=["almaceneros", "direccion"])
        # Crear notificaciones para cada usuario en esos grupos
        for group in target_groups:
            for user in group.customuser_set.all():
                # Notificación en base de datos
                Notification.objects.create(
                    user=user,
                    message=f"Nueva adquisición recibida: {instance}",
                    link=f'/movimientos/recepcion/{instance.tipo_adquisicion}/{instance.id}/'  # Ir a página para realizar la entrada al almacén.  
                ) """

""" @receiver(post_save, sender=Order)
def generate_first_purchase_coupon(sender, instance, created, **kwargs):
    if instance.status == instance.PROCESSED:
        user = instance.user
        # Verificar si es la primera compra exitosa
        if Order.objects.filter(user=user, status__in = [instance.PAIDED, instance.PROCESSED]).count() == 1:
            # Crear cupón
            coupon = Coupon_first.objects.create(
                user=user,
                discount_percent=settings.FIRST_PURCHASE_DISCOUNT,  # Agregar a settings: FIRST_PURCHASE_DISCOUNT = 10
                expiration_date=datetime.datetime.now() + datetime.timedelta(days=settings.COUPON_EXPIRATION_DAYS),  # COUPON_EXPIRATION_DAYS = 30
                related_order=instance
            )
            
            # Enviar cupón de forma asincrónica
            from .tasks import send_coupon_task
            send_coupon_task(user.id, coupon.pk) """
