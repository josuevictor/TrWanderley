"""User model and company membership (RBAC foundation)."""

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.companies.models import Company
from apps.core.models import TimeStampedModel


class User(AbstractUser):
    """Utilizador do sistema; pode pertencer a várias empresas."""

    phone = models.CharField("Telefone", max_length=32, blank=True)

    class Meta:
        verbose_name = "Utilizador"
        verbose_name_plural = "Utilizadores"


class MembershipRole(models.TextChoices):
    ADMIN = "admin", "Administrador"
    MANAGER = "manager", "Gerente"
    DRIVER = "driver", "Motorista"


class CompanyMembership(TimeStampedModel):
    """Liga user ↔ company com perfil."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="Utilizador",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="Empresa",
    )
    role = models.CharField(
        "Perfil",
        max_length=32,
        choices=MembershipRole.choices,
        default=MembershipRole.MANAGER,
    )
    is_active = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Membro da empresa"
        verbose_name_plural = "Membros das empresas"
        unique_together = [("user", "company")]
        indexes = [
            models.Index(fields=["company", "user"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} @ {self.company.name} ({self.get_role_display()})"
