from django.contrib import admin

from .models import Truck


@admin.register(Truck)
class TruckAdmin(admin.ModelAdmin):
    list_display = ("plate", "company", "brand", "model", "status")
    list_filter = ("company", "status")
    search_fields = ("plate", "model", "brand")
