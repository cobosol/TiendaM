from django.contrib import admin
from .models import Incentivo, ClienteIncentivo

@admin.register(Incentivo)
class IncentivoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'monto_objetivo', 'umbral_notificacion', 'producto_incentivo', 'activo']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['nombre', 'producto_incentivo__nombre']
    list_editable = ['activo']

@admin.register(ClienteIncentivo)
class ClienteIncentivoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'incentivo', 'monto_actual', 'estado', 'notificado', 'fecha_actualizacion']
    list_filter = ['estado', 'notificado', 'incentivo']
    search_fields = ['cliente__username', 'incentivo__nombre']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']