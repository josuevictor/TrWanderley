from django import forms
from django.db.models import Q

from apps.core.form_utils import finalize_company_form
from apps.finance.forms import T_INPUT, T_SELECT

from .models import Employee, EmployeeStatus


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            "name",
            "cpf",
            "phone",
            "address",
            "hire_date",
            "role_title",
            "payment_notes",
            "truck",
            "status",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": T_INPUT}),
            "cpf": forms.TextInput(attrs={"class": T_INPUT}),
            "phone": forms.TextInput(attrs={"class": T_INPUT}),
            "address": forms.TextInput(attrs={"class": T_INPUT}),
            "hire_date": forms.DateInput(attrs={"type": "date", "class": T_INPUT}),
            "role_title": forms.TextInput(attrs={"class": T_INPUT}),
            "payment_notes": forms.TextInput(attrs={"class": T_INPUT}),
            "status": forms.Select(attrs={"class": T_SELECT}),
        }

    def __init__(self, *args, company, **kwargs):
        self.company = company
        super().__init__(*args, **kwargs)
        from apps.trucks.models import Truck, TruckStatus

        tq = Q(company=company, status=TruckStatus.ACTIVE)
        if self.instance.pk and self.instance.truck_id:
            tq |= Q(pk=self.instance.truck_id)
        self.fields["truck"].queryset = Truck.objects.filter(tq).distinct().order_by("plate")
        self.fields["truck"].required = False
        self.fields["truck"].widget.attrs.update({"class": T_SELECT})
        finalize_company_form(self)

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.pk:
            obj.company = self.company
        elif obj.company_id != self.company.id:
            raise ValueError("Empresa inconsistente.")
        if commit:
            obj.save()
        return obj
