"""Sinais — sincronizar lançamentos gerados pela operação."""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.fuel.models import FuelEntry
from apps.maintenance.models import MaintenanceRecord
from apps.trips.models import Trip

from .models import FinancialEntry, FinancialSettlementStatus
from .services import (
    sync_auto_cash_for_entry,
    sync_fuel_financial_entry,
    sync_maintenance_financial_entry,
    sync_trip_financial_entry,
)


def _cancel_linked_entry(financial_entry_id: int | None) -> None:
    if not financial_entry_id:
        return
    FinancialEntry.objects.filter(pk=financial_entry_id).update(
        is_cancelled=True,
        settlement_status=FinancialSettlementStatus.PENDING,
    )
    entry = FinancialEntry.objects.get(pk=financial_entry_id)
    sync_auto_cash_for_entry(entry)


@receiver(post_save, sender=FinancialEntry)
def financial_entry_saved(sender, instance, **kwargs):
    sync_auto_cash_for_entry(instance)


@receiver(post_save, sender=Trip)
def trip_saved(sender, instance, **kwargs):
    sync_trip_financial_entry(instance)


@receiver(post_delete, sender=Trip)
def trip_deleted(sender, instance, **kwargs):
    _cancel_linked_entry(instance.financial_entry_id)


@receiver(post_save, sender=FuelEntry)
def fuel_saved(sender, instance, **kwargs):
    sync_fuel_financial_entry(instance)


@receiver(post_delete, sender=FuelEntry)
def fuel_deleted(sender, instance, **kwargs):
    _cancel_linked_entry(instance.financial_entry_id)


@receiver(post_save, sender=MaintenanceRecord)
def maintenance_saved(sender, instance, **kwargs):
    sync_maintenance_financial_entry(instance)


@receiver(post_delete, sender=MaintenanceRecord)
def maintenance_deleted(sender, instance, **kwargs):
    _cancel_linked_entry(instance.financial_entry_id)
