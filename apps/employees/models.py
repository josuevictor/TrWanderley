"""Funcionários e motoristas."""

from django.db import models

from apps.companies.models import Company
from apps.core.models import TimeStampedModel
from apps.trucks.models import Truck


class EmployeeStatus(models.TextChoices):
    ACTIVE = "active", "Ativo"
    INACTIVE = "inactive", "Inativo"


class Employee(TimeStampedModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="employees",
        verbose_name="Empresa",
    )
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_profile",
        verbose_name="Utilizador (login)",
    )
    name = models.CharField("Nome", max_length=255)
    cpf = models.CharField("CPF", max_length=14, blank=True, db_index=True)
    phone = models.CharField("Telefone", max_length=32, blank=True)
    address = models.CharField("Endereço", max_length=512, blank=True)
    hire_date = models.DateField("Data de contratação", null=True, blank=True)
    role_title = models.CharField("Função", max_length=128, blank=True)
    payment_notes = models.CharField(
        "Salário / forma de pagamento",
        max_length=512,
        blank=True,
    )
    truck = models.ForeignKey(
        Truck,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_employees",
        verbose_name="Caminhão associado",
    )
    status = models.CharField(
        "Situação",
        max_length=16,
        choices=EmployeeStatus.choices,
        default=EmployeeStatus.ACTIVE,
    )

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"
        ordering = ["name"]
        indexes = [models.Index(fields=["company", "status"])]

    def __str__(self) -> str:
        return self.name
