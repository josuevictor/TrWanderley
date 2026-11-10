"""Clientes."""

from django.db import models

from apps.companies.models import Company
from apps.core.models import TimeStampedModel


class Customer(TimeStampedModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="customers",
        verbose_name="Empresa",
    )
    name = models.CharField("Nome ou razão social", max_length=255)
    tax_id = models.CharField("CPF/CNPJ", max_length=18, blank=True)
    phone = models.CharField("Telefone", max_length=32, blank=True)
    email = models.EmailField("E-mail", blank=True)
    address = models.CharField("Endereço", max_length=512, blank=True)
    notes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["name"]
        indexes = [models.Index(fields=["company", "name"])]

    def __str__(self) -> str:
        return self.name


class CustomerDeliveryPlace(TimeStampedModel):
    """Pontos de entrega cadastrados por cliente (ex.: obras, filiais)."""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="delivery_places",
        verbose_name="Cliente",
    )
    label = models.CharField("Nome do local (opcional)", max_length=120, blank=True)
    address_line = models.CharField("Endereço / local de entrega", max_length=512)
    sort_order = models.PositiveSmallIntegerField("Ordem", default=0)

    class Meta:
        verbose_name = "Local de entrega"
        verbose_name_plural = "Locais de entrega"
        ordering = ["sort_order", "pk"]
        indexes = [models.Index(fields=["customer", "sort_order"])]

    def __str__(self) -> str:
        if self.label:
            return f"{self.label} — {self.address_line}"
        return self.address_line
