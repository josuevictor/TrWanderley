from django.contrib import admin

from .models import FuelEntry


@admin.register(FuelEntry)
class FuelEntryAdmin(admin.ModelAdmin):
    list_display = ("fuel_date", "company", "truck", "liters", "total_amount")
    list_filter = ("company", "fuel_date")
    raw_id_fields = ("truck", "driver", "supplier", "payment_method", "financial_entry")
