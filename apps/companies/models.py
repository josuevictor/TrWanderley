"""Company (tenant) — isolamento de dados por empresa."""

from django.db import models

from apps.core.models import TimeStampedModel


class Company(TimeStampedModel):
    """Uma empresa cliente do sistema (futuro SaaS)."""

    name = models.CharField("Nome", max_length=255)
    legal_name = models.CharField("Razão social", max_length=255, blank=True)
    cnpj = models.CharField("CNPJ", max_length=18, blank=True, db_index=True)
    timezone = models.CharField("Fuso horário", max_length=64, default="America/Maceio")
    currency = models.CharField("Moeda", max_length=8, default="BRL")
    is_active = models.BooleanField("Ativa", default=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
