from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ccheckout.models import Order

class Command(BaseCommand):
    help = 'Asigna 0 a todos los consecutivos'

    def handle(self, *args, **options):
        orders = Order.objects.all()
        
        count = 0
        for o in orders:
            o.save()
            count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Se actualizaron {count} órdenes existentes')
        )