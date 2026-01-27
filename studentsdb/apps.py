from django.apps import AppConfig


class StudentsdbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'studentsdb'

    def ready(self):
        from paymentdb.models import Payment
        from django.db.models.signals import post_save
        from .models import send_payment_onboarding_message
        post_save.connect(send_payment_onboarding_message, sender=Payment)
