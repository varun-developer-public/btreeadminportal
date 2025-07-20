from django.apps import AppConfig


class ConsultantdbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'consultantdb'

    def ready(self):
        import consultantdb.signals
