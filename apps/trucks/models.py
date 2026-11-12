"""Frota — caminhões."""

from django.core.exceptions import ValidationError
from django.db import models

from apps.companies.models import Company
from apps.core.models import TimeStampedModel


class TruckStatus(models.TextChoices):
    ACTIVE = "active", "Ativo"
    INACTIVE = "inactive", "Inativo"
    MAINTENANCE = "maintenance", "Em manutenção"


class Truck(TimeStampedModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="trucks",
        verbose_name="Empresa",
    )
    plate = models.CharField("Matrícula", max_length=16, db_index=True, null=True, blank=True)
    model = models.CharField("Modelo", max_length=128, blank=True)
    brand = models.CharField("Marca", max_length=128, blank=True)
    year = models.PositiveSmallIntegerField("Ano", null=True, blank=True)
    tank_capacity_liters = models.DecimalField(
        "Capacidade do tanque (L)",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    current_odometer = models.DecimalField(
        "Quilometragem atual",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    acquisition_date = models.DateField("Data de aquisição", null=True, blank=True)
    status = models.CharField(
        "Situação",
        max_length=16,
        choices=TruckStatus.choices,
        default=TruckStatus.ACTIVE,
    )
    notes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Caminhão"
        verbose_name_plural = "Caminhões"
        ordering = ["plate"]
        unique_together = [("company", "plate")]
        indexes = [models.Index(fields=["company", "status"])]

    def __str__(self) -> str:
        plate = self.plate or "—"
        return f"{plate} ({self.company.name})"

    def clean(self):
        super().clean()
        if self.company_id is None:
            raise ValidationError("Empresa obrigatória.")
