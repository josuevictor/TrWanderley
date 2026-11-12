"""Manutenção da frota."""

from django.core.exceptions import ValidationError
from django.db import models

from apps.companies.models import Company
from apps.core.models import TimeStampedModel
from apps.suppliers.models import Supplier
from apps.trucks.models import Truck


class MaintenanceKind(models.TextChoices):
    OIL = "oil", "Troca de óleo"
    FILTERS = "filters", "Filtros"
    TIRES = "tires", "Pneus"
    BRAKES = "brakes", "Freios"
    ENGINE = "engine", "Motor"
    PUMP = "pump", "Bomba d'água"
    HOSES = "hoses", "Mangueiras"
    GENERAL = "general", "Manutenção geral"
    OTHER = "other", "Outra"


class MaintenanceRecord(TimeStampedModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="maintenance_records",
        verbose_name="Empresa",
    )
    truck = models.ForeignKey(
        Truck,
        on_delete=models.PROTECT,
        related_name="maintenance_records",
        verbose_name="Caminhão",
        null=True,
        blank=True,
    )
    kind = models.CharField(
        "Tipo",
        max_length=32,
        choices=MaintenanceKind.choices,
        default=MaintenanceKind.GENERAL,
    )
    title = models.CharField("Resumo", max_length=255, blank=True)
    description = models.TextField("Descrição", blank=True)
    workshop = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="maintenance_jobs",
        verbose_name="Oficina / fornecedor",
    )
    workshop_name = models.CharField("Oficina (texto)", max_length=255, blank=True)
    service_date = models.DateField("Data", null=True, blank=True)
    odometer_km = models.DecimalField(
        "Quilometragem",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    parts_amount = models.DecimalField(
        "Valor peças",
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    labor_amount = models.DecimalField(
        "Mão de obra",
        max_digits=14,
        decimal_places=2,
        default=0,
    )
    total_amount = models.DecimalField(
        "Valor total", max_digits=14, decimal_places=2, default=0
    )
    next_service_date = models.DateField(
        "Próxima manutenção (data)",
        null=True,
        blank=True,
    )
    next_service_odometer = models.DecimalField(
        "Próxima manutenção (km)",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    financial_entry = models.OneToOneField(
        "finance.FinancialEntry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="maintenance_source",
        verbose_name="Lançamento financeiro",
    )
    receipt = models.FileField("Comprovante", upload_to="maintenance/%Y/%m/", blank=True)
    notes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Manutenção"
        verbose_name_plural = "Manutenções"
        ordering = ["-service_date", "-pk"]
        indexes = [
            models.Index(fields=["company", "service_date"]),
            models.Index(fields=["company", "truck"]),
        ]

    def __str__(self) -> str:
        plate = self.truck.plate if self.truck_id else "—"
        when = self.service_date or "—"
        return f"{self.get_kind_display()} — {plate} ({when})"

    def clean(self):
        super().clean()
        # company_id pode ainda não estar atribuído (ex.: form.save antes de definir FK)
        cid = self.company_id
        if self.truck_id and cid is not None and self.truck.company_id != cid:
            raise ValidationError("O caminhão deve pertencer à mesma empresa.")
        if self.workshop_id and cid is not None and self.workshop.company_id != cid:
            raise ValidationError("O fornecedor deve pertencer à mesma empresa.")
        if self.financial_entry_id and cid is not None and self.financial_entry.company_id != cid:
            raise ValidationError("O lançamento financeiro deve ser da mesma empresa.")
