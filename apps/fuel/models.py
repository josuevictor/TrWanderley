"""Abastecimento."""

from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.companies.models import Company
from apps.core.models import TimeStampedModel
from apps.employees.models import Employee
from apps.suppliers.models import Supplier
from apps.trucks.models import Truck


class FuelType(models.TextChoices):
    DIESEL = "diesel", "Diesel"
    GASOLINE = "gasoline", "Gasolina"
    ETHANOL = "ethanol", "Etanol"
    OTHER = "other", "Outro"


class FuelEntry(TimeStampedModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="fuel_entries",
        verbose_name="Empresa",
    )
    truck = models.ForeignKey(
        Truck,
        on_delete=models.PROTECT,
        related_name="fuel_entries",
        verbose_name="Caminhão",
    )
    driver = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="fuel_entries",
        verbose_name="Motorista",
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fuel_entries",
        verbose_name="Posto / fornecedor",
    )
    station_name = models.CharField("Posto (texto)", max_length=255, blank=True)
    fuel_date = models.DateField("Data")
    fuel_type = models.CharField(
        "Combustível",
        max_length=32,
        choices=FuelType.choices,
        default=FuelType.DIESEL,
    )
    liters = models.DecimalField("Litros", max_digits=12, decimal_places=3)
    price_per_liter = models.DecimalField(
        "Preço por litro",
        max_digits=12,
        decimal_places=4,
    )
    total_amount = models.DecimalField("Valor total", max_digits=14, decimal_places=2)
    odometer_km = models.DecimalField(
        "Quilometragem",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    payment_method = models.ForeignKey(
        "finance.PaymentMethod",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fuel_entries",
        verbose_name="Forma de pagamento",
    )
    financial_entry = models.OneToOneField(
        "finance.FinancialEntry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fuel_source",
        verbose_name="Lançamento financeiro",
    )
    receipt = models.FileField("Comprovante", upload_to="fuel/%Y/%m/", blank=True)

    class Meta:
        verbose_name = "Abastecimento"
        verbose_name_plural = "Abastecimentos"
        ordering = ["-fuel_date", "-pk"]
        indexes = [models.Index(fields=["company", "fuel_date"])]

    def __str__(self) -> str:
        return f"{self.truck.plate} — {self.fuel_date}"

    def clean(self):
        super().clean()
        cid = self.company_id
        for obj, label in ((self.truck, "caminhão"), (self.driver, "motorista")):
            if obj and cid is not None and obj.company_id != cid:
                raise ValidationError(f"O {label} deve pertencer à mesma empresa.")
        if self.supplier_id and cid is not None and self.supplier.company_id != cid:
            raise ValidationError("O fornecedor deve pertencer à mesma empresa.")
        if self.payment_method_id and cid is not None and self.payment_method.company_id != cid:
            raise ValidationError("A forma de pagamento deve pertencer à mesma empresa.")
        if self.liters is not None and self.liters <= 0:
            raise ValidationError("Litros devem ser positivos.")
        if self.price_per_liter is not None and self.price_per_liter < 0:
            raise ValidationError("Preço por litro inválido.")
        if self.total_amount is not None and self.total_amount <= 0:
            raise ValidationError("Valor total deve ser positivo.")
        if self.liters and self.price_per_liter is not None and self.total_amount:
            calc = (self.liters * self.price_per_liter).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if abs(calc - self.total_amount) > Decimal("0.05"):
                raise ValidationError(
                    f"Valor total ({self.total_amount}) não bate com litros × preço ({calc})."
                )
