from django.contrib import admin

from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "supplier_type")
    search_fields = ("name", "tax_id")
    list_filter = ("company", "supplier_type")
