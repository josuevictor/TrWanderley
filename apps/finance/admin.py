from django.contrib import admin

from .models import (
    CashMovement,
    EntryPaymentAllocation,
    FinancialAccount,
    FinancialCategory,
    FinancialEntry,
    PaymentMethod,
)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "is_active", "created_at")
    list_filter = ("company", "is_active")
    search_fields = ("name",)


@admin.register(FinancialCategory)
class FinancialCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "company", "is_active")
    list_filter = ("company", "kind", "is_active")
    search_fields = ("name",)


@admin.register(FinancialAccount)
class FinancialAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "company", "is_active")
    list_filter = ("company", "kind", "is_active")
    search_fields = ("name",)


@admin.register(FinancialEntry)
class FinancialEntryAdmin(admin.ModelAdmin):
    list_display = (
        "description",
        "entry_type",
        "amount",
        "competence_date",
        "settlement_status",
        "company",
    )
    list_filter = ("company", "entry_type", "settlement_status", "is_cancelled")
    search_fields = ("description", "notes")
    raw_id_fields = ("category", "payment_method", "default_account", "created_by")


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):
    list_display = ("kind", "amount", "movement_date", "financial_account", "company")
    list_filter = ("company", "kind", "movement_date")
    search_fields = ("memo",)
    raw_id_fields = ("financial_account", "payment_method", "created_by")


@admin.register(EntryPaymentAllocation)
class EntryPaymentAllocationAdmin(admin.ModelAdmin):
    list_display = ("entry", "cash_movement", "amount", "created_at")
    raw_id_fields = ("entry", "cash_movement")
