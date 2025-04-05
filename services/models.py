from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Servicio(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre
    
class Solicitud(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Usuario')
    telefono = models.CharField(max_length=10, null='True', verbose_name='Teléfono (Con WhatsApp)')
    correo = models.CharField(max_length=50, null='True', verbose_name='Correo electrónico')
    carnet = models.CharField(max_length=11)
    servicio = models.ForeignKey(Servicio, null=True, on_delete=models.CASCADE)
    fecha_solicitud = models.DateField(auto_now_add=True)
    estados = [('pendiente', 'Pendiente'), ('aprobado', 'Aprobado'), ('rechazado', 'Rechazado'), ('encurso', 'En curso'), ('pagado', 'Pagado'), ('recibido', 'Recibido')]
    estado = models.CharField(max_length=20, default='pendiente', choices=estados)

    class Meta:
        ordering = ['-fecha_solicitud']
        verbose_name_plural = 'Solicitudes de servicios'


    def __str__(self):
        return f"Solicitud de {self.usuario} - {self.servicio}"