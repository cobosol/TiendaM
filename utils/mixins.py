# mixins.py
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect

class ComercialGroupRequiredMixin(UserPassesTestMixin):
    """Mixin que permite acceso solo a usuarios del grupo 'comerciales'."""
    
    def test_func(self):
        return self.request.user.groups.filter(name='comercial').exists()
    
    def handle_no_permission(self):
        # Redirige a una página de error o al login
        return redirect('home')  # Cambia por tu URL