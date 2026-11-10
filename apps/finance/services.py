"""Serviços financeiros — categorias predefinidas e sincronização com a operação."""

from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import dateformat
from django.utils.dateparse import parse_date

def _format_date(d):
    if hasattr(d, "strftime"):
        return dateformat.format(d, "d/m/Y")
    if isinstance(d, str):
        parsed = parse_date(d)
        if parsed:
            return dateformat.format(parsed, "d/m/Y")
    return str(d)


from apps.finance.models import (
    CashMovement,
    CashMovementKind,
    EntryPaymentAllocation,
    FinancialAccount,
    FinancialAccountKind,
    FinancialCategory,
    FinancialCategoryKind,
    FinancialEntry,
    FinancialEntryType,
    FinancialSettlementStatus,
)

AUTO_CASH_MEMO = "Modo caderno (automático)"


def ensure_category(
    company,
    *,
    slug: str,
    name: str,
    kind: str,
) -> FinancialCategory:
    """
    Garante categoria por slug. Corrige linhas antigas criadas sem slug (unique por nome).
    """
    cat = FinancialCategory.objects.filter(
        company=company, kind=kind, slug=slug
    ).exclude(slug="").first()
    if cat:
        return cat
    legacy = FinancialCategory.objects.filter(
        company=company, kind=kind, name=name
    ).first()
    if legacy:
        if legacy.slug != slug:
            legacy.slug = slug
            legacy.is_active = True
            legacy.save(update_fields=["slug", "is_active"])
        return legacy
    return FinancialCategory.objects.create(
        company=company,
        kind=kind,
        slug=slug,
        name=name,
        is_active=True,
    )


def ensure_default_cash_account(company) -> FinancialAccount:
    """Conta usada para movimentos automáticos (modo caderno)."""
    account = (
        FinancialAccount.objects.filter(
            company=company, is_active=True, kind=FinancialAccountKind.CASH
        )
        .order_by("pk")
        .first()
    )
    if account is None:
        account = (
            FinancialAccount.objects.filter(company=company, is_active=True)
            .order_by("pk")
            .first()
        )
    if account is None:
        account = FinancialAccount.objects.create(
            company=company,
            name="Caixa principal",
            kind=FinancialAccountKind.CASH,
            is_active=True,
        )
    return account


def ensure_default_categories(company) -> None:
    """Categorias e formas base para o MVP (idempotente)."""
    defaults_income = [
        ("trip_income", "Receita de viagens"),
        ("service_extra", "Serviços adicionais"),
        ("other_income", "Outras receitas"),
    ]
    for slug, name in defaults_income:
        ensure_category(company, slug=slug, name=name, kind=FinancialCategoryKind.INCOME)

    defaults_expense = [
        ("fuel", "Combustível"),
        ("maintenance", "Manutenção"),
        ("tires", "Pneus"),
        ("salary", "Salários"),
        ("other_expense", "Outras despesas"),
    ]
    for slug, name in defaults_expense:
        ensure_category(company, slug=slug, name=name, kind=FinancialCategoryKind.EXPENSE)


@transaction.atomic
def sync_trip_financial_entry(trip) -> FinancialEntry:
    """Um lançamento de receita por viagem; atualiza sem duplicar."""
    from apps.trips.models import Trip

    if not isinstance(trip, Trip):
        trip = Trip.objects.select_related("company", "customer", "truck").get(pk=trip.pk)

    company = trip.company
    ensure_default_categories(company)
    category = FinancialCategory.objects.get(
        company=company,
        kind=FinancialCategoryKind.INCOME,
        slug="trip_income",
    )

    desc = f"Viagem {_format_date(trip.trip_date)} — {trip.customer.name}"

    if trip.financial_entry_id:
        entry = trip.financial_entry
        entry.description = desc[:512]
        entry.category = category
        entry.amount = trip.amount_charged
        entry.competence_date = trip.trip_date
        entry.entry_type = FinancialEntryType.INCOME
        entry.payment_method = trip.payment_method
        entry.truck = trip.truck
        entry.customer = trip.customer
        entry.is_system_generated = True
        entry.is_cancelled = False
        entry.save()
    else:
        entry = FinancialEntry.objects.create(
            company=company,
            entry_type=FinancialEntryType.INCOME,
            description=desc[:512],
            category=category,
            amount=trip.amount_charged,
            competence_date=trip.trip_date,
            due_date=None,
            settlement_status=FinancialSettlementStatus.PENDING,
            payment_method=trip.payment_method,
            is_system_generated=True,
            truck=trip.truck,
            customer=trip.customer,
        )
        trip.financial_entry = entry
        Trip.objects.filter(pk=trip.pk).update(financial_entry=entry)

    return entry


@transaction.atomic
def sync_fuel_financial_entry(fuel) -> FinancialEntry:
    from apps.fuel.models import FuelEntry

    if not isinstance(fuel, FuelEntry):
        fuel = FuelEntry.objects.select_related("company", "truck", "driver").get(pk=fuel.pk)

    company = fuel.company
    ensure_default_categories(company)
    category = FinancialCategory.objects.get(
        company=company,
        kind=FinancialCategoryKind.EXPENSE,
        slug="fuel",
    )

    desc = f"Combustível {_format_date(fuel.fuel_date)} — {fuel.truck.plate}"

    if fuel.financial_entry_id:
        entry = fuel.financial_entry
        entry.description = desc[:512]
        entry.category = category
        entry.amount = fuel.total_amount
        entry.competence_date = fuel.fuel_date
        entry.entry_type = FinancialEntryType.EXPENSE
        entry.payment_method = fuel.payment_method
        entry.default_account = None
        entry.truck = fuel.truck
        entry.employee = fuel.driver
        entry.is_system_generated = True
        entry.is_cancelled = False
        entry.save()
    else:
        entry = FinancialEntry.objects.create(
            company=company,
            entry_type=FinancialEntryType.EXPENSE,
            description=desc[:512],
            category=category,
            amount=fuel.total_amount,
            competence_date=fuel.fuel_date,
            settlement_status=FinancialSettlementStatus.PENDING,
            payment_method=fuel.payment_method,
            is_system_generated=True,
            truck=fuel.truck,
            employee=fuel.driver,
        )
        fuel.financial_entry = entry
        FuelEntry.objects.filter(pk=fuel.pk).update(financial_entry=entry)

    return entry


@transaction.atomic
def sync_maintenance_financial_entry(record) -> FinancialEntry:
    from apps.maintenance.models import MaintenanceRecord

    if not isinstance(record, MaintenanceRecord):
        record = MaintenanceRecord.objects.select_related("company", "truck").get(pk=record.pk)

    company = record.company
    ensure_default_categories(company)
    category = FinancialCategory.objects.get(
        company=company,
        kind=FinancialCategoryKind.EXPENSE,
        slug="maintenance",
    )

    desc = (
        f"Manutenção ({record.get_kind_display()}) {_format_date(record.service_date)} "
        f"— {record.truck.plate}"
    )

    if record.financial_entry_id:
        entry = record.financial_entry
        entry.description = desc[:512]
        entry.category = category
        entry.amount = record.total_amount
        entry.competence_date = record.service_date
        entry.entry_type = FinancialEntryType.EXPENSE
        entry.truck = record.truck
        entry.is_system_generated = True
        entry.is_cancelled = False
        entry.save()
    else:
        entry = FinancialEntry.objects.create(
            company=company,
            entry_type=FinancialEntryType.EXPENSE,
            description=desc[:512],
            category=category,
            amount=record.total_amount,
            competence_date=record.service_date,
            settlement_status=FinancialSettlementStatus.PENDING,
            is_system_generated=True,
            truck=record.truck,
        )
        record.financial_entry = entry
        MaintenanceRecord.objects.filter(pk=record.pk).update(financial_entry=entry)

    return entry


def _clear_auto_cash_for_entry(entry: FinancialEntry) -> None:
    """Remove movimento e alocação automáticos do lançamento."""
    cm = CashMovement.objects.filter(auto_for_entry_id=entry.pk).first()
    if cm is None:
        FinancialEntry.objects.filter(pk=entry.pk).update(
            settlement_status=FinancialSettlementStatus.PENDING
        )
        entry.settlement_status = FinancialSettlementStatus.PENDING
        return
    EntryPaymentAllocation.objects.filter(cash_movement=cm).delete()
    cm.delete()
    entry._refresh_settlement_status()


@transaction.atomic
def sync_auto_cash_for_entry(entry: FinancialEntry) -> None:
    """
    Modo caderno: cada lançamento gera recebimento/pagamento em caixa e quitação total.
    Idempotente por CashMovement.auto_for_entry.
    """
    if entry.is_cancelled or (entry.amount or Decimal("0")) <= 0:
        _clear_auto_cash_for_entry(entry)
        return

    company = entry.company
    if entry.default_account_id and entry.default_account.is_active:
        account = entry.default_account
    else:
        account = ensure_default_cash_account(company)

    kind = (
        CashMovementKind.RECEIPT
        if entry.entry_type == FinancialEntryType.INCOME
        else CashMovementKind.PAYMENT
    )
    memo = (entry.description[: 255 - len(AUTO_CASH_MEMO) - 3] or "Lançamento").strip()
    memo = f"{AUTO_CASH_MEMO}: {memo}"[:255]

    cm = CashMovement.objects.filter(auto_for_entry_id=entry.pk).first()
    if cm is None:
        cm = CashMovement(
            company=company,
            auto_for_entry=entry,
        )
    cm.financial_account = account
    cm.kind = kind
    cm.amount = entry.amount
    cm.movement_date = entry.competence_date
    cm.payment_method = entry.payment_method
    cm.memo = memo
    cm.save()

    alloc = EntryPaymentAllocation.objects.filter(
        entry=entry, cash_movement=cm
    ).first()
    if alloc is None:
        EntryPaymentAllocation.objects.create(
            entry=entry,
            cash_movement=cm,
            amount=entry.amount,
        )
    elif alloc.amount != entry.amount:
        alloc.amount = entry.amount
        alloc.save()
    else:
        entry._refresh_settlement_status()
