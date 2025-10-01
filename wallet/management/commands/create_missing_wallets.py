from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from wallet.models import Wallet


class Command(BaseCommand):
    help = 'Crea wallets para todos los usuarios que no tengan uno'

    def handle(self, *args, **options):
        User = get_user_model()
        users_without_wallet = User.objects.filter(wallet__isnull=True)
        
        count = 0
        for user in users_without_wallet:
            Wallet.objects.create(user=user)
            count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Se crearon {count} wallets para usuarios existentes')
        )