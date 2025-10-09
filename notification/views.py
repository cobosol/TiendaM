from django.shortcuts import render, redirect, get_object_or_404
from.models import Notification
import requests
from django.urls import reverse, reverse_lazy
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import Notification, Incentivo
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import ClienteIncentivo, Incentivo
from utils.mixins import ComercialGroupRequiredMixin
from django.shortcuts import render,  get_object_or_404
from django.http import HttpResponse, Http404, JsonResponse
from django.views.generic import CreateView, UpdateView, ListView, DeleteView

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
    Notification.objects.filter(user=request.user.profile, read=False).update(read=True)
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

""" Gestión de incentivos """
@method_decorator(login_required, name='dispatch')    
class Gestion_incentivos(ComercialGroupRequiredMixin, ListView):
    model = Incentivo
    template_name = 'notification/incentivos/incentivos_list.html'
    context_object_name = 'incentivos'

@method_decorator(login_required, name='dispatch')
class Crear_incentivos(ComercialGroupRequiredMixin, CreateView):
    model = Incentivo
    fields = '__all__'
    success_message = "Se ha creado correctamente el incentivo."

    def get_success_url(self):
        return reverse_lazy('incentivos')
    
@method_decorator(login_required, name='dispatch')
class Update_incentivos(ComercialGroupRequiredMixin, UpdateView):
    model = Incentivo
    fields = '__all__'
    success_message = "Se ha actualizado correctamente el incentivo."

    def get_success_url(self):
        return reverse('incentivos')

def eliminar_incentivo(request, pk):
    incentivo = get_object_or_404(Incentivo, pk=pk)
    incentivo.activo = False
    incentivo.save()

    return redirect('incentivos')