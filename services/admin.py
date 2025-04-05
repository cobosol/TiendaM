from django.contrib import admin
from .models import Servicio, Solicitud


class ServicioAdmin(admin.ModelAdmin):
    list_display=('nombre', 'descripcion_corta')

    def descripcion_corta(self, obj):
        return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion

class SolicitudAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'carnet', 'fecha_solicitud')
    #filter_horizontal = ('servicio',)

admin.site.register(Servicio, ServicioAdmin)
admin.site.register(Solicitud, SolicitudAdmin) 