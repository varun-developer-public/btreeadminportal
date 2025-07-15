from django.apps import AppConfig

class SettingsdbConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'settingsdb'

    def ready(self):
        import settingsdb.signals  # required to hook the signal
