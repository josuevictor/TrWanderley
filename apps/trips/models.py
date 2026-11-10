"""Viagens e serviços."""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.companies.models import Company
from apps.core.models import TimeStampedModel
from apps.customers.models import Customer, CustomerDeliveryPlace
from apps.employees.models import Employee
from apps.trucks.models import Truck


class TripPaymentStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    PARTIAL = "partial", "Parcial"
    SETTLED = "settled", "Recebido"


class Trip(TimeStampedModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="trips",
        verbose_name="Empresa",
    )
    truck = models.ForeignKey(
        Truck,
        on_delete=models.PROTECT,
        related_name="trips",
        verbose_name="Caminhão",
    )
    driver = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="trips_driven",
        verbose_name="Motorista",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="trips",
        verbose_name="Cliente",
    )
    trip_date = models.DateField("Data")
    trip_time = models.TimeField("Hora", null=True, blank=True)
    water_source = models.CharField("Local de captação", max_length=255, blank=True)
    delivery_place_ref = models.ForeignKey(
        CustomerDeliveryPlace,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trips",
        verbose_name="Local de entrega (cadastro)",
    )
    delivery_place = models.CharField("Local de entrega", max_length=255, blank=True)
    volume_m3 = models.DecimalField(
        "Volume (m³)", max_digits=12, decimal_places=3, null=True, blank=True
    )
    trip_count = models.PositiveIntegerField("Quantidade de viagens", default=1)
    amount_charged = models.DecimalField("Valor cobrado", max_digits=14, decimal_places=2)
    payment_method = models.ForeignKey(
        "finance.PaymentMethod",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trips",
        verbose_name="Forma de pagamento",
    )
    payment_status = models.CharField(
        "Situação do pagamento",
        max_length=16,
        choices=TripPaymentStatus.choices,
        default=TripPaymentStatus.PENDING,
    )
    financial_entry = models.OneToOneField(
        "finance.FinancialEntry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trip_source",
        verbose_name="Lançamento financeiro",
    )
    notes = models.TextField("Observações", blank=True)

    class Meta:
        verbose_name = "Viagem"
        verbose_name_plural = "Viagens"
        ordering = ["-trip_date", "-pk"]
        indexes = [
            models.Index(fields=["company", "trip_date"]),
            models.Index(fields=["company", "truck"]),
            models.Index(fields=["company", "customer"]),
        ]

    def __str__(self) -> str:
        return f"Viagem {self.trip_date} — {self.customer.name}"

    def clean(self):
        super().clean()
        cid = self.company_id
        if self.truck_id and cid is not None and self.truck.company_id != cid:
            raise ValidationError("O caminhão deve pertencer à mesma empresa.")
        if self.driver_id and cid is not None and self.driver.company_id != cid:
            raise ValidationError("O motorista deve pertencer à mesma empresa.")
        if self.customer_id and cid is not None and self.customer.company_id != cid:
            raise ValidationError("O cliente deve pertencer à mesma empresa.")
        if self.delivery_place_ref_id and self.customer_id:
            if self.delivery_place_ref.customer_id != self.customer_id:
                raise ValidationError("O local de entrega deve pertencer ao cliente selecionado.")
        if self.delivery_place_ref_id and cid is not None:
            if self.delivery_place_ref.customer.company_id != cid:
                raise ValidationError("O local de entrega deve ser da mesma empresa.")
        if self.payment_method_id and cid is not None and self.payment_method.company_id != cid:
            raise ValidationError("A forma de pagamento deve pertencer à mesma empresa.")
        if self.amount_charged is not None and self.amount_charged < 0:
            raise ValidationError("O valor cobrado não pode ser negativo.")
        if self.financial_entry_id and cid is not None and self.financial_entry.company_id != cid:
            raise ValidationError("O lançamento financeiro deve ser da mesma empresa.")

    @property
    def total_volume_if_count(self) -> Decimal | None:
        if self.volume_m3 is None:
            return None
        return (self.volume_m3 or Decimal("0")) * Decimal(self.trip_count or 1)
