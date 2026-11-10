from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.finance"
    verbose_name = "Financeiro"

    def ready(self) -> None:
        from apps.finance import signals  # noqa: F401
