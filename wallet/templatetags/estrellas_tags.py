from django import template
from django.contrib.auth.models import User
from registration.models import Profile

register = template.Library()

@register.simple_tag
def mostrar_estrellas(usuario):
    try:
        cliente = Profile.objects.get(user=usuario)
        return '★' * cliente.estrellas + '☆' * (5 - cliente.estrellas)
    except Profile.DoesNotExist:
        return '☆' * 5