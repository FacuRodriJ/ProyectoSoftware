from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """Funcion para importar las señales de la app accounts cuando se inicia la app."""
        import accounts.signals
