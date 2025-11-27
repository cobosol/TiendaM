from django.contrib import admin
from django.urls import path, re_path
from django.conf.urls.static import static
from django.conf import settings
from django.urls.conf import include
from django.views.static import serve
from .views import index_view 


admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('catalogo/', include('catalog.urls')),
    path('pagina/', include('pages.urls')),
    path('carrito/', include('cart.urls')),
    path('accounts/', include('registration.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('compra/', include('ccheckout.urls')),
    path('contacto/', include('contact.urls')),
    path('tiendas/', include('stores.urls')),
    path('promo/', include('promo.urls')),
    path('precio/', include('utils.urls')),
    path('servicios/', include('services.urls')),
    path('notification/', include('notification.urls')),
    path('wallet/', include('wallet.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('', index_view, name="home"),
]

""" urlpatterns += [
    re_path(r'^ckeditor5/(?P<path>.*)$', serve,{'document_root': settings.CKEDITOR_BASEPATH}),
    re_path(r'^ckeditor5/(?P<path>.*)$', serve,{'document_root': settings.CKEDITOR_UPLOAD_PATH}),
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
] """

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#handler404 = 'tienda.views.file_not_found_404'
