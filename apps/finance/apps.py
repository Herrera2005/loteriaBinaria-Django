from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.finance"
    verbose_name = "Finanzas y wallets"

    def ready(self) -> None:
        from . import signals  # noqa: F401
