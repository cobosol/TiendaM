from django.db import models
from django.contrib.auth.models import User, Group 
from django.dispatch import receiver
from django.db.models.signals import post_save
from stores.models import Store

def custom_upload_to(instance, filename):
    old_instance = Profile.objects.get(pk=instance.pk)
    old_instance.avatar.delete()
    return 'profiles/' + filename
    
class Profile(models.Model):
    # Tipo de cliente
    COMPRADOR = 0
    COMPRA_VENTA = 1
    DISTRIBUIDOR = 2
    CONSIGNACION = 3

    CLIENT_TYPE = ((COMPRADOR,'Comprador eventual'),
                   (COMPRA_VENTA,'Comprador con contrato'),
                   (DISTRIBUIDOR,'Distribuidor'),
                   (CONSIGNACION, 'Consignación'),
                   )

    # Moneda preferida
    USD = 0
    CUP = 1
    MLC = 2

    MONEY_TYPE = ((USD,'USD'),
                   (CUP,'CUP'),
                   (MLC,'MLC'),
                   )
    
    user = models.OneToOneField(User, on_delete = models.CASCADE, verbose_name = "Usuario")
    cid = models.CharField(max_length=20, verbose_name = "Número de identidad")
    avatar = models.ImageField(upload_to='profiles', null=True, blank=True, verbose_name = "Foto")
    bio = models.TextField(null=True, blank=True, verbose_name = "Biografía")
    client_type = models.IntegerField(choices=CLIENT_TYPE, default=COMPRADOR, help_text='Puede cambiarlo cuando desee en su perfil', verbose_name = "Tipo de cliente")
    money_type = models.IntegerField(choices=MONEY_TYPE, default=USD, help_text='En cualquier momento puede cambiarla', verbose_name = "Tipo de moneda")
    link = models.URLField(max_length=200, null=True, blank=True, verbose_name = "Enlace")
    phone = models.CharField(max_length=15, null=True, blank = True,
                            help_text='', 
                            verbose_name = "Número de móvil")
    ws = models.CharField(max_length=15, null=True, blank = True, verbose_name = "Número para WhatsApp")
    
    # Special User
    reeup = models.CharField(max_length=20, unique=True, null=True, blank = True,
                            help_text='', 
                            verbose_name = "Código REEUP")
    nit = models.CharField(max_length=20, unique=True, null=True, blank = True,
                            help_text='', 
                            verbose_name = "Código NIT")
    address = models.CharField(max_length=100, null=True, blank = True, 
                            verbose_name = "Dirección oficial")
    agency = models.CharField(max_length=100, null=True, blank = True, 
                            verbose_name = "Agencia bancaria")
    contract = models.CharField(max_length=50, null=True, blank = True, 
                            verbose_name = "Número de contrato")
    prefered_store = models.ForeignKey(Store, on_delete = models.SET_NULL, null=True, blank = True, 
                            verbose_name = "Forma de entrega preferida")
    estrellas = models.IntegerField(default=0)
    fecha_actualizacion_estrellas = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['user']
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

    def __str__(self):
        return f'{self.user.first_name} - {self.estrellas} estrellas'

    @property
    def name(self):
        return self.user.first_name + ' ' + self.user.last_name
    
    @property
    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url 
        else:
            return "/static/img/Profile/pensativo.jpg"

@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance, **kwargs):
    if kwargs.get('created', False):
        Profile.objects.get_or_create(user=instance)
