from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "legal_name", "cnpj", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "legal_name", "cnpj")
