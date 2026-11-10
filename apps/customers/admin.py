from django.contrib import admin

from .models import Customer, CustomerDeliveryPlace


class CustomerDeliveryPlaceInline(admin.TabularInline):
    model = CustomerDeliveryPlace
    extra = 0
    fields = ("sort_order", "label", "address_line")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "company", "phone")
    search_fields = ("name", "tax_id", "phone")
    list_filter = ("company",)
    inlines = [CustomerDeliveryPlaceInline]


@admin.register(CustomerDeliveryPlace)
class CustomerDeliveryPlaceAdmin(admin.ModelAdmin):
    list_display = ("customer", "label", "address_line", "sort_order")
    search_fields = ("address_line", "label", "customer__name")
    list_filter = ("customer__company",)
    raw_id_fields = ("customer",)
