from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

@shared_task
def monthly_wallet_refill():
    last_month = timezone.now() - timedelta(days=30)
    users = User.objects.annotate(
        total_spent=Sum('order__total_amount', 
                        filter=models.Q(order__created_at__gte=last_month))
    )
    
    for user in users:
        if user.total_spent and user.total_spent >= 1000:  # Ejemplo: 1000 USD
            bonus = user.total_spent * 0.10  # 10% de bonificación
            wallet = user.wallet
            wallet.balance += bonus
            wallet.save()
            # Opcional: Registrar transacción
            Transaction.objects.create(
                wallet=wallet,
                amount=bonus,
                description="Bonificación mensual por compras"
            )