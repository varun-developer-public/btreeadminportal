from django.apps import AppConfig


class BatchdbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'batchdb'
    
    def ready(self):
        # Import signals to register them
        import batchdb.signals
