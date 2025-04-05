from django.forms.models import BaseModelForm
from django.http import HttpResponseRedirect
from django.views.generic.edit import CreateView
from django.views.generic import ListView
from django.urls import reverse
from django.db.models import Count
from django.contrib.auth.models import User
from .models import Solicitud, Servicio
from .forms import SolicitudForm 
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models.functions import TruncDay
import json

# Create your views here.
def crearSolicitudView(request):
    if not (request.user.is_authenticated):
        messages.warning(request, "Debe estar autenticado para acceder a este servicio")
        url = reverse('login')
        return HttpResponseRedirect(url)
    if request.method == 'POST':
        form = SolicitudForm(request.POST)
        if form.is_valid():
            Solicitud.objects.filter(usuario=request.user).delete()

            for servicio in form.cleaned_data['home']:
                Solicitud.objects.create(
                    usuario = request.user,
                    servicio = servicio
                )
            return redirect('home')
    else:
        form = SolicitudForm()
    return render(request, 'servicio/solicitar.html', {'form':form})


    """ model = Solicitud
    form_class = SolicitudForm
    success_url = reverse_lazy('home')
    login_url = reverse_lazy('login')
    success_message = "Se ha registrado correctamente su solicitud."
    permission_denied_message = "debes iniciar sesión para acceder a esta página."
    redirect_field_name = 'next'

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        messages.success(self.request, self.success_message)
        return super().form_valid(form)
    
    def handle_no_permission(self):
        messages.warning(self.request, self.permission_denied_message)
        return super().handle_no_permission() """

class GestionSolicitudesView(LoginRequiredMixin, ListView):
    model = Solicitud
    template_name = 'servicio/gestion.html'
    context_object_name = 'solicitudes'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()

        if usuario := self.request.GET.get('usuario'):
            queryset = queryset.filter(usuario__username__icontains=usuario)
        if servicio := self.request.GET.get('servicio'):
            queryset = queryset.filter(servicio__nombre__icontains=servicio)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        servicios_stats = Solicitud.objects.values('servicio__nombre').annotate(total=Count('servicio'))
        estados_stats = Solicitud.objects.values('estado').annotate(total=Count('estado'))

        """ context['servicios_data'] = json.dumps({
            'labels': [item['servicio__nombre'] for item in servicios_stats],
            'data': [item['total'] for item in servicios_stats]
        }) """

        context['servicios_data'] = {
            'labels': [item['servicio__nombre'] for item in servicios_stats],
            'data': [item['total'] for item in servicios_stats]
        }

        servicios = Servicio.objects.all()
        usuarios = User.objects.filter(
            solicitud__isnull=False
        ).distinct()

        context['usuarios'] = usuarios

        context['servicios'] = servicios

        context['estados_data'] = {
            'labels': [item['estado'] for item in estados_stats],
            'data': [item['total'] for item in estados_stats]
        }

        return context
    


""" def analiticas_servicios(request):
    usuarios = User.objects.all()
    servicios = Servicio.objects.all()

    usuario_id = request.GET.get('usuario')
    servicio_id = request.GET.get('servicio')
    #orden = request.GET.get('orden', '-fecha_creacion')

    solicitudes = Solicitud.objects.all()

    if usuario_id:
        solicitudes = solicitudes.filter(usuario=usuario_id)
    if servicio_id:
        solicitudes = solicitudes.filter(servicios=servicio_id)

    #solicitudes = solicitudes.order_by(orden)

    total_solicitudes = solicitudes.count()

    solicitudes_por_servicio = solicitudes.values('servicios__nombre').annotate(total=Count('id'))

    #Gráfico de ultimos 7 días
    from django.db.models.functions import TruncDay
    solicitudes_por_dia = solicitudes.filter(
        fecha_solicitud__gte=timezone.now()- timezone.timedelta(days=7)
    ).annotate(
        dia=TruncDay('fecha_solicitud')
    ).values('dia').annotate(total=Count('id')).order_by('dia')

    context = {
        'usuarios': usuarios,
        'servicios': servicios,
        'solicitudes': solicitudes,
        'total_solicitudes': total_solicitudes,
        'solicitudes_por_servicio': list(solicitudes_por_servicio),
        'solicitudes_por_dia': list(solicitudes_por_dia),
    }
    return render(request, 'servicio/analiticas_servicios.html', context) """

