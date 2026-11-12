"""
Módulo financeiro — núcleo com valores em Decimal (competência vs caixa).

Parcelamento e amarrações (viagem, manutenção) evoluem nas etapas seguintes.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models import Sum

from apps.companies.models import Company
from apps.core.models import TimeStampedModel


class PaymentMethod(TimeStampedModel):
    """Forma de pagamento (PIX, dinheiro, cartão, etc.)."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="payment_methods",
        verbose_name="Empresa",
    )
    name = models.CharField("Nome", max_length=64, blank=True, default="")
    is_active = models.BooleanField("Ativo", default=True)

    class Meta:
        verbose_name = "Forma de pagamento"
        verbose_name_plural = "Formas de pagamento"
        unique_together = [("company", "name")]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class FinancialCategoryKind(models.TextChoices):
    INCOME = "income", "Receita"
    EXPENSE = "expense", "Despesa"


class FinancialCategory(TimeStampedModel):
    """Categoria financeira (receita ou despesa)."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="financial_categories",
        verbose_name="Empresa",
    )
    name = models.CharField("Nome", max_length=128, blank=True, default="")
    slug = models.SlugField(
        "Código",
        max_length=64,
        blank=True,
        default="",
        help_text="Identificador interno (ex.: trip_income, fuel).",
    )
    kind = models.CharField(
        "Tipo",
        max_length=16,
        choices=FinancialCategoryKind.choices,
        default=FinancialCategoryKind.EXPENSE,
    )
    is_active = models.BooleanField("Ativa", default=True)

    class Meta:
        verbose_name = "Categoria financeira"
        verbose_name_plural = "Categorias financeiras"
        unique_together = [("company", "kind", "name")]
        ordering = ["kind", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "kind", "slug"],
                condition=~Q(slug=""),
                name="finance_category_unique_slug_when_set",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.name}"


class FinancialAccountKind(models.TextChoices):
    CASH = "cash", "Caixa"
    BANK = "bank", "Conta bancária"
    DIGITAL = "digital", "Conta digital"
    OTHER = "other", "Outra"


class FinancialAccount(TimeStampedModel):
    """Caixa, banco ou carteira — saldo via movimentos (caixa)."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="financial_accounts",
        verbose_name="Empresa",
    )
    name = models.CharField("Nome", max_length=128, blank=True, default="")
    kind = models.CharField(
        "Tipo",
        max_length=16,
        choices=FinancialAccountKind.choices,
        default=FinancialAccountKind.CASH,
    )
    is_active = models.BooleanField("Ativa", default=True)

    class Meta:
        verbose_name = "Conta financeira"
        verbose_name_plural = "Contas financeiras"
        unique_together = [("company", "name")]
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class FinancialEntryType(models.TextChoices):
    INCOME = "income", "Receita"
    EXPENSE = "expense", "Despesa"


class FinancialSettlementStatus(models.TextChoices):
    PENDING = "pending", "Pendente"
    PARTIAL = "partial", "Parcial"
    SETTLED = "settled", "Quitado"
    OVERDUE = "overdue", "Vencido"


class FinancialEntry(TimeStampedModel):
    """
    Lançamento de competência (receita ou despesa).

    Valores monetários: Decimal; situação de quitação acompanha alocações em caixa.
    """

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="financial_entries",
        verbose_name="Empresa",
    )
    entry_type = models.CharField(
        "Tipo",
        max_length=16,
        choices=FinancialEntryType.choices,
        default=FinancialEntryType.EXPENSE,
    )
    description = models.CharField("Descrição", max_length=512, blank=True, default="")
    category = models.ForeignKey(
        FinancialCategory,
        on_delete=models.PROTECT,
        related_name="entries",
        verbose_name="Categoria",
        null=True,
        blank=True,
    )
    amount = models.DecimalField("Valor", max_digits=14, decimal_places=2, default=0)
    competence_date = models.DateField("Data de competência", null=True, blank=True)
    due_date = models.DateField("Vencimento", null=True, blank=True)
    settlement_status = models.CharField(
        "Situação",
        max_length=16,
        choices=FinancialSettlementStatus.choices,
        default=FinancialSettlementStatus.PENDING,
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entries",
        verbose_name="Forma de pagamento (padrão)",
    )
    default_account = models.ForeignKey(
        FinancialAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_for_entries",
        verbose_name="Conta (padrão)",
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_financial_entries",
        verbose_name="Criado por",
    )
    is_cancelled = models.BooleanField("Cancelado", default=False)
    cancelled_at = models.DateTimeField("Cancelado em", null=True, blank=True)
    notes = models.TextField("Observações", blank=True)
    is_system_generated = models.BooleanField(
        "Gerado automaticamente",
        default=False,
        help_text="Lançamento criado por viagem, combustível ou manutenção.",
    )
    truck = models.ForeignKey(
        "trucks.Truck",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="financial_entries",
        verbose_name="Caminhão",
    )
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="financial_entries",
        verbose_name="Cliente",
    )
    employee = models.ForeignKey(
        "employees.Employee",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="financial_entries",
        verbose_name="Funcionário",
    )

    class Meta:
        verbose_name = "Lançamento financeiro"
        verbose_name_plural = "Lançamentos financeiros"
        ordering = ["-competence_date", "-pk"]
        indexes = [
            models.Index(fields=["company", "competence_date"]),
            models.Index(fields=["company", "settlement_status"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_entry_type_display()} — {self.description} ({self.amount})"

    def clean(self):
        super().clean()
        cid = self.company_id
        if self.category_id and cid is not None and self.category.company_id != cid:
            raise ValidationError("A categoria deve pertencer à mesma empresa.")
        if self.payment_method_id and cid is not None and self.payment_method.company_id != cid:
            raise ValidationError("A forma de pagamento deve pertencer à mesma empresa.")
        if self.default_account_id and cid is not None and self.default_account.company_id != cid:
            raise ValidationError("A conta deve pertencer à mesma empresa.")
        expected_kind = (
            FinancialCategoryKind.INCOME
            if self.entry_type == FinancialEntryType.INCOME
            else FinancialCategoryKind.EXPENSE
        )
        if (
            self.category_id
            and self.entry_type
            and self.category.kind != expected_kind
        ):
            raise ValidationError("O tipo do lançamento não corresponde à categoria.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def _refresh_settlement_status(self) -> None:
        """Atualiza situação conforme alocações (evita recursão em save())."""
        paid = self.amount_paid
        total = self.amount or Decimal("0")
        if paid == 0:
            status = FinancialSettlementStatus.PENDING
        elif paid >= total:
            status = FinancialSettlementStatus.SETTLED
        else:
            status = FinancialSettlementStatus.PARTIAL
        if self.due_date and status != FinancialSettlementStatus.SETTLED:
            from django.utils import timezone

            if self.due_date < timezone.now().date():
                status = FinancialSettlementStatus.OVERDUE
        FinancialEntry.objects.filter(pk=self.pk).update(settlement_status=status)
        self.settlement_status = status

    @property
    def amount_paid(self) -> Decimal:
        total = self.payment_allocations.aggregate(s=models.Sum("amount"))["s"]
        return total if total is not None else Decimal("0")

    @property
    def amount_open(self) -> Decimal:
        return (self.amount or Decimal("0")) - self.amount_paid


class CashMovementKind(models.TextChoices):
    RECEIPT = "receipt", "Recebimento"
    PAYMENT = "payment", "Pagamento"
    TRANSFER_OUT = "transfer_out", "Transferência (saída)"
    TRANSFER_IN = "transfer_in", "Transferência (entrada)"


class CashMovement(TimeStampedModel):
    """
    Movimento de caixa (data de pagamento/recebimento).

    Transferências usam dois registos ligados por transfer_group.
    """

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="cash_movements",
        verbose_name="Empresa",
    )
    financial_account = models.ForeignKey(
        FinancialAccount,
        on_delete=models.PROTECT,
        related_name="movements",
        verbose_name="Conta",
        null=True,
        blank=True,
    )
    kind = models.CharField("Tipo", max_length=16, choices=CashMovementKind.choices)
    amount = models.DecimalField("Valor", max_digits=14, decimal_places=2, default=0)
    movement_date = models.DateField("Data do movimento", null=True, blank=True)
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cash_movements",
        verbose_name="Forma de pagamento",
    )
    transfer_group = models.UUIDField(
        "Grupo de transferência",
        null=True,
        blank=True,
        editable=False,
        db_index=True,
    )
    memo = models.CharField("Memorando", max_length=255, blank=True)
    auto_for_entry = models.OneToOneField(
        FinancialEntry,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="auto_cash_movement",
        verbose_name="Lançamento (caixa automático)",
        help_text="Preenchido no modo caderno: um movimento por lançamento.",
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_cash_movements",
        verbose_name="Criado por",
    )

    class Meta:
        verbose_name = "Movimento de caixa"
        verbose_name_plural = "Movimentos de caixa"
        ordering = ["-movement_date", "-pk"]
        indexes = [
            models.Index(fields=["company", "movement_date"]),
            models.Index(fields=["company", "kind"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} {self.amount} @ {self.financial_account}"

    def clean(self):
        super().clean()
        cid = self.company_id
        if self.financial_account_id and cid is not None and self.financial_account.company_id != cid:
            raise ValidationError("A conta deve pertencer à mesma empresa.")
        if self.payment_method_id and cid is not None and self.payment_method.company_id != cid:
            raise ValidationError("A forma de pagamento deve pertencer à mesma empresa.")
        if self.amount is not None and self.amount < 0:
            raise ValidationError("O valor do movimento não pode ser negativo.")
        if (
            self.auto_for_entry_id
            and cid is not None
            and self.auto_for_entry.company_id != cid
        ):
            raise ValidationError("O lançamento automático deve ser da mesma empresa.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class EntryPaymentAllocation(TimeStampedModel):
    """Liga um movimento de caixa a um lançamento (quitação parcial ou total)."""

    entry = models.ForeignKey(
        FinancialEntry,
        on_delete=models.CASCADE,
        related_name="payment_allocations",
        verbose_name="Lançamento",
    )
    cash_movement = models.ForeignKey(
        CashMovement,
        on_delete=models.CASCADE,
        related_name="entry_allocations",
        verbose_name="Movimento de caixa",
    )
    amount = models.DecimalField("Valor alocado", max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = "Alocação de pagamento"
        verbose_name_plural = "Alocações de pagamento"
        ordering = ["-pk"]

    def __str__(self) -> str:
        return f"{self.amount} → {self.entry_id}"

    def clean(self):
        super().clean()
        if self.entry.company_id != self.cash_movement.company_id:
            raise ValidationError("Lançamento e movimento devem ser da mesma empresa.")
        if self.entry.is_cancelled:
            raise ValidationError("Não é possível alocar a um lançamento cancelado.")
        entry_type = self.entry.entry_type
        if entry_type == FinancialEntryType.INCOME and self.cash_movement.kind not in (
            CashMovementKind.RECEIPT,
        ):
            raise ValidationError("Receita deve ser alocada a um recebimento.")
        if entry_type == FinancialEntryType.EXPENSE and self.cash_movement.kind not in (
            CashMovementKind.PAYMENT,
        ):
            raise ValidationError("Despesa deve ser alocada a um pagamento.")
        if self.amount is not None and self.amount <= 0:
            raise ValidationError("O valor alocado deve ser positivo.")
        qs = EntryPaymentAllocation.objects.filter(entry_id=self.entry_id)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        already = qs.aggregate(s=Sum("amount"))["s"] or Decimal("0")
        cap = self.entry.amount or Decimal("0")
        if self.amount is not None and already + self.amount > cap:
            raise ValidationError("O valor alocado excede o valor do lançamento.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.entry._refresh_settlement_status()

    def delete(self, *args, **kwargs):
        entry = self.entry
        super().delete(*args, **kwargs)
        entry._refresh_settlement_status()
