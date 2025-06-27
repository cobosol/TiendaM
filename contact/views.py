from django.shortcuts import render, redirect
from .forms import ContactForm
from django.urls import reverse
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from tienda.settings import EMAIL_HOST_USER
from tienda.settings import EMAIL_RECEIPT

def contact(request):
    contact_form = ContactForm 
    if request.method == "POST":
        contact_form = contact_form(data=request.POST)
        if contact_form.is_valid:
            name = request.POST.get('name', '')
            email = request.POST.get('email', '')
            content = request.POST.get('content', '')
            e_mail = EmailMessage(
                "MUHIA: Nuevo mensaje de la tienda",
                "De {} <{}>\n\n{}".format(name, email, content),
                EMAIL_HOST_USER,
                [EMAIL_RECEIPT]
            )
            subject = "MUHIA: Nuevo mensaje de la tienda"
            try:
                e_mail.send()
                return redirect(reverse('contact') + "?ok")
            except:
                return redirect(reverse('contact') + "?fail")
    return render(request, "contact/contactos.html", {'form':contact_form})
