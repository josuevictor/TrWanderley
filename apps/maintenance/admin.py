from django.contrib import admin

from .models import MaintenanceRecord


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ("service_date", "company", "truck", "kind", "total_amount")
    list_filter = ("company", "kind", "service_date")
    raw_id_fields = ("truck", "workshop", "financial_entry")
