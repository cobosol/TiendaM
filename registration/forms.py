from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.forms import PasswordResetForm
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from tienda.settings import EMAIL_HOST_USER

class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Tu correo electrónico'
        })

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Envía un correo multipart (texto y html) para restablecer contraseña
        """
        subject = render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())  # Elimina saltos de línea
        body = render_to_string(email_template_name, context)
        email = EmailMultiAlternatives(
            subject,
            body,
            EMAIL_HOST_USER,
            to=[to_email]
        )
        
        if html_email_template_name:
            html_email = render_to_string(html_email_template_name, context)
            email.attach_alternative(html_email, 'text/html')
        email.send()


class UserCreationFormWithEmail(UserCreationForm):
    email = forms.EmailField(required=True, label='Correo:', help_text="Hasta 254 caracteres y debe ser un correo válido.")
    
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "password1", "password2")

        labels = {
            'username': 'Usuario:',
        }

    def __init__(self, *args, **kwargs):
        super(UserCreationFormWithEmail, self).__init__(*args, **kwargs)   
        self.fields['username'].help_text = """Solo letras, dígitos y @/./+/-/_ """
        self.fields['first_name'].placeholder = 'Nombres'
        self.fields['last_name'].placeholder = 'Apellidos'
        self.fields['password1'].help_text = """<br> * No puede ser similar a tu otra información.<br>
        * Debe contener al menos 8 caracteres e incluir letras, números y caracteres especiales."""
        self.fields['password2'].help_text = """Verifique que coinciden."""

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(u'El correo ya está registrado, pruebe con otro.')
        return email
    
class ProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        # override default attributes
        self.fields['link'].widget.attrs['size'] = '100'

    class Meta:
        model = Profile
        fields = ['avatar', 'bio', 'link', 'cid', 'client_type', 'phone', 'ws', 'reeup', 'nit', 'address', 'agency', 'contract']
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={'class':'btn-primary btn-block form-control-file mt-3', 'placeholder':'Subir foto'}),
            'bio': forms.Textarea(attrs={'class':'form-control mt-3', 'rows':4, 'placeholder':'Biografía'}),
            'link': forms.URLInput(attrs={'class': 'form-control mt-3', 'placeholder':'enlace'}),
            """ 'cid': forms.TextInput(attrs={'class':'form-control mt-3', 'placeholder':'Número de identidad', 'required': True}), """
            """ 'reeup': forms.TextInput(attrs={'class':'form-control mt-3', 'placeholder':'Código reeup'}),
            'nit': forms.TextInput(attrs={'class':'form-control mt-3', 'placeholder':'Código nit'}), """ 
            'address': forms.TextInput(attrs={'class':'form-control mt-3', 'placeholder':'Dirección legal'}),
            """'agency': forms.TextInput(attrs={'class':'form-control mt-3', 'placeholder':'Agencia bancaria'}), """ 
            'contract': forms.TextInput(attrs={'class':'form-control mt-3', 'placeholder':'Número de contrato'}),
        }

        labels = {
            'link': 'Sitio personal:'
        }

class EmailForm(forms.ModelForm):
    email = forms.EmailField(required=True, max_length=254, help_text="Requerido. 254 caracteres máximo y debe ser un email válido.")

    class Meta:
        model = User
        fields = ['email']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if 'email' in self.changed_data:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError("El email ya está registrado, prueba con otro.")
        return email
                             
class UpdateProfileAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UpdateProfileAdminForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Profile
        fields = ['money_type', 'prefered_store']

from utils.context_processors import MONEY_TYPE

class MNDForm(forms.Form):
    mnd = forms.ChoiceField(choices=MONEY_TYPE)
    