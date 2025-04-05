from django.urls import path
from .views import crearSolicitudView, GestionSolicitudesView

urlpatterns = [
    path("gestion/", GestionSolicitudesView.as_view(), name='gestion_solicitudes'),
    path('crear/', crearSolicitudView, name='solicitar_servicios'),
]