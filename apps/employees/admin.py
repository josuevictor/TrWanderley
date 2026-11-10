from django.contrib import admin

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "role_title", "status", "user", "truck")
    list_filter = ("company", "status")
    search_fields = ("name", "cpf", "phone")
    raw_id_fields = ("user", "truck")
