"""Fornecedores."""

from django.db import models

from apps.companies.models import Company
from apps.core.models import TimeStampedModel


class SupplierType(models.TextChoices):
    FUEL = "fuel", "Combustível / posto"
    WORKSHOP = "workshop", "Oficina"
    PARTS = "parts", "Peças"
    OTHER = "other", "Outro"


class Supplier(TimeStampedModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="suppliers",
        verbose_name="Empresa",
    )
    name = models.CharField("Nome ou razão social", max_length=255, blank=True, default="")
    supplier_type = models.CharField(
        "Tipo",
        max_length=32,
        choices=SupplierType.choices,
        default=SupplierType.OTHER,
    )
    tax_id = models.CharField("CPF/CNPJ", max_length=18, blank=True)
    phone = models.CharField("Telefone", max_length=32, blank=True)
    address = models.CharField("Endereço", max_length=512, blank=True)
    notes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ["name"]
        indexes = [models.Index(fields=["company", "supplier_type"])]

    def __str__(self) -> str:
        return self.name
