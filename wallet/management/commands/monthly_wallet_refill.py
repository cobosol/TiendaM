from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Q
from django.contrib.auth import get_user_model
from wallet.models import Wallet, Transaction
from ccheckout.models import Order
import logging
import decimal

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Realiza la recarga mensual de los monederos basado en compras'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--threshold1',
            type=float,
            default=3000.0,
            help='Umbral mínimo de compras para recibir bonificación de 1 estrella'
        )
        parser.add_argument(
            '--percentage1',
            type=float,
            default=2.0,
            help='Porcentaje de bonificación para 1 estrella: 2%%)'
        )
        parser.add_argument(
            '--threshold2',
            type=float,
            default=5000.0,
            help='Umbral mínimo de compras para recibir bonificación de 2 estrellas'
        )
        parser.add_argument(
            '--percentage2',
            type=float,
            default=3.0,
            help='Porcentaje de bonificación para 2 estrellas: 3%%)'
        )
        parser.add_argument(
            '--threshold3',
            type=float,
            default=30000.0,
            help='Umbral mínimo de compras para recibir bonificación de 3 estrellas'
        )
        parser.add_argument(
            '--percentage3',
            type=float,
            default=4.0,
            help='Porcentaje de bonificación para 3 estrellas: 4%%)'
        )
        parser.add_argument(
            '--threshold4',
            type=float,
            default=100000.0,
            help='Umbral mínimo de compras para recibir bonificación de 4 estrellas'
        )
        parser.add_argument(
            '--percentage4',
            type=float,
            default=5.0,
            help='Porcentaje de bonificación para 4 estrellas: 5%%)'
        )
        parser.add_argument(
            '--threshold5',
            type=float,
            default=500000.0,
            help='Umbral mínimo de compras para recibir bonificación de 5 estrellas'
        )
        parser.add_argument(
            '--percentage5',
            type=float,
            default=10.0,
            help='Porcentaje de bonificación para 5 estrellas: 10%%)'
        )

    def handle(self, *args, **options):
        threshold1 = options['threshold1']
        threshold2 = options['threshold2']
        threshold3 = options['threshold3']
        threshold4 = options['threshold4']
        threshold5 = options['threshold5']
        percentage1 = options['percentage1'] / 100.0
        percentage2 = options['percentage2'] / 100.0
        percentage3 = options['percentage3'] / 100.0
        percentage4 = options['percentage4'] / 100.0
        percentage5 = options['percentage5'] / 100.0
        
        percentage = 0.0

        cambio_Oficial = 120

        User = get_user_model()
        today = timezone.now()
        first = today.replace(day=1)
        last_month = first - timedelta(days=1)
        last_month_first = last_month.replace(day=1)

        
        # Aplicar una vez para llenar el atributo cup_oficial
        """ orders = Order.objects.all()
        for o in orders:
            o.save() """

        # Obtener usuarios con compras en el mes
        users = User.objects.annotate(
            total_spent=Sum('order__cup_oficial', 
                           filter=Q(order__date__gte=last_month_first, order__status__in=[2, 3, 5, 7]))
        ).exclude(total_spent=None) #, order__date__lte=last_month
        
        count = 0
        for user in users:
            estrella = False
            if user.groups.filter(name__in=['comercial']):
                pass
            if user.total_spent >= threshold5:
                estrella = True
                bonus = user.total_spent * decimal.Decimal(percentage5)
                user.profile.estrellas = 5
                percentage = percentage5
            elif user.total_spent >= threshold4:
                estrella = True
                bonus = user.total_spent * decimal.Decimal(percentage4)
                user.profile.estrellas = 4
                percentage = percentage4
            elif user.total_spent >= threshold3:
                estrella = True
                bonus = user.total_spent * decimal.Decimal(percentage3)
                user.profile.estrellas = 3
                percentage = percentage3
            elif user.total_spent >= threshold2:
                estrella = True
                bonus = user.total_spent * decimal.Decimal(percentage2)
                user.profile.estrellas = 2
                percentage = percentage2
            elif user.total_spent >= threshold1:
                estrella = True
                bonus = user.total_spent * decimal.Decimal(percentage1)
                user.profile.estrellas = 1
                percentage = percentage1

            if estrella: 
                try:
                    user.profile.save()
                    wallet = Wallet.objects.get(user=user)
                    wallet.balance += bonus
                    wallet.save()
                    
                    Transaction.objects.create(
                        wallet=wallet,
                        amount=bonus,
                        description=f"Bonificación mensual ({percentage*100}%) por compras de ${user.total_spent}"
                    )
                    
                    count += 1
                    logger.info(f"Bonificación de ${bonus} aplicada al usuario {user.id}")
                    
                except Exception as e:
                    logger.error(f"Error procesando usuario {user.id}: {str(e)}")
                    continue
        
        self.stdout.write(
            self.style.SUCCESS(f'Bonificación aplicada a {count} usuarios')
        )