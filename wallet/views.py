from django.shortcuts import render
from .models import Wallet, Transaction

# Create your views here.
def transactions(request):
    tr = Transaction.objects.all().order_by('-created_at')
    return render(request, "wallet/transactions.html", {'transactions':tr})