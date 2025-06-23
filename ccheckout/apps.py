from django.apps import AppConfig


class CcheckoutConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ccheckout'
    verbose_name = 'Pagar'

    def ready(self):
        import ccheckout.signals

""" class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payments'
    verbose_name = 'Formas de pago'

    def ready(self):
        import payments.signals """