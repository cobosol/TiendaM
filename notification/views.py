from django.shortcuts import render, get_object_or_404
from.models import Notification
import requests
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import ClienteIncentivo, Incentivo

# Create your views here.
@login_required
def unread_notifications(request):
    notifications = Notification.objects.filter(
        user=request.user.profile, 
        read=False
    ).order_by('-created_at').values('id', 'message', 'created_at', 'link')[:20]
    
    # Formatear fecha
    for notif in notifications:
        notif['created_at'] = notif['created_at'].strftime("%d/%m/%Y %H:%M")
    
    return JsonResponse(list(notifications), safe=False)

@login_required
@csrf_exempt
def mark_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user.profile)
        notification.read = True
        notification.save()
        return JsonResponse({"status": "success"})
    except Notification.DoesNotExist:
        return JsonResponse({"status": "error"}, status=404)

@login_required
@csrf_exempt
def mark_all_read(request):
    Notification.objects.filter(user=request.user, read=False).update(read=True)
    return JsonResponse({"status": "success"})

@login_required
def mis_incentivos(request):
    """Vista para mostrar los incentivos del cliente actual"""
    incentivos = ClienteIncentivo.objects.filter(cliente=request.user)
    
    # Obtener incentivos disponibles que el cliente aún no tiene
    incentivos_disponibles = Incentivo.objects.filter(activo=True).exclude(
        id__in=incentivos.values_list('incentivo_id', flat=True)
    )
    
    context = {
        'incentivos': incentivos,
        'incentivos_disponibles': incentivos_disponibles,
    }
    return render(request, 'notification/mis_incentivos.html', context)

@login_required
@require_POST
def reclamar_incentivo(request, incentivo_id):
    """Vista para reclamar un incentivo"""
    cliente_incentivo = get_object_or_404(
        ClienteIncentivo, 
        cliente=request.user, 
        incentivo_id=incentivo_id,
        estado='notificado'
    )
    
    if cliente_incentivo.puede_reclamar():
        # Aquí iría la lógica para agregar el producto al carrito
        # Por ahora, solo marcamos como completado
        cliente_incentivo.estado = 'completado'
        cliente_incentivo.save()
        
        return JsonResponse({
            'success': True,
            'message': f'¡Felicidades! Has reclamado tu {cliente_incentivo.incentivo.producto_incentivo.nombre}'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'No puedes reclamar este incentivo en este momento'
    })