from django.db import models
from registration.models import Profile
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from catalog.models import Product
import math

class Notification(models.Model):
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='notification')
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # Campos adicionales (opcional)
    link = models.URLField(blank=True, null=True) 

    def __str__(self):
        return self.message

class Incentivo(models.Model):
    nombre = models.CharField(max_length=200, help_text="Nombre descriptivo del incentivo")
    monto_objetivo = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Monto que el cliente debe alcanzar para obtener el incentivo"
    )
    producto_incentivo = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name="incentivos",
        help_text="Producto a otorgar como incentivo"
    )
    umbral_notificacion = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Monto a partir del cual se notifica al cliente sobre el incentivo cercano"
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Incentivo"
        verbose_name_plural = "Incentivos"
        ordering = ['monto_objetivo']
    
    def __str__(self):
        return f"{self.nombre} - ${self.monto_objetivo}"

class ClienteIncentivo(models.Model):
    ESTADO_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('notificado', 'Notificado'),
        ('completado', 'Completado'),
        ('expirado', 'Expirado'),
        ('entregado', 'Entregado'),
    )
    
    cliente = models.ForeignKey(User, on_delete=models.CASCADE)
    incentivo = models.ForeignKey(Incentivo, on_delete=models.CASCADE)
    monto_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notificado = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['cliente', 'incentivo']
        verbose_name = "Incentivo de Cliente"
        verbose_name_plural = "Incentivos de Clientes"
    
    def __str__(self):
        return f"{self.cliente.username} - {self.incentivo.nombre}"
    
    def actualizar_progreso(self, monto_gastado):
        # Solo actualizar si el incentivo está activo y no completado
        if self.estado in ['pendiente', 'notificado'] and self.incentivo.activo:
            self.monto_actual = monto_gastado
            
            # Verificar si alcanzó el umbral de notificación
            if not self.notificado and self.monto_actual >= self.incentivo.umbral_notificacion:
                self.notificado = True
                self.estado = 'notificado'
                
            
            # Verificar si alcanzó el objetivo
            if self.monto_actual >= self.incentivo.monto_objetivo:
                self.estado = 'completado'
            
            self.save()
    
    def puede_reclamar(self):
        return (self.estado == 'notificado' and 
                self.monto_actual >= self.incentivo.umbral_notificacion and
                self.monto_actual < self.incentivo.monto_objetivo)
    
    @property
    def porcentaje_completado(self):
        if self.incentivo.monto_objetivo == 0:
            return 0
        porcentaje = (self.monto_actual / self.incentivo.monto_objetivo) * 100
        return min(100, math.floor(porcentaje))