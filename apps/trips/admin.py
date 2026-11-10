from django.contrib import admin

from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("trip_date", "company", "truck", "customer", "amount_charged", "payment_status")
    list_filter = ("company", "payment_status", "trip_date")
    search_fields = ("customer__name", "truck__plate")
    raw_id_fields = ("truck", "driver", "customer", "delivery_place_ref", "payment_method", "financial_entry")
